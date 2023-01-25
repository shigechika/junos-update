# Hi-Speeed Collection of JUNOS Request Support Information

from distutils.version import LooseVersion
from jnpr.junos import Device
from jnpr.junos.exception import (
    ConnectAuthError,
    ConnectClosedError,
    ConnectError,
    ConnectRefusedError,
    ConnectTimeoutError,
    ConnectUnknownHostError,
)
from jnpr.junos.exception import RpcError, RpcTimeoutError
from jnpr.junos.utils.config import Config
from jnpr.junos.utils.fs import FS
from jnpr.junos.utils.sw import SW
from lxml import etree
from ncclient.operations.errors import TimeoutExpiredError
from pprint import pprint
import argparse
import configparser
import datetime
import re
import sys


class rsi:
    version = "0.0"

    def __init__(self):
        self.parse_arg()
        self.parse_config()
        self.get_targets()

    def parse_arg(self):
        parser = argparse.ArgumentParser(
            description="automatically detect Juniper models and automatically update JUNOS packages",
            epilog="default action is show device facts",
        )
        parser.add_argument(
            "specialhosts",
            metavar="hostname",
            type=str,
            nargs="*",
            help="special hostname(s)",
        )
        parser.add_argument(
            "--recipe",
            default="junos.ini",
            type=str,
            help="junos recipe filename (default: %(default)s)",
        )
        parser.add_argument(
            "--list",
            "-ls",
            action="store_const",
            dest="list_format",
            const="short",
            help="short list remote path (like as ls)",
        )
        parser.add_argument(
            "--dryrun",
            action="store_true",
            help="test for --copy/--install/--update. connect and message output. No execute.",
        )
        parser.add_argument(
            "--showversion",
            "--version",
            action="store_true",
            help="show running/planning/pending version and reboot schedule",
        )
        parser.add_argument("-d", "--debug", action="store_true", help="for debug")
        parser.add_argument("-V", action="version", version="%(prog)s " + version)
        self.args = parser.parse_args()

    def parse_config(self):
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.read(self.args.recipe)
        if self.args.debug:
            if len(self.config.sections()) == 0:
                raise ValueError(f"{self.args.recipe} is empty")
        for section in self.config.sections():
            if self.config.has_option(section, "host"):
                host = self.config.get(section, "host")
            else:
                host = None
            if host is None:
                # host is [section] name
                self.config.set(section, "host", section)
            if self.args.debug:
                for key in self.config[section]:
                    print(f"{section} > {key} : {self.config[section][key]}")

    def get_targets(self):
        self.targets = []
        if len(self.args.specialhosts) == 0:
            for i in self.config.sections():
                tmp = self.config.get(i, "host")
                if self.args.debug:
                    print(i, tmp)
                if tmp is not None:
                    self.targets.append(i)
                else:
                    print(i, "is not found in", args.recipe)
                    sys.exit(1)
        else:
            for i in self.args.specialhosts:
                if self.config.has_section(i):
                    tmp = self.config.get(i, "host")
                else:
                    print(i, "is not found in", args.recipe)
                    sys.exit(1)
                if self.args.debug:
                    print(i, tmp)
                self.targets.append(i)

    def connect(self, hostname):
        if self.args.debug:
            print("connect: start", flush=True)
        dev = Device(
            host=self.config.get(hostname, "host"),
            port=self.config.get(hostname, "port"),
            user=self.config.get(hostname, "id"),
            passwd=self.config.get(hostname, "pw"),
            ssh_private_key_file=self.config.get(hostname, "sshkey"),
        )
        err = None
        try:
            dev.open()
            err = False
        except ConnectAuthError as e:
            print("Authentication credentials fail to login: {0}".format(e))
            dev = None
            err = True
        except ConnectRefusedError as e:
            print("NETCONF Connection refused: {0}".format(e))
            dev = None
            err = True
        except ConnectTimeoutError as e:
            print("Connection timeout: {0}".format(e))
            dev = None
            err = True
        except ConnectError as e:
            print("Cannot connect to device: {0}".format(e))
            dev = None
            err = True
        except ConnectUnknownHostError as e:
            print("Unknown Host: {0}".format(e))
            dev = None
            err = True
        except Exception as e:
            print(e)
            dev = None
            err = True
        if self.args.debug:
            print("connect: err=", err, "dev=", dev)
        if self.args.debug:
            print("connect: end", flush=True)
        return err, dev

    def get_support_information(self, dev):
        try:
            if dev.facts["personality"] == "SRX_BRANCH":
                # SRX3xx series RSI is VERY SLOW
                timeout = 1200
            else:
                timeout = 600
            if self.args.debug:
                print(f"get_support_information: timeout={timeout}", flush=True)
            rpc = dev.rpc.get_support_information(
                {"format": "text"}, dev_timeout=timeout
            )
            return rpc
        except RpcError as e:
            print("Show version failure caused by RpcError:", e)
            sys.exit(1)
        except RpcTimeoutError as e:
            print("Show version failure caused by RpcTimeoutError:", e)
            sys.exit(1)
        except Exception as e:
            print(err)
            sys.exit(1)

    def rsi_target(self, hostname):
        if self.args.debug:
            print("rsi_target: start", flush=True)
        err, dev = self.connect(hostname)
        if err or dev is None:
            sys.exit(1)
        rpc = self.get_support_information(dev)
        str = etree.tostring(rpc, encoding="unicode", method="text")
        if self.args.debug:
            print(f"rsi_target : {str}")
        if self.args.debug:
            print("rsi_target: end", flush=True)
        return str

    def rsi_targets(self):
        for target in self.targets:
            str = self.rsi_target(target)
            with open(f"{target}.RSI", mode="w") as f:
                f.write(str)


if __name__ == "__main__":
    rsi = rsi()
    rsi.rsi_targets()
