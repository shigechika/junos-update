# junos-update
automatic detect Juniper models and automatically update JUNOS packages

# usage
```
% ./junos-update -h
usage: junos-update [-h] [--inifile INIFILE] [--list] [--longlist] [--dryrun] [--copy] [--install] [--update] [--showversion] [-d] [-V]
                    [hostname ...]

junos automatic update

positional arguments:
  hostname              special hostname(s)

optional arguments:
  -h, --help            show this help message and exit
  --inifile INIFILE     junos recipe filename (default: junos.ini)
  --list, --short, -ls  short list remote path (like as ls)
  --longlist, -ll       long list remote path (like as ls -l)
  --dryrun              test for --copy/--install/--update. connect and message output. No execute.
  --copy                copy package from local to remote
  --install             install copied package on remote
  --update, --upgrade   copy(=--copy) and install(=--install)
  --showversion, --version
                        show running/planning/pending version and reboot schedule
  -d, --debug           for debug
  -V                    show program's version number and exit

default action is show device facts
```

#  PyEZ

require PyEZ [https://www.juniper.net/documentation/product/us/en/junos-pyez]

```
% pip3 install junos-eznc
```
