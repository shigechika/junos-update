# コードレビュー Issue 一覧

`junos-update` スクリプトのコードレビューで発見された問題点。
各セクションを GitHub Issue として登録する。

---

## Issue 1: [Bug] get_pending_version() で NameError — 例外変数 err が未定義

**重要度:** 高

### 概要

`get_pending_version()` 関数内の2箇所の `except` ブロックで、キャッチした例外変数 `e` ではなく未定義の `err` を参照しており、例外発生時に `NameError` が二重に発生する。

### 該当箇所

**714行目** （SRX_MIDRANGE/SRX_HIGHEND の内側の except）:
```python
except Exception as e:
    print(err)  # NameError: 'err' is not defined
    sys.exit(1)
```

**726行目** （外側の except）:
```python
except Exception as e:
    print(err)  # NameError: 'err' is not defined
    sys.exit(1)
```

### 修正案

両箇所とも `print(err)` → `print(e)` に修正する。

### 影響

SRX1500/SRX4600 でインストールログの取得中に例外が発生した場合、本来のエラーメッセージが表示されず `NameError` でクラッシュする。外側の例外ハンドラも同様の問題があるため、すべての `personality` タイプで影響を受ける。

---

## Issue 2: [Bug] f-string プレフィックス f の欠落（2箇所）

**重要度:** 中

### 概要

f-string を意図しているが `f` プレフィックスが欠落しているため、変数が展開されず文字列リテラルとしてそのまま出力される箇所が2つある。

### 該当箇所

**253行目** — `clear_reboot()`:
```python
logger.debug("{rpc=} {str=}")
```
`rpc` と `str` の値がログに展開されない。

**修正:** `logger.debug(f"{rpc=} {str=}")`

**989行目** — `main()`:
```python
logger.debug("f{targets=}")
```
`f` が文字列の中に入ってしまっている。ログに `f{targets=}` とリテラル出力される。

**修正:** `logger.debug(f"{targets=}")`

### 影響

デバッグ時にログメッセージに実際の値が表示されず、トラブルシューティングが困難になる。

---

## Issue 3: [Bug] logging.ini がリポジトリに含まれていない

**重要度:** 高

### 概要

スクリプト起動時に `config.fileConfig("logging.ini")` (43行目) が呼ばれるが、`logging.ini` ファイルがリポジトリに含まれていないため、クローン直後に実行すると `FileNotFoundError` で即座にクラッシュする。

### 修正案

以下のいずれかを検討：

1. サンプルの `logging.ini` をリポジトリに追加する
2. `logging.ini` が存在しない場合のフォールバック設定を追加する（例: `logging.basicConfig()`）
3. `logging.ini.example` を追加し、README にコピー手順を記載する

### 影響

新規ユーザがクローン直後にスクリプトを実行できない。

---

## Issue 4: [Bug] reboot() で dev.open() の二重呼出し

**重要度:** 中

### 概要

`reboot()` 関数（827行目）で `dev.open()` を呼んでいるが、`main()` の `connect()` で既にデバイスはオープンされている。

### 該当箇所

```python
def reboot(hostname: str, dev, reboot_dt: datetime.datetime):
    logger.debug(f"{reboot_dt=}")
    try:
        dev.open()  # ← connect() で既に open() 済み
```

### 修正案

827行目の `dev.open()` を削除するか、`reboot()` が独立して呼ばれる場合を考慮してガード条件を追加する。

---

## Issue 5: [Bug] 空レシピファイルが debug モード以外で検出されない

**重要度:** 中

### 概要

`read_config()` 関数（55-58行目）で、レシピファイルが空かどうかのチェックが `args.debug` フラグの中にネストされている。

### 該当箇所

```python
if args.debug:
    if len(config.sections()) == 0:
        print(args.recipe, "is empty")
        return True
```

### 修正案

空チェックを `args.debug` の外に出す：
```python
if len(config.sections()) == 0:
    print(args.recipe, "is empty")
    return True
```

### 影響

`--debug` なしで空のレシピファイルを指定すると、エラーにならず0ホストで無言終了する。

---

## Issue 6: [Bug] compare_version() の型注釈が不正

**重要度:** 低

### 概要

`compare_version()` の戻り値型注釈 `-> None or int` は Python では `-> int` と評価される（`None` は falsy のため `None or int` は `int` を返す）。

### 該当箇所

```python
def compare_version(left : str, right : str) -> None or int:
```

### 修正案

```python
from typing import Optional

def compare_version(left: str, right: str) -> Optional[int]:
```

---

## Issue 7: [改善] Python 組み込み名のシャドウイング

**重要度:** 低

### 概要

複数の関数で Python 組み込み名を変数名として使用しており、シャドウイングが発生している。

### 該当箇所

- `str = etree.tostring(...)` — 142, 216, 252, 621, 683, 760, 836行目
- `dict = fs.ls(...)` — 513行目
- `hash = get_model_hash(...)` — 438, 476行目

### 修正案

- `str` → `xml_str` や `result_str` など
- `dict` → `dir_info` など
- `hash` → `pkg_hash` など

---

## Issue 8: [Bug] タイポ修正

**重要度:** 低

### 該当箇所

- **163行目:** `"cheksum"` → `"checksum"`
- **742行目:** 関数名 `get_reboot_infomation` → `get_reboot_information`（815行目の呼び出し側も修正が必要）
