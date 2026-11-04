"""Finalize review manifests after numerical and manual figure acceptance."""
from evidence import *
import platform
from importlib.metadata import version

def main():
 t=time.monotonic();q=js(O/'PACKAGE_VALIDATION_SUMMARY.json');r=js(O/'REVIEW_SUMMARY.json');assert q['failures']==r['failures']==0
 replay=js(O/'RENDER_REPLAY_EXPECTED.json');replayed=[]
 for n,h in replay.items():replayed.append({'path':n,'before_sha256':h,'replayed_sha256':sha(O/n),'status':'PASS_BYTE_IDENTICAL' if sha(O/n)==h else 'FAIL'})
 table('FIGURE_REPLAY_CHECKS.csv',replayed);assert all(x['status']=='PASS_BYTE_IDENTICAL' for x in replayed)
 # This manual record attests the actual image review performed in the session;
 # regenerating it is not a substitute for viewing altered PNGs.
 visual=[]
 for x in rows(O/'FIGURE_SOURCE_MAPPING.csv'):
  png=next(n for n in x['files'].split(';') if n.endswith('.png'));visual.append({'figure_id':x['figure_id'],'png':png,'reviewed_sha256':sha(O/png),'inspection':'ACTUALLY_VIEWED_VIA_IMAGE_TOOL_2026-11-02; final metadata-only edit kept PNG bytes identical','font':'DejaVu Sans with Droid Sans Fallback for Japanese','clipping':'PASS','overlap':'PASS_AFTER_REPAIR','mojibake':'PASS_NONE','result':'PASS_STANDALONE_IMAGE;DOCX_LAYOUT_HOLD'})
 table('VISUAL_REVIEW.csv',visual)
 corrections=[{'id':'R01','target':'make_figures.py font.family','before':'Droid Sans Fallback only: missing Latin and digits warning','after':'DejaVu Sans plus Droid Sans Fallback: no glyph warning','verification':'FIGURES.stderr.log empty; all10 final PNG actually viewed','before_hashes':'revisions/FONT_REPAIR_BEFORE_HASHES.json'},{'id':'R02','target':'F5-2 legend / coverage labels','before':'ylim105, legend overlapped57/78 annotation','after':'ylim135 separates legend from bar annotations','verification':'F5_2 PNG re-viewed','before_hashes':'revisions/LAYOUT_BEFORE_HASHES.json'},{'id':'R03','target':'F5-4 ticks and F5-5 annotation','before':'adjacent12/13 and24/25 ticks; histogram text overlapped bars','after':'ticks1/6/13/18/25/30/36; remove redundant histogram annotation','verification':'F5_4 and F5_5 re-viewed','before_hashes':'revisions/LAYOUT_BEFORE_HASHES.json'},{'id':'R04','target':'SVG/PDF regeneration','before':'default random SVG ids and date metadata','after':'fixed svg.hashsalt; remove date metadata','verification':'30/30 figure files byte-identical on replay; final PNG10 unchanged','before_hashes':'revisions/RENDER_BEFORE_DETERMINISM_HASHES.json'},{'id':'R05','target':'DOCX mapping claim count','before':'editorial typo:29 claims','after':'26 actual claim rows','verification':'CLAIM_EVIDENCE_MAPPING.csv count26; numerical findings unchanged','before_hashes':'not scientific data'}]
 corrections.append({'id':'R06','target':'PRIMARY_REFERENCES_FOR_INSERTION.md Hadfield author order','before':'Draft had Biswas before Venturelli','after':'Venturelli before Biswas, matching arXiv1709.03489v2 author order','verification':'Primary arXiv metadata checked; journal reference2019/12(2)/34 and DOI confirmed','before_hashes':'editorial bibliography only; no original file altered'})
 table('revisions/CORRECTIONS_AND_REVALIDATION.csv',corrections)
 # Explicit line-level editorial delta; original research files are outside its scope.
 doc('revisions/FIGURE_REPAIR_DIFF.md','''# 図表の修正前後差分と再検証

修正はすべて今回のレビュー生成コード・画像内に限る。元CSV・研究コード・DOCXは変更していない。

```diff
- font.family = Droid Sans Fallback
+ font.family = [DejaVu Sans, Droid Sans Fallback]
- coverage ylim = (0,105)
+ coverage ylim = (0,135)
- mechanism xticks = [1,6,12,13,18,24,25,30,36]
+ mechanism xticks = [1,6,13,18,25,30,36]
- histogram annotation on bar area
+ redundant annotation removed; caption retains scope
+ svg.hashsalt = THESIS_20261102
+ SVG Date=None; PDF CreationDate=None, ModDate=None
```

元画像のhashを*_BEFORE_HASHES.jsonに残した。最終PNGを10点閲覧し、変更した3図を再度閲覧した。メタデータ固定後のPNGは全10点で同一hash、SVG/PDFを含む全30ファイルは描画再実行でbyte一致した。修正は数字・日本語の可読性と組版・再生成の安定性に関するもので、元数値・集計条件の変更ではない。
''')
 orig={}
 for x in rows(O/'PRESERVATION_CHECKS.csv'):orig[x['path']]={'path':x['path'],'sha256':x['expected_sha256'],'role':'ORIGINAL_PROTECTED_SOURCE'}
 table('SOURCE_INVENTORY_SHA256.csv',list(orig.values()))
 # Add a concise in-document hash inventory without requiring the reader to open scripts.
 inventory=O/'00_SOURCE_AND_RESULT_INVENTORY.md';text=inventory.read_text().split('\n<!-- MAIN_HASH_INVENTORY -->')[0]
 selected=['A_POLICY_DECISIONS_2808.csv','A_DELIVERY_COMPLETION_BY_STOP.csv','A_MECHANISM_COMPARISON.csv','B_PLAN_REFERENCES_36800.csv','B_SUMMARY_BY_SCALE_AND_METHOD.csv','C_CONDITIONAL_MASS_DC_SUMMARY.csv','PAIRED_COMPARISONS.csv','run_a.py','run_b.py','run_c.py','statistics_tables.py','verify_independent.py','verify_statistics.py']
 text+=f'\n<!-- MAIN_HASH_INVENTORY -->\n## 主資料のSHA256\n\n以下はすべて `review_outputs/no_sumo_full_analysis_20261102/run01/` 内である。全読取資料{q["protected_original_files"]:,}件のhashはSOURCE_INVENTORY_SHA256.csvに保存した。\n\n|ファイル|SHA256|\n|---|---|\n'
 for n in selected:text+=f'|{n}|`{sha(F/n)}`|\n'
 inventory.write_text(text)
 environment={'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'libraries':{x:version(x) for x in ['numpy','pandas','matplotlib','pillow','python-docx']},'purpose':'CURRENT_REVIEW_NOT_ORIGINAL_QAOA_ENVIRONMENT','scientific_runs':0,'bootstrap_reruns':0,'render_fonts':['DejaVu Sans','Droid Sans Fallback'],'randomness':'No new statistical sampling; original bootstrap seed20261102 retained; deterministic SVG hash salt'};dump('REVIEW_ENVIRONMENT.json',environment)
 doc('09_FINAL_QUALITY_REVIEW.md',f'''
# 最終品質レビュー

判定は**条件付き採用可**である。方法・結果・考察・結論のMarkdown、図10点のPNG/SVG/PDF、図表の元データ対応、26主張の審査、32箇所のDOCX反映対応を作成した。数値確認を工学的実証とみなさず、下記HOLD/FAILを保持している。DOCXへの実編集は実施していない。

## 独立照合と実行資源

|工程|今回の確認数|不一致|wall秒|最大RSS bytes|
|---|---:|---:|---:|---:|
|元行集計・経路・待機会計|{r['checks']}|{r['failures']}|{r['metrics']['wall_s']:.6f}|{r['metrics']['max_RSS_bytes']}|
|図表・代表部材・保存hashの別照合|{q['checks']}|{q['failures']}|{q['metrics']['wall_s']:.6f}|{q['metrics']['max_RSS_bytes']}|

上記合計{r['checks']+q['checks']:,}は照合項目数であり、独立標本数ではない。前回全件分析の独立検証・bootstrap検証の件数と区別した。Cの全速度の再積分、bootstrap再計算、科学runnerは今回実行していない。図表生成の実測資源はFIGURES_SUMMARY.json、描画の再実行ログはFIGURES_REPLAY.log、Python等はREVIEW_ENVIRONMENT.jsonに保存した。各工程のRSSは当該processのピークであり、総和や研究全体の最大メモリとして解釈しない。

保存図の全30形式ファイルは描画再実行でbyte一致した。PNG10点を実際に閲覧した。文字欠落・凡例重なり等の新規図表の不適合は修正し、差分・修正前hash・再確認をrevisions/へ保存した。数値結果や元データを修正していない。最終描画stderrは空である。Wordへの配置、印刷幅・ページまたぎ・目次と相互参照の更新はHOLDである。

## 品質基準の審査

|確認対象|判定|根拠と制限|
|---|---|---|
|数値・単位・分母|PASS|REVIEW_NUMERICAL_CHECKS.csv、PACKAGE_VALIDATION_CHECKS.csv不一致0|
|主張の証拠対応|PASS|26行にfile/row/hash/式/実装/図/限界。一般同等性・量子一般優劣等は使用不可|
|Aの100%と完了時刻差の区別|PASS|待機吸収9,216行、帰庫会計2,304組、余裕78問題を保存|
|Aの実世界解釈|CONDITIONAL|固定OD・102秒・期限余裕。実配送同等性ではない|
|Bの6設定同値の理由|PASS|初期値＝mirror支持最小2,300fit、active zero460。経路リストも別照合|
|Bの規模・方式・計算予算|CONDITIONAL|全8設定・6規模、支持・FIT/最終検証/RESULT分離。同予算一般比較は不可|
|Bの407/53分母と未実施DC|PASS|53入力を補完せず、走行DCはUNTESTEDのまま|
|Bの実機回路資源|HOLD|hardware qubits/compiled gates/depth、統一当時環境の保存不足|
|Cの既知と完成パック|PASS記載／HOLD完成品|全183完成pack NULL、既知差を完成品差としない|
|T09全面対向|FAIL保持|T09_ROW_183、元CSV source_row184。除外・修正なし|
|量子材料解析→材料改善|UNTESTED|参照文献は古典DFT・電極実験、量子機による改善実証なし|
|統計区間|CONDITIONAL|25群内依存を保持した補助感度1,176区間、検定0、モデル誤差未包含|
|図表の元CSV対応・再生成|PASS|10図×3形式、全36/8設定の表、生成コードとplot-data保存|
|用語・結果／考察分離|PASS|である調、モデル完了、OD秒、工程CPU、固定軌跡DCを区別|
|方法の再実行情報|CONDITIONAL|式・単位・設定・seed・protocol・sourcehashを記載。外部保全rawを含む公開資料不足|
|本文引用と末尾参考文献|HOLD|背景8引用の対応、Faraji-Niri DOI、引用様式の整理。LITERATURE_VERIFICATION.csv|
|論文DOCX・既存成果物の保全|PASS|{q['protected_original_files']:,}資料hash一致、DOCX SHA一致、tracked diff不変|

既存道路網N0幾何FAIL、N1動的FAILは継続し、地域代表試行は開始していない。Aの正の遅延native、B走行DC、T09完成パックを実証済みとしていない。実世界の交通・材料・実車妥当性について研究全体の再現性を確保したとは記さない。

## 再現手順

作業ディレクトリは `/home/takuma/kmd-analysis` である。元科学runnerを実行せず、以下のレビュー専用入口を使う。材料原著・元会計のhashを再照合する補助入口はpin_material_provenance.pyである。主要参考文献の転記案はPRIMARY_REFERENCES_FOR_INSERTION.md、元材料モデルはMATERIAL_PRIMARY_SOURCES.csv、アルゴリズム全設定はALGORITHM_PROTOCOL_APPENDIX.mdを参照する。出力先は各スクリプトの親review directoryとして決定するため、第三者はscripts/を新しいrunへコピーして再生成できる。参照元F/D等の実パスはevidence.pyに明示し、再配置時はsha一致を要求する。

```bash
.conda/bin/python -B review_outputs/thesis_results_interpretation_20261102/run01/scripts/source_and_docx.py
.conda/bin/python -B review_outputs/thesis_results_interpretation_20261102/run01/scripts/review_numbers.py
.conda/bin/python -B review_outputs/thesis_results_interpretation_20261102/run01/scripts/make_figures.py
.conda/bin/python -B review_outputs/thesis_results_interpretation_20261102/run01/scripts/write_review.py
.conda/bin/python -B review_outputs/thesis_results_interpretation_20261102/run01/scripts/write_drafts.py
.conda/bin/python -B review_outputs/thesis_results_interpretation_20261102/run01/scripts/docx_map_and_protocols.py
.conda/bin/python -B review_outputs/thesis_results_interpretation_20261102/run01/scripts/verify_package.py
```

finish_review.pyは検算と描画再実行の成功後に台帳を作る最終入口である。VISUAL_REVIEW.csvの手動確認欄は今回実際に閲覧した画像hashの証明であり、異なる画像を再生成した第三者は改めて目視確認する。自動実行だけで新たな目視受入を主張しない。RENDER_REPLAY_EXPECTED.jsonと同じ30出力hashを確認してからfinish_review.pyを使う。

入力・コード・出力のhashはSOURCE_INVENTORY_SHA256.csvとSHA256_MANIFEST.csv。hash台帳自体は自己参照を避けてその台帳から除外し、SHA256_MANIFEST.sha256で別管理する。環境用matplotlib cacheは研究成果物台帳から除外する。外部保全資料を持たない環境で全ソースを再取得できることはHOLDである。

## DOCX編集前の残作業と停止

1. 08の32対応に沿って、主系列と旧補助系列の配置・章番号を確定する。特に3.8、欠落5.2、旧548/99配送先・native3099秒の履歴を整理する。
2. 背景引用8件・DOI・参考文献様式を照合し、未確認の出典を推測で追加しない。
3. 本文の主要図・付録図、全条件表、補助区間を決め、Wordへ反映した際の数式・フォント・図幅・目次・相互参照を確認する。
4. 因果経路の到達範囲と限界を維持する。実機・実交通・完成パックに関するHOLDは追加工学証拠なしで解消しない。

限定された研究主張の転記素材は準備済みである。無修正で提出できる完成DOCXの受入ではない。新規SUMO、道路修復、再学習、全件科学実験、既存docsやDOCXの編集を行わず、このレビューの保存で停止した。
''')
 # Hash manifest last; no self-hash or transient font cache.
 artifacts=[]
 for p in sorted(O.rglob('*')):
  if p.is_file() and p.name not in ['SHA256_MANIFEST.csv','SHA256_MANIFEST.sha256'] and '.mplconfig' not in p.parts:
   artifacts.append({'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size,'role':'GENERATED_REVIEW_ARTIFACT'})
 table('SHA256_MANIFEST.csv',artifacts);(O/'SHA256_MANIFEST.sha256').write_text(sha(O/'SHA256_MANIFEST.csv')+'  SHA256_MANIFEST.csv\n')
 print(json.dumps({'review_check_total':r['checks']+q['checks'],'failures':0,'figures':10,'claims':26,'docx_insertions':32,'protected_files':q['protected_original_files'],'manifest_files':len(artifacts),'manifest_sha256':sha(O/'SHA256_MANIFEST.csv')},ensure_ascii=False))
if __name__=='__main__':main()
