"""Offline analysis of frozen research telemetry; no runtime selection policy."""
import argparse, copy, hashlib, json, math, platform
from pathlib import Path
import numpy as np
from PIL import Image
from pyproj import Transformer
from swissimage_baseline import verify_sources
from riffelhorn_support import source_record
from information_display_math import applied_ratio, containing_tile, footprint, jacobian, metres_per_pixel, sample_projection, singular, wavelength_projection
MODES=['aws','tryfan-regional','riffelhorn-regional','riffelhorn-appearance']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def tile_spacing(tile,lat,kind):
    if not tile:return None
    size=tile.get('demDim') if kind=='dem' else (tile.get('texture') or {}).get('size',[None])[0]
    return metres_per_pixel(lat,tile['z'],size) if size else None

def inspect_scene(mode,entry,requests=()):
    state=entry['state'];display=state['display'];ratio=applied_ratio([display['cssRect']['width'],display['cssRect']['height']],display['canvas']);points=[]
    for p in state['points']:
        item={'fraction':p['fraction'],'screen':p['screen'],'location':p['origin']['xyz'],'roundTripCssError':max(v['roundTripCssError'] for st in p['stencils'] for v in [p['origin'],st['east'],st['west'],st['north'],st['south']])}
        try:
            j=jacobian(p['origin']['xyz'],p['stencils'][0],1.45);j2=jacobian(p['origin']['xyz'],p['stencils'][1],1.45)
            item['physical']=footprint(j,ratio);item['rendered']=footprint(jacobian(p['origin']['xyz'],p['stencils'][0]),ratio)
            item['stepSensitivity']=float(np.max(np.abs(np.asarray(singular(j2))/singular(j)-1)))
            item['flags']=[flag for flag,condition in [('finite-step sensitivity',item['stepSensitivity']>.25),('project/unproject mismatch',item['roundTripCssError']>2)] if condition]
            loc=item['location'];geom=containing_tile([dict(g['render'],geometry=g) for g in state['geometry']],loc)
            projections={}
            if geom:
                g=geom['geometry'];item['geometryIdentity']={k:g[k] for k in ['source','render','sourceDim','sha256']}
                item['drapingTextureObserved']=g.get('rttTexture') is not None
                request=next((r for r in requests if r.get('kind')=='terrain' and all(r[k]==g['source'][k] for k in ['z','x','y'])),None)
                item['selectionIdentity']={k:request['decision'].get(k) for k in ['family','sourceFamily','role','product','level','refinement','reason']} if request else {'family':'aws-common','product':'production AWS visual registry','informationCeiling':'unknown'}
                for name,spacing in [('encodedDEM',metres_per_pixel(loc[1],g['source']['z'],g['sourceDim'])),('meshGrid',metres_per_pixel(loc[1],g['render']['z'],state['mesh'])),('drapedRTT',metres_per_pixel(loc[1],g['render']['z'],display['rttSize']))]:projections[name]=sample_projection(j,spacing,ratio)
            relief=containing_tile(state.get('reliefTiles'),loc);image=containing_tile(state.get('imageryTiles') if entry['appearance']=='regional' else state.get('commonImageryTiles'),loc)
            for name,tile,kind in [('reliefDEM',relief,'dem'),('imageryDelivery',image,'image')]:
                spacing=tile_spacing(tile,loc[1],kind)
                if spacing:projections[name]=sample_projection(j,spacing,ratio)
            selected_family=item.get('selectionIdentity',{}).get('family')
            nominal=1 if selected_family=='welsh-regional' else .5 if selected_family=='swiss-regional' else None
            if nominal:projections['distributedSourceGrid']=sample_projection(j,nominal,ratio)
            if entry['appearance']=='regional':
                projections['nominalOrthophotoInformation']=sample_projection(j,.25,ratio);projections['distributedOrthophotoGrid']=sample_projection(j,.1,ratio)
            item['sampling']=projections;item['wavelengths']=[wavelength_projection(j,l,ratio) for l in [1,10,100]]
            item['tileLevels']={'relief':None if not relief else relief['z'],'imagery':None if not image else image['z']}
        except (ValueError,TypeError,np.linalg.LinAlgError) as e:item['unavailable']=str(e)
        points.append(item)
    return {'mode':mode,'id':entry['scene']['id'],'appearance':entry['appearance'],'dpr':entry['dpr'],'camera':state['camera'],'requestedMapMetresPerCssPixel':entry['scene']['targetMetresPerCssPixel'],'display':display,'actualFramebufferRatio':ratio,'filename':entry['filename'],'sha256':entry['sha256'],'points':points}

def signatures(state):
    return {'geometry':sorted(set((g['source']['z'],g['source']['x'],g['source']['y'],g['sourceDim'],g['sha256']) for g in state['geometry'])),
      'renderTiles':sorted((g['render']['z'],g['render']['x'],g['render']['y']) for g in state['geometry']),
      'relief':sorted((t['z'],t['x'],t['y'],t.get('demDim')) for t in state.get('reliefTiles',[])),
      'commonImagery':sorted((t['z'],t['x'],t['y'],(t.get('texture') or {}).get('size')) for t in state.get('commonImageryTiles',[])),
      'regionalImagery':sorted((t['z'],t['x'],t['y'],(t.get('texture') or {}).get('size')) for t in state.get('imageryTiles',[])),
      'mesh':state['mesh'],'rtt':state['display']['rttSize']}

def analyze(root,repo,appearance_run="validated",terrain_run="validated"):
    plan_path=repo/'docs/atlas/information-display-plan.json';plan=json.loads(plan_path.read_text());plan_hash=sha(plan_path);rows=[];raw=[];manifests={};capture_root=root/'experiments/atlas/information-display-v1'/('captures-'+terrain_run)
    for mode in MODES:
        mode_root=root/'experiments/atlas/information-display-v1'/('captures-'+appearance_run if mode=='riffelhorn-appearance' else 'captures-'+terrain_run)/mode
        file=mode_root/'capture.json';r=json.loads(file.read_text());assert r['planSha256']==plan_hash;assert not r.get('failure');assert not r['pageErrors'];assert all(f['error']=='net::ERR_ABORTED' for f in r['failures']);assert all(q['status']==200 for q in r['requests'])
        assert all('/weather/gfs/' in e['url'] and e['status']==503 for e in r['httpErrors']),r['httpErrors']
        manifests[mode]={'sha256':sha(file),'identities':r['identities'],'browserVersion':r['browserVersion'],'imageryIdentity':r.get('imageryIdentity'),'metadataSynchronization':r.get('metadataSynchronization',[]),'activationSynchronization':r.get('activationSynchronization',[]),'cancelledRequests':r['failures']}
        for s in r['scenes']:
            img=mode_root/s['filename'];assert sha(img)==s['sha256'];size=Image.open(img).size;assert size==(1440*s['dpr'],900*s['dpr'])
            st=s['state']
            if s['appearance']!='terrain':
                assert st['satellite']['raster-opacity']==1
                curve=st['hillshade']['hillshade-exaggeration'];assert all(curve[i]==0 for i in range(4,len(curve),2))
            assert st['terrain']=={'source':'terrain-dem','exaggeration':1.45};assert st['mesh']==128;assert st['display']['transform']==[1440,900]
            task=next(t for t in plan['tasks'] if t['mode']==mode and t['scene']['id']==s['scene']['id']);assert s['scene']==task['scene'];assert s['dpr'] in task['dprs'];assert s['appearance'] in task['appearances']
            assert all(abs(st['camera'][k]-s['scene'][k])<1e-7 for k in ['zoom','pitch','bearing']);assert np.allclose(st['camera']['center'],s['scene']['center'],atol=1e-9)
            row=inspect_scene(mode,s,r['requests'])
            if s['appearance']=='regional':
                image_root=root/'derived/atlas/riffelhorn/riffelhorn-swissimage-baseline-v1';manifest=json.loads((image_root/'manifest.json').read_text());transform=Transformer.from_crs('OGC:CRS84',manifest['nativeCRS'],always_xy=True);bounds=manifest['sourceBounds']
                for point in row['points']:
                    lon,lat=point['location'][:2];east,north=transform.transform(lon,lat);inside=bounds[0]<=east<bounds[2] and bounds[1]<=north<bounds[3]
                    image_tile=containing_tile(st.get('imageryTiles'),[lon,lat]);alpha=None
                    if image_tile:
                        tile_file=image_root/f"tiles/{image_tile['z']}/{image_tile['x']}/{image_tile['y']}.png"
                        if tile_file.exists():
                            with Image.open(tile_file) as tile_image:
                                x=(lon+180)/360*2**image_tile['z'];y=(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**image_tile['z'];ix=min(tile_image.width-1,max(0,int((x-image_tile['x'])*tile_image.width)));iy=min(tile_image.height-1,max(0,int((y-image_tile['y'])*tile_image.height)));alpha=tile_image.getpixel((ix,iy))[3]/255
                        else:alpha=0
                    point['appearanceSupport']={'nativePosition':[east,north],'insideSourceBounds':inside,'nearestPreparedAlphaFraction':alpha,'semantics':'Area support fraction; not quality/shadow/occlusion/confidence'}
                    if not inside:
                        for name in ['nominalOrthophotoInformation','distributedOrthophotoGrid']:point.get('sampling',{}).pop(name,None)
            row['screenshotPixels']=size;row['captureDirectory']=mode_root.relative_to(root).as_posix();rows.append(row);raw.append((mode,s))
    expected={(t['mode'],t['scene']['id'],d,a) for t in plan['tasks'] for d in t['dprs'] for a in t['appearances']};actual={(r['mode'],r['id'],r['dpr'],r['appearance']) for r in rows};assert actual==expected and len(rows)==plan['expectedCaptures']
    groups=[]
    for mode,e in raw:
        if e['dpr']!=1:continue
        peers=[s for m,s in raw if m==mode and s['scene']['id']==e['scene']['id'] and s['appearance']==e['appearance']]
        if len(peers)<2:continue
        base=signatures(e['state']);groups.append({'mode':mode,'id':e['scene']['id'],'appearance':e['appearance'],'differencesFromDpr1':{str(s['dpr']):[k for k,v in signatures(s['state']).items() if v!=base[k]] for s in peers},'levels':{str(s['dpr']):{'geometry':sorted(set(g['source']['z'] for g in s['state']['geometry'])),'relief':sorted(set(t['z'] for t in s['state'].get('reliefTiles',[]))),'commonImagery':sorted(set(t['z'] for t in s['state'].get('commonImageryTiles',[]))),'regionalImagery':sorted(set(t['z'] for t in s['state'].get('imageryTiles',[])))} for s in peers}})
    pairs=[]
    for mode,e in raw:
        if e['appearance']!='common':continue
        peer=next(s for m,s in raw if m==mode and s['scene']['id']==e['scene']['id'] and s['dpr']==e['dpr'] and s['appearance']=='regional')
        pairs.append({'id':e['scene']['id'],'dpr':e['dpr'],'sameGeometry':signatures(e['state'])['geometry']==signatures(peer['state'])['geometry'],'sameCamera':e['state']['camera']==peer['state']['camera']})
    for f,h in plan['productionHashes'].items():assert sha(repo/f)==h,f
    for f,h in plan['rendererHashes'].items():assert sha(repo/'node_modules/maplibre-gl/src'/f)==h,f
    source=source_record(root);rgb=verify_sources(repo,root);prior=json.loads((repo/'docs/atlas/multiscale-representation.json').read_text());assert source['identity']==prior['sourceIdentityChecks']['swissTerrainSource'];assert rgb==prior['sourceIdentityChecks']['swissimageSources']
    return {'id':plan['id'],'planSha256':plan_hash,'captureRoot':capture_root.relative_to(root).as_posix(),'versions':{'python':platform.python_version(),'numpy':np.__version__},'manifests':manifests,'captures':rows,'dprComparisons':groups,'matchedAppearanceControls':pairs,'productionFilesVerified':len(plan['productionHashes']),'rendererFilesVerified':len(plan['rendererHashes']),'sourceIdentityChecks':{'swissTerrainSource':source['identity'],'terrainAssets':len(source['assets']),'swissimageSources':rgb},
      'limits':['Finite ray/query footprint of the displayed heightfield, not exact mesh triangle derivative or sensor footprint','Physical heights de-exaggerated 1.45; slope depends on delivered DEM, not claimed source truth','Spherical local ENU and isotropic map-plane sampling proxies; principal axes retain anisotropy','Framebuffers and screenshots differ at clamped DPR; screenshot density is not independent rasterisation','Common-source optical information remains unknown; nominal spacing is not a confidence or legibility threshold']}


def compact(value,full_path,full_hash):
    result=copy.deepcopy(value);result['fullDiagnostic']={'path':full_path,'sha256':full_hash}
    for scene in result['captures']:
        points=scene.pop('points');scene['centreProbe']=points[4];scene['probes']=[]
        for point in points:
            item={k:point[k] for k in ['fraction','location','roundTripCssError','stepSensitivity','flags','appearanceSupport','unavailable'] if k in point}
            if 'physical' in point:
                f=point['physical'];item['physical']={k:f[k] for k in ['jacobianMetresPerCssPixel','surfacePrincipalMetresPerCssPixel','surfacePrincipalMetresPerFramebufferPixel','slopeDegrees','normalENU']}
                item['geometrySource']=point.get('geometryIdentity',{}).get('source');item['family']=point.get('selectionIdentity',{}).get('family')
                item['encodedDEM']=point.get('sampling',{}).get('encodedDEM')
            scene['probes'].append(item)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('data');parser.add_argument('--appearance-run',default='validated');parser.add_argument('--terrain-run',default='validated');parser.add_argument('--output',default='docs/atlas/information-display.json');a=parser.parse_args();repo=Path(__file__).resolve().parents[2];root=Path(a.data);value=analyze(root,repo,a.appearance_run,a.terrain_run)
    full=root/'experiments/atlas/information-display-v1/diagnostics/full-metrics.json';write(full,value);summary=compact(value,full.relative_to(root).as_posix(),sha(full));write(repo/a.output,summary)
    print(json.dumps({'captures':len(value['captures']),'sha256':sha(repo/a.output),'fullSha256':sha(full),'flaggedPoints':sum(bool(p.get('flags')) for r in value['captures'] for p in r['points'])}))
