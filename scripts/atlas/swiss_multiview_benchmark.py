"""Metadata-only Alpine benchmark discovery; offline retained inputs, no aerial acquisition."""
import csv,json,math,sys,pyproj,matplotlib
from datetime import datetime
from pathlib import Path
import numpy as np,rasterio
from matplotlib.path import Path as Poly
from pyproj import Transformer

import hashlib,re

def verify_inputs(root):
    manifest=json.loads((root/'input-manifest.json').read_text(encoding='utf8'))
    for item in manifest['files']:
        path=root/item['file']
        if path.parent!=root or not path.is_file(): raise ValueError('Missing/invalid retained input')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Retained input hash mismatch: '+item['file'])
    return manifest

def normals(height,spacing):
    h=np.asarray(height,dtype=float)
    if spacing<=0 or h.ndim!=2 or not np.isfinite(h).all():raise ValueError('Invalid terrain')
    gy,gx=np.gradient(h,spacing,spacing)
    stretch=np.sqrt(1+gx*gx+gy*gy)
    return np.stack((-gx,gy,np.ones(h.shape)),axis=-1)/stretch[:,:,None],stretch

def incidence_vectors(normal,vectors):
    v=np.asarray(vectors,dtype=float);length=np.linalg.norm(v,axis=-1)
    if not np.isfinite(v).all() or np.any(length==0):raise ValueError('Invalid view vectors')
    n=np.asarray(normal,dtype=float)
    if n.shape[-1]!=3 or not np.isfinite(n).all() or not np.allclose(np.linalg.norm(n,axis=-1),1,atol=1e-6):raise ValueError('Expected unit normals')
    mu=np.sum(n*v/length[...,None],axis=-1)
    return mu,np.degrees(np.arccos(np.clip(mu,-1,1)))

def rotation(omega,phi,kappa):
    # HxMap-compatible cam-to-world Rx Ry Rz; radians. Incidence does not depend on OPK.
    if not all(math.isfinite(q) for q in (omega,phi,kappa)):raise ValueError('Invalid angles')
    co,so,cp,sp,ck,sk=np.cos(omega),np.sin(omega),np.cos(phi),np.sin(phi),np.cos(kappa),np.sin(kappa)
    return np.array([[1,0,0],[0,co,-so],[0,so,co]])@np.array([[cp,0,sp],[0,1,0],[-sp,0,cp]])@np.array([[ck,-sk,0],[sk,ck,0],[0,0,1]])

def camera_plane(points,centre,matrix,focal=107):
    if focal<=0 or np.asarray(matrix).shape!=(3,3) or not np.allclose(matrix.T@matrix,np.eye(3),atol=1e-8):raise ValueError('Invalid camera calibration')
    q=(np.asarray(points)-centre)@matrix
    if np.any(q[...,2]>=0):raise ValueError('Point is behind camera plane')
    return -focal*q[...,:2]/q[...,2,None]

def tangent_sampling(points,normal,centre,matrix,focal=107,pixel_mm=.00376):
    """Local pinhole/composite projection Jacobian. Sampling proxy, not observation accuracy."""
    points=np.asarray(points);normal=np.asarray(normal);q=(points-centre)@matrix
    axis=np.broadcast_to([0.,0.,1.],normal.shape).copy()
    axis[np.abs(normal[:,2])>.9]=[1,0,0]
    t1=np.cross(normal,axis);t1/=np.linalg.norm(t1,axis=1)[:,None]
    t2=np.cross(normal,t1);basis=np.stack((t1,t2),axis=-1)
    j=np.stack([-focal*(matrix[:,i]*q[:,2,None]-q[:,i,None]*matrix[:,2])/q[:,2,None]**2/pixel_mm for i in (0,1)],axis=1)
    sv=np.linalg.svd(j@basis,compute_uv=False)
    return 1/sv[:,1],1/sv[:,0]

def parse_gori(text):
    keys=('x0','y0','z0','omega','phi','kappa','focal','ppx','ppy','ux','vy','lines','samples')
    result={}
    for k in keys:
        match=re.search(r'(?m)^\s*'+k+r'=([-+0-9.]+);',text)
        if match is None:raise ValueError('Missing GORI field: '+k)
        result[k]=float(match.group(1))
    if not all(math.isfinite(q) for q in result.values()):raise ValueError('Invalid GORI')
    if 'LHN95' not in text or 'EPSG:2056' not in text:raise ValueError('Unexpected reference')
    return result

def los_clearance(profile,camera_height,target_height):
    distance=np.array([q['dist'] for q in profile]);ground=np.array([q['alts']['DTM2'] for q in profile])
    if len(distance)<2 or distance[-1]<=0 or not np.all(np.diff(distance)>=0):raise ValueError('Invalid profile')
    ray=target_height+distance/distance[-1]*(camera_height-target_height)
    # 0-10 m self-intersection neighbourhood is excluded, reported as unresolved.
    return float(np.min((ray-ground)[distance>=10]))

def percentile(values):
    return dict(zip(('p05','median','p95'),map(float,np.percentile(values,[5,50,95]))))

def discovery_tiles(root,frames):
    """Retained coarse transects choose exactly three tiles, without manual map selection."""
    candidates=[];receipts=json.loads((root/'coarse-receipts.json').read_text())
    if len(receipts)!=14:raise ValueError('Expected fixed fourteen transects')
    for receipt in receipts:
        profile=json.loads((root/receipt['file']).read_text())
        if len(profile)!=101:raise ValueError('Unexpected coarse sampling')
        xy=np.array([[q['easting'],q['northing']] for q in profile])
        z=np.array([q['alts']['DTM2'] for q in profile])
        slope=np.degrees(np.arctan(abs(np.gradient(z,130))))
        coverage=np.sum([f['poly'].contains_points(xy) for f in frames],axis=0)
        for point,sl,count in zip(xy,slope,coverage):
            if count>=2:candidates.append((float(sl),tuple(point),f'{int(point[0]//1000)}-{int(point[1]//1000)}'))
    candidates.sort(key=lambda q:(-q[0],q[1]))
    tiles=[]
    for _,_,tile in candidates:
        if tile not in tiles:tiles.append(tile)
        if len(tiles)==3:return tiles
    raise ValueError('Insufficient bounded terrain candidates')

def draw_map(out,chosen,frames,root):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    x,y,x1,y1=chosen['bounds']
    with rasterio.open(root/(chosen['tile']+'.tif')) as ds:
        h=ds.read(1);ns,st=normals(h,2);bb=ds.bounds
        fig,ax=plt.subplots(figsize=(8,7))
        im=ax.imshow(np.degrees(np.arccos(ns[:,:,2])),extent=[bb.left,bb.right,bb.bottom,bb.top],vmin=0,vmax=85,cmap='terrain')
        for role,color in [('best','tab:blue'),('poor','tab:red')]:
            identity=chosen['pair'][role];f=next(q for q in frames if q['row']['feature_id']==identity);ring=f['poly'].vertices;cam=f['cam']
            ax.plot(ring[:,0],ring[:,1],color=color,lw=1,label=role+' footprint / '+identity.split('_')[-2])
            ax.scatter(cam[0],cam[1],color=color,marker='^');ax.plot([x+30,cam[0]],[y+30,cam[1]],color=color,ls='--')
        ax.add_patch(Rectangle((x,y),60,60,fill=False,color='black',lw=2,label='frozen 60 m target'))
        ax.set_xlim(x-450,x+850);ax.set_ylim(y-1000,y+400);ax.set_aspect('equal');ax.ticklabel_format(style='plain',useOffset=False)
        ax.set_xlabel('LV95 easting (m)');ax.set_ylabel('LV95 northing (m)');ax.set_title('2026 frame-camera benchmark: published footprints and derived sight rays')
        ax.legend(loc='upper right',fontsize=8);fig.colorbar(im,ax=ax,label='Native 2 m heightfield slope (degrees)')
        fig.tight_layout();fig.savefig(out/'benchmark-map.png',dpi=150,metadata={'Software':'Meridian metadata diagnostic'});plt.close(fig)

def main():
    import argparse
    parser=argparse.ArgumentParser(description="Offline frame-centre/terrain benchmark screening; never acquires aerial pixels")
    parser.add_argument("--metadata",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    p=args.metadata
    out=args.out
    out.mkdir(parents=True,exist_ok=True)
    verify_inputs(p)
    rows=list(csv.DictReader((p/'catalogue.csv').read_text(encoding='utf-8-sig').splitlines(),delimiter=';'))
    r={x['feature_id']:x for x in rows}
    if len(r)!=len(rows):raise ValueError('Duplicate catalogue identity')
    for row in rows:
        for key in ('easting','northing','altitude','omega','phi','kappa','focal_length','pixel_size'):
            if not math.isfinite(float(row[key])):raise ValueError('Invalid catalogue number')
        datetime.fromisoformat(row['capture_time'])
    freeze=json.loads((p/'pre-discovery-freeze.json').read_text())
    if freeze['patchSideMetres']!=60 or freeze['minimumMedianSlopeDegrees']!=50 or freeze['minimumDifficultCellFraction']!=.25 or freeze['materialGate']!={'maximumCandidateIncidenceDegrees':60,'minimumFractionDifficultCellsImproved':.5,'minimumAngularSeparationDegrees':15}:raise ValueError('Frozen criteria changed')
    frames=json.loads((p/'august-complete.json').read_text());tr=Transformer.from_crs(4326,2056,always_xy=True)
    for f in frames:
        if f['geometry']['type']!='Polygon' or len(f['geometry']['coordinates'])!=1:raise ValueError('Expected single-ring footprint')
        ring=np.asarray(f['geometry']['coordinates'][0],dtype=float)
        if ring.ndim!=2 or ring.shape[1]!=2 or len(ring)<4 or not np.isfinite(ring).all():raise ValueError('Invalid footprint')
        f['row']=r[f['id'].removeprefix('lubis-luftbilder_digital_')]
        f['poly']=Poly(np.column_stack(tr.transform(*ring.T)))
        f['cam']=np.array([float(f['row'][k]) for k in ('easting','northing','altitude')])
    allpatch=[];short=[];screened=0
    tiles=discovery_tiles(p,frames)
    for tile in tiles:
     with rasterio.open(p/(tile+'.tif')) as ds:
      h=ds.read(1).astype(float);norm,st=normals(h,2)
      a,b=map(lambda q:int(q)*1000,tile.split('-'));passing=[]
      for x in range(a+20,a+921,60):
       for y in range(b+20,b+921,60):
        screened+=1;rr,cc=ds.index(x,y+60);rr=int(rr);cc=int(cc);hs=h[rr:rr+30,cc:cc+30];n=norm[rr:rr+30,cc:cc+30].reshape(-1,3);s=st[rr:rr+30,cc:cc+30].ravel();sl=np.degrees(np.arccos(n[:,2]));difficult=s>2
        if np.median(sl)<50 or np.mean(difficult)<.25:continue
        xx,yy=np.meshgrid(x+1+np.arange(30)*2,y+59-np.arange(30)*2);points=np.column_stack((xx.ravel(),yy.ravel()));xyz=np.column_stack((points,hs.ravel()));views=[]
        for f in frames:
         if not np.all(f['poly'].contains_points(points)):continue
         v=f['cam']-xyz;mu,inc=incidence_vectors(n,v);centre=f['cam']-xyz.mean(axis=0);direction=centre/np.linalg.norm(centre)
         views.append({'id':f['row']['feature_id'],'line':f['row']['line_id'],'medianIncidence':float(np.median(inc)),'goodDifficultFraction':float(np.mean(inc[difficult]<=60)),'direction':direction.tolist(),'viewAzimuth':float(np.degrees(np.arctan2(centre[0],centre[1]))%360),'viewElevation':float(np.degrees(np.arcsin(direction[2]))),'medianFactor':float(np.median(np.divide(1,mu,out=np.full(mu.shape,1e9),where=mu>0)))})
        pairs=[]
        for best in views:
         if best['goodDifficultFraction']<.5:continue
         for poor in views:
          sep=float(np.degrees(np.arccos(np.clip(np.dot(best['direction'],poor['direction']),-1,1))))
          if sep<15 or poor['medianIncidence']<=best['medianIncidence']:continue
          pairs.append({'best':best['id'],'poor':poor['id'],'separation':sep,'contrast':poor['medianIncidence']-best['medianIncidence'],'sameLine':best['line']==poor['line']})
        rec={'tile':tile,'bounds':[x,y,x+60,y+60],'centre':[x+30,y+30,float(np.mean(hs))],'medianSlope':float(np.median(sl)),'slopeP95':float(np.percentile(sl,95)),'stretchMedian':float(np.median(s)),'stretchP95':float(np.percentile(s,95)),'normalMean':n.mean(axis=0).tolist(),'aspectMedian':float(np.median(np.degrees(np.arctan2(n[:,0],n[:,1]))%360)),'difficultFraction':float(np.mean(difficult)),'views':views,'pairs':sorted(pairs,key=lambda q:(not q['sameLine'],-q['contrast'],q['best'],q['poor']))}
        allpatch.append(rec)
        if pairs:passing.append(rec)
      print(tile,'steep',sum(q['tile']==tile for q in allpatch),'passing',len(passing))
      if passing:
       passing.sort(key=lambda q:(not q['pairs'][0]['sameLine'],q['bounds']));short.append(passing[0])
    (out/'screened-patches.json').write_text(json.dumps(allpatch,sort_keys=True,indent=2),encoding='utf8',newline='\n');(out/'shortlist.json').write_text(json.dumps({'screened':screened,'steep':len(allpatch),'shortlist':short},sort_keys=True,indent=2),encoding='utf8',newline='\n')
    summaries=[]
    for candidate in short:
        tile=candidate['tile'];pair=candidate['pairs'][0];views=[]
        with rasterio.open(p/(tile+'.tif')) as ds:
            h=ds.read(1).astype(float);ns,stretch=normals(h,2)
            x,y,x1,y1=candidate['bounds'];rr,cc=map(int,ds.index(x,y1))
            normal=ns[rr:rr+30,cc:cc+30].reshape(-1,3)
            ss=stretch[rr:rr+30,cc:cc+30].ravel()
            xx,yy=np.meshgrid(x+1+np.arange(30)*2,y1-1-np.arange(30)*2)
            points=np.column_stack((xx.ravel(),yy.ravel(),h[rr:rr+30,cc:cc+30].ravel()))
            np.save(out/(tile+'-normals.npy'),normal);np.save(out/(tile+'-points.npy'),points)
            aspect=np.degrees(np.arctan2(normal[:,0],normal[:,1]))%360
            circ=float(np.degrees(np.arctan2(normal[:,0].mean(),normal[:,1].mean()))%360)
            offsets=(aspect-circ+180)%360-180
            for role in ('best','poor'):
                identity=pair[role];row=r[identity];centre=np.array([float(row[k]) for k in ('easting','northing','altitude')])
                frame=next(f for f in frames if f['row']['feature_id']==identity)
                if frame['properties']['datetime']!=row['capture_time']+'Z':raise ValueError('Acquisition timestamp mismatch')
                published=parse_gori((p/(identity+'.txt')).read_text(encoding='utf8'))
                for key,gkey in [('easting','x0'),('northing','y0'),('altitude','z0')]:
                    if abs(float(row[key])-published[gkey])>1e-6:raise ValueError('GORI centre disagrees')
                for key in ('omega','phi','kappa'):
                    if abs(np.radians(float(row[key]))-published[key])>6e-9:raise ValueError('GORI angular-unit crosscheck fails')
                if abs(published['focal']-107)>1e-6 or abs(published['ux']-1/.00376)>1e-5 or published['vy']!=-published['ux']:
                    raise ValueError('Composite camera calibration disagrees')
                M=rotation(*(published[k] for k in ('omega','phi','kappa')))
                footprint=np.column_stack(tr.transform(*np.array(frame['geometry']['coordinates'][0]).T))
                heights=json.loads((p/(identity+'-footprint-heights.json')).read_text())
                hxy=np.array([[q['easting'],q['northing']] for q in heights]);fh=np.array([heights[np.argmin(np.linalg.norm(hxy-pt,axis=1))]['alts']['DTM2'] for pt in footprint])
                ratios=camera_plane(np.column_stack((footprint,fh)),centre,M)/np.array([31520,13440])/.00376*2
                edge=np.max(abs(ratios),axis=1)
                if not np.all((edge>.97)&(edge<1.02)):raise ValueError('Published footprint contradicts projection')
                patchuv=camera_plane(points,centre,M)/np.array([31520,13440])/.00376*2
                target_inside=bool(np.max(abs(patchuv))<1)
                mu,inc=incidence_vectors(normal,centre-points)
                major,minor=tangent_sampling(points,normal,centre,M)
                factors=np.divide(1,mu,out=np.full(mu.shape,np.inf),where=mu>0)
                base=next(v for v in candidate['views'] if v['id']==identity)
                clearance=[];delta=[]
                for k in range(9):
                    profile=json.loads((p/f'los-{tile}-{role}-{k}.json').read_text())
                    point=profile[0];height=float(next(ds.sample([(point['easting'],point['northing'])]))[0])
                    delta.append(point['alts']['DTM2']-height)
                    # Anchor ray at the frozen tile, not potentially interpolated service first height.
                    clearance.append(los_clearance(profile,float(row['altitude']),height))
                sensitivity=[]
                for perturb in (-5,0,5):
                    c=centre.copy();c[2]+=perturb
                    _,ia=incidence_vectors(normal,c-points)
                    sensitivity.append({'cameraHeightPerturbationMetres':perturb,'goodDifficultFraction':float(np.mean(ia[ss>2]<=60)),'medianIncidence':float(np.median(ia))})
                views.append({**base,'role':role,'acquisitionUTC':frame['properties']['datetime'],'published':row,'gori':published,'incidenceDegrees':percentile(inc),'supportFactor':percentile(factors),'tangentMetresPerCompositePixelFrontfaces':{'major':percentile(major[mu>0]),'minor':percentile(minor[mu>0])},
                    'footprintProjectionEdgeRange':[float(edge.min()),float(edge.max())],'maximumTargetImageExtentRatio':float(abs(patchuv).max()),'calibratedTargetInside':target_inside,'calibratedTargetInsideFraction':float(np.mean(np.max(abs(patchuv),axis=1)<1)),
                    'losSamples':9,'losSupported':sum(q>=-2 for q in clearance),'losMinimumClearanceMetres':min(clearance),
                    'profileNativeStartDeltaMetres':[min(delta),max(delta)],'heightReferenceSensitivity':sensitivity,
                    'backfacingFraction':float(np.mean(mu<=0))})
        summaries.append({k:candidate[k] for k in ('tile','bounds','centre','medianSlope','slopeP95','stretchMedian','stretchP95','normalMean','difficultFraction')}|
            {'aspectCircularMeanDegrees':circ,'aspectOffsetsDegrees':percentile(offsets),'pair':pair,'observationCount':len(candidate['views']),'views':views})
    # Frozen tie-break: same acquisition, LOS-supported sample count, minimum set (2), then coordinates.
    summaries.sort(key=lambda q:(-min(v['losSupported'] for v in q['views']),q['bounds']))
    eligible=[q for q in summaries if all(v['calibratedTargetInside'] for v in q['views'])]
    if not eligible:raise ValueError('No verified complete frame coverage')
    chosen=eligible[0]
    result={'catalogueRows':len(r),'augustFrames':len(frames),'coarseProfilePoints':1414,'patchesScreened':screened,'steepPatches':len(allpatch),
            'qualifyingPatches':sum(bool(q['pairs']) for q in allpatch),'shortlist':summaries,'selected':chosen,
            'benchmarkId':f"ch-frame2026-lv95-{chosen['centre'][0]}-{chosen['centre'][1]}-v1",'aerialPixelsDownloaded':False,
            'geometryReferences':{'camera':'EPSG:2056+5729 (LHN95)','terrain':'EPSG:2056+5728 (LN02)','transformation':'NONE; +/-5m sensitivity is an engineering perturbation, not an error bound'},
            'versions':{'numpy':np.__version__,'rasterio':rasterio.__version__,'gdal':rasterio.__gdal_version__,'pyproj':pyproj.__version__,'matplotlib':matplotlib.__version__,'python':sys.version.split()[0]},'inputManifestSha256':hashlib.sha256((p/'input-manifest.json').read_bytes()).hexdigest()}
    (out/'analysis.json').write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
    draw_map(out,chosen,frames,p)
    print('Selected',result['benchmarkId'],chosen['bounds'],chosen['pair'])

if __name__=='__main__': main()
