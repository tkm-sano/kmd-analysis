# 都道316号 `13403160320` direction formal investigation

## 直接原因

既存 `UNRESOLVED` の直接原因は、公式の起点・終点は確認済みでも、部分被覆の7-edge
固定列のどちらの端が公式起点／終点側かを、当時の公式隣接区間・接続路線・明示的
route relation方向から一意にanchorできなかったことである。これは証拠矛盾ではなく
`PRIOR_EVIDENCE_INSUFFICIENT_NOT_CONFLICTING` である。

## 結論

3 targetすべてについて、selected corridorを `RESOLVED_UP` と判定する
（導出分類は `RESOLVED_BY_COMBINED_EVIDENCE`）。診断上の方向は次のとおりである。

- 固定7-edge corridor: `UP_TERMINUS_TO_ORIGIN`
- alternate 4-edge corridor: `DOWN_ORIGIN_TO_TERMINUS`

既存正式mapping、既存direction classification、SUMO network、matching閾値は変更していない。
本成果物は診断レイヤーであり、正式mappingへの採択適用は別工程とする。

方向証拠statusは `RESOLVED` だが、traffic assignment statusは `REVIEW_REQUIRED` である。
alternateは方向・route identity・topologyの観点では
`FORMAL_ADOPTION_REVIEW_ELIGIBLE_NOT_ADOPTED` であり、正式採択済みではない。

## 公式定義とendpoint

- MLIT定義: `UP=TERMINUS_TO_ORIGIN; DOWN=ORIGIN_TO_TERMINUS`
- Road Census `13403160320`: route 316「日本橋芝浦大森線」、起点側「品川区道」
  （接続先 `13403160400`）、終点側「品川区・大田区境」
- 東京都路線調書: 起点 `中央区日本橋本町三丁目`、終点 `大田区大森南一丁目`
  （2024-04-01現在、PDF page 10 / printed page 193）

東京都の公式路線調書: https://www.kensetsu.metro.tokyo.lg.jp/content/000064960.pdf

## resolving evidence combination

1. `60320`終点と`60330`起点は公式原票で同じ「品川区・大田区境」である。
2. alternate末尾と`60330`先頭はedge `45662512`を共有する。
3. `60330`終点／`60340`起点は「環状七号線」で、edge `1457802380`を共有する。
4. `60340`終点／`60350`起点は「高速１号羽田線」で、edge
   `1068239670;45662504`を共有する。
5. 各列はconnection violation 0で、同じcanonical route relationに属する。
6. 固定列とalternate列は別oneway carriagewayで逆向き
   （direction cosine -0.998690）である。

この公式endpoint chainとSUMO shared-edge topologyがalternateを起点→終点へanchorし、
alternateをDOWN、対応する反対車道の固定列をUPへ接続する。geometryは車道対応と位置の
補助に限定し、GeoJSON coordinate orderを方向証拠には使用していない。

## route relation diagnosis

- relation: `11699637`
- name / network / ref: `日本橋芝浦大森線` / `JP:prefectural:tokyo` / `316`
- operator: 空欄
- fixed member sequence: `CONTIGUOUS_DECREASING`
- alternate member sequence: `CONTIGUOUS_DECREASING`
- member role: 対象memberはすべて空欄

relationはcanonical identityとmember continuityを支持するが、方向注記、operator、
forward/backward roleがない。さらに両反対車道が同じdecreasing index trendを持つため、
relation sequence単独ではUP/DOWNを確定できない。bare numeric `ref=316`単独も使用していない。

## 残る制約

原票が`60320`起点側の接続先として参照する`13403160400`は、手元の`kasyo13.csv`に
対応行がないため、起点側からの独立anchorは得られない。ただし終点側から始まる3段の
公式section chainとSUMO edge共有が同一結論を与え、矛盾証拠はない。

## 次工程と成果物

正式mappingへ反対車道を追加する場合は、本診断とは分離した採択reviewを実施する。
本調査は `route316_direction_evidence.csv`、`route316_direction_diagnosis.csv`、詳細な
edge/relation/adjacent/final classification CSV、QA JSON、manifest、validation JSONを生成する。

## automated tests

関連回帰は `82 passed / `
`0 failed`
（Route316専用 `12`件）である。

## Git差分

Gitの更新・stage・commitは行っていない。task sourceとして調査script、本文書、専用testを
workspaceへ追加し、生成CSV/JSONは既存のignored processed-data directoryへ出力した。
formal mapping、SUMO network、matching config/thresholdのhashはmanifest入力hashとして固定した。
