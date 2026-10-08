"""Three-point observed curves, not fitted asymptotic models."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['svg.hashsalt']='atlas-generation-scaling-v1'
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[3]
v=json.loads((R/'docs/research/atlas-generation-scaling-results.json').read_text())
fig,axes=plt.subplots(1,3,figsize=(12,3.7),layout='constrained')
colors={'Q05':'#2166ac','Q18':'#b35806'}
for q in ['Q05','Q18']:
 for variant in ['accepted','request-reuse']:
  rows=sorted((r for r in v['rows'] if r['query']==q and r['variant']==variant),key=lambda r:r['depth'])
  style='-' if variant=='accepted' else '--';label=q+' '+variant
  axes[0].plot([r['depth'] for r in rows],[r['structural']['reads']['generations']['bytes']/1e6 for r in rows],style,marker='o',color=colors[q],label=label)
  axes[1].plot([r['depth'] for r in rows],[r['warmMilliseconds']['median']/1000 for r in rows],style,marker='o',color=colors[q],label=label)
for variant,color in [('accepted','#2166ac'),('request-reuse','#b35806')]:
 rows=sorted((r for r in v['historical'] if r['variant']==variant),key=lambda r:r['depth'])
 axes[2].plot([r['depth'] for r in rows],[r['startupMilliseconds']/1000 for r in rows],marker='o',color=color,label=variant)
for ax,title,y in zip(axes,['Current generation metadata reads','Current query: 20 warm requests','Historical pin: single fresh process'],['Requested generation MB','Median elapsed seconds','Startup + historical pin seconds']):
 ax.set(title=title,xlabel='Current ancestry depth',ylabel=y);ax.set_xticks([7,28,112]);ax.grid(alpha=.25);ax.legend(fontsize=7)
fig.suptitle('Atlas retained-generation scaling — fixed Tryfan scientific state',fontsize=12)
fig.savefig(R/'docs/research/atlas-generation-scaling.svg',metadata={'Date':None})
svg=R/'docs/research/atlas-generation-scaling.svg'
svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
fig.savefig(Path(v['runtime'].get('stateRoot','C:/Users/gbsam/Documents/Codex/atlas-generation-scaling-v1'))/'scaling-figure.png',dpi=140)
