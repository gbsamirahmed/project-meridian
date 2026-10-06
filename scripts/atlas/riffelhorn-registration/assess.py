"""Read-only native patch diagnostics, not a registration correction or accuracy benchmark."""
from pathlib import Path
import importlib.util,json,math,hashlib
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import reproject,Resampling
from rasterio.transform import from_origin
from pyproj import Transformer
from PIL import Image
def gaussian_filter(a,sigma):
 radius=math.ceil(4*sigma);x=np.arange(-radius,radius+1);kernel=np.exp(-x*x/(2*sigma*sigma));kernel/=kernel.sum()
 out=np.asarray(a,dtype=float)
 for axis in (0,1):
  pads=[(0,0),(0,0)];pads[axis]=(radius,radius);padded=np.pad(out,pads,mode='reflect')
  out=np.apply_along_axis(lambda row:np.convolve(row,kernel,mode='valid'),axis,padded)
 return out
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[3];DATA=ROOT.parent/'meridian-data'
PREFIX='riffelhorn-registration-epoch'
OUT=ROOT/'docs/research'
PLAN=json.loads(Path(__file__).with_name('plan.json').read_text(encoding='utf-8'))
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def module(p):
 s=importlib.util.spec_from_file_location('baseline',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
BASE=module(ROOT/'scripts/atlas/swissimage_baseline.py')
def pearson(a,b):
 a=np.asarray(a,dtype=float).ravel();b=np.asarray(b,dtype=float).ravel();a=a-a.mean();b=b-b.mean();den=np.linalg.norm(a)*np.linalg.norm(b)
 return float(np.dot(a,b)/den) if den>1e-15 else None
def search(image,terrain,halo,size,limit,step):
 # dx/dy are image sampling offsets relative to terrain, east/north positive.
 n=size;box=(slice(halo,halo+n),slice(halo,halo+n));t=terrain[box];rows=[]
 if halo<limit or image.shape[0]<halo+n+limit or image.shape[1]<halo+n+limit:raise ValueError('Insufficient fixed-support search halo')
 if not np.isfinite(image).all() or not np.isfinite(terrain).all():raise ValueError('Nonfinite diagnostic inputs')
 for dy in range(-limit,limit+1):
  for dx in range(-limit,limit+1):
   b=image[halo-dy:halo-dy+n,halo+dx:halo+dx+n];v=pearson(t,b)
   rows.append({'eastMetres':dx*step,'northMetres':dy*step,'score':v})
 usable=[r for r in rows if r['score'] is not None]
 if not usable:return {'zero':None,'best':None,'surface':rows,'ambiguous':True}
 best=max(usable,key=lambda r:r['score']);zero=next(r['score'] for r in rows if not r['eastMetres'] and not r['northMetres'])
 other=max((r['score'] for r in usable if abs(r['eastMetres']-best['eastMetres'])>=1 or abs(r['northMetres']-best['northMetres'])>=1),default=best['score'])
 return {'zero':zero,'best':best,'bestMinusZero':best['score']-zero,'bestMarginBeyond1m':best['score']-other,'atSearchBoundary':abs(best['eastMetres'])==limit*step or abs(best['northMetres'])==limit*step,'surface':rows,'notGeospatialShift':True}
def coupling(dh,angle):return dh*math.tan(math.radians(angle))
def grids(s):return {'crs':str(s.crs),'shape':list(s.shape),'transform':list(s.transform)[:6],'bounds':list(s.bounds),'areaOrPoint':s.tags().get('AREA_OR_POINT'),'nodata':s.nodata,'pixelCorner':list(s.transform*(0,0)),'firstCentre':list(s.transform*(.5,.5))}
def native_patch(centre,images,dtm):
 x,y,size=centre;h=PLAN['haloMetres'];b=[x-size/2-h,y-size/2-h,x+size/2+h,y+size/2+h];n=round((size+2*h)/.5)
 tr=from_origin(b[0],b[3],.5,.5);height=dtm.read(1,window=from_bounds(*b,dtm.transform))
 assert height.shape==(n,n) and np.isfinite(height).all() and (height!=-9999).all()
 image=next(s for s in images if s.bounds.left<=b[0] and s.bounds.right>=b[2] and s.bounds.bottom<=b[1] and s.bounds.top>=b[3])
 raw=image.read(window=from_bounds(*b,image.transform)).astype(float)
 assert raw.shape==(3,n*5,n*5)
 rgb=raw.reshape(3,n,5,n,5).mean(axis=(2,4)).transpose(1,2,0)/255
 luma=np.einsum('ijk,k->ij',rgb,[.2126,.7152,.0722]);luma=gaussian_filter(luma,2)
 gy,gx=np.gradient(luma,.5);edges=np.hypot(gx,gy)
 z=gaussian_filter(height.astype(float),2);zy,zx=np.gradient(z,.5)
 slope=np.degrees(np.arctan(np.hypot(zx,zy)));lap=np.abs(np.gradient(zx,.5,axis=1)+np.gradient(zy,.5,axis=0))
 return {'bounds':b,'transform':tr,'rgb':rgb,'height':height,'slope':slope,'edges':edges,'lap':lap,'imageAsset':image.name}
def coordinates(images,terrain,manifest,prepared):
 forward=Transformer.from_crs(2056,3857,always_xy=True);back=Transformer.from_crs(3857,2056,always_xy=True)
 errors=[];xyzerrors=[];fields=[];terrain_checks=[];sources=BASE.Sources(DATA,manifest['sources'])
 for name,(x,y,size) in PLAN['patches'].items():
  mx,my=forward.transform(x,y);xx,yy=back.transform(mx,my);errors.append(math.hypot(xx-x,yy-y))
  z=18;span=BASE.WORLD/2**z;tx=math.floor((mx+BASE.WORLD/2)/span);ty=math.floor((BASE.WORLD/2-my)/span)
  tr=BASE.tile_transform(z,tx,ty);col,row=(~tr)*(mx,my)
  px,py=tr*(math.floor(col)+.5,math.floor(row)+.5)
  # Independent global XYZ centre equation, not raster inverse roundtrip only.
  step=BASE.WORLD/(2**z*512);ix=-BASE.WORLD/2+(tx*512+math.floor(col)+.5)*step;iy=BASE.WORLD/2-(ty*512+math.floor(row)+.5)*step
  xyzerrors.append(math.hypot(px-ix,py-iy));a=sources.finest(z,tx,ty);f=prepared/f'fields/{z}/{tx}/{ty}.npz';stored=np.load(f)['rgba']
  fields.append({'patch':name,'tile':[z,tx,ty],'sha256':digest(f),'maxAbsoluteFieldDifference':float(np.max(np.abs(a-stored)))})
  # Independent pixel-centred native bilinear samples of retained z18 Terrarium.
  tp=DATA/f'derived/atlas/riffelhorn/riffelhorn-swiss-support-v1/tiles/{z}/{tx}/{ty}.png'
  codes=np.asarray(Image.open(tp),dtype=float);values=codes[:,:,0]*256+codes[:,:,1]+codes[:,:,2]/256-32768
  indices=np.arange(32,225,24);cc,rr=np.meshgrid(indices,indices);step256=span/256
  ex=-BASE.WORLD/2+(tx*256+cc+.5)*step256;no=BASE.WORLD/2-(ty*256+rr+.5)*step256;se,sn=back.transform(ex,no)
  pp=(se-terrain.transform.c)/.5-.5;qq=(terrain.transform.f-sn)/.5-.5;pc=np.floor(pp).astype(int);pr=np.floor(qq).astype(int)
  xmin=int(pc.min());ymin=int(pr.min());w=int(pc.max()-xmin+2);h=int(pr.max()-ymin+2)
  window=terrain.read(1,window=rasterio.windows.Window(xmin,ymin,w,h)).astype(float)
  fx=pp-pc;fy=qq-pr;pc-=xmin;pr-=ymin
  ref=(window[pr,pc]*(1-fx)+window[pr,pc+1]*fx)*(1-fy)+(window[pr+1,pc]*(1-fx)+window[pr+1,pc+1]*fx)*fy
  delta=values[rr,cc]-ref
  terrain_checks.append({'patch':name,'tile':[z,tx,ty],'samples':delta.size,'maxAbsoluteHeightDifferenceMetres':float(np.max(np.abs(delta))),'rmsHeightDifferenceMetres':float(np.sqrt(np.mean(delta**2))),'notHorizontalRegistrationAccuracy':True})

 sources.close()
 # Independent continuous coordinate ramps through GDAL area preparation.
 x,y,_=PLAN['patches']['ordinary'];sx,sy=forward.transform(x,y);dst=from_origin(sx-20,sy+20,1,1);st=from_origin(x-25,y+25,.1,.1)
 yy,xx=np.mgrid[:500,:500];ramp=np.stack([((xx+.5)*.1-25),25-(yy+.5)*.1]).astype('float64');out=np.empty((2,40,40))
 reproject(ramp,out,src_transform=st,src_crs=2056,dst_transform=dst,dst_crs=3857,resampling=Resampling.average,num_threads=1)
 yy,xx=np.mgrid[:40,:40];mx=dst.c+(xx+.5)*dst.a;my=dst.f+(yy+.5)*dst.e;nx,ny=back.transform(mx,my);err=np.hypot(out[0]-(nx-x),out[1]-(ny-y))
 return {'sourceGrids':[grids(s) for s in images],'terrainGrid':grids(terrain),'horizontalOperation':forward.description,'operationStatedAccuracyMetres':forward.accuracy,'terrainZ18NativeBilinearChecks':terrain_checks,'verticalTransformationPerformed':False,'maxCRSRoundtripMetres':max(errors),'maxIndependentXYZCentreErrorMercatorMetres':max(xyzerrors),'coordinateRampMaxNativeMetres':float(err.max()),'coordinateRampMedianNativeMetres':float(np.median(err)),'coordinateRampIsAveragedFieldNotSurveyControl':True,'nativeCellCentreDifferenceMetres':[.2,-.2],'nativeCellEdgesAlign':True,'nativeLocalTerrainGrids':local_native_grids(),'z18FieldRegeneration':fields}
def local_native_grids():
 source=load(ROOT/'docs/atlas/riffelhorn-support-product.json')['source'];rows=[]
 for asset in source['assets']:
  if any(tile in asset['href'] for tile in ['2624-1091','2624-1092','2625-1091','2625-1092']):
   path=DATA/asset['href'].replace('${MERIDIAN_DATA_ROOT}/','')
   with rasterio.open(path) as ds:rows.append({'asset':path.name,**grids(ds)})
 return rows
def run():
 image_meta=load(ROOT/'docs/atlas/swissimage-source-derived-baseline.json');terrain_meta=load(ROOT/'docs/atlas/riffelhorn-support-product.json')
 prepared=DATA/'derived/atlas/riffelhorn/riffelhorn-swissimage-baseline-v1';tmroot=DATA/'derived/atlas/riffelhorn/riffelhorn-swiss-support-v1'
 manifest=load(prepared/'manifest.json');tmanifest=load(tmroot/'manifest.json');verified=[]
 docsroot=DATA/'sources/atlas/riffelhorn/swisstopo-2021-2024/metadata/official-documents'
 for file,sha in [('swissimage-specification.pdf','3cfce137b3cfc54ae29eba54c8f9b6fd053cfc7915f11dc090c169d31f53b435'),('swissalti3d-release-2024-2.pdf','cec9d46967be920d467fd22aafe042ca2846809a63cd175b2ae7a099a5cc1167')]:
  assert digest(docsroot/file)==sha;verified.append({'role':'retained-document','path':(docsroot/file).relative_to(DATA).as_posix(),'sha256':sha})
 assert digest(prepared/'manifest.json')=='3c8b50fb9d7721b678abc46b9450495b417ccafff15d4ee8a67d9d6a3fee4934'
 assert manifest['recipeSha256']=='d917612512380cb6940c103fe679d3af9acc0390a5a0681deb6e4fdda2667cf7'
 assert digest(BASE.__file__)==manifest['recipeSha256']
 assert digest(tmroot/'manifest.json')=='30413b6698c1e75e27fd169f61925d8d60044fa14f444fb072b652c54816e106'
 assert digest(tmroot/'source-mosaic.vrt')=='8b097d62be84e110cdf8efd695f63d685a9069fcad98aae91660b7fb42e17998'
 # Hash validation before any correspondence diagnostics. Every retained source / payload stays read-only.
 for r in image_meta['source']['assets']:
  p=DATA/r['path'];assert digest(p)==r['sha256'];verified.append({'role':'source-image',**r})
 for r in terrain_meta['source']['assets']:
  rel=r['href'].replace('${MERIDIAN_DATA_ROOT}/','');p=DATA/rel;assert digest(p)==r['sha256'];verified.append({'role':'source-terrain','path':rel,'sha256':r['sha256'],'bytes':p.stat().st_size})
 for role,root,m in [('prepared-image',prepared,manifest),('prepared-terrain',tmroot,tmanifest)]:
  for f in m['files']:
   assert digest(root/f['path'])==f['sha256'] and (root/f['path']).stat().st_size==f['bytes']
  verified.append({'role':role,'manifestSha256':digest(root/'manifest.json'),'files':len(m['files']),'bytes':sum(f['bytes'] for f in m['files'])})
 images=[rasterio.open(DATA/r['path']) for r in manifest['sources']];dtm=rasterio.open(tmroot/'source-mosaic.vrt')
 audit=coordinates(images,dtm,manifest,prepared);patches={};arrays={}
 for name,centre in PLAN['patches'].items():
  a=native_patch(centre,images,dtm);arrays[name]=a;h=round(PLAN['haloMetres']/.5);n=round(centre[2]/.5);core=(slice(h,h+n),slice(h,h+n));results={}
  for label,t in [('slope',a['slope']),('break-of-slope',a['lap'])]:
   full=search(a['edges'],t,h,n,10,.5);results[label]={'whole':full}
   for quadrant,dy,dx in [('NW',0,0),('NE',0,n//2),('SW',n//2,0),('SE',n//2,n//2)]:
    # Fixed quadrant inside same patch; pass translated array origins to general search.
    tt=t[dy:,dx:];ii=a['edges'][dy:,dx:];results[label][quadrant]=search(ii,tt,h,n//2,10,.5)
  patches[name]={'centreEPSG2056':centre[:2],'sizeMetres':centre[2],'actualReadBoundsEPSG2056':a['bounds'],'cells':n*n,'sourceImageAsset':Path(a['imageAsset']).name,'meanEncodedLuminance':float(np.mean(np.einsum('ijk,k->ij',a['rgb'][core],[.2126,.7152,.0722]))),'slopeDegreesP05MedianP95':np.percentile(a['slope'][core],[5,50,95]).tolist(),'proxies':results}
 for s in images:s.close()
 dtm.close()
 result={'assessment':PLAN['proof'],'methodSha256':digest(__file__),'planSha256':digest(Path(__file__).with_name('plan.json')),'inputVerification':verified,'coordinateAudit':audit,'nativeTerrainVrtSha256':digest(tmroot/'source-mosaic.vrt'),'terrainSourceRevision':terrain_meta['source']['revision'],'terrainProductRevision':terrain_meta['product']['revision'],'imageryProductIdentity':manifest['identity'],'patches':patches,'heightHorizontalCouplingHypothetical':[{'heightDifferenceMetres':dh,'offNadirDegrees':ang,'horizontalMetres':coupling(dh,ang)} for dh in [.3,1,5] for ang in [10,20,30]],'noTrueLocalShiftEstimated':True,'noWarpOrCorrection':True,'pixelEpochsAndOriginalOrthoRevisionUnknown':True,'software':{'python':__import__('sys').version.split()[0],'numpy':np.__version__,'rasterio':rasterio.__version__,'gdal':rasterio.__gdal_version__,'pyproj':__import__('pyproj').__version__},'readOnlyMetadataSha256':{p:digest(ROOT/p) for p in ['docs/atlas/riffelhorn-support-product.json','docs/atlas/swissimage-source-derived-baseline.json','docs/atlas/riffelhorn-observation-support.json','docs/atlas/riffelhorn-data-catalog.json']}}
 # Compact search surfaces stay in figure; retain quantitative optima / ambiguity in JSON.
 figure(arrays,patches)
 for p in patches.values():
  for pair in p['proxies'].values():
   for region in pair.values():region.pop('surface')
 (OUT/(PREFIX+'-results.json')).write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps({'coordinateAudit':{k:v for k,v in audit.items() if k not in ['sourceGrids','terrainGrid']},'patches':{k:{pair:{reg:v['best'] for reg,v in rows.items()} for pair,rows in p['proxies'].items()} for k,p in patches.items()}}))
def figure(arrays,patches):
 fig,axs=plt.subplots(4,3,figsize=(10,11),layout='constrained')
 for row,(name,a) in enumerate(arrays.items()):
  n=round(PLAN['patches'][name][2]/.5);h=round(PLAN['haloMetres']/.5);sl=(slice(h,h+n),slice(h,h+n));size=PLAN['patches'][name][2];ext=[-size/2,size/2,-size/2,size/2]
  for col in (0,1):axs[row,col].imshow(a['rgb'][sl],extent=ext,origin='upper',interpolation='nearest')
  xs=np.arange(n)*.5+.25-size/2;ys=size/2-np.arange(n)*.5-.25
  levels=np.arange(math.floor(a['height'][sl].min()/5)*5,a['height'][sl].max()+5,5)
  axs[row,1].contour(xs,ys,a['height'][sl],levels=levels,colors='#ffdf00',linewidths=.4,alpha=.8)
  axs[row,2].imshow(a['lap'][sl],extent=ext,cmap='gray',vmin=0,vmax=.3,interpolation='nearest')
  axs[row,0].set_ylabel(name+'; north up\nnorth offset (m)')
  for col,title in enumerate(['source RGB, fixed [0,255]','same RGB + DTM 5m contours','DTM absolute Laplacian [0,0.3]']):
   axs[row,col].set_title(title,fontsize=9);axs[row,col].set_xlabel('east offset (m)')
 fig.suptitle('Native LV95 correspondence diagnostics; no shifts or corrections; RGB is not geometry')
 fig.savefig(OUT/(PREFIX+'-patches.png'),dpi=100,metadata={'Software':'Meridian registration assessment v2'});plt.close(fig)
 fig,axs=plt.subplots(4,2,figsize=(7,10),layout='constrained')
 for row,(name,p) in enumerate(patches.items()):
  for col,(pair,r) in enumerate(p['proxies'].items()):
   vals=np.array([v['score'] for v in r['whole']['surface']]).reshape(21,21)
   im=axs[row,col].imshow(vals,origin='lower',extent=[-5.25,5.25,-5.25,5.25],vmin=-.25,vmax=.5,cmap='coolwarm');axs[row,col].plot(0,0,'ko',ms=3)
   b=r['whole']['best'];axs[row,col].plot(b['eastMetres'],b['northMetres'],'kx');axs[row,col].set_title(name+' / '+pair,fontsize=9);axs[row,col].set_xlabel('image sampling offset east (m)');axs[row,col].set_ylabel('north (m)')
 fig.colorbar(im,ax=axs,shrink=.5,label='edge/terrain correlation; not registration accuracy');fig.suptitle('Fixed-support translation diagnostics; maxima are not accepted physical shifts',fontsize=11)
 fig.savefig(OUT/(PREFIX+'-search.png'),dpi=100,metadata={'Software':'Meridian registration assessment v2'});plt.close(fig)
if __name__=='__main__':run()
