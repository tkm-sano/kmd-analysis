"""Audit the reflected deck and record how the updated research summary was used."""
from pathlib import Path
import json,csv,hashlib
O=Path(__file__).resolve().parent;R=O.parents[2]
LAST=R/'output/slides/sato_discussion_9slides_20261105'
stem='研究紹介_佐野巧馬_佐藤先生相談用_研究まとめ反映版_本編9枚'
code=(LAST/'finish_discussion.py').read_text()
code=code[:code.index("report='''")]
code=code.replace("stem='研究紹介_佐野巧馬_佐藤先生研究相談_本編9枚_補足4枚'", "stem='研究紹介_佐野巧馬_佐藤先生相談用_研究まとめ反映版_本編9枚'")
code=code.replace('to_page=12','to_page=13').replace('len(d)==13','len(d)==14').replace('list(range(13))','list(range(14))').replace('全13ページプレビュー.png','全14ページプレビュー.png')
code=code.replace('backup_slides=4,total_pages=13,explanation_minutes=18,discussion_minutes=32','backup_slides=5,total_pages=14,explanation_minutes=19,discussion_minutes=31')
exec(compile(code,str(LAST/'finish_discussion.py'),'exec'))

with (R/'review_outputs/t08_t09_final_adoption_20261105/data/BOUNDARIES.csv').open() as f:
 bounds=list(csv.DictReader(f))
b=next(float(x['boundary']) for x in bounds if x['model']=='T08' and x['variable']=='extra_S_minus_LP')
assert abs(b-5.448297415076951)<1e-12
with (R/'review_outputs/t08_t09_final_adoption_20261105/data/DC_SUMMARY.csv').open() as f:
 rr=[x for x in csv.DictReader(f) if x['case_id']=='T08_fixed_loading_q_195.959596']
assert len(rr)==2 and all(int(x['n'])==460 for x in rr)
assert all(round(float(x['weighted_saving_percent']),2)==.41 for x in rr)
assert '28,200' in d[4].get_text() and '8,600' in d[4].get_text()
audit['material_reference_only']=dict(mass_cancellation_kg=b,energy_rows=rr,status='INPUT_UNQUALIFIED_REFERENCE_ONLY')
audit['reflection_source']=str(R/'研究のまとめ_20261105更新版.pptx')
audit['reference_vehicle']=dict(vehicle_mass_kg=1100,driver_kg=55,running_mass_kg=1155,nominal_battery_kWh=20,source='user supplied updated summary; not vehicle-calibrated SUMO')
(O/'evidence/validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))

report='''「研究のまとめ_20261105更新版.pptx」の反映報告

成果物は本編9枚＋補足5枚である。説明19分・意見交換31分を想定する。
第1枚目と既存の相談用資料、今回提示された研究まとめ、研究データは上書きしていない。

今回、説明の中心に戻した内容
・量子・古典の比較対象は訪問順序であり、現在の目的関数は総旅行時間である。
・待機・配達作業時間・電力量は、この目的関数には含めない。
・総旅行時間の差と、顧客別の配達完了・定時配達率を分ける。
・基盤となる配送需要、1巡の条件、汎用SUMO車両と参照車種、電力量モデルの仮定を具体的に説明する。
・材料側は、仮定した入力から質量・電力量へ伝わる条件と、追加部材による相殺を説明する。

スライドごとの変更
1：元のスライドを完全保全。PPTXのスライドXML・関連定義は元と同一。最終PDFは元第1ページを直接使い、3解像度で全画素一致を確認した。
2：京浜トラックターミナルを想定した研究上の代理拠点、39,956地点・81,859個相当の合成需要、1巡1台を追加した。基盤全地点を一括して量子計算した図にはしていない。
3：研究目的・問いを更新版2枚目に合わせた。現在評価する総旅行時間を明示し、配達完了・定時率は未評価の接続先として図中で分けた。
4：容量216個相当、全地点訪問・帰還、102秒、32,400秒、実際の比較規模を具体化した。MINICAB EV参照の車両1,100kg・電池20kWh、運転者55kg、走行質量1,155kgを追加した。汎用SUMOモデルは車種固有の寸法・加減速性能を再現していないことを明記した。
5：更新版の同等28,200件・長い候補8,600件を補足した。平均+441.8秒、中央値0、最大+9,484.0秒、短い候補0件は維持した。
6：更新版5枚目の相殺境界約5.448kg、条件付きDC削減率約0.41%を見える位置へ追加した。これらは入力適格性未確認の参考例として、同じ欄・直下・ノートで留保した。100kg質量感度は材料参考値と区別して残し、図は補足3へ移した。
7：構築済みの道路・合成需要モデル、全入力の厳密最適証明・取得時間統制の未完了、車種固有の消費・交通相互作用・完成パックの質量・寿命・出力適格性を整理した。
8・9：佐藤先生に伺う10項目の質問は変更していない。
補足1・2・4：旅行時間内訳、電力量式、部材質量式を維持した。
補足3：以前の本編6枚目の100kg感度の棒グラフを配置した。距離・移動時間との散布図は本版の説明の中心から外した。
補足5：基盤需要、今回の460入力、旧小規模・拡張規模、車両参照と仮想感度の違いを対比した。

研究まとめの記述をそのまま混合しなかった点
1. 99地点と100地点
更新版6枚目には99地点等があるが、今回の36,800計画を集計したStep5のR4は100顧客である。
本編の主結果は3・4・5・25・100・125顧客の460入力に統一した。旧3・4地点中心の直接比較と、150・175・200等の列挙は別系列として補足5へ移した。
2. 5.448kg・約0.41%
算術と保存結果は確認できるが、逆算材料容量の実用全電池への適格性はStep4以降の採用判断で保留されている。
したがって「確認された実材料の改善量」ではなく、材料条件を置いた参考例として反映した。
0.41%は保存軌跡の電力量総和の比であり、各軌跡の削減率の単純平均とは区別した。
3. 1,155kgと1,000→1,100kg
前者は参照車両に運転者を加えた基準値、後者は材料に依存しない仮想的な質量感度計算である。
T08参考パック置換後の質量は別途計算され、1,155kgへ新パックを単純加算しない。
4. 拠点名と参照車種
名称・参照値は今回提示された更新版を根拠として反映した。実営業拠点の再現やMINICAB EV実車への校正完了を主張していない。

検証
全14ページをレンダリングした。原第1ページの画素一致、全テキストの抽出一致、指定質問文、同一パレット、Noto Sans JP、ページ外図形・文字、文字重なり候補を検査した。
元の36,800計画の差の分数、件数・平均・最大、既存の100kg感度の対応を照合した。
T08相殺境界5.448297415076951kg、DC総和比0.41257901006062697/0.4135904116974739%を採用済み台帳と最終報告CSVに照合した。
23個の読取元ファイルは開始時と終了時のSHA256が一致した。これは使用した資料群の保全確認であり、リポジトリ全ファイルの監査ではない。

主要出典
研究のまとめ_20261105更新版.pptx：目的、条件、参照車両、主要参考値、二経路の説明。
docs/QUANTITATIVE_GUIDE.md：合成需要の基盤、代理デポ、旧系列と評価条件。
review_outputs/quantum_ev_step5_20261105/THESIS_FULL_TEXT.md：現行B入力の規模・主比較。
同/data/B_PLAN_GAPS_36800.csv、同/data/B_INPUT_CONDITIONS_460.csv：保存計画と条件。
review_outputs/t08_t09_final_adoption_20261105/FINAL_REPORT_JA.md・data/BOUNDARIES.csv・data/DC_SUMMARY.csv：参考例と採用上の留保。
01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json：車両・電池・運転者・物理モデルの凍結条件。
evidence/validation.json：本版の表示・数値・保全確認。
'''
(O/'reports/研究まとめの反映内容.txt').write_text(report,encoding='utf8')
uncertain='''反映時に区別した事項

・旧99顧客系列と現行Bの100顧客系列を区別した。現行36,800計画の対象は入力表とStep5本文を優先した。
・更新版にある主に3・4地点の旧直接比較と、現行460入力のCPU模擬を区別した。
・京浜トラックターミナル想定の拠点名とMINICAB EV参照値は更新版を出典とする。実拠点・実車の再現性が検証済みとはしていない。
・約5.448kg・約0.41%は材料入力が未適格の参考例。実用セルや完成パックの予測値へ昇格させていない。
・定時配達率、量子実機優位、実材料改善、実車効果、全入力の最適証明、取得時間の完全な統制は引き続き未実証・未完了である。
'''
(O/'reports/反映時の確認事項.txt').write_text(uncertain,encoding='utf8')
rd=fitz.open();fontpath=PREV/'fonts/NotoSansJP-Regular.ttf';font=fitz.Font(fontfile=str(fontpath))
for filename in ['研究まとめの反映内容.txt','反映時の確認事項.txt']:
 page=None;y=0
 for rawline in (O/'reports'/filename).read_text().splitlines():
  lines=[];chunk=''
  for ch in rawline:
   if font.text_length(chunk+ch,fontsize=10.5)>510:lines.append(chunk);chunk=ch
   else:chunk+=ch
  lines.append(chunk)
  for st in lines:
   if page is None or y>784:
    page=rd.new_page(width=595.276,height=841.89);page.insert_font(fontname='NR',fontfile=str(fontpath));page.insert_text((42,32),'研究まとめ更新版の反映報告',fontname='NR',fontsize=12,color=(0,32/255,96/255));page.insert_text((42,818),str(len(rd)),fontname='NR',fontsize=9);y=58
   if st:page.insert_text((42,y),st,fontname='NR',fontsize=10.5)
   y+=16
rd.save(O/'reports/研究まとめ反映報告.pdf',garbage=4,deflate=True)
hashes=[]
for p in O.rglob('*'):
 if p.is_file() and p.name!='output_hashes.csv' and p.suffix!='.log':hashes.append([str(p.relative_to(O)),p.stat().st_size,sha(p)])
with (O/'evidence/output_hashes.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['path','bytes','sha256']);w.writerows(hashes)
print(json.dumps({k:v for k,v in audit.items() if k!='source_preservation'},ensure_ascii=False,indent=2))
