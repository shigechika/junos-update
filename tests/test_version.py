"""バージョン関連関数のテスト"""

import argparse
import datetime
from unittest.mock import MagicMock

import pytest


class TestCompareVersion:
    """compare_version() のテスト"""

    def test_greater(self, junos_update, mock_args):
        assert junos_update.compare_version("22.4R3-S6", "22.4R3-S5") == 1

    def test_less(self, junos_update, mock_args):
        assert junos_update.compare_version("18.4R3-S9", "18.4R3-S10") == -1

    def test_equal(self, junos_update, mock_args):
        assert junos_update.compare_version("22.4R3-S6", "22.4R3-S6") == 0

    def test_none_left(self, junos_update, mock_args):
        assert junos_update.compare_version(None, "22.4R3-S6") is None

    def test_none_right(self, junos_update, mock_args):
        assert junos_update.compare_version("22.4R3-S6", None) is None

    def test_both_none(self, junos_update, mock_args):
        assert junos_update.compare_version(None, None) is None

    def test_major_version_diff(self, junos_update, mock_args):
        assert junos_update.compare_version("22.4R3-S6", "18.4R3-S10") == 1

    def test_minor_version_diff(self, junos_update, mock_args):
        assert junos_update.compare_version("22.2R1", "22.4R1") == -1


class TestYymmddhhmmType:
    """yymmddhhmm_type() のテスト"""

    def test_valid(self, junos_update):
        result = junos_update.yymmddhhmm_type("2501020304")
        assert result == datetime.datetime(2025, 1, 2, 3, 4)

    def test_year_end(self, junos_update):
        result = junos_update.yymmddhhmm_type("2512311959")
        assert result == datetime.datetime(2025, 12, 31, 19, 59)

    def test_invalid_format(self, junos_update):
        with pytest.raises(argparse.ArgumentTypeError):
            junos_update.yymmddhhmm_type("invalid")

    def test_empty_string(self, junos_update):
        with pytest.raises(argparse.ArgumentTypeError):
            junos_update.yymmddhhmm_type("")


class TestGetPlanningVersion:
    """get_planning_version() のテスト"""

    def test_normal(self, junos_update, mock_args, mock_config):
        dev = MagicMock()
        dev.facts = {"model": "EX2300-24T"}
        result = junos_update.get_planning_version("test-host", dev)
        assert result == "22.4R3-S6.5"

    def test_different_format(self, junos_update, mock_args, mock_config):
        """SRX系のファイル名からもバージョン抽出できる"""
        mock_config.set("DEFAULT", "srx345.file", "junos-srxsme-15.1X49-D240.tgz")
        mock_config.set("DEFAULT", "srx345.hash", "dummy")
        dev = MagicMock()
        dev.facts = {"model": "SRX345"}
        result = junos_update.get_planning_version("test-host", dev)
        assert result == "15.1X49-D240"

    def test_no_match(self, junos_update, mock_args, mock_config):
        """正規表現にマッチしないファイル名の場合 None"""
        mock_config.set("DEFAULT", "srx345.file", "noversion.tgz")
        mock_config.set("DEFAULT", "srx345.hash", "dummy")
        dev = MagicMock()
        dev.facts = {"model": "SRX345"}
        result = junos_update.get_planning_version("test-host", dev)
        assert result is None
