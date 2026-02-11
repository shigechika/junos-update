# junos-ops

Juniperデバイスのモデルを自動検出し、JUNOSパッケージを自動更新するツールです。

## 特徴

- デバイスモデルの自動検出とパッケージの自動マッピング
- SCP転送＋チェックサム検証による安全なパッケージコピー
- インストール前のパッケージ検証（validate）
- ロールバック対応（MX/EX/SRXモデル別処理）
- スケジュールリブート
- RSI/SCF の並列収集
- ドライランモード（`--dry-run`）で事前確認
- ThreadPoolExecutor による並列実行
- 設定ファイル（INI形式）によるホスト・パッケージ管理

## 目次

- [インストール](#インストール)
- [設定ファイル（config.ini）](#設定ファイルconfigini)
- [使い方](#使い方)
- [ワークフロー](#ワークフロー)
- [実行例](#実行例)
- [対応モデル](#対応モデル)
- [License](#license)

## インストール

```bash
pip install git+https://github.com/shigechika/junos-ops.git
```

### 開発用インストール

```bash
git clone https://github.com/shigechika/junos-ops.git
cd junos-ops
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
```

### 依存ライブラリ

- [junos-eznc (PyEZ)](https://www.juniper.net/documentation/product/us/en/junos-pyez) — Juniper NETCONF自動化ライブラリ
- [looseversion](https://pypi.org/project/looseversion/) — バージョン比較

### pip3のインストール（未導入の場合）

<details>
<summary>OS別手順</summary>

- **Ubuntu/Debian**
  ```bash
  sudo apt install python3-pip
  ```

- **CentOS/RedHat**
  ```bash
  sudo dnf install python3-pip
  ```

- **macOS**
  ```bash
  brew install python3
  ```

</details>

## 設定ファイル（config.ini）

INI形式の設定ファイルで、接続情報とモデル別パッケージを定義します。

設定ファイルは以下の順序で探索されます（`-c` / `--config` で明示指定も可能）：

1. カレントディレクトリの `./config.ini`
2. `~/.config/junos-ops/config.ini`（XDG_CONFIG_HOME）

### DEFAULTセクション

全ホスト共通の接続設定とモデル→パッケージマッピングを記述します。

```ini
[DEFAULT]
id = exadmin          # SSHユーザ名
pw = password         # SSHパスワード
sshkey = id_ed25519   # SSH秘密鍵ファイル
port = 830            # NETCONFポート
hashalgo = md5        # チェックサムアルゴリズム
rpath = /var/tmp      # リモートパス
# huge_tree = true    # 大きなXMLレスポンスを許可
# RSI_DIR = ./rsi/    # RSI/SCFファイルの出力先

# モデル名.file = パッケージファイル名
# モデル名.hash = チェックサム値
EX2300-24T.file = junos-arm-32-18.4R3-S10.tgz
EX2300-24T.hash = e233b31a0b9233bc4c56e89954839a8a
```

モデル名はデバイスから自動取得される`model`フィールドと一致させます。

### ホストセクション

各セクション名がホスト名になります。DEFAULTの値をホスト単位でオーバーライドできます。

```ini
[rt1.example.jp]             # セクション名がそのまま接続先ホスト名
[rt2.example.jp]
host = 192.0.2.1             # IPアドレスで接続先を指定
[sw1.example.jp]
id = sw1                     # 接続ユーザを変更
sshkey = sw1_rsa             # SSH鍵を変更
[sw2.example.jp]
port = 10830                 # ポートを変更
[sw3.example.jp]
EX4300-32F.file = jinstall-ex-4300-20.4R3.8-signed.tgz   # このホストだけ別バージョン
EX4300-32F.hash = 353a0dbd8ff6a088a593ec246f8de4f4
```

## 使い方

```
junos-ops <subcommand> [options] [hostname ...]
```

### サブコマンド一覧

| サブコマンド | 説明 |
|-------------|------|
| `upgrade` | コピー＋インストールを一括実行 |
| `copy` | ローカルからリモートへパッケージをコピー |
| `install` | コピー済みパッケージをインストール |
| `rollback` | 前バージョンにロールバック |
| `version` | running/planning/pendingバージョンとリブート予定を表示 |
| `reboot --at YYMMDDHHMM` | 指定日時にリブートをスケジュール |
| `ls [-l]` | リモートパスのファイル一覧 |
| `config -f FILE [--confirm N]` | set コマンドファイルを適用 |
| `rsi` | RSI/SCF を並列収集 |
| （なし） | デバイスファクト（device facts）を表示 |

### 共通オプション

| オプション | 説明 |
|-----------|------|
| `hostname` | 対象ホスト名（省略時は設定ファイル内の全ホスト） |
| `-c`, `--config CONFIG` | 設定ファイル指定（デフォルト: `config.ini` → `~/.config/junos-ops/config.ini`） |
| `-n`, `--dry-run` | テスト実行（接続とメッセージ出力のみ、実行しない） |
| `-d`, `--debug` | デバッグ出力 |
| `--force` | 条件を無視して強制実行 |
| `--workers N` | 並列実行数（デフォルト: upgrade系=1, rsi=20） |
| `--version` | プログラムバージョン表示 |

## ワークフロー

JUNOSアップデートの典型的な作業フローです。

```
1. dry-run で事前確認
   junos-ops upgrade -n hostname

2. upgrade でコピー＋インストール
   junos-ops upgrade hostname

3. version でバージョン確認
   junos-ops version hostname

4. reboot でリブート日時を指定
   junos-ops reboot --at 2506130500 hostname
```

問題が発生した場合は `rollback` で前バージョンに戻せます。

### config 適用ワークフロー

```
1. dry-run で差分を確認
   junos-ops config -f commands.set -n hostname

2. 適用
   junos-ops config -f commands.set hostname
```

## 実行例

### upgrade（パッケージ更新）

```
% junos-ops upgrade rt1.example.jp
# rt1.example.jp
remote: jinstall-ppc-18.4R3-S10-signed.tgz is not found.
copy: system storage cleanup successful
rt1.example.jp: cleaning filesystem ...
rt1.example.jp: b'jinstall-ppc-18.4R3-S10-signed.tgz': 380102074 / 380102074 (100%)
rt1.example.jp: checksum check passed.
install: clear reboot schedule successful
install: rescue config save successful
rt1.example.jp: software validate package-result: 0
```

### version（バージョン確認）

```
% junos-ops version rt1.example.jp
# rt1.example.jp
  - hostname: rt1
  - model: MX5-T
  - running version: 18.4R3-S7.2
  - planning version: 18.4R3-S10
    - running='18.4R3-S7.2' < planning='18.4R3-S10'
  - pending version: 18.4R3-S10
    - running='18.4R3-S7.2' < pending='18.4R3-S10' : Please plan to reboot.
  - reboot requested by exadmin at Sat Dec  4 05:00:00 2021
```

### rsi（RSI/SCF並列収集）

```
% junos-ops rsi --workers 5 rt1.example.jp rt2.example.jp
# rt1.example.jp
  rt1.example.jp.SCF done
  rt1.example.jp.RSI done
# rt2.example.jp
  rt2.example.jp.SCF done
  rt2.example.jp.RSI done
```

### reboot（スケジュールリブート）

```
% junos-ops reboot --at 2506130500 rt1.example.jp
# rt1.example.jp
	Shutdown at Fri Jun 13 05:00:00 2025. [pid 97978]
```

### config（set コマンドファイル適用）

set 形式のコマンドファイルを複数デバイスに適用します。commit check → commit confirmed → confirm の安全なコミットフローで実行します。

```
% cat add-user.set
set system login user viewer class read-only
set system login user viewer authentication ssh-ed25519 "ssh-ed25519 AAAA..."

% junos-ops config -f add-user.set -n rt1.example.jp rt2.example.jp
# rt1.example.jp
[edit system login]
+    user viewer {
+        class read-only;
+        authentication {
+            ssh-ed25519 "ssh-ed25519 AAAA...";
+        }
+    }
	dry-run: rollback (no commit)
# rt2.example.jp
	...

% junos-ops config -f add-user.set rt1.example.jp rt2.example.jp
# rt1.example.jp
	...
	commit check passed
	commit confirmed 1 applied
	commit confirmed, changes are now permanent
# rt2.example.jp
	...
```

`--confirm N` で commit confirmed のタイムアウトを変更できます（デフォルト: 1分）。

### 引数なし（デバイスファクト表示）

```
% junos-ops gw1.example.jp
# gw1.example.jp
{'2RE': True,
 'hostname': 'gw1',
 'model': 'MX240',
 'version': '18.4R3-S7.2',
 ...}
```

## 対応モデル

設定ファイルでモデル名とパッケージファイルを定義することで、任意のJuniperモデルに対応できます。設定例に含まれるモデル:

| シリーズ | モデル例 |
|---------|---------|
| EX | EX2300-24T, EX3400-24T, EX4300-32F |
| MX | MX5-T, MX240 |
| QFX | QFX5110-48S-4C |
| SRX | SRX300, SRX345, SRX1500, SRX4600 |

## License

[Apache License 2.0](LICENSE)

Copyright 2022-2025 AIKAWA Shigechika
