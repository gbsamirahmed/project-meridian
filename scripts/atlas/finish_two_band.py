"""Independent checks of retained terminal-experiment outputs; no terrain fit."""
import argparse
import heapq
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import two_band_transition as tb
from terrain_scale import stats
from analyze_regional_parents import sample_field
from analyze_two_band import samples


def spill_depth(a):
    """Eight-neighbour priority flood with patch perimeter as fixed outlets."""
    h,w=a.shape; out=a.copy(); seen=np.zeros(a.shape,bool); queue=[]
    for y,x in [(y,x) for y in range(h) for x in range(w) if y in [0,h-1] or x in [0,w-1]]:
        seen[y,x]=True; heapq.heappush(queue,(float(a[y,x]),y,x))
    while queue:
        height,y,x=heapq.heappop(queue)
        for dy in [-1,0,1]:
            for dx in [-1,0,1]:
                yy,xx=y+dy,x+dx
                if not(0<=yy<h and 0<=xx<w) or seen[yy,xx]:continue
                seen[yy,xx]=True;out[yy,xx]=max(height,a[yy,xx]);heapq.heappush(queue,(float(out[yy,xx]),yy,xx))
    return out-a


def direction(a):
    scores=[]
    for dy,dx in [(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1)]:
        scores.append((a-np.roll(np.roll(a,-dy,0),-dx,1))/np.hypot(dx,dy))
    scores=np.stack(scores);return np.argmax(scores,axis=0),np.max(scores,axis=0)>0


def main(data):
    out=Path(data)/tb.EXPERIMENT
    m=json.loads((out/'measurements.json').read_text()); f={k:np.load(out/(k+'.npy')) for k in m['arrayHashes']}
    for k,a in f.items():assert tb.sc.array_hash(a)==m['arrayHashes'][k]
    s,c,sb,cb,a,r,b,d=[f[k] for k in ['swiss','common','swissBroad','commonBroad','terrain','radius','b','d']]
    valid=f['valid']&(r>1500)&(r<4000)
    # Independent expansion of the four signed operator coefficients.
    expected=d*s+(1-d)*c+(b-d)*sb+(d-b)*cb
    closure=float(np.max(abs((a-expected)[valid])))
    assert closure<1e-9
    eps=.01
    def eval_at(rho):
        t=np.clip((rho-1500)/2500,0,1); u=np.clip((rho-3000)/1000,0,1)
        bw=1-10*t**3+15*t**4-6*t**5;dw=1-10*u**3+15*u**4-6*u**5
        return cb+bw*(sb-cb)+dw*(s-sb)+(1-dw)*(c-cb)
    derivative=(eval_at(r+eps)-eval_at(r-eps))/(2*eps)
    check=float(np.max(abs((derivative-f['induced'])[valid])))
    assert check<1e-8
    td,tdown=direction(a);sd,sdown=direction(s);cd,cdown=direction(c)
    diff=np.minimum((td-sd)%8,(sd-td)%8)*45
    curvature=lambda v:(np.roll(v,1,0)+np.roll(v,-1,0)+np.roll(v,1,1)+np.roll(v,-1,1)-4*v)/(6.64**2)
    safe=valid.copy();safe[[0,-1],:]=False;safe[:,[0,-1]]=False
    result={'operatorClosureIndependentMaxM':closure,'inducedDerivativeIndependentMaxDifference':check,
      'drainageDirectionChangeDegreesAgainstSwiss':stats(diff[safe&tdown&sdown]),
      'nonDescendingTWhereBothSourcesHaveDescendingNeighbour':int((safe&~tdown&sdown&cdown).sum()),
      'curvatureChangeAgainstSwissInverseMetres':stats((curvature(a)-curvature(s))[safe]),
      'interpretation':'D8 and five-point curvature are representation diagnostics, not hydrological correctness; elevations remain untouched.', 'flaggedMinimumPatches':[]}
    fig,axes=plt.subplots(4,2,figsize=(15,13),layout='constrained')
    for j,row in enumerate(m['extrema']['newMinimumLocations'][:8]):
        i=np.argmin((f['east']-row['east'])**2+(f['north']-row['north'])**2);y,x=np.unravel_index(i,a.shape)
        patch=(slice(y-32,y+33),slice(x-32,x+33));q={k:v[patch] for k,v in [('T',a),('S',s),('C',c)]}
        depths={k:spill_depth(v) for k,v in q.items()}
        item={**row,'radiusM':float(r[y,x]),'iceChangeProxy':bool(f['ice'][y,x]),
          'patchSizeMApprox':432,'fixedOutletSpillDepthAtFlagM':{k:float(v[32,32]) for k,v in depths.items()},
          'maximumSpillDepthWithin53MOfFlag':{k:float(np.max(v[24:41,24:41])) for k,v in depths.items()}}
        result['flaggedMinimumPatches'].append(item)
        ax=axes.ravel()[j];dist=(np.arange(65)-32)*6.64
        for k,v in q.items():ax.plot(dist,v[32],label=k)
        ax.set_title(f"flag {j+1}: r={r[y,x]:.0f}m; change={bool(f['ice'][y,x])}")
        ax.set_xlabel('east/west patch distance (approx m)');ax.set_ylabel('native/heterogeneous height (m)')
    axes.ravel()[0].legend();fig.savefig(out/'extrema-patch-profiles.png',dpi=125);plt.close(fig)
    tb.sp.save(out/'independent-checks.json',result)
    print(json.dumps(result,indent=2))


def hierarchy(data):
    out=Path(data)/tb.EXPERIMENT;t=tb.Transition(data)
    e,n,r,a=[np.load(out/(key+'.npy')) for key in ['east','north','radius','terrain']]
    valid=np.load(out/'valid.npy');report={}
    for z in [12,13]:
        x0,x1,y0,y1,shape,_=tb.sp.hierarchy(z);grid=np.zeros(shape)
        for y in range(y0,y1+1):
            for x in range(x0,x1+1):
                grid[(y-y0)*256:(y-y0+1)*256,(x-x0)*256:(x-x0+1)*256]=tb.rt.decode(t.tile('transition',z,x,y)[0])
        mx,my=t.forward.transform(e,n)
        gx=(mx+tb.rt.WORLD/2)/tb.rt.WORLD*256*2**z-.5
        gy=(tb.rt.WORLD/2-my)/tb.rt.WORLD*256*2**z-.5
        prediction=tb.sample_grid(grid,z,x0,y0,gx,gy);delta=a-prediction
        assert np.all(np.isfinite(prediction[valid&(r<4500)]))
        report[str(z)+'-to14']={}
        for lo,hi in [(0,1500),(1500,3000),(3000,4000),(4000,4500)]:
            report[str(z)+'-to14'][f'{lo}-{hi}']=stats(delta[valid&(r>=lo)&(r<hi)])
    tb.sp.save(out/'collar-lod.json',report)
    yy,xx=np.mgrid[:100,:100];ee=2620000+(xx+.125)*100;nn=1097000-(yy+.125)*100
    protected=np.hypot(ee-2625000,nn-1092000)<=1500;ee=ee[protected];nn=nn[protected]
    handoff={'common9ToDerived10':stats(samples(t,10,ee,nn)-samples(t,9,ee,nn)),
             'interpretation':'Unresolved common to derived low-level handoff; not an accuracy measurement'}
    tb.sp.save(out/'coarse-handoff.json',handoff)
    print(json.dumps(report,indent=2))


def sheets(folder):
    folder=Path(folder)
    groups={}
    for path in sorted(folder.glob('*.png')):
        if path.name.startswith('sheet-'):continue
        group=path.name.split('--')[0].split('-')[0];groups.setdefault(group,[]).append(path)
    for group,paths in groups.items():
        for start in range(0,len(paths),12):
            subset=paths[start:start+12];canvas=Image.new('RGB',(1440,((len(subset)+2)//3)*324),'white');draw=ImageDraw.Draw(canvas)
            for i,path in enumerate(subset):
                im=Image.open(path);im.thumbnail((480,300));x=(i%3)*480;y=(i//3)*324;canvas.paste(im,(x,y));draw.text((x+4,y+301),path.name[:65],fill='black')
            canvas.save(folder/f'sheet-{group}-{start//12}.jpg',quality=85)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path);p.add_argument('--sheets',type=Path);p.add_argument('--hierarchy',action='store_true');args=p.parse_args()
    if args.sheets:sheets(args.sheets)
    elif args.hierarchy:hierarchy(args.data)
    else:main(args.data)
