"""Seal new review artifacts and retain source/evidence identities."""
from evidence import *
def main():
 allsources={}
 for f in sorted(O.glob('*SOURCES.json')):
  for x in json.loads(f.read_text()):
   path=x['path']
   if Path(path).is_relative_to(O):continue
   if path in allsources and allsources[path]['sha256']!=x['sha256']:raise ValueError('Conflicting source hash '+path)
   allsources[path]=x
 fields=['path','sha256','bytes','expected_sha256','storage']
 table('COMBINED_SOURCE_FILES.csv',[{k:x.get(k) for k in fields} for x in allsources.values()],fields)
 rr={x['candidate_id']:x for x in rows(O/'B_FINAL_RECOVERY_CLASSIFICATION.csv')};refs=rows(P2/'B_PLAN_RUN_LINKS.csv');linked=[]
 for x in refs:
  y=rr[x['candidate_id']];linked.append(dict(x,recovery_class=y['recovery_class'],recovered_complete_input_id=y['complete_input_id'],available_physical_input_id=y['available_physical_input_id'],network_status=y['network_status'],original_identity_status='PASS' if y['recovery_class']=='ORIGINAL_RECOVERED' else 'HOLD'))
 table('B_PLAN_RECOVERY_LINKS.csv',linked)
 judgments=[]
 def add(k,status,name,ids,basis,cmd,gap):
  p=O/name;judgments.append({'decision_id':k,'status':status,'evidence_path':str(p),'evidence_sha256':sha(p),'row_or_problem_or_run_ids':ids,'basis':basis,'verification_command':'.conda/bin/python -B '+str(O/cmd),'unresolved':gap})
 add('N0_GEOMETRY','FAIL','N0_GAP_PRIMITIVES.csv.gz','connection_index510027; junction448039303; all563513','>1m 563513 primitives, maximum97.033728m','diagnose_network.py','No accepted N0 geometry repair')
 add('N1_GAP_SCREEN','PASS','N1_PROFILE.json','B6','No >1m endpoint gap','diagnose_network.py','Screen only; collision/stop/global geometry not thereby accepted')
 add('N1_DYNAMIC','FAIL','COLLISION_BODY_OVERLAP_INDEPENDENT.csv','183 saved native events','Independent body SAT confirms overlap; runtime guard also fails waiting/throughput','network_supplement.py','No simultaneously acceptable dynamic repair')
 add('N1_OLD_ENDPOINT_REUSE','FAIL','ENDPOINT_REUSE_N0_N1.csv','6670 role endpoints;958 outside','Old offsets out of bounds on new lane lengths','diagnose_network.py','New mapping/full OD/reference results required')
 add('B_ORIGINAL_LEG_RECOVERY','PASS','RECOVERED_OD_LEGS.jsonl.gz','217123 OD keys;2323 complete candidate payloads','Direct original saved edge recovery and exact NPZ/parquet endpoint/weight identity','recover_routes.py','Whole B route assembled now, not previously executed; network remains FAIL')
 add('B37_IDENTITY','HOLD','KNOWN37_IDENTITY_COMPARISON.csv','B-01993; B-04253; other35 match','35 exact full sequences;2 unprovable because original OD edge missing','review_recovery.py','Do not call alternative cache exact reconstruction')
 add('B_MISSING_PATHS','HOLD','MISSING_OD_GENERATOR_PROVENANCE.csv','13249 unique OD keys;16 partitions','Numeric rows found, original edge sequences unretained','missing_feasibility.py','Exact original generator replay/identity test not executed')
 add('G4_MODEL_DEFINITION','PASS','MEASUREMENT_TEST_CASES.csv','service boundary fixture IDs','Task binding/range/continuous coverage needed; ended is not handover','validate_measurements.py','Native active ledger integration HOLD; observations not real handover')
 add('G5_DC_KERNEL','PASS','DC_INDEPENDENT_FIXTURES.csv','rest,constant,accel,decel,restart','Scalar formula and frozen kernel match','validate_measurements.py','Conditional model; primary B mass not adopted')
 add('G5_B_MASS','HOLD','MASS_EVIDENCE.json','current B no-window series','Legacy1155kg is evidenced candidate; no unique current B adoption','validate_measurements.py','Mass adoption and terminal boundary required; no PEkg conversion')
 add('FINAL_PRESERVATION','PASS','FINAL_SOURCE_HASH_CHECK.csv','all recorded original sources and prior875artifacts','Start/final hash readback and empty tracked diff','final_review.py','External preservation paths are required, not public Git standalone reproduction')
 table('EVIDENCE_DECISIONS.csv',judgments)
 doc='''# 最終独立レビューの記録

1. 元データとの一致：既存875成果物の開始hash、最終全参照hashを照合。36,800参照を全4,987候補の分類へ結合。数値・payloadSHA・主キー検査はFINAL_REVIEW_CHECKS.csv。
2. 道路版：N0/N1の差分・958無効端点を保持。新道路で旧目的値が成立するとの主張なし。N2未構築。
3. B同一性：元edge直接回収2,323と旧cache同一性HOLD2を分離。35一致／2保留、134区間中133PASS／1HOLD。距離だけの一致を経路一致と扱わない。
4. 未確定入力：partial2,662件に完全IDなし。networkblockedは完全入力にも保持。
5. 配送完了：endedを完了とせず、連続停車証拠を伴うモデル完了を定義。native監視接続HOLD。
6. B質量：主massはnull。旧B0=1,155kgは候補のみ、PEkg換算なし。
7. Cとの分離：T08/T09をB実証に転用せず、T09完成183HOLD／対向1FAILと量子材料未実証を保持。
8. 除外防止：全4,987候補・36,800参照・未保存13,249脚と制御1HOLDを残す。全候補のnetworkblockも列で保持。
9. 保全：元コード・入力・結果・FREEZE・原稿を変更せず、新レビュー領域のみ追加。FINAL_SOURCE_HASH_CHECK.csvとGIT_DIFF_FINAL.patch参照。
10. 再実行：コード、ログ、入力source/hash、raw元経路、公式資料cache、出力manifestを保存。外部保全が必要な限界を明記。地域試行や全件実験は実行していない。

## レビューで修正した事項

制御134区間のうち元edge欠落1区間が中間native距離照合台帳から落ちていた。分母134と明示HOLD1を復帰した。修正前code/CSV、修正diffをrevisionsに保存し、review_recovery.pyとfinal_review.pyを再実行して不一致0。元CSVは変更していない。

経路回収初回は同一parquet/XMLの反復hashによる遅延で中断し、hashキャッシュを適用して再実行した。初回ログを保持。科学式・保存結果・分類受入条件の変更なし。この効率修正前codeの完全snapshotは未保存で、遡及して保存済みとは主張しない。

N1の8link対は方向付きであり、順序を除くmovement対は7。この単位を両記した。追加来歴検査では欠落旧schemaにlane-mode/hash欄がないことを明示し、後期lane-routerのhash不一致と誤解しない表現にした。

すべてのFAIL/HOLDを隠さず、最終ゲートはA/BともNO-GO。これはfixture不一致があるという意味ではなく、地域道路・比較可能性・nativeイベント計測・B質量の科学受入が未成立という判断である。
'''
 (O/'FINAL_REVIEW_NOTES.md').write_text(doc)
 (O/'revisions/REVISION_LOG.md').write_text('''# 修正と再検証

- `review_recovery_before_missing_control.py`／`KNOWN37_RAW_NATIVE_DISTANCE_CHECKS.before.csv` を保存し、HOLD1行を明示して134区間の分母を復帰。`review_recovery.diff`、`control_ledger.diff` が修正差分。
- `RECOVERY_REVIEW.log` と `FINAL_REVIEW.log` が修正後再検証。既存科学データの変更なし。
- 初回経路回収の効率問題は `ROUTE_RECOVERY_ATTEMPT01.log` を保持。キャッシュ修正前code完全snapshotは未保存。
''')
 # Manifest includes itself only by exclusion to avoid recursive hashing.
 artifacts=[]
 for p in sorted(O.rglob('*')):
  if p.is_file() and p.name!='ARTIFACT_MANIFEST.json':artifacts.append({'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size})
 write('ARTIFACT_MANIFEST.json',artifacts)
 print(canon({'source_records':len(allsources),'plan_recovery_links':len(linked),'judgments':len(judgments),'artifacts':len(artifacts),'artifact_manifest_self_excluded':True}))
if __name__=='__main__':main()
