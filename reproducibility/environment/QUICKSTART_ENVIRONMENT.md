# 小規模再利用環境

Python 3.12.3 / Linuxで、新規venvへPyPIからキャッシュを使わずインストールして検証する環境です。元の`.conda`と全量研究環境は変更しません。

リポジトリ直下で次を実行します。配布候補がGitHubへ反映されるまでは、現在のcloneで全ファイルが揃うとは保証しません。

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r reproducibility/environment/requirements-quickstart.lock.txt
.venv/bin/python -m pip check
.venv/bin/python -B scripts/verify_quickstart.py
```

lockは今回の新規インストールで解決した全ランタイム依存のバージョンです。wheelのプラットフォーム横断ロックではなく、他OS/Pythonは未検証です。直接依存の起点は[notebooks/requirements.txt](../../notebooks/requirements.txt)。インストール時の配布物URLとハッシュは取得記録（Hayate保存参照: `docs/audits/quantitative_repository_final_release_20261009/PIP_INSTALL_REPORT.json`、公開ツリー非同梱）にあります。

1コマンド検証は45件の既存API/契約テストと6冊の既定セルを実行します。Notebookやfreezeを保存し直しません。`-O`は禁止。旧互換リンクのテスト、全量SUMO/OD、正式QAOA最適化は対象外です。教材QAOAのNOT_ACQUIREDは科学的再現成功を意味しません。

Jupyter UIは含みません。既存のJupyter UIを使う場合、`.venv/bin/python -m ipykernel install --user --name kmd-notebooks`でkernelを登録する方法があります（UI操作自体は未検証）。nbclientによる自動実行はUI不要です。

[依存範囲](DEPENDENCY_SCOPE.md) / 最新の検証報告（Hayate保存参照: `docs/audits/quantitative_repository_final_release_20261009/10_FINAL_READINESS_REPORT.md`、公開ツリー非同梱）。公開許諾未確定・GitHub Actions実行未確認です。
