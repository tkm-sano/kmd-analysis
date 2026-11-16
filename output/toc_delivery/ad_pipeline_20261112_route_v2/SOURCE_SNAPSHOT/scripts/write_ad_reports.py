"""Render evidence-bound reports from completed result/audit files."""
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import statistics

ROOT=Path(os.environ.get('KMD_AD_OUTPUT_ROOT','output/toc_delivery/ad_pipeline_20261112'));DOC=Path('docs/research')
def read(name):return json.loads((ROOT/name).read_text())
def csvrows(name):return list(csv.DictReader((ROOT/name).open()))
def fmt(x):return '未取得' if x is None or x=='' else f'{float(x):.6f}'
def mdtable(headers,rows):return '|'+ '|'.join(headers)+'|\n|'+'|'.join(['---']*len(headers))+'|\n'+''.join('|'+ '|'.join(str(x).replace('|','/') for x in row)+'|\n' for row in rows)
def write(name,body):(DOC/name).write_text(body.rstrip()+'\n')

def main():
    rows=csvrows('A_TO_D_COMPARISON.csv');ranges=csvrows('OBSERVED_RANGES.csv');audit=read('INDEPENDENT_RAW_AUDIT.json');bundles=read('roads/COMMON_BUNDLES.json');meta=read('roads/ROAD_METADATA.json');route_based=meta.get('table_distances_used') is False
    checkpoint=read('roads/route_S3/CHECKPOINT.json' if route_based else 'roads/full_S3/CHECKPOINT.json');ref=read('EPSILON_REFERENCES.json')['S1']
    tour=read('FULL_TOUR_ROUTE_AUDIT/SUMMARY.json')
    all_tours=read('ALL_SCALES_FULL_TOUR_AUDIT.json')
    if not all(t['all_passed'] for t in all_tours):raise ValueError('ALL_SCALE_ROUTE_VERIFICATION_NOT_COMPLETE')
    all_tour_count=sum(t['tours'] for t in all_tours)
    if not route_based:raise ValueError('TABLE_RUN_REJECTED: set KMD_AD_OUTPUT_ROOT to the Route v2 root')
    road_audit=read('ALL_ROUTE_DATA_INDEPENDENT_AUDIT.json');exact_ref=read('ROAD_N6_EXACT_REFERENCE.json')
    if checkpoint['status']!='COMPLETE' or not tour['all_passed'] or not road_audit['passed']:raise ValueError('FINAL_ROAD_VERIFICATION_NOT_COMPLETE')
    attribution=read('D_ATTRIBUTION_AUDIT/SUMMARY.json')
    if not all(r.get('integer_tie_policy')=='primary_then_other_lexicographic_D-lex-v1' for r in attribution):raise ValueError('OLD_D_ATTRIBUTION_NOT_ADOPTED')
    same_seed=read('REPRODUCIBILITY_CHECK.json')
    small_D=next(r for r in rows if r['scenario']=='ROAD_N6' and r['method']=='D' and r['status']=='FEASIBLE')
    s1=[r for r in rows if r['scenario']=='S1'];good=[r for r in s1 if r['status']=='FEASIBLE'];a=[r for r in good if r['method'].startswith('A')];s1range=next(r for r in ranges if r['scenario']=='S1' and r['method']=='A_ALL')
    primary=[r for r in s1 if r['condition'] in ['B_primaryD_epsW_1','C_primaryD_epsW_1','D_primaryD_epsW_1']]
    first={r['method']:r for r in primary};witness=''
    if all(m in first and first[m]['status']=='FEASIBLE' for m in ['C','D']):
        delta=float(first['D']['D_km'])-float(first['C']['D_km'])
        witness=f"同じW上限のC可行解はDより{delta:.6f}km短い。これはS1のDが全体最適ではない具体的反証であり、有限IP−LP=0を全VRP gap=0へ転用できない。Cを参照とする距離差率は{100*delta/float(first['C']['D_km']):.6f}%（最適性gapの等式ではない）。"
    table=mdtable(['手法/条件','D［km］','W［分］','T_program［秒］','判定'],[[r['method']+'/'+r['condition'],fmt(r['D_km']),fmt(r['W_min']),fmt(r['T_program_s']),r['status']] for r in s1])
    range_table=mdtable(['手法','可行/試行','D min/median/max［km］','W min/median/max［分］','T_program min/max［秒］'],[[r['method'],r['feasible']+'/'+r['attempts'],' / '.join(fmt(r['D_km_'+k]) for k in ['min','median','max']),' / '.join(fmt(r['W_min_'+k]) for k in ['min','median','max']),fmt(r['T_program_s_min'])+' / '+fmt(r['T_program_s_max'])] for r in ranges if r['scenario']=='S1'])
    human=[h for h in csvrows('A_HUMAN_TIME_SENSITIVITY.csv') if h['scenario']=='S1' and 'repeat' not in h['condition']];human_range=[min(float(h['T_human_estimate_s']) for h in human),max(float(h['T_human_estimate_s']) for h in human)]
    testlog=(ROOT/'FINAL_REGRESSION_TESTS.log').read_text();tests=re.findall(r'(\d+) passed(?:, \d+ warnings)? in ([\d.]+)s',testlog)[-1]
    warning_matches=re.findall(r'(\d+) warnings',testlog);warning_count=int(warning_matches[-1]) if warning_matches else 0
    raw_total=sum(r['status']=='FEASIBLE' for r in rows);maxrss=max(float(r['max_rss_KiB']) for r in rows if r['max_rss_KiB'])
    d_results=[]
    for r in rows:
        if r['method']=='D' and r['status']=='FEASIBLE':
            rr=json.loads(Path(r['source']).read_text());m=rr['plan']['method_settings'];h=m['hybrid'];base=m['base'];lp=h['LP']['objective'];ip=h['IP']['objective']
            d_results.append({'scenario':r['scenario'],'condition':r['condition'],'macro_coverage':m['macro_full_route_coverage'],'columns':m['day_columns'],'qubits':m['qubits_max'],'LP':lp,'IP':ip,'restricted_integrality_gap':ip-lp,'finite_min_rc':min(h['LP']['rc']),'zero_columns':h['zero_face_added'],'quantum_pool_delta':m['quantum_candidate_pool_integer_delta'],'before_zero_IP':h['IP_before_zero_face']['objective'],'after_zero_IP':h['IP_after_zero_face']['objective'],'full_declared_IP':h['IP_all_declared_columns'],'T_s':float(r['T_program_s']),'max_rss_KiB':float(r['max_rss_KiB'])})
    (ROOT/'D_SCALING_SUMMARY.json').write_text(json.dumps(d_results,indent=2)+'\n')
    dtable=mdtable(['規模/条件','列数','qubits','macro被覆率','LP','IP','IP−LP','有限領域min rc','量子候補追加のIP差'],[[r['scenario']+'/'+r['condition'],r['columns'],r['qubits'],fmt(r['macro_coverage']),fmt(r['LP']),fmt(r['IP']),fmt(r['restricted_integrality_gap']),fmt(r['finite_min_rc']),fmt(r['quantum_pool_delta'])] for r in d_results])
    active_config=read('PREREGISTRATION.json')['config']
    link=f'証拠根：`{ROOT}/`。設定：`{active_config}`。実行前計画：`docs/research/A_TO_D_PIPELINE_IMPLEMENTATION_PLAN.md`。共通schema差分：`docs/research/A_TO_D_COMMON_INTERFACE.md`。'
    conditions='''# 共通運行条件・Wの独立監査

2026-11-12。共通条件v1.1のhashは `bbb15417a4eee5072f8118056c90ab422d792b4cedc35a6a06bf6bc0497fe8d2`。既存正本を変更していない。

|規模|需要単位/地点|車両|バース|総2便容量|最低便数|積込総占有/バース数|顧客作業/車両の下界|
|---|---|---|---|---|---|---|---|
|S1|1000/1000|10|2|1200|17|255分|200分|
|S2|2000/2000|20|4|2400|34|255分|200分|
|S3|4000/4000|40|8|4800|67|251.25分|200分|

最低便数はceil(N/60)。積込下界は最低便数×30/B分であり、離散便数のバースmakespan下界はceil(最低便数/B)×30＝270分（全規模）。これは配送実行可能性の証明ではない。S1は保存した可行計画が存在証拠。S2/S3はOD入力完了までで、運行実験未実行。

単位需要1、60単位/便、最大2便、積込1800秒、顧客作業120秒、帰着後準備0秒、勤務28800〜72000秒。積込も勤務時間内。全値は共通の研究仮定で、実事業者の実測値ではない。労働法令全体の充足を主張しない。

第1便readyは `28800+floor(3600*(v+0.5)/V)`。第2便readyは第1便の実帰着時刻。loading startはready以後、departureはloading end以後、顧客作業120秒と各道路移動のceil秒を順次反映し、帰着≤72000。1秒ごとの網羅的な離散変数は使わず整数秒で検査する。

`W=sum(load_start-ready)/60`。積込自体は含めない。参考値ready→積込終了は `W+30×実行便数` 分。車両待機を減らす目的でreadyをload_startに置き換えることは禁止。未使用車両には便・待機を生成しない。第2便の帰着が早ければ、その時点からバース待ちを数える。

Aは固定FCFS、B/Cは共通CP-SATが物理車両・1/2便・積込開始を選び、Dは有限日列masterが選ぶ。バースIDは実際の半開区間[start,end)の彩色で割り当て、開始時刻を修正しない。政策は手法間で異なり、制約とW定義を共通化している。

D=sum(全便の有向arc距離m)/1000。距離と時間は同じ静的OSRM最速経路であり、道路の最短距離経路とは限らない。顧客時間窓なし。積込開始を意図的に遅らせる場合も待機に計上。全手法が割当と順序を決定する。

T_programは入力読込直前〜共通独立検査完了のperf_counter wall秒。初期構築・変換・AOA/整数選択・完成を含む。OD前生成と保存・事後の追加監査は別。T_humanは未観測の工程感度で、T_programと別列。実機量子時間は測っていない。
'''
    write('COMMON_CONSTRAINT_AUDIT.md',conditions+'\n'+link)
    sizes=[]
    for b in bundles:
        if b['id'] in ['S1','S2','S3']:
            size=sum((Path(b['path'])/'od'/name).stat().st_size for name in ['distance_m.npy','duration_s.npy','reachable.npy']);sizes.append([b['id'],b['N']+1,(b['N']+1)**2,size,fmt(size/2**20),b['OD_hash']])
    write('COMMON_OD_VALIDATION.md',f'''# 共通実道路ODの検証

2026-11-12。S1/S2/S3入力生成・全OD検査：GO（地図と静的profileによる研究用道路モデルの範囲）。現地進入可否の保証ではない。

道路は既存関東PBF、OSM timestamp `{meta['osm_timestamp']}`、raw SHA256 `{meta['raw_sha256']}`。元の取得記録は残っておらず、2026-07-17の保存日とPBFヘッダを区別している。推定取得日を実測運行日とはしない。
ROAD_METADATAの年月日付きsource_urlは保存ファイル名からの推定で、元のダウンロードURLを確認した記録ではない。現在の公開URLから同日版を再取得できるとは確認できなかった。ヘッダのGeofabrik replication baseを根拠とし、再現時は保全済みPBFとhashを使う。詳細はsources/OSM_SOURCE_PROVENANCE_ADDENDUM.json。latestを同版として代入しない。
OSRM {meta['osrm_version']}、標準car.lua SHA256 `{meta['profile_sha256']}`、MLD。公式GHCR amd64 image digestはsources/OSRM_RUNTIME_MANIFEST.jsonに固定。Docker権限不足をユーザー空間の同じ公式バイナリで解決した。無料ローカル処理であり、公共OSRMへ大量要求していない。

OSM/OSRM出典：[OSM利用条件](https://www.openstreetmap.org/copyright)、[Geofabrik関東](https://download.geofabrik.de/asia/japan/kanto.html)、[OSRM Table/Route仕様](https://project-osrm.org/docs/v26.4.0/http)。© OpenStreetMap contributors。OSMはODbL、OSRM/VeRyPy等のソフトウェアライセンスは取得元manifest/LICENSEを参照。

拠点は[日本自動車ターミナル公式京浜案内](https://www.j-m-t.co.jp/terminal/keihin.html)と[公式構内図](https://www.j-m-t.co.jp/images/terminal/keihin/kei_map1.png)、OSM way235963579/node2440398083を照合し、西側中央の車両進入通路 `(lon139.7429862, lat35.5863301)` を採用。図面に基づく入口モデルで位置誤差目安20m、現地測量ではない。根拠はDEPOT_ENTRANCE_DECISION.json、原画像・地物図はsources/。

座標系はEPSG:4326、lon/lat。凍結地点の元座標を維持し、5候補から道路属性・同一OSM node pair・100m上限を検査。産業道路の地上trunk2wayは個別に通行属性を確認した例外で、全trunkを無条件許可していない。初回12地点の非連結を検出し、最大100候補へ拡張して同じ100m内の拠点往復可能候補を採用。元需要の間引き・移動はない。アクセス権の現地確認や建物搬入口確認を済ませたとはしない。

最終全4001地点・{checkpoint['audit']['pairs']:,}組、到達不能{checkpoint['audit']['unreachable_pairs']}、距離非対称セル{checkpoint['audit']['asymmetric_directed_cells']:,}。全自己距離/時間0、非負・有限・単位m/sを検査。**採用ODは全ordered pairをRoute APIから生成し、同じRoute objectのdistance/durationと注釈node列を保存した。Table距離は採用していない。**

初回Table版では負距離11組を検出し、さらに代表S1の91便中12便でRoute距離と不一致（固有7arc、0.8〜41.8m差、時間一致）。OSRM26.11.0を同じPBF/同じprofileで再構築しても差を再現した。Table値や差の原因を推定で正当化せず、初回入力/全結果を`output/toc_delivery/ad_pipeline_20261112/`に保全しTABLE_DISTANCE_REJECTION.mdで正式採用を保留した。最新版graphは診断専用で、採用データへ混在させていない。

v2はRoute全組方式へ変更した。S1→S2→S3の順に生成し、既に得た同じID pairの経路をOD hash/元block参照で引き継ぐ。各pairの元座標+同じhint、返却snap同一性、Routeの非負distance/duration・annotated nodesを確認し、推定速度・直線距離・0埋めを使わない。保存したS1可行計画の全{tour['tours']}便で、連結Routeの全legとpair ODが距離/時間とも丸め許容0.25m/0.25秒以内に一致（{tour['passed']}/{tour['tours']}）。顧客停車時の方向変更を許す`continue_straight=false`という共通ODモデルの仮定を明記する。

生成器とは別実装で、全{road_audit['pair_records_audited']:,}件の保存pair recordを配列と照合した。注釈付き実Route応答{road_audit['direct_annotated_HTTP_paths']:,}組と祖先参照{road_audit['ancestor_records_audited']:,}組のID・hash・距離/時間・snap・node列を確認し、S1⊆S2⊆S3の3配列が全組で同一と検証。ALL_ROUTE_DATA_INDEPENDENT_AUDIT.jsonを参照。

25×25のblock、S3は{checkpoint['total']}block。gzip原Route応答・SHA256・context pin・mmapで再開する。S1は4thread、その後8fork worker/同じOSRM graphの8threadへ実行資源だけを変更した。OD_RESOURCE_REVISION_1.jsonに停止前後と変更しない条件を記録。キャッシュの全hashと完成配列hashを確認し、既完成S1はそのまま再利用。S3段階wallは{checkpoint['elapsed_s']:.3f}秒で、S1/S2やgraph構築を含む全取得時間ではない。全段階のROUTE_OD_BUILD*RESOURCES、各route_S*/CHECKPOINTへ実測を保存した。

{mdtable(['規模','地点','OD組','3配列bytes','MiB','OD SHA256'],sizes)}

S1/S2の既計算pairをS3へ引き継ぐので、重複するID pairの距離/時間は同一。地点順とfingerprintを固定し、全方法は同じinput.json/manifest/npyを読む。入力hashとOD hashはCOMMON_BUNDLES.json/比較CSVに記録。S3の3配列は約260MiB。関東graphは約3.6GB、graph処理最大RSSは約3.6GiB。道路データ・profile・全graphのhashと生成コマンドはROAD_METADATA.jsonに保存。

注意：car profileの静的速度はモデル仮定。weight_name=routabilityを原応答に残しており、仕様上のfastest_same_routeはOSRM profileによる経路選択を指す。duration単独の数学的最小性を証明していない。渋滞・時刻変動・全車両の寸法規制・実走行距離は表していない。徒歩区間を道路ODへ追加しない。

{link}
''')
    write('A_HUMAN_TIME_CALIBRATION.md',f'''# Aの人手T：根拠・校正状況・感度

2026-11-12。工程モデル算術はGO、実務係数の実測校正はHOLD。人手実験は実施していない。プログラム実行を人手計画の実測として扱わない。

[日本郵便の公開事例](https://loogia.jp/cases/nihonyubin/)は従来の紙地図によるルート作成について、熟練者300〜600秒、初心者1800〜3600秒を記載する。一方、対応する配送先数・車両数・並列作成人数と準備/検査範囲がなく、S1への比例換算係数を同定できない。日本郵便の値であり佐川急便の測定ではない。2021年事例として保存した。

[佐川急便の担当コース説明](https://www.sagawa-exp.co.jp/about-csr/column/article_33.html)は業務の参考に用いる。2025年の13km/通常約20kmを2020年人手計画レンジにせず、拠点間荷積み待ち26分やLoogia導入後/改善率をD/W/Tへ代入しない。

固定済みa_rule_baseline_v1.jsonを維持。低/中央/高の3作業速度、人数P=1/ceil(V/2)/Vの9条件。各使用車両iの顧客数n_iについて、job_i=車両準備+(地点照合+順序決定+地点レビュー)×n_i。工程経過時間は `共通準備+a*N+c*使用車両数+LPTによるP人のjob最大累積`。総person_secondsは並列jobの単純和で別保存し、Tには用いない。

低/中央/高の係数は、準備300/600/900秒、中央割当2/4/8秒/地点、車両準備60/120/240秒、照合5/10/20秒/地点、順序5/10/20秒/地点、レビュー2/4/8秒/地点、全体調整30/60/120秒/使用車両。すべて明示した研究仮定で、公開値から校正済みではない。A3の人手判断回数と改善熟練度は未校正。

均等100地点/車を仮定した旧構造レンジはS1=3860〜60500、S2=6160〜120100、S3=10760〜239300秒で再計算一致。ただし入力準備・最終検査の未知部分を含む完全Tの保証範囲ではない。

今回の可行S1計画の実際の負荷配分を入れ、プログラムの共通入力読込＋共通検査wallを別成分として加えた感度は **{human_range[0]:.6f}〜{human_range[1]:.6f}秒**。A_HUMAN_TIME_SENSITIVITY.csvに全条件・人数・人秒・工程・機械overheadを保存。この機械overheadを人の住所入力や最終判断時間の代替としない。人固有の入力/確認工程の未測定追加時間は未同定で、上記に無制限な外挿根拠はない。

採用：T_programはA〜Dと同じ境界の実測として比較可能。T_human感度は条件付き推計の補助図表のみ。人手対プログラムの何倍高速という実証はHOLD。実際の人手Tを埋めず、未知の工程はunknownのまま残す。

次の研究者作業：ROAD_N20→ROAD_N120の同じ入力を人が地図上で割当/順序/バースまで作り、準備・割当・車両別作成・調整・最終検査の開始終了、人数、経験、修正回数、可行性を記録する。複数人数/規模で係数を推定し、holdoutの誤差で外挿可能範囲を判断。事業者への問い合わせ・外部依頼は行っていない。

{link}
''')
    bc=[r for r in rows if r['method'] in ['B','C']]
    write('B_C_EXECUTION_REPORT.md',f'''# B・Cの共通条件実行

2026-11-12。小規模6/20/120/240→S1。以下は保存した実測で、一般的な優劣の証明ではない。

{mdtable(['規模','方法/条件','判定','D［km］','W［分］','T_program［秒］'],[[r['scenario'],r['method']+'/'+r['condition'],r['status'],fmt(r['D_km']),fmt(r['W_min']),fmt(r['T_program_s'])] for r in bc])}

BはVeRyPyの節約量計算を再利用。上流parallel_savings_initは対称距離前提なので、そのまま有向ODで実行したとは記載しない。有向tail→head結合・逆転なしのCW派生法。容量60、便数過多なら最小便を他便へ最小増分挿入し、物理車両/バースは共通CP-SATで完成する。名称は「有向CW＋共通古典完成器」。外部コードは改変せずcommit/LICENSE/hashをVERY_PY_PROVENANCE.jsonに保存。

CはOR-Tools9.14.6206 Routing、2V仮想便、容量、directed decimeter arc、CW初期解、PCI/GLSで60秒。その最終経路集合と初期経路集合の和集合を、同じ共通CP-SATで物理車両2便とバースへ接続する。勤務/積込排他はRouting内ではなく最終完成器で満たす。有限route poolからの選択で、全VRPの最適性保証ではない。[公式Routing文書](https://developers.google.com/optimization/routing)。

完成器は1 worker/seed20261112/最大30秒。第1便readyは固定、第2便readyは変数の第1便帰着。積込1800秒のoptional interval cumulative B。顧客被覆・容量・帰着・便数を同時制約化。Dは0.1m整数費用、Wは整数秒。主目的と副目的の厳密lexicographic tie breakを使い、恣意的な加重和のトレードオフは導入しない。D/Wの主評価は両方向ε。

S1共通参照は事前のA順で最初に可行な {ref['method']} offset={ref['offset']}、D_ref={ref['D_km']:.6f}km、W_ref={ref['W_min']:.6f}分。ε_D=D_ref×[1,1.1,1.25]、ε_W=W_ref×[1,1.25,1.5]。EPSILON_REFERENCES.jsonをB/C/D実行前に保存。A1失敗を隠して参照を作っていない。

Tは毎回新プロセスで読込・初期構築・Routing・CP完成・共通検査までを含む。比較CSVにinput/optimization/validation内訳、raw timing_eventsに細分化を保存。60秒上限のため探索結果は同seedでもwall環境で終端が変わり得る。時間平均や統計的優位性は単発条件集合から主張しない。RSSも各プロセス実測。

{link}
''')
    macro_path=ROOT/'D_MACRO_SCOPE_AUDIT/SUMMARY.json';macro=json.loads(macro_path.read_text()) if macro_path.exists() else []
    write('D_SCALING_VALIDATION.md',f'''# D：探索被覆・整数gap・実道路規模拡張

2026-11-12。既存Huang AOA/Qiskit・日列make_day/検査を保全して、新規pipeline/hybrid.pyで接続。DのS1数値は有限マクロ候補によるhybridの結果であり、旧小規模全列モデルの完全スケール化や全VRPの最適性を意味しない。

{dtable}

LP/IP/被約費用/候補追加deltaの単位は、primaryDがkm、primaryWが分。範囲の異なるmasterのLPをS1全体の下界とは呼ばない。

AOAはCW各便を3連続fragmentへ縮約し、その内部順を保った順列を2回提案する。実際のQiskit状態ベクトル回路を実行し、完全macro順列をサンプルできた場合だけ新routeとして展開。古典全列oracleをサンプルへ混入しない。最大12qubits（安全上限16）、p=2、80角度評価、train1000/final4096shots、seed=20261112+100*round+route_index。最終量子実機時間ではない。

実装の量子ビット数は `q=(候補node数)*(可変位置数)`。S1の1000顧客を未圧縮で候補とし60訪問位置を持たせるなら60060qubitsとなり、状態ベクトルだけでも16×2^60060 bytesを要する（符号化上の算術、未実行）。既存実装のnode数≤7/qubits≤21ガードも通らない。今回のS1はこの未圧縮問題を実行したものではなく、3fragmentのkernelを全需要の古典日列モデルへ接続したもの。候補列数・時間/メモリは増大するが、量子kernelを固定した分だけ探索域を制限している。

時間内訳はD_TIME_BREAKDOWN.csv。初期古典完成、変換/基底CG、AOA提案、拡張catalogue/LP/IP、組立、共通検査を分離した。training_simulatorとQiskit_circuitの秒数はAOA提案wallの内訳で、重複加算しない。実機量子時間は未測定/null。

車両日列は実車両・最大2便・同一OD・固定seed calendarを用いる。バースは全積込開始/終了端点の区間行で厳密に表し、1秒スロット行を圧縮した。顧客/車両/バース/ε双対による真の被約費用は日列masterで照合する。AOA自体は距離/顧客双対を用いる限定提案で、バース/車両/ε資源の完全な価格付けではない。W目的では単位違いのW双対をkmから引かず、距離提案→W日列選択とする。この限定はCONDITIONAL GOの理由。

古典seed/列生成→AOA新規候補→同じ有限masterのLP/IP/ゼロ面補充を別記録。量子候補追加のIP差は表のdeltaで確認する。差0を量子性能改善と呼ばない。帰属監査で、初回S1の同距離IP選択がWを320.2分へ悪化させていたため、修正前D全出力をD_PRE_LEXICOGRAPHICへ保存してDを再実行した。D-lex-v1では主目的incumbentを悪化させず他方の指標を最小化する第2段階MILPを追加し、B/Cと同じ同点規則に揃えた。各IPの2段階合計予算30秒と外側300秒を維持。共通OD・需要・A・ε・AOA/domainは変更していない。S1の最初の条件はW320.2→285.75分、距離444.1768kmで、これは古典整数選択の修正であり量子改善ではない。

{mdtable(['条件','古典対照D/km','古典対照W/分','最終D/km','最終W/分','新AOA経路の採用本数'],[[r['condition'],fmt(r['classical_master_D_km']),fmt(r['classical_master_W_min']),fmt(r['final_D_km']),fmt(r['final_W_min']),r['new_AOA_routes_selected']] for r in attribution])}

今回のS1全ε条件・同seed反復では新AOA経路の最終採用0本、整数主目的の改善0。量子固有の改善は確認されなかった。主目的/副目的の同点処理と有限calendar領域、完全な全域価格付けを区別する。D/Bの探索政策や時刻領域が全く同じとは主張しない。

LP閉包後も整数解に必要な0/正rc列が不足し得る。新規回帰反例ではLP=3分、ゼロ面後IP=4分、正rcを持つ宣言済み列を含むIP=3.1分。そこでgapが残れば宣言済み全有限列のIPを別の古典処理として解く。LP閉包を整数最適性と呼ばない。有限IP−LP、有限min rc、MILP証明状態をraw結果へ保存。領域外の全VRP負列・整数gapはunknown。

旧Dの同じ人工6顧客回帰を今回再実行：旧最終双対の負列212本は旧候補域では0本（被覆0）、拡張域は212本（被覆100%、AOA3seedとも取得）。旧AOAはD4.2/全列IP3.6kmでgap0.6km、ゼロ面だけでは3.9km/負列212本残存、拡張・古典補充/置換で3.6kmに一致。旧古典CGの3.9→3.6kmも同じ古典補充で改善。証拠は親版output/toc_delivery/ad_pipeline_20261112/D_LEGACY_COVERAGE_RECHECK/COVERAGE.csvと同D_LEGACY_INTEGRATED_RECHECK/INTEGER_GAPS.csv。これは人工回帰の改善前後で、S1 gapの数値へ転用しない。

実道路小規模の同一macro・同一calendar全順列古典対照はD_MACRO_SCOPE_AUDIT/SUMMARY.json。原oracleは実験後の監査専用でDへ注入しない。ROAD_N6のさらに独立した全訪問順/部分集合DP距離下界は{exact_ref['D_lower_bound_km']:.6f}km、可行日程で達成し厳密な小問題距離参照となった。S1へ厳密性を外挿しない。

ROAD_N6のDは{float(small_D['D_km']):.6f}kmで、上記厳密距離参照との差は{float(small_D['D_km'])-exact_ref['D_lower_bound_km']:.6f}km。小問題でも固定fragment内部を探索しない影響が残る。有限macro内のIP gap=0を全経路に対するgap=0とは呼ばない。

{mdtable(['規模','macro全順列数','取得率','実験IP','同一macro全列IP','参照との差','未取得負列'],[[r['case'],r['exact_macro_routes'],fmt(r['route_coverage']),fmt(r['experimental_IP']),fmt(r['exact_macro_IP']),fmt(r['same_scope_gap_to_exact_IP']),r.get('unobtained_negative_columns_in_exact_macro_scope','未同定')] for r in macro])}

S1の全1000地点を扱った事実は入力hash・計画被覆の検査で確認。限定fragment内順序・固定calendar外の探索漏れは残る。HOLD解除は「実道路S1に接続した限定hybridとして数値が得られた」範囲のみで、グローバル完全価格付け・整数最適性・量子優位性のHOLDは解除しない。古典完成と量子計算の公平性は同一macro対照の範囲で評価する。

{witness}

{link}
''')
    comparison=f'''# A〜Dの対応付き比較・研究上の限界

2026-11-12。S1は1000配送先・10台・2バースの同一凍結需要/道路OD/v1.1。Aは従来業務を参考にした推計規則で、佐川の実績再現ではない。Bは有向CW派生、CはOR-Tools＋完成、Dは限定macro AOA日列hybrid。全方法とも同じ割当・順序・運行制約の問題で、完全探索を保証しない。

{table}

{range_table}

Aの範囲は固定9条件中可行6条件の観測範囲で信頼区間ではない。A1の3条件は勤務超過で棄却。最小Dと最小Wの計画が一致するとは限らず、列ごとの最小を一つの計画として結合しない。paired値の出典はCSVのsource。全試行・違反はraw result/planを保全した。

共通参照εでB/C/Dを比較する。異なるεの最良D/Wを合成しない。プログラムTは実測の同じ境界で比較可能だが、方法ごとの予算・実装・cache/ホスト条件を明記し、単発から一般的高速性・有意差を結論しない。道路OD前生成は共通でT外。Aの人手感度{human_range[0]:.3f}〜{human_range[1]:.3f}秒は未校正の仮定集合で、B〜DプログラムTとの実測速度比の証拠ではない。

Dの量子候補で実際に改善したかはD_SCALING_SUMMARY.jsonのIP差で確認。0なら量子固有効果を主張しない。主結果は研究上の同一条件の経験的比較であり、事業者の性能順位や量子優位性ではない。S2/S3は入力/道路ODまで完了し、四方法比較は未実行。

判定：同一条件のS1対応付きD/W/T_program比較は必要な可行値と独立検査が揃った範囲でGO。Aの外部妥当性/人手TとDの限定探索を含む論文採用全体はCONDITIONAL GO。実人手Tの校正、全VRP整数gap、量子固有改善の実証はHOLD。

{link}
'''
    write('A_TO_D_COMPARISON.md',comparison);shutil.copy2(ROOT/'A_TO_D_COMPARISON.csv',DOC/'A_TO_D_COMPARISON.csv')
    preservation=read('PRESERVATION_RESULT.json') if (ROOT/'PRESERVATION_RESULT.json').exists() else {'status':'最終hash検査前'}
    write('INDEPENDENT_VALIDATION.md',f'''# 独立検証

2026-11-12。既存Aの188テスト/2400監査成果を変更せず保全。今回は既存188件を含む **{tests[0]}テスト通過、{tests[1]}秒、警告{warning_count}件**。FINAL_REGRESSION_TESTS.logを参照。警告はpytestのmulti-thread環境でのforkに関するもので、無警告・他OS対応の検証済みとはしない。実データ生成はLinuxの専用起動プロセスで完了し、全出力を別実装で検査した。新規はdirected CW、物理2便/バース完成、元座標hint/1点ブロック、cache改竄/context変更拒否、人工ODの実道路偽装拒否、古典grid masterとのevent master LP/IP照合、別全探索IP、実AOA/JSON保存、正rc整数反例、Route各pair・thread/fork・祖先再利用等。

結果{audit['plans_audited']}可行計画を別のraw JSON/Decimal/区間sweepで再計算し、全件一致={audit['all_passed']}、検査項目{audit['checks']}。共通validate_plan、A既存独立recomputeに加えた第三計算で、実装本体の生成関数を呼ばず入力配列と生時刻からD/W・勤務・ready・容量・被覆・バース・ε・T境界を確認。INDEPENDENT_RAW_AUDIT.jsonに計画別結果。原ODと同じ配列を使うのは共通評価要件で、OSRM自体の正確性は別Route照合で検査。

ROAD_N6は全部分集合の全訪問順とtrip数mask DPで距離下界{exact_ref['D_lower_bound_km']:.6f}kmを求め、別可行スケジュールが達成。旧D全列参照・新event master・物理制約の別oracleを照合。S1の最適性証明ではない。

道路については全{road_audit['pair_records_audited']:,}件のraw recordとOD配列を独立照合し、全規模の保存可行計画{all_tour_count}便（うちS1 {tour['tours']}便）を連結Routeと再照合して全一致。Table初回の距離差を許容幅の変更で通過させず、全pairをRouteで作り直し全実験を再実行した。

失敗保全：初回snap非連結12、Table負距離11、hint照会ずれ、1点block400、D numpy JSON保存2件、初回新規試験のfixture指定/反例seed誤りを修正して再実行。A1の勤務違反3件は修復せず失敗のまま。最終結果の自動補正で成功化しない。道路の補正は原応答と再計算の双方を保存した。

保全結果：`{json.dumps(preservation,ensure_ascii=False)}`。詳細はPRESERVATION_RESULT.json。共通モデルのroad_validation追加のみ既存ソースを意図的に変更。需要/旧A・B・C・D/旧結果/固定設定の変更はしない。初期statusと最終status/diffを保存しcommit/pushを行わない。

seedは20261112、AOA派生seedは仕様式、Aは乱数なし。ロード→最終共通検査のT eventを全件確認。OR-Toolsのwall上限は同seedでも探索終端に変動があり得る。再実行の測定は別結果として保存し、厳密bit再現性を未確認のまま主張しない。

S1のA2/B/C/Dを各1回同seed反復し、全4方法で同じ入力/ODとD/W一致を確認した。REPRODUCIBILITY_CHECK.jsonは経路/時刻レコードの同一性と実測Tの差も保持する。これは単一反復で、異なるseedや環境に対する統計的安定性の証明ではない。

{link}
''')
    write('REPRODUCE.md',f'''# A〜D共通パイプライン再実行

2026-11-12。repo rootで実行。既存出力を上書きしない。現在の確定結果は `{ROOT}`。新しい比較では出力rootも新規版へ変更し、設定/コードhashを先に保存する。

環境：Linux x86_64、AMD EPYC9684X、Python3.12、numpy2.3.1、scipy1.16.0、qiskit2.1.1、ortools9.14.6206、osmium4.1.1、pytest8.4.2。ENVIRONMENT_FREEZE.txt/CPU.txt/PLATFORM.txtを参照。専用venvは `/home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python`。既存vehicle-day-v1を改変せず新venvへ追加。VeRyPy外部cloneのcommit/ライセンスはVERY_PY_PROVENANCE.json、import pathはvenv .pthに保存。

別環境の最小依存は上記版とmatplotlib3.10.3。VeRyPyは https://github.com/yorak/VeRyPy のcommit8698f910ffcfb4bc8743aedbf203d6de72fbe006、MIT。既存外部cloneを変更せず、別の新規cloneを同commitへ固定し、そのpathをPYTHONPATHまたはvenv .pthへ追加する。Gurobiや有料TSPサービスは呼ばない。全freezeは環境台帳で、無関係なGPUパッケージ全ての再導入を必須としない。

```bash
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export KMD_AD_OUTPUT_ROOT={ROOT}
/home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -m pytest tests/toc_pipeline tests/toc_baseline_a tests/toc_common tests/toc_cg tests/toc_vehicle_day tests/toc_search_improvement tests/test_toc_contracts.py -q -p no:cacheprovider

# 例：確定共通S1を新しい一時結果へ。入力読込は実行器内で計時。
/home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python scripts/run_ad_method.py --input {ROOT}/roads/inputs/S1 --method A3 --output /tmp/ad-new-A3
/home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python scripts/run_ad_method.py --input {ROOT}/roads/inputs/S1 --method B --primary D --other-limit {ref['W_min']} --output /tmp/ad-new-B
```

C/Dは--method C/D、同じε、同じ新規出力。A感度は `--offset 0`、`--offset 120`、`--offset 240`。C Routing60秒、共通schedule30秒、D外側stage300秒。Dは既存PricingAOAの実Qiskit simulationを使用。T内訳はresult.json timing_events、RSSはprocess KiB。未可行時T_programは空欄、失敗経過時間はelapsed_wall_s。

全固定条件の逐次実行は `scripts/run_ad_experiments.py`。完了resultは読み取り再利用して二重実行せず、A45試行→EPSILON_REFERENCES.json固定→B/C/Dの小中S1→S1両方向εの順。失敗は自動成功化しない。Table親版のFAILED_ATTEMPTS_REGISTER.jsonは初回D保存失敗2件の保全で、v2へ数値を流用しない。experiments/S1/*repeat*を別の同seed反復として読む。固定Aレンジへ反復を重複加算しない。

ODを再生成する場合は無料ローカルOSRM5.27.1。`scripts/bootstrap_local_osrm.py --rootfs /tmp/osrm-new-rootfs` は保存manifestの公式imageのlayer SHA256を検証しDocker不要で取り出す。LD_LIBRARY_PATHはそのusr/local/lib:usr/lib/x86_64-linux-gnu。PBFは保全した関東rawファイルを別作業ディレクトリへコピーし、下記を実行（binaryはrootfs/usr/local/bin）。

```bash
osrm-extract -p /tmp/osrm-new-rootfs/opt/car.lua -t 4 kanto.osm.pbf
osrm-partition -t 4 kanto.osrm
osrm-customize -t 4 kanto.osrm
osrm-routed --algorithm mld --port 5000 --threads 4 --max-table-size 1000 kanto.osrm
```

**採用OD生成口**は `scripts/build_route_pair_od.py --parent output/toc_delivery/ad_pipeline_20261112 --output NEW_ROOT --process-workers 8 --port 5002`。5002には同じOSRM5.27.1/graphを8threadで起動し、必要なら--verbosity ERRORとする。親版から使うのは凍結ID・座標・採択snap・道路来歴だけで、親のTable距離はコピーしない。全pairをRoute objectから取得し、注釈付きnode経路を保存する。S1完成後、同じRoute pairをS2/S3へhash付き参照で再利用。Linux fork workerの動作とthread/fork双方のcache再開/改竄拒否は回帰試験済み。OD_RESOURCE_REVISION_1.jsonに実行資源の変更を記録。

同じ採択snapを再現するには親版の保存済みnearest（expanded含む）/SNAP_ROAD_WAYS/CONNECTIVITY_REVIEW/SNAP_EXCEPTION_REVIEWと出入口decisionを維持する。旧build_common_road_odはTable診断の再現用で、最終採用ODの生成口ではない。メタデータの生成時刻もhashに含むので完全な同一入力hash比較には確定bundleを使う。新規graph版は新しいODとして区別。途中再開は同じroot/context、改竄cacheは拒否。通常の再実行で一度限りのforensic回復scriptsを実行しない。

集計・監査は `scripts/audit_ad_results.py` → `scripts/audit_d_macro_scope.py --include-s1` → `scripts/audit_ad_full_routes.py --all-feasible` → `scripts/audit_route_data.py` → `scripts/audit_ad_preservation.py` → `scripts/write_ad_reports.py`。解析対象rootは上記環境変数で指定する。旧Table結果を混ぜない。raw result/planを先に保存し、CSV/文書は派生物。Source snapshotとhash manifestが実装の版。

Dの最終整数同点規則はD_LEX_POLICY_REVISION.json、OD資源変更はOD_RESOURCE_REVISION_1.json、両者を反映した値はEFFECTIVE_SETTINGS.json。初期登録JSONを後から書き換えず、A/B/C・共通条件・ε/seedを維持した修正履歴を分離する。D_PRE_LEXICOGRAPHICは修正前で、最終比較へ混ぜない。再現性/帰属を再計算する場合はsummarize_ad_reproducibility.pyとaudit_d_attribution.pyも実行する。

上流原資料：OSRM/OSM/JMT/OR-Tools/VeRyPy/日本郵便事例のURL・取得hashはsources内manifest。非公開データ・有料API・会社連絡は使用しない。
''')
    four=all(any(r['method']==m and r['status']=='FEASIBLE' for r in s1) for m in ['B','C','D']) and bool(a)
    write('A_TO_D_PIPELINE_FINAL_REPORT.md',f'''# A〜D共通配送計画：最終報告

2026-11-12。**S1四条件の対応付きD/W/T_program取得={four}。論文採用全体はCONDITIONAL GO。** 佐川実績再現、人手Tの実測校正、全VRP最適性、量子優位性を達成したとはしない。

本報告とRoute v2の保存計画/CSVを今回の統合判定の正本とする。旧A_RULE_FINAL_DECISION等の「道路未整備のためS1 HOLD」は履歴として保全し、今回の証拠が揃ったD/W/T_programの範囲で解除する。人手Tの実測校正やDの全域完全価格付けのHOLDは解除しない。初回Table版の比較値は距離不一致を検出したため採用しない。

|工程|判定|完了した範囲/制限|
|---|---|---|
|1 共通条件|GO|v1.1保持、容量/ready/W/T/schema/hash監査|
|2 道路OD|GO（地図モデル）|S1/S2/S3全OD、入口図面/snap/到達性/Route照合。現地調査ではない|
|3 A実道路|CONDITIONAL GO|6/20/120/240/S1×9を実行、S1可行6/9。A1勤務超過を保持|
|4 T校正|CONDITIONAL GO|プログラムT全境界実測。人手係数は未観測・未校正でHOLD、感度のみ|
|5 B/C|GO（経験的S1比較）|同一入力、directed CW派生/OR-Tools＋共通完成、両方向ε|
|6 D|CONDITIONAL GO|S1全需要の限定macro AOA日列hybrid。全域価格付け/整数最適性/量子優位は未証明|
|7 統合/検証|GO（上記範囲）|共通/第二/第三検査、全列小問題参照、保全、対応CSV|

最初の共通ε条件はW≤{ref['W_min']:.6f}分。次の行は各々一つの保存計画で、別計画の最良値を合成していない。

{mdtable(['手法','D［km］','W［分］','T_program［秒］','最大RSS［KiB］'],[[r['method'],fmt(r['D_km']),fmt(r['W_min']),fmt(r['T_program_s']),r['max_rss_KiB']] for r in primary])}

{range_table}

AはS1可行6条件の推計観測範囲。DとWの最小・最大・中央値を別に示し、統計的信頼区間や佐川実績とは呼ばない。人手Tは固定作業仮定＋機械IO/検査の感度{human_range[0]:.3f}〜{human_range[1]:.3f}秒で、未知の人間の準備/確認を校正できていない。プログラムTとの速度比に用いない。

検証：既存188件を含む{tests[0]}テスト通過、{tests[1]}秒。第三計算{audit['plans_audited']}計画/{audit['checks']}検査項目、全一致={audit['all_passed']}。既存2400項目の監査成果は保全。ROAD_N6全訪問順/部分集合DPの厳密距離参照{exact_ref['D_lower_bound_km']:.6f}kmと可行日程が一致。全{road_audit['pair_records_audited']:,}件のraw OD recordと配列を独立照合し、全規模{all_tour_count}便（うちS1 {tour['tours']}便）の連結Routeが一致。

計算資源：AMD EPYC9684X、アプリ1worker、OSRMは初期4threads、Route拡張8threads/8fork workers。方法実行で観測した最大RSS{maxrss:.0f}KiB。graph構築/ODは別time -vログ（失敗含む）、final S3 ODは16008001組/float64距離・時間+bool到達性で約260MiB。時間/メモリのmethod別内訳は比較CSVとrawtiming。Qiskit状態ベクトル実測で、量子実機時間ではない。

Dの旧6顧客回帰：負列被覆0/212→212/212、限定整数D4.2→3.6km（古典完成を含む）。実道路S1は有限macroの被覆/min rc/LP-IP差を別保存し、旧回帰の完全性を移植しない。正rc整数反例を追加し、必要な宣言済み全列IPを古典処理として分離。量子候補による実際の改善差はD_SCALING_SUMMARY.json、0なら量子効果なし。

S1の最終Dは古典同点処理を修正してW320.2→285.75分（D444.1768km一定）。修正前を保全して全Dを再実行・再検査した。新AOA候補の最終採用0本/整数主目的改善0で、量子由来の改善は確認されなかった。修正効果を量子へ帰属しない。

残存課題（優先順）：①人手20/120地点の工程実測と入力/確認込み校正、②Dのmacro内部/車両間分割/時刻領域外の価格付けと同資源古典対照、③複数seed/反復・予算感度による経験的安定性、④S2/S3の段階的な四方法計算。S2/S3はODまで完了、数値比較未実行。現地入口/アクセス・車両規制・交通変動を研究境界外の未知として保持する。

保全：初期50162ファイルをhash登録し、最終結果はPRESERVATION_RESULT.json。既存コード変更は共通モデルにroad_validationを許可する最小追加のみ。凍結8、固定v1.1/A設定、旧A/B/C/Dと過去結果を保全。新規コード・成果物はpipeline/、scripts/、本研究報告、今回outputへ追加。git status/diffを保存し、commit/push/会社連絡/有料処理なし。

詳細：COMMON_OD_VALIDATION.md、COMMON_CONSTRAINT_AUDIT.md、A_HUMAN_TIME_CALIBRATION.md、B_C_EXECUTION_REPORT.md、D_SCALING_VALIDATION.md、A_TO_D_COMPARISON.md/CSV、INDEPENDENT_VALIDATION.md、REPRODUCE.md。

{link}
''')
    for name in ['A_TO_D_PIPELINE_FINAL_REPORT.md','COMMON_OD_VALIDATION.md','COMMON_CONSTRAINT_AUDIT.md','A_HUMAN_TIME_CALIBRATION.md','B_C_EXECUTION_REPORT.md','D_SCALING_VALIDATION.md','A_TO_D_COMPARISON.md','INDEPENDENT_VALIDATION.md','REPRODUCE.md','A_TO_D_COMMON_INTERFACE.md','A_TO_D_PIPELINE_IMPLEMENTATION_PLAN.md']:shutil.copy2(DOC/name,ROOT/name)
    print('reports rendered',len(rows),'result rows',raw_total,'feasible')

if __name__=='__main__':main()
