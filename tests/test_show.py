"""show サブコマンドのテスト"""

from unittest.mock import MagicMock, patch

from junos_ops import cli


class TestCmdShow:
    """cmd_show() のテスト"""

    def test_connect_fail(self, junos_common, mock_args, mock_config):
        """接続失敗時に 1 を返す"""
        mock_args.show_command = "show version"
        with patch.object(cli.common, "connect", return_value=(True, None)):
            result = cli.cmd_show("test-host")
            assert result == 1

    def test_success(self, junos_common, mock_args, mock_config, capsys):
        """正常時にホスト名付きで出力される"""
        mock_args.show_command = "show version"
        mock_dev = MagicMock()
        mock_dev.cli.return_value = "  Hostname: test-host\nModel: MX204  \n"

        with patch.object(cli.common, "connect", return_value=(False, mock_dev)):
            result = cli.cmd_show("test-host")

        assert result == 0
        mock_dev.cli.assert_called_once_with("show version")
        mock_dev.close.assert_called_once()
        captured = capsys.readouterr()
        assert "# test-host" in captured.out
        assert "Hostname: test-host" in captured.out
        assert "Model: MX204" in captured.out

    def test_exception(self, junos_common, mock_args, mock_config):
        """dev.cli() 例外時に 1 を返す"""
        mock_args.show_command = "show bgp summary"
        mock_dev = MagicMock()
        mock_dev.cli.side_effect = Exception("RPC timeout")

        with patch.object(cli.common, "connect", return_value=(False, mock_dev)):
            result = cli.cmd_show("test-host")

        assert result == 1
        mock_dev.close.assert_called_once()

    def test_dev_close_on_exception(self, junos_common, mock_args, mock_config):
        """例外時でも dev.close() が呼ばれる"""
        mock_args.show_command = "show interfaces terse"
        mock_dev = MagicMock()
        mock_dev.cli.side_effect = RuntimeError("unexpected")

        with patch.object(cli.common, "connect", return_value=(False, mock_dev)):
            result = cli.cmd_show("test-host")

        assert result == 1
        mock_dev.close.assert_called_once()

    def test_close_exception_suppressed(self, junos_common, mock_args, mock_config):
        """dev.close() の例外が握り潰される"""
        mock_args.show_command = "show version"
        mock_dev = MagicMock()
        mock_dev.cli.return_value = "output"
        mock_dev.close.side_effect = Exception("close failed")

        with patch.object(cli.common, "connect", return_value=(False, mock_dev)):
            result = cli.cmd_show("test-host")

        assert result == 0

    def test_show_command_passed_to_cli(self, junos_common, mock_args, mock_config):
        """args.show_command がそのまま dev.cli() に渡される"""
        mock_args.show_command = "show configuration system login user nttview"
        mock_dev = MagicMock()
        mock_dev.cli.return_value = "user nttview { ... }"

        with patch.object(cli.common, "connect", return_value=(False, mock_dev)):
            result = cli.cmd_show("test-host")

        assert result == 0
        mock_dev.cli.assert_called_once_with(
            "show configuration system login user nttview"
        )
