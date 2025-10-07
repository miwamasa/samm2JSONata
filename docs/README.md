# SAMM to JSONata - ドキュメントインデックス

## 📚 ドキュメント一覧

### 初心者向け

1. **[クイックスタートガイド](quickstart.md)** ⭐ おすすめ
   - 5分で始められる
   - 基本的な使い方
   - よくあるエラーと解決方法

### 技術詳細

2. **[理論と実装](theory_and_implementation.md)** 🎓 必読
   - SAMMモデルの構造
   - マッピング理論
   - アルゴリズム詳細
   - 実装アーキテクチャ
   - 拡張方法

3. **[変換仕様書](../spec/specifcation.md)**
   - 変換ルール生成の仕様
   - マッピング決定アルゴリズム
   - JSONata式生成ルール
   - 出力フォーマット

### 実行結果

4. **[変換実行レポート](../output/transformation_summary.md)**
   - 最新のテスト結果
   - モデル解析結果
   - 変換精度
   - 検証結果

### 参考資料

5. **[SAMM仕様](../spec/samm_specification.md)**
   - SAMMメタモデルの基本
   - データ型とJSONマッピング
   - 命名規則

6. **[SAMM公式ドキュメント](https://eclipse-esmf.github.io/samm-specification/snapshot/index.html)**
   - Eclipse ESMF SAMM仕様（外部リンク）

---

## 📖 推奨読む順序

### ケース1: すぐに使いたい
1. [クイックスタートガイド](quickstart.md)
2. [変換実行レポート](../output/transformation_summary.md) - 期待される結果を確認

### ケース2: システムを理解したい
1. [理論と実装](theory_and_implementation.md) の「概要」と「基本理論」
2. [SAMM仕様](../spec/samm_specification.md) でSAMMの基本を学ぶ
3. [理論と実装](theory_and_implementation.md) の「実装アーキテクチャ」
4. [変換仕様書](../spec/specifcation.md) で詳細を確認

### ケース3: カスタマイズしたい
1. [理論と実装](theory_and_implementation.md) の「実装アーキテクチャ」
2. [理論と実装](theory_and_implementation.md) の「拡張性」
3. ソースコード（`src/`ディレクトリ）を読む

---

## 🔍 トピック別インデックス

### SAMMモデル
- [SAMMモデルの構造](theory_and_implementation.md#sammモデルの構造)
- [階層構造とJSONマッピング](theory_and_implementation.md#2-階層構造とjsonマッピング)
- [Entity の扱い](theory_and_implementation.md#1-基本要素)

### マッチング
- [マッチング戦略](theory_and_implementation.md#マッピング理論)
- [Characteristic Match](theory_and_implementation.md#2-characteristic-matchの理論的根拠)
- [信頼度の計算](theory_and_implementation.md#4-信頼度の計算)

### 変換
- [変換アルゴリズム](theory_and_implementation.md#変換アルゴリズム)
- [JSONata式の生成](theory_and_implementation.md#jsonata式の生成)
- [ネスト構造の処理](theory_and_implementation.md#2-階層構造の処理詳細)

### 実装
- [Parser の実装](theory_and_implementation.md#parser-srcparserpy)
- [Matcher の実装](theory_and_implementation.md#matcher-srcmatcherpy)
- [Transformer の実装](theory_and_implementation.md#transformer-srctransformerpy)

### 拡張
- [新しいマッチング方法の追加](theory_and_implementation.md#1-新しいマッチング方法の追加)
- [カスタム変換関数](theory_and_implementation.md#2-カスタム変換関数)
- [単位換算の実装](theory_and_implementation.md#3-単位換算の実装)
- [機械学習ベースのマッチング](theory_and_implementation.md#5-機械学習ベースのマッチング)

---

## 💡 よくある質問

### Q: どのドキュメントから読めばいい？

**A:** 目的によります：
- **すぐ使いたい** → [クイックスタート](quickstart.md)
- **仕組みを知りたい** → [理論と実装](theory_and_implementation.md)
- **カスタマイズしたい** → 理論と実装の「拡張性」セクション

### Q: SAMMについて何も知らない

**A:** まず [SAMM仕様](../spec/samm_specification.md) の最初の3セクションを読んでください。
特に「階層構造とJSONマッピング」が重要です。

### Q: なぜマッチング数が少ない？

**A:** [トラブルシューティング](quickstart.md#トラブルシューティング) を参照してください。
一般的な原因：
- モデルが大きく異なる
- 信頼度閾値が高すぎる
- Characteristicが一致しない

### Q: 独自のマッチングロジックを追加したい

**A:** [理論と実装](theory_and_implementation.md#1-新しいマッチング方法の追加) の「拡張性」セクションに具体例があります。

---

## 🎯 ユースケース別ガイド

### ユースケース1: 既存モデル間の変換

```bash
# 1. 変換ルール生成
python src/generator.py --source model_a.ttl --target model_b.ttl --output mapping/

# 2. 結果確認
cat mapping/mapping_result.json | jq '.metadata'

# 3. データ変換
python src/apply_transformation.py \
  --input data.json \
  --transformation mapping/transformation.jsonata \
  --output transformed.json
```

**参考**: [クイックスタート](quickstart.md#例1-異なるモデル間の変換)

### ユースケース2: 低信頼度マッチングの確認

```bash
# 低い閾値で生成
python src/generator.py ... --confidence-threshold 0.5 --output low_threshold/

# 警告を確認
cat low_threshold/mapping_result.json | jq '.warnings'

# 低信頼度マッピングを手動で確認
cat low_threshold/mapping_result.json | jq '.mappings[] | select(.confidence < 0.7)'
```

**参考**: [理論と実装 - 信頼度の計算](theory_and_implementation.md#4-信頼度の計算)

### ユースケース3: バッチ処理

```bash
# 複数ファイルの変換
for json_file in data/*.json; do
  python src/apply_transformation.py \
    --input "$json_file" \
    --transformation mapping/transformation.jsonata \
    --output "output/$(basename $json_file)"
done
```

**参考**: [クイックスタート - バッチ処理](quickstart.md#例3-バッチ処理)

---

## 📝 フィードバック

ドキュメントの改善提案や質問は、GitHubのIssueでお願いします。

---

最終更新: 2025-10-07
