#!/usr/bin/env python3

from ansible.errors import AnsibleParserError, AnsibleError
from ansible.plugins.inventory import BaseInventoryPlugin
import sys

if sys.version_info < (3, 11):
    raise AnsibleParserError("This inventory plugin requires Python version 3.11 or higher.")

DOCUMENTATION = r'''
    name: Inventory Plugin for Vagrant vms
    plugin_type: inventory
    author:
        - Abhinav (@abhinav1107)
    short_description: "Gets all inventory hosts from Vagrant"
    version_added: "2.12"
    description:
        - "Gets all ansible inventory hosts from running vms with Vagrant"
    options:
        vagrant_paths:
            description: "Full path of folder where Vagrantfile is"
            type: list
            required: True
        parse_vagrant_private_ip:
            description:
              - use this to find host only ip of vms from Vagrantfile
              - use this only if each vm has individual block definition for creation, other wise the parsing will fail
              - defaults to false
            type: bool
            default: False
            required: False
    requirements:
        - python >= 3.11
'''

EXAMPLES = r'''
plugin: vagrant
vagrant_paths:
  - path: /home/abhinav/workrelated/vagrant/k8s-cluster-demo    # REQUIRED
    group_name: kubernetes                                      # OPTIONAL
    additional_vars:                                            # OPTIONAL
      - key: some_key_name
        val: some_key_val
      - key: some_other_key_name
        val: some_other_val_and_so_on
parse_vagrant_file: False                                       # OPTIONAL
'''


class InventoryModule(BaseInventoryPlugin):
    NAME = 'vagrant'

    def __init__(self):
        super(InventoryModule, self).__init__()
        self.display.columns = 120

    def verify_file(self, path):
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('vagrant.yml', 'vagrant.yaml', 'dynamic.yaml', 'dynamic.yml')):
                return True

    def _get_vagrant_vm_details(self):
        """
        return a dictionary of found running vms in each folder.
        :return: list
        """
        vm_data = [
            {
                "group":"group1",
                "vms":[
                    {
                        "name":"vm1",
                        "host":"127.0.0.1",
                        "user":"vagrant",
                        "port":2222,
                        "key":"some-vagrant-private-key"
                    },
                    {
                        "name":"vm2",
                        "host":"127.0.0.1",
                        "user":"vagrant",
                        "port":2200,
                        "key":"some-vagrant-private-key"
                    }
                ]
            },
            {
                "group":"group2",
                "vms":[
                    {
                        "name":"vm3",
                        "host":"127.0.0.1",
                        "user":"vagrant",
                        "port":2201,
                        "key":"some-vagrant-private-key"
                    },
                    {
                        "name":"vm4",
                        "host":"127.0.0.1",
                        "user":"vagrant",
                        "port":2202,
                        "key":"some-vagrant-private-key"
                    }
                ]
            }
        ]

        self._parse_ansible_data(vm_data)

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
        self._get_vagrant_vm_details()
