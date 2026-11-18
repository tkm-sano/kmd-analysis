"""Figures and an offline-readable metric dashboard with standard-output drilldown."""
import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, fontManager
from kmd_toc.dwt.evaluation import eligible

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else 'output/toc_delivery/dwt_balance_20261113_v1/revision_1_3_1')
font = Path.home() / '.local/share/fonts/NotoSansJP-Regular.ttf'
if font.exists():
    fontManager.addfont(str(font))
    plt.rcParams['font.family'] = FontProperties(fname=font).get_name()
plt.rcParams.update({'axes.spines.top': False, 'axes.spines.right': False, 'font.size': 10})
data = json.loads((ROOT / 'THREE_OBJECTIVE_EVALUATION.json').read_text())
rows = json.loads((ROOT / 'ALL_TRIALS.json').read_text())
selected = [r for r in rows if r['phase'] == 'limited' and eligible(r) and r['method'] in ('B', 'C', 'D')]
colors = {'B': '#2563a8', 'C': '#098574', 'D': '#914ab4'}
figures = ROOT / 'figures'
figures.mkdir(exist_ok=True)


def save(fig, name):
    fig.savefig(figures / (name + '.png'), dpi=300, bbox_inches='tight')
    fig.savefig(figures / (name + '.svg'), bbox_inches='tight')
    fig.savefig(figures / (name + '.pdf'), bbox_inches='tight')
    plt.close(fig)


fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')
for method in colors:
    rs = [r for r in selected if r['method'] == method]
    if rs:
        ax.scatter([r['D_km'] for r in rs], [r['W_min'] for r in rs], [r['T_program_s'] for r in rs],
                   c=colors[method], label=method, s=60)
for r in selected:
    if r['trial_id'] in data['front_trial_ids']:
        ax.text(r['D_km'], r['W_min'], r['T_program_s'], f" {r['method']} τ{r['tau_s']}", fontsize=8)
ax.set(xlabel='総走行距離 D [km]', ylabel='積込待機 W [分]', zlabel='実測 T_program [秒]',
       title='S1：観測されたD・W・Tの組合せ（各条件1試行）')
ax.legend()
fig.text(.05, .02, 'Aの人手Tは工程境界未校正のため除外。数学的Pareto最適性・母集団性能の証明ではない。', fontsize=9)
save(fig, '01_observed_DWT_front')

fig, axes = plt.subplots(2, 3, figsize=(14, 8), squeeze=False)
epsilons = sorted({r['epsilon_W_min'] for r in selected})
for i, eps in enumerate(epsilons):
    for j, (key, label) in enumerate([('D_km', 'D [km]'), ('W_min', 'W [分]'), ('T_program_s', 'T_program [秒]')]):
        ax = axes[i, j]
        for method in colors:
            rs = sorted([r for r in selected if r['epsilon_W_min'] == eps and r['method'] == method], key=lambda r: r['tau_s'])
            if rs:
                ax.plot([r['tau_s'] for r in rs], [r[key] for r in rs], 'o-', c=colors[method], label=method)
        ax.set(xlabel='計算予算 τ [秒]', ylabel=label, title=f'W上限 {eps:g}分')
        ax.grid(alpha=.2)
        ax.legend()
fig.suptitle('S1：予算と実測値の関係（失敗を0へ置換しない・各点1試行）')
fig.tight_layout()
save(fig, '02_budget_epsilon_response')

sens = [s for s in data['weight_reference_sensitivity'] if s['T_ref_multiplier'] == 1 and s['J'] is not None]
if sens:
    names = list(dict.fromkeys(s['trial_id'] for s in sens))
    profiles = ['equal', 'distance', 'waiting', 'time']
    matrix = [[next(s['J'] for s in sens if s['trial_id'] == n and s['weight_profile'] == p) for n in names] for p in profiles]
    fig, ax = plt.subplots(figsize=(max(10, len(names) * .8), 4))
    im = ax.imshow(matrix, aspect='auto', cmap='YlGnBu')
    ax.set_yticks(range(4), profiles)
    ax.set_xticks(range(len(names)), [n.replace('limited_S1_', '').replace('_r0', '') for n in names], rotation=40, ha='right', fontsize=8)
    for i, line in enumerate(matrix):
        for j, value in enumerate(line):
            ax.text(j, i, f'{value:.3f}', ha='center', va='center', fontsize=8)
    fig.colorbar(im, ax=ax, label='J（小さいほど小スコア、重みは研究設定例）')
    ax.set_title('S1：事前固定の重み感度（D/W/T参照は全手法共通）')
    fig.tight_layout()
    save(fig, '03_weight_sensitivity')

# Link the actual standard products, not a fabricated map from metric aggregates.
display = [{k: r.get(k) for k in ['trial_id', 'method', 'scenario_id', 'phase', 'epsilon_W_min', 'tau_s',
                                'D_km', 'W_min', 'T_program_s', 'status', 'feasible', 'error', 'export_error']}
           for r in rows if r['phase'] in ('limited', 'baseline', 'control')]
payload = json.dumps({'rows': display, 'front': data['front_trial_ids']}, ensure_ascii=False).replace('</', '<\\/')
html = r'''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DWT予算付き比較</title><style>body{font:15px system-ui,sans-serif;color:#152637;background:#f3f6fa;margin:0}main{max-width:1400px;margin:auto;padding:28px}h1{font-size:28px}section{background:white;padding:22px;margin:18px 0;border-radius:12px}table{border-collapse:collapse;width:100%;font-size:12px}th,td{padding:9px;border-bottom:1px solid #ddd;text-align:right}td:first-child,th:first-child{text-align:left}tr.front{background:#edf8ee}canvas{width:100%;height:480px;border:1px solid #eee}select{padding:10px;max-width:100%}svg{width:100%;height:auto}p{line-height:1.7}.warn{color:#8c3e22}.figs{display:flex;flex-wrap:wrap;gap:8px}.figs img{width:48%;object-fit:contain}#details{white-space:pre-wrap}</style><main>
<h1>大田区ToC配送：D・W・Tの予算付き比較</h1><p>保存済み共通Route ODによる限定シミュレーション。Tは入力読込から最終二重検査までの実測秒。τは上限であり実測Tとは異なる。<b>Aの人手Tは未校正で、B〜Dの3目的front/Jには含めない。</b></p>
<section><h2>全条件と観測された非支配点</h2><p>緑色の行がB〜Dの観測非支配点。未取得値を0で表示しない。失敗を含む全試行CSV/JSONを別保存。</p><table id="results"></table></section>
<section><h2>実際の配送計画とバース運用</h2><select id="trial"></select> <select id="vehicle"><option value="all">全車両</option></select> <select id="trip"><option value="all">全便</option><option value="1">第1便</option><option value="2">第2便</option></select><p id="details">計画を選択してください。</p><canvas id="map" width="1300" height="480"></canvas><div id="gantt"></div><p class="warn">直接HTMLを開く場合は指標表・図が表示されます。計画GeoJSONの読込にはREADMEのローカルHTTPサーバを使用してください。経路は保存Routeの実道路形状。背景タイルへの通信なし。</p></section>
<section><h2>3目的・予算反応・重み感度</h2><div class="figs"><img src="figures/01_observed_DWT_front.png" alt="DWT"><img src="figures/02_budget_epsilon_response.png" alt="予算反応"><img src="figures/03_weight_sensitivity.png" alt="重み感度"></div><p>重みは事業者の選好ではなく研究設定例。各cell1観測で、信頼区間・性能分布や純粋な予算の因果効果を示さない。</p><p>道路形状：© OpenStreetMap contributors / ODbL。外部タイル・経路APIへの通信なし。</p></section></main><script>
const DATA=__DATA__;let features=[];const palette=['#2166ac','#e1812c','#319b74','#8b5cb8','#ca5278','#697e39','#159cad','#b76d45','#726d9c','#999c28'];
const fmt=(x,n=3)=>x==null?'未取得':Number(x).toFixed(n), esc=s=>String(s).replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
document.querySelector('#results').innerHTML='<tr><th>条件</th><th>εW [分]</th><th>τ [秒]</th><th>D [km]</th><th>W [分]</th><th>T_program [秒]</th><th>状態</th></tr>'+DATA.rows.map(r=>`<tr class="${DATA.front.includes(r.trial_id)?'front':''}"><td>${esc(r.trial_id)}</td><td>${fmt(r.epsilon_W_min)}</td><td>${fmt(r.tau_s,0)}</td><td>${fmt(r.D_km,4)}</td><td>${fmt(r.W_min)}</td><td>${fmt(r.T_program_s)}</td><td>${esc(r.status)}</td></tr>`).join('');
const selector=document.querySelector('#trial');for(const r of DATA.rows.filter(x=>x.status==='COMPLETE')){const o=document.createElement('option');o.value=r.trial_id;o.textContent=r.trial_id;selector.append(o)}
const vsel=document.querySelector('#vehicle');for(let i=0;i<10;i++){let o=document.createElement('option');o.value='v'+i;o.textContent='車両v'+i;vsel.append(o)}
async function load(){try{const r=await fetch('trials/'+selector.value+'/routes.geojson');if(!r.ok)throw Error('HTTP '+r.status);features=(await r.json()).features;document.querySelector('#details').textContent=selector.value+'｜保存された経路・時刻';draw()}catch(e){document.querySelector('#details').textContent='読込HOLD: '+e.message+'。READMEのHTTP起動手順を使用してください。'}}
function draw(){const canvas=document.querySelector('#map'),ctx=canvas.getContext('2d'),chosen=features.filter(f=>(vsel.value==='all'||f.properties.vehicle_id===vsel.value)&&(document.querySelector('#trip').value==='all'||f.properties.trip_no==document.querySelector('#trip').value)),all=features.flatMap(f=>f.geometry?.coordinates||[]);ctx.clearRect(0,0,1300,480);if(!all.length)return;const xs=all.map(c=>c[0]),ys=all.map(c=>c[1]),lo=[Math.min(...xs),Math.min(...ys)],hi=[Math.max(...xs),Math.max(...ys)],scale=Math.min(1240/Math.max(.001,(hi[0]-lo[0])*.81),420/Math.max(.001,hi[1]-lo[1]));const xy=c=>[30+(c[0]-lo[0])*.81*scale,450-(c[1]-lo[1])*scale];for(const f of chosen){if(!f.geometry)continue;ctx.beginPath();f.geometry.coordinates.forEach((c,i)=>{const p=xy(c);i?ctx.lineTo(...p):ctx.moveTo(...p)});ctx.strokeStyle=palette[Number(f.properties.vehicle_id.slice(1))%10];ctx.lineWidth=2;ctx.setLineDash(f.properties.trip_no===2?[7,4]:[]);ctx.stroke()}ctx.setLineDash([]);const depot=xy(all[0]);ctx.fillStyle='#dd432c';ctx.beginPath();ctx.arc(...depot,6,0,Math.PI*2);ctx.fill();
let svg='<svg viewBox="0 0 1300 '+(60+chosen.length*28)+'" role="img" aria-label="保存時刻ガント">';for(let h=8;h<=20;h++){const x=100+(h-8)*95;svg+=`<text x="${x}" y="20" font-size="12">${h}:00</text>`}chosen.forEach((f,i)=>{const p=f.properties,y=42+i*28,X=t=>100+(t-28800)/3600*95;svg+=`<text x="2" y="${y+12}" font-size="12">${p.vehicle_id}-${p.trip_no} ${p.berth_id}</text><line x1="${X(p.ready_s)}" x2="${X(p.load_start_s)}" y1="${y+8}" y2="${y+8}" stroke="#d78a22" stroke-width="5"/><rect x="${X(p.load_start_s)}" y="${y}" width="${X(p.load_end_s)-X(p.load_start_s)}" height="16" fill="${palette[Number(p.vehicle_id.slice(1))%10]}"/><line x1="${X(p.departure_s)}" x2="${X(p.return_s)}" y1="${y+8}" y2="${y+8}" stroke="#9babb8" stroke-width="3"/><title>${p.vehicle_id}-${p.trip_no}: ready ${p.ready_s}, load ${p.load_start_s}–${p.load_end_s}, return ${p.return_s}, W ${p.waiting_s/60}分</title>`});document.querySelector('#gantt').innerHTML=svg+'</svg><p>橙：積込待機／色矩形：積込／灰線：出発から帰着。全て保存時刻。</p>'}
selector.onchange=load;vsel.onchange=draw;document.querySelector('#trip').onchange=draw;if(selector.options.length)load();
</script></html>'''
(ROOT / 'index.html').write_text(html.replace('__DATA__', payload))
(ROOT / 'VISUALIZATION_DATA.json').write_text(json.dumps({'rows': display, 'front': data['front_trial_ids']}, ensure_ascii=False) + '\n')
print('Figures and dashboard saved:', ROOT)
