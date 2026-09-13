"""Validate a declared R21/R22 lineage without claiming a fresh scientific rerun."""
from pathlib import Path
from .r23_evidence_gate import load, check, hash_check, require, EvidenceBlocked
from .r23_validation_gate import aggregate_checks

def lineage_authority_checks(root,authority,stage):
    key=stage.lower();rows=[]
    def add(name,fn):rows.append(check(stage+'/'+name,'provenance_completeness',key+' authority configuration',fn))
    def results_hash():return hash_check(root,authority[key+'_results'],authority[key+'_results_sha256'])
    def manifest_hash():return hash_check(root,authority[key+'_manifest'],authority[key+'_manifest_sha256'])
    def binding():
        path=authority[key+'_results'];mp=authority[key+'_manifest'];manifest=load(root,mp)
        rel=str(Path(path).relative_to(Path(mp).parent))
        return hash_check(root,path,manifest['files'][rel])
    def declared_contents():
        result=load(root,authority[key+'_results']);manifest=load(root,authority[key+'_manifest'])
        require(result['status'] in ('PASS','VERIFIED') and manifest['status'] in ('PASS','VERIFIED'),'authority declares failure')
        instances=result['instances'];require(isinstance(instances,(list,dict)) and bool(instances),'empty authority instance set')
        values=list(instances.values()) if isinstance(instances,dict) else instances
        statuses=[x['status'] for x in values]
        require(all(x in ('PASS','VERIFIED') for x in statuses),'instance authority status not successful')
        require(all(isinstance(x['checks'],dict) and x['checks'] and all(v is True for v in x['checks'].values()) and x['failure_reasons']==[] for x in values),'authority checks contradict declared successful status')
        return {'instance_count':len(statuses),'checked':'recorded status consistency and hashes only; scientific validity is not reexecuted'}
    add('results_SHA',results_hash);add('manifest_SHA',manifest_hash);add('manifest_binds_results',binding);add('declared_status_consistency',declared_contents)
    return {'status':aggregate_checks(rows),'checks':rows,'scientific_revalidation':'NOT_TESTED','legacy_PASS_mapping':'PASS accepted only as historical declared status, not emitted as new verification'}
