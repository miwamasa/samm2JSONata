# 配列（Collection）の処理

## 概要

SAMMモデルにおける配列（Collection, Set, List等）の処理について説明します。

## 対応状況

### ✅ 対応済み

#### 1. 配列→単一要素のマッピング

**ソース**: 配列内のプロパティ
**ターゲット**: 単一プロパティ
**動作**: 配列の最初の要素（`[0]`）を取得

**例**:
```jsonata
{
  "purchaseOrder": "$.attestationOfConformance[0].attestationType"
}
```

**入力**:
```json
{
  "attestationOfConformance": [
    { "attestationType": "Type 1" },
    { "attestationType": "Type 2" },
    { "attestationType": "Type 3" }
  ]
}
```

**出力**:
```json
{
  "purchaseOrder": "Type 1"
}
```

#### 2. 配列→配列のマッピング（フラット）

**ソース**: 配列内のプロパティ
**ターゲット**: 配列内のプロパティ
**動作**: 全要素を配列として取得

**例**:
```jsonata
{
  "records": {
    "recordName": "$.items.itemName",
    "recordValue": "$.items.itemValue"
  }
}
```

**入力**:
```json
{
  "items": [
    { "itemName": "Item 1", "itemValue": "Value 1" },
    { "itemName": "Item 2", "itemValue": "Value 2" }
  ]
}
```

**出力**:
```json
{
  "records": {
    "recordName": ["Item 1", "Item 2"],
    "recordValue": ["Value 1", "Value 2"]
  }
}
```

### ⚠️ 制限事項

#### 配列内オブジェクトの構造保持

現在の実装では、配列内の複数プロパティをマッピングする際、オブジェクト構造が保持されません。

**期待される動作**:
```json
{
  "records": [
    { "recordName": "Item 1", "recordValue": "Value 1" },
    { "recordName": "Item 2", "recordValue": "Value 2" }
  ]
}
```

**現在の動作**:
```json
{
  "records": {
    "recordName": ["Item 1", "Item 2"],
    "recordValue": ["Value 1", "Value 2"]
  }
}
```

この問題を解決するには、JSONataのオブジェクト変換構文が必要です：
```jsonata
{
  "records": $.items.{
    "recordName": itemName,
    "recordValue": itemValue
  }
}
```

この機能は将来のバージョンで実装予定です。

## 実装詳細

### パーサー（parser.py）

`is_collection`フラグで配列プロパティを識別：
- Collection
- Set
- List
- SortedSet
- TimeSeries

`is_array_element`フラグで配列内のプロパティをマーク。

### トランスフォーマー（transformer.py）

配列マッピングのロジック：

```python
if source_prop.is_array_element and source_prop.parent_property:
    if not target_prop.is_array_element:
        # Array to single: take first element
        source_path = "parent[0].child"
    # else: both are array elements, map entire arrays
```

### Apply処理（apply_transformation.py）

配列アクセスのサポート：
- `$.array[0].field` - インデックス指定
- `$.array.field` - 全要素マッピング（配列を返す）

## テスト結果

### テストケース1: 複数要素配列→単一

**ソース**: `test/pcf/Pcf_multiarray.json`
**結果**: ✅ 成功

```json
"attestationOfConformance": [
  { "attestationType": "Type 1", ... },
  { "attestationType": "Type 2", ... },
  { "attestationType": "Type 3", ... }
]
```

↓

```json
"purchaseOrder": "Type 1"
```

最初の要素のみが正しく取得されました。

### テストケース2: 配列→配列

**ソース**: `test/array_test/source_data.json`
**結果**: ✅ 部分的成功

全要素が変換されましたが、構造が変わりました（上記の制限事項を参照）。

## 回避策

配列内オブジェクトの構造を保持する必要がある場合：

### 方法1: カスタムJSONata式を手動で記述

生成された`transformation.jsonata`を編集：

```jsonata
{
  "records": $.items.{
    "recordName": itemName,
    "recordValue": itemValue
  }
}
```

### 方法2: 後処理スクリプト

変換後にPythonスクリプトで配列を再構築：

```python
def restructure_arrays(data):
    # recordName配列とrecordValue配列を組み合わせる
    names = data["records"]["recordName"]
    values = data["records"]["recordValue"]

    data["records"] = [
        {"recordName": n, "recordValue": v}
        for n, v in zip(names, values)
    ]
    return data
```

## 今後の改善予定

1. **配列内オブジェクト変換の自動生成**
   - JSONataのオブジェクト変換構文（`{}`）を使用
   - ネストした配列構造を保持

2. **配列マッピングのより詳細な制御**
   - フィルタリング（条件付き要素選択）
   - ソート
   - 集約（sum, count等）

3. **複雑な配列変換**
   - 配列の結合
   - 配列の分割
   - クロス積

## 関連ファイル

- `src/models.py` - `is_collection`, `is_array_element`フラグ
- `src/parser.py` - 配列検出ロジック
- `src/transformer.py` - 配列マッピング式生成
- `src/apply_transformation.py` - 配列アクセス処理
- `test/array_test/` - 配列変換のテストケース

---

最終更新: 2025-10-08
