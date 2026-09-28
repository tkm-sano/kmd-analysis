# リポジトリの配置

2026-09-28に、直下の研究文書15件を用途別に移動しました。

| 保存先 | 文書 |
|---|---|
| `00_project_management/` | 現在の実行状況・実行計画・研究工程の進捗 |
| `01_research_design/` | 研究概要・正式な研究タイトル・問いと仮説 |
| `docs/` | 研究手順の参照資料・利用案内 |
| `00_project_management/history/` | 日付付きの過去の研究記録8件 |

直下には入口の `README.md`、`LICENSE`、実行用の `research` と `compose.yaml`、設定用の `.gitignore` と `.dockerignore` を残します。コマンドは従来どおりリポジトリ直下で実行します。

- [現在の実行状況](../00_project_management/CURRENT_EXECUTION.md)
- [研究概要](../01_research_design/RESEARCH_OVERVIEW.md)
- [研究手順の参照資料](RESEARCH_PIPELINE_REFERENCE.md)
- [過去の研究記録](../00_project_management/history/README.md)
- [移動対応表](ROOT_FILE_RELOCATIONS.json)

移動対応表には旧保存先・新保存先・移動前のコミットと内容のハッシュを記録しています。凍結済みの成果物・監査記録は当時のパスとハッシュを保持しています。過去の記録から現在の文書を探す場合は対応表を使い、当時の内容を確認する場合は記録されたコミットを参照してください。過去の監査スクリプトの再実行も当時のコミットを対象とします。ポータルの旧 `/artifact/` 文書リンクは移動先へ転送します。
