<a id="markdown参照archive監査-2026-09-15"></a>

# 文書参照・保管履歴の監査 2026-09-15

## 目的

現行R24入口を明確にし、最上位直下に残る未参照軽量マークアップ文書を整理しました。大量の研究証拠を「参照数0」だけで削除すると出典・来歴を損なうため、今回の自動判定は最上位直下のtracked 軽量マークアップ文書に限定しています。

## 判定方法

- `*.md`内で対象filenameが文字列として現れるかを検索
- `reproducibility/archive/`と`legacy/`からの参照は現行 incoming 参照に数えない
- 現行正本、案内文書、ポータル、コマンド操作、索引から参照される文書は保持
- 参照が0でも、削除ではなくGit-tracked archiveへ移動
- 固定済み仕様、実行 成果物、data 出典・来歴は対象外

## Archiveした文書

| 元保存先 | 判定 |
|---|---|
| `0-2-B-1_20260825_COMPLETE_Mac側Git整理.md` | incoming 参照 0、完了済み環境移行履歴 |
| `0-2-B_20260825_CURRENT_Hayate正本環境移行準備.md` | incoming 参照 0、後続完了記録により旧現行化 |
| `20260718_sumo_tokyo_motorized_typemap_design_updated(1).md` | incoming 参照 0、最上位の`(1)` コピー |

Archive先: [pre-R24 最上位 文書](../../reproducibility/archive/project_management/pre_r24_root_documents/20260915_v1/README.md)

## 保持した主な旧文書

次は古い記述を含みますが、現在も他文書から参照されるため、参照先を移行せずにarchiveしませんでした。

- `RESEARCH_STATUS.md`
- `RESEARCH_OVERVIEW.md`
- `20260903_20260903_RESEARCH_OVERVIEW.md`
- `RESEARCH_PIPELINE_REFERENCE.md`
- `EVRP_EXECUTION_PLAN.md`
- 最上位の交通量較正・project-management記録

これらを将来archiveする場合は、先にポータル、コマンド操作、リポジトリ索引、learning documentのリンクと正本表現を現行 R24文書へ移す必要があります。

## 結果

- 削除: 0
- Archive移動: 3
- 現行R24 正本の移動: 0
- 固定済み仕様の変更: 0
- Generated ベンチマーク dataの変更: 0
