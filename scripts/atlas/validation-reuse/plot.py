"""Standalone structural figure from measured receipts, outside timed paths."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[3];D=R/'docs/research'
r=json.loads((D/'atlas-validation-reuse-results.json').read_text(encoding='utf-8'))
rows=[x for x in r['cases'] if not x.get('boundary') and x['fanout']==1 and x['pattern']=='one-local']
fig,axes=plt.subplots(1,2,figsize=(10,3.7),layout='constrained')
for ax,key,title in zip(axes,['rowsChecked','objectReads'],['Semantic row checks avoided','Current integrity and receipt reads remain']):
    for mode,label,color in [('full','Full','#386994'),('incremental','Incremental','#cd7137')]:
        ax.plot([x['components'] for x in rows],[x[mode]['counter'][key] for x in rows],marker='o',label=label,color=color)
    ax.set_title(title,fontsize=11);ax.set_xlabel('Current components (64 records each)');ax.set_ylabel('Logical checks' if key=='rowsChecked' else 'Metadata objects read');ax.grid(alpha=.2);ax.legend(frameon=False)
fig.suptitle('Local update, fan-out one: structural work, not production throughput',fontsize=12)
path=D/'atlas-validation-reuse.svg';fig.savefig(path,metadata={'Date':None});path.write_text('\n'.join(line.rstrip() for line in path.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
fig.savefig(Path(r['rawFiles'][0]['path']).parent/'validation-reuse.png',dpi=130)
