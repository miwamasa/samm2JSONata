# SAMM to JSONata 変換システム - 理論と実装

## 目次

1. [概要](#概要)
2. [基本理論](#基本理論)
3. [SAMMモデルの構造](#sammモデルの構造)
4. [マッピング理論](#マッピング理論)
5. [実装アーキテクチャ](#実装アーキテクチャ)
6. [変換アルゴリズム](#変換アルゴリズム)
7. [具体例](#具体例)
8. [拡張性](#拡張性)

---

## 概要

本システムは、SAMM (Semantic Aspect Meta Model) で定義された2つのモデル間で、JSONインスタンスデータを変換するためのJSONata式を自動生成します。

### システムの目的

- **セマンティックな一貫性**: SAMMの意味情報を活用した正確なマッピング
- **自動化**: 手動でのマッピング定義を最小化
- **検証可能性**: 生成されたルールの信頼度と妥当性の評価
- **実行可能性**: 標準的なJSONataエンジンで実行可能な式の生成

---

## 基本理論

### 1. セマンティックモデルとデータインスタンスの分離

```
┌─────────────────┐              ┌─────────────────┐
│  SAMM Model     │              │  JSON Instance  │
│  (構造定義)      │  ─────→      │  (実データ)      │
│                 │              │                 │
│ - Aspect        │              │ { "id": "123",  │
│ - Entity        │              │   "pcf": {      │
│ - Property      │              │     "value": 1  │
│ - Characteristic│              │   }             │
└─────────────────┘              └─────────────────┘
```

**原則**:
- モデルは「型」、インスタンスは「値」
- モデル間のマッピング = インスタンス間の変換ルール
- セマンティック情報（preferredName, description等）を活用したマッチング

### 2. 変換の数学的定義

ソースモデル **S** からターゲットモデル **T** への変換関数 **f**:

```
f: Instance(S) → Instance(T)
```

この関数は以下の性質を満たす：

1. **構造保存**: S の階層構造を T の階層構造にマッピング
2. **型安全性**: データ型の互換性を保証
3. **意味保存**: セマンティック情報の損失を最小化

---

## SAMMモデルの構造

### 1. 基本要素

```turtle
:Pcf a samm:Aspect ;
    samm:properties (
        :id          # トップレベルプロパティ
        :pcf         # Entityを参照するプロパティ
        ...
    ) .

:pcf a samm:Property ;
    samm:characteristic :CarbonFootprint .

:CarbonFootprint a samm-c:SingleEntity ;
    samm:dataType :PcfEntity .

:PcfEntity a samm:Entity ;
    samm:properties (
        :declaredUnitOfMeasurement
        :declaredUnitAmount
        ...
    ) .
```

### 2. 階層構造とJSONマッピング

**SAMMの階層**:
```
Aspect
  └─ Property (pcf)
       └─ Characteristic (SingleEntity)
            └─ Entity (PcfEntity)
                 └─ Property (declaredUnitOfMeasurement)
                      └─ payloadName: "declaredUnitOfMeasurement"
```

**対応するJSON構造**:
```json
{
  "pcf": {
    "declaredUnitOfMeasurement": "liter"
  }
}
```

### 3. 重要な属性

| 属性 | 役割 | 例 |
|------|------|-----|
| `samm:preferredName` | 人間可読な名前 | "Unit of measurement" |
| `samm:payloadName` | JSONでのキー名 | "declaredUnitOfMeasurement" |
| `samm:characteristic` | プロパティの意味的特性 | `:CarbonFootprint` |
| `samm:dataType` | データ型（Entity or XSD型） | `:PcfEntity` or `xsd:string` |
| `samm:optional` | 必須/オプション | `true`/`false` |

---

## マッピング理論

### 1. マッチング戦略の優先順位

```
Level 1: Explicit Mapping (明示的定義)
   ↓ (confidence: 1.0)
Level 2: Characteristic Match (特性URI一致)
   ↓ (confidence: 0.9)
Level 3: PreferredName Match (名前の正規化後一致)
   ↓ (confidence: 0.8)
Level 4: Property URI Match (ローカル名一致)
   ↓ (confidence: 0.7)
Level 5: Semantic Similarity (意味的類似度)
   ↓ (confidence: 0.6-0.7)
No Match
   (confidence: 0.0)
```

### 2. Characteristic Matchの理論的根拠

SAMMでは、Characteristicがプロパティの**意味的役割**を定義します。

```turtle
# Source
:sourceSpeed a samm:Property ;
    samm:characteristic samm-c:Measurement ;
    samm-c:unit unit:kilometrePerHour .

# Target
:targetSpeed a samm:Property ;
    samm:characteristic samm-c:Measurement ;
    samm-c:unit unit:metrePerSecond .
```

同じCharacteristic（`samm-c:Measurement`）を持つため、**意味的に同等**と判断できる。
さらに、単位情報から換算係数を計算可能。

### 3. PreferredName Matchの正規化

```python
def normalize(name: str) -> str:
    """
    名前を正規化して比較可能にする

    例:
    "Product (Carbon) Footprint" → "productcarbonfootprint"
    "Product Carbon Footprint"   → "productcarbonfootprint"
    "PCF"                        → "pcf"
    """
    # 1. 小文字化
    name = name.lower()
    # 2. 括弧と内容を削除
    name = re.sub(r'\([^)]*\)', '', name)
    # 3. 特殊文字と空白を削除
    name = re.sub(r'[^a-z0-9]', '', name)
    return name
```

### 4. 信頼度の計算

各マッチング方法には信頼度スコアが割り当てられています：

```python
confidence = {
    "characteristic_match": 0.9,    # 高い意味的確実性
    "preferred_name_match": 0.8,    # 中程度の確実性
    "property_uri_match": 0.7,      # やや低い確実性
}
```

信頼度閾値（デフォルト: 0.6）を下回るマッチングは採用されません。

---

## 実装アーキテクチャ

### 1. システム全体図

```
┌──────────────────────────────────────────────────────────┐
│                    Generator (Main)                       │
└──────────────────────────────────────────────────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
    ┌───────────────┐    ┌───────────────┐    ┌──────────────┐
    │    Parser     │    │    Matcher    │    │ Transformer  │
    │               │    │               │    │              │
    │ - Parse TTL   │    │ - Match props │    │ - Detect     │
    │ - Extract     │    │ - Calculate   │    │   transform  │
    │   properties  │    │   confidence  │    │   type       │
    │ - Build       │    │               │    │ - Generate   │
    │   hierarchy   │    │               │    │   JSONata    │
    └───────────────┘    └───────────────┘    └──────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
    ┌──────────────────────────────────────────────────────┐
    │                     Models                           │
    │  SAMMProperty | SAMMEntity | SAMMAspect              │
    │  PropertyMapping | TransformationResult              │
    └──────────────────────────────────────────────────────┘
```

### 2. データフロー

```
Input: Source.ttl, Target.ttl
    │
    ▼
[Parser]
    │
    ├─→ Source: SAMMAspect (96 properties)
    └─→ Target: SAMMAspect (96 properties)
    │
    ▼
[Matcher]
    │
    └─→ List[(SourceProp, TargetProp, Method, Confidence)]
        (93 matches)
    │
    ▼
[Transformer]
    │
    ├─→ PropertyMapping[] (with JSONata fragments)
    └─→ Complete transformation (nested dict)
    │
    ▼
Output: mapping_result.json, transformation.jsonata
```

### 3. コンポーネント詳細

#### Parser (src/parser.py)

**責務**:
- TTLファイルの解析（RDFLib使用）
- Aspect、Entity、Propertyの抽出
- 階層構造の再構築
- json_pathの計算

**主要メソッド**:
```python
def parse_file(file_path: str) -> SAMMAspect:
    """TTLファイルを解析してSAMMモデルを構築"""

def _parse_aspect(aspect_uri: URIRef) -> SAMMAspect:
    """Aspectとその全プロパティを解析"""

def _extract_nested_properties(entity, parent_path, parent_name):
    """Entityのプロパティを再帰的に抽出"""
```

**階層構造の処理**:
```python
# トップレベルプロパティ
prop.json_path = "id"

# ネストされたプロパティ
nested_prop.json_path = f"{parent_path}.{prop.local_name}"
# 例: "pcf.declaredUnitOfMeasurement"

# さらにネストされたプロパティ（再帰）
deeper_prop.json_path = f"{nested_prop.json_path}.{deep_prop.local_name}"
# 例: "pcf.dataQualityRating.technologicalDQR"
```

#### Matcher (src/matcher.py)

**責務**:
- プロパティ間のマッチング
- 信頼度スコアの計算
- 最適マッチの選択

**アルゴリズム**:
```python
def match_properties(source_props, target_props):
    matches = []
    matched_targets = set()

    for source_prop in source_props:
        best_match = None
        best_confidence = 0.0

        for target_prop in target_props:
            if target_prop in matched_targets:
                continue

            # 優先順位に従ってマッチング試行
            result = _find_best_match(source_prop, target_prop)
            if result and result.confidence > best_confidence:
                best_match = target_prop
                best_confidence = result.confidence

        if best_confidence >= threshold:
            matches.append((source_prop, best_match, ...))
            matched_targets.add(best_match)

    return matches
```

**マッチングの戦略**:
1. **Greedy Matching**: 各ソースプロパティに対して最良のターゲットを選択
2. **One-to-One**: 一度マッチしたターゲットは再利用しない
3. **Threshold Filtering**: 信頼度が閾値以下のマッチは破棄

#### Transformer (src/transformer.py)

**責務**:
- 変換タイプの判定
- JSONata式の生成
- ネスト構造の構築

**変換タイプの判定**:
```python
def _determine_transformation_type(source_prop, target_prop):
    # 1. データ型チェック
    if source_prop.data_type != target_prop.data_type:
        if can_cast(source_type, target_type):
            return "type_cast"

    # 2. 構造チェック
    if is_collection(source) != is_collection(target):
        return "structure_transform"

    # 3. デフォルト
    return "direct"
```

**JSONata式の生成**:
```python
def _generate_jsonata_expression(source_prop, target_prop, transform_type):
    # ソースパスの構築
    if source_prop.json_path:
        base_expr = f"$.{source_prop.json_path}"
    else:
        base_expr = f"$.{source_prop.local_name}"

    # 変換の適用
    if transform_type == "type_cast":
        return f"$number({base_expr})"  # 例
    elif transform_type == "direct":
        return base_expr
```

**ネスト構造の構築**:
```python
def _set_nested_path(obj: Dict, path: str, value: Any):
    """
    ドット区切りパスを使ってネストされた値を設定

    例:
    path = "pcf.dataQualityRating.technologicalDQR"
    → obj["pcf"]["dataQualityRating"]["technologicalDQR"] = value
    """
    keys = path.split(".")
    current = obj

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value
```

---

## 変換アルゴリズム

### 1. 全体フロー

```
1. 入力検証
   ├─ ソースモデルの妥当性確認
   └─ ターゲットモデルの妥当性確認

2. プロパティ抽出
   ├─ トップレベルプロパティの解析
   ├─ Entityプロパティの再帰的抽出
   └─ json_pathの計算

3. マッチング
   ├─ Characteristic Match
   ├─ PreferredName Match
   ├─ Property URI Match
   └─ 信頼度スコア計算

4. 変換ルール生成
   ├─ 変換タイプの判定
   ├─ JSONata式の生成
   └─ ネスト構造の構築

5. 出力生成
   ├─ マッピング詳細（JSON）
   ├─ 変換式（JSONata）
   └─ 警告・統計情報
```

### 2. 階層構造の処理詳細

**問題**: SAMMのEntity構造をフラットなプロパティリストに展開しつつ、JSONパスを保持する必要がある。

**解決策**: 再帰的な深さ優先探索

```python
def extract_all_properties(aspect: SAMMAspect) -> List[SAMMProperty]:
    """
    全プロパティを階層を保持しながら展開
    """
    all_properties = []

    # Phase 1: トップレベルプロパティ
    for prop in aspect.properties:
        prop.json_path = prop.payload_name or prop.local_name
        all_properties.append(prop)

    # Phase 2: Entityプロパティの展開
    for prop in aspect.properties:
        if prop.characteristic:
            entity_uri = get_entity_from_characteristic(prop.characteristic)
            if entity_uri:
                entity = parse_entity(entity_uri)
                # 再帰的に展開
                nested = extract_nested_properties(
                    entity,
                    parent_path=prop.json_path,
                    parent_name=prop.local_name
                )
                all_properties.extend(nested)

    return all_properties

def extract_nested_properties(entity, parent_path, parent_name):
    """
    Entityのプロパティを再帰的に展開
    """
    nested_props = []

    for entity_prop in entity.properties:
        # json_pathを計算
        nested_prop = copy(entity_prop)
        nested_prop.json_path = f"{parent_path}.{entity_prop.payload_name}"
        nested_prop.parent_property = parent_name
        nested_props.append(nested_prop)

        # さらにネストがある場合は再帰
        if nested_prop.characteristic:
            deeper_entity = get_entity(nested_prop.characteristic)
            if deeper_entity:
                deeper_props = extract_nested_properties(
                    deeper_entity,
                    parent_path=nested_prop.json_path,
                    parent_name=nested_prop.local_name
                )
                nested_props.extend(deeper_props)

    return nested_props
```

**結果**:
```
22 top-level properties
+ 74 nested properties (from 3 entities)
= 96 total properties with full json_path
```

### 3. マッチングの最適化

**課題**: O(n²) の比較計算量

**最適化手法**:

1. **早期終了**: Characteristic matchが見つかった時点で他の方法を試さない
2. **キャッシング**: 正規化した名前をキャッシュ
3. **インデックス構築**: Characteristicごとにプロパティをグループ化

```python
# 最適化版
def match_properties_optimized(source_props, target_props):
    # Characteristicでインデックス構築
    target_by_char = defaultdict(list)
    for t in target_props:
        if t.characteristic:
            target_by_char[t.characteristic].append(t)

    matches = []
    for source_prop in source_props:
        # まずCharacteristic matchを試す
        if source_prop.characteristic in target_by_char:
            candidates = target_by_char[source_prop.characteristic]
            if candidates:
                matches.append((source_prop, candidates[0], ...))
                continue

        # フォールバック: 他の方法
        ...
```

---

## 具体例

### 例1: 単純な直接マッピング

**SAMM定義**:
```turtle
# Source
:id a samm:Property ;
    samm:preferredName "PCF ID"@en ;
    samm:characteristic ext-uuid:UuidV4Trait ;
    samm:payloadName "id" .

# Target
:id a samm:Property ;
    samm:preferredName "PCF ID"@en ;
    samm:characteristic ext-uuid:UuidV4Trait ;
    samm:payloadName "id" .
```

**マッチング結果**:
- Method: `characteristic_match`
- Confidence: 0.9
- Transform type: `direct`

**生成されるJSONata**:
```jsonata
{
  "id": $.id
}
```

**実行例**:
```json
Input:  { "id": "3893bb5d-da16-4dc1-9185-11d97476c254" }
Output: { "id": "3893bb5d-da16-4dc1-9185-11d97476c254" }
```

### 例2: ネストされたプロパティ

**SAMM定義**:
```turtle
# Source (トップレベル)
:pcf a samm:Property ;
    samm:characteristic :CarbonFootprint ;
    samm:payloadName "pcf" .

:CarbonFootprint a samm-c:SingleEntity ;
    samm:dataType :PcfEntity .

# Source (Entity内)
:PcfEntity a samm:Entity ;
    samm:properties (
        [ samm:property :declaredUnitOfMeasurement;
          samm:payloadName "declaredUnitOfMeasurement" ]
    ) .

:declaredUnitOfMeasurement a samm:Property ;
    samm:preferredName "Unit of measurement"@en ;
    samm:characteristic :DeclaredUnitCharacteristic .
```

**プロパティ抽出結果**:
```python
# トップレベル
SAMMProperty(
    local_name="pcf",
    json_path="pcf",
    parent_property=None
)

# ネストされたプロパティ
SAMMProperty(
    local_name="declaredUnitOfMeasurement",
    json_path="pcf.declaredUnitOfMeasurement",
    parent_property="pcf"
)
```

**生成されるJSONata**:
```jsonata
{
  "pcf": {
    "declaredUnitOfMeasurement": $.pcf.declaredUnitOfMeasurement
  }
}
```

**実行例**:
```json
Input:  { "pcf": { "declaredUnitOfMeasurement": "liter" } }
Output: { "pcf": { "declaredUnitOfMeasurement": "liter" } }
```

### 例3: 3階層のネスト

**SAMM定義**:
```turtle
:pcf → :PcfEntity → :dqi → :DataQualityEntity → :technologicalDQR
```

**json_path計算**:
```
Level 1: "pcf"
Level 2: "pcf" + "." + "dqi" = "pcf.dqi"  (実際は "dataQualityRating")
Level 3: "pcf.dataQualityRating" + "." + "technologicalDQR"
       = "pcf.dataQualityRating.technologicalDQR"
```

**生成されるJSONata**:
```jsonata
{
  "pcf": {
    "dataQualityRating": {
      "technologicalDQR": $.pcf.dataQualityRating.technologicalDQR
    }
  }
}
```

### 例4: 型変換

**SAMM定義**:
```turtle
# Source
:speedString a samm:Property ;
    samm:dataType xsd:string .

# Target
:speed a samm:Property ;
    samm:dataType xsd:float .
```

**マッチング結果**:
- Method: `preferred_name_match`
- Confidence: 0.8
- Transform type: `type_cast`

**生成されるJSONata**:
```jsonata
{
  "speed": $number($.speedString)
}
```

---

## 拡張性

### 1. 新しいマッチング方法の追加

```python
class PropertyMatcher:
    MATCHING_LEVELS = {
        "characteristic_match": 0.9,
        "preferred_name_match": 0.8,
        "property_uri_match": 0.7,
        # 新規追加
        "description_similarity": 0.65,
    }

    def _description_similarity_match(self, source, target):
        """descriptionの類似度に基づくマッチング"""
        if not source.description or not target.description:
            return False

        similarity = calculate_semantic_similarity(
            source.description,
            target.description
        )
        return similarity > 0.7
```

### 2. カスタム変換関数

```python
class Transformer:
    def register_custom_transform(self, name, function):
        """カスタム変換関数の登録"""
        self.custom_transforms[name] = function

    def _apply_custom_transform(self, expr, transform_name):
        """カスタム変換の適用"""
        if transform_name in self.custom_transforms:
            func = self.custom_transforms[transform_name]
            return func(expr)
        return expr
```

### 3. 単位換算の実装

```python
UNIT_CONVERSION_TABLE = {
    ("unit:kilometrePerHour", "unit:metrePerSecond"): 0.27778,
    ("unit:mile", "unit:kilometre"): 1.60934,
}

def apply_unit_conversion(expr, source_unit, target_unit):
    """単位換算の適用"""
    key = (source_unit, target_unit)
    if key in UNIT_CONVERSION_TABLE:
        factor = UNIT_CONVERSION_TABLE[key]
        return f"$round({expr} * {factor}, 2)"
    return expr
```

### 4. 外部マッピングテーブルの統合

```python
def load_explicit_mapping(mapping_file):
    """
    外部定義されたマッピングを読み込む

    Format (CSV):
    source_property,target_property,confidence,transformation
    :sourceId,:targetId,1.0,direct
    :sourceSpeed,:targetVelocity,1.0,unit_conversion
    """
    mappings = {}
    with open(mapping_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            mappings[row['source_property']] = {
                'target': row['target_property'],
                'confidence': float(row['confidence']),
                'transformation': row['transformation']
            }
    return mappings
```

### 5. 機械学習ベースのマッチング

```python
class MLMatcher:
    """機械学習を使用したセマンティックマッチング"""

    def __init__(self, model_path):
        self.model = load_embedding_model(model_path)

    def calculate_semantic_similarity(self, source, target):
        """埋め込みベクトルの類似度計算"""
        source_vec = self.model.encode(source.description)
        target_vec = self.model.encode(target.description)
        similarity = cosine_similarity(source_vec, target_vec)
        return similarity

    def find_best_match(self, source_prop, target_props):
        """最も類似したターゲットプロパティを検索"""
        best_match = None
        best_score = 0.0

        for target_prop in target_props:
            score = self.calculate_semantic_similarity(
                source_prop,
                target_prop
            )
            if score > best_score:
                best_match = target_prop
                best_score = score

        return best_match, best_score
```

---

## まとめ

本システムは以下の理論的基盤の上に構築されています：

1. **セマンティックモデリング**: SAMMの意味情報を活用
2. **グラフ理論**: RDFグラフの探索とマッピング
3. **パターンマッチング**: 複数のヒューリスティックの組み合わせ
4. **信頼度理論**: 確率的なマッチングの評価
5. **構造変換理論**: 階層構造の保存と変換

これにより、人手による定義を最小化しつつ、高精度なデータ変換ルールを自動生成できます。

### 今後の改善方向

1. **マッチング精度の向上**
   - 機械学習モデルの統合
   - ドメイン知識の活用
   - ユーザーフィードバックの学習

2. **変換の高度化**
   - 複雑な数式の対応
   - 条件分岐の生成
   - 集約関数の適用

3. **スケーラビリティ**
   - 大規模モデルへの対応
   - 並列処理の実装
   - キャッシング戦略の最適化

4. **ユーザビリティ**
   - GUIツールの提供
   - マッピングの可視化
   - インタラクティブな修正機能
