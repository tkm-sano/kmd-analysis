"""Publication figures; saved road vertices and saved event times only."""
import json,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt,font_manager
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT/'data/dashboard.json').read_text())
font=Path('/home/takuma/.local/share/fonts/NotoSansJP-Regular.ttf')
if font.exists():font_manager.fontManager.addfont(str(font));plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
plt.rcParams.update({'font.size':10,'axes.titlesize':12,'axes.labelsize':10,'svg.fonttype':'none','pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
COLORS=['#245cb4','#b65b24','#138576','#8b52af','#d34767','#66712d','#1794af','#91563f','#7168c5','#4b718a'];MC={'B':'#245cb4','C':'#138576','D':'#8b52af'}
CAPTIONS={}


def save(fig,name,caption):
    for ext in ['png','svg','pdf']:fig.savefig(ROOT/'figures'/f'{name}.{ext}',dpi=300,bbox_inches='tight',facecolor='white')
    plt.close(fig);CAPTIONS[name]=caption


def base(ax):
    main={'motorway','trunk','primary','secondary','tertiary','motorway_link','trunk_link','primary_link','secondary_link','tertiary_link'}
    segments=[w['coordinates'] for w in DATA['roads'] if w['highway'] in main]
    ax.add_collection(LineCollection(segments,colors='#d8dfe7',linewidths=.35,zorder=0))
    boundary=[]
    for f in DATA['boundary']['features']:
        polys=f['geometry']['coordinates'] if f['geometry']['type']=='MultiPolygon' else [f['geometry']['coordinates']]
        boundary.extend(ring for poly in polys for ring in poly)
    ax.add_collection(LineCollection(boundary,colors='#718198',linewidths=.65,linestyles='--',zorder=1))
    p=DATA['scenarios']['S3']['points'];x=[v['lon'] for v in p];y=[v['lat'] for v in p]
    ax.set_xlim(min(x)-.006,max(x)+.006);ax.set_ylim(min(y)-.006,max(y)+.006);ax.set_aspect(1/math.cos(math.radians(35.58)))
    ax.set_xlabel('経度［°E / WGS84］');ax.set_ylabel('緯度［°N / WGS84］');ax.tick_params(labelsize=8)
    depot=p[0];ax.scatter([depot['lon']],[depot['lat']],marker='*',s=120,c='#dd4d26',edgecolors='white',linewidth=.6,zorder=10)
    ax.annotate('京浜TT',(depot['lon'],depot['lat']),xytext=(5,6),textcoords='offset points',fontsize=8,color='#a33b23',zorder=11)


def main():
    fig,axes=plt.subplots(1,3,figsize=(14,5.8),constrained_layout=True)
    for ax,s in zip(axes,['S1','S2','S3']):
        base(ax);pts=DATA['scenarios'][s]['points'][1:];ax.scatter([p['lon'] for p in pts],[p['lat'] for p in pts],s=2.5,c='#245cb4',alpha=.6,zorder=3)
        ax.set_title(f"{s}：{len(pts):,}配送先\n共通有向道路OD / 保存OSMの主要車道")
    save(fig,'01_S1_S3_demand_roads','凍結された研究需要の全地点。背景はhash固定OSMの主要車道地物、破線は国土数値情報N03の大田区境界（EPSG:6668→4326）。実配送需要・実績ではない。各パネルの範囲は共通。© OpenStreetMap contributors / ODbL。')
    fig,axes=plt.subplots(1,3,figsize=(15,6.3),constrained_layout=True)
    for ax,m in zip(axes,['B','C','D']):
        base(ax);p=DATA['plans'][m]
        for t in p['trips']:
            if t['geometry'] is None:raise ValueError('Unvalidated route cannot enter thesis figure')
            a=np.array(t['geometry']);ax.plot(a[:,0],a[:,1],color=COLORS[int(t['vehicle_id'][1:])],lw=.85,ls='-' if t['trip_no']==1 else (0,(4,2)),alpha=.9,zorder=4)
        ax.set_title(f"{m}：D={p['D_km']:.4f} km / W={p['W_min']:.2f} 分")
    handles=[Line2D([0],[0],color=c,lw=2,label=f'v{i}') for i,c in enumerate(COLORS)]
    handles+=[Line2D([0],[0],color='#344860',lw=1.5,label='第1便'),Line2D([0],[0],color='#344860',lw=1.5,ls='--',label='第2便')]
    fig.legend(handles=handles,loc='outside lower center',ncol=12,fontsize=8)
    save(fig,'02_S1_BCD_road_routes','S1・W≤422.45分の保存最終計画。経路は保存OSRM node列と同版PBF座標・snap点から復元し、全3051区間でOD距離/時間・形状長を照合した。直線ODや合成経路ではない。B/Dは便の道路経路集合が一致するが車両割当・時刻が異なる。© OpenStreetMap contributors / ODbL。')
    fig,axes=plt.subplots(3,1,figsize=(13,7),sharex=True,constrained_layout=True)
    for ax,m in zip(axes,['B','C','D']):
        p=DATA['plans'][m]
        for t in p['trips']:
            row=int(t['berth_id'].replace('b',''));a=t['load_start_s']/3600;b=t['load_end_s']/3600
            ax.barh(row,b-a,left=a,height=.55,color=COLORS[int(t['vehicle_id'][1:])]);ax.text((a+b)/2,row,f"{t['vehicle_id']}-{t['trip_no']}",ha='center',va='center',fontsize=7,color='white')
        ax.set_yticks([0,1],['バース1','バース2']);ax.set_ylim(-.6,1.6);ax.invert_yaxis();ax.set_title(f"{m}：積込待機合計 W={p['W_min']:.2f}分",loc='left');ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
    axes[-1].set_xlim(8,20);axes[-1].set_xticks(range(8,21));axes[-1].xaxis.set_major_formatter(FuncFormatter(lambda v,_:f'{int(v):02}:00'));axes[-1].set_xlabel('時刻［JST・研究上の1運行日］')
    save(fig,'03_S1_BCD_berth_gantt','保存された積込開始・終了をそのまま描画。各矩形は30分のバース占有、色は車両、ラベルは車両ID-便番号。バース重複0。積込待機Wは準備完了から開始までの総和であり、占有時間を含まない。研究シミュレーションで実事業者の時刻ではない。')
    fig,axes=plt.subplots(1,3,figsize=(12,4.3),constrained_layout=True)
    for ax,key,title,unit in zip(axes,['D_km','W_min','T_program_s'],['総走行距離 D','積込待機 W','計画作成 T_program'],['km','分','秒']):
        vals=[DATA['plans'][m][key] for m in ['B','C','D']];ax.bar(['B','C','D'],vals,color=[MC[m] for m in ['B','C','D']],width=.57)
        ax.set_ylim(0,max(vals)*1.18);ax.set_ylabel(unit);ax.set_title(title);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
        for i,v in enumerate(vals):ax.text(i,v+max(vals)*.025,f'{v:.2f}',ha='center',fontsize=11)
    save(fig,'04_S1_BCD_metrics','共通入力・同一OD・W≤422.45分の各手法1観測。丸め前のD/Wを独立再計算し保存結果と一致。T_programは入力読込開始から共通検査終了までの保存wall秒。OD事前生成・追加の第二再計算・結果出力は含まない。標準偏差・信頼区間や性能分布を表さない。')
    fig,axes=plt.subplots(3,3,figsize=(13,10),constrained_layout=True)
    for row,s in enumerate(['S1','S2','S3']):
        stats=DATA['stats'][s]
        for col,key,label in [(0,'distance_km','道路距離［km］'),(1,'duration_min','移動時間［分］'),(2,'signed_asymmetry_km','方向別距離差［km］')]:
            hist=stats[key]['hist'];e=np.array(hist['edges']);axes[row,col].bar(e[:-1],hist['counts'],width=np.diff(e),align='edge',color=['#245cb4','#138576','#8b52af'][col]);axes[row,col].set_title(f'{s} · {label}');axes[row,col].set_ylabel('OD組数');axes[row,col].ticklabel_format(axis='y',style='sci',scilimits=(0,0))
    save(fig,'05_all_OD_quality_distributions','S1〜S3の全非対角OD組を用いた距離・時間分布。方向差は保存ID順i<jのd(i,j)−d(j,i)で各無向対1組。非対称性を異常として除外していない。Route方式のみを使用。')
    (ROOT/'figures/CAPTIONS.json').write_text(json.dumps(CAPTIONS,ensure_ascii=False,indent=2)+'\n')
    print('Saved',len(CAPTIONS),'figure sets (PNG/SVG/PDF)',flush=True)


if __name__=='__main__':main()
