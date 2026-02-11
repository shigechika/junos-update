"""設定読込・モデル取得・ハッシュキャッシュのテスト"""

import configparser
import threading

import pytest


class TestReadConfig:
    """read_config() のテスト"""

    def test_valid_recipe(self, junos_update, mock_args, tmp_path):
        """正常なINIファイルを読み込める"""
        recipe = tmp_path / "test.ini"
        recipe.write_text(
            "[DEFAULT]\n"
            "id = testuser\n"
            "port = 830\n"
            "\n"
            "[host1.example.jp]\n"
            "\n"
            "[host2.example.jp]\n"
            "host = 192.0.2.1\n"
        )
        junos_update.args.recipe = str(recipe)
        result = junos_update.read_config()
        assert result is False
        assert junos_update.config.has_section("host1.example.jp")
        assert junos_update.config.has_section("host2.example.jp")

    def test_empty_recipe(self, junos_update, mock_args, tmp_path):
        """空のINIファイルはエラー（True）を返す"""
        recipe = tmp_path / "empty.ini"
        recipe.write_text("")
        junos_update.args.recipe = str(recipe)
        result = junos_update.read_config()
        assert result is True

    def test_host_default_to_section_name(self, junos_update, mock_args, tmp_path):
        """hostキー省略時にセクション名がhostとして設定される"""
        recipe = tmp_path / "test.ini"
        recipe.write_text(
            "[DEFAULT]\nid = testuser\nport = 830\n\n"
            "[rt1.example.jp]\n"
        )
        junos_update.args.recipe = str(recipe)
        junos_update.read_config()
        assert junos_update.config.get("rt1.example.jp", "host") == "rt1.example.jp"

    def test_host_override(self, junos_update, mock_args, tmp_path):
        """hostキー指定時はその値が使われる"""
        recipe = tmp_path / "test.ini"
        recipe.write_text(
            "[DEFAULT]\nid = testuser\nport = 830\n\n"
            "[rt2.example.jp]\n"
            "host = 192.0.2.1\n"
        )
        junos_update.args.recipe = str(recipe)
        junos_update.read_config()
        assert junos_update.config.get("rt2.example.jp", "host") == "192.0.2.1"


class TestGetModelFile:
    """get_model_file() のテスト"""

    def test_found(self, junos_update, mock_config):
        result = junos_update.get_model_file("test-host", "EX2300-24T")
        assert result == "junos-arm-32-22.4R3-S6.5.tgz"

    def test_not_found(self, junos_update, mock_config):
        """存在しないモデルは例外を raise"""
        with pytest.raises(configparser.NoOptionError):
            junos_update.get_model_file("test-host", "UNKNOWN_MODEL")

    def test_case_insensitive(self, junos_update, mock_config):
        """モデル名は小文字に変換される"""
        result = junos_update.get_model_file("test-host", "ex2300-24t")
        assert result == "junos-arm-32-22.4R3-S6.5.tgz"


class TestGetModelHash:
    """get_model_hash() のテスト"""

    def test_found(self, junos_update, mock_config):
        result = junos_update.get_model_hash("test-host", "EX2300-24T")
        assert result == "abc123def456"

    def test_not_found(self, junos_update, mock_config):
        """存在しないモデルは例外を raise"""
        with pytest.raises(configparser.NoOptionError):
            junos_update.get_model_hash("test-host", "UNKNOWN_MODEL")


class TestHashcache:
    """get_hashcache() / set_hashcache() のテスト"""

    def test_set_and_get(self, junos_update, mock_config):
        junos_update.set_hashcache("test-host", "testfile.tgz", "hash123")
        result = junos_update.get_hashcache("test-host", "testfile.tgz")
        assert result == "hash123"

    def test_get_nonexistent_section(self, junos_update, mock_config):
        """存在しないセクションは None を返す"""
        result = junos_update.get_hashcache("nonexistent-host", "file.tgz")
        assert result is None

    def test_get_nonexistent_option(self, junos_update, mock_config):
        """存在しないオプションは None を返す"""
        result = junos_update.get_hashcache("test-host", "nofile.tgz")
        assert result is None

    def test_set_creates_section(self, junos_update, mock_config):
        """存在しないセクションは自動作成される"""
        junos_update.set_hashcache("new-host", "file.tgz", "hash456")
        result = junos_update.get_hashcache("new-host", "file.tgz")
        assert result == "hash456"

    def test_thread_safety(self, junos_update, mock_config):
        """複数スレッドからの同時アクセスでデータが壊れない"""
        errors = []

        def worker(host_id):
            try:
                host = f"thread-host-{host_id}"
                for i in range(50):
                    junos_update.set_hashcache(host, "file.tgz", f"hash-{host_id}-{i}")
                    val = junos_update.get_hashcache(host, "file.tgz")
                    if val is None:
                        errors.append(f"{host}: got None")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread safety errors: {errors}"
