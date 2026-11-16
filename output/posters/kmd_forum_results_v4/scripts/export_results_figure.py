"""Export the same fixed-cohort result as a standalone scientific plot."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

O=Path(__file__).resolve().parents[1]
R=O.parents[2]
f=FontProperties(fname=str(R/'output/slides/sato_revision_20261105/fonts/NotoSansJP-Regular.ttf'))
data=json.loads((O/'evidence/RESULT_FIGURE.json').read_text());rows=data['rows']
plt.rcParams.update({'pdf.fonttype':42,'svg.fonttype':'none','font.size':12,'axes.unicode_minus':False})
fig,ax=plt.subplots(figsize=(13.5,6.2))
y=np.arange(len(rows));h=.28
ax.barh(y-h/2,[r['classical'] for r in rows],height=h,facecolor='white',edgecolor='black',label='古典対照')
ax.barh(y+h/2,[r['qaoa'] for r in rows],height=h,facecolor='.75',edgecolor='black',label='QAOA候補')
for k,r in enumerate(rows):
    for key,dy in [('classical',-h/2),('qaoa',h/2)]:
        ax.text(r[key]+24,k+dy,f"{r[key]:,.3f}",va='center',fontproperties=f,fontsize=10)
    ax.text(1.15,k,f"+{r['delta']:,.3f} / {r['absolute']:,.3f}",va='center',fontproperties=f,fontsize=10,transform=ax.get_yaxis_transform(),clip_on=False)
ax.text(1.15,-.62,'平均差 / 平均絶対差［秒］',fontproperties=f,fontsize=10,transform=ax.get_yaxis_transform(),clip_on=False)
ax.set_yticks(y,[r['label']+f"  ({r['n']:,}比較)" for r in rows],fontproperties=f)
ax.set_xlim(0,3600);ax.set_xticks([0,1000,2000,3000,3600]);ax.invert_yaxis()
ax.set_xlabel('平均往復旅行時間 J［秒］（短いほど良い）',fontproperties=f)
ax.spines[['top','right','left']].set_visible(False)
ax.grid(axis='x',color='.88');ax.set_axisbelow(True)
ax.legend(prop=f,loc='lower right',frameon=False)
ax.set_title('同じ入力の古典対照とQAOA候補の比較',fontproperties=f,pad=23)
fig.text(.04,.035,'ΔJ＝QAOA−古典。正が悪化。460入力・8設定・各10抽出反復の保存集合の記述。全体行は8設定の混合平均。',fontproperties=f,fontsize=10)
fig.text(.04,.008,'出典：Step5 B_PLAN_GAPS_36800.csv。計算予算・初期解保持規則は未統一であり、速度優位や実配送効果は示さない。',fontproperties=f,fontsize=9)
fig.subplots_adjust(left=.25,right=.74,top=.83,bottom=.17)
for ext in ['pdf','svg','png']:
    fig.savefig(O/'figures'/f'04_classical_qaoa_comparison.{ext}',dpi=300)
plt.close(fig)
print('Standalone PDF / SVG / PNG exported.')
