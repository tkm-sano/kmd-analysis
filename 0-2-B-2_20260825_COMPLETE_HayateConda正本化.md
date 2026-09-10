# 0-2-B-2 Hayate Conda正本化 完了記録

```text
0-1 社会科学としての問い                    [PARTIAL]
0-2 研究設計                                [CURRENT]
0-3 方法論                                  [CURRENT]
  ├─ 0-2-B 正本実行環境のHayate移行         [CURRENT]
  │   ├─ 0-2-B-1 Mac側Git正規化             [COMPLETE]
  │   └─ 0-2-B-2 Conda正本化                [COMPLETE] ← この記録
1. 道路・交通条件                           [PARTIAL]
2. 交通状態                                 [CURRENT]
  └─ 2-3 交通量較正                         [CURRENT]  ← 復帰先
3. 配送条件                                 [PARTIAL]
4. 配送simulation                           [PARTIAL]
5. 配送最適化問題                           [NOT STARTED]
6. 計算手法比較                             [NOT STARTED]
```

## 作業位置

- Current location: `0-2-B-2 Hayate実行環境のConda正本化`
- Parent research stage: `0-2 研究設計 / 0-2-B 正本実行環境のHayate移行`
- Research question addressed: 研究コードをDocker daemonに依存せず、Hayate上の固定Conda・SUMO環境で再現実行できるか。
- Why this task is necessary: 交通量較正と後続simulationを同じ正本環境で繰り返し実行するため。
- Main route / Branch route: 研究基盤を整える派生ルート。
- Entry condition: Mac側Git正規化済み、Hayate上にPython 3.11.15、Conda環境、SUMO 1.24.0が配置済み。
- Exit condition: 正本依存定義、起動手順、環境検証、全交通simulation回帰がDockerなしで成立する。
- Next destination: `2-3 交通量較正`へ戻る。

## 完了した整理

- Pythonの直接依存18件を `reproducibility/environment/requirements-analysis.txt` へ移し、Docker外の正本とした。
- Dockerは同じ正本requirementsを参照する任意の追加確認環境とした。
- Hayateの起動、再構築、環境検証、回帰試験の手順を文書化した。
- `.conda/` と `.local/` はHayateローカル環境としてGit対象外のまま維持した。
- `.bashrc` 自体はGit管理せず、環境変数例だけをrepositoryへ保存した。
- 研究コード、過去の再現性出力、source dataは変更していない。

## 検証結果

実行日: 2026-08-25（Asia/Tokyo）

| 確認項目 | 結果 |
|---|---|
| Python | `/home/takuma/kmd-analysis/.conda/bin/python`, 3.11.15 |
| Python依存整合性 | `pip check`: 問題なし |
| SUMO | `/home/takuma/kmd-analysis/.local/sumo-1.24.0/bin/sumo`, 1.24.0 |
| pytest | 8.3.3 |
| 正本requirements SHA-256 | `0ba6c464a5bb550b54f9215cbe86ef770583d7d5e29cbb221bdf32c3936652e0` |
| Git除外 | `.conda/`, `.local/` とも追跡0件 |
| Docker Compose定義 | daemon未使用の構文検証に合格 |
| 全回帰試験 | `794 passed in 442.82s` |

標準回帰コマンドは次である。

```bash
python -m pytest -q 05_src/traffic_simulation/validation
```

## 終了時の整理

- What was learned: 現在のHayateローカル環境は、Docker daemonなしで交通simulation検証一式を実行できる。
- What was decided: Hayate native Conda environmentを正本実行環境、Dockerを任意の二次クロスチェックとする。
- What remains unresolved: SUMO本体やOSレベルライブラリをゼロから取得・構築する完全な供給経路は、Python requirementsとは別に管理が必要である。
- Whether this branch is closed: `0-2-B-2`は完了。Hayate移行全体はデータ配置や主要pipelineの正本運用確認が残るため継続。
- Where we return to in the main route: `2-3 交通量較正`。

## 根拠の位置づけ

今回確認したのは、固定済みのHayate環境での実行可能性とPython直接依存の再現手順である。Python requirementsだけでSUMOのビルド内容やOS全体を完全再現できるとは扱わない。
