"""Offline metadata/normal diagnostic. Never downloads or processes aerial pixels."""
import argparse, csv, hashlib, json, math
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from pyproj import Transformer
from matplotlib.path import Path as PolygonPath
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import swissimage_baseline as baseline

TARGETS = {k: baseline.PATCHES[k] for k in ('steep', 'summit', 'dark-context')}

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n', encoding='utf8')

def normals(height, spacing):
    """Upward ENU normal; raster rows increase south, hence north gradient=-gy."""
    gy, gx = np.gradient(np.asarray(height, dtype='float64'), spacing, spacing)
    stretch = np.sqrt(1 + gx*gx + gy*gy)
    return np.stack((-gx/stretch, gy/stretch, 1/stretch), axis=-1), stretch

def incidence(normal, vector):
    """Target-to-camera vector. Good incidence is NOT line-of-sight visibility."""
    v = np.asarray(vector, dtype='float64')
    if not np.all(np.isfinite(v)) or np.linalg.norm(v) == 0: raise ValueError('Invalid view vector')
    mu = np.sum(normal * (v/np.linalg.norm(v)), axis=-1)
    angle = np.degrees(np.arccos(np.clip(mu, -1, 1)))
    factor = np.divide(1., mu, out=np.full(mu.shape, np.inf), where=mu>0)
    return angle, factor

def covered(rings, points):
    # Selected official 2023 records are single-ring polygons; fail rather than guess holes.
    if len(rings) != 1: raise ValueError('Expected single-ring footprint')
    ring=np.asarray(rings[0],dtype='float64')
    if ring.ndim!=2 or ring.shape[1]!=2 or len(ring)<4 or not np.isfinite(ring).all():
        raise ValueError('Invalid footprint coordinates')
    return PolygonPath(ring).contains_points(points)

def read_frames(path):
    with path.open(encoding='utf-8-sig') as handle:
        rows = list(csv.DictReader(handle, delimiter=';'))
    required = {'feature_id','easting','northing','altitude','capture_time','omega','phi','kappa'}
    if not rows or not required.issubset(rows[0]): raise ValueError('Unexpected digital catalogue fields')
    for row in rows:
        for key in ('easting','northing','altitude','omega','phi','kappa'):
            if not math.isfinite(float(row[key])): raise ValueError('Invalid camera metadata')
    return rows

def fetch_metadata(repo, destination):
    import urllib.request
    from datetime import datetime, timezone
    record=json.loads((repo/'docs/atlas/riffelhorn-observation-support.json').read_text())
    if destination.exists(): raise ValueError('Use an absent metadata directory; retain previous receipt bytes')
    destination.mkdir(parents=True)
    save(destination/'pre-evaluation-freeze.json',record['frozenGate'])
    receipts=[]
    for row in record['metadataReceipts']:
        url=row['url'];name=row['file']
        if Path(name).name!=name: raise ValueError('Invalid metadata filename')
        is_csv=url=='https://data.geo.admin.ch/ch.swisstopo.lubis-luftbilder_digital/lubis-luftbilder_digital.csv'
        is_json=url.startswith('https://api3.geo.admin.ch/rest/services/api/MapServer') and name.endswith('.json')
        if not (is_csv or is_json): raise ValueError('Only pinned metadata endpoints allowed')
        cap=10_000_000 if is_csv else 2_000_000
        with urllib.request.urlopen(url,timeout=30) as response:
            content=response.read(cap+1);headers=dict(response.headers)
        if len(content)>cap: raise ValueError('Metadata size cap exceeded')
        if not is_csv: json.loads(content)
        digest=hashlib.sha256(content).hexdigest()
        published=headers.get('X-Amz-Meta-Sha256')
        if published and published!=digest: raise ValueError('Published checksum mismatch')
        (destination/name).write_bytes(content)
        receipts.append({'file':name,'url':url,'receivedUTC':datetime.now(timezone.utc).isoformat(),
                         'bytes':len(content),'sha256':digest,**({'providerSha256':published} if published else {})})
    save(destination/'receipts.json',receipts)
    print('Metadata only retained; mutable catalogues may differ from original hashes.')

def run(repo, data, metadata, out):
    out.mkdir(parents=True, exist_ok=True)
    freeze = json.loads((metadata/'pre-evaluation-freeze.json').read_text())
    canonical=json.loads((repo/'docs/atlas/riffelhorn-observation-support.json').read_text(encoding='utf8'))
    assert freeze==canonical['frozenGate'], 'Frozen acquisition gate changed'
    assert freeze['targets'] == {k:list(v) for k,v in TARGETS.items()}
    assert freeze['boundsLV95'] == list(baseline.BOUNDS)
    retained = json.loads((repo/'docs/atlas/swissimage-source-derived-baseline.json').read_text())
    verified = {}
    for asset in retained['source']['assets']:
        assert sha(data/asset['path']) == asset['sha256']
        verified[asset['path']] = asset['sha256']
    product = data/retained['externalOutputs']['product']
    manifest = json.loads((product/'manifest.json').read_text())
    assert manifest['identity'] == retained['product']['identity']
    for row in manifest['files']:
        assert sha(product/row['path']) == row['sha256']
    for name, expected in retained['externalOutputs']['diagnosticHashes'].items():
        assert sha(product/name) == expected
    for name, expected in retained['productionUnchanged']['hashes'].items():
        assert sha(repo/name) == expected
    vrt = data/'derived/atlas/riffelhorn/riffelhorn-swiss-support-v1/source-mosaic.vrt'
    assert sha(vrt) == retained['geometrySourceHashesVerified']['vrtSha256']
    # Verify the actual native DEM files supplying these targets, not just their VRT.
    support = json.loads((repo/'docs/atlas/riffelhorn-support-product.json').read_text())
    native_assets = [r for r in support['source']['assets'] if '_2624-1092_' in r['href']]
    assert len(native_assets)==1
    for row in native_assets:
        asset_path = data/row['href'].replace('${MERIDIAN_DATA_ROOT}/','')
        assert sha(asset_path)==row['sha256']
    for row, directory in zip(retained['geometry'], ['riffelhorn-regional-parents-v1','riffelhorn-swiss-support-v1']):
        assert sha(data/'derived/atlas/riffelhorn'/directory/'manifest.json')==row['manifestSha256']
    receipts = json.loads((metadata/'receipts.json').read_text())
    for row in receipts:
        assert sha(metadata/row['file']) == row['sha256']
        assert (metadata/row['file']).stat().st_size==row['bytes']
    strips = json.loads((metadata/'strips.json').read_text())['results']
    assert len(strips) < 200, 'Bounded result may be truncated'
    selected = sorted((r for r in strips if r['attributes']['bgdi_flugjahr']==2023), key=lambda r:r['featureId'])
    expected={r['id']:r for r in canonical['observations']}
    assert {r['featureId'] for r in selected}==set(expected), '2023 catalogue changed; review rather than inherit verdict'
    for row in selected:
        assert row['geometry']['spatialReference']['wkid']==2056
        assert set(row['attributes'])==set(expected[row['featureId']]['attributes']), 'Metadata schema changed; review geometry availability'
    geo = Transformer.from_crs(2056,4326,always_xy=True)
    result = {'baseline':freeze['baseline'],'frozenGate':freeze,'geometry':retained['geometry'],
              'nativeGeometryAssets':native_assets,'geometryVrtSha256':sha(vrt),'sourceHashes':verified,'verifiedProductFiles':len(manifest['files']),
              'productIdentity':manifest['identity'],'metadataReceipts':receipts,'targets':{},'observations':[],
              'classification':'PARTIAL \u2014 COVERAGE WITHOUT SUFFICIENT GEOMETRY',
              'candidateIncidence':'UNAVAILABLE: no target-specific ADS trajectory, calibration or line/ray mapping in public strip records',
              'visibility':'UNKNOWN; no candidate camera positions, therefore no line-of-sight test',
              'noPixelsAcquired':True,'noCorrectionOrReconstruction':True}
    fig, ax = plt.subplots(figsize=(8,8))
    ax.add_patch(plt.Rectangle((2624000,1091000),2000,2000,fill=False,color='black',lw=2,label='Frozen 4 square km support'))
    palette = plt.get_cmap('tab10')
    for i,row in enumerate(selected):
        ring = np.asarray(row['geometry']['rings'][0]); ax.plot(ring[:,0],ring[:,1],color=palette(i),label=row['featureId'],lw=1.5)
        ax.fill(ring[:,0],ring[:,1],color=palette(i),alpha=.07)
        result['observations'].append({'id':row['featureId'],'attributes':row['attributes'],
                    'publishedFootprint':row['geometry'],'targetCoverage':{},'poseAvailable':False,
                    'mosaicContribution':'UNKNOWN','generation':'2023 ADS strip, not 2026 frame',
                    'acquisitionInstant':'UNKNOWN: published date only; ID time-like component not decoded as UTC'})
    with rasterio.open(vrt) as dem:
        assert dem.crs.to_epsg()==2056 and dem.res==(0.5,0.5)
        for name,(x,y,side) in TARGETS.items():
            window=from_bounds(x-side/2,y-side/2,x+side/2,y+side/2,dem.transform)
            h=dem.read(1,window=window); n,stretch=normals(h,.5)
            assert np.all(h!=dem.nodata)
            assert np.all(np.isfinite(h)) and np.allclose(np.linalg.norm(n,axis=-1),1)
            old=retained['sourcePatches'][name]
            assert np.allclose(np.percentile(stretch,[5,50,95]),old['surfaceAreaFactorP05P50P95'],rtol=0,atol=1e-12)
            az=np.mod(np.degrees(np.arctan2(n[:,:,0],n[:,:,1])),360)
            difficult=stretch>2
            mean=n.mean(axis=(0,1)); tr=dem.window_transform(window)
            yy,xx=np.indices(h.shape); points=np.column_stack(((tr.c+(xx+.5)*.5).ravel(),(tr.f-(yy+.5)*.5).ravel()))
            info={'centreLV95':[x,y],'centreWGS84':list(geo.transform(x,y)),'sideMetres':side,'nativeGridMetres':.5,
                  'slopeP05P50P95':old['slopeDegreesP05P50P95'], 'stretchP05P50P95':old['surfaceAreaFactorP05P50P95'],
                  'nominalTangentFootprintP05P50P95':old['nominalTangentFootprintMetresP05P50P95'],
                  'normalENUAverage':mean.tolist(),'normalMeanDirectionAzimuthGridNorth':float(np.mod(np.degrees(np.arctan2(mean[0],mean[1])),360)),
                  'aspectHistogramEdgesDegrees':list(range(0,361,45)), 'aspectCounts':np.histogram(az,bins=range(0,361,45))[0].tolist(),
                  'aspectCountsStretchAbove2':np.histogram(az[difficult],bins=range(0,361,45))[0].tolist(),
                  'difficultCells':int(difficult.sum()),'cells':int(h.size),
                  'heightRangeLN02': [float(h.min()),float(h.max())],
                  'normalConvention':'ENU, grid north; horizontal normal points downslope. No renderer exaggeration or height transformation.'}
            result['targets'][name]=info
            for row,record in zip(selected,result['observations']):
                mask=covered(row['geometry']['rings'],points)
                record['targetCoverage'][name]={'cellCentreFraction':float(mask.mean()),'centreCovered':bool(covered(row['geometry']['rings'],[(x,y)])[0])}
            ax.add_patch(plt.Rectangle((x-side/2,y-side/2),side,side,fill=False,color='black'))
            direction=mean[:2]/np.linalg.norm(mean[:2])
            ax.arrow(x,y,direction[0]*75,direction[1]*75,width=3,color='black',length_includes_head=True)
            ax.annotate(name,(x,y),xytext={'steep':(20,25),'summit':(30,-22),'dark-context':(-100,25)}[name],textcoords='offset points',fontsize=9)
    frames=read_frames(metadata/'digital-catalogue.csv')
    nearest=min(frames,key=lambda r:math.hypot(float(r['easting'])-TARGETS['steep'][0],float(r['northing'])-TARGETS['steep'][1]))
    distance=math.hypot(float(nearest['easting'])-TARGETS['steep'][0],float(nearest['northing'])-TARGETS['steep'][1])
    result['newGeneration']={'catalogueRows':len(frames),'nearestCentreRecord':nearest,'nearestCentreDistanceMetres':distance,
        'centresWithin20km':sum(math.hypot(float(r['easting'])-2624805,float(r['northing'])-1092330)<20000 for r in frames),
        'interpretation':'No local candidate centre in this retained newer catalogue; no target incidence or coverage inferred from remote records. Not evidence of 2023 geometry or universal absence of unpublished acquisitions.'}
    ax.text(2624060,1091600,'0907 (21 Aug) + 1035 (7 Sep): all target cells covered\nArrows: mean horizontal terrain-normal direction\nFootprints do not establish camera rays or visibility.',fontsize=8)
    result['software']={'numpy':np.__version__,'rasterio':rasterio.__version__,'matplotlib':matplotlib.__version__}
    ax.set(xlim=(2624000,2626000),ylim=(1091000,1093000),xlabel='LV95 easting (m)',ylabel='LV95 northing (m)',title='Published 2023 strip footprints \u2014 coverage, NOT visibility')
    ax.set_aspect('equal');ax.ticklabel_format(style='plain',useOffset=False);ax.legend(fontsize=7,loc='lower left');fig.tight_layout()
    fig.savefig(out/'footprint-map.png',dpi=160,metadata={'Software':'Meridian metadata diagnostic v1'});plt.close(fig)
    save(out/'analysis.json',result)
    print(json.dumps({'classification':result['classification'],'coverage':[{ 'id':r['id'],'patches':r['targetCoverage']} for r in result['observations']], 'targetOrientations':{k:v['normalMeanDirectionAzimuthGridNorth'] for k,v in result['targets'].items()},'newGeneration':{'rows':len(frames),'nearestMetres':distance}},ensure_ascii=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path);p.add_argument('--metadata',type=Path,required=True);p.add_argument('--out',type=Path);p.add_argument('--refresh-metadata',action='store_true')
    args=p.parse_args();repo=Path(__file__).resolve().parents[2]
    if args.refresh_metadata:fetch_metadata(repo,args.metadata)
    else:
        if args.data is None or args.out is None:p.error('--data and --out required for offline analysis')
        run(repo,args.data,args.metadata,args.out)
