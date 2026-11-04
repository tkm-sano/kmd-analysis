from pathlib import Path
import csv,json,hashlib,datetime,subprocess,collections,platform,sys
O=Path(__file__).resolve().parents[1];R=O.parents[1]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def writej(p,x):(O/p).write_text(json.dumps(x,ensure_ascii=False,indent=2))
rows=list(csv.DictReader((O/'INPUT_FILE_LEDGER.csv').open()));source_results=[]
for x in rows:
 p=Path(x['path']);exists=p.is_file();actual=sha(p)if exists else None
 source_results.append(dict(path=str(p),expected_sha256=x['sha256'],actual_sha256=actual,unchanged=exists and actual==x['sha256']))
writej('SOURCE_PRESERVATION_REPORT.json',dict(count=len(rows),unchanged=sum(x['unchanged']for x in source_results),failures=[x for x in source_results if not x['unchanged']],checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),records=source_results))
tracked=json.load((O/'TRACKED_BASELINE.json').open());out=[]
for x in tracked:
 p=Path(x['path']);actual=sha(p)if p.is_file()else None
 out.append(dict(path=str(p),expected_sha256=x['sha256'],actual_sha256=actual,unchanged=actual==x['sha256']))
writej('TRACKED_PRESERVATION_REPORT.json',dict(count=len(out),unchanged=sum(x['unchanged']for x in out),failures=[x for x in out if not x['unchanged']],records=out))
(O/'GIT_STATUS_END.txt').write_bytes(subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=all'],cwd=R))
(O/'GIT_DIFF_END.patch').write_bytes(subprocess.check_output(['git','diff','--binary'],cwd=R))
endhead=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();starthead=json.load((O/'START.json').open())['head']
writej('GIT_PRESERVATION_SUMMARY.json',dict(start_head=starthead,end_head=endhead,same_head=starthead==endhead,tracked_diff_identical=(O/'GIT_DIFF_START.patch').read_bytes()==(O/'GIT_DIFF_END.patch').read_bytes(),note='new outputs are untracked within this directory; no commit/push performed'))
# Add acquisition artifacts to ledger; these are downloaded/new copies, not immutable pre-existing research inputs.
existing={x['path']for x in rows};claims=list(csv.DictReader((O/'CLAIM_EVIDENCE_LEDGER.csv').open()))
for x in rows:x['claim_ids']=';'.join(c['claim_id']for c in claims if x['path']in c['source_paths'].split(';'))
for p in sorted((O/'sources').rglob('*')):
 if p.is_file()and str(p)not in existing:
  rejected='REJECTED'in p.name;role='文献取得・一次資料/DB応答の今回スナップショット'if 'literature'in str(p)else '今回固定した原稿・構造の入力記録'
  rows.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,role=role,adoptable_result='使用不可（誤取得）'if rejected else '原著確認範囲と文献台帳の選定判定に限定',conditional_result='本文のモデル仮定・推論は別判定',HOLD='API失敗応答・棄却資料は証拠にしない。確認範囲を超える主張は禁止',claim_ids=''))
with(O/'INPUT_FILE_LEDGER.csv').open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Per-table and figure page lookup, useful for concrete review.
items=json.load((O/'DOCX_BUILD_LEDGER.json').open())['caption_list'];pagecount=json.load((O/'RENDER_AUDIT.json').open())['pages']
for item in items:
 target=(('図'if item['kind']=='Figure'else'表')+item['id'])
 item['PDF_pages_with_caption_label']=';'.join(str(i)for i in range(1,pagecount+1)if target in (O/f'render/page_{i:03}.txt').read_text().replace(' ',''))
with(O/'FIGURE_TABLE_INDEX.csv').open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
writej('ENVIRONMENT.json',dict(python=sys.version,executable=sys.executable,platform=platform.platform(),render_engine='Preserved LibreOffice runtime; PyMuPDF page images',native_Word_test='NOT EXECUTED'))
# Final report uses actual audits, not expected outcomes.
a=json.load((O/'DOCUMENT_AUDIT.json').open());n=json.load((O/'NUMERICAL_AUDIT_RESULT.json').open());pr=json.load((O/'SOURCE_PRESERVATION_REPORT.json').open());tr=json.load((O/'TRACKED_PRESERVATION_REPORT.json').open())
assert n['failures']==0 and a['failures']==0 and not pr['failures']and not tr['failures']
report=f'''# 最終監査報告

総合判定：**CONDITIONAL GO**。独立した論文改訂、今回のStep3考察、表示・根拠・保全の監査は実施した。量子実機、実材料、完成pack、実EV、社会的転換の実証を完了したことを意味しない。HOLDを保持した範囲で研究者の採用レビューへ進める状態である。

## A〜Lの監査

|項目|判定|根拠と範囲|
|---|---|---|
|A 目的・方法・結果・結論|PASS|RQ0〜RQ3に対応し、能力・適用・成果の区別を要旨/1/3/5/6/7章で整合|
|B 文献3分類と横断比較|PASS|2.1社会技術、2.2エネルギー、2.3モビリティ物流、2.4横断比較。指定の13小節を検査|
|C 文献実在・書誌・URL|CONDITIONAL|13主要文献の一次資料を台帳の範囲で確認。L02/L03/L07は公開要旨・節等に主張を限定。L12と元Papachristosは新論証に採用せずHOLD。技術文献は再現根拠と区別|
|D 被引用数|PASS|OpenAlex、2026-11-04。採用13主要文献全て2024以前100件以上。全26取得結果のid・countを保存JSON照合。未知件数を合格扱いしていない|
|E Step2数値|PASS|{n['checks']:,}項目の独立算術・raw照合で不一致{n['failures']}。NUMERICAL_AUDIT_CHECKS.csv。保存結果の確認を実世界妥当性としない|
|F 統計単位・区間|PASS|入力/fit/測定/group/軌跡を分離。Wilsonとgroup補助感度の対象を明記。実配送母平均のCIとしない|
|G 量子優位性|PASS|確認したとは記載しない。主greedy正改善0、診断3入力ではgreedy既に最適|
|H T08/T09|PASS|T08簡略会計、T09既知小計/未知BOM、完成質量NULL、異会計直接順位禁止|
|I 実EV削減|PASS|指定保存軌跡のControlled-DCに限定。実EV削減の実証はNOT CLAIMED|
|J HOLD保持|PASS|H01〜H16の影響と次作業を記録。旧道路受入・T09対向条件の不適合も保持|
|K Word・図表・数式・参照|CONDITIONAL|XML等{a['check_count']}検査不一致{a['failures']}、PDF{a['pages']}頁を画像確認。11表/8画像、本文方法42OMML保持+新3式。Wordネイティブの改ページ・代替フォント差はHOLD|
|L 元ファイル保全|PASS|開始時の参照{pr['count']}ファイル同一、Git追跡{tr['count']}ファイル同一、元DOCX SHA同一、HEAD不変|

## 数値と解釈

主B36,800計画の全可行・正改善0、R5Grover p2の平均−5,983.706453秒/SD1,314.364537秒を保持した。新統制9,312fit/93,120測定の取得確率と、主対照への目的値差を分離した。固定CPU時間は4顧客R1_001/全支持/一様初期/projector p2の97fitを用い、実機や公平なgreedy速度優位へ換算していない。

T08境界5.448297415kg/u=.877094072/V=3.193155684Vと、T09既知差9.722608121/5.977891152kgを異なる会計として記載した。総和比.412579010/.413590412%と個別率平均.409329419/.410435042%を区別した。δ=bはモデル会計の相殺境界であり、未知δの実測・量子改善の達成ではない。

追加統制のexact_success_probability_best8192という列名は実装上greedy厳密改善確率を意味していた。列名だけによる最適取得との混同を避け、raw primary_rep0_optimalから取得率を再構成した。SOURCE_FIELD_SEMANTICS.mdに記録し、元出力を変更していない。

## 表示監査

全{a['pages']}ページのcontact sheetを確認し、主要結果・数式・文献・付録全設定をページ画像で拡大確認した。表2-1のページ跨ぎを検出し、独立改訂内で改ページを修正した。図表の切断、ページ領域外ブロック、置換文字、欠落した本文の英数字/日本語は検出されなかった。表C-1は行を分割せず見出しを繰返す。

厳密文字抽出ではR5の負号がfallback-fontの抽出順の影響を受けたが、ページ画像上の負号と範囲、数値CSVを確認した。PDF_EXTRACTION_DIFFERENCES.jsonに差を保持した。演算子を除いた本文英数字・日本語の全段落カバレッジを別途確認した。テキスト抽出一致を数式の視覚確認の代用としていない。

Wordネイティブアプリは利用していない。LinuxのLibreOfficeではArial Unicode MS等の代替フォントが使われる可能性がある。MS Wordでの最終レイアウトと研究者の採否はH15とする。元数式86のうち現行方法42は再使用し、旧付録のみの44は保全原DOCXに保持した。削除・移動を含む原稿再構成を、全86式を新本文へ残したと誤記していない。

## 未実施と理由

新しい量子学習・solver・SUMO・実車実験は実施していない。必要な報告値は保存結果の再分析で照合可能であり、大規模再実験は原稿統合に不要である。HOLDの解消を推測で代替していない。独立原稿の作成は実施したが、正式研究への採否・統合、commit/push/公開/外部送信は未実施である。
'''
(O/'FINAL_AUDIT_REPORT.md').write_text(report)
(O/'EXECUTIVE_SUMMARY.md').write_text(f'''# 実行結果

総合判定はCONDITIONAL GOである。第2章を三領域と横断比較へ再構成し、主要文献13件を確認範囲付きで採用した。Step2の数値をraw根拠へ照合し、今回新たにStep3を執筆した。論文全体は要旨、第1〜7章、参考文献、付録A〜Dへ整合させた。

経路1では、36,800保存bestの可行性と主greedyへの正改善0を確認した。取得率を改善できる診断条件は存在するが、既に最適な対照を上回る解品質改善とは異なる。414参照のうち41は保存MIP証拠に条件付き、46は未証明である。CPU時間から運用締切やQPU速度優位を同定できない。

経路2では、既知会計の軽量化が未知・追加部材差δで相殺される境界を、T08/T09それぞれの設計条件で示した。保存速度のDC感度は条件付きであり、量子技術による実材料・実EV改善とは帰属できない。量子材料接続、完成pack、実車、社会制度・普及は未検証である。

新しい価値は、異なる二経路の能力・適用・成果を分け、支持や既に最適な対照による解品質の上限と、部材質量による効果の相殺を、異なる機構として比較した点である。数値検算{n['checks']:,}、文書監査{a['check_count']}は不一致0、PDF{a['pages']}頁。原資料の現実妥当性、Wordネイティブ表示、研究者の正式採否は未完了である。

本成果物は独立した1回のtrialであり、正式な研究成果への採用・統合は未実施である。
''')
print('preserved',pr['count'],'source files;',tr['count'],'tracked files; final report saved')
