"""Small scientific diagnostics/contact sheet from accepted captures, no image processing product."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('data');a=p.parse_args();repo=Path(__file__).resolve().parents[2];summary=json.loads((repo/'docs/atlas/information-display.json').read_text());r=json.loads((Path(a.data)/summary['fullDiagnostic']['path']).read_text());out=Path(a.data)/'experiments/atlas/information-display-v1/diagnostics';out.mkdir(parents=True,exist_ok=True)
fig,axs=plt.subplots(1,3,figsize=(13,4),layout='constrained')
for mode,name in [('aws','AWS: 0.125 m/CSS px'),('tryfan-regional','Welsh: 0.5 m/CSS px'),('riffelhorn-regional','Swiss: 0.5 m/CSS px')]:
 rows=[s for s in r['captures'] if s['mode']==mode and s['dpr'] in [1,2,3] and s['id'] in ['tryfan-0.125m','tryfan-0.5m','riffelhorn-0.5m']]
 rows.sort(key=lambda s:s['dpr']);x=[s['dpr'] for s in rows];y=[np.median([p['sampling']['encodedDEM']['framebufferPixelsPerSamplePrincipal'][0] for p in s['points'] if 'sampling' in p]) for s in rows];axs[0].plot(x,y,'o-',label=name)
axs[0].set(xlabel='Requested DPR',ylabel='Median major framebuffer pixels / DEM sample',title='Extra raster pixels; same encoded DEM');axs[0].legend(fontsize=7)
for axis,label,color in [(0,'Major','tab:blue'),(1,'Minor','tab:orange')]:
 rows=[s for s in r['captures'] if s['mode']=='riffelhorn-regional' and s['dpr']==1 and s['requestedMapMetresPerCssPixel']==8]
 rows.sort(key=lambda s:s['camera']['pitch'])
 for s in rows:
  values=[p['physical']['surfacePrincipalMetresPerCssPixel'][axis] for p in s['points'] if 'physical' in p];pitch=s['camera']['pitch'];axs[1].plot([pitch]*len(values),values,'o',color=color,alpha=.65,label=label if pitch==0 else None)
axs[1].set(xlabel='Pitch degrees',ylabel='Local physical surface metres / CSS pixel',title='Nine probes: anisotropy and perspective');axs[1].legend()
rows=[s for s in r['captures'] if s['mode']=='riffelhorn-appearance' and s['id']=='riffelhorn-0.125m' and s['appearance']=='regional'];rows.sort(key=lambda s:s['dpr']);x=[s['dpr'] for s in rows]
for metric,name in [('distributedOrthophotoGrid','Distributed 0.1 m grid'),('nominalOrthophotoInformation','Nominal 0.25 m statement'),('imageryDelivery','Prepared delivery pixels'),('drapedRTT','Draping RTT grid')]:
 y=[np.median([p['sampling'][metric]['framebufferPixelsPerSamplePrincipal'][0] for p in s['points'] if metric in p.get('sampling',{})]) for s in rows];axs[2].plot(x,y,'o-',label=name)
axs[2].set(xlabel='Requested DPR',ylabel='Median major framebuffer pixels / sample',title='Different sampling statements');axs[2].legend(fontsize=7)
fig.savefig(out/'sampling.png',dpi=150);plt.close(fig)
# Small fixed CSS-centre crops: native screenshot density then reduced solely for this index.
chosen=[s for s in r['captures'] if (s['mode']=='aws' and s['id']=='tryfan-0.125m') or (s['mode']=='riffelhorn-appearance' and s['id']=='riffelhorn-0.125m')]
cols=3;rows=(len(chosen)+cols-1)//cols;sheet=Image.new('RGB',(cols*480,rows*330),'white');draw=ImageDraw.Draw(sheet)
chosen.sort(key=lambda s:(s['mode'],s['appearance'],s['dpr']))
for i,s in enumerate(chosen):
 img=Image.open(Path(a.data)/s['captureDirectory']/s['filename']).convert('RGB');d=s['dpr'];crop=img.crop((480*d,290*d,960*d,590*d));crop.thumbnail((480,300));x=i%cols*480;y=i//cols*330;sheet.paste(crop,(x,y+30));draw.text((x+4,y+7),f"{s['mode']} / {s['appearance']} / DPR {d}",fill='black')
sheet.save(out/'capture-index.png');print(out)
