"""Compile reports only from completed saved trials; verify protected originals."""
import argparse
from collections import Counter
import csv
import difflib
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from kmd_toc.dwt.audit import audit
from kmd_toc.dwt.evaluation import eligible

parser = argparse.ArgumentParser()
parser.add_argument('--root', default='output/toc_delivery/dwt_balance_20261113_v1/revision_1_3_1')
parser.add_argument('--publish-docs', action='store_true')
args = parser.parse_args()
root = Path(args.root)
parent = root.parent


def read(p):
    return json.loads(Path(p).read_text())


def save(p, value):
    Path(p).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(p):
    with Path(p).open('rb') as h:
        return hashlib.file_digest(h, 'sha256').hexdigest()


rows = read(root / 'ALL_TRIALS.json')
main = [r for r in rows if r['phase'] == 'limited']
assert len(main) == 12, 'All registered limited attempts must be represented'
assert len([r for r in rows if r['phase'] == 'control']) == 4
assert len([r for r in rows if r['phase'] == 'baseline']) == 1
independent = audit(root)
assert independent['passed'] == independent['checks'], 'Independent numeric audit failed'
standard = read(root / 'STANDARD_OUTPUT_AUDIT.json')
browser = read(root / 'BROWSER_VALIDATION.json')
data_manifest = read(root / 'DATA_MANIFEST.json')
assert data_manifest['files'] and all(v['checked_now'] for v in data_manifest['files'].values())
assert standard['passed'] == standard['checks'] and not standard['failed']
assert browser['passed'] == browser['checks'] and not browser['failed']
front = read(root / 'THREE_OBJECTIVE_EVALUATION.json')
baseline = next(r for r in rows if r['phase'] == 'baseline')
registered = read(root / 'limited_REGISTERED.json')
source_changes = [p for p, h in registered['code_hashes'].items() if sha(p) != h]
assert sha(registered['config_path']) == registered['config_sha256']
assert all(r.get('demand_seed') is None and r.get('demand_random_generator') is None for r in rows)
before = read(parent / 'PRESERVATION_BEFORE.json')
changed_originals = [p for p, h in before['files'].items() if not Path(p).exists() or sha(p) != h]
allowed = {'src/kmd_toc/common/models.py'}
assert sha(parent / 'SOURCE_COMMON_MODELS_BEFORE_IO.py') == before['files']['src/kmd_toc/common/models.py']
unexpected = [p for p in changed_originals if p not in allowed]
status = subprocess.check_output(['git', 'status', '--short', '--untracked-files=no'], text=True)
preservation = {'protected_files': len(before['files']), 'changed_originals': changed_originals,
                'intentional_changes': [{'path': p, 'before': before['files'][p], 'after': sha(p),
                                          'reason': 'same pinned Snap policy passed once per input validation; remove repeated file reads, no constraint change'}
                                         for p in changed_originals if p in allowed],
                'unexpected_changes': unexpected,
                'frozen_eight_unchanged': all(sha(p) == h for p, h in before['files'].items() if '/frozen_demand/v1/' in p),
                'registered_source_changes_during_limited_experiment': source_changes,
                'tracked_status_before': before['tracked_status'], 'tracked_status_after': status,
                'passed': not unexpected and not source_changes and status == before['tracked_status']}
save(root / 'PRESERVATION_FINAL.json', preservation)
assert preservation['passed'], preservation
save(root / 'ENVIRONMENT.json', {'python': sys.version, 'platform': platform.platform(),
      'packages': {p: importlib.metadata.version(p) for p in ['numpy', 'scipy', 'ortools', 'qiskit', 'pytest', 'matplotlib']},
      'CPU': subprocess.check_output(['lscpu'], text=True),
      'timing': 'time.perf_counter wall; complete common input read through final second verification; uniform import-only library setup before T, recorded separately',
      'worker_launch_modes': dict(Counter(r.get('worker_launch_mode') for r in rows)),
      'dependency_setup': {p.name: read(p) for p in root.glob('*_DEPENDENCY_SETUP.json')},
      'threads': 'OR/CP-SAT=1; OMP/BLAS environment=1; HiGHS internal behavior not independently certified'})

table = '|手法|W上限 [分]|予算τ [秒]|D [km]|W [分]|T_program [秒]|状態|\n|---|---:|---:|---:|---:|---:|---|\n'
for r in main:
    cells = [r['method'], f"{r['epsilon_W_min']:.4f}", str(r['tau_s'])]
    cells += ['未取得' if r.get(k) is None else f'{r[k]:.6f}' for k in ['D_km', 'W_min', 'T_program_s']]
    cells += [r['status']]
    table += '|' + '|'.join(cells) + '|\n'

qrows = []
for r in main:
    if r['method'] != 'D' or r['status'] != 'COMPLETE':
        continue
    plan = read(Path(r['trial_directory']) / 'plan.json')
    m = plan['method_settings']
    qrows.append({'trial_id': r['trial_id'], 'quantum_calls': m['quantum_calls'],
                  'training_evaluations': sum(x['training_evaluations'] for x in m['quantum']),
                  'training_shots': sum(x['training_total_shots'] for x in m['quantum']),
                  'final_shots': sum(x['final_total_shots'] for x in m['quantum']),
                  'circuit_build_s': sum(x['circuit_build_s'] for x in m['quantum']),
                  'parameter_training_s': sum(x['result']['training_seconds'] for x in m['quantum']),
                  'statevector_sampling_decode_s': sum(x['simulation_sampling_decode_s'] for x in m['quantum']),
                  'sampling_only_s': None, 'new_quantum_routes': m['quantum_new_routes'],
                  'new_quantum_routes_in_final': m['new_quantum_routes_in_final'],
                  'base_columns': m['base_columns'], 'hybrid_columns': m['hybrid_columns'],
                  'catalogue_truncated': (m.get('hybrid') or {}).get('catalogue_construction', {}).get('truncated_at_time_limit'),
                  'completion_selected_source': m['completion_selected_source']})
save(root / 'D_QUANTUM_ATTRIBUTION.json', qrows)
controls = []
by_id = {r['trial_id']: r for r in rows}
for r in rows:
    if r['phase'] != 'control':
        continue
    spec = read(Path(r['trial_directory']) / 'spec.json')
    counterpart = by_id[spec['paired_quantum_trial']]
    controls.append({'quantum_trial': counterpart['trial_id'], 'classical_control': r['trial_id'],
                     'paired_solver_seed': r['solver_seed'] == counterpart['solver_seed'],
                     'D_quantum': counterpart.get('D_km'), 'W_quantum': counterpart.get('W_min'), 'T_quantum': counterpart.get('T_program_s'),
                     'D_control': r.get('D_km'), 'W_control': r.get('W_min'), 'T_control': r.get('T_program_s'),
                     'quantum_status': counterpart['status'], 'control_status': r['status'],
                     'interpretation': 'whole-budget paired ablation; stochastic scheduling and different remaining completion time prevent attributing every final difference solely to quantum candidates'})
save(root / 'D_CLASSICAL_CONTROLS.json', controls)
control_table = '|W上限 [分]|τ [秒]|量子あり D/W/T|量子なし D/W/T|状態（あり／なし）|\n|---:|---:|---|---|---|\n'
for c in controls:
    trial = by_id[c['quantum_trial']]
    vals = lambda side: '未取得' if c['D_' + side] is None else '/'.join(f"{c[k + '_' + side]:.6f}" for k in ['D', 'W', 'T'])
    control_table += f"|{trial['epsilon_W_min']}|{trial['tau_s']}|{vals('quantum')}|{vals('control')}|{c['quantum_status']}／{c['control_status']}|\n"
with (root / 'A_TO_D_DWT_COMPARISON.csv').open('w', newline='') as handle:
    keys = ['trial_id', 'method', 'epsilon_W_min', 'tau_s', 'D_km', 'W_min', 'T_program_s',
            'T_human_s', 'T_program_role', 'status', 'input_hash', 'OD_hash']
    writer = csv.DictWriter(handle, fieldnames=keys)
    writer.writeheader()
    writer.writerows({k: r.get(k) for k in keys} for r in rows if r['phase'] in ['limited', 'baseline'])
old_main = [r for r in read(parent / 'ALL_TRIALS.json') if r['phase'] == 'limited']
fix = {'old_completed': sum(eligible(r) for r in old_main), 'old_attempts': len(old_main),
       'new_completed': sum(eligible(r) for r in main), 'new_attempts': len(main),
       'same_problem_epsilon_tau_seeds': all(any(
            r['method'] == s['method'] and r['epsilon_W_min'] == s['epsilon_W_min'] and r['tau_s'] == s['tau_s']
            and r['solver_seed'] == s['solver_seed'] and r['quantum_seed'] == s['quantum_seed'] for s in old_main) for r in main),
       'old_failures_preserved': [r['trial_id'] for r in old_main if not eligible(r)],
       'interpretation': 'code-revision regression, not additional independent statistical repetitions'}
save(root / 'REVISION_COMPARISON.json', fix)
testlog = (root / 'REGRESSION_TESTS.log').read_text()
test_count = re.findall(r'(\d+) passed', testlog)[-1]

resources = {'sum_trial_T_program_s': sum(r['T_program_s'] or 0 for r in rows),
             'sum_export_wall_s': sum(r.get('export_wall_s', 0) for r in rows),
             'max_recorded_getrusage_RSS_KiB': max((r['max_rss_KiB'] for r in rows if r.get('max_rss_KiB') is not None), default=None),
             'RSS_scope': 'getrusage process high water including inherited library pages; not algorithm-exclusive memory',
             'batch_wall': {p.name: read(p) for p in root.glob('*_BATCH_TIMING.json')},
             'dependency_setup': {p.name: read(p) for p in root.glob('*_DEPENDENCY_SETUP.json')},
             'samples': read(root / 'RESOURCE_SAMPLES.json') if (root / 'RESOURCE_SAMPLES.json').exists() else None}
save(root / 'RESOURCES.json', resources)
valid_count = sum(eligible(r) for r in main)
methods_available = {r['method'] for r in main if eligible(r)}
numeric_comparison_status = 'GO' if methods_available == {'B', 'C', 'D'} else 'HOLD'
overall = 'CONDITIONAL GO' if numeric_comparison_status == 'GO' else 'HOLD'
source = str(root)
qselected = sum(r['new_quantum_routes_in_final'] for r in qrows) if qrows else None
comparison = f'''# DWT最終比較：予算付き限定S1

2026-11-13。総合判定 **{overall}**。計画生成→共通完成→二重検証→実測T予算確認→標準出力→3目的解析を実行した。主統計実験・全VRP最適性・量子優位の判定は未成立。

証拠根：`{source}/`。設定：`{registered['config_path']}`。旧v1〜v1.3の結果・失敗・中止記録と旧Route v2結果は別保存で、主frontには混在させない。

## 限定結果

{table}

受理は{valid_count}/12。無効・未取得試行もALL_TRIALS.csv/JSONへ保存した。「可行解なし」は予算内取得失敗であり、数学的不可行の証明ではない。

観測された非支配点数：{json.dumps(front['front_count_by_method'], ensure_ascii=False)}。点IDはNONDOMINATED.csv、全支配関係はDOMINANCE.csv。入力hashが異なる点は支配比較しない。各条件n=1であり、性能順位・有意差・信頼区間を主張しない。微小なwall時間差も観測frontに影響する。予算と探索seedの双方が異なるため、純粋な予算の因果効果とも解釈しない。

S1参照値D551.1398/W422.45/T60と4重み、時間参照倍率0.5/1/2の全感度をWEIGHT_REFERENCE_SENSITIVITY.csvへ出力。Aの人手Tを混在させない。重み別最小値を唯一の研究結論とせず、生D/W/Tとfrontを併記する。

## 単一A

AはA2・角度0°のルールを事前固定し、共通完成器に接続した。状態={baseline['status']}、D={baseline.get('D_km')}km、W={baseline.get('W_min')}分。T_program={baseline.get('T_program_s')}秒は補助プログラム値でありAの人手Tではない。人手T全体は未校正・未取得。日本郵便/Loogiaの熟練300〜600秒・新人1800〜3600秒は1回のルート作成工程の外部参照で、S1全体秒数へ換算していない。D/Wは同じ計画に対応する推計値で、佐川急便の実績ではない。

## Dの量子部分

成功したD試行の新量子経路最終採用は合計{qselected}本。D_QUANTUM_ATTRIBUTION.jsonに回路構築・訓練・評価回数・訓練標本・最終shots・新規候補・日列・最終完成を分離保存。sampling-only時間は未測定でnull、状態ベクトル＋標本＋復号の合算を保存した。量子実機実行は0。

4条件すべての量子なし対照を登録・実行し、D_CLASSICAL_CONTROLS.jsonで同じsolver_seedの対応差を保存した。これは独立反復ではない。対照は候補プールと残り完成器時間も変わるため、最終値の差だけを量子固有効果と呼ばない。日列の有限探索、列構築打切り、CPのincumbent選択を記録し、量子由来改善を推測しない。

{control_table}

表中の順はD[km]/W[分]/T_program[秒]。失敗時に値を補完しない。

## 成立する範囲・残る制約

D/Wトレードオフは人工exact-cover証人で独立に検証した。実S1のε/τ反応はBUDGET_EPSILON_RESULTS.csvで計画ごとに示す。S1ではCの30秒/90秒条件に距離差があり、W上限の変更でも完成計画の待機時間が変わった。ただし、この2水準で明瞭なD対Wの反対方向の変化を実証したとは主張しない。人工証人の6.1/8.1kmを実S1値に使わない。S2/S3は共通入力/OD/容量の事前監査と同一CLIを整備したが、未実行。DのCW二乗メモリ、日列O(VR²)、nativeソルバーの大規模資源と本番shots/反復数の検証が残る。

Dと量子なし対照はいずれも厳しいW・30秒条件で初期共通完成器のCP UNKNOWNとなり、検証済み計画を取得できなかった。共通条件を緩めず失敗を残した。次版では短予算での初期可行計画取得・時間配分を小規模/中間規模で検証する必要がある。

主実験開始はHOLD。固定S1条件の独立seed pilotから分散・必要試行数・効果量・停止規則を決め、Dの量子候補の限定領域とshotsの校正を終える必要がある。追加の限定検証は同じパイプラインで実施可能。仮説を結果に合わせて追加・変更していない。
'''
validation = f'''# DWT実装・独立検証報告

2026-11-13。限定実装の総合判定{overall}。根拠は`{source}/`。

## 判定

|項目|状態|結果・制限|
|---|---|---|
|3目的定式化|GO|内部D/W、外部手法/予算/実測Tの二段階|
|ε制約法|GO|共通完成器のW上限と独立再検査。旧422.45分も維持|
|T予算制御|GO|残時間配分、親watchdog、最終実測。超過は不採用|
|正規化加重和|GO|固定共通参照・4重み・時間参照感度。欠測を補完しない|
|パレート分析|GO|有限観測集合の非支配点、別実装で全件照合|
|B〜D公平性|{numeric_comparison_status}（限定範囲）|同入力・OD・制約・完成器・T境界、同一CPU affinity。候補能力・OS負荷は異なり得る|
|S1限定実験|{numeric_comparison_status}|全12試行実行、{valid_count}受理。失敗も保持|
|S2/S3適用準備|HOLD|入力とCLIあり、本計算資源・結果は未検証|
|独立検証|GO|{independent['passed']}/{independent['checks']}項目合格|
|標準出力・可視化|GO|受理計画は7標準ファイル・実道路GeoJSON・図・HTML|

## 実施内容

既存207件と新規26件、合計 **{test_count}件の異なるテストが合格**。227件・24件・追加2件の実行には重複があり、233件の一括実行とは呼ばない。TEST_RUNS.jsonと全実行ログを参照。新規はD/W再計算、同点・格子丸め・支配、無効/欠測排除、重み/参照、予算境界、実OR上限、人工トレードオフ、CP UNKNOWNでも検証済みincumbent保持、無効incumbent拒否、実AOA/量子なし、標準hash、登録入力改変拒否、同一設定の1回読込、実測検証時間による予約、協調停止と例外区別、純粋なライブラリ準備、起動方式の引渡し、単一Aの時間境界を検査した。

旧S1を旧入口で各1回再実行し、全B/C/DのD/W・入力hashが一致。LEGACY_REPRODUCTION_CHECK.jsonは親ディレクトリに保存。旧Tは33.05/93.11/82.94秒の新観測を得たが、旧Tを上書きしていない。旧T境界は共通検査まで、新版は第二再計算まで含む。また新版は全方法同じライブラリ和集合の準備を入力読込前に別計測するため、旧Tとの速度比を主張しない。

小規模道路24条件は全て標準出力を作成。S1は12試行、量子なし対照4試行、単一Aを1試行実行。重複実行・既存出力上書きは拒否。予備と本番を区別し、異条件や修正前後の同seedを独立反復と数えない。

## 失敗と修正履歴

v1の受理は{fix['old_completed']}/12。未取得初期計画、日列全構築が段階予算を超える問題、最後のCP解未取得により既得計画を失う問題を確認した。旧版の失敗と全結果を保全した。

v1.1では、全手法共通でgreedyまたは既得計画を二重検証したincumbentとして保持し、CPが解を返さない場合や劣る場合は検証済み計画を選択する。無効解の修復ではない。Dでは同じcalendarと走査順を保ち、35%の構築時間枠をループ内で点検し、seed被覆を先に含む部分カタログを構築する。途中打切りの閉鎖を全候補領域の閉鎖と呼ばない。完了段階ログをT内で保存する。

v1.2では診断スタックでProblem.validate→全地点Snap.validate→共通設定ファイル再読込というO(N)回のIOを確認し、Problem.validate内で既にhash検証した同じalert値をprivate helperへ渡すようにした。公開Snap.validateの意味は保持する。設定ファイルは各入力検証で必ずhash確認し、制約値やODを変えていない。NFS待機も観測され、wall時間へのIO変動は残る。全/proc資源走査は負荷を観測して停止し、旧cohortを保存した。最終cohortは同一CPU0で逐次実行し、旧cohortと混在させない。

v1.3で実測した検証時間に基づく共通予約と、全手法同一のライブラリimport準備を導入した。準備は入力・回路・ソルバーを実行しない。v1.3では実行関数へのfork方式引渡し欠落があり、実際はfresh execだったためS1前に停止・保全した。v1.3.1で引渡しを修正し専用回帰テストを追加した。最終試行は全て起動方式・CPU・準備秒をmetricsへ記録した。native thread数1を確認できたimport-only親から独立した新規子を作り、各子はT開始後に入力を読み直す。親に計算済み計画や探索状態は存在しない。ライブラリ準備とバッチ全時間はRESOURCES.jsonへ別記した。

同じ需要・W上限・τ・seed・shotsを維持した新版の受理は{valid_count}/12。REVISION_COMPARISON.jsonを参照。短予算で初期計画を取得できないケースを成功扱いしない。バグ修正前後の同seed比較を性能分布へ加算しない。

旧workerが入力experiment.random_seedをdemand_seedとして保存した意味上の誤りも確認した。旧生記録を保全し、v1.2でdemand_seed=null、input_experiment_seed=元の値として直接記録する。失敗試行の経過をT_attempt_wall_sへ分け、検証済み計画のTは未取得ならnull。計画、実際に使用したsolver/quantum seedを補正して成功化する変更ではない。

## 独立性と資源

独立監査は生JSON/NPY、Decimal、時刻区間、GeoJSONとの訪問順、全支配比較、J再計算を使用し、主生成器・主パレート関数を呼ばない。元の共通検査とbaseline独立再計算に加える第三確認。形状は保存Routeのnode列と同版PBFから復元し、全区間のRoute距離とODを照合する。直線経路は代入しない。

さらに標準出力の独立監査{standard['passed']}/{standard['checks']}件、実道路区間{standard['road_arcs']}件を照合し、形状長とOD距離の最大絶対差{standard['max_abs_shape_delta_m']:.6f}m（許容0.35m）。生地点座標・snap・訪問順・CSVの全時刻も照合した。Chrome実操作{browser['passed']}/{browser['checks']}件合格。失敗行の表示、front、実道路描画、車両/便フィルタ、ガント、図、外部サービス通信なしを検査し、画面をscreenshotsへ保存した。

記録された最大getrusage RSS={resources['max_recorded_getrusage_RSS_KiB']}KiB。ライブラリの継承ページを含むプロセス高水準であり、アルゴリズム固有の純粋なピーク割当とは呼ばない。表示用出力時間の合計{resources['sum_export_wall_s']:.3f}秒はTから除外した。全計算環境はENVIRONMENT.json。

## 保全

開始時hash対象{preservation['protected_files']}ファイルについて、共通models.pyの上記IO改善1件を意図的変更として記録し、元ソースと前後hashを保全。その他の意図しない変更0、凍結8ファイル変更0。アルゴリズム本体・旧設定・旧OD・旧保存結果・README/.gitignoreの開始時変更を維持。最終実験登録後のコードhash変更0。追加は新規DWT実装・テスト・設定・文書・出力。commit/pushなし。

## 未完了

S1各cellの独立反復・外部妥当性、Aの全体T_human、Dのshots統計校正、S2/S3の本計算は未完了。最適性が未証明の値を真のPareto最適値として記載しない。
'''
for name, text in [('DWT_FINAL_COMPARISON.md', comparison), ('DWT_VALIDATION_REPORT.md', validation)]:
    (root / name).write_text(text)
    if args.publish_docs:
        Path('docs/research', name).write_text(text)
snapshot = root / 'SOURCE_FINAL'
snapshot.mkdir(exist_ok=True)
for p in Path('src/kmd_toc/dwt').glob('*.py'):
    shutil.copy2(p, snapshot / p.name)
shutil.copy2('src/kmd_toc/common/models.py', snapshot / 'common_models.py')
(root / 'COMMON_MODELS_IO.diff').write_text(''.join(difflib.unified_diff(
    (parent / 'SOURCE_COMMON_MODELS_BEFORE_IO.py').read_text().splitlines(keepends=True),
    Path('src/kmd_toc/common/models.py').read_text().splitlines(keepends=True),
    fromfile='preserved-original/src/kmd_toc/common/models.py', tofile='src/kmd_toc/common/models.py')))
for p in [registered['config_path'], 'tests/toc_dwt/test_dwt.py', 'scripts/run_dwt.py',
          'scripts/run_dwt_bundle.py', 'scripts/register_dwt_controls.py',
          'scripts/finalize_dwt.py', 'scripts/render_dwt.py', 'scripts/check_dwt_dashboard.py',
          'scripts/audit_dwt_standard_geometry.py', 'scripts/build_dwt_data_manifest.py']:
    shutil.copy2(p, snapshot / Path(p).name)
save(root / 'FINAL_COMPLETION.json', {'completed_UTC': datetime.now(timezone.utc).isoformat(),
     'overall': overall, 'main_statistics': 'HOLD', 'tests_passed': int(test_count),
     'independent_checks': independent['checks'], 'limited_attempts': 12, 'limited_accepted': valid_count,
     'front_count_by_method': front['front_count_by_method'], 'preservation': preservation,
     'quantum_new_routes_selected': qselected})
print(json.dumps(read(root / 'FINAL_COMPLETION.json'), ensure_ascii=False, indent=2))
