from pathlib import Path
import pandas as pd,json,sys,platform
O=Path(__file__).resolve().parents[1];dc=pd.read_csv(O/'data/DC_MASS_KERNEL_SUMMARY.csv')
s='\n材料非依存の追加検算：下/上Crrの1000kg右微分は、460軌跡について最小{:.6f}/{:.6f}、中央値{:.6f}/{:.6f}、平均{:.6f}/{:.6f}、軌跡間SD{:.6f}/{:.6f} Wh/kgである。材料の確率分布や実EVの推定区間ではない。\n'.format(*[dc.set_index('rolling_case').loc[k,col] for col in ['slope_min','slope_median','slope_mean','slope_SD'] for k in ['CRR_LOWER_BOUND','CRR_UPPER_BOUND']])
for n in ['PATH2_CONTRIBUTION_CONDITIONS.md','PATH2_MAIN_VS_REFERENCE_RESULTS.md']:
 p=O/n;p.write_text(p.read_text()+s)
p=O/'THESIS_RESULTS_DRAFT.md';t=p.read_text();t=t.replace('以下は条件付き参考例である。',s+'\n以下は条件付き参考例である。');p.write_text(t)
# Stage-by-stage variable/formula/unknown mapping, no causal status conflation.
rows=[('材料性能','q,u,V','有効容量・平均電圧','実験条件/容量分母の整合','Chen直接報告と逆算を分離','実用適格性','材料予測→実材料HOLD'),('電極・セル設計','E,V,q,u,r,f_p,f_n,q_n','Q=E/V;mp=Q/(qu);mn=rQ/q_n','gross設計、活物質割合の定義','T08 SCENARIOSと数式','設計変数の同時実現','A;E'),('構成部材質量','塗工材・面積・空隙','mp/f_p+mn/f_n+箔+膜+液','T09幾何・密度移用','path2_analysis.py t09()','case/tabs等','既知subtotalのみ'),('電池パック質量','既知subtotal+未知部材','M_complete=known+unknown','部材境界非重複','T08簡略会計/T09 NULL','未知BOM/安全寿命','完成pack確定HOLD'),('車両質量','非pack車体+pack+driver/cargo','m=m_nonpack+M+55','比較時に他要因一定','凍結モデル','実積載/実車設計','条件付き'),('走行DC','m,固定速度,物理条件','sum max(W1+W2+W3+W4,0)/(3600η)','同軌跡/平坦/回生補機除外','frozen_sources/run_full_controlled_dc.py','モデル誤差/実車','1000–1250kg検算')]
pd.DataFrame(rows,columns=['stage','inputs','formula','assumption','source_locator','unknown','verification_scope']).to_csv(O/'PATH2_CAUSAL_STAGE_MAP.csv',index=False)
(O/'REPRODUCIBILITY_REPORT.md').write_text('''# 再現方法と実行環境
Pythonはリポジトリの.conda/bin/python（3.11.15）を使用した。numpy/pandas/matplotlib/python-docxの版とplatformはevidence/ENVIRONMENT.jsonに記録した。PYTHONDONTWRITEBYTECODEおよび-Bを用い、入力先へのpycache生成を避けた。新規大規模QAOA/SUMO/厳密求解は行っていない。
同じ入力版を用いた処理順は scripts/audit_inputs.py → synthesize.py → correct_path2.py → dc_independent.py → refine_text.py → figures.py → finish_content.py → build_docx.py → render_docx.py → final_audit.py である。初期synthesizeだけの出力は採用しない。Chen採用修正を必須として最後まで実行する。重複追記を避けるため、再実行時はscripts/dataと元入力を別の新規ディレクトリへ複製してから一巡させる。既存Step3の再実行・上書きを再現方法とはしない。
実行コマンドはリポジトリrootから .conda/bin/python -B <trial>/scripts/<name>.py である。スクリプトは自分の親ディレクトリをtrialとする。現状はS1/S2の実在ローカルパスを参照し、単一trialだけで全上流実験を再実行できる意味ではない。
DCの追加検算は材料入力を使用せず、既存宣言質量範囲で保存460速度入力を読み、凍結evaluateと区分線形表現を両端で照合した。詳細時間はevidence/DC_INDEPENDENT_RUN.json。図の数値源はFIGURE_INDEX.csv、図形ソースはscripts/figures.pyとdata/FIGURE_NODES.csvに保存した。Wordは同じ草稿とCSV/PNGから生成し、LibreOffice read-only binaryを新profileで起動してPDF/ページPNGへ変換した。Word実機表示はHOLDである。
入力ハッシュはSTEP3_SOURCE_MANIFEST.csv、出力ハッシュはOUTPUT_SHA256_MANIFEST.csvである。源ファイルと追跡100ファイルの保全再照合はevidence/PRESERVATION_RESULTS.csvを参照する。脚注や浮動図の最終体裁はStep4で大学様式に合わせる。
''')
import numpy,matplotlib,docx
(O/'evidence/ENVIRONMENT.json').write_text(json.dumps(dict(python=sys.version,platform=platform.platform(),numpy=numpy.__version__,pandas=pd.__version__,matplotlib=matplotlib.__version__,python_docx=docx.__version__),indent=2))
with (O/'STEP4_HANDOFF.md').open('a') as f:f.write('\n採用判断の優先事項：Chen逆算容量は主分析の確定値として採用しない。経路2主分析は解析感度・一般収支・材料非依存DCを先に置き、具体LP/S数値は参考例として後置する。CHEN_2020_ADOPTION_CORRECTION、PATH2_INPUT_PROVENANCE、CHEN_DEPENDENCY_AUDITの分類を本文/図/台帳で維持する。新しい材料入力範囲は未設定であり、将来実用ペアが揃えば別trialで再評価する。\n')
# Figure/table plans must match created artifacts.
(O/'THESIS_FIGURE_TABLE_PLAN.md').write_text('''# 作成済み図表と論文配置
図1二経路、図2経路1条件、図3経路2条件、図4共通枠組み、図5保存B品質差、図6条件付き参考境界、図7材料非依存DC質量応答をPNG/PDFで作成した。FIGURE_INDEX.csvに元CSVとChen依存を記録した。図6は参考例の表示をタイトル・captionに含む。
表1は経路1の条件、表2は経路2の主分析/参考例、表3は未検証事項である。詳細台帳はdata/TABLE1_CONDITIONS.csv、TABLE2_CONDITIONS.csv、TABLE3_LIMITATIONS.csvであり、Word内は読みやすい要約版である。Word図の挿入幅は16.2cm、行内配置、caption付きである。
数値グラフは保存CSVを用い、構造図はscripts/figures.pyとdata/FIGURE_NODES.csvから再現できる。完成pack/実車への未検証接続を破線/別色で区別した。大学様式の最終図表番号はStep4へ引き継ぐ。
''')
print('Final content prepared')
