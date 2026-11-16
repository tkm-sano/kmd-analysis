"""Read-only post-run artifact audit; no solver, demand generation or new runs."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUTPUTS = ['output/toc_delivery/a_rule_v1_20261115_checks01',
           'output/toc_delivery/a_rule_v1_20261115_berths01']


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):
            h.update(block)
    return h.hexdigest()


def save(name,value):
    with (HERE/name).open('x') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')


def main():
    checks, rows = [], []
    def check(name,truth):
        checks.append({'check':name,'pass':bool(truth)})
    for output in OUTPUTS:
        root = ROOT/output
        check(output+':source_stability',json.loads((root/'SOURCE_STABILITY.json').read_text())['unchanged'])
        hashes = json.loads((root/'OUTPUT_HASHES.json').read_text())
        check(output+':all_output_hashes',all(digest(root/name)==h for name,h in hashes.items()))
        for row in json.loads((root/'SUMMARY.json').read_text()):
            run = root/row['run_id']
            search = json.loads((run/'search.json').read_text())
            report = json.loads((run/'validation.json').read_text())
            success = row['status'].startswith('VALIDATED')
            plan = json.loads((run/('plan.json' if success else 'rejected_plan.json')).read_text())
            label = row['run_id']
            v = {'S1':10,'S2':20,'S3':40}[row['scale']]
            n = {'S1':1000,'S2':2000,'S3':4000}[row['scale']]
            visits = [s['stop_id'] for t in plan['trips'] for s in t['visits']]
            check(label+':coverage',len(visits)==len(set(visits))==n)
            check(label+':budget',row['T_attempt']<=180 and row['max_rss_KiB']<=4096*1024)
            check(label+':resource',len(row['allocated_cpu_ids'])==4 and len(row['cpu_affinity'])==1 and
                  all(x=='1' for x in row['native_threads_environment'].values()))
            check(label+':phase_wall',abs(row['T_input']+row['T_planning']+row['T_validation']-row['T_attempt'])<1e-9)
            check(label+':counts',search['accepted_moves']<=v and
                  search['candidate_evaluations']==len(search['candidate_trace']) and
                  search['accepted_moves']==sum(x['status']=='ACCEPTED' for x in search['candidate_trace']))
            groups = [list(g) for g in search['initial_groups']]
            previous = tuple(search['initial_objective'])
            for item in search['candidate_trace']:
                check(label+':candidate_base',tuple(item['before'])==previous)
                if item['status']=='ACCEPTED':
                    check(label+':strict_improvement',tuple(item['after'])<previous)
                    src,dst,node = item['source'],item['destination'],item['node']
                    if item['direction']=='clockwise':
                        check(label+':boundary',(src+1)%v==dst and groups[src][-1]==node)
                        groups[src].pop();groups[dst].insert(0,node)
                    else:
                        check(label+':boundary',(dst+1)%v==src and groups[src][0]==node)
                        groups[src].pop(0);groups[dst].append(node)
                    previous = tuple(item['after'])
            check(label+':assignment_replay',groups==search['final_groups'] and all(len(g)<=120 for g in groups))
            check(label+':final_objective',previous==tuple(search['final_objective']))
            own = report['independent']
            check(label+':objective_oracle',[own['O_s'],own['H_s2']]==search['final_objective'])
            if success:
                check(label+':physical_and_FCFS',report['common']['feasible'] and own['feasible'])
                check(label+':D_W',abs(row['D']-float(own['D_km']))<=1e-7 and
                      row['W']==float(own['W_min']) and row['W_first']==own['W_first'] and
                      row['W_reload']==own['W_reload'])
                check(label+':no_overtime',own['O_s']==0)
            else:
                check(label+':null_accepted',all(row[k] is None for k in ['D','W','W_first','W_reload','T_program']))
                check(label+':rejected_not_infeasibility_proof',(run/'rejected_plan.json').exists() and
                      row['error']['not_a_proof_of_problem_infeasibility'])
            row = {**row,'output':output,'search':{k:search[k] for k in
                ['scans','candidate_evaluations','accepted_moves','stop_reason','initial_objective','final_objective']},
                'diagnostic_rejected_only':None if success else {'D':float(own['D_km']),
                    'W':float(own['W_min']),'W_first':own['W_first'],'W_reload':own['W_reload'],
                    'O_s':own['O_s'],'L_s':own['L_s'],'final_return_s':own['final_return_s']}}
            rows.append(row)
    s2 = [r for r in rows if r['scale']=='S2' and r['berths']==4]
    repeat = {'attempts':len(s2),'same_plan_sha256':len({r['plan_sha256'] for r in s2})==1,
        'same_D':len({r['D'] for r in s2})==1,'same_W':len({r['W'] for r in s2})==1,
        'same_input_hash':len({r['input_hash'] for r in s2})==1,
        'plan_sha256':s2[0]['plan_sha256'],'T_program_all':[r['T_program'] for r in s2],
        'independent_demand_samples':False}
    check('S2_reproducibility',all(repeat[k] for k in ['same_plan_sha256','same_D','same_W','same_input_hash']))
    original = json.loads((HERE/'PRESERVATION_BEFORE.json').read_text())['files']
    changed = [name for name,h in original.items() if digest(ROOT/name)!=h]
    check('protected_original_hashes',not changed)
    save('PRESERVATION_AFTER.json',{'checked':len(original),'changed':changed})
    save('REPRODUCIBILITY.json',repeat)
    save('ALL_ATTEMPTS.json',rows)
    fields = ['method','method_version','scale','scenario_id','demand_seed','solver_seed','repeat_id','run_id',
              'input_hash','config_hash','status','berths','D','W','W_first','W_reload','T_program','T_input',
              'T_planning','T_validation','T_attempt']
    with (HERE/'ALL_ATTEMPTS.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    save('FINAL_AUDIT.json',{'pass':all(c['pass'] for c in checks),'check_count':len(checks),
         'attempts':len(rows),'validated':sum(r['status'].startswith('VALIDATED') for r in rows),
         'failed_attempts':sum(not r['status'].startswith('VALIDATED') for r in rows),'checks':checks})
    print(json.dumps({'pass':all(c['pass'] for c in checks),'checks':len(checks),
                      'attempts':len(rows),'protected_files':len(original),'changed':changed}))


if __name__=='__main__':
    main()
