# グループ受付モデル v2

## 条件

hayateの正式親登録は `formal_J30_v4` である。今回承認された条件は `configs/grouped_loading_20261124_v2/conditions.json` である。旧結果・旧Freeze・旧診断出力を参照資産として保存する。正式実験はこの作業から投入しない。

- 需要はS1・S2・S3の1,000・2,000・4,000配送先であり、1配送先1箱、1便60箱、最大2便。配置車両10・20・40台、バース2・4・8、入力ODの有向秒は弧ごとに切上げ、勤務・休憩条件は継承する。
- 三菱MINICAB EV CD 20.0kWh・2シーター・2WD。クロネコボックス8を外寸38×27×15cm、梱包込み5kgとする。60箱300kg、4列×4列×4段の配置は152×108×60cmであり、公表積載350kg・荷室内寸183×130×123cm内である。積付け固定・荷室形状・取り出し順の実車検証は別の適用範囲。 [車両諸元](https://www.mitsubishi-motors.co.jp/lineup/minicab_ev/spec/spe_02.html) [梱包外寸](https://faq.kuronekoyamato.co.jp/app/answers/detail/a_id/8661/c/4) [80サイズ重量上限](https://www.kuronekoyamato.co.jp/ytc/customer/send/search/payment/size/)
- 数値順の車両IDを5台ずつ固定し、第1組08:00:00、後続は1秒以上の昇順、最後は09:00:00以下。空組は予定時刻を計画ハッシュに保持し、受付・積込のイベントは0件。
- 第1便の実際の受付時刻はグループ予定時刻。物理readyはその時刻までに完了する仮定であり個別の時刻値は不明としてnullで保存。旧来の車両別readyは入手元の入力ハッシュ照合に残るだけであり、新版の受付モデルに読み込まない。第2便は第1便の帰着＋準備0秒。
- 単一FCFSで受付時刻と車両ID数値順、空いている最小IDバース。第2便の便番号による優先はない。同一車両の第1便と第2便は900秒の積込と移動により受付が同時にならない。積込900秒、積込終了時に出発。
- Wは第1便受付から積込開始、第2便帰着から積込開始。受付前の勤務開始からの経過秒は補助項目であり、実際の休憩・非勤務・作業時間を表さない。Dは有向ODの総距離で両指標の主表示はkm／個、分／台・日。I_dualの基準・ゼロ例外・既存の順位付けを継承する。

## 各方式と有限予算

- Bは有向Clarke–Wrightと既存の路線集約を再実行し、ルート集合を決める。第1便を長いルート優先または顧客数優先等の決定的順で割り当て、第2便の機会は帰着見込の早い車両優先を先に試す。各組の受付は直前までの第1便積込を並べたときの次の空きバース時刻を候補とし、1秒間隔と09:00上限から決まる範囲に制限する。全便を再評価して最初の可行解を保存する。最大は列挙順3×第1便台数の候補数×割当順2。10台／2バース等の容量に依存し、旧601秒固定や旧車両別時刻均等分散には依存しない。C・Dの結果を参照する経路はない。
- Cは固定Bの訪問順・車両スロットをOR-Tools Routingに渡し、既存探索チェック上限を使用する。Routingの経路集合をCPへ渡し、便割当と第2組以降の受付時刻を同じモデルで探索する。CP内の待ち・帰着・距離は保存可能な共通評価計画と照合する。既存の各段階の競合上限、改善解上限、単一スレッド、相対評価式を使用する。
- D両方式は同じ外側の再割当、Tabuとaspiration、既存D3の群移管・回転、奇数反復の現在計画／偶数反復の再割当上での順序探索を使用する。3古典枠のうち1枠を時刻候補へ、最大2枠を再割当へ配分し、局所順序の最大4枠は継承した。候補上限は計7／反復、10反復・70／枝。時刻提案は容量由来の点と1秒幅の許容端を決定的に切り替える。時刻専用の追加乱数はない。既存の局所問題構築、量子・古典局所探索、用途別seedを使用する。
- 計画ハッシュには経路、受付時刻、グループ・時刻定義・計算済み全便を含む。Dの候補JSONは経路と受付時刻の両方で識別し、同じ固定B・seedで再開したことを確認する。採択・最良はB基準であり、C値をD入口は読み込まない。
- 限定予備は既存予備の同じ需要、比較単位、seed対応の3ケース。資源は既存hayateの協調リースで1ケース、方式間逐次、D4枝各1CPU・native 1、Cは単独。診断や予備は正式Jへ加算しない。

## 操作と証跡

```bash
cd /home/takuma/kmd-analysis
py=/tmp/kmd-p1-pricing-20261118/bin/python
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
pilot=$PWD/output/iterative_d3/grouped_loading_20261124_v2_pilot
"$py" -B scripts/run_grouped_loading_v2.py pilot --output "$pilot"
"$py" -B scripts/run_grouped_loading_v2.py resume-pilot --output "$pilot"
"$py" -B scripts/audit_grouped_loading_v2.py "$pilot" /tmp/kmd-grouped-v2-audit
"$py" -B scripts/plot_grouped_pilot_v2.py "$pilot" /tmp/kmd-grouped-v2-audit /tmp/kmd-grouped-v2-figures
PYTHONPATH=src "$py" -B -m pytest -q -p no:cacheprovider tests/grouped_loading_v1 tests/grouped_loading_v2
```

MPSシミュレーションと、QAOAにより変えた訪問順の直接寄与、探索軌跡の間接寄与を区別する。固定Bを30観測に複製せず、未完了計画のD/Wは補完しない。

## 正式登録の操作

正式登録先は `output/iterative_d3/formal_J30_grouped_v2` である。固定Bは登録に保存され、J＝30／規模、計90比較ケース、C単独90実行、D両方式720枝、計810 solverジョブを登録する。乱数の方式別・用途別台帳と元の試行対応を継承する。実行mirrorのパスと照合したソース数は正式登録の `MIRROR_BINDING.json` に記録する。

```bash
cd /home/takuma/kmd-analysis
py=/tmp/kmd-p1-pricing-20261118/bin/python
formal=$PWD/output/iterative_d3/formal_J30_grouped_v2
mirror=$("$py" -B -c 'import json,sys; print(json.load(open(sys.argv[1]))["mirror"])' "$formal/MIRROR_BINDING.json")
entry=$mirror/scripts/run_grouped_formal_v2.py
"$py" -B "$entry" preflight --output "$formal"
"$py" -B "$entry" aggregate --output "$formal" --analysis "$formal/analysis_$(date +%Y%m%dT%H%M%S)"
```

実際に開始するときは `"$py" -B "$entry" run --output "$formal" --execute` を使用する。開始記録のある登録を再開するときは `"$py" -B "$entry" resume --output "$formal" --execute` を使用する。hayateの協調リースを取得できない場合は、同じ登録の実行状態と管理対象workerを確認し、終了後に再開する。受領記録と計画の不整合が検出された場合は該当パスを保全し、該当成果物と枝記録を照合してから再開する。集計では該当行の理由が保存され、対の有効件数には入らない。

CP-SATの競合上限256は独立した内部SAT solveごとのパラメータである。予備S3のCP-SATが報告した集約競合数は502,563であり、同規模のCの壁時計は約535秒であった。固定の外側段階数と改善解上限を継承し、実行時間を結果から再設定していない。 [OR-Tools v9.14のパラメータ定義](https://github.com/google/or-tools/blob/v9.14/ortools/sat/sat_parameters.proto#L268-L276)
