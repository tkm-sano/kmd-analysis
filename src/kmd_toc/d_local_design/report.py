"""Generate a Japanese report from evidence; unknown fields remain explicit."""
from .pipeline import read, dump, digest


def report(out):
    selected = read(out / 'SELECTED_CONFIG.json')
    benchmark = read(out / 'BENCHMARK.json')
    validation = read(out / 'VALIDATION.json')
    connection = read(out / 'COMPLETION.json')
    comparison = ['# 符号化比較（設計検証専用）', '',
        '|方式|n|論理/補助/総qubits|全状態|有効/不正状態|実行状態|方式|実測親wall秒|ピークRSS MiB|復号率|',
        '|---|---:|---|---:|---|---|---|---:|---:|---:|']
    for r in benchmark['results']:
        comparison.append(f"|{r['encoding']}|{r['n']}|{r['logical_qubits']}/0/{r['total_qubits']}|{r['states']}|{r['valid_states']}/{r['invalid_states']}|{r['status']}|{r['method']}|{r.get('parent_worker_wall_s','未実測')}|{r.get('peak_RSS_MiB','未実測')}|{r.get('decode_success_rate','未実測')}|")
    comparison += ['', '全方式で2便への割当てと訪問順の両方を符号化する。全有効状態は(n+1)n!、両局所部分非空なら(n−1)n!。',
        'one-hot: n+1位置×(n顧客+デポ区切り)。行/列を1-hotにするQUBO。Fは有向隣接と両端デポ費用。',
        'P=Σrow(Σx−1)^2+Σlabel(Σx−1)^2、H=F+AP。B=(n+2)max距離、A=B+1。F>=0で全有効F<=B、全不正P>=1なので不正状態を全有効より高くする。',
        'binary: n個のceil(log2 n)ラベル＋ceil(log2(n+1))分割位置。重複・範囲外ラベル・不正分割を棄却。',
        'compact: z=(n+1)rank(π)+split。rankはLehmer順位。z>=M(n)を棄却。古典encode/decodeは素朴実装O(n²)。',
        'binary/compactのコストはH[z]=D_local/B、有効以外2。B=(n+2)max距離により有効<=1。容量や勤務はこのペナルティに混ぜない。',
        '全方式はplus初期状態、Xミキサー exp(-iβΣX)。不正状態を保持しないため測定で検出・棄却する。修復は行わない。',
        'p=1、COBYLA最大8評価、学習256shots/評価、最終512shotsは資源測定専用PROPOSED。P1由来ではない。',
        '実回路はH層→exp(-iγH)対角位相→RX(2β)層。Aerは対角ゲートをnative実行する。対角ゲートを1個の1q/2qゲートと数えない。',
        '物理実装可能性はWalsh変換 H=Σα_S Z_S を用いる非切捨てパリティ回路で確認した。各SでCX列→RZ→逆CX、補助0。',
        '1層のRZ数2^q−1、CX数q2^q−2(2^q−1)。深さは実装順序のwire依存で算出。n2でnative対角と分解回路の全振幅を比較する。',
        'RESOURCE_BENCHMARK.csvに論理/総qubits、ゲート数・深さ、メモリ、時間、状態数、復号率、版とスキップ根拠を保存。ハードウェア結線へのroutingは含まない。',
        'MPSはn2 compact/binaryで実行し全振幅を独立テスト。大きいqはexact bond上限とwide oracleコストが未検証で安全見送り。one-hotの密状態メモリだけでMPS不可能とは判定しない。',
        '本コンパクト方式は指数個の古典費用表と指数ゲート合成を要する。19qubitは省メモリ表現であり効率的量子アルゴリズムや量子優位を意味しない。',
        '有効な符号状態の取得率、両局所部分非空率、全体物理可行率を区別する。全体可行率は限定completionログにのみ存在する。',
        '公式仕様: https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html 、https://qiskit.github.io/qiskit-aer/tutorials/7_matrix_product_state_method.html 、https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.DiagonalGate 。',
        'Webの最新版とインストール版を同一視しない。MANIFEST.jsonに実版を保存し、docs/d_local_design/evidence/simulator_sourcesのtag付きソースで確認する。']
    (out / 'ENCODING_COMPARISON.md').write_text('\n'.join(comparison) + '\n')
    architecture = '''# 量子局所再最適化の構成

今回のユーザー指示により本番D候補はColumn Generationを用いない。既存D/P1入口を変更せず独立実装する。APPROVEDは今回の役割分担、共通運行値、4枝各native1thread、保全、本実験HOLD。p/shots/最適化回数、符号化、完成器、選定規則、採択規則は提案。

入力LocalProblemは局所ID、2便(vehicle_id,trip_no)、n件ID、需要、デポを含む有向距離m/時間s、全体計画ID・入力/OD hash、全局所対象外ルート・制約、seedを保持する。詳細入力はlocal_n*.json。

出力はtrip_1,trip_2。順列πと分割sの組は一意で、候補数Σ_s C(n,s)s!(n−s)!=(n+1)n!。n8では362,880。これは制約を付す前の数であり、全列挙は古典検算である。

量子側は選定n件の便への割当てと各便内の相対順序を同時決定する。古典完成器は対象便の最初の除去位置へ量子の順序列を挿入し、それ以外の顧客の相対順序・便所属を固定する。他便も固定する。古典側で量子順序を再最適化しない。

同一車両なら第2便は第1便の帰着後にreadyとなる。異なる車両でも各車両の便接続を保持する。全体のready FCFSで具体的バースを再割当てし、容量・最大2便・時刻・積込1800秒・顧客120秒・勤務終了・バース排他を二重検証する。完成不能・量子割当/順序変更・物理違反を棄却記録する。

共通validatorは非空の活動便を要求するため空活動便は棄却する。量子の局所部分が空でも対象外顧客が残れば活動便は非空になる。局所空部分を許す/禁止する数学を両方検査し、局所空部分を許す提案と活動便非空の既存条件を区別する。

量子位相の費用は選定顧客だけの2本のデポ往復距離の代理指標であり、対象外顧客の境界挿入費用・全体Wを含まない。この設計上の限界を隠さずPROPOSEDとする。採択には必ず完成後の全計画D/Wを用いる。境界を含む位相費用への変更には別検算が必要。

Kは各枝・各サイクルの局所問題数、P=4は独立枝、Rは更新サイクル上限、外側統計反復は別物。局所対象選定は未探索優先・除去可能有向arc費用優先・両者のhybridを比較し、採用候補hybridは未探索数、除去費用、便ID、顧客IDの順で決定する。K=Vを1車両1問題とは定義しない。

coverageは保存済みB計画に対する選択だけのreplay。全P枝に同じ保存snapshotを使うためunionをP倍しない。計画更新後の実被覆・改善停滞・量子可行率とは区別し、未測定項目はnullにする。全体初期計画の作成をこの検証で実行しない。
'''
    (out / 'ARCHITECTURE.md').write_text(architecture)
    dw = '''# D/W採択規則（PROPOSED）

復号→量子割当/順序記録→固定完成→保持検査→全体二重物理検証→可行な場合のみ全体D/W再計算→比較記録→更新/棄却、の順とする。

D_new<=D_oldかつW_new<=W_oldで少なくとも一方が厳密小なら自動採択。一方改善・他方悪化はSAVE_NONDOMINATEDとして現行を維持し、両方の変化と積込スケジュール/経路変更という発生理由を記録する。双方悪化・一方悪化他方不変は棄却。同値は現行維持。非優越候補はCOMPLETION.jsonに量子順序・変化量を保持する。

比較単位は既存完成器の0.1mと整数秒に合わせる提案。元ODのdecimal文字列表現で全arcを加算し、全体距離を0.1m単位へROUND_HALF_EVEN。WはΣ(load_start-ready)秒。指標表示はkm/分。数値のiscloseによるPareto曖昧比較や重みは導入しない。

単体試験は双方改善、Dのみ改善、Wのみ改善、相反2方向、双方悪化、同値、完成不能、量子順序変更、全体物理違反、容量、便接続、移動時間、積込、バース、勤務終了、古い計画参照、不正復号を検査する。テスト結果はTEST_RESULTS.xmlとTEST_LOG.txt。限定実測のCOMPLETION.jsonは本実験のD/W性能結果ではない。
'''
    (out / 'DW_ACCEPTANCE.md').write_text(dw)
    approvals = '''# 承認状態

## APPROVED
- 今回指示の2便の個別再配分＋両便訪問順、量子決定保持、古典全体完成、CG不採用。
- 共通S1=1000/10/2、S2=2000/20/4、S3=4000/40/8、最大2便、需要/有向Route OD/容量/時刻/バース共通条件。
- AGENTS.mdの4枝CPU並列、各native1thread、手法間逐次、有限作業量、既存成果物保全、本実験HOLD。
- 数理検算・単体試験・限定回路・資源計測・選択被覆検証の実行許可。

## PROPOSED
- 3符号化、Xミキサー、代理距離コスト、固定ブロック挿入＋FCFS完成、hybrid局所対象選定。
- 測定用p=1/最大8評価/学習256/最終512shots。P1 p2/1000/80から転用していない。
- Pareto自動採択、相反保存、同値現行維持、0.1m/1秒比較。
- 局所空部分を許す候補。共通validatorの空活動便禁止を維持。

## UNRESOLVED
- 新構造Dの正式深さ・shots・評価回数・初期角度・代理コスト採否。
- 同じ全体計算時間予算によるn比較。現行は有限作業量で旧時間予算を復活させない。
- 新初期計画作成と4枝最大wall全体見積り、計画更新を伴う被覆とD/W停滞の裏付け。
- 総合研究評価/反復/精度、正式本実験契約。

P1 docs/p1_pricing/APPROVALS.mdのp2/1000shots/80評価/P4はP1専用。旧D termination_v1のp2/10000shots/80評価/pricing_rounds2は旧アーキテクチャの履歴設定であり、新局所Dへの承認を推定しない。P4はP1からでなく現行AGENTS.mdに独立した根拠がある。

数理と限定シミュレーションがPASSでも本実験の採用・実行を承認しない。残存ゲートはSELECTED_CONFIG.jsonのgaps/required_approvals。
'''
    (out / 'APPROVALS.md').write_text(approvals)
    lines = ['| 項目 | 単一推奨値 | 根拠 | 状態 |', '|---|---:|---|---|',
             '| 局所配送先数 n | 未確定 | 同一予算でのn比較に必要な条件不足 | UNRESOLVED |',
             '| K_S1 | 未確定 | 更新後被覆・正式呼出し費用未検証 | UNRESOLVED |',
             '| K_S2 | 未確定 | 同上 | UNRESOLVED |', '| K_S3 | 未確定 | 同上 | UNRESOLVED |',
             '| 改善サイクル上限 R | 未確定 | 更新後被覆・停滞未測定 | UNRESOLVED |', '',
             '**本実験HOLD。数値を捏造せず、順位規則の欠測キーを飛ばした最終設定は出していない。**', '',
             '## A. 採用する量子局所問題',
             '8件例: 元便1=[a,b,c,d]、元便2=[e,f,g,h]から、量子出力便1=[h,b,e]、便2=[c,a,g,d,f]を得る。割当てと順序の両方が変化する。古典側はこの割当て・相対順序を変えずに全体時刻とバースを完成し、不可行なら理由付き棄却する。',
             '詳細はARCHITECTURE.md、local_n*.json、COMPLETION.json。', '', '## B. 採用する符号化',
             '正式採用は保留。compact順位＋分割はn7/8/9で実回路を試験した。3方式の全状態、無効率、回路、ミキサー、測定はENCODING_COMPARISON.mdとRESOURCE_BENCHMARK.csv。', '',
             '## C. nの採用理由', 'n8は19論理qubits・補助0。362,880候補を全列挙し3符号化の復号と費用を検算。n7は16qubits、n9は22qubits。one-hotが実行不能でもn8自体は不採用としない。',
             'n7/8/9はいずれも最終採用保留。同一全体時間予算、正式量子設定と初期計画費用が不明なのでn9のサイズだけを優先しない。', '',
             '|n|方式|総qubits|測定親wall秒|ピークRSS MiB|復号率|', '|---:|---|---:|---:|---:|---:|']
    for r in benchmark['results']:
        if r['encoding'] == 'compact_rank_split' and r['method'] == 'statevector' and r['n'] >= 7:
            lines.append(f"|{r['n']}|compact rank/split|{r['total_qubits']}|{r.get('parent_worker_wall_s')}|{r.get('peak_RSS_MiB')}|{r.get('decode_success_rate')}|")
    lines += ['', '## D. KとRの採用理由',
              'n7/8/9×系列A/B/C×R5/13/25の27組を各S1〜S3で評価（規模別81組）。COVERAGE_ANALYSIS.csvはサイクルごとに実ID、重複、未探索、同/異車両を保持する。TIME_ESTIMATES.csvは全組の絶対呼出し数・部分時間予測を保持する。',
              '以下は最終推奨ではなく、先頭2つの被覆キーと最少呼出しだけの診断値。同一時間予算でのn比較キーが欠測なので正式順位付けを停止した。',
              '```json', __import__('json').dumps(selected['resource_only_diagnostic'], ensure_ascii=False, indent=2), '```', '',
              '量子可行率・古典棄却率・D/W停滞・4枝更新後のcoverageは選択replayからは算出できずnull。nKR/Nを実coverageと呼ばない。', '',
              '## E. D/W採択規則', 'Pareto優越のみ自動採択。一方改善・他方悪化なら相反候補として保存し現行維持。0.1m・1秒比較も含めPROPOSED。DW_ACCEPTANCE.md参照。', '',
              '## F. 計算資源', 'MANIFEST.jsonにCPU/実メモリ/cgroup全祖先/affinity/版を保存。各新規子プロセスを1コア/native1threadに固定し、事前メモリ評価・RSS監視・240秒安全停止を適用。安全上限は本実験予算ではない。',
              '密状態vectorとMPSを実測し、NumPy独立状態更新と分解回路も照合。n7/8/9はnative対角を実行する。1q/2qゲート分解の指数コストとdepthはCSVに別記し、native oracle depth3でごまかさない。',
              '量子calls、最適化評価、学習shots、最終shots、回路準備、simulator、completion、検証、更新を分離。P4×K×Rを検算し、wallを枝合計にしない。',
              'TIME_ESTIMATES.csvの部分予測は単一局所問題実測の外挿。初期計画と親の全体wallは未実測null。全体予算適合や本実験実行可能とは結論しない。', '',
              '## G. 未承認事項', *['- ' + gap for gap in selected['gaps']], '',
              '## H. 保全・検証結果', '既存D/P1入口、A〜C、凍結需要、OD、既存結果を変更しない追加実装。証拠台帳はdocs/d_local_design/evidence/PRESERVATION_BEFORE.jsonl、PRESERVATION_AFTER.json、Git前後記録。README/commit/push変更なし。',
              '単体テストと関連回帰の結果はTEST_RESULTS.xml/TEST_LOG.txt/REGRESSION_RESULTS.xml/REGRESSION_LOG.txt。初回失敗も保存し修正理由を報告する。', '',
              '## 実行・再開コマンド', '```bash',
              'export PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1',
              f'/tmp/kmd-p1-pricing-20261118/bin/python -B -m kmd_toc.d_local_design all --output {out}',
              '# allの代わりにvalidate / benchmark / coverage / select / reportで各工程を再開',
              '```', '入力・設定・ソースhashが変化した再開は拒否。既存完了kernelは再使用。新しいsourceでは別出力へ保存する。', '',
              '## 最終判定', f"A={selected['A_mathematical_validity']}、B={selected['B_simulator_local_resource_validity']}、C={selected['C_production_adoptability']}。", '本実験を開始せず終了する。']
    (out / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    files = [p for p in out.rglob('*') if p.is_file() and p.name != 'ARTIFACT_HASHES.json' and not p.name.endswith('.tmp')]
    dump(out / 'ARTIFACT_HASHES.json', {str(p.relative_to(out)): digest(p) for p in files})
