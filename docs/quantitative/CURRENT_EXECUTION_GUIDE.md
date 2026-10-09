# 現行公開候補の実行ガイド

[環境構築](../../reproducibility/environment/QUICKSTART_ENVIRONMENT.md)後、リポジトリ直下で実行します。

```bash
python -B scripts/verify_quickstart.py
```

45件のAPI/契約テストとNotebook6冊の既定セルを検証します。Notebookだけは `python -B notebooks/test_notebooks.py`。入力・元Notebook・freezeを通常は書き換えません。`-O`は禁止です。

[Notebook一覧](../../notebooks/README.md)と[Model Index](QUANTITATIVE_MODEL_INDEX.md)からrouting、quantum、simulation、battery、energy、analysisへ辿れます。必要な旧R0/science等は元位置で呼び、科学的数式を再実装していません。

以前の9ファイル静的test_transferや`./research` CLI、全量OD/SUMO/workerコマンドは今回の95件に含まれず、本ガイドのQuick Startでは使用しません。原記録はHayateとGit履歴に保持します。小規模再利用の成功を全量再現へ拡大しません。

[保存結果](../../results/README.md)は新規生成しません。欠損・hash不一致では失敗し、代替結果やゼロで補いません。[評価範囲](GITHUB_AND_HAYATE.md)を参照してください。remote CI、他OS、Colabは未検証。公開許諾とGit操作は承認待ちです。
