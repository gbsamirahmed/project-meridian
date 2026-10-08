"""Observed local comparison; sampled curves are not fitted complexity proofs."""
from pathlib import Path
import json,matplotlib
matplotlib.use('Agg');matplotlib.rcParams['svg.hashsalt']='atlas-component-membership-v1'
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[3];new=json.loads((R/'docs/research/atlas-component-membership-results.json').read_text(encoding='utf-8'));old=json.loads((R/'docs/research/atlas-generation-scaling-results.json').read_text(encoding='utf-8'))
fig,axes=plt.subplots(1,3,figsize=(12,3.7),layout='constrained')
for values,label,color in [(old['rows'],'e88 request reuse','#b35806'),(new['rows'],'component membership','#2166ac')]:
 rows=sorted([r for r in values if (r.get('query')=='Q05' and r.get('variant')=='request-reuse') or r.get('mode')=='Q05'],key=lambda r:r['depth'])
 mb=[(r['structural']['reads']['generations']['bytes'] if 'structural' in r else sum(r['reads'][k]['bytes'] for k in ['membership','publications','components']))/1e6 for r in rows]
 axes[0].plot([r['depth'] for r in rows],mb,marker='o',label=label,color=color)
 axes[1].plot([r['depth'] for r in rows],[r['warmMilliseconds']['median']/1000 for r in rows],marker='o',label=label,color=color)
for label,values,color in [('Whole snapshots + locators',[(r['depth'],r['metadataBytes']+r['depth']*46860) for r in old['fixtures']],'#b35806'),('Shared components + publications + registry',[(r['depth'],sum(r['footprint'][k]['bytes'] for k in ['components','publications','membership'])) for r in new['fixtures']],'#2166ac')]:
 axes[2].plot([x[0] for x in values],[x[1]/1e6 for x in values],marker='o',label=label,color=color)
for ax,title,y in zip(axes,['Current Q05 requested metadata','Current Q05 observed latency','Persistent metadata (no payloads)'],['Requested MB','Warm median seconds','Stored MB']):
 ax.set(title=title,xlabel='Retained publications',ylabel=y);ax.set_xticks([7,28,112]);ax.grid(alpha=.25);ax.legend(fontsize=7)
fig.suptitle('Atlas component-membership proof — fixed retained Tryfan state')
svg=R/'docs/research/atlas-component-membership.svg';fig.savefig(svg,metadata={'Date':None});svg.write_text('\n'.join(s.rstrip() for s in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n');fig.savefig('C:/Users/gbsam/Documents/Codex/atlas-component-membership-v1/figure.png',dpi=140)
