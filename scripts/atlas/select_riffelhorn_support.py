"""Official selection metadata and SHA-256 verification for one fixed extent."""
import argparse,json
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from pyproj import Transformer
import numpy as np
import riffelhorn_support as sp
import riffelhorn_terrain as rt

def select(data):
    t=Transformer.from_crs(2056,4326,always_xy=True,allow_ballpark=False)
    e,n=np.meshgrid(np.linspace(sp.BOUNDS[0],sp.BOUNDS[2],21),np.linspace(sp.BOUNDS[1],sp.BOUNDS[3],21));lon,lat=t.transform(e,n)
    bbox=[float(lon.min()),float(lat.min()),float(lon.max()),float(lat.max())]
    url='https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissalti3d/items?bbox='+','.join(map(str,bbox))+'&limit=1000';features=[]
    while url:
        with urlopen(Request(url,headers={'User-Agent':'Meridian-bounded-Swiss-support-evaluation'}),timeout=60)as r:page=json.load(r)
        features.extend(page['features']);url=next((x['href']for x in page.get('links',[])if x['rel']=='next'),None)
    selected=[]
    for x in range(2620,2630):
        for y in range(1087,1097):
            id=f'swissalti3d_2024_{x}-{y}';rows=[f for f in features if f['id']==id]
            if len(rows)!=1:raise ValueError('Expected exactly one 2024 item: '+id)
            f=rows[0];name=f'{id}_0.5_2056_5728.tif';a=f['assets'][name]
            selected.append({'id':id,'assetName':name,'url':a['href'],'officialMetadata':f,'bounds':[x*1000,y*1000,(x+1)*1000,(y+1)*1000]})
    plan={'bounds':list(sp.BOUNDS),'geographicEnvelope':bbox,'protectedInterior':{'centreLV95':list(sp.CENTRE),'radiusMetres':sp.RADIUS,'polygonSides':64},'minimumSupportMetres':3500,'priorDiagnosticMaximumMetres':2500,'sourceRelease':'2024','accessDate':datetime.now(timezone.utc).date().isoformat(),'selection':selected}
    p=data/sp.SOURCE/'metadata/selection-plan.json';sp.save(p,plan);print('SELECTED',len(selected),p)

def verify_official(data):
    path=data/sp.SOURCE/'metadata/selection-plan.json';plan=json.loads(path.read_text(encoding='utf8'));source=sp.source_record(data)
    rows={a['assetName']:a for a in plan['selection']}
    for a in source['assets']:
        row=rows[a['path'].split('/')[-1]];asset=row['officialMetadata']['assets'][row['assetName']]
        multihash=asset['checksum:multihash'].lower()
        if len(multihash)!=68 or not multihash.startswith('1220')or multihash[4:]!=a['sha256']:raise ValueError('Official checksum mismatch: '+a['path'])
    record={'sourceIdentity':source['identity'],'verifiedAssetCount':len(source['assets']),'officialChecksum':'STAC checksum:multihash SHA-256, prefix 1220','allMatched':True,'selectionMetadataSha256':rt.digest(path),'sourceMetadataAccessDate':plan['accessDate'],'verificationDate':datetime.now(timezone.utc).date().isoformat()}
    sp.save(sp.REPO/'docs/atlas/riffelhorn-support-official-verification.json',record);print('OFFICIAL VERIFIED',len(source['assets']))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['select','verify-official']);args=p.parse_args();data=rt.resolve_storage_roots(require_data=True).data
    if args.command=='select':select(data)
    else:verify_official(data)
