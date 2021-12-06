# junos-update
automatic detect Juniper models and automatically update JUNOS packages

# usage
```
% ./junos-update -h
usage: junos-update [-h] [--inifile INIFILE] [--list] [--longlist] [--dryrun] [--copy] [--install] [--update] [--showversion] [-d] [-V]
                    [hostname ...]

automatic detect Juniper models and automatically update JUNOS packages

positional arguments:
  hostname              special hostname(s)

optional arguments:
  -h, --help            show this help message and exit
  --recipe RECIPE       junos recipe filename (default: junos.ini)
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

# PyEZ

require PyEZ [https://www.juniper.net/documentation/product/us/en/junos-pyez]

```
% pip3 install junos-eznc
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
running version: 18.4R3-S7.2
planning version: 18.4R3-S10
	running version seems older than planning version.
pending version: 18.4R3-S10
	running version seems older than pending version. Please plan to reboot.
local package: junos-arm-32-18.4R3-S10.tgz is found. checksum is OK.
remote package: junos-arm-32-18.4R3-S10.tgz is not found.
shutdown requested by exadmin at Sun Dec 12 08:30:00 2021

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
% junos-update --dryrun --update gw1.example.jp
[gw1.example.jp]
remote package: junos-install-mx-x86-64-18.4R3-S10.tgz is found. checksum is OK.
remote package is already copied successfully
dryrun: clear system reboot
dryrun: request system configuration rescue save
dryrun: request system software add /var/tmp/junos-install-mx-x86-64-18.4R3-S10.tgz
```
