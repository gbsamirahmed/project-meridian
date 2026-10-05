"""Verify sparse output/mask hashes and pure endpoint cells against inputs."""
import argparse
import json
from pathlib import Path
import numpy as np
import two_band_transition as tb
from terrain_scale import stats


def verify(data):
    t=tb.Transition(data);out=Path(data)/tb.EXPERIMENT
    previous=out/'output-verification.json';ledger=out/'verified-inventory.json'
    checked={}
    report={'tiles':{},'protectedCellsByZoom':{},'outsideCellsByZoom':{},'allMaskWeightsVerified':True,'maximumEncodingErrorM':0}
    if previous.exists() and ledger.exists():
        report=json.loads(previous.read_text());old=json.loads(ledger.read_text())
        assert old['identity']==report['inventoryIdentity'] and old['config']==t.config
        checked={r['path']:(r['sha256'],r['maskSha256']) for r in old['files']}
    manifest=t.inventory();report['inventoryIdentity']=manifest['identity'];report['sourceInputs']=t.verification
    for row in manifest['files']:
        if row['strategy']!='transition':continue
        if checked.get(row['path'])==(row['sha256'],row['maskSha256']):continue
        z,x,y=[row[k] for k in ['z','x','y']];body=(t.out/row['path']).read_bytes();a=tb.rt.decode(body)
        e,n,r,_,_=t.coordinates(z,x,y)
        report['tiles'][str(z)]=report['tiles'].get(str(z),0)+1
        report['maximumEncodingErrorM']=max(report['maximumEncodingErrorM'],row['maxQuantizationM'])
        if z>=12:
            b,d=tb.weights(r)
            with np.load(t.out/row['maskPath']) as m:
                np.testing.assert_array_equal(m['broadWeight'],b);np.testing.assert_array_equal(m['detailWeight'],d)
                assert np.all(m['labels'][r<=1500]==1) and np.all(m['labels'][r>=4000]==0)
            outer=r>=4000
            if np.any(outer):
                c=tb.rt.decode(tb.rt.encode(t.common(z,x,y)))
                delta=a[outer]-c[outer];assert np.all(delta==0)
                report['outsideCellsByZoom'][str(z)]=report['outsideCellsByZoom'].get(str(z),0)+int(outer.sum())
            inner=r<=1500
            if np.any(inner):
                s=tb.rt.decode(tb.rt.encode(t.regional(z,x,y)))
                assert np.all(a[inner]==s[inner])
                report['protectedCellsByZoom'][str(z)]=report['protectedCellsByZoom'].get(str(z),0)+int(inner.sum())
    assert report['maximumEncodingErrorM']<=1/512+1e-8
    # Explicit mean footprint support at diagnostic parents, distinct from b/d.
    report['parentSupport']={}
    folder=t.out/'parent-support';folder.mkdir(exist_ok=True)
    for row in manifest['files']:
        if row['strategy']!='transition' or row['z'] not in [10,11]:continue
        z,x,y=[row[k] for k in ['z','x','y']];factor=2**(12-z)
        support=np.zeros((256,256))
        for dy in range(factor):
            for dx in range(factor):
                _,_,r,_,_=t.coordinates(12,x*factor+dx,y*factor+dy)
                support[dy*256//factor:(dy+1)*256//factor,dx*256//factor:(dx+1)*256//factor]=(r<4000).reshape(256//factor,factor,256//factor,factor).mean(axis=(1,3))
        path=folder/f'{z}-{x}-{y}.npz'
        np.savez_compressed(path,regionalOperatorFootprintFraction=support,commonInputSupportFraction=np.ones((256,256)))
        report['parentSupport'][path.name]={'sha256':tb.rt.digest(path),'partialCells':int(((support>0)&(support<1)).sum()),'regionalRequiredCells':int((support>0).sum())}
    report['parentSupportMeaning']='Fraction of z12 descendant centres requiring regional operator; all required regional/broad cells passed strict support preflight. Not confidence, not equality with mean b/d. Common input complete everywhere delivered.'
    tb.sp.save(out/'output-verification.json',report);tb.sp.save(ledger,manifest)
    print(json.dumps({k:v for k,v in report.items() if k not in ['sourceInputs','parentSupport']},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);verify(p.parse_args().data)
