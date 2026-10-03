"""Bounded live terrain diagnostics; not run by CI or used by production sampling.

Uses existing NumPy/Pillow research dependencies. Saves only ignored evaluation
products. Same-z comparisons average 2x2 Mapterhorn pixels onto the AWS tile grid;
this explicit diagnostic registration is not a change to Meridian's sampler.
No accuracy claim, ground truth, general downloader, retry or provider fallback.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from io import BytesIO
from hashlib import sha256
import json
import math
import time
from datetime import datetime, timezone

import numpy as np
from PIL import Image

OUT = Path('test-results/atlas-terrain-foundation/numeric')
OUT.mkdir(parents=True, exist_ok=True)
URLS = {
    'aws': 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png',
    'mapterhorn': 'https://tiles.mapterhorn.com/{z}/{x}/{y}.webp',
}
requests = []
cache = {}


def tile_xy(lon, lat, z):
    n = 2 ** z
    return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n


def tile(provider, z, x, y):
    key = (provider, z, x, y)
    if key in cache:
        return cache[key]
    url = URLS[provider].format(z=z, x=x, y=y)
    started = time.perf_counter()
    try:
        response = urlopen(Request(url, headers={'Origin': 'http://localhost:4173', 'User-Agent': 'Meridian-bounded-terrain-evaluation'}), timeout=30)
    except HTTPError as error:
        response = error
    with response:
        body = response.read()
        row = {'provider': provider, 'z': z, 'x': x, 'y': y, 'url': url,
               'status': response.status, 'bytes': len(body), 'ms': (time.perf_counter()-started)*1000,
               'headers': dict(response.headers), 'sha256': sha256(body).hexdigest()}
    requests.append(row)
    (OUT / 'http-requests.json').write_text(json.dumps(requests,indent=2)+'\n',encoding='utf-8')
    if row['status'] != 200:
        cache[key] = None
        return None
    image = Image.open(BytesIO(body)).convert('RGB')
    row['dimensions'] = image.size
    expected = 256 if provider == 'aws' else 512
    assert image.size == (expected, expected)
    rgb = np.asarray(image, dtype=np.float64)
    heights = rgb[..., 0] * 256 + rgb[..., 1] + rgb[..., 2]/256 - 32768
    cache[key] = heights
    (OUT / f'{provider}-{z}-{x}-{y}.bin').write_bytes(body)
    return heights


def stats(data):
    return {'min': float(np.min(data)), 'max': float(np.max(data)), 'mean': float(np.mean(data)),
            'std': float(np.std(data)), 'rms': float(np.sqrt(np.mean(data**2))),
            'p95abs': float(np.percentile(np.abs(data), 95))}


def bilinear(array, x, y):
    # Pixel centers; clamp within this parent tile for the diagnostic only.
    x = np.clip(x, 0, array.shape[1]-1); y = np.clip(y, 0, array.shape[0]-1)
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    x1 = np.minimum(x0+1, array.shape[1]-1); y1 = np.minimum(y0+1, array.shape[0]-1)
    fx = x-x0; fy = y-y0
    return (array[y0,x0]*(1-fx)+array[y0,x1]*fx)*(1-fy)+(array[y1,x0]*(1-fx)+array[y1,x1]*fx)*fy


locations = [('tryfan', -3.999, 53.115), ('riffelhorn', 7.76121329, 45.97910794),
             ('downs', -.766, 50.908), ('cambridge', .12, 52.20)]
report = {'accessTime': datetime.now(timezone.utc).isoformat(), 'sameZoom': [], 'higherZoom': [], 'requests': requests}
for name, lon, lat in locations:
    x, y = [math.floor(v) for v in tile_xy(lon,lat,15)]
    aws = tile('aws',15,x,y); mt = tile('mapterhorn',15,x,y)
    assert aws is not None and mt is not None
    reduced = mt.reshape(256,2,256,2).mean(axis=(1,3))
    report['sameZoom'].append({'location':name,'z':15,'x':x,'y':y,
        'aws':stats(aws),'mapterhorn':stats(mt),'mapterhornMinusAws':stats(reduced-aws),
        'awsNeighborDifferenceRms': float(np.sqrt(np.mean(np.diff(aws,axis=1)**2))),
        'mapterhornOnAwsGridNeighborDifferenceRms': float(np.sqrt(np.mean(np.diff(reduced,axis=1)**2))),
        'mtGroundPixelMetres':40075016.68557849*math.cos(math.radians(lat))/(512*2**15)})
    if name in ('tryfan','riffelhorn'):
        hz = 16 if name == 'tryfan' else 17
        factor = 2 ** (hz-15)
        hx,hy = [math.floor(v) for v in tile_xy(lon,lat,hz)]
        high = tile('mapterhorn',hz,hx,hy)
        assert high is not None, 'Higher-level tile unavailable; inspect http-requests.json'
        xs=(hx%factor*512+np.arange(512)+.5)/factor-.5
        ys=(hy%factor*512+np.arange(512)+.5)/factor-.5
        xx,yy=np.meshgrid(xs,ys)
        residual=high-bilinear(mt,xx,yy)
        report['higherZoom'].append({'location':name,'z':hz,'x':hx,'y':hy,
            'groundPixelMetres':40075016.68557849*math.cos(math.radians(lat))/(512*2**hz),
            'minusInterpolatedZ15':stats(residual),'high':stats(high)})

# Small sparse-delivery and ocean probes, not a worldwide coverage survey.
for lon,lat,z in [(-25,40,12),(-25,40,15),(86.86,27.98,12),(86.86,27.98,15),(-3.999,53.115,18),(7.76121329,45.97910794,18)]:
    x,y=[math.floor(v) for v in tile_xy(lon,lat,z)]
    data=tile('mapterhorn',z,x,y)
    requests[-1]['elevationStats']=stats(data) if data is not None else None

# Inspect the documented western swissALTI3D coverage edge, not a presumed political border.
# Three short east-west transects, 5 m ground spacing. Coverage is candidate-source metadata;
# winner/blending masks are unavailable, so jumps are diagnostic rather than labelled seams.
transects=[]
for lat in (45.939,45.94,45.941):
    lon=7.6965; offsets=np.arange(-100,101,5,dtype=float)
    longitude=lon+offsets/(111320*math.cos(math.radians(lat)))
    heights=[]
    for lo in longitude:
        fx,fy=tile_xy(float(lo),lat,16);x,y=math.floor(fx),math.floor(fy)
        data=tile('mapterhorn',16,x,y)
        heights.append(None if data is None else float(bilinear(data,np.array((fx-x)*512-.5),np.array((fy-y)*512-.5))))
    values=np.array(heights,dtype=float)
    transects.append({'latitude':lat,'longitude':lon,'offsetMetres':offsets.tolist(),'heights':heights,
                      'maxAdjacent5mDifference':float(np.max(np.abs(np.diff(values)))),
                      'adjacent5mDifferences':np.diff(values).tolist()})
report['boundaryTransects']=transects
(OUT / 'measurements.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('requests','boundaryTransects')},indent=2))
print('REQUESTS',len(requests),'404',sum(r['status']==404 for r in requests))
print('BOUNDARY',[(r['latitude'],r['maxAdjacent5mDifference']) for r in transects])
