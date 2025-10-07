# クイックスタートガイド

## 5分で始めるSAMM to JSONata変換

### 前提条件

```bash
# Python 3.9以上
python3 --version

# 依存関係のインストール
pip install -r requirements.txt
```

### 基本的な使い方

#### 1. 変換ルールの生成

```bash
python3 src/generator.py \
  --source test/pcf/Pcf.ttl \
  --target test/pcf/Pcf.ttl \
  --output output
```

**出力ファイル**:
- `output/mapping_result.json` - マッピングの詳細
- `output/transformation.jsonata` - JSONata変換式

#### 2. 変換の実行

```bash
# Pythonスクリプトで実行
python3 src/apply_transformation.py \
  --input test/pcf/Pcf.json \
  --transformation output/transformation.jsonata \
  --output output/transformed.json
```

### 出力の確認

```bash
# マッピング統計の確認
cat output/mapping_result.json | jq '.metadata'

# 変換式の確認
head -30 output/transformation.jsonata

# 変換結果の確認
cat output/transformed.json | jq . | head -30
```

### よくある使用例

#### 例1: 異なるモデル間の変換

```bash
python3 src/generator.py \
  --source models/source_model.ttl \
  --target models/target_model.ttl \
  --output output/mapping1
```

#### 例2: 信頼度閾値の変更

```bash
# より厳密なマッチング（デフォルト: 0.6）
python3 src/generator.py \
  --source test/pcf/Pcf.ttl \
  --target models/target.ttl \
  --confidence-threshold 0.8 \
  --output output/strict_mapping
```

#### 例3: バッチ処理

```bash
# 複数のJSONファイルを変換
for file in data/*.json; do
  python3 src/apply_transformation.py \
    --input "$file" \
    --transformation output/transformation.jsonata \
    --output "output/transformed_$(basename $file)"
done
```

### トラブルシューティング

#### Q1: "No Aspect found in the model" エラー

**原因**: TTLファイルにAspectが定義されていない

**解決**:
```turtle
# TTLファイルに以下が含まれているか確認
:YourAspect a samm:Aspect ;
    samm:properties ( ... ) .
```

#### Q2: マッチング数が少ない

**原因**:
- モデルが大きく異なる
- 信頼度閾値が高すぎる

**解決**:
```bash
# 閾値を下げて再試行
python3 src/generator.py ... --confidence-threshold 0.5
```

#### Q3: ネストされたプロパティが抽出されない

**確認**:
```bash
# パーサーのログを確認
python3 -c "
import sys
sys.path.insert(0, 'src')
from parser import SAMMParser

parser = SAMMParser()
aspect = parser.parse_file('your_model.ttl')
print(f'Total properties: {len(aspect.properties)}')
print(f'Entities: {len(aspect.entities)}')
"
```

### 次のステップ

- [詳細な理論と実装](theory_and_implementation.md)を読む
- [仕様書](../spec/specifcation.md)でマッピングルールを理解する
- カスタムマッチング方法を実装する

### サポート

問題が発生した場合は、以下の情報とともに報告してください：
- Python バージョン
- SAMMモデルファイル（可能であれば）
- エラーメッセージ
- `output/mapping_result.json` の内容
