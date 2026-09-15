# 0-2-B-1 Mac側Git整理

```text
0-1 社会科学としての問い                    [PARTIAL]
0-2 研究設計                                [CURRENT]
0-3 方法論                                  [CURRENT]
  ├─ 0-2-B 正本実行環境のHayate移行         [CURRENT]
  │   └─ 0-2-B-1 Mac側Git整理               [COMPLETE]  ← 今回
  ├─ 1. 道路・交通条件                      [PARTIAL]
  ├─ 2. 交通状態                            [CURRENT]
  │   └─ 2-3 交通量較正                     [CURRENT]
  ├─ 3. 配送条件                            [PARTIAL]
  ├─ 4. 配送simulation                      [PARTIAL]
  ├─ 5. 配送最適化問題                      [NOT STARTED]
  └─ 6. 計算手法比較                        [NOT STARTED]
```

- Current location: `0-2-B-1 Mac側Git整理`
- Parent research stage: `0-2-B 正本実行環境のHayate移行`
- Research question addressed: Mac上に蓄積した複数工程の研究変更を、意味の異なる作業や大容量成果物を混ぜずに追跡可能なGit履歴へ整理できるか。
- Why this task is necessary: dirty working treeのままHayateへ移すと、コード履歴、研究判断、raw data、生成成果の責務境界が曖昧になるため。
- Main route / Branch route: Hayate移行から一時分岐した前処理。
- Entry condition: Git HEAD、変更済み・未追跡ファイル、byte-level移行manifestが固定済み。
- Exit condition: Git対象と大容量保存対象が分離され、全検証合格後に意味別commitが作成され、working treeがcleanになる。
- Next destination: `0-2-B Hayate正本環境移行`へ戻る。

## 結論

MacのGit repositoryは壊れていない。`main`は`origin/main`と同じHEAD `722986952e7242f7389db748124d37ed4006340e`にあり、その上に複数工程の未コミット成果が重なっていた。

大容量のraw、processed、traffic simulation output、環境移行manifestはGitではなくHayate正本データ領域へ保存する。Git候補にはコード、test、schema、policy、decision、provenance metadata、研究進捗文書だけを残した。

## 今回修正したGit汚染原因

`test_compare_phase13_psv_probe_fails_when_hash_contract_is_invalid`が、10.9 MBの変異JSONをsource fixture directoryへ書き込んでいた。

- 出力先をpytestの`tmp_path`へ変更した。
- 該当試験を2回実行し、2回ともpassした。
- fixture directory全体の前後SHA-256は一致した。
- 変異JSONが再生成されないことを確認した。
- 既存の変異JSONは削除せず、Macのゴミ箱`mutated_psv_probe_bad_hash_20260825.json`へ退避した。
- この不具合を`.gitignore`で隠していない。

## Gitと大容量保存の境界

| 対象 | Git | Hayate正本データ |
|---|---|---|
| Python code、test | 管理する | repo snapshotにも含む |
| policy、decision、schema、設定 | 管理する | repo snapshotにも含む |
| 研究進捗Markdown | 管理する | repo snapshotにも含む |
| source provenance metadata | 管理する | repo snapshotにも含む |
| raw data原本 | 管理しない | 保存する |
| processed data | 原則管理しない | 保存する |
| traffic simulation outputs | 管理しない | 保存する |
| failed probe・historical evidence | 管理しない | 保存する |
| migration byte inventory | 管理しない | 保存する |
| cache・一時変異fixture | 管理しない | 原則保存しない |

`.gitignore`へ`reproducibility/outputs/environment_migration/**`を追加した。移行方法を定義するscript、config、この進捗文書はGit管理対象のままである。

## 検証

### PSV一時ファイル再発試験

```text
1 passed
1 passed
fixture fingerprint before = 55724854aff661b8174934f53ada5a9ca76863146fc0649bc57e7ca10c493253
fixture fingerprint after  = 55724854aff661b8174934f53ada5a9ca76863146fc0649bc57e7ca10c493253
fixture regenerated = no
```

### 固定分析コンテナ全回帰

```text
794 passed in 2028.18s (0:33:48)
```

Macのbase Pythonでは`rfc8785`と`folium`が不足していたため、base環境へ追加installせず、既存の固定Docker分析環境を使用した。

## 作成したcommitの構成

変更を次の4単位へ分ける。すべて明示的なファイル一覧だけをstageし、`git add .`は使用しない。

1. `feat(traffic-network): record Phase 13 access and lane resolution`
   - 道路方向、車線、通行権限、oneway materialization。
   - decision、policy、schema、registry、comparator、test。
   - 固定分類68件。
2. `feat(traffic-calibration): add official observations and PT demand preparation`
   - 国交省・警視庁観測のmetadata。
   - PT小ゾーンOD、空間支持、外外通過交通、TAZ・経路配分。
   - code、test、policy、2-3進捗文書。
   - 固定分類34件。
3. `chore(environment): prepare canonical Hayate execution environment`
   - Git ignore境界。
   - path portable化。
   - Hayate環境設定例、監査・転送・hash検証script。
   - READMEの現在地更新。
   - 固定分類9件。
4. `docs(research): add numbered workflow and source records`
   - 研究全体構造と作業管理規則。
   - 研究現状・設計案件。
   - このGit整理記録。
   - 配送条件に使用する公式調査原本の来歴記録。
   - 固定分類4件。

`git add .`は使用しない。各群を明示的なpath listでstageし、`git diff --cached --check`、対象file一覧、想定外large fileなしを確認してからcommitする。

## 実行許可と境界

2026-08-25に、ローカルbranch `research/mac-git-normalization-20260825`の作成と上記4 commitの作成が明示的に許可された。pushとPRは禁止されたままであり、実施していない。

## 終了時記録

- What was learned: Gitの主問題は破損ではなく、複数工程の変更と生成物の境界が未整理だったこと。
- What was decided: Gitはcode・decision・policy・test・研究文書を管理し、大容量研究成果はHayate正本データへ分離する。
- What remains unresolved: Git整理としての未解決はない。Hayateへの転送・環境構築・動作検証は親工程に残る。
- Whether this branch is closed: はい。4 commitとcommit後検査の完了をもって閉じる。
- Where we return to in the main route: `0-2-B Hayate正本環境移行`へ戻る。

要するに、Mac側の研究変更は4つの意味単位へ整理され、全794試験に合格した状態でローカルGit履歴へ固定された。次はHayate移行へ戻る。
