#!/usr/bin/env python3

# pylint: disable-next=line-too-long
from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = """
    name: vagrant
    plugin_type: inventory
    short_description: Vagrant inventory source
    requirements:
        - python >= 3.11
    extends_documentation_fragment:
        - constructed
        - inventory_cache
    description:
        - Gets inventory hosts from Vagrant VMs
        - The inventory file is a YAML configuration file and must end with yml or yaml
    options:
        plugin:
            description: token that ensures this is a source file for the 'vagrant' plugin.
            required: True
            choices: ['vagrant']
        cache:
            description: enables caching of Vagrant vm details
            type: boolean
            default: False
        paths:
            description: List of paths where Vagrantfile is located
            type: list
            elements: dict
            required: True
        get_host_only_ips:
            description:
                - use this to find host only ip of vms from Vagrantfile
                - use this only if each vm has individual block definition for creation, other wise the parsing will fail
            type: bool
            default: False
"""

EXAMPLES = """
plugin: vagrant
paths:
  - path: "/home/abhinav/workrelated/vagrant/k8s-cluster-demo"
    group_name: "kubernetes"
    additional_vars:
      - key: some_key_name
        val: some_key_val
      - key: some_other_key_name
        val: some_other_val_and_so_on
get_host_only_ips: false
cache: true
"""

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
import sys
import os.path
import subprocess

if sys.version_info < (3, 11):
    raise AnsibleParserError("This inventory plugin requires Python version 3.11 or higher.")


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = "vagrant"

    def __init__(self):
        super(InventoryModule, self).__init__()

    def verify_file(self, path):
        valid = False
        if path.endswith(("vagrant.yml", "vagrant.yaml")):
            valid = True
        elif path.endswith(("dynamic.yml", "dynamic.yaml")):
            valid = True
        return valid

    def _run_vagrant_command(self, arguments=None, folder=None):
        """Runs 'vagrant ssh-config' command in a folder and returns a dictionary data for processing"""
        if arguments and not folder:
            raise AnsibleError("You must specify a folder to run vagrant ssh-config")

        if not folder:
            folder = "/tmp"

        if not arguments:
            arguments = "--version"

        run_command = "vagrant {}".format(arguments)

        output = None
        try:
            result = subprocess.run(run_command, shell=True, check=True, timeout=15, capture_output=True, cwd=folder)
            output = result.stdout.decode('utf-8')
        except subprocess.CalledProcessError as e:
            if arguments != "ssh-config":
                raise AnsibleError("Running vagrant command failed: {}".format(e))
            else:
                self.display.warning("Running 'vagrant ssh-config' failed at path: {}. SKIPPED".format(folder))

        return output

    @staticmethod
    def _get_vms_private_ips(file_path):
        """
        reads a Vagrantfile and returns a dictionary of vms and private ip
        :param file_path: full path to Vagrantfile
        :return: a dictionary of vms and private ips
        """
        with open(file_path) as f1:
            vagrant_file_data = f1.readlines()

        return_data = {}
        current_vm = None
        current_vm_ip = None
        for each_line in vagrant_file_data:
            each_line_strip = each_line.strip()

            if each_line_strip.startswith("config.vm.define"):
                current_vm = each_line_strip.split(",")[0].strip().split(" ")[-1].strip("'").strip('"')

            if "vm.network :private_network, ip:" in each_line_strip:
                current_vm_ip = each_line_strip.split(":")[-1].strip().strip('"').strip("'")

            if current_vm and current_vm_ip:
                return_data[current_vm] = current_vm_ip
                current_vm = None
                current_vm_ip = None

        return return_data

    def _get_vagrant_vm_details(self):
        """
        return a dictionary of found running vms in each folder.
        :return: list
        """
        self.display.vv("vagrant version: {}".format(self._run_vagrant_command()))

        get_private_ip = self.get_option("get_host_only_ips")
        vm_paths = self.get_option("paths")
        private_ips = {}
        existing_group_names = []
        vagrant_vm_details = {}

        for each_item in vm_paths:
            if 'path' not in each_item:
                self.display.warning("dictionary doesn't contain 'path' key. {}".format(each_item))
                continue
            vagrant_path = each_item["path"]
            vagrant_file_path = "{}/Vagrantfile".format(vagrant_path)
            if not os.path.isfile(vagrant_file_path):
                self.display.warning("Vagrantfile not found at {}".format(vagrant_path))
                continue

            group_name = None
            if 'group_name' in each_item and each_item['group_name']:
                group_name = each_item['group_name']
            else:
                vagrant_folder_name_base = vagrant_path.split("/")[-1]
                counter = 0
                in_loop = True
                while in_loop:
                    if counter == 0:
                        vm_folder_name = vagrant_folder_name_base
                    else:
                        vm_folder_name = "{}-{}".format(vagrant_folder_name_base, counter)

                    if vm_folder_name not in existing_group_names:
                        existing_group_names.append(vm_folder_name)
                        in_loop = False
                        group_name = vm_folder_name

                    if counter > len(existing_group_names):
                        break

                    counter += 1

            if not group_name:
                raise AnsibleParserError("Could not decide group name from given data for path {}".format(each_item["path"]))

            if get_private_ip:
                vagrant_file_ips = self._get_vms_private_ips(vagrant_file_path)
                private_ips[group_name] = vagrant_file_ips

            if group_name not in vagrant_vm_details:
                vagrant_vm_details[group_name] = {"vms": []}

            if 'additional_vars' in each_item and each_item['additional_vars']:
                vagrant_vm_details[group_name]['vars'] = each_item['additional_vars']

            vagrant_output = self._run_vagrant_command(arguments="ssh-config", folder=vagrant_path).splitlines()

            vm_name = None
            vm_ip = None
            vm_user = None
            vm_port = None
            vm_key = None
            for each_line in vagrant_output:
                if each_line.startswith('Host'):
                    vm_name = each_line.split()[-1].strip()
                    continue

                if not vm_name:
                    continue

                each_line_strip = each_line.strip()

                if each_line_strip.startswith("HostName"):
                    vm_ip = each_line_strip.split()[-1].strip()

                if each_line_strip.startswith("User") and 'UserKnownHostsFile' not in each_line_strip:
                    vm_user = each_line_strip.split()[-1].strip()

                if each_line_strip.startswith("Port"):
                    vm_port = each_line_strip.split()[-1].strip()

                if each_line_strip.startswith("IdentityFile"):
                    vm_key = each_line_strip.split()[-1].strip()

                if vm_name and vm_ip and vm_user and vm_port and vm_key:
                    vm_details = {
                        "name": vm_name,
                        "host": vm_ip,
                        "user": vm_user,
                        "port": vm_port,
                        "key": vm_key
                    }

                    if group_name in private_ips and vm_name in private_ips[group_name] and private_ips[group_name][vm_name]:
                        vm_details["host_only_ip"] = private_ips[group_name][vm_name]

                    vagrant_vm_details[group_name]['vms'].append(vm_details)
                    vm_name = None
                    vm_ip = None
                    vm_user = None
                    vm_port = None
                    vm_key = None

        vm_data = []
        for each_key in vagrant_vm_details:
            group_data = {"group": each_key, "vms": vagrant_vm_details[each_key]['vms']}
            if 'vars' in vagrant_vm_details[each_key] and vagrant_vm_details[each_key]:
                group_data['vars'] = vagrant_vm_details[each_key]['vars']

            vm_data.append(group_data)

        return vm_data

    def _parse_ansible_data(self, data):
        vagrant_main_group = self.inventory.add_group("vagrant")

        for each_item in data:
            # add group to inventory
            group_name = each_item["group"]
            ansible_group = self.inventory.add_group(group_name)

            # add group vars if we have been provided with
            if 'vars' in each_item and type(each_item['vars']) == list:
                for each_var_item in each_item['vars']:
                    if 'key' not in each_var_item or 'val' not in each_var_item:
                        # drop items in list silently which doesn't have key and val in them.
                        continue
                    self.inventory.set_variable(ansible_group, each_var_item['key'], each_var_item['val'])

            # now add each vm to this ansible group
            for each_vm in each_item['vms']:
                if 'host_only_ip' in each_vm and each_vm['host_only_ip']:
                    inventory_host = each_vm['host_only_ip']
                else:
                    inventory_host = each_vm['name']

                host = self.inventory.add_host(inventory_host, group=ansible_group)
                self.inventory.set_variable(host, 'ht_name', each_vm['name'])
                self.inventory.set_variable(host, 'ansible_host', each_vm['host'])
                self.inventory.set_variable(host, 'ansible_port', each_vm['port'])
                self.inventory.set_variable(host, 'ansible_user', each_vm['user'])
                self.inventory.set_variable(host, 'ansible_ssh_private_key_file', each_vm['key'])

            # add this group under vagrant group in ansible
            self.inventory.add_child(vagrant_main_group, ansible_group)

        # add vagrant group to all main group
        self.inventory.add_child('all', vagrant_main_group)

        # add local group for local work
        local_group = self.inventory.add_group("local")
        local_host = self.inventory.add_host("127.0.0.1", group=local_group)
        self.inventory.set_variable(local_host, "ansible_connection", "local")
        self.inventory.set_variable(local_host, 'ht_name', 'local')
        self.inventory.add_child('all', local_group)

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path)

        # Cache logic: copied pasted from gcp_compute.py plugin
        # - https://github.com/ansible-collections/google.cloud/blob/master/plugins/inventory/gcp_compute.py
        # I didn't care enough to understand it, but it works as is.
        vagrant_data = None
        if cache:
            cache = self.get_option("cache")
            cache_key = self.get_cache_key(path)
        else:
            cache_key = None

        cache_needs_update = False
        if cache:
            try:
                vagrant_data = self._cache[cache_key]
            except KeyError:
                cache_needs_update = True

        if not cache or cache_needs_update:
            vagrant_data = self._get_vagrant_vm_details()

            if cache_needs_update:
                self._cache[cache_key] = vagrant_data

        # vagrant_data = self._get_vagrant_vm_details()
        self._parse_ansible_data(vagrant_data)
