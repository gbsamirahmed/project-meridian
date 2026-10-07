"""Controlled display transfers over immutable retained RGB8. No corrected product."""
from pathlib import Path
import importlib.util,json,hashlib
import numpy as np
import rasterio
from PIL import Image
from pyproj import Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[3];DATA=ROOT.parent/'meridian-data';HERE=Path(__file__).parent
PREFIX='riffelhorn-display-transfer';OUT=ROOT/'docs/research'
PLAN=json.loads((HERE/'protocol.json').read_text(encoding='utf-8'))
spec=importlib.util.spec_from_file_location('prior',ROOT/'scripts/atlas/riffelhorn-dark-source/assess.py');PRIOR=importlib.util.module_from_spec(spec);spec.loader.exec_module(PRIOR)
BASE=PRIOR.BASE;BINS=PLAN['binsDN'];PRODUCT=PRIOR.PRODUCT

def sha(p):return BASE.digest(p)
def smooth(u):
 u=np.clip(u,0,1);return u*u*(3-2*u)
def curve(i,a):return i+a*smooth((i-5)/15)*(1-smooth((i-20)/60))
def transfer(rgb,a):
 rgb=np.asarray(rgb,dtype='float64');i=PRIOR.intensity(rgb)
 gain=np.divide(curve(i,a),i,out=np.ones_like(i),where=i>0)
 peak=rgb.max(axis=-1);headroom=np.divide(255,peak,out=np.ones_like(peak),where=peak>0)
 gain=np.minimum(np.minimum(gain,1.5),headroom)
 raw=rgb*gain[...,None]
 return np.rint(raw).astype('uint8'),raw,gain

def hsv(rgb):
 rgb=np.asarray(rgb,dtype='float64');mx=rgb.max(axis=-1);mn=rgb.min(axis=-1);delta=mx-mn
 sat=np.divide(delta,mx,out=np.zeros_like(mx),where=mx>0);h=np.zeros_like(mx)
 nz=delta>0
 for k in range(3):
  hit=nz&(rgb[...,k]==mx)
  if k==0:hh=np.divide(rgb[...,1]-rgb[...,2],delta,out=np.zeros_like(mx),where=nz)%6
  elif k==1:hh=np.divide(rgb[...,2]-rgb[...,0],delta,out=np.zeros_like(mx),where=nz)+2
  else:hh=np.divide(rgb[...,0]-rgb[...,1],delta,out=np.zeros_like(mx),where=nz)+4
  h[hit]=hh[hit]*60
 return h,sat

def q(a):return PRIOR.quant(a)
def blockstats(rgb,assignment):
 y=PRIOR.intensity(rgb);bb=PRIOR.blocks(y,50);a05=PRIOR.aggregate(bb,5);ac,_,grad=PRIOR.spatial(a05)
 return {f'{lo}-{hi}':{'blocks':int(PRIOR.binmask(assignment,lo,hi).sum()),'contrast':{str(f*.1):q(PRIOR.aggregate(bb,f)[PRIOR.binmask(assignment,lo,hi)].std(axis=(1,2))) for f in PLAN['aggregationFactors']},'gradient05m':q(grad[PRIOR.binmask(assignment,lo,hi)]),'adjacency05m':PRIOR.nullable_quant(ac[PRIOR.binmask(assignment,lo,hi)])} for lo,hi in zip(BINS[:-1],BINS[1:])}

def phase_gain(source,out,row,col):
 # Both endpoints selected by SOURCE intensity; never change population after transfer.
 si=PRIOR.intensity(source);oi=PRIOR.intensity(out);res={}
 for axis,offset in [(0,row),(1,col)]:
  sl=si[:-1,:] if axis==0 else si[:,:-1];sr=si[1:,:] if axis==0 else si[:,1:]
  ol=oi[:-1,:] if axis==0 else oi[:,:-1];orr=oi[1:,:] if axis==0 else oi[:,1:]
  mask=(sl<20)&(sr<20);phase=(np.arange(si.shape[axis]-1)+offset+1)%8
  ph=phase[:,None] if axis==0 else phase[None,:];items=[]
  for k in range(8):
   hit=mask&(ph==k);n=int(hit.sum());b=float(np.abs(sr-sl)[hit].mean()) if n else None;c=float(np.abs(orr-ol)[hit].mean()) if n else None
   items.append({'phase':k,'pairs':n,'baselineMeanAbsoluteDN':b,'displayMeanAbsoluteDN':c,'gain':c/b if b else None})
  res['rows' if axis==0 else 'columns']=items
 return res

def pixelstats(rgb,out,raw,gain):
 i=PRIOR.intensity(rgb);o=PRIOR.intensity(out);h,s=hsv(rgb);hh,ss=hsv(out);colour=(rgb.max(axis=-1).astype(float)-rgb.min(axis=-1))>=4
 dh=np.abs(hh-h);dh=np.minimum(dh,360-dh);r=raw.sum(axis=-1);b=rgb.sum(axis=-1).astype(float)
 ratios=np.divide(raw,r[...,None],out=np.zeros_like(raw),where=r[...,None]>0);old=np.divide(rgb,b[...,None],out=np.zeros_like(raw),where=b[...,None]>0)
 return {'outputRGB8Sha256':hashlib.sha256(out.tobytes()).hexdigest(),'sourceIntensityQuantiles':q(i),'displayIntensityQuantiles':q(o),'allRGBZero':int((out==0).all(axis=-1).sum()),'anyChannel255':int((out==255).any(axis=-1).sum()),'rawRatioMaxError':float(np.abs(ratios-old).max()),'channelOrderInversions':sum(int(((rgb[...,j].astype(float)-rgb[...,k])*(out[...,j].astype(float)-out[...,k])<0).sum()) for j,k in [(0,1),(0,2),(1,2)]),'hueErrorDegreesP05P50P95':q(dh[colour]),'saturationAbsErrorP05P50P95':q(np.abs(ss-s)[colour]),'strata':{f'{lo}-{hi}':{'samples':int(PRIOR.binmask(i,lo,hi).sum()),'gainP05P50P95':q(gain[PRIOR.binmask(i,lo,hi)]),'intensityDeltaP05P50P95':q((o-i)[PRIOR.binmask(i,lo,hi)]),'changedPixels':int(((out!=rgb).any(axis=-1)&PRIOR.binmask(i,lo,hi)).sum())} for lo,hi in zip(BINS[:-1],BINS[1:])},'weakIdentity':bool(np.array_equal(out[i<=5],rgb[i<=5])),'brightIdentity':bool(np.array_equal(out[i>=80],rgb[i>=80]))}

def prepared(sources):
 m=json.loads((PRODUCT/'manifest.json').read_text(encoding='utf-8'))
 for f in m['files']:assert sha(PRODUCT/f['path'])==f['sha256']
 t=Transformer.from_crs(3857,2056,always_xy=True);gather={k:[] for k in PLAN['patches']};tiles=[]
 for x,y in m['levels'][-1]['tiles']:
  tr=BASE.tile_transform(18,x,y);xx,yy=np.meshgrid(tr.c+(np.arange(512)+.5)*tr.a,tr.f+(np.arange(512)+.5)*tr.e);ee,nn=t.transform(xx,yy)
  masks={k:(ee>=cx-side/2)&(ee<cx+side/2)&(nn>=cy-side/2)&(nn<cy+side/2) for k,(cx,cy,side) in PLAN['patches'].items()}
  if not any(v.any() for v in masks.values()):continue
  rgba=np.asarray(Image.open(PRODUCT/f'tiles/18/{x}/{y}.png'));assert (rgba[:,:,3][np.logical_or.reduce(list(masks.values()))]==255).all()
  tiles.append([18,x,y])
  for k,mask in masks.items():gather[k].append(rgba[:,:,:3][mask])
 res={}
 for k,arrs in gather.items():
  rgb=np.concatenate(arrs);res[k]={'samples':len(rgb),'candidates':{}}
  for name,c in PLAN['candidates'].items():
   out,raw,gain=transfer(rgb,c['amplitudeDN']);res[k]['candidates'][name]=pixelstats(rgb,out,raw,gain)
 return {'identity':m['identity'],'manifestSha256':sha(PRODUCT/'manifest.json'),'payloadsVerified':len(m['files']),'tiles':tiles,'patches':res,'alphaUnchanged':True,'operatorAfterPNGDecode':True}

def figures(images,results):
 for inset in [False,True]:
  fig,ax=plt.subplots(4,3,figsize=(9,10));fig.suptitle('Display only: identity / bounded toe4 / bounded toe8'+(' - fixed central10m' if inset else ' - inherited full patches'))
  for row,k in enumerate(PLAN['patches']):
   rgb=images[k]
   if inset:
    h,w=rgb.shape[:2];rgb=rgb[h//2-50:h//2+50,w//2-50:w//2+50]
   for col,name in enumerate(['identity']+PLAN['candidateOrder']):
    out=rgb if col==0 else transfer(rgb,PLAN['candidates'][name]['amplitudeDN'])[0]
    ax[row,col].imshow(out,interpolation='nearest',vmin=0,vmax=255);ax[row,col].set_title(k+' / '+name,fontsize=10);ax[row,col].set_xticks([]);ax[row,col].set_yticks([])
  fig.tight_layout();fig.savefig(OUT/(f'{PREFIX}-'+('insets' if inset else 'views')+'.png'),dpi=90);plt.close(fig)
 fig,ax=plt.subplots(1,2,figsize=(9,3));i=np.linspace(0,100,1001)
 for name,c in PLAN['candidates'].items():ax[0].plot(i,curve(i,c['amplitudeDN'])-i,label=name)
 ax[0].set(xlabel='encoded intensity DN',ylabel='continuous lift DN');ax[0].legend();ax[0].grid(alpha=.2)
 ramp=np.arange(81,dtype='uint8');greys=np.repeat(ramp[:,None],3,axis=1)
 for n,name in enumerate(['identity']+PLAN['candidateOrder']):
  img=greys if n==0 else transfer(greys,PLAN['candidates'][name]['amplitudeDN'])[0];ax[1].imshow(np.tile(img[None],(10,1,1)),extent=[0,81,n,n+1],interpolation='nearest',aspect='auto')
 ax[1].set(ylim=(0,3),yticks=[.5,1.5,2.5],yticklabels=['identity','toe4','toe8'],xlabel='input neutral code');fig.tight_layout();fig.savefig(OUT/f'{PREFIX}-curves.png',dpi=110);plt.close(fig)

def run():
 oldpath=OUT/'riffelhorn-dark-source-signal-results.json';old=json.loads(oldpath.read_text(encoding='utf-8'));sources=BASE.verify_sources(ROOT,DATA);assert sources==old['sources']
 images={};res={}
 for k,definition in PLAN['patches'].items():
  tile=old['patches'][k]['sourceTile'];asset=next(s for s in sources if s['tile']==tile)
  with rasterio.open(DATA/asset['path']) as ds:rgb,row,col=PRIOR.patch(ds,definition)
  images[k]=rgb;assert PRIOR.quant(PRIOR.intensity(rgb))==old['patches'][k]['intensityP05P50P95']
  assignment=PRIOR.blocks(PRIOR.intensity(rgb),50).mean(axis=(1,2));baseline=blockstats(rgb,assignment);res[k]={'sourceTile':tile,'sourceWindow':old['patches'][k]['sourceWindow'],'baseline':baseline,'candidates':{}}
  for name,c in PLAN['candidates'].items():
   out,raw,gain=transfer(rgb,c['amplitudeDN']);ps=pixelstats(rgb,out,raw,gain);bs=blockstats(out,assignment);pg=phase_gain(rgb,out,row,col)
   ratios={bin:{'gradient05mMedianGain':bs[bin]['gradient05m'][1]/v['gradient05m'][1] if v['gradient05m'] and v['gradient05m'][1]>0 else None,'contrastMedianGains':{scale:bs[bin]['contrast'][scale][1]/b[1] if b and b[1]>0 else None for scale,b in v['contrast'].items()}} for bin,v in baseline.items()}
   res[k]['candidates'][name]={'pixels':ps,'blocks':bs,'ratios':ratios,'codecPhaseGain':pg}
 checks={}
 for name,c in PLAN['candidates'].items():
  grey=np.repeat(np.arange(256,dtype='uint8')[:,None],3,axis=1);out,_,_=transfer(grey,c['amplitudeDN']);step=int(np.diff(out[:,0].astype(int)).max());dense=np.linspace(0,255,100001)
  checks[name]={'curveMonotonic':bool((np.diff(curve(dense,c['amplitudeDN']))>=0).all()),'greyMaxStep':step,'greyOccupiedOutputLevels':int(len(np.unique(out[:,0]))),'greyMergedAdjacentPairs':int((np.diff(out[:,0].astype(int))==0).sum()),'darkNumericalPass':all(res[k]['candidates'][name]['ratios']['10-20']['gradient05mMedianGain']>=1.15 and res[k]['candidates'][name]['ratios']['10-20']['contrastMedianGains']['1.0']>=1.1 for k in ['steep','dark-context']),'codecNumericalPass':all(res[k]['candidates'][name]['codecPhaseGain'][axis][0]['gain']<=1.35 and res[k]['candidates'][name]['ratios']['10-20']['contrastMedianGains']['1.0']/res[k]['candidates'][name]['ratios']['10-20']['contrastMedianGains']['0.1']>=.9 for k in ['steep','dark-context'] for axis in ['rows','columns']),'preservationPass':all(v['candidates'][name]['pixels']['weakIdentity'] and v['candidates'][name]['pixels']['brightIdentity'] and v['candidates'][name]['pixels']['anyChannel255']==0 and v['candidates'][name]['pixels']['allRGBZero']==0 and v['candidates'][name]['pixels']['rawRatioMaxError']<=1e-12 and v['candidates'][name]['pixels']['hueErrorDegreesP05P50P95'][2]<=5 and v['candidates'][name]['pixels']['saturationAbsErrorP05P50P95'][2]<=.05 and v['candidates'][name]['pixels']['strata']['5-10']['gainP05P50P95'][2]<=1.25 for v in res.values()),'visualAssessmentRequired':True}
 result={'experiment':PLAN['experiment'],'protocolSha256':sha(HERE/'protocol.json'),'methodSha256':sha(Path(__file__)),'priorMetricsSha256':sha(oldpath),'sources':sources,'patches':res,'prepared':prepared(sources),'numericalCriteria':checks,'noSourceOrProductWrites':True,'displayOnly':True,'software':{'numpy':np.__version__,'rasterio':rasterio.__version__,'GDAL':rasterio.__gdal_version__},'productionDisplayCodeSha256':{p:sha(ROOT/p) for p in ['src/atlas/map/satelliteLayer.ts','src/atlas/map/satelliteProvider.ts']}}
 (OUT/f'{PREFIX}-results.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8',newline='\n');figures(images,res);print(json.dumps(checks))
if __name__=='__main__':run()
