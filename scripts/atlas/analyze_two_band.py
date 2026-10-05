"""Fixed numerical tests of the terminal transition; no parameter search."""
from collections import deque
import json
from pathlib import Path
import numpy as np
import two_band_transition as tb
from terrain_scale import stats
from analyze_regional_parents import sample_field


def samples(t,z,e,n,strategy='transition'):
    x,y=t.forward.transform(e,n)
    gx=(x+tb.rt.WORLD/2)/tb.rt.WORLD*256*2**z-.5
    gy=(tb.rt.WORLD/2-y)/tb.rt.WORLD*256*2**z-.5
    ix,iy=np.floor(gx).astype(int),np.floor(gy).astype(int);wx,wy=gx-ix,gy-iy
    values=[]
    for dx,dy in [(0,0),(1,0),(0,1),(1,1)]:
        px,py=ix+dx,iy+dy;a=np.full(e.shape,np.nan)
        for tx,ty in sorted(set(zip(px//256,py//256))):
            body,_=t.tile(strategy,z,int(tx),int(ty));height=tb.rt.decode(body)
            m=(px//256==tx)&(py//256==ty);a[m]=height[py[m]%256,px[m]%256]
        values.append(a)
    a,b,c,d=values
    return (1-wy)*((1-wx)*a+wx*b)+wy*((1-wx)*c+wx*d)


def connected_length(mask,step):
    """Four-neighbour shortest-path extent witness, not a fitted physical feature."""
    visited=np.zeros(mask.shape,dtype=bool);components=0;longest=0;largest=0
    rows,cols=mask.shape
    for rr,cc in zip(*np.where(mask)):
        if visited[rr,cc]:continue
        components+=1;queue=deque([(rr,cc,0)]);visited[rr,cc]=True;members=[];last=(rr,cc)
        while queue:
            r,c,d=queue.popleft();members.append((r,c));last=(r,c)
            for r2,c2 in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                if 0<=r2<rows and 0<=c2<cols and mask[r2,c2] and not visited[r2,c2]:
                    visited[r2,c2]=True;queue.append((r2,c2,d+1))
        largest=max(largest,len(members))
        seen={last};queue=deque([(*last,0)])
        while queue:
            r,c,d=queue.popleft();longest=max(longest,d)
            for r2,c2 in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                if 0<=r2<rows and 0<=c2<cols and mask[r2,c2] and (r2,c2) not in seen:
                    seen.add((r2,c2));queue.append((r2,c2,d+1))
    return {'components':components,'largestCellCount':largest,'longestGraphDistanceLowerBoundM':float(longest*step),
            'method':'double BFS geodesic-diameter lower bound; no diagonal adjacency; centre ground spacing approximation'}


def extrema(a,valid):
    neighbors=[np.roll(np.roll(a,dy,0),dx,1) for dy in [-1,0,1] for dx in [-1,0,1] if dx or dy]
    safe=valid.copy()
    for dy in [-1,0,1]:
        for dx in [-1,0,1]:safe &= np.roll(np.roll(valid,dy,0),dx,1)
    safe[[0,-1],:]=False;safe[:,[0,-1]]=False
    lo=np.minimum.reduce(neighbors);hi=np.maximum.reduce(neighbors)
    return safe & (a<lo),safe & (a>hi),lo-a,a-hi


def run(data):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    t=tb.Transition(data);out=Path(data)/tb.EXPERIMENT;out.mkdir(parents=True,exist_ok=True)
    z=14;x0,x1,y0,y1,shape,_=tb.sp.hierarchy(z)
    fields={key:np.full(shape,np.nan) for key in ['terrain','common','swissBroad','commonBroad','radius','east','north','b','d']}
    swiss=t.fields[z]
    for y in range(y0,y1+1):
        for x in range(x0,x1+1):
            e,n,r,gx,gy=t.coordinates(z,x,y);a,b,d,_=t.values(z,x,y);c=t.common(z,x,y);sb,cb=t.broad(z,gx,gy)
            rs=slice((y-y0)*256,(y-y0+1)*256);cs=slice((x-x0)*256,(x-x0+1)*256)
            for key,val in [('terrain',a),('common',c),('swissBroad',sb),('commonBroad',cb),('radius',r),('east',e),('north',n),('b',b),('d',d)]:fields[key][rs,cs]=val
            t.tile('transition',z,x,y)
    r=fields['radius'];a=fields['terrain'];c=fields['common'];sb=fields['swissBroad'];cb=fields['commonBroad']
    mixed=(r>1500)&(r<4000);valid=np.isfinite(swiss)&np.isfinite(sb)&np.isfinite(cb)
    induced=np.zeros(shape)
    induced[mixed]=(sb-cb)[mixed]*tb.weight_derivative(r[mixed],1500,2500)+((swiss-sb)-(c-cb))[mixed]*tb.weight_derivative(r[mixed],3000,1000)
    rs=swiss-sb;rc=c-cb
    # Fixed retained classification: diagnostic proxy, not dated per-cell ice change.
    iy=np.clip(((1097000-fields['north'])/25).astype(int),0,399);ix=np.clip(((fields['east']-2620000)/25).astype(int),0,399)
    ice=t.retained['glacier250Mask'][iy,ix];stable=t.retained['primaryMask'][iy,ix];slope=t.retained['slope'][iy,ix]
    report={'baseline':'53b9efbc9e1e2d9393291a1b3fe90abcfcf3f7d0','buildIdentity':t.config['identity'],'specSha256':t.config['specSha256'],
            'protectedUnencodedDifference':stats((a-swiss)[valid&(r<=1500)]),
            'outsideUnencodedDifference':stats((a-c)[r>=4000]),'weights':{'r1500':list(map(float,tb.weights(np.array(1500.)))),
                'r3000':list(map(float,tb.weights(np.array(3000.)))),'r4000':list(map(float,tb.weights(np.array(4000.))))},
            'inducedGradient':{},'radialBands':{},'extrema':{},'profiles':{},'lod':{},'boundaries':{},'arrayHashes':{}}
    for key,mask in [('all',mixed&valid),('iceChange',mixed&valid&ice),('nonIce',mixed&valid&~ice),('stableCandidates',mixed&valid&stable),('steepNonIce',mixed&valid&~ice&(slope>=45))]:
        report['inducedGradient'][key]={'signed':stats(induced[mask]),'absolute':stats(abs(induced[mask])),
             'above005Fraction':float(np.mean(abs(induced[mask])>.05)),'above010Fraction':float(np.mean(abs(induced[mask])>.10))}
    report['inducedGradient']['connectedAbove010']=connected_length(mixed&valid&(abs(induced)>.10),6.64)
    for lo,hi in [(0,1500),(1500,2000),(2000,2500),(2500,3000),(3000,3500),(3500,4000),(4000,4500)]:
        m=valid&(r>=lo)&(r<hi)
        report['radialBands'][f'{lo}-{hi}']={'terrainMinusSwiss':stats((a-swiss)[m]),'terrainMinusCommon':stats((a-c)[m]),
            'broadContribution':stats((fields['b']*(sb-cb))[m]),'regionalDetailContribution':stats((fields['d']*rs)[m]),
            'detailWeight':stats(fields['d'][m]),'broadWeight':stats(fields['b'][m])}
    mins,maxs,depth,height=extrema(a,valid&mixed)
    smin,smax,_,_=extrema(swiss,valid);cmin,cmax,_,_=extrema(c,valid)
    newmin=mins&~smin&~cmin;newmax=maxs&~smax&~cmax
    report['extrema']={'newMinimumCellCandidates':int(newmin.sum()),'newMaximumCellCandidates':int(newmax.sum()),
        'minimumProminenceOneRing':stats(depth[newmin]),'maximumProminenceOneRing':stats(height[newmax]),
        'belowBothSourceHeights':stats((np.minimum(swiss,c)-a)[mixed&valid&(a<np.minimum(swiss,c))]),
        'aboveBothSourceHeights':stats((a-np.maximum(swiss,c))[mixed&valid&(a>np.maximum(swiss,c))]),
        'interpretation':'Same-cell eight-neighbour strict extrema are flags, not proof of a new landform. Signed two-band operator need not be inside the pointwise source envelope.'}
    for label,mask in [('newMinimum',newmin),('newMaximum',newmax)]:
        index=np.flatnonzero(mask)
        score=depth if label=='newMinimum' else height
        index=sorted(index,key=lambda i:score.ravel()[i],reverse=True)[:8]
        report['extrema'][label+'Locations']=[{'east':float(fields['east'].ravel()[i]),'north':float(fields['north'].ravel()[i]),'oneRingProminence':float(score.ravel()[i])} for i in index]
    # Dense fixed radial profiles: all directions, no selection against results.
    distances=np.arange(1000,4501,5.)
    for angle in range(0,360,15):
        theta=np.deg2rad(angle);e=2625000+distances*np.sin(theta);n=1092000+distances*np.cos(theta)
        row={'radiusM':distances.tolist(),'angleDegreesClockwiseFromNorth':angle}
        for key,grid in [('terrain',a),('swiss',swiss),('common',c),('swissBroad',sb),('commonBroad',cb),('induced',induced)]:
            val=sample_field(grid,z,e,n);row[key]=[float(v) if np.isfinite(v) else None for v in val]
        report['profiles'][str(angle)]=row
    # Local analytic band-boundary test removes legitimate local source slope:
    # branch difference from the d=1 formula at r=3000, S at1500, C at4000.
    for radius in [1500,3000,4000]:
        deltas=[];adjacent=[]
        for angle in range(0,360,5):
            theta=np.deg2rad(angle);rho=radius+np.array([-2.,-.5,0,.5,2.])
            e=2625000+rho*np.sin(theta);n=1092000+rho*np.cos(theta)
            s=sample_field(swiss,z,e,n);cc=sample_field(c,z,e,n);ssb=sample_field(sb,z,e,n);ccb=sample_field(cb,z,e,n)
            tt,b,d,_=tb.compose(s,cc,ssb,ccb,rho)
            reference=s if radius==1500 else cc if radius==4000 else s+(b-1)*(ssb-ccb)
            deltas.append((tt-reference)[3]-(tt-reference)[1]);adjacent.append(tt[3]-tt[1])
        report['boundaries'][str(radius)]={'introducedInterceptProxyHalfMetreSides':stats(np.array(deltas)),
                                         'actualOneMetreHeightChangeIncludingTerrainSlope':stats(np.array(adjacent))}
    yy,xx=np.mgrid[:100,:100];e=2620000+(xx+.125)*100;n=1097000-(yy+.125)*100
    # Exact previous705 sample locations are source 25m cell centres every fourth cell.
    protected=np.hypot(e-2625000,n-1092000)<=1500;e=e[protected];n=n[protected]
    report['protectedSamples']=int(len(e));previous=None
    for level in range(10,19):
        val=samples(t,level,e,n)
        if previous is not None:report['lod'][f'{level-1}-{level}']=stats(val-previous)
        previous=val
        if level>=14:
            reference=samples(t,level,e,n,'hard')
            report.setdefault('protectedFineDeliveredDifference',{})[str(level)]=stats(val-reference)
    report['fineDetailEquations']={'dEqualsOneThrough3000':bool(np.all(fields['d'][r<=3000]==1)),
        'dEqualsZeroFrom4000':bool(np.all(fields['d'][r>=4000]==0)),
        'operatorClosureMax':float(np.nanmax(abs((a-(fields['d']*swiss+(1-fields['d'])*c+(fields['b']-fields['d'])*(sb-cb)))[mixed&valid])))}
    fig,axes=plt.subplots(2,3,figsize=(15,10),layout='constrained')
    for ax,(name,grid,lo,hi) in zip(axes.ravel(),[('T−Swiss',a-swiss,-80,80),('T−common',a-c,-80,80),('Induced radial grade',induced,-.10,.10),('Broad weight',fields['b'],0,1),('Detail weight',fields['d'],0,1),('T outside input envelope',np.where(a<np.minimum(swiss,c),a-np.minimum(swiss,c),np.where(a>np.maximum(swiss,c),a-np.maximum(swiss,c),0)),-20,20)]):
        im=ax.imshow(np.where(valid,grid,np.nan),cmap='RdBu_r',vmin=lo,vmax=hi);ax.set_title(name);ax.axis('off')
        ax.contour(r,levels=[1500,3000,4000],colors='black',linewidths=.4);fig.colorbar(im,ax=ax,shrink=.6)
    fig.savefig(out/'numerical-fields.png',dpi=130);plt.close(fig)
    fig,axes=plt.subplots(4,2,figsize=(14,12),layout='constrained')
    for row,angle in enumerate([0,90,180,270]):
        q=report['profiles'][str(angle)]
        for key in ['terrain','swiss','common']:axes[row,0].plot(q['radiusM'],q[key],label=key)
        axes[row,0].set_title(f'{angle}° clockwise from north')
        axes[row,1].plot(q['radiusM'],q['induced'],label='introduced radial grade');axes[row,1].axhline(.05,color='red');axes[row,1].axhline(-.05,color='red')
        for ax in axes[row]:
            for cut in [1500,3000,4000]:ax.axvline(cut,lw=.4,color='black')
    axes[0,0].legend();fig.savefig(out/'radial-profiles.png',dpi=130);plt.close(fig)
    for key,grid in {**fields,'swiss':swiss,'induced':induced,'valid':valid,'ice':ice,'stable':stable}.items():
        np.save(out/(key+'.npy'),grid,allow_pickle=False);report['arrayHashes'][key]=tb.sc.array_hash(grid)
    tb.sp.save(out/'measurements.json',report)
    tb.sp.save(out/'inventory.json',t.inventory())
    print(json.dumps({'buildIdentity':t.config['identity'],'induced':report['inducedGradient']['all'],
                      'connected':report['inducedGradient']['connectedAbove010'],'protected':report['protectedSamples'],
                      'lod13-14':report['lod']['13-14'],'extrema':{k:v for k,v in report['extrema'].items() if isinstance(v,int)}}),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--data',type=Path,required=True);run(parser.parse_args().data)
