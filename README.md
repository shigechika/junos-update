# junos-ops

Juniperデバイスのモデルを自動検出し、JUNOSパッケージを自動更新するツールです。

## 特徴

- デバイスモデルの自動検出とパッケージの自動マッピング
- SCP転送＋チェックサム検証による安全なパッケージコピー
- インストール前のパッケージ検証（validate）
- ロールバック対応（MX/EX/SRXモデル別処理）
- スケジュールリブート（`--rebootat`）
- ドライランモード（`--dry-run`）で事前確認
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
junos-ops [-h] [-c CONFIG] [--list] [--longlist] [-n] [--dry-run]
             [--copy] [--install] [--update] [--force] [--showversion]
             [--rollback] [--rebootat REBOOTAT] [-d] [-V]
             [hostname ...]
```

### オプション一覧

| オプション | 説明 |
|-----------|------|
| `hostname` | 対象ホスト名（省略時は設定ファイル内の全ホスト） |
| `-c`, `--config CONFIG` | 設定ファイル指定（デフォルト: `config.ini` → `~/.config/junos-ops/config.ini`） |
| `--copy` | ローカルからリモートへパッケージをコピー |
| `--install` | コピー済みパッケージをインストール |
| `--update`, `--upgrade` | コピー＋インストールを一括実行 |
| `--force` | 条件を無視して強制実行 |
| `--showversion`, `--version` | running/planning/pendingバージョンとリブート予定を表示 |
| `--rollback` | 前バージョンにロールバック |
| `--rebootat YYMMDDHHMM` | 指定日時にリブートをスケジュール（例: `2501020304`） |
| `--list`, `-ls` | リモートパスのファイル一覧（短縮表示） |
| `--longlist`, `-ll` | リモートパスのファイル一覧（詳細表示） |
| `-n`, `--dry-run` | テスト実行（接続とメッセージ出力のみ、実行しない） |
| `-d`, `--debug` | デバッグ出力 |
| `-V` | プログラムバージョン表示 |

引数なしで実行するとデバイスファクト（device facts）を表示します。

## ワークフロー

JUNOSアップデートの典型的な作業フローです。

```
1. --dry-run で事前確認
   junos-ops --update --dry-run hostname

2. --update でコピー＋インストール（--copy + --install）
   junos-ops --update hostname

3. --showversion でバージョン確認
   junos-ops --showversion hostname

4. --rebootat でリブート日時を指定
   junos-ops --rebootat 2506130500 hostname
```

問題が発生した場合は `--rollback` で前バージョンに戻せます。

## 実行例

### --update（パッケージ更新）

```
% junos-ops --update rt1.example.jp
[rt1.example.jp]
remote: jinstall-ppc-18.4R3-S10-signed.tgz is not found.
copy: system storage cleanup successful
rt1.example.jp: cleaning filesystem ...
rt1.example.jp: before copy, computing checksum on remote package: /var/tmp/jinstall-ppc-18.4R3-S10-signed.tgz
rt1.example.jp: b'jinstall-ppc-18.4R3-S10-signed.tgz': 38010880 / 380102074 (10%)
...
rt1.example.jp: b'jinstall-ppc-18.4R3-S10-signed.tgz': 380102074 / 380102074 (100%)
rt1.example.jp: after copy, computing checksum on remote package: /var/tmp/jinstall-ppc-18.4R3-S10-signed.tgz
rt1.example.jp: checksum check passed.
install: clear reboot schedule successful
install: rescue config save suecessful
rt1.example.jp: validating software against current config, please be patient ...
rt1.example.jp: software validate package-result: 0
```

### --showversion（バージョン確認）

```
% junos-ops --showversion
[rt1.example.jp]
hostname: rt1
model: MX5-T
running version: 18.4R3-S7.2
planning version: 18.4R3-S10
 	running version seems older than planning version.
	pending version: 18.4R3-S10
running version seems older than pending version. Please plan to reboot.
local package: jinstall-ppc-18.4R3-S10-signed.tgz is found. checksum is OK.
remote package: jinstall-ppc-18.4R3-S10-signed.tgz is found. checksum is OK.
reboot requested by exadmin at Sat Dec  4 05:00:00 2021

[rt2.example.jp]
hostname: rt2
model: EX3400-24T
running version: 18.4R3-S9.2
planning version: 18.4R3-S10
	running version seems older than planning version.
pending version: 18.4R3-S10
	running version seems older than pending version. Please plan to reboot.
local package: junos-arm-32-18.4R3-S10.tgz is found. checksum is OK.
remote package: junos-arm-32-18.4R3-S10.tgz is not found.
reboot requested by exadmin at Wed Dec  8 01:00:00 2021
```

### --dry-run（テスト実行）

```
% junos-ops --update --dry-run srx.example.jp
[srx.example.jp]
remote package: junos-srxentedge-x86-64-18.4R3-S9.2.tgz is not found.
dry-run: request system storage cleanup
dry-run: scp(cheksum:md5) junos-srxentedge-x86-64-18.4R3-S9.2.tgz srx.example.jp:/var/tmp
dry-run: clear system reboot
dry-run: request system configuration rescue save
dry-run: request system software add /var/tmp/junos-srxentedge-x86-64-18.4R3-S9.2.tgz
```

### --rebootat（スケジュールリブート）

```
% junos-ops --rebootat 2506130500 --force
[INFO]main - host='rt1.example.jp'
[INFO]reboot - Shutdown at Fri Jun 13 05:00:00 2025. [pid 97978]

[INFO]main - host='rt2.example.jp'
[INFO]reboot - ANY SHUTDWON/REBOOT SCHEDULE EXISTS
[INFO]reboot - force clear reboot
[INFO]clear_reboot - clear reboot schedule successful
[INFO]reboot - Shutdown at Fri Jun 13 05:00:00 2025. [pid 3321]
```

### 引数なし（デバイスファクト表示）

```
% junos-ops gw1.example.jp
[gw1.example.jp]
{'2RE': True,
 'hostname': 'gw1',
 'model': 'MX240',
 'version': '18.4R3-S7.2',
 'version_RE0': '18.4R3-S7.2',
 'version_RE1': '18.4R3-S7.2',
 ...}
```

## 対応モデル

レシピファイルでモデル名とパッケージファイルを定義することで、任意のJuniperモデルに対応できます。設定例に含まれるモデル:

| シリーズ | モデル例 |
|---------|---------|
| EX | EX2300-24T, EX3400-24T, EX4300-32F |
| MX | MX5-T, MX240 |
| QFX | QFX5110-48S-4C |
| SRX | SRX300, SRX345, SRX1500, SRX4600 |

## License

[Apache License 2.0](LICENSE)

Copyright 2022-2025 AIKAWA Shigechika
