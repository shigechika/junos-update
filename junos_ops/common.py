"""共通機能: 設定読込、接続管理、ターゲット決定、並列実行"""

from concurrent import futures
from jnpr.junos import Device
from jnpr.junos.exception import (
    ConnectAuthError,
    ConnectClosedError,
    ConnectError,
    ConnectRefusedError,
    ConnectTimeoutError,
    ConnectUnknownHostError,
)
import configparser
import os
import sys
import threading
from logging import getLogger

logger = getLogger(__name__)

config = None
config_lock = threading.Lock()
args = None

DEFAULT_CONFIG = "config.ini"


def get_default_config():
    """設定ファイルのデフォルトパスを探索順に返す"""
    # カレントディレクトリ
    if os.path.isfile(DEFAULT_CONFIG):
        return DEFAULT_CONFIG
    # XDG_CONFIG_HOME（未設定なら ~/.config）
    xdg = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    xdg_path = os.path.join(xdg, "junos-ops", DEFAULT_CONFIG)
    if os.path.isfile(xdg_path):
        return xdg_path
    return DEFAULT_CONFIG


def read_config():
    global config
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(args.config)
    if len(config.sections()) == 0:
        print(args.config, "is empty")
        return True
    for section in config.sections():
        if config.has_option(section, "host"):
            host = config.get(section, "host")
        else:
            host = None
        if host is None:
            # host is [section] name
            config.set(section, "host", section)
        if args.debug:
            for key in config[section]:
                print(section, ">", key, ":", config[section][key])
            print()
    return False


def connect(hostname):
    if args.debug:
        print("connect: start")
    dev = Device(
        host=config.get(hostname, "host"),
        port=int(config.get(hostname, "port")),
        user=config.get(hostname, "id"),
        passwd=config.get(hostname, "pw"),
        ssh_private_key_file=config.get(hostname, "sshkey"),
        huge_tree=config.getboolean(hostname, "huge_tree", fallback=False),
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
    if args.debug:
        print("connect: err=", err, "dev=", dev)
    if args.debug:
        print("connect: end")
    return err, dev


def get_targets():
    """specialhosts が指定されていればそのリスト、なければ全セクション"""
    targets = []
    if len(args.specialhosts) == 0:
        for i in config.sections():
            tmp = config.get(i, "host")
            logger.debug(f"{i=} {tmp=}")
            if tmp is not None:
                targets.append(i)
            else:
                print(i, "is not found in", args.config)
                sys.exit(1)
    else:
        for i in args.specialhosts:
            if config.has_section(i):
                tmp = config.get(i, "host")
            else:
                print(i, "is not found in", args.config)
                sys.exit(1)
            logger.debug(f"{i=} {tmp=}")
            targets.append(i)
    return targets


def run_parallel(func, targets, max_workers=1):
    """ターゲットリストに対して関数を並列実行する

    max_workers=1 の場合はシリアル実行（既存動作と同じ）
    """
    if max_workers <= 1:
        results = {}
        for target in targets:
            results[target] = func(target)
        return results

    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_target = {
            executor.submit(func, target): target
            for target in targets
        }
        results = {}
        for future in futures.as_completed(future_to_target):
            target = future_to_target[future]
            try:
                results[target] = future.result()
            except Exception as e:
                logger.error(f"{target} generated an exception: {e}")
                results[target] = 1
        return results
