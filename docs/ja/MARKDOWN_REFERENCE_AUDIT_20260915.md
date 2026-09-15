# Markdown参照・archive監査 2026-09-15

## 目的

現行R24入口を明確にし、root直下に残る未参照Markdownを整理しました。大量の研究証拠を「参照数0」だけで削除するとprovenanceを損なうため、今回の自動判定はroot直下のtracked Markdownに限定しています。

## 判定方法

- `*.md`内で対象filenameが文字列として現れるかを検索
- `reproducibility/archive/`と`legacy/`からの参照はcurrent incoming referenceに数えない
- 現行authority、README、portal、CLI、indexから参照される文書は保持
- referenceが0でも、削除ではなくGit-tracked archiveへ移動
- freeze済みspecification、execution artifact、data provenanceは対象外

## Archiveした文書

| 元path | 判定 |
|---|---|
| `0-2-B-1_20260825_COMPLETE_Mac側Git整理.md` | incoming reference 0、完了済み環境移行履歴 |
| `0-2-B_20260825_CURRENT_Hayate正本環境移行準備.md` | incoming reference 0、後続完了記録により旧CURRENT化 |
| `20260718_sumo_tokyo_motorized_typemap_design_updated(1).md` | incoming reference 0、rootの`(1)` copy |

Archive先: [pre-R24 root documents](../../reproducibility/archive/project_management/pre_r24_root_documents/20260915_v1/README.md)

## 保持した主な旧文書

次は古い記述を含みますが、現在も他文書から参照されるため、参照先を移行せずにarchiveしませんでした。

- `RESEARCH_STATUS.md`
- `RESEARCH_OVERVIEW.md`
- `20260903_20260903_RESEARCH_OVERVIEW.md`
- `RESEARCH_PIPELINE_REFERENCE.md`
- `EVRP_EXECUTION_PLAN.md`
- rootの交通量較正・project-management記録

これらを将来archiveする場合は、先にportal、CLI、repository index、learning documentのlinkとauthority表現をcurrent R24文書へ移す必要があります。

## 結果

- 削除: 0
- Archive移動: 3
- 現行R24 authorityの移動: 0
- Freeze済みspecificationの変更: 0
- Generated benchmark dataの変更: 0
