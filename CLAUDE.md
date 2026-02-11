# CLAUDE.md

このファイルはClaude Codeがリポジトリを理解するためのコンテキストを提供します。

## プロジェクト概要

junos-opsは、Juniper Networksデバイスの運用を自動化するPythonツールです。デバイスモデルの自動検出、JUNOSパッケージの自動更新、ロールバック、リブートスケジュール管理をNETCONF/SSH経由で行います。

## 技術スタック

- **言語:** Python 3（3.12以上）
- **主要ライブラリ:** junos-eznc（PyEZ）— Juniper公式のPython自動化ライブラリ
- **プロトコル:** NETCONF（ポート830）、SCP（ファイル転送）
- **パッケージ管理:** pyproject.toml（pip installable）
- **テスト:** pytest + モック
- **CI:** GitHub Actions（Python 3.12/3.13 マトリクス）
- **ライセンス:** Apache License 2.0

## ファイル構成

```
junos_ops/
├── __init__.py     # パッケージ定義、__version__
├── __main__.py     # python -m junos_ops 対応
└── cli.py          # メインロジック（全関数）
tests/
├── conftest.py     # pytest フィクスチャ
├── test_version.py
├── test_config.py
├── test_connect.py
└── test_process_host.py
pyproject.toml      # パッケージメタデータ、エントリポイント
config.ini          # 設定ファイル（設定例）
logging.ini         # ロギング設定
README.md
LICENSE
```

## 開発環境セットアップ

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
```

## 設定ファイル（config.ini）の構造

INI形式の設定ファイル。configparserで読み込む。
探索順: `--config`指定 → `./config.ini` → `~/.config/junos-ops/config.ini`

### DEFAULTセクション

グローバルな接続情報とモデル別パッケージ定義を記述する。

```ini
[DEFAULT]
id = exadmin          # SSHユーザ名
pw = password         # SSHパスワード
sshkey = id_ed25519   # SSH秘密鍵ファイル
port = 830            # NETCONFポート
hashalgo = md5        # チェックサムアルゴリズム
rpath = /var/tmp      # リモートパス
```

### モデル→パッケージマッピング

DEFAULTセクション内に`モデル名.file`と`モデル名.hash`のペアで定義する。モデル名はデバイスから自動取得される`model`フィールドと一致させる。

```ini
EX2300-24T.file = junos-arm-32-18.4R3-S10.tgz
EX2300-24T.hash = e233b31a0b9233bc4c56e89954839a8a
```

### ホストセクション

セクション名がホスト名となる。DEFAULTの値をホスト単位でオーバーライドできる。`host`キーを指定しない場合、セクション名がそのまま接続先ホスト名として使用される。

```ini
[rt1.example.jp]           # hostキー省略 → rt1.example.jpに接続
[rt2.example.jp]
host = 192.0.2.1           # IPアドレスでオーバーライド
```

ホストセクション内でモデル→パッケージマッピングをオーバーライドすることも可能（特定ホストだけ異なるバージョンにする場合など）。

## コードの主要構成

`junos_ops/cli.py` に全関数が集約されている。

- **接続管理:** `connect()` — NETCONF接続（認証エラー、タイムアウト等の個別例外処理あり）
- **パッケージ転送:** `copy()` — SCP転送＋チェックサム検証、ストレージクリーンアップ
- **インストール:** `install()` — パッケージ検証・インストール（pre/postフライトチェック）
- **ロールバック:** `rollback()` — 前バージョンへの復帰（MX/EX/SRXモデル別処理あり）
- **リブート:** `reboot()` — スケジュールリブートまたは即時リブート
- **ホスト処理:** `process_host()` — 単一ホストの全処理（ThreadPoolExecutor対応済み）
- **バージョン管理:** `get_pending_version()`, `get_planning_version()`, `compare_version()`
- **設定読込:** `read_config()` — config.iniの解析（XDG対応）
- **ドライラン:** `dry_run()` — 実行せずに操作内容を表示

## テスト

```bash
pytest tests/ -v --tb=short
```

45テスト（バージョン比較、設定読込、接続モック、process_host統合テスト、スレッド安全性）。

## 既知の注意事項

- グローバル変数`config`が`logging.config`と`configparser`の両方で使われており、モジュール読込時に`config.fileConfig()`呼出し後に`config = None`で上書きされる
- `args`と`config`はグローバル変数として管理される
- `config`への書き込みは`config_lock`（threading.Lock）で保護済み
