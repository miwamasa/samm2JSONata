仕様に従い、SAMM(Semantic Aspect Meta Model)で定義された２つのモデルから、それぞれのモデルのインスタンスであるjsonデータを変換するルールを作成する


# SAMMの仕様
https://eclipse-esmf.github.io/samm-specification/snapshot/index.html

# 変換仕様
spec/specifcation.md

# テスト
## ソース pcf
SAMMモデル
test/pcf/Pcf.ttl

インスタンス例
test/pcf/Pcf.json

## ターゲット generic_digitalpasport
SAMMモデル
test/generic_digitalpassport/DigitalProductPassport.ttl