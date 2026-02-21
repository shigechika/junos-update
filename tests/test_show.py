"""show サブコマンドのテスト"""

from unittest.mock import MagicMock, patch

from junos_ops import cli
from junos_ops import common


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


class TestCmdShowFile:
    """cmd_show() の -f ファイルモードのテスト"""

    def test_showfile_success(self, junos_common, mock_args, mock_config, capsys):
        """複数コマンドファイルからの正常実行、出力フォーマット確認"""
        mock_args.showfile = "commands.txt"
        mock_args.show_command = None
        mock_dev = MagicMock()
        mock_dev.cli.side_effect = [
            "  terse output  ",
            "  route summary  ",
        ]

        with (
            patch.object(cli.common, "connect", return_value=(False, mock_dev)),
            patch.object(
                cli.common, "load_commands",
                return_value=["show interfaces terse", "show route summary"],
            ),
        ):
            result = cli.cmd_show("test-host")

        assert result == 0
        assert mock_dev.cli.call_count == 2
        mock_dev.cli.assert_any_call("show interfaces terse")
        mock_dev.cli.assert_any_call("show route summary")
        mock_dev.close.assert_called_once()

        captured = capsys.readouterr()
        assert "# test-host" in captured.out
        assert "## show interfaces terse" in captured.out
        assert "terse output" in captured.out
        assert "## show route summary" in captured.out
        assert "route summary" in captured.out

    def test_showfile_skips_comments_and_blanks(
        self, junos_common, mock_args, mock_config, capsys
    ):
        """load_commands がコメント行と空行をスキップすることの確認"""
        mock_args.showfile = "commands.txt"
        mock_args.show_command = None
        mock_dev = MagicMock()
        mock_dev.cli.return_value = "output"

        with (
            patch.object(cli.common, "connect", return_value=(False, mock_dev)),
            patch.object(
                cli.common, "load_commands",
                return_value=["show version"],
            ),
        ):
            result = cli.cmd_show("test-host")

        assert result == 0
        # load_commands がフィルタ済みの1コマンドだけ返すので cli() は1回
        mock_dev.cli.assert_called_once_with("show version")

    def test_showfile_exception_on_one_command(
        self, junos_common, mock_args, mock_config
    ):
        """途中のコマンドで例外 → エラー返却"""
        mock_args.showfile = "commands.txt"
        mock_args.show_command = None
        mock_dev = MagicMock()
        mock_dev.cli.side_effect = Exception("RPC timeout")

        with (
            patch.object(cli.common, "connect", return_value=(False, mock_dev)),
            patch.object(
                cli.common, "load_commands",
                return_value=["show version", "show bgp summary"],
            ),
        ):
            result = cli.cmd_show("test-host")

        assert result == 1
        mock_dev.close.assert_called_once()

    def test_showfile_connect_fail(self, junos_common, mock_args, mock_config):
        """接続失敗時に 1 を返す"""
        mock_args.showfile = "commands.txt"
        mock_args.show_command = None
        with patch.object(cli.common, "connect", return_value=(True, None)):
            result = cli.cmd_show("test-host")
            assert result == 1


class TestLoadCommands:
    """common.load_commands() ヘルパーの単体テスト"""

    def test_load_commands(self, tmp_path):
        """コメント行と空行を除外してコマンド行のみ返す"""
        cmd_file = tmp_path / "commands.txt"
        cmd_file.write_text(
            "# コメント行\n"
            "show version\n"
            "\n"
            "  # インデント付きコメント\n"
            "show interfaces terse\n"
            "  show route summary  \n"
        )
        result = common.load_commands(str(cmd_file))
        assert result == [
            "show version",
            "show interfaces terse",
            "show route summary",
        ]

    def test_load_commands_empty_file(self, tmp_path):
        """空ファイルからは空リストが返る"""
        cmd_file = tmp_path / "empty.txt"
        cmd_file.write_text("")
        result = common.load_commands(str(cmd_file))
        assert result == []

    def test_load_commands_only_comments(self, tmp_path):
        """コメントのみのファイルからは空リストが返る"""
        cmd_file = tmp_path / "comments.txt"
        cmd_file.write_text("# comment 1\n# comment 2\n\n")
        result = common.load_commands(str(cmd_file))
        assert result == []
