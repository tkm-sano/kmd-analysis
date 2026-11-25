"""Reproduce stricter pre-S3 screening without changing any measured group."""
from datetime import datetime,timezone
import json
from .study import OUT,read,dump,digest


def apply():
    protocol=read(OUT/'PROTOCOL.json');records=[]
    for n in [10,12]:
        path=OUT/f'groups/probe_S3_n{n}/branch_0/RESULT.json';result=read(path);row=result['rows'][0]
        quantum=row['quantum']['wall_s'];assessment=result['timings']['assessment_s']
        generation=result['timings']['candidate_generation_s'];oracle=result['timings']['oracle_validation_s']
        predicted=2*(quantum+assessment+generation+oracle)*20*5+60
        records.append({'scale':'S3','n':n,'probe_source':str(path.relative_to(OUT)),'source_sha256':digest(path),
            'probe_quantum_s':quantum,'probe_assessment_s':assessment,'probe_generation_s':generation,
            'probe_oracle_validation_s':oracle,'additional_gate_triggered':assessment>=quantum,
            'conservative_full_call_prediction_s':predicted,'prediction_not_measurement':True})
    target=OUT/'RESOURCE_PREFLIGHT_SUPPLEMENT.json'
    if target.exists():
        saved=read(target)
        if saved['records']!=records:raise ValueError('SAVED_PREFLIGHT_DIFFERS')
    else:
        for record in records:
            tag=f"screen_S3_n{record['n']}_K20_R5_seed9201"
            if (OUT/'groups'/tag).exists():raise ValueError('PREFLIGHT_MUST_PRECEDE_GROUP')
        saved={'registered_utc':datetime.now(timezone.utc).isoformat(),'before_any_S3_four_branch_job':True,
            'reason':'measured full-plan assessment can exceed quantum work; use full-call cost before launching',
            'rule':'if assessment_s>=quantum wall_s, require 2*(quantum+assessment+generation+oracle)*K*R+60 within unchanged safety caps',
            'adaptive_pilot':True,'group_safety_cap_s':protocol['safety_only']['group_wall_s'],
            'batch_active_cap_s':protocol['safety_only']['batch_wall_s'],'records':records}
        dump(target,saved)
    for record in records:
        if not (record['additional_gate_triggered'] and record['conservative_full_call_prediction_s']>protocol['safety_only']['group_wall_s']):continue
        tag=f"screen_S3_n{record['n']}_K20_R5_seed9201";folder=OUT/'groups'/tag
        if folder.exists():
            marker=read(folder/'GROUP.json')
            if marker.get('status')!='NOT_RUN_RESOURCE' or marker.get('reason')!='SUPPLEMENTAL_FULL_CALL_RESOURCE_GATE':
                raise ValueError('REFUSE_OVERWRITE_MEASURED_GROUP')
        else:
            folder.mkdir(parents=True,exist_ok=False)
            dump(folder/'GROUP.json',{'tag':tag,'status':'NOT_RUN_RESOURCE','reason':'SUPPLEMENTAL_FULL_CALL_RESOURCE_GATE','main_experiment':False})
            dump(OUT/'gates'/(tag+'.json'),{'allowed':False,'reason':'SUPPLEMENTAL_FULL_CALL_RESOURCE_GATE',**record})
    source=OUT/'RESOURCE_PREFLIGHT_SUPPLEMENT_SOURCE.json'
    if not source.exists():dump(source,{'source':__file__,'sha256':digest(__file__),'action':'verified pre-S3 record without altering measured results'})
    return saved


if __name__=='__main__':print(json.dumps(apply(),indent=2))
