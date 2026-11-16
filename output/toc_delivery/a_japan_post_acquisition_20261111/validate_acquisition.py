"""Check saved primary evidence, units, access categories and draft readiness."""
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, unquote
from decimal import Decimal
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DOCS = ROOT/'docs/research/toc_delivery_a'
NAMES = ['A_JAPAN_POST_DATA_AVAILABILITY.md','A_DATA_ACQUISITION_PLAN.md','A_DATA_ACQUISITION_DECISION.md']


def normalize(url):
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, unquote(parts.path).rstrip('/'), parts.query, ''))


def main():
    checks=[]
    def check(name, value):
        checks.append({'check':name,'passed':bool(value)})
        if not value:
            raise AssertionError(name)
    manifest=json.loads((HERE/'SOURCE_MANIFEST.json').read_text())
    sources={r['id']:r for r in manifest}
    check('thirty_five_primary_sources',len(manifest)==len(sources)==35)
    for r in manifest:
        check(r['id']+'_GET_source_received',r['method']=='GET' and r.get('status')==200 and not r.get('error'))
        check(r['id']+'_original_hash',hashlib.sha256((ROOT/r['archive']).read_bytes()).hexdigest()==r['sha256'])
        check(r['id']+'_text_hash',hashlib.sha256((ROOT/r['text']).read_bytes()).hexdigest()==r['text_sha256'])
    texts={sid:(ROOT/r['text']).read_text() for sid,r in sources.items()}
    data=json.loads((HERE/'DATA_AVAILABILITY_REGISTER.json').read_text())
    check('ten_records',len(data['records'])==10)
    required=['data_name','holder_or_publisher','source_ids','urls','acquisition_method','license_and_conditions',
              'privacy_and_commercial_constraints','region','period','unit','metric_computability_now','lead_time_and_basis','final_status']
    for rec in data['records']:
        check(rec['id']+'_all_required_metadata',all(k in rec and rec[k] is not None for k in required))
        check(rec['id']+'_status_enum',rec['final_status'] in data['allowed_statuses'])
        check(rec['id']+'_saved_primary_sources',all(s in sources for s in rec['source_ids']))
        check(rec['id']+'_no_provider_SLA_invented',rec['provider_promised_days'] is None)
        check(rec['id']+'_contact_not_permission',rec['general_contact_is_not_permission'] is True)
        if rec['id']!='J01':
            check(rec['id']+'_target_raw_access_unverified',rec['raw_target_access_status']=='UNVERIFIED')
    case=texts['JP_LOOGIA']
    check('T_experienced_original','5分～10分' in case)
    check('T_novice_original','30分～1時間' in case)
    check('T_article_as_of_not_measurement_date','2021年時点' in case)
    for group,minutes in [('experienced',[5,10]),('novice',[30,60])]:
        check('T_'+group+'_conversion',[int(Decimal(m)*60) for m in minutes]==data['human_T_references_s'][group])
    check('D_W_common_T_missing',all(data[k] is None for k in ['Japan_Post_human_plan_D_km','Japan_Post_loading_W_min','Japan_Post_common_T_s']))
    for sid in ['SAFIE_JP_2024','HACOBU_JP_2024']:
        txt=texts[sid]
        check(sid+'_site_and_dates','新東京郵便局' in txt and '2024年10月1日から12月31日' in txt)
        check(sid+'_inbound_not_outbound_assumed','到着バース' in txt and '荷役時間' in txt)
    check('PDX_use_restricted','本取り組みでのみ使用' in texts['JP_PDX_DATA'])
    check('PDX_month_aggregation','月間配達個数' in texts['JP_PDX_DATA'] and '1,000' in texts['JP_PDX_DATA'])
    check('startup_eligibility_not_research_application','スタートアップ' in texts['JP_INNOVATION'] and '法人登記' in texts['JP_INNOVATION'] and '2名以上' in texts['JP_INNOVATION'])
    check('monthly_selection_not_delivery_SLA','翌月末' in texts['JP_INNOVATION'] and data['followup_days_are_provider_SLA'] is False)
    check('researcher_followup_milestones',data['researcher_followup_business_days']==[5,10,20])
    check('Tokyo_distance_is_estimate','推計で約5億km/年' in texts['TOKYO_JP_DATA'] and '軽4輪は約0.6億km/年' in texts['TOKYO_JP_DATA'])
    check('Tokyo_PDF_locator_verified','page 164' in (HERE/'TOKYO_PAGE_LOCATOR.txt').read_text() and (HERE/'sources/TOKYO_JP_DISTANCE_PAGE.png').exists())
    check('university_raw_dataset_not_inferred','電子付録 (0)' in texts['NISHIMERA_LANDING'] or re.search(r'電子付録\s*\(0\)',texts['NISHIMERA_LANDING']))
    check('UTokyo_case_operator_is_Sagawa','佐川急便' in texts['UTOKYO_CHECK'])
    check('MOVO_Fleet_is_other_product','MOVO Fleet' in texts['HACOBU_CSV_TECH'] and '契約が必要' in texts['HACOBU_CSV_TECH'])
    check('NTT_case_motorcycle_not_delivery_car','集配用バイク' in texts['NTT_JP_2026'])
    plan=(DOCS/NAMES[1]).read_text()
    draft=plan.split('<!-- draft-jp:start -->')[1].split('<!-- draft-jp:end -->')[0].strip()
    check('JP_form_limit_in_primary','2,000文字以内' in texts['JP_INQUIRY'])
    check('draft_under_2000_characters',len(draft)<=2000)
    check('draft_standalone_exact',(HERE/'DRAFT_JAPAN_POST_UNSENT.txt').read_text().strip()==draft)
    for term in ['[所属機関・研究科]','[氏名]','研究責任者','研究','匿名化','出典','利用条件','1営業日','5営業日','総走行距離','積込待機時間','計画作成時間']:
        check('draft_contains_'+term,term in draft)
    check('draft_private_identifiers_not_requested','提供は希望しません' in draft and '車番・映像' in draft)
    check('no_contact_or_submission',not data['outbound_contact_executed'] and not data['form_submission_executed'])
    check('no_alternative_adopted',not data['alternative_adopted'])
    check('three_levels_not_conflated',data['level_1_all_three']==data['level_2']==data['level_3']=='HOLD' and data['level_1_T_only']=='CONDITIONAL GO')
    known={normalize(r['url']) for r in manifest}|{normalize(r.get('final_url',r['url'])) for r in manifest}
    for name in NAMES:
        txt=(DOCS/name).read_text()
        check(name+'_nonempty',len(txt)>1000)
        check(name+'_no_trailing_whitespace',all(line==line.rstrip() for line in txt.splitlines()))
        for target in re.findall(r'\]\(([^)]+)\)',txt):
            if target.startswith(('http://','https://')):
                check(name+'_primary_link_'+target,normalize(target) in known)
            else:
                check(name+'_local_link_'+target,(DOCS/target.split('#')[0]).exists())
    context=json.loads((HERE/'CONTEXT_AUDIT.json').read_text())
    check('common_conditions_unchanged',context['conditions_sha256']==hashlib.sha256((ROOT/'configs/toc_delivery/common_conditions_v1_1.json').read_bytes()).hexdigest()=='bbb15417a4eee5072f8118056c90ab422d792b4cedc35a6a06bf6bc0497fe8d2')
    result={'passed':len(checks),'failed':0,'checks':checks,'draft_characters_including_subject':len(draft),
            'primary_sources_received':len(manifest),'interpretation':'primary source/definition/units/status/draft/document audit, not validation of unpublished operational records or provider consent'}
    (HERE/'VALIDATION_RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(checks)} checks passed; 35 sources received; unsent draft {len(draft)} characters')


if __name__=='__main__':
    main()
