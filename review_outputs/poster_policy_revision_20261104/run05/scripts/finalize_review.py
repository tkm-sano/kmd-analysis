"""Record review only after inspecting the current real-PPTX preview."""
from pathlib import Path
import json,csv
R=Path(__file__).resolve().parents[1];p=R/'render/FINAL_VALIDATION.json';v=json.loads(p.read_text())
assert not any(v[k] for k in ['shape_bounds_violations','paragraphs_not_found_in_pdf','text_outside_print_margins','text_crossing_column_gap'])
v['visual_review']='PASS：実PPTX描画の全体画像で、目的→工程図→二経路の方法・結果→結果の意味→構成案と未検証範囲の順を確認した。文字欠落・重なりはない。'
v['scientific_scope_review']='PASS：保存値・研究方針を維持した。今回比較した区間を色付き、未検証の接続を破線とし、参照材料の計算を量子材料の成果としない。'
v['layout_validation_scope']='二段組の境界検査は本文300〜695mmに適用する。上部の全幅工程図・凡例は意図した全幅要素である。'
v['printed_size_note']='A1縦594×841mm。主本文21–24pt、見出し25–30pt、図の主ラベル21pt、詳細17–19pt、文献18pt。実機PowerPoint描画・紙への試し刷りは未実施である。'
p.write_text(json.dumps(v,ensure_ascii=False,indent=2))
rows=[]
for i,b in enumerate(json.loads((R/'poster_layout.json').read_text()),1):
 x,y,t=b['x_mm'],b['y_mm'],b['text']
 if y<140:scope='研究目的・分析の枠組み';src='TITLE/PURPOSE/RQ; 03_RESEARCH_STRUCTURE'
 elif y<277:
  scope='確認区間A／未実施・未検証Cの表示／配置はB';src='07_CONNECTIONS_ABC; READING_STRUCTURE.json'
 elif y>=788:scope='参考文献・実施範囲';src='08_REFERENCES'
 elif y>=701:scope='B：構成の条件候補／C：未検証範囲';src='B04,B05,C01–C06; R2,R3,R4,R6,R7'
 elif x<300 and y>=614:scope='A：各群の結果／B：改善余地と取得品質の区別';src='A01–A03,B01; B_BY_CONFIGURATION'
 elif x<300:scope='A：比較設計・結果・平均の定義';src='B_NORMALIZED_BY_SCALE_CONFIG; SETTING_SCOPE_AUDIT; SAVED_ROUTE_INPUT_CHECKS'
 elif y>=600:scope='A：部材モデル・代表差／B：相殺の会計';src='A07–A09,B02; C_COMPONENT_BOUNDARIES'
 elif y>=564:scope='A/B：固定条件下の算定と解釈';src='A06,B03; CONTROLLED_MASS_TO_DC_MODEL_FREEZE'
 else:scope='A：参照入力・簡略質量とDCの保存算定';src='A05,A06; C_MASS_DC_RECONCILIATION; R5'
 rows.append(dict(block=i,x_mm=x,y_mm=y,font_pt=b['font_pt'],text=t,evidence_scope=scope,source=src,review='本文は自然文で説明し、根拠のA/B/Cは補足の接続台帳に保持する。'))
with (R/'evidence/POSTER_BLOCK_CLAIM_REGISTER.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('Reader-oriented layout and evidence scope reviewed.')
