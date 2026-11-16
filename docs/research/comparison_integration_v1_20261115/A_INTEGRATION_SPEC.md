# A_rule_v1の非改変接続

凍結対象は `configs/toc_delivery/comparison_a_rule_v1_freeze_20261115.json` に列挙した原CLI・生成器・規則検証器・入力アダプタ・設定2件・既存テストの7ファイル。原結果・文書は別のPRESERVATION_BEFORE.jsonにも記録する。新規comparison_v1/CLI/設定/テストは凍結対象から分ける。

旧単独入口は `scripts/run_a_rule_v1.py:worker → rule_inputs.load_input → rule_v1.generate → validate_plan/audit_rule`。旧比較入口の `dwt.methods.generate(method=A)` は construction.create_plan(A2)→complete→complete_routesであり、新Aとは別物のまま保全する。

新入口は `scripts/run_comparison_v1.py register/run/aggregate`。新契約のregistryでAは `frozen_A_rule_v1_direct_FCFS` に一意対応する。比較親は入力をhash照合し、共通Problemを読んでからfresh workerを起動する。workerは同じ未割当Problemを再読込し、凍結cfgのdeadline/候補上限を使って凍結rule_v1.generateを直接呼ぶ。最適化完成器へは渡さない。path_PID.jsonlに実際の関数呼出を保存する。

元からPlan形式が共通なので、意味を変える変換は不要。`asdict → ensure_ascii=False/indent=2/newline` は原CLIと同じJSON書式で候補bytesを保存し、親はhash照合とload_planで検査する。採用時は受信bytesをそのままコピーする。キー順・車両割当・便所属・訪問順・積込順・ready・load/departure/returnを変更しない。D/Wだけの一致では同一性を認定しない。意味上のhashはcanonical JSONでtuple/listの表現差を正規化するが、車両・便・訪問・時刻の配列順は保持する。

親共通検証はvalidate_planと、生成器を呼ばないDecimal audit_planでD/W・制約を再計算する。Aだけはaudit_ruleでFCFS/全帰着/OH、凍結版/採用回数/厳密改善trace/停止等を追加確認する。AのFCFSをB/C/Dへ課さない。B/C/Dは既存execute_parallel/methods.generateをそのまま呼び、同じ共通物理検証だけを通す。

接続確認は登録したS1/S2/S3各1回を保存済み原本とraw bytes・semantic hash・全便/全訪問時刻で照合する。S2は原CLIのworkerを新しいmanifest/outputで1回起動し、同じ照合を行う。原S2 hash `64114d3fed738a14198c0958a4c3cdd6bafb9c9d81926bdaf276250bd651f4d9` は開始時に原本の実bytesと照合済みで、期待値を新出力へ書換えない。

保存済み計画は同一性照合だけに使用し、生成の入力や新T測定の代用品にはしない。新比較Tは起動/初期化/候補受渡し/親の最終検証も含むため、旧単独Tと別時間種類である。S2単独のnative Tも参考として区別して保存する。
