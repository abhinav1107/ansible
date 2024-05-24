# ansible
Ansible automation for my local play


## Initial Setup

- ensure python3.11 or higher is installed in your machine.
  - for ubuntu 22.04, this is how I installed:
    ```shell
    apt update
    apt install python3.11-full
    apt install python3-virtualenv
    ```
- create a virtual environment, so that we don't end up messing with system's version of python
  - for ubuntu 22.04, this is how I created virtual environment for my user:
    ```shell
    mkdir -p ~/.pyenvs
    virtualenv -p python3.11 ~/.pyenvs/python3.11
    ```
- modify `~/.bashrc` file so that this `~/.pyenvs/python3.11` becomes our default python. Add these at the bottom of your `.bashrc` file:
  ```shell
  export VIRTUAL_ENV_DISABLE_PROMPT="true"
  source ~/.pyenvs/python3.11/bin/activate
  ```
- either logout and login again or run `source ~/.bashrc` / `. ~/.bashrc`. This is to reflect the above `.bashrc` file changes
- now install `pipx`. More details [here](https://pipx.pypa.io/stable/#on-linux). This is how I installed:
  ```shell
  python3 -m pip install pipx
  pipx ensurepath
  ```
- Now install ansible using pipx. More instructions [here](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#pipx-install). This is how I did it:
  ```shell
  pipx install --include-deps ansible
  ```
if everything is goes successfully, running `ansible --version` should give output similar to below one:
```text
abhinav@desktop:~$ ansible --version
ansible [core 2.16.7]
  config file = /etc/ansible/ansible.cfg
  configured module search path = ['/home/abhinav/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /home/abhinav/.local/pipx/venvs/ansible/lib/python3.11/site-packages/ansible
  ansible collection location = /home/abhinav/.ansible/collections:/usr/share/ansible/collections
  executable location = /home/abhinav/.local/bin/ansible
  python version = 3.11.0rc1 (main, Aug 12 2022, 10:02:14) [GCC 11.2.0] (/home/abhinav/.local/pipx/venvs/ansible/bin/python)
  jinja version = 3.1.4
  libyaml = True
abhinav@desktop:~$
```
