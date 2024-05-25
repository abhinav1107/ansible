## Ansible Inventory Plugin for Vagrant

create a file `02-dynamic.yml` under environment directory.

It can cache results. use environment variables `ANSIBLE_CACHE_PLUGIN_CONNECTION` and `ANSIBLE_INVENTORY_CACHE_PLUGIN`

`ANSIBLE_INVENTORY_CACHE_PLUGIN` is the plugin that will be used for storing cache data. More information [here](https://docs.ansible.com/ansible/2.9/plugins/cache.html?highlight=cache_plugin#plugin-list)

if `ANSIBLE_INVENTORY_CACHE_PLUGIN` is set to `jsonfile`, we need to set up `ANSIBLE_CACHE_PLUGIN_CONNECTION` directory.

`ANSIBLE_CACHE_PLUGIN_CONNECTION` is the path of the cache where ansible will store the inventory cache. For ex:
```shell
export ANSIBLE_CACHE_PLUGIN_CONNECTION="~/.ansible-retry-files"
```
