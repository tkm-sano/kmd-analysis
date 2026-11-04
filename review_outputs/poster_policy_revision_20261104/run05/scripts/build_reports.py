"""Reproducible review package; no Markdown output or mutation of input files."""
from pathlib import Path
import csv,json,hashlib,html
from review_content import *
R=Path(__file__).resolve().parents[1];O=R/'reports';O.mkdir(exist_ok=True)
esc=lambda v:html.escape(str(v))
CSS='body{font-family:system-ui,sans-serif;max-width:1450px;margin:30px auto;padding:0 24px;line-height:1.7;color:#17232d}h1,h2{color:#143653}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border:1px solid #b9c6cf;padding:9px;vertical-align:top;text-align:left;overflow-wrap:anywhere}th{background:#edf3f7}a{color:#286a96}.note{padding:14px;background:#edf3f7;border-left:5px solid #a6522c}img{max-width:100%}pre{white-space:pre-wrap}'
def table(headers,rows):return '<table><tr>'+''.join('<th>'+esc(h)+'</th>' for h in headers)+'</tr>'+''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</table>'
def page(name,title,body):
 (O/name).write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>'+esc(title)+'</title><style>'+CSS+'</style><body><p><a href="../README.html">成果物一覧</a></p><h1>'+esc(title)+'</h1>'+body+'</body></html>')
def dataset(stem,title,headers,rows,prefix=''):
 with (O/(stem+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:w=csv.writer(f);w.writerow(headers);w.writerows(rows)
 page(stem+'.html',title,prefix+table(headers,rows))
def csvtable(path):
 rows=list(csv.DictReader(path.open()));return table(list(rows[0]),[list(v.values()) for v in rows])
dataset('02_CHANGE_COMPARISON','修正前後の対照表',['項目','run04','run05','理由'],CHANGES)
before=json.loads((R/'baseline/poster_layout.json').read_text());after=json.loads((R/'poster_layout.json').read_text())
def selected(rows,x,ys):return '\n'.join(v['text'] for v in rows if abs(v['x_mm']-x)<.01 and any(abs(v['y_mm']-y)<.01 for y in ys))
def region(rows,x_side,y0,y1):
 return '\n'.join(v['text'] for v in rows if y0<=v['y_mm']<=y1 and (x_side=='all' or (v['x_mm']<300 if x_side=='left' else v['x_mm']>=300)))
exact=[
 ('目的・全体像',region(before,'all',89,160),region(after,'all',89,277)),
 ('配送方法',region(before,'left',190,349),region(after,'left',303,426)),
 ('配送結果',region(before,'left',356,557),region(after,'left',430,610)),
 ('配送の解釈',region(before,'left',568,695),region(after,'left',614,694)),
 ('材料方法・入力',region(before,'right',190,346),region(after,'right',303,442)),
 ('材料の計算結果',region(before,'right',356,557),region(after,'right',448,599)),
 ('部材分析の意味',region(before,'right',568,695),region(after,'right',600,694)),
 ('共通の考察',region(before,'all',699,778),region(after,'all',701,781))]
dataset('02_TEXT_EXACT_COMPARISON','実際の本文の変更対照',['箇所','修正前の実テキスト','修正後の実テキスト'],exact,'<p>生成レイアウト台帳から抽出した本文である。表は数値監査表と新旧PDFを併せて参照する。</p>')
dataset('04_CONDITIONS','成立条件候補・制約の根拠一覧',['ID','経路','区分','結果・条件・制約','根拠','適用範囲・留保'],CONDITIONS,'<p>Aは固定入力・固定モデルの保存結果の確認、Bは文献またはモデルに基づく条件付き推論、Cは未検証である。Aを現実の量子因果効果とみなさない。</p>')
dataset('05_UNTESTED_AND_HOLD','残存課題・HOLD一覧',['ID','経路','未確定事項','現状と扱い','出典'],HOLDS,'<p>HOLDは不明事項を推測で埋めないための状態である。新しい実験・追加の最適化は今回実施していない。接続ごとのCは接続監査一覧にも示す。</p>')
dataset('07_CONNECTIONS_ABC','接続ごとのA/B/C監査',['ID','経路','接続','区分','判定の意味','根拠'],EDGES,'<p>Aの矢印も条件付き計算内の対応であり、実機・実車の因果効果ではない。</p>')
dataset('07_COMMON_FRAMEWORK','二経路の共通枠組みと到達段階',['分類','配送計画','電池材料'],FRAMEWORK)
structure=[
 ('問い',RQ,'ポスターの目的、全条件一覧と対応する。'),
 ('目的','保存定量結果と文献から、量子計算が二経路を通じて寄与し得る条件・制約を整理する。','研究方針を変更していない。'),
 ('方法：配送','古典初期解・各支持・保存候補を区別し、同じJと制約で460問題例の保存結果を再集計・算術検証する。','新しい探索は行わない。'),
 ('方法：材料','①の簡略質量・固定速度DCと、②の部材別183設計・未知差の会計を分離して分析する。','新しい材料計算や速度再積分は行わない。'),
 ('結果：配送','限定位置交換は同支持最小＝初期値、GMでは7入力改善と25配送先以上の平均悪化、隣接交換は限定gridのt=0選択である。','A01–A04。8設定を同一アルゴリズムとしない。'),
 ('結果：材料','①の5.67%→0.478%→0.413%、②の代表部材差と183完成質量未確定、bridge会計の恒等式を確認した。','A05–A09。完成パック実測ではない。'),
 ('考察：配送','支持に改善候補が存在することは厳密改善の必要条件である。限定位置交換はその条件を満たさない。','B01。存在だけでは取得・採用の十分条件ではない。'),
 ('考察：材料','既知部材軽量化が正でも、未知部材差が達する／超えると質量収支の軽量化は消失／逆転する。','B02。実用成立の十分条件ではない。'),
 ('統合','上流の能力だけでは下流の成果は決まらず、探索範囲・採用・部材・走行条件の接続を確認する必要がある。','B05。計画品質と固定速度DCの評価段階は異なる。'),
 ('範囲','二経路、定時配達率除外、量子優位性を目的にしない、面接・RIQ・M1を採用しない。','保存値・原本を保全する。')]
dataset('03_RESEARCH_STRUCTURE','問い・方法・結果・考察の対応',['項目','内容','根拠・境界'],structure)
refrows=[]
for v in REFS:
 f=R/'sources'/(v['file']+'.pdf');refrows.append([v['id'],f"{v['author']} ({v['year']}). {v['title']}. {v['journal']}",v['doi'],v['locator'],v['use'],hashlib.sha256(f.read_bytes()).hexdigest()])
dataset('08_REFERENCES','参考文献と一次資料の役割',['番号','書誌','DOI','確認箇所','使用範囲','保存PDFのSHA256'],refrows,''.join('<p>['+str(v['n'])+'] <a href="'+esc(v['url'])+'">'+esc(v['title'])+'</a> ／ <a href="../sources/'+v['file']+'.pdf">保存一次資料</a></p>' for v in REFS))
# Preserve originals, including previous outputs and all saved exact certificates.
inv=list(csv.DictReader((R/'00_SOURCE_INVENTORY.csv').open()));pres=[]
for v in inv:
 f=Path(v['path']);now=hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else 'MISSING';pres.append([str(f),v['sha256'],now,'PASS' if now==v['sha256'] else 'FAIL'])
assert all(v[-1]=='PASS' for v in pres)
with (R/'evidence/ORIGINAL_PRESERVATION.csv').open('w',newline='') as f:w=csv.writer(f);w.writerow(['path','before_or_saved_sha256','final_sha256','status']);w.writerows(pres)
base=json.loads((R/'evidence/AUDIT_RESULTS.json').read_text());ext=json.loads((R/'evidence/EXTENDED_AUDIT.json').read_text());replay=json.loads((R/'evidence/ROUTE_REPLAY_SUMMARY.json').read_text())
coverage=csvtable(R/'evidence/GLOBAL_REFERENCE_COVERAGE.csv')
num='<p>前版の41項目＋13項目、計54項目の監査に不一致はない。保存経路36,800件の目的値と全訪問・需要容量・帰庫制約の元行列照合も前版で完了しており、今回は元資料hashの一致により引き継いだ。新しい経路探索・状態準備・回路実行・速度再積分は行っていない。</p>'
num+='<h2>数値照合表</h2>'+csvtable(R/'evidence/NUMERICAL_CHECKS.csv')+'<h2>追加監査</h2>'+csvtable(R/'evidence/EXTENDED_CHECKS.csv')+'<h2>全問題の厳密最適値</h2>'+coverage+'<h2>CPU工程</h2>'+csvtable(R/'evidence/TIME_SCOPE_AUDIT.csv')+'<h2>材料・質量・DC</h2>'+csvtable(R/'evidence/C_MASS_DC_RECONCILIATION.csv')
page('09_NUMERIC_AUDIT.html','数値・計算条件・出典の照合結果',num)
body='''<h2>説明の構造を変更した点</h2><p>前版は監査上の分類・数値・留保を先に示し、研究全体の目的と分析範囲を理解する前に記号や条件を読む構成であった。本版は、目的と二経路の工程図を先に示し、比較・計算した内容、観測結果、その意味、未検証の接続の順に再構成した。</p><p>古典初期解を基準の訪問順、比容量を活物質1kg当たりの電気容量として定義した。材料側は、容量固定の簡略計算から、部材質量が変わる設計を別に調べる理由へ進む構成とした。A/B/Cの根拠区分は補足台帳に保持し、本文では結果・解釈・未検証を文章で示す。</p><p>以下の科学的根拠・制限は前版の監査を引き継いだものである。説明を改善するために保存数値や研究方針を変更したものではない。</p><h2>今回の確認と変更方針</h2><p>現行run04の編集可能PPTX・生成コード、保存配送460問題例と集計コード、T08・T09・Controlled-DC、11月2日の方法・結果・考察原稿、11月3日の統合原稿、一次資料を確認した。AGENTS.mdは確認できなかった。指定タイトルは、検討対象の探索処理・材料物性計算に対応する「量子計算」を用いた表現として採用した。資料の日付から棄却済みの方法を復活させず、最新の明示的な採用方針を優先する。</p><p>元資料と前版成果物2,040ファイルは現状確認で全件hash一致した。今回は保存値を変更せず、読者が研究の目的・方法・結果・意味を追える順に全面再構成した。前版の54監査項目と36,800保存経路の照合結果を元資料hashの一致により引き継いだ。新しい探索、材料計算、速度シミュレーションや数値結果の再作成は実施していない。</p><p class="note">研究方針は維持した。保存結果、文献・モデルに基づく解釈、未検証の接続を分離した。A/B/Cの記号は補足の接続台帳に保持し、本文では文章で説明した。Aは固定モデル内の確認であり、量子技術の実機・実車の因果効果や社会的価値の実証ではない。</p>
<h2>最も重要な発見</h2><p>配送では、限定位置交換5設定の全2,300学習記録で、同支持の古典厳密最小値が古典初期値と一致した。したがって、この固定目的値と支持の下では探索器の変更だけで厳密改善は起こらない。これは支持の改善余地に関する知見であり、量子計算一般の能力限界ではない。この必要条件は目的値の厳密改善に限り、同じ計画を早く得る等の別の寄与まで否定するものではない。取得時間差の運用価値は未検証である。全順列GMの大規模平均悪化は、広い範囲だけでは現行予算下の取得品質が保証されない例である。ただし支持・学習・予算が同時に異なり、範囲拡大の単独因果効果は同定していない。</p><p>材料では、既知部材軽量化bが正でも、未知部材のS−LP差δにより正味軽量化b−δが消失・逆転する。固定面積と担持量固定でbが異なり、材料入力だけで完成パック質量を確定できない。この符号境界は質量会計の推論であり、安全性や実用成立の証明ではない。</p>
<h2>監査対象・指示・作業順序</h2><p>run04のPPTX、PDF、本文、生成コードを入力とし、保存CSV、固定仕様、方法・結果・考察原稿、実装snapshotと証明を照合した。本文抽出→数値と実装の照合→主張監査→修正特定→再編集→PPTX実描画→自己レビューの順で進めた。研究方法に面接・RIQ・M1を再導入せず、定時配達率を主要指標に戻していない。祖先とリポジトリ内でAGENTS.mdは確認できなかった。</p>
<h2>配送：初期解・支持・候補・検証・採用の分離</h2><p>古典初期解は旧無時間窓系列の保存された決定的ヒューリスティック解である。実装では3種類の決定的構成（due/readyによる最近傍系と挿入）を比較し、relocateと有向反転を最大3 sweep行う。今回、再生成せず、460入力の経路・入力hash・目的値を保存基準解と照合した。初期解は常に全問題の最適解ではない。</p><p>限定位置交換5設定は初期経路の対称位置i,n−1−iを交換する2^floor(n/2)の支持を用い、MEAN_P2、CVAR10_P2、CVAR01_P2、COHERENT2_P2、COHERENT4_P2を区別する。全顧客を保持し、地域別に顧客分割した部分問題や、列挙した候補経路プールから選ぶ方式ではない。同支持最小は古典chain-DPで評価する。</p><p>ACTIVE_ADJACENT_P3_GRIDは層数3の隣接swapとt={0,0.5,1}の限定探索である。全460入力でt=0を選んだことと、全連続角度の大域最適性、隣接交換全体の改善解不存在は異なる。後者二つは確認していない。</p><p>GROVER_P2/P3だけが理想全n!順列の一様状態を用いるGrover-mixer QAOAである。費用位相とrank-oneミキサーをCPUで数値処理する。通常のmarked-item Grover検索ではない。固定65,536学習費用poolは角度評価用の標本であり、最終経路を選ぶ事前列挙候補集合や実施済みの顧客分割ではない。角度は2開始点のCOBYLA・最大68固有評価、最終βの解析処理であり、角度の大域最適を証明していない。</p><p>25配送先は複素部分集合DP、100・125配送先は独立一様MCの共有prefix・既定精度で最終状態を検証する。Born分布に対応する候補は、CPU上で一様順列の提案に振幅由来の受理確率を用いる棄却標本法により生成される。8192は受理された標本数であり、提案総数や実機ショット数ではない。各反復内の近最小候補を元制約・正確な目的値で再検証し、最良候補を評価する。初期解とのminを取って悪化を隠していない。</p><p>25・100・125配送先はいずれも全8設定を実行した保存記録があり、各設定の入力数は78、78、70である。主表の数値はGM2設定のみであり、他6設定は別群の支持・角度条件として記す。同じ入力・目的値・実行可能性を使う一方、支持・学習目的・計算予算は同一ではない。公平なアルゴリズム順位や量子優位性の比較ではない。</p>
<h2>三つの比較基準・53入力の意味</h2><p>J0は保存古典初期経路の目的値、J_orbitは限定matching支持の厳密最小、J*は全配送先閉路の固定OD目的値の厳密最適値である。Jはデポ出発・帰庫を含む有向OD旅行時間和であり、サービス時間を目的へ加えない。各配送先1回訪問、総需要≤216 PE、J＋102n≤32,400秒を保存実行可能性として検査し、顧客時間窓は設けない。</p><p>407入力のJ*は全問題の厳密最適値であり、範囲内最小ではない。3・4・5配送先は独立列挙、25配送先は厳密整数Held–Karp、100・125配送先の証明済み集合は厳密有理下界と独立実行可能閉路の一致に基づく。460の証明ファイルhashを台帳と照合し、証明済み407値をFractionで照合した。</p><p>残る53入力はファイルの単なる未保存ではなく、EXACT_BOUND_WITNESS_MISMATCH、proved_optimal=falseである。全てtime_limit_reached=falseであり、今回タイムアウトと解釈していない。100配送先21例・125配送先32例に偏り、各方式で同じ入力が欠測となる。数値上近い下界・実行可能値でも厳密一致へ丸めず、0gapを代入しない。407入力での条件付きgapを全460の最適性に一般化しない。</p>
<h2>表の定義と正規化</h2><p>1問題例は配送先・移動時間行列の1組であり、測定反復とは別である。3・4・5・25・100配送先各78入力、125配送先70入力、計460入力である。8設定×10測定反復＝36,800保存参照、学習fitは3,680である。各fitを10反復へ重複計上しない。</p><p>ΔJ=J_best−J0、相対差=100ΔJ/J0である。10反復を入力内で平均し、その後入力間を等重み平均した。別添に保持した相対差はこの順の平均であり、規模平均ΔJを規模平均J0で割った比ではない。既存保存値の派生算術であり、新しい実験ではない。幅は層数2・3の2つの平均の最小～最大であり、信頼区間・標準誤差ではない。主表の秒差は2桁に丸めた。相対差は保存した別添に示す。</p><p>改善7入力はR1_020（4先）とR2_027、030、032、033、051、078（5先）であり、両GM設定で同じ集合である。反復を70独立問題例と数えない。25先以上の悪化は現行支持・学習・測定予算・初期解に条件付けられ、実機の有効規模限界としない。</p>
<h2>CPU工程時間と公平性</h2><p>25配送先・GM層数3の78fitを一度ずつ平均し、学習の壁時計時間0.888420618秒、最終状態・精度検証の壁時計時間168.745341710秒を再照合した。各工程78件の元JSONと保存pointer・hashを確認した。これらはCPU工程であり、候補生成だけの時間、実機時間、全求解時間ではない。</p><p>最終検証は保存結果を評価する数値計算工程であり、実運用で必須の量子後処理時間を測定したものではない。前処理、候補取得、通信、待ち、全体統合を含む統一工程値と、全fitの当時の共通実行環境は未確認である。古典初期解生成時間は別に保存されるが、現在の全設定に対する同予算が証明されていない。欠測工程の合算・推定や、公平な速度優位の主張はしない。実機ビット・深さ・ゲート列は未保存である。</p>
<h2>材料入力と①簡略質量・固定速度DC</h2><p>Chenら[5]は古典DFT・電極実験の入力出典である。1C・100サイクル後のLP121、S-200194 mAh/gを保持率70.4%、99.0%で割り、171.875、195.95959596 Ah/kgを逆算した。保存入力のS値は約195.959596に丸められている。保持率の定義と丸めに依存する参照値であり、初回全電池の実測ではない。材料計算を今回実行したとは述べない。</p><p>①はgross容量20kWh、平均セル電圧3.5V、負極比容量360Ah/kg、N/P1.1、正負活物質率0.75/0.98を固定し、塗工層に固定19＋15＝34kgを加えた簡略質量推計である。LP96.145654799→S90.697357384kg、差5.448297415kgである。完成パックの実測・工学的適格性の確認ではない。</p><p>非電池車体988.888888889kg、運転者55kg、積載0であり、走行質量1140.034543688→1134.586246273kgとなる。運転者は走行質量の固定項であり電池質量に含めない。削減率は各項目の（LP−S）/LPで、電池5.666712059%、走行質量0.477906345%である。</p><p>DCは旧古典460保存速度の下側Crr条件を主表示とし、LP合計1,440,101.369798Wh、差5,941.555975Wh、総量比0.412579010%である。個別百分率の単純平均ではない。上側条件は0.413590412%であり、両係数は信頼区間やタイヤ圧変更実験ではない。現在Bの460問題例とは別系列である。</p><p>1秒刻み・右端速度、転がりmgCrr ds、空力0.5ρCdA v²ds、並進0.5mΔv²、固定回転等価質量61kgの項を用い、合計仕事を区間ごとに正値化し効率0.90でDCへ換算する。平坦、回生・補機・旋回損失・荷重変化除外、観測保存区間のみである。保存終端以降の電力量は不明で補完しない。補機除外を実車補機消費0としない。対象EVへ校正した係数ではない。</p><p>変化の比は当該モデルの有限差分であり、走行質量減/電池質量減=0.084335738、DC減/走行質量減=0.863305153である。比容量の14.012856%増加からDC減への相対変化率比は0.029442893である。普遍係数・微分感度・量子因果効果ではない。固定の非電池質量と走行項の構成により、部分の変化が全体へ同じ割合で伝わらないことを示す。</p>
<h2>②部材別183設計とb−δ</h2><p>②は正負電極塗工層、Al/Cu集電体、セパレータ、電解液を個別計上する別モデルである。①の固定34kgを重ねて加えず、①の96.15→90.70kgや削減率を②の完成パックへ流用しない。183設計には参照材料・設計条件の複数系列を含み、全てが同じLP/S比較ではない。</p><p>代表LP/S比較の固定担持量は、正極活物質の面積当たり担持量kg/m²を共通にして必要面積が変わる条件である。固定面積はLP基準の正極面積を共通にし、担持量・厚さが変わる条件である。既往の改稿で「固定塗工量」を「固定担持量」として意味を明確化し、今回も維持した。代表bは担持量固定T09_ROW_031/032の9.722608121kg、面積固定T09_ROW_079/080の5.977891152kgである。</p><p>Kを既知部材小計、Uを未知部材として、b=K_LP−K_S、δ=U_S−U_LP、正味軽量化ΔM=(K_LP＋U_LP)−(K_S＋U_S)=b−δ、全てkgである。b−δ>0ならLP基準でSが軽い、=0なら差消失、<0なら逆転する。δ=bはこの質量収支のゼロ境界であり、δ<bは当該式内でΔM>0と同値である。実用電池・安全性の成立境界や十分条件ではない。</p><p>外装・タブ・余白・冷却・BMS・パック構造等が未確定で、完成パック質量は全183行で空である。182行HOLD_COMPLETE_PACK_MASS、1行FAIL_FULL_OPPOSING_FOOTPRINTであり、183保留＋1失敗ではない。bridge25,760行では旧460速度×2代表設計×7未知差×2Crr×2参照走行質量の会計を確認した。δは感度入力であり実測値ではない。δ=0は未知部材差が同じという仮定で、未知部材質量そのものを0とした意味ではない。</p>
<h2>量子材料文献・共通枠組みの役割</h2><p>Delgadoら[2]とShokrian Ziniら[7]は量子材料評価の対象・精度・誤り耐性資源を検討する先行研究である。Chenらの古典材料研究や今回の参照材料の改善を量子計算が実現した証拠ではない。量子評価情報が実際の選択・試験・電池設計に使われること、出力・寿命・安全性・構造質量の適格性は条件候補／未検証である。</p><p>Geels[4]は技術能力と主体・適用判断の区別に、Stilgoeら[3]は将来構成の予見とモデル前提・不成立条件の省察に限定して用いる。社会技術的移行の実証やRRI全過程の実施とはしない。Hollidayら[6]の古典探索と量子アニーリングの部分処理は役割分担の先行例であり、今回のGM-QAOA統合・動的運用の実績ではない。</p><p>共通枠組みはBであり、各接続をA/B/C別に監査した。今回のAの到達点は配送側が採用前の計画品質、材料側が固定速度条件のモデルDCである。異なる評価段階を同じ実運用成果として並べず、実運用採用・完成電池・実車成果はCの破線として残した。</p>
<h2>残存する課題</h2><p>H01–H08と接続表のCを参照する。全問題参照53件、統一された全工程時間・当時環境、実機回路資源、部分問題と全体統合、対象での量子材料情報の価値、完成パック質量・工学的成立、現在計画とDCの接続、実車校正が未解決である。現時点で最適性・速度・量子優位性・量子材料改善・実車性能の証明として扱わない。</p>
'''
body+='<h2>数値・原本保全・表示確認</h2>'+num.split('<h2>')[0]+'<p>原本・旧成果物・入力・元証明・ソースの'+str(len(pres))+'ファイルについてSHA256が一致した。commit・push・PR作成は行っていない。</p>'
validation=R/'render/FINAL_VALIDATION.json'
if validation.exists():body+='<pre>'+esc(validation.read_text())+'</pre><p>LibreOffice Impress 24.2.7.2でPPTXを実描画した。配布PDFはこの結果であり、Microsoft PowerPoint固有の描画と紙への試し刷りは未実施である。本文は主に21–24pt、主要数値23pt、見出し25–30pt、図の主ラベル21pt、補足17–19pt、文献18ptである。別添には全条件と再現上の制限を保持した。</p>'
selfcheck=[('問いと知見の対応','支持内改善余地と未知部材相殺を、それぞれの寄与条件として明示した。'),('二経路の統合','Bの共通枠組みと各接続のA/B/Cを対応させた。'),('確認済みと未検証','固定モデル内のAと実運用のCを混同しない。'),('具体的条件','改善解の範囲内存在、b・δの符号境界と固定条件を示した。'),('過剰な主張','量子優位性・実用化・社会的価値を実証したと述べない。'),('図表の根拠','54監査項目と36800経路の元行列算術検証で照合した。'),('最重要発見の伝達','限定位置交換の改善余地不在と、未知部材による相殺を考察の中心に置いた。')]
body+='<h2>自己レビュー</h2>'+table(['基準','確認結果'],selfcheck)
page('06_REVIEW_REPORT.html','学術レビュー・再修正報告',body)
links=[('01_RESEARCH_EXPLANATION.html','研究内容を目的から順に読む'),('../poster.pptx','再修正版ポスター：編集可能PPTX'),('../poster.pdf','実PPTX描画PDF'),('../poster_preview.png','確認用プレビュー'),('02_CHANGE_COMPARISON.html','修正対照表'),('02_TEXT_EXACT_COMPARISON.html','新旧の実テキスト'),('03_RESEARCH_STRUCTURE.html','研究構造'),('04_CONDITIONS.html','条件・制約20項目'),('05_UNTESTED_AND_HOLD.html','残存課題・HOLD8項目'),('07_CONNECTIONS_ABC.html','接続16件のA/B/C監査'),('07_COMMON_FRAMEWORK.html','二経路の評価段階の対応'),('10_CAUSAL_MODEL_REVIEW.html','因果モデルの削除・再定義・修飾条件'),('11_REQUIREMENT_COVERAGE.html','今回依頼の要件対応'),('05_UNVERIFIED_CONNECTIONS.html','未検証接続と今後の確認内容'),('causal_model_ABC.svg','接続の確認範囲を示す補足図'),('../evidence/POSTER_BLOCK_CLAIM_REGISTER.csv','紙面全テキストと根拠の台帳'),('08_REFERENCES.html','参考文献と一次資料'),('09_NUMERIC_AUDIT.html','数値・出典・条件の照合'),('06_REVIEW_REPORT.html','レビュー報告')]
index='<h1>'+esc(TITLE)+'</h1><p class="note">run05：研究の全体像→二つの分析→結果の意味→未検証の接続の順に読み直せる構成とした。保存数値と研究方針は変更していない。</p><p>配送側は支持内の改善余地、材料側は未知部材による質量差の相殺を中心に、異なるモデルと評価段階を分離した。</p><ul>'+''.join('<li><a href="reports/'+u+'">'+esc(t)+'</a></li>' for u,t in links)+'</ul>'
(R/'README.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>再修正成果物 run05</title><style>'+CSS+'</style><body>'+index+'</body></html>')
(R/'01_POLICY_AND_SCOPE.txt').write_text(TITLE+'\n\n'+RQ+'\n\n現在の方針を維持する。二経路の保存定量結果と文献から条件・制約を検討し、A/B/Cを区別する。面接・RIQ・M1、定時配達率、新たな科学実験を採用しない。\n現行入力：run04。新規出力：run05。原本・保存結果・旧成果物を保全する。\n相対差は前版と同じ保存目的値からの派生算術であり、再照合した。\n維持した重要な区別：53件は未保存ではなく全問題最適値未証明である。8設定を3群に分離し、①簡略質量モデルと②部材別モデルを分け、b−δ境界の適用範囲を限定する。\n')
print('Reports built; originals preserved:',len(pres))
