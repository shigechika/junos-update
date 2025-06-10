# junos-update
automatically detect Juniper models and automatically update JUNOS packages

# usage
```
% junos-update --help
usage: junos-update [-h] [--recipe RECIPE] [--list] [--longlist] [--dryrun] [--copy] [--install] [--update] [--force] [--showversion] [--rollback] [--rebootat REBOOTAT] [-d] [-V] [hostname ...]

automatically detect Juniper models and automatically update JUNOS packages

positional arguments:
  hostname              special hostname(s)

options:
  -h, --help            show this help message and exit
  --recipe RECIPE       junos recipe filename (default: junos.ini)
  --list, --short, -ls  short list remote path (like as ls)
  --longlist, -ll       long list remote path (like as ls -l)
  --dryrun              test for --copy/--install/--update. connect and message output. No execute.
  --copy                copy package from local to remote
  --install             install copied package on remote
  --update, --upgrade   copy(=--copy) and install(=--install)
  --force               force execute copy, install and update
  --showversion, --version
                        show running/planning/pending version and reboot schedule
  --rollback            rollback installed package
  --rebootat REBOOTAT   reboot at Date and Time. format is yymmddhhmm. ex: 2501020304
  -d, --debug           for debug
  -V                    show program's version number and exit

default action is show device facts
```

# Install

```bash
python3 -m venv .venv
. .env/bin/activate
pip3 install -r requirements.txt
```

## PyEZ

- requires PyEZ [https://www.juniper.net/documentation/product/us/en/junos-pyez]

```
% pip3 install junos-eznc
```

- pip3

  - Ubuntu/Debian
```
sudo apt install python3-pip
```

  - CentOS/RedHat
```
sudo dnf install python3-pip
```

  - macOS
```
brew install python3
```

# example

- --update

```
% junos-update --update rt1.example.jp
[rt1.example.jp]
remote: jinstall-ppc-18.4R3-S10-signed.tgz is not found.
copy: system storage cleanup successful
rt1.example.jp: cleaning filesystem ...
rt1.example.jp: before copy, computing checksum on remote package: /var/tmp/jinstall-ppc-18.4R3-S10-signed.tgz
rt1.example.jp: b'jinstall-ppc-18.4R3-S10-signed.tgz': 38010880 / 380102074 (10%)
rt1.example.jp: b'jinstall-ppc-18.4R3-S10-signed.tgz': 76021760 / 380102074 (20%)
rt1.example.jp: b'jinstall-ppc-18.4R3-S10-signed.tgz': 114032640 / 380102074 (30%)
rt1.example.jp: b'jinstall-ppc-18.4R3-S10-signed.tgz': 152043520 / 380102074 (40%)
rt1.example.jp: b'jinstall-ppc-18.4R3-S10-signed.tgz': 190054400 / 380102074 (50%)
rt1.example.jp: b'jinstall-ppc-18.4R3-S10-signed.tgz': 228065280 / 380102074 (60%)
rt1.example.jp: b'jinstall-ppc-18.4R3-S10-signed.tgz': 266076160 / 380102074 (70%)
rt1.example.jp: b'jinstall-ppc-18.4R3-S10-signed.tgz': 304087040 / 380102074 (80%)
rt1.example.jp: b'jinstall-ppc-18.4R3-S10-signed.tgz': 342097920 / 380102074 (90%)
rt1.example.jp: b'jinstall-ppc-18.4R3-S10-signed.tgz': 380102074 / 380102074 (100%)
rt1.example.jp: after copy, computing checksum on remote package: /var/tmp/jinstall-ppc-18.4R3-S10-signed.tgz
rt1.example.jp: checksum check passed.
install: clear reboot schedule successful
install: rescue config save suecessful
rt1.example.jp: request-package-checks-pending-install rpc is not supported on given device
rt1.example.jp: validating software against current config, please be patient ...
rt1.example.jp: software validate package-result: 0
Output:
Checking compatibility with configuration
Initializing...
Using jbase-ppc-18.4R3-S7.2
Verified manifest signed by PackageProductionECP256_2021 method ECDSA256+SHA256
Using /var/tmp/jinstall-ppc-18.4R3-S10-signed.tgz
Verified jinstall-ppc-18.4R3-S10.tgz signed by PackageProductionECP256_2021 method ECDSA256+SHA256
Using jinstall-ppc-18.4R3-S10.tgz
Using jbundle-ppc-18.4R3-S10.tgz
Checking jbundle-ppc requirements on /
Using jbase-ppc-18.4R3-S10.tgz
Verified manifest signed by PackageProductionECP256_2021 method ECDSA256+SHA256
Verified jbase-ppc-18.4R3-S10 signed by PackageProductionECP256_2021 method ECDSA256+SHA256
Using /var/v/c/tmp/jbundle-ppc/jboot-ppc-18.4R3-S10.tgz
Using jcrypto-dp-support-18.4R3-S10.tgz
Verified manifest signed by PackageProductionECP256_2021 method ECDSA256+SHA256
Verified jcrypto-dp-support-18.4R3-S10 signed by PackageProductionECP256_2021 method ECDSA256+SHA256
Using jcrypto-ppc-18.4R3-S10.tgz
Verified manifest signed by PackageProductionECP256_2021 method ECDSA256+SHA256
Verified jcrypto-ppc-18.4R3-S10 signed by PackageProductionECP256_2021 method ECDSA256+SHA256
Using jdocs-18.4R3-S10.tgz
Verified manifest signed by PackageProductionECP256_2021 method ECDSA256+SHA256
Verified jdocs-18.4R3-S10 signed by PackageProductionECP256_2021 method ECDSA256+SHA256
Using jkernel-ppc-18.4R3-S10.tgz
Verified manifest signed by PackageProductionECP256_2021 method ECDSA256+SHA256
Verified jkernel-ppc-18.4R3-S10 signed by PackageProductionECP256_2021 method ECDSA256+SHA256
Using jmacsec-18.4R3-S10.tgz
Verified manifest signed by PackageProductionECP256_2021 method ECDSA256+SHA256
Verified jmacsec-18.4R3-S10 signed by PackageProductionECP256_2021 method ECDSA256+SHA256
Using jpfe-ppc-18.4R3-S10.tgz
Verified SHA1 checksum of jpfe-ACX-18.4R3-S10.tgz
Verified SHA1 checksum of jpfe-MX104-18.4R3-S10.tgz
Verified SHA1 checksum of jpfe-MX80-18.4R3-S10.tgz
Verified manifest signed by PackageProductionECP256_2021 method ECDSA256+SHA256
```

- --showversion

```
% junos-update --showversion
[rt1.example.jp]
hostname: rt1
model: MX5-T
running version: 18.4R3-S7.2
planning version: 18.4R3-S10
 	running version seems older than planning version.
	pending version: 18.4R3-S10
running version seems older than pending version. Please plan to reboot.
local package: jinstall-ppc-18.4R3-S10-signed.tgz is found. checksum is OK.
remote package: jinstall-ppc-18.4R3-S10-signed.tgz is found. checksum is OK.
reboot requested by exadmin at Sat Dec  4 05:00:00 2021

[rt2.example.jp]
hostname: rt2
model: EX3400-24T
running version: 18.4R3-S9.2
planning version: 18.4R3-S10
	running version seems older than planning version.
pending version: 18.4R3-S10
	running version seems older than pending version. Please plan to reboot.
local package: junos-arm-32-18.4R3-S10.tgz is found. checksum is OK.
remote package: junos-arm-32-18.4R3-S10.tgz is not found.
reboot requested by exadmin at Wed Dec  8 01:00:00 2021

[rt3.example.jp]
hostname: rt3
model: QFX5110-48S-4C
running version: 18.4R3-S7.2
planning version: 18.4R3-S10
 	running version seems older than planning version.
pending version: None
local package: jinstall-host-qfx-5e-x86-64-18.4R3-S10-secure-signed.tgz is not found.
remote package: jinstall-host-qfx-5e-x86-64-18.4R3-S10-secure-signed.tgz is not found.
No shutdown/reboot scheduled.

[sw1.example.jp]
hostname: sw1
model: EX2300-24T
running version: 18.4R3-S7.2
planning version: 18.4R3-S10
 	running version seems older than planning version.
	pending version: 18.4R3-S10
running version seems older than pending version. Please plan to reboot.
local package: junos-arm-32-18.4R3-S10.tgz is found. checksum is OK.
remote package: junos-arm-32-18.4R3-S10.tgz is not found.
reboot requested by sw1 at Sat Dec  4 05:00:00 2021

[sw2.example.jp]
hostname: sw2
model: EX3400-24T
running version: 18.4R3-S7.2
planning version: 18.4R3-S10
	running version seems older than planning version.
pending version: 18.4R3-S10
	running version seems older than pending version. Please plan to reboot.
local package: junos-arm-32-18.4R3-S10.tgz is found. checksum is OK.
remote package: junos-arm-32-18.4R3-S10.tgz is not found.
shutdown requested by exadmin at Sun Dec 12 08:30:00 2021

[sw3.example.jp]
hostname: sw2
model: EX4300-32F
running version: 20.4R2-S2.2
planning version: 20.4R3.8
	running version seems older than planning version.
pending version: None
local package: jinstall-ex-4300-20.4R3.8-signed.tgz is found. checksum is OK.
remote package: jinstall-ex-4300-20.4R3.8-signed.tgz is found. checksum is OK.
shutdown requested by exadmin at Sun Dec 12 08:30:00 2021
```

- --dryrun

```
% junos-update --update --dryrun srx.example.jp
[srx.example.jp]
remote package: junos-srxentedge-x86-64-18.4R3-S9.2.tgz is not found.
dryrun: request system storage cleanup
dryrun: scp(cheksum:md5) junos-srxentedge-x86-64-18.4R3-S9.2.tgz srx.example.jp:/var/tmp
dryrun: clear system reboot
dryrun: request system configuration rescue save
dryrun: request system software add /var/tmp/junos-srxentedge-x86-64-18.4R3-S9.2.tgz
```

- --rebootat

```
% junos-update --reboot 2506130500 --force
[INFO]main - host='rt1.example.jp'
[INFO]reboot - Shutdown at Fri Jun 13 05:00:00 2025. [pid 97978]

[INFO]main - host='rt2.example.jp'
[INFO]reboot - ANY SHUTDWON/REBOOT SCHEDULE EXISTS
[INFO]reboot - dt=datetime.datetime(2025, 7, 20, 8, 0)
[INFO]reboot - force clear reboot
[INFO]clear_reboot - clear reboot schedule successful
[INFO]reboot - Shutdown at Fri Jun 13 05:00:00 2025. [pid 3321]

[INFO]main - host='rt3.example.jp'
[INFO]reboot - ANY SHUTDWON/REBOOT SCHEDULE EXISTS
[INFO]reboot - dt=datetime.datetime(2025, 6, 27, 9, 0)
[INFO]reboot - force clear reboot
[INFO]clear_reboot - clear reboot schedule successful
[INFO]reboot - Shutdown at Fri Jun 13 05:00:00 2025. [pid 49174]
```

- default

```
% junos-update gw1.example.jp
[gw1.example.jp]
{'2RE': True,
 'HOME': '/var/home/exadmin',
 'RE0': {'last_reboot_reason': 'Router rebooted after a normal shutdown.',
         'mastership_state': 'master',
         'model': 'RE-S-1800x4',
         'status': 'OK',
         'up_time': '100 days, 10 hours, 20 minutes, 30 seconds'},
 'RE1': {'last_reboot_reason': 'Router rebooted after a normal shutdown.',
         'mastership_state': 'backup',
         'model': 'RE-S-1800x4',
         'status': 'OK',
         'up_time': '123 days, 12 hours, 34 minutes, 56 seconds'},
 'RE_hw_mi': False,
 'current_re': ['re0', 'master', 'node', 'fwdd', 'member', 'pfem'],
 'domain': None,
 'fqdn': 'gw1',
 'hostname': 'gw1',
 'hostname_info': {'re0': 'gw1', 're1': 'gw1'},
 'ifd_style': 'CLASSIC',
 'junos_info': {'re0': {'object': junos.version_info(major=(18, 4), type=R, minor=3-S7, build=2),
                        'text': '18.4R3-S7.2'},
                're1': {'object': junos.version_info(major=(18, 4), type=R, minor=3-S7, build=2),
                        'text': '18.4R3-S7.2'}},
 'master': 'RE0',
 'model': 'MX240',
 'model_info': {'re0': 'MX240', 're1': 'MX240'},
 'personality': 'MX',
 're_info': {'default': {'0': {'last_reboot_reason': 'Router rebooted after a '
                                                     'normal shutdown.',
                               'mastership_state': 'master',
                               'model': 'RE-S-1800x4',
                               'status': 'OK'},
                         '1': {'last_reboot_reason': 'Router rebooted after a '
                                                     'normal shutdown.',
                               'mastership_state': 'backup',
                               'model': 'RE-S-1800x4',
                               'status': 'OK'},
                         'default': {'last_reboot_reason': 'Router rebooted '
                                                           'after a normal '
                                                           'shutdown.',
                                     'mastership_state': 'master',
                                     'model': 'RE-S-1800x4',
                                     'status': 'OK'}}},
 're_master': {'default': '0'},
 'serialnumber': 'XXXXXXXXXXXX',
 'srx_cluster': None,
 'srx_cluster_id': None,
 'srx_cluster_redundancy_group': None,
 'switch_style': 'BRIDGE_DOMAIN',
 'vc_capable': False,
 'vc_fabric': None,
 'vc_master': None,
 'vc_mode': None,
 'version': '18.4R3-S7.2',
 'version_RE0': '18.4R3-S7.2',
 'version_RE1': '18.4R3-S7.2',
 'version_info': junos.version_info(major=(18, 4), type=R, minor=3-S7, build=2),
 'virtual': False}
 ```
