"""Current research authority, separate from historical loading-only analysis."""
from kmd_toc.common.config import ROOT, read_json
from .evaluation import VERSION, load_model

POLICY_ID = VERSION
RQ = ('京浜トラックターミナルを起点とする大田区のToC配送において、量子・古典ハイブリッド最適化手法は、'
      '従来的な経路作成手法および古典的最適化手法と比較して、同一の計画作成時間内に得られる配送計画の'
      '総走行距離および1運行当たりの荷待ち時間にどのような差異を示すか。また、これらの評価結果は、'
      'オープンデータに基づく外部参照ベースラインとどのような関係にあるか。')
HYPOTHESIS = ('量子・古典ハイブリッド最適化手法は、従来的な経路作成手法および古典的最適化手法と比較して、'
              '同一の計画作成時間内に、総走行距離および1運行当たり平均荷待ち時間の両方を削減した配送計画を生成できる。')
POLICY_PATH = ROOT / 'configs/toc_delivery/dw_policy_20261117_v1.json'


def load_policy(path=POLICY_PATH):
    p = read_json(path)
    if (p['policy_id'], p['rq'], p['hypothesis']) != (POLICY_ID, RQ, HYPOTHESIS):
        raise ValueError('CURRENT_RESEARCH_POLICY_DRIFT')
    if p['objectives'] != {'D': 'total_distance_km', 'W': 'mean_cargo_wait_min_per_operation'}:
        raise ValueError('CURRENT_OBJECTIVE_DRIFT')
    if (p['main']['executable'] is not False or p['main']['runs'] != [] or
            p['execution']['launch_authorized'] is not False):
        raise ValueError('MAIN_EXPERIMENT_HOLD')
    if p['composite'] != {'name': 'J_DW', 'status': 'HOLD', 'weights': None, 'normalization': None, 'support_rule': None}:
        raise ValueError('UNAPPROVED_COMPOSITE')
    if p['execution'] != {'mode': 'preserved_finite_work_not_equal_time_evidence',
        'rules': 'configs/toc_delivery/termination_rules_20261116_v1.json', 'BCD_branches': 4,
        'native_threads_per_branch': 1, 'outer_execution': 'sequential',
        'timing_logs': 'auxiliary_record', 'launch_authorized': False}:
        raise ValueError('EXECUTION_POLICY_DRIFT')
    if p['A'] != {'role': 'external_administrative_reference', 'distance_km_per_parcel': 0.58,
                  'wait_min_per_operation': 60, 'generated_plan': False, 'planning_time': None,
                  'same_observed_plan_pair': False}:
        raise ValueError('EXTERNAL_REFERENCE_DRIFT')
    load_model(ROOT / p['wait_model'])
    return p
