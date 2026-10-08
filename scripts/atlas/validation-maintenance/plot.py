from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
r=Path(__file__).resolve().parents[3];results=json.loads((r/'docs/research/atlas-validation-maintenance-results.json').read_text(encoding='utf-8'))
fig,axes=plt.subplots(1,3,figsize=(15,4.8),layout='constrained')
for seq in results['sequences']:
 if seq['case']['id'] not in ['high-small','high-medium','high-large','high-long']:continue
 raws=[json.loads(Path(x['path']).read_text(encoding='utf-8')) for x in results['rawFiles'] if Path(x['path']).name.startswith(seq['case']['id']+'-')]
 curves=[x['summary']['curve'] for x in raws];xs=[x['publication'] for x in curves[0]];ys=[[c[i]['savingMs']/1000 for c in curves] for i in range(len(xs))]
 import statistics
 axes[0].plot(xs,[statistics.median(y) for y in ys],label=seq['case']['id'])
 axes[0].fill_between(xs,[min(y) for y in ys],[max(y) for y in ys],alpha=.08)
axes[0].axhline(0,color='black',linewidth=.8);axes[0].set(title='Cumulative saving, including maintenance',xlabel='Retained publications',ylabel='Full minus incremental seconds');axes[0].legend(fontsize=8)
seqs=[x for x in results['sequences'] if x['case']['id'] in ['unchanged','high-medium','moderate','low']];names=[x['case']['id'] for x in seqs]
axes[1].bar(names,[x['observations'][0]['full']['rowsChecked'] for x in seqs],label='Full',alpha=.7)
axes[1].bar(names,[x['observations'][0]['incremental']['rowsChecked'] for x in seqs],label='Incremental',alpha=.7);axes[1].set(title='Semantic work avoided is real',ylabel='Cumulative row checks');axes[1].legend(fontsize=8)
seqs=[x for x in results['sequences'] if x['case']['id'] in ['unchanged','high-medium','high-long','local-rule']];names=[x['case']['id'] for x in seqs]
local=[x['footprints'][0]['groups']['validation-local-receipt/v1']['bytes']/1e6 for x in seqs];root=[x['footprints'][0]['groups']['maintenance-trust-root/v1']['bytes']/1e6 for x in seqs]
axes[2].bar(names,local,label='Local receipts');axes[2].bar(names,root,bottom=local,label='Trust directories');axes[2].set(title='Retained receipt versus directory bytes',ylabel='Decimal MB');axes[2].legend(fontsize=8)
for a in axes:a.grid(axis='y',alpha=.2);a.tick_params(axis='x',labelrotation=15)
fig.suptitle('Isolated metadata experiment: three paired repeats; warm OS cache, no SLA',fontsize=12)
p=r/'docs/research/atlas-validation-maintenance.svg';fig.savefig(p,metadata={'Date':None});p.write_text('\n'.join(x.rstrip() for x in p.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
