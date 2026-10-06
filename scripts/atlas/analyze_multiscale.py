"""Validate frozen cameras, summarize scale telemetry and index local evidence."""
import argparse,hashlib,json,math,platform
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw,__version__ as pillow_version
import rasterio,pyproj
from swissimage_baseline import verify_sources
from riffelhorn_support import source_record
WORLD=2*math.pi*6378137

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,value):Path(p).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
def centre_level(tiles,lonlat):
    levels=[]
    for t in tiles or []:
        if t is None:continue
        z=t['z'];x=(lonlat[0]+180)/360*2**z;y=(1-math.asinh(math.tan(math.radians(lonlat[1])))/math.pi)/2*2**z
        if t['x']<=x<t['x']+1 and t['y']<=y<t['y']+1:levels.append(z)
    return max(levels) if levels else None

def signal(p):
    a=np.asarray(Image.open(p).convert('RGB'),dtype='float64')[250:650,520:920]/255
    a=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4);lum=a@np.array([.2126,.7152,.0722]);return{'samplePixels':int(lum.size),'luminanceP05MedianP95':np.quantile(lum,[.05,.5,.95]).tolist(),'gradientMeanSquare':float(np.mean(np.diff(lum,axis=0)**2)+np.mean(np.diff(lum,axis=1)**2))}

def contact(out,name,rows):
    w,h=560,350;image=Image.new('RGB',(2*w,len(rows)*h),'white');draw=ImageDraw.Draw(image)
    for j,row in enumerate(rows):
        for i,(label,p) in enumerate(row):
            a=Image.open(p).convert('RGB');a.thumbnail((w,h-26));image.paste(a,(i*w,j*h+26));draw.text((i*w+5,j*h+5),label,fill='black')
    file=out/(name+'.jpg');image.save(file,quality=90);return{'path':file.name,'sha256':digest(file)}

def run(data):
    repo=Path(__file__).resolve().parents[2];out=data/'experiments/atlas/multiscale-representation-v1';planPath=repo/'docs/atlas/multiscale-representation-plan.json';plan=json.loads(planPath.read_text(encoding='utf8'));assert digest(planPath)==digest(out/'frozen-plan.json')
    records={};summary={'baseline':plan['baseline'],'planSha256':digest(planPath),'externalRoot':'experiments/atlas/multiscale-representation-v1','software':{'python':platform.python_version(),'numpy':np.__version__,'rasterio':rasterio.__version__,'gdal':rasterio.__gdal_version__,'pyproj':pyproj.__version__,'pillow':pillow_version},'runs':[],'measurements':[],'visualIndex':[],'productionFilesVerified':len(plan['productionHashes']),'limitations':['Screen differential is a finite 2-CSS-pixel first-hit estimate on loaded heightfields, not a calibrated optical footprint or true mesh normal.','Physical heights divide the renderer query by 1.45; physical and exaggerated metrics retained separately.','Spherical local ENU approximates metres; ellipsoidal/large-distance precision not claimed.','Central capture luminance uses fixed 400x400 CSS-pixel window, not a fixed ground population; includes portrayal, source epochs, contrast and residual labels. Not optical resolution or accuracy.','Screenshots are locally retained service evidence, not a public redistribution clearance.','No psychophysical test, task optimization, source PSF estimation or universal usefulness threshold.']}
    for mode in ['aws','tryfan-regional','riffelhorn-regional','riffelhorn-appearance']:
        base=out/'captures'/mode;file=base/'capture.json';a=json.loads(file.read_text(encoding='utf8'));assert a['planSha256']==summary['planSha256'];assert 'failure' not in a;assert not a['pageErrors']
        assert all(r['status']==200 for r in a['requests'])
        expectedScenes=plan['scenes'] if mode=='aws' else [s for s in plan['scenes'] if s['site']==('tryfan' if mode.startswith('tryfan') else 'riffelhorn')]
        appearances=['common','regional'] if mode.endswith('appearance') else ['terrain']
        expected={(s['id'],v) for s in expectedScenes for v in appearances}
        actual=[(r['scene']['id'],r['appearance']) for r in a['scenes']]
        assert len(actual)==len(expected) and set(actual)==expected
        summary['runs'].append({'mode':mode,'reportSha256':digest(file),'scenes':len(a['scenes']),'browser':a['browserVersion'],'identities':a.get('identities',[]),'imageryIdentity':a.get('imageryIdentity'),'endpointRequests':len(a['requests']),'httpErrors':a['httpErrors'],'navigationCancellations':a['failures']})
        for row in a['scenes']:
            scene=row['scene'];state=row['state'];camera=state['camera'];assert all(abs(camera[k]-scene[k])<1e-10 for k in ['zoom','pitch','bearing']);assert np.allclose(camera['center'],scene['center'],rtol=0,atol=1e-10);assert scene==next(s for s in plan['scenes'] if s['id']==scene['id']);assert state['mesh']==128;assert state['terrain']['exaggeration']==1.45
            if mode.endswith('appearance'):
                assert state['satellite']['raster-opacity']==1;ex=state['hillshade']['hillshade-exaggeration'];assert all(ex[i]==0 for i in range(4,len(ex),2))
            p=base/row['filename'];assert digest(p)==row['sha256'];summary['visualIndex'].append({'mode':mode,'scene':scene['id'],'appearance':row['appearance'],'path':p.relative_to(out).as_posix(),'sha256':row['sha256']});records[(mode,scene['id'],row['appearance'])]=(row,p)
            level=centre_level([t.get('source') for t in state['actualDEMs']],camera['center']);mesh=centre_level([t['render'] for t in state['actualDEMs']],camera['center']);relief=centre_level(state.get('reliefTiles'),camera['center']);imagery=centre_level(state.get('imageryTiles') if row['appearance']=='regional' else state.get('commonImageryTiles'),camera['center']);mpp=scene['targetMetresPerCssPixel'];lat=scene['center'][1]
            spacing=lambda z,n:WORLD*math.cos(math.radians(lat))/(n*2**z) if z is not None else None
            d=spacing(level,256);s=spacing(imagery,512)
            summary['measurements'].append({'mode':mode,'scene':scene['id'],'appearance':row['appearance'],'targetMetresPerCssPixel':mpp,'cameraZoom':scene['zoom'],'pitch':scene['pitch'],'geometryLevelAtCentre':level,'reliefLevelAtCentre':relief,'renderTileLevelAtCentre':mesh,'imageryLevelAtCentre':imagery,'geometryDeliveryMetresAtCentre':d,'geometryDeliverySamplesPerCssPixel':mpp/d if d else None,'meshStepMetresAtCentre':spacing(mesh,128),'imageryDeliveryMetresAtCentre':s,'imageryDeliverySamplesPerCssPixel':mpp/s if s else None,'nominalSwissimageInformationSamplesPerCssPixel':mpp/.25 if row['appearance']=='regional' else None,'physicalSurfaceProbes':[q['physicalMetric'] for q in state['points']],'renderedSurfaceProbes':[q['renderedMetric'] for q in state['points']],'captureSignal':signal(p)})
    for f,h in plan['productionHashes'].items():assert digest(repo/f)==h
    source=source_record(data);rgb=verify_sources(repo,data);summary['sourceIdentityChecks']={'swissTerrainSource':source['identity'],'terrainAssets':len(source['assets']),'swissimageSources':rgb}
    summary['spectrum']=json.loads((out/'spectrum.json').read_text(encoding='utf8'));summary['spectrumSha256']=digest(out/'spectrum.json');summary['diagnosticImages']=[]
    for site in ['tryfan','riffelhorn']:
        rows=[]
        for m in [128,8,.5,.125]:
            key=f'{site}-{m:g}m';rows.append([(f'{site} {m:g} m/CSS px / AWS',records[('aws',key,'terrain')][1]),(f'{site} {m:g} m/CSS px / regional eligible + fallback',records[(site+'-regional',key,'terrain')][1])])
        for m in [8,.5]:
            key=f'{site}-{m:g}m-p55';rows.append([(f'{site} {m:g} / pitch55 AWS',records[('aws',key,'terrain')][1]),(f'{site} {m:g} / pitch55 regional eligible + fallback',records[(site+'-regional',key,'terrain')][1])])
        summary['diagnosticImages'].append(contact(out,site+'-terrain-contact',rows))
    rows=[]
    for m in plan['scales']:
        key=f'riffelhorn-{m:g}m';rows.append([(f'{m:g} m/CSS px / MapTiler',records[('riffelhorn-appearance',key,'common')][1]),(f'{m:g} m/CSS px / SWISSIMAGE',records[('riffelhorn-appearance',key,'regional')][1])])
    summary['diagnosticImages'].append(contact(out,'riffelhorn-appearance-contact',rows))
    rows=[[(f'Downs / {m:g} m/CSS px',records[('aws',f'downs-{m:g}m','terrain')][1]),(f'Cambridge / {m:g} m/CSS px',records[('aws',f'cambridge-{m:g}m','terrain')][1])] for m in [128,8,.5]]
    summary['diagnosticImages'].append(contact(out,'rolling-low-relief-contact',rows))
    fig,axes=plt.subplots(1,2,figsize=(11,4.5))
    x=np.asarray(plan['scales']);axes[0].loglog(x,x/.25,'o-',label='SWISSIMAGE nominal 0.25 m');axes[0].loglog(x,x/1,'o-',label='Welsh distributed 1 m grid');axes[0].loglog(x,x/.5,'o-',label='Swiss distributed 0.5 m grid');axes[0].axhline(1,color='grey',linestyle='--');axes[0].invert_xaxis();axes[0].set(xlabel='Nominal map-plane metres / CSS pixel (finer →)',ylabel='Nominal source samples / CSS pixel',title='Sampling relationships; not independent resolution');axes[0].legend(fontsize=8)
    for d in summary['spectrum']['diagnostics']:
        b=d['spectrum']['bands'][1:5];axes[1].plot(range(4),[r['rmsMetres'] for r in b],'o-',label=d['site'])
    axes[1].set(xticks=range(4),xticklabels=['4–16','16–64','64–256','256–1024'],xlabel='Diagnostic horizontal wavelength band (m)',ylabel='Window-normalised elevation RMS (m)',title='Read-only 1,024 m terrain patches');axes[1].set_yscale('log');axes[1].legend();fig.tight_layout();file=out/'scale-and-wavelength.png';fig.savefig(file,dpi=150);plt.close(fig);summary['diagnosticImages'].append({'path':file.name,'sha256':digest(file)})
    save(out/'summary.json',summary);save(repo/'docs/atlas/multiscale-representation.json',summary)
    print(json.dumps({'captures':len(summary['visualIndex']),'sourceTerrainAssetsVerified':len(source['assets']),'productionFilesVerified':len(plan['productionHashes']),'summarySha256':digest(out/'summary.json')}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);a=p.parse_args();run(a.data)
