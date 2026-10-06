"""Offline analysis of the frozen derivative-only depiction control."""
import argparse,hashlib,json,math,platform
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,__version__ as pillow_version
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
WORLD=40075016.6855785

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def kernel(sigma):
 x=np.arange(-6,7);w=np.exp(-.5*(x/sigma)**2);return w/w.sum()
def blur(a,sigma):
 w=kernel(sigma);r=6;v=np.pad(a,((0,0),(r,r),(0,0)),mode='edge');v=sum(weight*v[:,i:i+a.shape[1]] for i,weight in enumerate(w));v=np.pad(v,((r,r),(0,0),(0,0)),mode='edge');return sum(weight*v[i:i+a.shape[0]] for i,weight in enumerate(w))
def derivative_patch(input,scale):
 h=np.array(input['heights']);z=input['overscaledZ'];dim=input['dim'];c=input['canonical']
 north=lambda y:math.degrees(math.atan(math.sinh(math.pi*(1-2*y/2**c['z']))))
 lat=north(c['y']+.5);spacing=WORLD*math.cos(math.radians(lat))/(dim*2**c['z']);sigma=scale/spacing
 dx=h[:-2,2:]+2*h[1:-1,2:]+h[2:,2:]-h[:-2,:-2]-2*h[1:-1,:-2]-h[2:,:-2]
 dy=h[2:,:-2]+2*h[2:,1:-1]+h[2:,2:]-h[:-2,:-2]-2*h[:-2,1:-1]-h[:-2,2:]
 factor=.4 if z<2 else .35 if z<4.5 else .3;gain=(z-15)*factor if z<15 else 0
 d=np.stack([dx,dy],axis=-1)*dim/2**(gain+28.2562-z)
 encoded=np.rint(np.clip(d/8+128/255,0,1)*255)/255
 a=(encoded-128/255)*8/math.cos(math.radians(lat));b=(blur(encoded,sigma)-128/255)*8/math.cos(math.radians(lat))
 # Central 64x64 avoids numerical patch padding; not a fixed physical population across levels.
 a=a[15:79,15:79];b=b[15:79,15:79]
 mag=lambda v:np.linalg.norm(v,axis=-1)
 rms=lambda v:float(np.sqrt(np.mean(mag(v)**2)))
 return {'level':z,'canonicalLevel':c['z'],'tileCentreLatitude':lat,'deliverySpacingMetres':spacing,'sigmaDerivativeTexels':sigma,'windowPhysicalSideMetres':64*spacing,'stockSlopeMedianP95':np.quantile(mag(a),[.5,.95]).tolist(),'filteredSlopeMedianP95':np.quantile(mag(b),[.5,.95]).tolist(),'stockVectorRms':rms(a),'filteredVectorRms':rms(b),'withheldDerivativeRms':rms(a-b),'kernelEdgeWeight':float(kernel(sigma)[0])}
def sheet(out,name,rows):
 w,h=560,350;im=Image.new('RGB',(w*2,h*len(rows)),'white');draw=ImageDraw.Draw(im)
 for j,row in enumerate(rows):
  for i,(label,file) in enumerate(row):
   a=Image.open(file).convert('RGB');a.thumbnail((w,h-25));im.paste(a,(i*w,j*h+25));draw.text((i*w+4,j*h+4),label,fill='black')
 p=out/(name+'.jpg');im.save(p,quality=90);return {'path':p.name,'sha256':digest(p)}
def run(data):
 repo=Path(__file__).resolve().parents[2];out=data/'experiments/atlas/scale-separated-relief-v1';planPath=repo/'docs/atlas/scale-separated-relief-plan.json';plan=json.loads(planPath.read_text(encoding='utf8'));assert digest(planPath)==digest(out/'frozen-plan.json')
 summary={'id':plan['id'],'operator':{'kind':'cartographic-derived-relief','sigma':'one nominal map-plane CSS pixel in metres','kernel':'normalized 13x13 Gaussian of prepared RG derivative channels','radiusTexels':6,'sourceCodeSha256':digest(repo/'scripts/atlas/relief_scale_control.mjs'),'analyzerSha256':digest(Path(__file__))},'software':{'python':platform.python_version(),'numpy':np.__version__,'pillow':pillow_version,'matplotlib':matplotlib.__version__,'maplibre':'6.11.2'},'pinnedShaderHashes':{name:digest(repo/'node_modules/maplibre-gl/src/shaders/glsl'/name) for name in ['hillshade_prepare.fragment.glsl','hillshade.fragment.glsl']},'planSha256':digest(planPath),'runs':[],'measurements':[],'visualIndex':[],'contactSheets':[],'geometryPairsVerified':0,'productionFilesVerified':len(plan['productionHashes']),'limitations':['Derivative quantization emulation is an offline proxy, not an exact GPU readback','Central tile window is 64 derivative texels, variable physical support across levels','Shader filter clamps beyond the one-texel prepared halo; tile-edge behavior must be evaluated separately','Settled-step navigation is not interactive frame-rate or loading-continuity validation']}
 for mode in ['aws','tryfan-regional','riffelhorn-regional']:
  root=out/'captures'/mode;file=root/'capture.json';a=json.loads(file.read_text(encoding='utf8'));assert 'failure' not in a and not a['pageErrors'];assert a['planSha256']==summary['planSha256'];assert all(r['status']==200 for r in a['requests'])
  navRoot=root
  assert len(a.get('navigation',[]))==(0 if mode=='aws' else 18), 'Incomplete nine-step navigation'
  if mode!='aws':
   first=next(s for s in plan['scenes'] if s['site']==('tryfan' if mode.startswith('tryfan') else 'riffelhorn') and s['targetMetresPerCssPixel']==8 and s['pitch']==0)
   for step in range(9):
    for r in a['navigation'][2*step:2*step+2]:
     s=r['scene'];assert s['center']==first['center'] and s['zoom']==first['zoom']+step/4
     assert s['targetMetresPerCssPixel']==8*2**(-step/4) and s['id']==first['site']+'-nav-'+str(step)
  expected=[s for s in plan['scenes'] if (s['site'] in ['downs','cambridge'] if mode=='aws' else s['site']==('tryfan' if mode.startswith('tryfan') else 'riffelhorn'))]
  assert len(a['scenes'])==2*len(expected)
  summary['runs'].append({'mode':mode,'reportSha256':digest(file),'scenes':len(a['scenes']),'navigationFrames':len(a.get('navigation',[])),'identities':a['identities'],'shaderSourceHashes':a['shaderSourceHashes'],'browser':a['browserVersion'],'httpErrors':a['httpErrors'],'navigationCancellations':a['failures']})
  for group,records in [('scenes',a['scenes']),('navigation',a.get('navigation',[]))]:
   groupRoot=root if group=='scenes' else navRoot
   for n in range(0,len(records),2):
    stock,control=records[n:n+2];assert [stock['depiction'],control['depiction']]==['igor','scale-separated'];assert stock['scene']==control['scene'];s=stock['scene']
    for field in ['geometryBuffers','actualDEMs','camera','points','terrain','mesh','hillshade']:assert stock['state'][field]==control['state'][field],field
    assert stock['state']['terrain']['exaggeration']==1.45 and stock['state']['mesh']==128
    camera=stock['state']['camera'];assert all(abs(camera[k]-s[k])<1e-10 for k in ['zoom','pitch','bearing']);assert all(abs(x-y)<1e-10 for x,y in zip(camera['center'],s['center']))
    mpp=WORLD*math.cos(math.radians(camera['center'][1]))/(512*2**camera['zoom']);assert abs(mpp-s['targetMetresPerCssPixel'])/mpp<1e-10
    if group=='scenes':assert s in expected
    else:assert s['pitch']==0 and s['bearing']==0
    assert stock['state']['reliefHook']['enabled']==False and control['state']['reliefHook']['enabled']==True
    assert len(stock['state']['geometryBuffers'])>0;summary['geometryPairsVerified']+=1
    for r in [stock,control]:
     assert digest(groupRoot/r['filename'])==r['sha256'];summary['visualIndex'].append({'mode':mode,'group':group,'scene':s['id'],'depiction':r['depiction'],'path':(groupRoot/r['filename']).relative_to(out).as_posix(),'sha256':r['sha256']})
    stat=derivative_patch(stock['state']['derivativeInput'],s['targetMetresPerCssPixel'])
    aa=np.asarray(Image.open(groupRoot/stock['filename']).convert('RGB'),dtype=float)[250:650,520:920]/255;bb=np.asarray(Image.open(groupRoot/control['filename']).convert('RGB'),dtype=float)[250:650,520:920]/255
    l=lambda v:(np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4)@np.array([.2126,.7152,.0722]))
    aL,bL=l(aa),l(bb)
    summary['measurements'].append({'site':s['site'],'scene':s['id'],'group':group,'sigmaMetres':s['targetMetresPerCssPixel'],'camera':s,'derivatives':stat,'captureLuminanceMeanAbsoluteChange':float(np.abs(aL-bL).mean()),'captureLuminanceP95P05Stock':float(np.quantile(aL,.95)-np.quantile(aL,.05)),'captureLuminanceP95P05Control':float(np.quantile(bL,.95)-np.quantile(bL,.05))})
  sites=sorted(set(r['scene']['site'] for r in a['scenes']))
  for site in sites:
   rows=[]
   for n in range(0,len(a['scenes']),2):
    stock,control=a['scenes'][n:n+2]
    if stock['scene']['site']!=site:continue
    rows.append([(f"{stock['scene']['targetMetresPerCssPixel']:g} m/CSS px pitch {stock['scene']['pitch']} / IGOR",root/stock['filename']),(f"same geometry / scale-separated",root/control['filename'])])
   summary['contactSheets'].append(sheet(out,site+'-relief',rows))
  if a.get('navigation'):
   rows=[]
   for n in range(0,len(a['navigation']),2):
    stock,control=a['navigation'][n:n+2];rows.append([(f"{stock['scene']['targetMetresPerCssPixel']:.3f} m/CSS px / IGOR",navRoot/stock['filename']),('same geometry / scale-separated',navRoot/control['filename'])])
   summary['contactSheets'].append(sheet(out,sites[0]+'-navigation',rows))
 for file,h in plan['productionHashes'].items():assert digest(repo/file)==h
 fig,ax=plt.subplots(figsize=(7,4));x=np.geomspace(1,64,150);ax.semilogx(x,np.exp(-.5*(2*np.pi/x)**2));ax.set(xlabel='Horizontal wavelength / nominal map-plane CSS pixel',ylabel='Continuum Gaussian derivative response',title='Frozen sigma = one nominal map-plane CSS pixel');ax.axvline(2,color='grey',linestyle='--');ax.grid();fig.tight_layout();p=out/'filter-response.png';fig.savefig(p,dpi=150);plt.close(fig);summary['responsePlot']={'path':p.name,'sha256':digest(p)}
 text=json.dumps(summary,sort_keys=True,indent=2,allow_nan=False)+'\n';(out/'summary.json').write_text(text,encoding='utf8',newline='\n');(repo/'docs/atlas/scale-separated-relief.json').write_text(text,encoding='utf8',newline='\n');print(json.dumps({'pairs':summary['geometryPairsVerified'],'sha256':digest(out/'summary.json')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);run(p.parse_args().data)
