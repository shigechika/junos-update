"""run_parallel() / get_targets() のテスト"""

import argparse

import pytest


class TestRunParallel:
    """run_parallel() のテスト"""

    def test_serial(self, junos_common):
        """max_workers=1 でシリアル実行"""
        results = junos_common.run_parallel(lambda t: t.upper(), ["a", "b", "c"], max_workers=1)
        assert results == {"a": "A", "b": "B", "c": "C"}

    def test_parallel(self, junos_common):
        """max_workers>1 で並列実行"""
        results = junos_common.run_parallel(lambda t: t.upper(), ["a", "b", "c"], max_workers=3)
        assert results == {"a": "A", "b": "B", "c": "C"}

    def test_parallel_exception(self, junos_common):
        """並列実行中の例外はエラーコード1を返す"""
        def failing(t):
            if t == "b":
                raise RuntimeError("fail")
            return 0

        results = junos_common.run_parallel(failing, ["a", "b", "c"], max_workers=3)
        assert results["a"] == 0
        assert results["b"] == 1
        assert results["c"] == 0

    def test_empty_targets(self, junos_common):
        """空のターゲットリスト"""
        results = junos_common.run_parallel(lambda t: 0, [], max_workers=1)
        assert results == {}


class TestGetTargets:
    """get_targets() のテスト"""

    def test_all_sections(self, junos_common, mock_args, mock_config):
        """specialhosts 未指定時は全セクションを返す"""
        junos_common.args.specialhosts = []
        targets = junos_common.get_targets()
        assert targets == ["test-host"]

    def test_specific_hosts(self, junos_common, mock_args, mock_config):
        """specialhosts 指定時はそのリストを返す"""
        junos_common.args.specialhosts = ["test-host"]
        targets = junos_common.get_targets()
        assert targets == ["test-host"]

    def test_unknown_host_exits(self, junos_common, mock_args, mock_config):
        """存在しないホスト指定時は sys.exit"""
        junos_common.args.specialhosts = ["unknown-host"]
        with pytest.raises(SystemExit):
            junos_common.get_targets()
