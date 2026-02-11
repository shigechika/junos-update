"""connect() のモックテスト"""

from unittest.mock import patch, MagicMock

from jnpr.junos.exception import (
    ConnectAuthError,
    ConnectClosedError,
    ConnectRefusedError,
    ConnectTimeoutError,
    ConnectUnknownHostError,
)


class TestConnect:
    """connect() の接続テスト"""

    def test_success(self, junos_update, mock_args, mock_config):
        """正常接続"""
        with patch.object(junos_update, "Device") as MockDevice:
            mock_dev = MagicMock()
            MockDevice.return_value = mock_dev

            err, dev = junos_update.connect("test-host")

            assert err is False
            assert dev is mock_dev
            mock_dev.open.assert_called_once()

    def test_auth_error(self, junos_update, mock_args, mock_config):
        """認証エラー"""
        with patch.object(junos_update, "Device") as MockDevice:
            mock_dev = MagicMock()
            MockDevice.return_value = mock_dev
            mock_dev.open.side_effect = ConnectAuthError(mock_dev)

            err, dev = junos_update.connect("test-host")

            assert err is True
            assert dev is None

    def test_timeout_error(self, junos_update, mock_args, mock_config):
        """接続タイムアウト"""
        with patch.object(junos_update, "Device") as MockDevice:
            mock_dev = MagicMock()
            MockDevice.return_value = mock_dev
            mock_dev.open.side_effect = ConnectTimeoutError(mock_dev)

            err, dev = junos_update.connect("test-host")

            assert err is True
            assert dev is None

    def test_refused_error(self, junos_update, mock_args, mock_config):
        """接続拒否"""
        with patch.object(junos_update, "Device") as MockDevice:
            mock_dev = MagicMock()
            MockDevice.return_value = mock_dev
            mock_dev.open.side_effect = ConnectRefusedError(mock_dev)

            err, dev = junos_update.connect("test-host")

            assert err is True
            assert dev is None

    def test_unknown_host_error(self, junos_update, mock_args, mock_config):
        """不明なホスト"""
        with patch.object(junos_update, "Device") as MockDevice:
            mock_dev = MagicMock()
            MockDevice.return_value = mock_dev
            mock_dev.open.side_effect = ConnectUnknownHostError(mock_dev)

            err, dev = junos_update.connect("test-host")

            assert err is True
            assert dev is None

    def test_generic_exception(self, junos_update, mock_args, mock_config):
        """その他の例外"""
        with patch.object(junos_update, "Device") as MockDevice:
            mock_dev = MagicMock()
            MockDevice.return_value = mock_dev
            mock_dev.open.side_effect = Exception("unexpected error")

            err, dev = junos_update.connect("test-host")

            assert err is True
            assert dev is None
