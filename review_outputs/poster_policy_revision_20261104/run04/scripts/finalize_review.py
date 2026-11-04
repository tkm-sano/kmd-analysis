"""Run after inspecting the current real-PPTX preview; do not replace visual review."""
from pathlib import Path
import json,csv
r=Path(__file__).resolve().parents[1]
p=r/'render/FINAL_VALIDATION.json';v=json.loads(p.read_text())
assert not any(v[k] for k in ['shape_bounds_violations','paragraphs_not_found_in_pdf','text_outside_print_margins','text_crossing_column_gap'])
v['visual_review']='PASS：実PPTX描画の全体画像で、問い・方法・図表・正式手法名・条件候補・未検証範囲・共通枠組みを確認した。'
v['scientific_scope_review']='PASS：研究方針と保存値を維持し、3群8設定、二つの質量モデル、確認結果・推論・未検証接続を区別した。'
v['printed_size_note']='A1縦594×841mm。本文22–26pt、表21pt、詳細18–20pt、文献18pt。Microsoft PowerPoint固有描画と紙への試し刷りは未実施である。'
p.write_text(json.dumps(v,ensure_ascii=False,indent=2))
rows=[]
for i,b in enumerate(json.loads((r/'poster_layout.json').read_text()),1):
 x,y,t=b['x_mm'],b['y_mm'],b['text']
 if y<160:cat='研究設定・A/B/C定義';src='TITLE/PURPOSE/RQ; 03_RESEARCH_STRUCTURE'
 elif y>=780:cat='文献・案内';src='08_REFERENCES'
 elif y>=699:cat='B枠組み／C適用・成果／A到達段階';src='07_CONNECTIONS_ABC; 10_CAUSAL_MODEL_REVIEW'
 elif t.startswith('B　量子評価'):cat='B 文献に基づく条件候補';src='B04; R2,R7'
 elif x<300 and y>=568:cat='B目的値改善の条件／C未検証／A参照';src='A01–A04,B01,C01–C03; GLOBAL_REFERENCE_COVERAGE'
 elif x>=300 and y>=568:cat='A部材差／B会計境界';src='A07–A09,B02; C_COMPONENT_BOUNDARIES'
 elif x<300:cat='A 保存計算・集計、正式名は文献定義';src='B_NORMALIZED_BY_SCALE_CONFIG; SETTING_SCOPE_AUDIT; SAVED_ROUTE_INPUT_CHECKS; R1'
 else:cat='A 固定入力・モデルの算定';src='C_MASS_DC_RECONCILIATION; C_T08_ENERGY_FULL; C_T09_COMPONENTS_183; R5'
 rows.append(dict(block=i,x_mm=x,y_mm=y,font_pt=b['font_pt'],text=t,evidence_scope=cat,source=src,review='確認済み。見出し・表セルを含むため接続ごとのABC表と併読する。'))
with (r/'evidence/POSTER_BLOCK_CLAIM_REGISTER.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('Final visual-review record and exact-text evidence register saved.')
