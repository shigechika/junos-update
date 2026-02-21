"""load_config() のテスト"""

from unittest.mock import MagicMock, patch, call

from junos_ops import common


class TestLoadConfig:
    """load_config() のテスト"""

    def test_success(self, junos_upgrade, mock_args, mock_config):
        """正常系: load → diff → commit_check → commit confirmed → confirm"""
        dev = MagicMock()
        mock_cu = MagicMock()
        mock_cu.diff.return_value = "[edit]\n+  set system ..."
        with (
            patch("junos_ops.upgrade.Config", return_value=mock_cu),
            patch.object(
                common, "load_commands",
                return_value=["set system host-name test"],
            ),
        ):
            result = junos_upgrade.load_config("test-host", dev, "commands.set")
        assert result is False
        mock_cu.lock.assert_called_once()
        mock_cu.load.assert_called_once_with(
            "set system host-name test", format="set",
        )
        mock_cu.diff.assert_called_once()
        mock_cu.pdiff.assert_called_once()
        mock_cu.commit_check.assert_called_once()
        # commit confirmed 1 → commit で確定
        assert mock_cu.commit.call_count == 2
        mock_cu.commit.assert_any_call(confirm=1)
        mock_cu.commit.assert_any_call()
        mock_cu.unlock.assert_called_once()

    def test_no_changes(self, junos_upgrade, mock_args, mock_config):
        """差分なし → "no changes" で正常終了"""
        dev = MagicMock()
        mock_cu = MagicMock()
        mock_cu.diff.return_value = None
        with (
            patch("junos_ops.upgrade.Config", return_value=mock_cu),
            patch.object(common, "load_commands", return_value=["set system ntp"]),
        ):
            result = junos_upgrade.load_config("test-host", dev, "commands.set")
        assert result is False
        mock_cu.lock.assert_called_once()
        mock_cu.load.assert_called_once()
        mock_cu.commit.assert_not_called()
        mock_cu.unlock.assert_called_once()

    def test_dry_run(self, junos_upgrade, mock_args, mock_config):
        """dry-run: diff 表示のみ、commit しない"""
        mock_args.dry_run = True
        dev = MagicMock()
        mock_cu = MagicMock()
        mock_cu.diff.return_value = "[edit]\n+  set system ..."
        with (
            patch("junos_ops.upgrade.Config", return_value=mock_cu),
            patch.object(common, "load_commands", return_value=["set system ntp"]),
        ):
            result = junos_upgrade.load_config("test-host", dev, "commands.set")
        assert result is False
        mock_cu.pdiff.assert_called_once()
        mock_cu.commit.assert_not_called()
        mock_cu.rollback.assert_called_once()
        mock_cu.unlock.assert_called_once()

    def test_commit_check_fail(self, junos_upgrade, mock_args, mock_config):
        """commit_check 失敗 → rollback + unlock"""
        dev = MagicMock()
        mock_cu = MagicMock()
        mock_cu.diff.return_value = "[edit]\n+  set system ..."
        mock_cu.commit_check.side_effect = Exception("commit check failed")
        with (
            patch("junos_ops.upgrade.Config", return_value=mock_cu),
            patch.object(common, "load_commands", return_value=["set system ntp"]),
        ):
            result = junos_upgrade.load_config("test-host", dev, "commands.set")
        assert result is True
        mock_cu.rollback.assert_called_once()
        mock_cu.unlock.assert_called_once()
        mock_cu.commit.assert_not_called()

    def test_commit_fail(self, junos_upgrade, mock_args, mock_config):
        """commit 失敗 → rollback + unlock"""
        dev = MagicMock()
        mock_cu = MagicMock()
        mock_cu.diff.return_value = "[edit]\n+  set system ..."
        mock_cu.commit.side_effect = Exception("commit failed")
        with (
            patch("junos_ops.upgrade.Config", return_value=mock_cu),
            patch.object(common, "load_commands", return_value=["set system ntp"]),
        ):
            result = junos_upgrade.load_config("test-host", dev, "commands.set")
        assert result is True
        mock_cu.rollback.assert_called_once()
        mock_cu.unlock.assert_called_once()

    def test_load_error(self, junos_upgrade, mock_args, mock_config):
        """ファイル読み込みエラー → rollback + unlock"""
        dev = MagicMock()
        mock_cu = MagicMock()
        mock_cu.load.side_effect = Exception("file not found")
        with (
            patch("junos_ops.upgrade.Config", return_value=mock_cu),
            patch.object(common, "load_commands", return_value=["set system ntp"]),
        ):
            result = junos_upgrade.load_config("test-host", dev, "commands.set")
        assert result is True
        mock_cu.rollback.assert_called_once()
        mock_cu.unlock.assert_called_once()
        mock_cu.commit.assert_not_called()

    def test_lock_error(self, junos_upgrade, mock_args, mock_config):
        """ロック取得失敗"""
        dev = MagicMock()
        mock_cu = MagicMock()
        mock_cu.lock.side_effect = Exception("lock failed")
        with patch("junos_ops.upgrade.Config", return_value=mock_cu):
            result = junos_upgrade.load_config("test-host", dev, "commands.set")
        assert result is True
        mock_cu.load.assert_not_called()
        mock_cu.commit.assert_not_called()

    def test_custom_confirm_timeout(self, junos_upgrade, mock_args, mock_config):
        """confirm_timeout カスタム値"""
        mock_args.confirm_timeout = 3
        dev = MagicMock()
        mock_cu = MagicMock()
        mock_cu.diff.return_value = "[edit]\n+  set system ..."
        with (
            patch("junos_ops.upgrade.Config", return_value=mock_cu),
            patch.object(common, "load_commands", return_value=["set system ntp"]),
        ):
            result = junos_upgrade.load_config("test-host", dev, "commands.set")
        assert result is False
        mock_cu.commit.assert_any_call(confirm=3)


class TestConfigCommentStripping:
    """config -f のコメント行・空行除去テスト"""

    def test_config_comments_stripped(self, junos_upgrade, mock_args, mock_config):
        """# コメント行が除去されて cu.load() に文字列で渡される"""
        dev = MagicMock()
        mock_cu = MagicMock()
        mock_cu.diff.return_value = "[edit]\n+  set system ..."
        with (
            patch("junos_ops.upgrade.Config", return_value=mock_cu),
            patch.object(
                common, "load_commands",
                return_value=[
                    "set system host-name test",
                    "set system ntp server 10.0.0.1",
                ],
            ) as mock_load_cmds,
        ):
            result = junos_upgrade.load_config("test-host", dev, "commands.set")

        assert result is False
        # load_commands がファイルパスで呼ばれている
        mock_load_cmds.assert_called_once_with("commands.set")
        # cu.load() に文字列が渡されている（path= ではない）
        mock_cu.load.assert_called_once_with(
            "set system host-name test\nset system ntp server 10.0.0.1",
            format="set",
        )

    def test_config_blank_lines_stripped(self, junos_upgrade, mock_args, mock_config):
        """空行が除去される（load_commands の責務だが統合確認）"""
        dev = MagicMock()
        mock_cu = MagicMock()
        mock_cu.diff.return_value = "[edit]\n+  set system ..."
        with (
            patch("junos_ops.upgrade.Config", return_value=mock_cu),
            patch.object(
                common, "load_commands",
                return_value=["set system host-name test"],
            ),
        ):
            result = junos_upgrade.load_config("test-host", dev, "commands.set")

        assert result is False
        mock_cu.load.assert_called_once_with(
            "set system host-name test", format="set",
        )
