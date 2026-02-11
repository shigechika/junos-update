# CLAUDE.md

このファイルはClaude Codeがリポジトリを理解するためのコンテキストを提供します。

## プロジェクト概要

junos-updateは、Juniper Networksデバイスのモデルを自動検出し、JUNOSパッケージを自動更新するPythonスクリプトです。NETCONF/SSH経由でデバイスに接続し、パッケージのコピー・インストール・ロールバック・リブートスケジュールを管理します。

## 技術スタック

- **言語:** Python 3（3.13対応済み）
- **主要ライブラリ:** junos-eznc（PyEZ）— Juniper公式のPython自動化ライブラリ
- **プロトコル:** NETCONF（ポート830）、SCP（ファイル転送）
- **ライセンス:** Apache License 2.0

## ファイル構成

```
junos-update    # メインスクリプト（単一ファイル構成）
junos.ini       # レシピファイル（設定例）
requirements.txt
README.md
LICENSE
```

## 開発環境セットアップ

```bash
python3 -m venv .venv
. .venv/bin/activate
pip3 install -r requirements.txt
```

## レシピファイル（junos.ini）の構造

INI形式の設定ファイル。configparserで読み込む。

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

メインスクリプト`junos-update`は単一ファイルで、以下の機能群で構成される。

- **接続管理:** `connect()` — NETCONF接続（認証エラー、タイムアウト等の個別例外処理あり）
- **パッケージ転送:** `copy()` — SCP転送＋チェックサム検証、ストレージクリーンアップ
- **インストール:** `install()` — パッケージ検証・インストール（pre/postフライトチェック）
- **ロールバック:** `rollback()` — 前バージョンへの復帰（MX/EX/SRXモデル別処理あり）
- **リブート:** `reboot()` — スケジュールリブートまたは即時リブート
- **バージョン管理:** `get_running_version()`, `get_pending_version()`, `get_planning_version()`, `compare_version()`
- **設定読込:** `read_config()` — junos.iniの解析
- **ドライラン:** `dryrun()` — 実行せずに操作内容を表示

## テスト

フォーマルなテストスイートは存在しない。`--dryrun`オプションが手動テスト手段となる。

```bash
./junos-update --update --dryrun hostname
```

## 既知の注意事項

- `logging.ini`ファイルがスクリプト起動時に必要だが、リポジトリに含まれていない
- グローバル変数`config`が`logging.config`と`configparser`の両方で使われており、43行目で`config.fileConfig()`呼出し後に46行目で`config = None`で上書きされる
- `args`と`config`はグローバル変数として管理される
