"""Exclusive new outputs, saved-plan evaluation only, hash-pinned evidence."""
import csv
import json
import sys
from pathlib import Path
from kmd_toc.descriptive_v1.policy import digest, require_frozen
from .analysis import AuditedReader, load_audited, gated_analyze


def dump(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)


def csvwrite(path, rows, fields=None):
    fields = fields or list(dict.fromkeys(k for r in rows for k in r)) or ['status']
    with Path(path).open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                             for k, v in row.items()})


def write_statistics(registration, output, *, figures=True):
    require_frozen()
    path, out = Path(registration).resolve(), Path(output).resolve()
    if out.exists(): raise ValueError('NEW_OUTPUT_REQUIRED')
    reader = AuditedReader(path)
    reg = json.loads(path.read_text())
    original = digest(path)
    rows = load_audited(reg, reader)
    result = gated_analyze(reg, rows, reader.evidence)
    result['data_role'] = reg['data_role']
    out.mkdir(parents=True, exist_ok=False)
    dump(out/'ANALYSIS.json', result)
    csvwrite(out/'METHOD_SUMMARY.csv', result['summaries'])
    csvwrite(out/'COMPARISONS.csv', result['comparisons'])
    csvwrite(out/'DUAL_IMPROVEMENT.csv', result['direct_dual_improvement'])
    csvwrite(out/'TRIAL_STATUS.csv', result['audited_rows'])
    csvwrite(out/'FAILURE_SUMMARY.csv', result['failures'])
    mcse = [{'kind': 'absolute', **{k: r[k] for k in ('scale', 'method', 'metric', 'J', 'MCSE', 'MCSE_status')}}
            for r in result['summaries']]
    mcse += [{'kind': 'contrast', 'scale': r['scale'], 'comparison': r['baseline']+'->'+r['comparison'],
              'metric': r['metric'], 'MCSE': r['MCSE_delta'], 'MCSE_status': r['MCSE_status']}
             for r in result['comparisons']]
    mcse += [{'kind': 'trial_dual', 'scale': r['scale'], 'comparison': r['baseline']+'->D',
              'metric': 'I_dual_percent', 'MCSE': r['MCSE_trial_I_dual_percent'],
              'MCSE_status': r.get('MCSE_status', 'HOLD_NO_VERIFIED_PAIRS')}
             for r in result['direct_dual_improvement']]
    csvwrite(out/'MCSE_SUMMARY.csv', mcse)
    dump(out/'MEASUREMENT_CERTIFICATES.json', reader.measurements)
    if figures:
        from kmd_toc.descriptive_v1.plots import render
        dump(out/'FIGURE_SPEC.json', render(result, result['audited_rows'], out/'figures'))
        from .plots import render_direct
        dump(out/'DIRECT_FIGURE_SPEC.json', render_direct(result, out/'figures'))
    changed = reader.unchanged()
    if digest(path) != original: changed.append(str(path))
    if changed: raise ValueError('INPUT_CHANGED_DURING_ANALYSIS:'+str(changed))
    require_frozen()
    root = Path(__file__).resolve().parents[3]
    code = [*Path(__file__).parent.glob('*.py'), *(root/'src/kmd_toc/descriptive_v1').glob('*.py'),
            root/'scripts/analyze_common_measurement_v1.py']
    dump(out/'ANALYSIS_MANIFEST.json', {'version': 'common-measurement-audit-20261121-v1',
         'data_role': reg['data_role'], 'registration': str(path), 'registration_sha256': original,
         'input_hashes': reader.hashes, 'code_hashes': {str(p): digest(p) for p in code},
         'python': sys.version, 'main_experiment': 'HOLD', 'formal_J': 'HOLD',
         'parameter_adoption': 'HOLD', 'hypothesis_testing': 'NOT_PERFORMED',
         'primary_error_bar': 'sample_SD', 'MCSE_role': 'internal precision only',
         'unit_policy': 'I_dual_percent = 100*min(relative_fraction_D, relative_fraction_W); no second factor of 100',
         'no_optimizer_or_quantum_invocation': True, 'source_changes': []})
    lines = ['# 記述統計集計', '', 'データ区分: '+reg['data_role'], '',
             '正式J・n/K/R採用・本実験はHOLD。エラーバーは平均±1標本SD。', '',
             '|規模|方式|指標|有効記録数|独立性確認|平均|SD|MCSE|', '|---|---|---|---:|---|---:|---:|---:|']
    for r in result['summaries']:
        lines.append('|'+ '|'.join(str(r[k]) for k in ('scale','method','metric','J','independence_confirmed','mean','SD','MCSE'))+'|')
    lines += ['', '30比較枠を保存。Aは比較範囲等5項目がPASSの場合のみ参照。未登録・未確認はnullのまま保持。',
              '平均値からのI_dualと対応試行別I_dualの平均を別列で保存。対応なしでは試行差SD・同時改善割合を生成しない。',
              '総Wは全活動便の積込待機の総和［分］。内部枝・パラメータ条件を独立試行へ加算しない。']
    (out/'STATISTICAL_REPORT.md').write_text('\n'.join(lines)+'\n')
    return result
