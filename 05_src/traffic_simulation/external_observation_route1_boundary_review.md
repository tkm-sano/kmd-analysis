# 国道1号 opposite carriageway coverage不足個別調査

既存の固定DOWN 15-edge列、alternate UP 14-edge候補、matching閾値、SUMO network、元データは変更していない。

## 結論

最終判定は `BOUNDARY_GEOMETRY_MISMATCH` であり、UP列は採択しない。

- 現候補coverage: 0.586498（閾値0.60）
- 現候補の最大端点差: 220.357 m（公式起点側、固定DOWN始点／候補UP終点）
- 最良局所延長: `EXTEND_UP_START_1`、coverage 0.589805、最大端点差 220.357 m
- 公式geometry被覆: 0.840896、未被覆 163.795 m
- 境界edge: `542890137#0`、長さ 233.782 m

## 原因

候補末尾のSUMO edgeは観測区間境界をまたぐ粒度であり、edge全体を含めると公式起点側へ過走する。直前側の短い1 edgeは自然な国道1号本線延長だがcoverageを0.60まで上げず、反対側の220.357 m差も解消しない。候補軸の25 m buffer外は198.333 m、13.749 m、202.159 mの3区間に分かれ、最後が起点側の末尾edge過走、前二者は分離車道軸間隔が25 mを超える内部区間である。さらに延ばすと端点対応が悪化するため、単純なcorridor aggregation不足ではない。

## 非変更確認

正本mapping、66区間mapping、候補列、network、config・閾値、公式geometryはpre-work hashで固定した。

Validation: 100 passed, 0 failed.
