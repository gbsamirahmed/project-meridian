"""Read-only retained illumination identifiability diagnostics. No correction or fitting.
NOAA published fractional-year equations; approximate geometric Sun, not SPA/refraction.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, math, sys
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT.parent/'meridian-data'
import importlib.util
_spec=importlib.util.spec_from_file_location('appearance_metadata_verifier',ROOT/'scripts/atlas/appearance-assessment/assess.py')
_old=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_old)
verify_entries,digest,read=_old.verify_entries,_old.digest,_old.read
PROTOCOL=Path(__file__).with_name('protocol.json')
OUT=ROOT/'docs/research/illumination-identifiability-results.json'

def solar(instant, lon, lat):
    t=datetime.fromisoformat(instant.replace('Z','+00:00'))
    if t.tzinfo is None:raise ValueError('Explicit timezone required')
    if not (-180<=lon<=180 and -90<=lat<=90):raise ValueError('Geographic coordinates required')
    t=t.astimezone(timezone.utc)
    hour=t.hour+t.minute/60+t.second/3600+t.microsecond/3.6e9
    year_days=366 if t.year%4==0 and (t.year%100!=0 or t.year%400==0) else 365
    g=2*math.pi/year_days*(t.timetuple().tm_yday-1+(hour-12)/24)
    eq=229.18*(0.000075+0.001868*math.cos(g)-0.032077*math.sin(g)-0.014615*math.cos(2*g)-0.040849*math.sin(2*g))
    dec=0.006918-0.399912*math.cos(g)+0.070257*math.sin(g)-0.006758*math.cos(2*g)+0.000907*math.sin(2*g)-0.002697*math.cos(3*g)+0.00148*math.sin(3*g)
    ha=math.radians((hour*60+eq+4*lon)%1440/4-180)
    phi=math.radians(lat)
    enu=np.array([-math.cos(dec)*math.sin(ha),math.cos(phi)*math.sin(dec)-math.sin(phi)*math.cos(dec)*math.cos(ha),math.sin(phi)*math.sin(dec)+math.cos(phi)*math.cos(dec)*math.cos(ha)])
    return {'inputUTC':t.isoformat().replace('+00:00','Z'),'lonlat':[lon,lat],'azimuthTrueNorthDegrees':math.degrees(math.atan2(enu[0],enu[1]))%360,'geometricElevationDegrees':math.degrees(math.asin(np.clip(enu[2],-1,1))),'unitENU':enu.tolist(),'method':'NOAA fractional-year equations/v1; no refraction, parallax or irradiance'}

def normals(z, spacing):
    gy,gx=np.gradient(z.astype(float),spacing)
    v=np.stack((-gx,gy,np.ones_like(z)),axis=-1)
    return v/np.linalg.norm(v,axis=-1)[...,None]

def grid_basis(lon,lat,crs=2056):
    tr=Transformer.from_crs(4326,crs,always_xy=True)
    x,y=tr.transform(lon,lat)
    e=np.array(tr.transform(lon+0.0001,lat))-[x,y]
    n=np.array(tr.transform(lon,lat+0.0001))-[x,y]
    e/=np.linalg.norm(e);n/=np.linalg.norm(n)
    return e,n

def grid_sun(s,e,n):
    h=e*s['unitENU'][0]+n*s['unitENU'][1]
    return np.array([h[0],h[1],s['unitENU'][2]])

def sampled_horizon(z, transform, point, sun, maximum=1000, step=1):
    # nearest DTM samples, no interpolation across terrain discontinuities or fitting
    def sample(x,y):
        inv=~transform
        col=inv.a*x+inv.b*y+inv.c;row=inv.d*x+inv.e*y+inv.f
        cols=np.floor(col).astype(int);rows=np.floor(row).astype(int)
        if np.any(cols<0) or np.any(rows<0) or np.any(cols>=z.shape[1]) or np.any(rows>=z.shape[0]):raise ValueError('Insufficient retained halo')
        return z[rows,cols]
    h=np.linalg.norm(sun[:2])
    if sun[2]<=0:raise ValueError('Daylight diagnostic only')
    if h<1e-12:return {'blockerWithinRadius':False,'maximumHorizonDegrees':None}
    d=np.arange(2,maximum+step/2,step,dtype=float)
    dx,dy=sun[:2]/h
    height=sample(point[0]+d*dx,point[1]+d*dy)
    base=float(sample(point[0],point[1]))
    angles=np.degrees(np.arctan2(height-base,d))
    i=int(np.argmax(angles));el=math.degrees(math.atan2(sun[2],h))
    return {'blockerWithinRadius':bool(angles[i]>el),'maximumHorizonDegrees':float(angles[i]),'horizonMaximumDistanceMetres':float(d[i]),'sunElevationDegrees':el,'stateOutsideRadius':'UNKNOWN; non-terrain occluders UNKNOWN'}

def quant(a):return [float(x) for x in np.percentile(a,[5,50,95])]

def build():
    protocol=read(PROTOCOL)
    baseline=read(ROOT/'docs/atlas/swissimage-source-derived-baseline.json')
    product=DATA/'derived/atlas/riffelhorn/riffelhorn-swissimage-baseline-v1'
    manifest=read(product/'manifest.json')
    # Verify frozen source/product files exactly as previous assessment, reuse old verifier.
    source=[]
    for f in baseline['source']['assets']:
        path=DATA/f['path']
        if digest(path)!=f['sha256']:raise ValueError('Changed original imagery')
        source.append({'file':str(path.relative_to(DATA)).replace(chr(92),'/'),'sha256':f['sha256'],'bytes':path.stat().st_size})
    if digest(product/'manifest.json')!='3c8b50fb9d7721b678abc46b9450495b417ccafff15d4ee8a67d9d6a3fee4934':raise ValueError('Changed product')
    prepared=verify_entries(product,manifest['files'],'path')
    diag_path=product/'source-diagnostics.json'
    if digest(diag_path)!='3d5c859f03d71037b8d9cfeeb56c3c80dd6be93b7a58cd097845d9b82c4d1618':raise ValueError('Changed source diagnostics')
    diag=read(diag_path)
    obs=read(ROOT/'docs/atlas/riffelhorn-observation-support.json')
    receipts=verify_entries(DATA/'experiments/atlas/riffelhorn-acquisition-support-v1',obs['metadataReceipts'],'file')
    mv=read(ROOT/'docs/atlas/swiss-multiview-input-manifest.json')
    parked=verify_entries(DATA/'experiments/atlas/swiss-alpine-multiview-discovery-v1',mv['files'],'file')
    vrt=DATA/'derived/atlas/riffelhorn/riffelhorn-swiss-support-v1/source-mosaic.vrt'
    if digest(vrt)!=obs['geometryVrtSha256']:raise ValueError('Changed geometry VRT')
    geometry=read(ROOT/'docs/atlas/riffelhorn-support-product.json')['source']
    with rasterio.open(vrt) as ds:
        win=from_bounds(*protocol['dtmReadBoundsLV95'],ds.transform).round_offsets().round_lengths()
        transform=ds.window_transform(win);z=ds.read(1,window=win)
        if not np.isfinite(z).all() or np.any(z==ds.nodata):raise ValueError('Unsupported terrain halo')
    leaves=[]
    for asset in geometry['assets']:
        path=Path(asset['href'].replace('${MERIDIAN_DATA_ROOT}',str(DATA)))
        with rasterio.open(path) as ds:
            b=ds.bounds;a=protocol['dtmReadBoundsLV95']
            used=b.left<a[2] and b.right>a[0] and b.bottom<a[3] and b.top>a[1]
        if used:
            if digest(path)!=asset['sha256']:raise ValueError('Changed terrain input')
            leaves.append({'file':str(path.relative_to(DATA)).replace(chr(92),'/'),'sha256':asset['sha256'],'bytes':path.stat().st_size})
    ns=normals(z,0.5)
    lon,lat=Transformer.from_crs(2056,4326,always_xy=True).transform(2624810,1092252)
    e,n=grid_basis(lon,lat)
    envelopes=[];scenarios=[]
    for date in protocol['dates']:
        start=datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        suns=[solar((start+timedelta(minutes=i)).isoformat(),lon,lat) for i in range(0,1440,protocol['envelopeUTCStepMinutes'])]
        daytime=[s for s in suns if s['geometricElevationDegrees']>0]
        policy=[s for s in daytime if s['geometricElevationDegrees']>=35]
        def envelope(ss):return {'firstSampleUTC':ss[0]['inputUTC'],'lastSampleUTC':ss[-1]['inputUTC'],'azimuthRangeDegrees':[min(s['azimuthTrueNorthDegrees'] for s in ss),max(s['azimuthTrueNorthDegrees'] for s in ss)],'maximumElevationDegrees':max(s['geometricElevationDegrees'] for s in ss),'samples':len(ss)}
        envelopes.append({'date':date,'daylightSampleEnvelope':envelope(daytime),'conditional35DegreePolicyEnvelope':envelope(policy),'policyApplicableToStripGoal':date=='2023-09-07','notExposureTimeBound':True})
        for hour in protocol['candidateUTCHours']:
            sun=solar(date+f'T{hour:02}:00:00Z',lon,lat)
            if sun['geometricElevationDegrees']>0:scenarios.append(sun)
    patches={}
    for name,(cx,cy,size) in protocol['patches'].items():
        probes=[p for p in diag['probes'] if p['patch']==name]
        coords=np.array([p['lv95'] for p in probes]);inv=~transform
        cc=inv.a*coords[:,0]+inv.b*coords[:,1]+inv.c;rr=inv.d*coords[:,0]+inv.e*coords[:,1]+inv.f
        nprobe=ns[np.floor(rr).astype(int),np.floor(cc).astype(int)]
        luma=np.array([p['sourceRGB'] for p in probes])@np.array(protocol['encodedLumaWeights'])
        scenarios_patch=[]
        for sun in scenarios:
            sg=grid_sun(sun,e,n);mu=nprobe@sg
            rays=[]
            for p in probes:
                if p['row'] in protocol['castShadowProbeRowsColumns'] and p['column'] in protocol['castShadowProbeRowsColumns']:
                    ray=sampled_horizon(z,transform,p['lv95'],sg,protocol['rayMaximumMetres'],protocol['rayStepMetres'])
                    ray['probe']=p['id'];ray['pointLV95']=p['lv95']
                    index=probes.index(p);ray['localIncidenceMu']=float(mu[index]);ray['sourceEncodedLuma']=float(luma[index]);rays.append(ray)
            scenarios_patch.append({'hypotheticalUTC':sun['inputUTC'],'muP05P50P95':quant(mu),'nonpositiveLocalIncidenceFraction':float(np.mean(mu<=0)),'encodedLumaVersusMuPearson':float(np.corrcoef(luma,mu)[0,1]),'rayBlockerCountOf9':sum(x['blockerWithinRadius'] for x in rays),'positiveLocalIncidenceBlockerCount':sum(x['blockerWithinRadius'] and x['localIncidenceMu']>0 for x in rays),'blockedProbeMedianEncodedLuma':float(np.median([x['sourceEncodedLuma'] for x in rays if x['blockerWithinRadius']])) if any(x['blockerWithinRadius'] for x in rays) else None,'notBlockedProbeMedianEncodedLuma':float(np.median([x['sourceEncodedLuma'] for x in rays if not x['blockerWithinRadius']])) if any(not x['blockerWithinRadius'] for x in rays) else None,'rays':rays})
        patches[name]={'centreLV95':[cx,cy],'widthMetres':size,'probes':len(probes),'probeLumaP05P50P95':quant(luma),'probeSlopeP05P50P95':quant(np.degrees(np.arccos(np.clip(nprobe[:,2],-1,1)))),'wholePatchPriorSourceStatistics':{k:v for k,v in diag['patches'][name].items() if k in ['exactBlackFraction','encodedLumaAtMost5Fraction','sourceLinearLuminanceP05P50P95']},'conditionalScenarios':scenarios_patch}
    frames=read(ROOT/'docs/atlas/swiss-multiview-benchmark.json')['analysis']['selected']
    flon,flat=Transformer.from_crs(2056,4326,always_xy=True).transform(*frames['centre'][:2])
    frame_suns=[{'frame':v['id'],'sunAtRemoteBenchmark':solar(v['acquisitionUTC'],flon,flat),'noPixels':True} for v in frames['views']]
    temporal=read(ROOT/'docs/earth-lab/tryfan-005c-temporal-evidence.json')
    temporal_receipt=DATA/'earth-lab/tryfan-005c/sentinel2-temporal-evidence/lab005c-report.json'
    if digest(temporal_receipt)!='06fe074eb64ad1fa675467a572c506e50d040429214a7d3acee8258c955d3fa8':raise ValueError('Changed Tryfan receipt')
    td=read(temporal_receipt);native_count=native_bytes=0
    for f in td['input_files']:
        path=Path(f['path'])
        if digest(path)!=f['sha256']:raise ValueError('Changed retained temporal input')
        native_count+=1;native_bytes+=path.stat().st_size
    retained_temporal={'receiptSha256':digest(temporal_receipt),'inputFilesVerified':native_count,'inputBytesVerified':native_bytes,'legacyBrightnessRelationships':td['illumination']['brightness_relationship_by_observation'],'legacyEncodingNotReanalysed':True}
    rgbpath=DATA/'experiments/earth-lab/tryfan-010/observed-natural-colour-v1/lab010-rgb-reflectance-10m.tif'
    if digest(rgbpath)!='89304e0045bc72b49c360c20bb62acd977673897c170ed5ee73b5920e1fb70b2':raise ValueError('Changed corrected-encoding reflectance')
    retained_temporal['lab010ReflectanceSha256']=digest(rgbpath)
    tlon,tlat=Transformer.from_crs(27700,4326,always_xy=True).transform(266400,359300)
    tryfan=[]
    for o in temporal['observations']:
        tryfan.append({'season':o['season'],'officialProduct':o['official_product_id'],'officialTimeSunAtAOICentre':solar(o['official_acquisition_time_utc'],tlon,tlat),'granuleTimeSunAtAOICentre':solar(o['cog_granule_time_utc'],tlon,tlat),'documentedSceneSun':{'elevation':o['sun_elevation_degrees'],'azimuth':o['sun_azimuth_degrees']},'SCL':o['aoi_scl'],'localUpstreamTerrainCorrectionConfiguration':'NOT RETAINED','notPixelTimeBound':True})
    meta_paths=['docs/atlas/swissimage-source-derived-baseline.json','docs/atlas/riffelhorn-observation-support.json','docs/atlas/riffelhorn-support-product.json','docs/atlas/swiss-multiview-benchmark.json','docs/atlas/swiss-multiview-input-manifest.json','docs/earth-lab/tryfan-005c-temporal-evidence.json','docs/earth-lab/tryfan-010-observed-natural-colour.json']
    return {'protocol':protocol,'protocolSha256':digest(PROTOCOL),'methodSha256':digest(Path(__file__)),'metadataHashes':{p:digest(ROOT/p) for p in meta_paths},'sourceVerification':source,'preparedVerification':prepared,'stripMetadataVerification':receipts,'parkedMetadataVerification':parked,'geometry':{'VRTSha256':digest(vrt),'sourceRevision':geometry['revision'],'vertical':geometry['verticalReference'],'actualReadScopeLV95':protocol['dtmReadBoundsLV95'],'gridMetres':0.5,'gridTrueEast':e.tolist(),'gridTrueNorth':n.tolist(),'verifiedLeaves':leaves},'sourceDiagnosticsSha256':digest(diag_path),'riffelhornLonLat':[lon,lat],'stripCandidates':[{'id':o['id'],'date':o['attributes']['flugdatum'],'goal':o['attributes']['goal'],'coverage':o['targetCoverage'],'pixelContributor':'UNKNOWN','exactExposureUTC':'UNKNOWN'} for o in obs['observations'] if o['id'] in ['20230907_1035_12504','20230821_0907_12501']],'dateEnvelopes':envelopes,'hypotheticalSunScenarios':scenarios,'patches':patches,'datedFrameContrast':frame_suns,'datedTryfanContrast':tryfan,'retainedTemporalVerification':retained_temporal,'noCorrection':True,'noAcquisition':True,'noNewShadowClassification':True}

if __name__=='__main__':
    logical=build();encoded=json.dumps(logical,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
    OUT.write_text(json.dumps({'logicalSha256':hashlib.sha256(encoded).hexdigest(),'logical':logical},indent=1,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'logicalSha256':hashlib.sha256(encoded).hexdigest(),'patches':len(logical['patches']),'sourceFiles':len(logical['sourceVerification']),'terrainLeaves':len(logical['geometry']['verifiedLeaves'])}))
