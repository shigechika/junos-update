import argparse
import configparser
import pytest

from junos_ops import cli as junos_update_mod


@pytest.fixture
def junos_update():
    """junos_ops.cli モジュールを返す"""
    return junos_update_mod


@pytest.fixture
def mock_args(junos_update):
    """テスト用の args グローバル変数を設定"""
    junos_update.args = argparse.Namespace(
        debug=False,
        dry_run=False,
        force=False,
        copy=False,
        install=False,
        update=False,
        showversion=False,
        rollback=False,
        rebootat=None,
        list_format=None,
        config="config.ini",
    )
    return junos_update.args


@pytest.fixture
def mock_config(junos_update):
    """テスト用の config グローバル変数を設定"""
    cfg = configparser.ConfigParser(allow_no_value=True)
    cfg.read_dict(
        {
            "DEFAULT": {
                "id": "testuser",
                "pw": "testpass",
                "sshkey": "id_ed25519",
                "port": "830",
                "hashalgo": "md5",
                "rpath": "/var/tmp",
                "ex2300-24t.file": "junos-arm-32-22.4R3-S6.5.tgz",
                "ex2300-24t.hash": "abc123def456",
            },
            "test-host": {"host": "192.0.2.1"},
        }
    )
    junos_update.config = cfg
    return cfg
