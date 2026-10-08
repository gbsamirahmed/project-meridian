"""Static scientific figure from committed observations, not new benchmarks."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
R=Path(__file__).resolve().parents[3]
r=json.loads((R/'docs/research/atlas-component-granularity-results.json').read_text())
strategies=['coarse','moderate','fine','selective'];labels=['Whole','64 / spatial','One record','Internal / key']
colors=['#4c566a','#007c91','#b74f31','#6f42a5']
plt.rcParams.update({'font.size':9,'svg.hashsalt':'atlas-granularity-v1'})
fig,axes=plt.subplots(1,3,figsize=(13,4.5))
width=.2;x=np.arange(3)
for i,(s,c) in enumerate(zip(strategies,colors)):
 values=[]
 for f,q in [('terrain','narrow'),('inventory','narrow'),('inventory','feature')]:
  a=next(a for a in r['rows'] if a['family']==f and a['population']==2048 and a['strategy']==s and a['query']==q);values.append(a['counter']['metadataBytes']/1000)
 axes[0].bar(x+(i-1.5)*width,values,width,color=c,label=labels[i])
 writes=[a['construction']['newBytes']/1000 for pattern in ['local','scattered','broad'] for a in r['updates'] if a['family']=='terrain' and a['strategy']==s and a['pattern']==pattern]
 axes[1].bar(x+(i-1.5)*width,writes,width,color=c)
 a=next(a for a in r['rows'] if a['family']=='terrain' and a['population']==2048 and a['strategy']==s and a['query']=='broad')
 axes[2].bar(i,a['counter']['objectReads'],color=c)
axes[0].set_xticks(x,['Terrain / place','Inventory / place','Inventory / ID']);axes[0].set_ylabel('Requested metadata (decimal KB)');axes[0].set_title('Narrow access includes membership and qualifier')
axes[1].set_xticks(x,['2 local keys','32 spread keys','512 local keys']);axes[1].set_ylabel('New component / internal page metadata (KB)');axes[1].set_title('Scoped write cost depends on locality')
axes[2].set_xticks(range(4),labels,rotation=15);axes[2].set_yscale('log');axes[2].set_ylabel('Immutable metadata objects read (log scale)');axes[2].set_title('Broad terrain access: all 2,048 records needed')
for ax in axes:ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
fig.legend(loc='lower center',ncol=4,frameon=False,bbox_to_anchor=(.5,.04));fig.suptitle('Atlas synthetic metadata granularity: 2,048 records, verified selected paths',fontsize=12)
fig.text(.5,.005,'No payload reads. Synthetic unit supports; native qualification retained. All staged updates still fully validate 2,048 records.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.14,1,.92))
fig.savefig(R/'docs/research/atlas-component-granularity.svg',metadata={'Date':None})
fig.savefig(Path(r['rawSetupReceipt']['path']).parent/'granularity-preview.png',dpi=130)

svg=R/'docs/research/atlas-component-granularity.svg'
svg.write_bytes(b'\n'.join(line.rstrip() for line in svg.read_bytes().splitlines())+b'\n')
