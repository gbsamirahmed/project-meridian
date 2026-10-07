"""Read-only native RGB diagnostics. No appearance correction or physical SNR."""
import hashlib, importlib.util, json, math
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window
from pyproj import Transformer
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT.parent/'meridian-data'
HERE=Path(__file__).parent
PLAN=json.loads((HERE/'assessment-plan.json').read_text())
PREFIX='riffelhorn-dark-source-signal'
OUT=ROOT/'docs/research'
PRODUCT=DATA/'derived/atlas/riffelhorn/riffelhorn-swissimage-baseline-v1'
spec=importlib.util.spec_from_file_location('baseline',ROOT/'scripts/atlas/swissimage_baseline.py')
BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)
BINS=PLAN['binsDN']; WEIGHTS=np.array(PLAN['intensityWeights'])

def digest(p):return BASE.digest(p)
def intensity(rgb):return np.einsum('...c,c->...',rgb.astype('float64'),WEIGHTS)
def binmask(a,lo,hi):return (a>=lo)&(a<hi)
def quant(a):
 a=np.asarray(a)
 return None if not a.size else np.percentile(a,[5,50,95]).tolist()
def corr(a,b):
 a=np.asarray(a).ravel();b=np.asarray(b).ravel();a=a-a.mean();b=b-b.mean()
 d=np.sqrt(np.dot(a,a)*np.dot(b,b))
 return None if d<=1e-20 else float(np.dot(a,b)/d)
def blocks(a,n):
 h,w=a.shape
 if h%n or w%n:raise ValueError('native patch must exactly partition')
 return a.reshape(h//n,n,w//n,n).transpose(0,2,1,3).reshape(-1,n,n)
def aggregate(a,f):
 n=a.shape[-1]
 if n%f:raise ValueError('aggregation must exactly partition block')
 return a.reshape(len(a),n//f,f,n//f,f).mean(axis=(2,4))
def spatial(a):
 """Block-demeaned adjacency cosine and squared gradient orientation coherence."""
 z=a-a.mean(axis=(1,2),keepdims=True)
 x=np.concatenate([z[:,:,:-1].reshape(len(a),-1),z[:,:-1,:].reshape(len(a),-1)],axis=1)
 y=np.concatenate([z[:,:,1:].reshape(len(a),-1),z[:,1:,:].reshape(len(a),-1)],axis=1)
 d=np.sqrt((x*x).sum(axis=1)*(y*y).sum(axis=1))
 ac=np.divide((x*y).sum(axis=1),d,out=np.full(len(a),np.nan),where=d>1e-20)
 gx=a[:,:-1,1:]-a[:,:-1,:-1];gy=a[:,1:,:-1]-a[:,:-1,:-1]
 xx=(gx*gx).sum(axis=(1,2));yy=(gy*gy).sum(axis=(1,2));xy=(gx*gy).sum(axis=(1,2));tr=xx+yy
 c=np.divide((xx-yy)**2+4*xy**2,tr**2,out=np.full(len(a),np.nan),where=tr>1e-20)
 return ac,c,np.sqrt(tr/(2*gx.shape[1]*gx.shape[2]))
def nullable_quant(a):return quant(np.asarray(a)[np.isfinite(a)])
def shuffled(a,seed):
 rng=np.random.default_rng(seed)
 return rng.permuted(a.reshape(len(a),-1),axis=1).reshape(a.shape)
def phase_audit(y,row,col):
 result={}
 for name,lo,hi in [('dark',0,20),('bright',80,256)]:
  result[name]={}
  for axis,offset in [(0,row),(1,col)]:
   left=y[:-1,:] if axis==0 else y[:,:-1];right=y[1:,:] if axis==0 else y[:,1:]
   valid=binmask(left,lo,hi)&binmask(right,lo,hi);delta=np.abs(right-left)
   coords=(np.arange(y.shape[axis]-1)+offset+1)%8
   ph=coords[:,None] if axis==0 else coords[None,:]
   result[name]['rows' if axis==0 else 'columns']=[{'phase':k,'pairs':int((valid&(ph==k)).sum()),'meanAbsoluteDN':float(delta[valid&(ph==k)].mean()) if (valid&(ph==k)).any() else None} for k in range(8)]
 return result

def patch(ds,definition):
 x,y,size=definition;n=round(size/.1)
 c=round((x-size/2-ds.bounds.left)/.1);r=round((ds.bounds.top-y-size/2)/.1)
 win=Window(c,r,n,n)
 rgb=ds.read(window=win).transpose(1,2,0)
 if rgb.shape!=(n,n,3) or not (ds.dataset_mask(window=win)>0).all():raise ValueError('incomplete native support')
 return rgb,r,c

def statistics(rgb,row,col):
 y=intensity(rgb);n=round(PLAN['blockMetres']/.1);bb=blocks(y,n);means=bb.mean(axis=(1,2));aa=aggregate(bb,5)
 ac,coh,grad=spatial(aa);sa,sc,_=spatial(shuffled(aa,PLAN['shuffleSeed']))
 out={'nativeCells':int(y.size),'intensityP05P50P95':quant(y),'allRGBZeroCells':int((rgb==0).all(axis=2).sum()),'anyChannelZeroCells':int((rgb==0).any(axis=2).sum()),'anyChannel255Cells':int((rgb==255).any(axis=2).sum()),'blocks5m':len(bb),'nativeStrata':{},'blockStrata':{},'JPEGPhaseAudit':phase_audit(y,row,col)}
 for lo,hi in zip(BINS[:-1],BINS[1:]):
  key=f'{lo}-{hi}';m=binmask(y,lo,hi);rr=rgb[m];bm=binmask(means,lo,hi)
  out['nativeStrata'][key]={'cells':int(m.sum()),'channelOccupiedLevels':[int(len(np.unique(rr[:,c]))) for c in range(3)],'channelP05P50P95':[quant(rr[:,c]) for c in range(3)],'channelZeros':[int((rr[:,c]==0).sum()) for c in range(3)],'channel255':[int((rr[:,c]==255).sum()) for c in range(3)],'RGCorrelation':corr(rr[:,0],rr[:,1]) if len(rr)>1 else None,'GBCorrelation':corr(rr[:,1],rr[:,2]) if len(rr)>1 else None}
  out['blockStrata'][key]={'blocks':int(bm.sum()),'notIndependentSamples':True,'contrastRMS_DN':{str(f*.1):quant(aggregate(bb,f)[bm].std(axis=(1,2))) for f in PLAN['aggregationFactors']},'adjacency05m':nullable_quant(ac[bm]),'shuffleAdjacency05m':nullable_quant(sa[bm]),'coherence05m':nullable_quant(coh[bm]),'shuffleCoherence05m':nullable_quant(sc[bm]),'gradientRMS05m_DN':quant(grad[bm]),'adjacency1m':nullable_quant(spatial(aggregate(bb,10))[0][bm])}
 return out

def prepared(sources,patches):
 m=json.loads((PRODUCT/'manifest.json').read_text());assert m['recipeSha256']==digest(ROOT/'scripts/atlas/swissimage_baseline.py')
 for f in m['files']:assert digest(PRODUCT/f['path'])==f['sha256'] and (PRODUCT/f['path']).stat().st_size==f['bytes']
 trans=Transformer.from_crs(3857,2056,always_xy=True);src=BASE.Sources(DATA,sources);rows=[];counts={k:0 for k in patches};strata={k:{f'{lo}-{hi}':[] for lo,hi in zip(BINS[:-1],BINS[1:])} for k in patches}
 try:
  for x,y in m['levels'][-1]['tiles']:
   tr=BASE.tile_transform(18,x,y);xx=tr.c+(np.arange(512)+.5)*tr.a;yy=tr.f+(np.arange(512)+.5)*tr.e
   xx,yy=np.meshgrid(xx,yy);ee,nn=trans.transform(xx,yy)
   masks={k:(ee>=cx-side/2)&(ee<cx+side/2)&(nn>=cy-side/2)&(nn<cy+side/2) for k,(cx,cy,side) in patches.items()}
   if not any(v.any() for v in masks.values()):continue
   field=np.load(PRODUCT/f'fields/18/{x}/{y}.npz')['rgba']; fresh=src.finest(18,x,y)
   img=np.asarray(Image.open(PRODUCT/f'tiles/18/{x}/{y}.png'))
   assert np.array_equal(field,fresh) and np.array_equal(img,BASE.rgba(field))
   alpha=field[3];lin=np.divide(field[:3],alpha[None],out=np.zeros_like(field[:3]),where=alpha[None]>0)
   continuous=255*np.where(lin<=.0031308,12.92*lin,1.055*lin**(1/2.4)-.055)
   yy0=intensity(continuous.transpose(1,2,0));yd=intensity(img[:,:,:3]);err=np.abs(yd-yy0)
   for k,mask in masks.items():
    assert (alpha[mask]>.999999).all();counts[k]+=int(mask.sum())
    for lo,hi in zip(BINS[:-1],BINS[1:]):
     hit=mask&binmask(yy0,lo,hi)
     if hit.any():strata[k][f'{lo}-{hi}'].append([int(hit.sum()),float(err[hit].sum()),float(err[hit].max()),int((img[:,:,:3][hit]==0).all(axis=1).sum())])
   rows.append({'z':18,'x':x,'y':y,'fieldExact':True,'PNGExactDeclaredEncoding':True})
 finally:src.close()
 summary={}
 for k,st in strata.items():
  summary[k]={}
  for key,values in st.items():
   if values:
    total=sum(v[0] for v in values);summary[k][key]={'samples':total,'meanIntensityRoundingErrorDN':sum(v[1] for v in values)/total,'maxIntensityRoundingErrorDN':max(v[2] for v in values),'encodedAllRGBZero':sum(v[3] for v in values)}
   else:summary[k][key]={'samples':0}
 return {'identity':m['identity'],'revision':m['revision'],'manifestSha256':digest(PRODUCT/'manifest.json'),'recipeSha256':m['recipeSha256'],'payloadsVerified':len(m['files']),'tilesRegenerated':rows,'patchSamples':counts,'encodingStrata':summary,'noNewLossyCompression':True,'comparisonIsPreparationFidelityNotNativePointwiseEquality':True}

def figures(images,stats):
 fig,ax=plt.subplots(4,3,figsize=(9,10));fig.suptitle('Native source / fixed diagnostic lift / fixed central 10 m inset')
 for i,k in enumerate(PLAN['patches']):
  rgb=images[k]
  ax[i,0].imshow(rgb,interpolation='nearest');ax[i,0].set_title(k+' original')
  ax[i,1].imshow(np.sqrt(rgb.astype(float)/255),interpolation='nearest');ax[i,1].set_title('sqrt(DN/255), display only')
  n=round(PLAN['figureInsetMetres']/.1);h,w=rgb.shape[:2];inset=rgb[h//2-n//2:h//2+n//2,w//2-n//2:w//2+n//2]
  ax[i,2].imshow(np.sqrt(inset.astype(float)/255),interpolation='nearest');ax[i,2].set_title('same lift; 10 m map plane')
  for a in ax[i]:a.set_xticks([]);a.set_yticks([])
 fig.tight_layout();fig.savefig(OUT/f'{PREFIX}-views.png',dpi=90);plt.close(fig)
 fig,ax=plt.subplots(2,2,figsize=(10,7));keys=list(PLAN['patches'])
 for k in keys:
  st=stats[k]['blockStrata'];xs=[];contrast=[];coarse=[];ac=[];sh=[]
  for lo,hi in zip(BINS[:-1],BINS[1:]):
   b=st[f'{lo}-{hi}']
   if b['blocks']:
    xs.append((lo+hi)/2);contrast.append(b['contrastRMS_DN']['0.1'][1]);coarse.append(b['contrastRMS_DN']['1.0'][1]);ac.append(b['adjacency05m'][1] if b['adjacency05m'] else np.nan);sh.append(b['shuffleAdjacency05m'][1] if b['shuffleAdjacency05m'] else np.nan)
  ax[0,0].plot(xs,contrast,'o-',label=k);ax[0,1].plot(xs,coarse,'o-',label=k);ax[1,0].plot(xs,ac,'o-',label=k);ax[1,1].plot(xs,sh,'o-',label=k)
 for a in ax[1]:a.set_ylim(-.2,.9)
 for a,title in zip(ax.ravel(),['Native within-block RMS DN','1 m aggregated within-block RMS DN','0.5 m demeaned adjacency','Histogram-preserving shuffle adjacency']):
  a.set_title(title);a.set_xlabel('5 m block-mean intensity stratum midpoint DN');a.grid(alpha=.2);a.legend(fontsize=8)
 fig.tight_layout();fig.savefig(OUT/f'{PREFIX}-support.png',dpi=110);plt.close(fig)

def run():
 sources=BASE.verify_sources(ROOT,DATA);images={};stats={};metadata=[]
 for s in sources:
  with rasterio.open(DATA/s['path']) as ds:metadata.append({'tile':s['tile'],'dtype':list(ds.dtypes),'crs':ds.crs.to_epsg(),'res':list(ds.res),'imageStructure':ds.tags(ns='IMAGE_STRUCTURE'),'blocks':ds.block_shapes,'AREA_OR_POINT':ds.tags().get('AREA_OR_POINT')})
 for k,p in PLAN['patches'].items():
  matches=[s for s in sources if s['bounds'][0]<=p[0]-p[2]/2 and s['bounds'][2]>=p[0]+p[2]/2 and s['bounds'][1]<=p[1]-p[2]/2 and s['bounds'][3]>=p[1]+p[2]/2]
  if len(matches)!=1:raise ValueError('frozen patch needs one retained tile')
  with rasterio.open(DATA/matches[0]['path']) as ds:rgb,r,c=patch(ds,p)
  images[k]=rgb;stats[k]=statistics(rgb,r,c);stats[k]['sourceTile']=matches[0]['tile'];stats[k]['sourceWindow']={'row':r,'column':c,'size':len(rgb)}
 result={'assessment':PLAN['assessment'],'planSha256':digest(HERE/'assessment-plan.json'),'methodSha256':digest(Path(__file__)),'sources':sources,'encoding':metadata,'sourceBytes':sum(s['bytes'] for s in sources),'patches':stats,'prepared':prepared(sources,PLAN['patches']),'noCorrection':True,'noFitting':True,'noiseModel':'unavailable; no physical SNR','software':{'numpy':np.__version__,'rasterio':rasterio.__version__,'GDAL':rasterio.__gdal_version__},'retainedMetadataSha256':{p:digest(ROOT/p) for p in ['docs/atlas/riffelhorn-data-catalog.json','docs/atlas/swissimage-source-derived-baseline.json','scripts/atlas/riffelhorn-registration/plan.json','docs/research/riffelhorn-registration-epoch-results.json']}}
 (OUT/f'{PREFIX}-results.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
 figures(images,stats)
 print(json.dumps({k:{'cells':v['nativeCells'],'quantiles':v['intensityP05P50P95'],'zeros':v['allRGBZeroCells'],'blocks':v['blocks5m']} for k,v in stats.items()}))
if __name__=='__main__':run()
