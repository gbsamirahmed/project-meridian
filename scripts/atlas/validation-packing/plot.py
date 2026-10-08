from pathlib import Path
import json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['svg.hashsalt']='atlas-validation-packing-v1'
R=Path(__file__).resolve().parents[3];r=json.loads((R/'docs/research/atlas-validation-packing-results.json').read_text(encoding='utf-8'));seq={x['case']['id']:x for x in r['sequences']}
ids=['unchanged','high-small','high-medium','high-large','high-long','scattered','moderate','low'];modes=['full','individual','packed','shared'];colors=['#455a64','#b34b3d','#327bb5','#228c72']
fig,ax=plt.subplots(1,2,figsize=(13,5.3));x=np.arange(len(ids));w=.19
for j,m in enumerate(modes):
 y=np.array([seq[i]['timing'][m]['totalMs']['median']/1000 for i in ids]);low=np.array([seq[i]['timing'][m]['totalMs']['min']/1000 for i in ids]);high=np.array([seq[i]['timing'][m]['totalMs']['max']/1000 for i in ids]);ax[0].bar(x+(j-1.5)*w,y,w,color=colors[j],label=m,yerr=np.array([y-low,high-y]),capsize=2,error_kw={'elinewidth':.6})
ax[0].set_xticks(x,ids,rotation=40,ha='right');ax[0].set_ylabel('Cumulative validation + maintenance (seconds)');ax[0].set_title('Independent stores; three-repeat medians');ax[0].legend(frameon=False)
for j,m in enumerate(modes):
 raw=json.loads(Path(next(x['path'] for x in r['rawFiles'] if Path(x['path']).name=='high-long-0.json')).read_text(encoding='utf-8'));v=raw['summary'][m]['curve'];ax[1].plot(range(1,len(v)+1),np.array(v)/1000,color=colors[j],label=m)
ax[1].set_xlabel('Retained publication number');ax[1].set_ylabel('Cumulative cost (seconds)');ax[1].set_title('112-publication trace, repeat 1 (not an SLA)');ax[1].legend(frameon=False)
for a in ax:a.spines[['top','right']].set_visible(False);a.grid(axis='y',alpha=.2)
fig.suptitle('Atlas packed validation evidence: receipt lifecycle comparison',fontweight='bold');fig.tight_layout();out=R/'docs/research/atlas-validation-packing.svg';fig.savefig(out,metadata={'Date':None});out.write_text('\n'.join(x.rstrip() for x in out.read_text(encoding='utf-8').splitlines()).rstrip()+'\n',encoding='utf-8',newline='\n');fig.savefig(Path(r['rawFiles'][0]['path']).parent/'chart-review.png',dpi=120)
