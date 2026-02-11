import importlib.util
import importlib.machinery
import argparse
import configparser
from pathlib import Path
import pytest

# プロジェクトルートの junos-update スクリプトのパス
SCRIPT_PATH = str(Path(__file__).resolve().parent.parent / "junos-update")


@pytest.fixture
def junos_update():
    """junos-update スクリプトをモジュールとしてインポート"""
    loader = importlib.machinery.SourceFileLoader("junos_update", SCRIPT_PATH)
    spec = importlib.util.spec_from_file_location(
        "junos_update", SCRIPT_PATH, loader=loader
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def mock_args(junos_update):
    """テスト用の args グローバル変数を設定"""
    junos_update.args = argparse.Namespace(
        debug=False,
        dryrun=False,
        force=False,
        copy=False,
        install=False,
        update=False,
        showversion=False,
        rollback=False,
        rebootat=None,
        list_format=None,
        recipe="junos.ini",
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
