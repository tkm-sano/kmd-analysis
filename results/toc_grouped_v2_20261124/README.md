# グループ受付v2 予備結果と登録索引

- `pilot_summary.csv` は保存計画再評価済みの各規模1件の総D、総W、参考分母の集計です。Cの内部名は `C_Idual`、Dの内部対照は `D_classical`、量子側は `D_quantum` です。固定Bは参照です。
- `FIGURE_1.png` はC基準の両立改善率、`FIGURE_2.png` は箱当たり走行距離、`FIGURE_3.png` は稼働車両日当たり荷待ちです。図はB、C、D量子を比較します。各規模1点なので、箱・ひげは一点に重なります。行政値は図の独立参照欄です。
- `formal_registration_index.json` は条件参照、試行識別子、入力と固定Bのハッシュ、およびseed再生成の索引です。登録は各規模30件、観測は0件です。
- `input_provenance.json` は採用入力の出典と照合値です。検証の範囲と具体的な操作は[公開再現ガイド](../../docs/research/TOC_PUBLIC_REPRODUCTION.md)を参照してください。
