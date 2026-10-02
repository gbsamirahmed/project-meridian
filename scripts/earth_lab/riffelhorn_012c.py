"""Bounded raw XYZ retention diagnostics; no reconstructed or production surface."""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta
import hashlib
import importlib.metadata
import json
from pathlib import Path
import struct
import sys
import time
import numpy as np
from PIL import Image, ImageDraw
from riffelhorn_012b import BOUNDS, source_catalog, height_grid, nearest_spacing
from meridian_paths import resolve_storage_roots
from bluesky_012a import digest

PATCHES = {
    'summit_cliff': [2624780,1092222,2624840,1092282],
    'sloping_control': [2625210,1092500,2625240,1092530],
    'rough_ground': [2625240,1092530,2625270,1092560],
}
RADII = (.5,1.,2.)
QUERY_COUNT = 1024
LAS_DTYPE = np.dtype({'names':['ix','iy','iz','intensity','return_flags','class_flags','scan_angle','user_data','point_source_id','gps'],
    'formats':['<i4','<i4','<i4','<u2','u1','u1','i1','u1','<u2','<f8'],
    'offsets':[0,4,8,12,14,15,16,17,18,20],'itemsize':28})


def write_json(path, value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def stats(values):
    a=np.asarray(values);a=a[np.isfinite(a)]
    if not len(a):return {'count':0}
    return {'count':int(a.size),'min':float(a.min()),'max':float(a.max()),'mean':float(a.mean()),'std':float(a.std()),
            **{f'p{p:g}':float(np.percentile(a,p)) for p in (1,5,25,50,75,90,95,99,99.5)}}


def counts(values):
    k,n=np.unique(values,return_counts=True);return {str(int(a)):int(b) for a,b in zip(k,n)}


def extract(source, catalog, out):
    """Preserve entire original format-1 records, original order and scaled XYZ."""
    pieces={k:[] for k in PATCHES};origins={k:[] for k in PATCHES};sources=[]
    for asset in catalog['assets']:
        if asset['product']!='swisssurface3d':continue
        lower=asset['actual_file']['xyz_min'];upper=asset['actual_file']['xyz_max']
        if not any(lower[0]<b[2] and upper[0]>=b[0] and lower[1]<b[3] and upper[1]>=b[1] for b in PATCHES.values()):continue
        member=asset['extracted_members'][0];path=source/member['path']
        with path.open('rb') as f:
            h=f.read(227)
            if h[:4]!=b'LASF' or h[24:26]!=bytes([1,2]) or h[104]!=1 or struct.unpack_from('<H',h,105)[0]!=28:
                raise ValueError('Unsupported acquired LAS encoding')
            scale=np.array(struct.unpack_from('<3d',h,131));offset=np.array(struct.unpack_from('<3d',h,155))
            total=struct.unpack_from('<I',h,107)[0];f.seek(struct.unpack_from('<I',h,96)[0])
            index=0
            while index<total:
                records=np.frombuffer(f.read(min(250000,total-index)*28),dtype=LAS_DTYPE)
                xyz=np.column_stack([records[k] for k in ('ix','iy','iz')])*scale+offset
                for name,(x0,y0,x1,y1) in PATCHES.items():
                    mask=(xyz[:,0]>=x0)&(xyz[:,0]<x1)&(xyz[:,1]>=y0)&(xyz[:,1]<y1)
                    if mask.any():
                        pieces[name].append((records[mask].copy(),xyz[mask].copy()))
                        origins[name].append({'source':member['path'],'record_indices':(np.flatnonzero(mask)+index).tolist()})
                index+=len(records)
        sources.append({'path':member['path'],'sha256':member['sha256'],'scale':scale.tolist(),'offset':offset.tolist(),'points':total})
    result={}
    for name in PATCHES:
        records=np.concatenate([v[0] for v in pieces[name]]);xyz=np.concatenate([v[1] for v in pieces[name]])
        np.save(out/(name+'-records.npy'),records);np.save(out/(name+'-xyz.npy'),xyz)
        write_json(out/(name+'-source-indices.json'),origins[name]);result[name]=(records,xyz)
    return result,sources


def triangle_closest(points, triangles):
    """All point/triangle closest points; exact plane interior plus clamped edges."""
    q=np.asarray(points);t=np.asarray(triangles);a,b,c=t[:,0],t[:,1],t[:,2]
    ab,ac=b-a,c-a;n=np.cross(ab,ac);nn=np.sum(n*n,axis=1)
    offset=q[:,None,:]-a
    projection=q[:,None,:]-n*np.sum(offset*n,axis=2)[...,None]/nn[None,:,None]
    v=projection-a;d00=np.sum(ab*ab,axis=1);d11=np.sum(ac*ac,axis=1);d01=np.sum(ab*ac,axis=1)
    den=d00*d11-d01*d01;d20=np.sum(v*ab,axis=2);d21=np.sum(v*ac,axis=2)
    u=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den
    squared=np.sum((projection-q[:,None,:])**2,axis=2)
    squared[(u<0)|(w<0)|(u+w>1)]=np.inf
    closest=projection.copy()
    for start,end in ((a,b),(b,c),(c,a)):
        edge=end-start;fraction=np.clip(np.sum((q[:,None,:]-start)*edge,axis=2)/np.sum(edge*edge,axis=1),0,1)
        candidate=start+fraction[...,None]*edge
        distance=np.sum((candidate-q[:,None,:])**2,axis=2);use=distance<squared
        squared[use]=distance[use];closest[use]=candidate[use]
    index=np.argmin(squared,axis=1);chosen=closest[np.arange(len(q)),index]
    normal=n[index]/np.sqrt(nn[index,None]);normal[normal[:,2]<0]*=-1
    return np.sqrt(squared[np.arange(len(q)),index]),chosen,normal


def triangles_at(grid, point, radius):
    x,y=point[:2];col=(x-BOUNDS[0])/.5-.5;row=(BOUNDS[3]-y)/.5-.5
    pad=int(np.ceil(radius/.5))+2
    r,c=np.mgrid[max(0,int(np.floor(row))-pad):min(grid.shape[0]-1,int(np.floor(row))+pad+1),
                  max(0,int(np.floor(col))-pad):min(grid.shape[1]-1,int(np.floor(col))+pad+1)]
    vertices=[]
    for dr,dc in ((0,0),(1,0),(0,1),(1,1)):
        vertices.append(np.stack([BOUNDS[0]+(c+dc+.5)*.5,BOUNDS[3]-(r+dr+.5)*.5,grid[r+dr,c+dc]],axis=-1).reshape(-1,3))
    a,b,c,d=vertices
    return np.concatenate([np.stack([a,b,c],axis=1),np.stack([c,b,d],axis=1)])


def mesh_distances(grid, points):
    distances=[];closest=[];normals=[];radii=[]
    for point in points:
        radius=1.
        while True:
            t=triangles_at(grid,point,radius)
            d,p,n=triangle_closest(point[None,:],t)
            if d[0]<radius:break  # excluded triangles cannot be nearer in XY
            radius*=2
            if radius>128:raise ValueError('Bounded globally-exact search did not converge')
        distances.append(d[0]);closest.append(p[0]);normals.append(n[0]);radii.append(radius)
    return np.array(distances),np.array(closest),np.array(normals),np.array(radii)


def fit_plane(points):
    centred=points-points.mean(axis=0);eigen,axes=np.linalg.eigh(centred.T@centred/len(points))
    eigen=np.maximum(eigen,0);normal=axes[:,0]
    if normal[2]<0:normal=-normal
    planarity=(eigen[1]-eigen[0])/max(eigen[2],1e-15)
    return normal,float(np.sqrt(eigen[0])),float(planarity)


def normals(points, queries, radius):
    result=[]
    # Bounded patch sizes: exact 3-D spherical neighbourhoods, not XY-only circles.
    for q in queries:
        squared=np.sum((points-q)**2,axis=1);subset=points[squared<=radius**2]
        if len(subset)<10:result.append([*([np.nan]*3),np.nan,np.nan,len(subset),np.nan]);continue
        n,rmse,planarity=fit_plane(subset)
        # Deterministic interleaved split: repeatability diagnostic, not an accuracy CI.
        n1,_,_=fit_plane(subset[::2]);n2,_,_=fit_plane(subset[1::2])
        repeat=float(np.degrees(np.arccos(np.clip(abs(n1@n2),0,1))))
        result.append([*n,rmse,planarity,len(subset),repeat])
    return np.asarray(result)


def rendered_normals(grid, points):
    """012B finite-difference vertex normals interpolated on its exact diagonal."""
    col=(points[:,0]-BOUNDS[0])/.5-.5;row=(BOUNDS[3]-points[:,1])/.5-.5
    c=np.floor(col).astype(int);r=np.floor(row).astype(int);u=row-r;v=col-c
    vertices=[]
    for dr,dc in ((0,0),(1,0),(0,1),(1,1)):
        rr,cc=r+dr,c+dc
        dx=grid[rr,cc+1]-grid[rr,cc-1];dn=grid[rr-1,cc]-grid[rr+1,cc]
        a=np.column_stack([-dx,-dn,np.ones(len(r))]);a/=np.linalg.norm(a,axis=1)[:,None];vertices.append(a)
    nw,sw,ne,se=vertices
    a=nw*(1-u-v)[:,None]+sw*u[:,None]+ne*v[:,None]
    b=ne*(1-u)[:,None]+sw*(1-v)[:,None]+se*(u+v-1)[:,None]
    result=np.where((u+v<=1)[:,None],a,b);return result/np.linalg.norm(result,axis=1)[:,None]


def hull(points):
    p=sorted(set(map(tuple,points)))
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    sides=[]
    for sequence in (p,p[::-1]):
        side=[]
        for q in sequence:
            while len(side)>=2 and cross(side[-2],side[-1],q)<=0:side.pop()
            side.append(q)
        sides.append(side[:-1])
    return np.array(sides[0]+sides[1])


def overlap_audit(points, records, candidates):
    """Conservative screen: test coherent upper/lower XY support, retain ambiguity."""
    results=[]
    for candidate in candidates:
        ids=candidate['indices'];centre=np.mean(points[ids,:2],axis=0)
        mask=np.max(np.abs(points[:,:2]-centre),axis=1)<=1
        indices=np.flatnonzero(mask);p=points[indices];order=np.argsort(p[:,2]);gaps=np.diff(p[order,2])
        gap_index=int(np.argmax(gaps));lower=p[order[:gap_index+1]];upper=p[order[gap_index+1:]]
        item={k:v for k,v in candidate.items() if k!='indices'};item['centre_lv95']=centre.tolist();item['local_box_halfwidth_m']=1.
        item['local_largest_z_gap_m']=float(gaps[gap_index]);item['groups']=[]
        for group in (lower,upper):
            if len(group)<10:item['groups'].append({'count':len(group),'confidence':'insufficient'});continue
            n,rms,planarity=fit_plane(group);poly=hull(group[:,:2]-centre)
            # Is common XY inside the actual convex footprint, not just its box?
            edges=np.roll(poly,-1,axis=0)-poly
            support=bool(len(poly)>=3 and np.all(edges[:,0]*(-poly[:,1])-edges[:,1]*(-poly[:,0])>=-1e-9))
            margins=(edges[:,0]*(-poly[:,1])-edges[:,1]*(-poly[:,0]))/np.maximum(np.linalg.norm(edges,axis=1),1e-12)
            item['groups'].append({'count':len(group),'normal_unsigned':n.tolist(),'plane_rms_m':rms,'planarity':planarity,
                'centre_in_xy_convex_hull':support,'centre_margin_to_xy_hull_m':float(margins.min()) if len(poly) else None,
                'predicted_height_at_common_xy_m':float(group.mean(0)[2]-n[:2]@(centre-group.mean(0)[:2])/n[2]) if abs(n[2])>.1 else None})
        good=[g for g in item['groups'] if g.get('predicted_height_at_common_xy_m') is not None and g['plane_rms_m']<=.15 and g['planarity']>=.3 and g['centre_margin_to_xy_hull_m']>=.4]
        item['robust_two_sheet_support']=len(good)==2 and abs(good[0]['predicted_height_at_common_xy_m']-good[1]['predicted_height_at_common_xy_m'])>1
        item['classification_counts']=counts(records['class_flags'][indices]&31);item['flight_ids']=counts(records['point_source_id'][indices])
        results.append(item)
    return results


def slice_points(points, axis, position, thickness):
    return points[np.abs(points[:,axis]-position)<=thickness/2]


def overlap_candidates(points, bin_width=.1, minimum_z_gap=1.):
    """Flag XY bins only. Steep single-valued planes can trigger this: NOT topology."""
    keys=np.floor(points[:,:2]/bin_width).astype(np.int64);groups={}
    for i,key in enumerate(map(tuple,keys)):groups.setdefault(key,[]).append(i)
    candidates=[]
    for key,indices in sorted(groups.items()):
        p=points[indices]
        if len(p)<4:continue
        z=np.sort(p[:,2]);gaps=np.diff(z);i=int(np.argmax(gaps))
        if gaps[i]>=minimum_z_gap and i>=1 and len(z)-i-1>=2:
            candidates.append({'bin_lv95':list(map(int,key)),'count':len(p),'z_gap_m':float(gaps[i]),'z_span_m':float(z[-1]-z[0]),
                               'indices':indices})
    return candidates


def project(points, camera, target, width=1280, height=720, fov=50):
    forward=target-camera;forward/=np.linalg.norm(forward)
    right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,forward)
    delta=points-camera;depth=delta@forward;focal=width/(2*np.tan(np.radians(fov/2)))
    screen=np.column_stack([width/2+focal*(delta@right)/depth,height/2-focal*(delta@up)/depth])
    return screen,depth


def render(triangles, points, camera, target, mode):
    """CPU perspective z-buffer: native triangles and one-pixel measured points only."""
    width,height=1280,720;canvas=np.full((height,width,3),245,np.uint8);depth=np.full((height,width),np.inf)
    if mode!='raw':
        projected,z=project(triangles.reshape(-1,3),camera,target);projected=projected.reshape(-1,3,2);z=z.reshape(-1,3)
        nn=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);nn/=np.linalg.norm(nn,axis=1)[:,None]
        nn[nn[:,2]<0]*=-1;light=np.array([.4,-.3,.8660254]);shade=(.65+.35*np.maximum(nn@light,0))*170
        for face,tz,grey in zip(projected,z,shade):
            if (tz<.1).any():continue
            x0,y0=np.maximum(np.floor(face.min(0)).astype(int),[0,0]);x1,y1=np.minimum(np.ceil(face.max(0)).astype(int),[width-1,height-1])
            if x0>x1 or y0>y1:continue
            yy,xx=np.mgrid[y0:y1+1,x0:x1+1];p=np.stack([xx+.5,yy+.5],axis=-1)
            a,b,c=face;den=(b-a)[0]*(c-a)[1]-(b-a)[1]*(c-a)[0]
            if abs(den)<1e-12:continue
            v=p-a;beta=(v[...,0]*(c-a)[1]-v[...,1]*(c-a)[0])/den
            gamma=((b-a)[0]*v[...,1]-(b-a)[1]*v[...,0])/den;alpha=1-beta-gamma
            inside=(alpha>=0)&(beta>=0)&(gamma>=0)
            zz=1/(alpha/tz[0]+beta/tz[1]+gamma/tz[2]);region=depth[y0:y1+1,x0:x1+1]
            use=inside&(zz<region);region[use]=zz[use];canvas[y0:y1+1,x0:x1+1][use]=int(grey)
    if mode!='mesh':
        screen,z=project(points,camera,target);pix=np.floor(screen).astype(int)
        good=(z>.1)&(pix[:,0]>=0)&(pix[:,0]<width)&(pix[:,1]>=0)&(pix[:,1]<height)
        # Far-to-near paints leave the nearest return; overlay tolerance is 0.02 m.
        for idx in np.argsort(z)[::-1]:
            if not good[idx]:continue
            x,y=pix[idx]
            if z[idx]<=depth[y,x]+.02:canvas[y,x]=[30,95,180];depth[y,x]=z[idx]
    return Image.fromarray(canvas)


def patch_triangles(grid,bounds):
    x0,y0,x1,y1=bounds;r0=int((BOUNDS[3]-y1)/.5);r1=int((BOUNDS[3]-y0)/.5);c0=int((x0-BOUNDS[0])/.5);c1=int((x1-BOUNDS[0])/.5)
    r,c=np.mgrid[r0:r1-1,c0:c1-1];vertices=[]
    for dr,dc in ((0,0),(1,0),(0,1),(1,1)):
        vertices.append(np.stack([BOUNDS[0]+(c+dc+.5)*.5,BOUNDS[3]-(r+dr+.5)*.5,grid[r+dr,c+dc]],axis=-1).reshape(-1,3))
    a,b,c,d=vertices
    return np.concatenate([np.stack([a,b,c],axis=1),np.stack([c,b,d],axis=1)])


def figures(out,name,xyz,query,distances,nearest,normal_results,grid,bounds):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(16,5))
    e,n=np.mean(np.array(bounds).reshape(2,2),axis=0)
    for ax,values,title in zip(axes,(distances,normal_results[1][0],normal_results[1][1]),
            ('Exact point-to-triangle distance (m)','Reliable raw/triangle acute angle (degrees)','Raw plane RMS at 1 m radius (m)')):
        im=ax.scatter(query[:,0]-e,query[:,1]-n,c=values,s=8,cmap='viridis');fig.colorbar(im,ax=ax);ax.set(title=title,aspect='equal',xlabel='east (m)',ylabel='north (m)')
    fig.suptitle(name+' | deterministic queries, not population fractions | \u00a9swisstopo');fig.tight_layout();fig.savefig(out/(name+'-maps.png'),dpi=130);plt.close(fig)
    # Three E-W and two N-S cuts; raw thickness 0.2 m, exact mesh section is 0-width.
    specs=[(1,n-5),(1,n),(1,n+5),(0,e-20 if name=='summit_cliff' else e-5),(0,e)]
    fig,axes=plt.subplots(2,3,figsize=(16,10));sections=[]
    triangles=patch_triangles(grid,bounds)
    for ax,(axis,pos) in zip(axes.ravel(),specs):
        p=slice_points(xyz,axis,pos,.2);other=1-axis
        ax.scatter(p[:,other]-(e if other==0 else n),p[:,2],s=3,label='raw within +/-0.1 m')
        for t in triangles:
            hits=[]
            for a,b in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])):
                if (a[axis]<=pos<b[axis]) or (b[axis]<=pos<a[axis]):hits.append(a+(b-a)*(pos-a[axis])/(b[axis]-a[axis]))
            if len(hits)==2:
                h=np.array(hits);ax.plot(h[:,other]-(e if other==0 else n),h[:,2],color='orange',lw=.8)
        ax.set(title=f'{"N" if axis==1 else "E"}={pos:.2f}; {len(p)} returns',xlabel=('east' if other==0 else 'north')+' offset (m)',ylabel='LN02 (m)');ax.set_aspect('equal',adjustable='box')
        sections.append({'constant_axis':'northing' if axis==1 else 'easting','coordinate':pos,'full_thickness_m':.2,'point_count':len(p),'mesh':'exact triangle-plane intersection'})
    if name=='summit_cliff':
        ax=axes.ravel()[-1];pos=float(np.median(xyz[:,2])-20);p=slice_points(xyz,2,pos,.2)
        ax.scatter(p[:,0]-e,p[:,1]-n,s=3,label='raw within +/-0.1 m height')
        for t in triangles:
            hits=[]
            for a,b in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])):
                if (a[2]<=pos<b[2]) or (b[2]<=pos<a[2]):hits.append(a+(b-a)*(pos-a[2])/(b[2]-a[2]))
            if len(hits)==2:
                h=np.array(hits);ax.plot(h[:,0]-e,h[:,1]-n,color='orange',lw=.8)
        ax.set(title=f'Horizontal Z={pos:.2f} LN02; {len(p)} returns',xlabel='east offset (m)',ylabel='north offset (m)',aspect='equal')
        sections.append({'constant_axis':'height_ln02_m','coordinate':pos,'full_thickness_m':.2,'point_count':len(p),'mesh':'exact triangle-plane intersection'})
    else:axes.ravel()[-1].axis('off')
    fig.suptitle(name+' | equal metre scales; sections do not prove topology | \u00a9swisstopo');fig.tight_layout();fig.savefig(out/(name+'-sections.png'),dpi=150);plt.close(fig)
    return sections


def build(repo,data,out):
    start=time.monotonic();out.mkdir(parents=True,exist_ok=True)
    catalog,source=source_catalog(repo,data)  # verify all originals and extracted LAS
    baseline=json.loads((repo/'docs/earth-lab/riffelhorn-012b-metadata.json').read_text(encoding='utf-8'))
    previous=data/'experiments/earth-lab/riffelhorn-012b/observed-mountain-v1'
    for item in baseline['products']:
        if item['path'].startswith('meshes/dsm/') and digest(previous/item['path'])!=item['sha256']:raise ValueError('012B DSM mesh changed')
    grid=height_grid(catalog,source,'swisssurface3d-raster')
    subsets,sources=extract(source,catalog,out);measurements={};view_specs=[]
    for name,(records,xyz) in subsets.items():
        print('analyse',name,len(xyz),flush=True);bounds=PATCHES[name];x0,y0,x1,y1=bounds
        eligible=np.where((xyz[:,0]>x0+2)&(xyz[:,0]<x1-2)&(xyz[:,1]>y0+2)&(xyz[:,1]<y1-2))[0]
        order=eligible[np.lexsort((xyz[eligible,2],xyz[eligible,1],xyz[eligible,0]))]
        indices=order[np.linspace(0,len(order)-1,min(QUERY_COUNT,len(order)),dtype=int)];q=xyz[indices]
        distance,closest,mesh_normal,radius=mesh_distances(grid,q)
        np.save(out/(name+'-queries.npy'),indices);np.save(out/(name+'-closest.npy'),np.column_stack([distance,closest,mesh_normal,radius]))
        normal_reports={};plot_values={};normal_arrays=[];smooth_normal=rendered_normals(grid,closest)
        for r in RADII:
            a=normals(xyz,q,r);np.save(out/(name+f'-normals-{r:g}.npy'),a);normal_arrays.append(a)
            angle=np.degrees(np.arccos(np.clip(np.abs(np.sum(a[:,:3]*mesh_normal,axis=1)),0,1)))
            smooth_angle=np.degrees(np.arccos(np.clip(np.abs(np.sum(a[:,:3]*smooth_normal,axis=1)),0,1)))
            reliable=(a[:,5]>=10)&(a[:,4]>=.3)&(a[:,3]<=min(.1,r*.1))&(a[:,6]<=10)
            inclination=np.degrees(np.arccos(np.clip(np.abs(a[:,2]),0,1)))
            detail=reliable&(smooth_angle>15)&(distance<=.25)
            geometry=reliable&(distance>.5)
            pair_distance=np.linalg.norm(q[:,None,:]-q[None,:,:],axis=2)
            same_orientation=np.abs(a[:,:3]@a[:,:3].T)>np.cos(np.radians(15))
            neighbours=(pair_distance>0)&(pair_distance<=2*r)&same_orientation
            coherent_detail=detail&(np.sum(neighbours&detail[None,:],axis=1)>=2)
            coherent_geometry=geometry&(np.sum(neighbours&geometry[None,:],axis=1)>=2)
            normal_reports[str(r)]={'radius_m':r,'diameter_m':r*2,'usable_count':int(np.isfinite(a[:,0]).sum()),'reliable_count':int(reliable.sum()),
                'reliability':'at least 10 returns, planarity >=0.3, plane RMS <=min(0.1,radius*0.1) m, split-fit angle <=10 deg; heuristic, not accuracy CI',
                'all_inclination_degrees':stats(inclination),'reliable_inclination_degrees':stats(inclination[reliable]),'plane_rms_m':stats(a[:,3]),
                'planarity':stats(a[:,4]),'split_angle_degrees':stats(a[:,6]),'reliable_raw_facet_angle_degrees':stats(angle[reliable]),
                'reliable_raw_rendered_normal_angle_degrees':stats(smooth_angle[reliable]),
                'detail_candidates':int(detail.sum()),'detail_candidates_with_two_similar_neighbours':int(coherent_detail.sum()),
                'geometry_candidates':int(geometry.sum()),'geometry_candidates_with_two_similar_neighbours':int(coherent_geometry.sum()),
                'coherence_screen':'Within 2*radius in 3-D, >=2 other reliable queries with acute normal separation <15 deg; diagnostic sample support, not independent accuracy or population coverage',
                'reliable_angle_over_15_percent':float(np.mean(angle[reliable]>15)*100) if reliable.any() else None,
                'reliable_distance_over_25cm_percent':float(np.mean(distance[reliable]>.25)*100) if reliable.any() else None,
                'distance_vs_raw_inclination_pearson':float(np.corrcoef(distance[reliable],inclination[reliable])[0,1]) if reliable.sum()>2 else None,
                'distance_vs_neighbour_count_pearson':float(np.corrcoef(distance[np.isfinite(a[:,0])],a[np.isfinite(a[:,0]),5])[0,1]) if np.isfinite(a[:,0]).sum()>2 else None,
                'median_distance_by_inclination':{f'{low}-{high}':stats(distance[reliable&(inclination>=low)&(inclination<high)]) for low,high in ((0,30),(30,60),(60,80),(80,90.001))}}
            plot_values[r]=(np.where(reliable,angle,np.nan),a[:,3])
        candidates=overlap_candidates(xyz)
        topology_audit=overlap_audit(xyz,records,candidates)
        np.save(out/(name+'-overlap-candidates.npy'),np.array([i for c in candidates for i in c['indices']],dtype=np.int64))
        density=np.histogram2d(xyz[:,0],xyz[:,1],bins=(np.arange(x0,x1+1,1),np.arange(y0,y1+1,1)))[0]
        dates=[(datetime(1980,1,6)+timedelta(seconds=float(t)+1e9)).date().isoformat() for t in records['gps']]
        signed=np.sum((q-closest)*mesh_normal,axis=1)
        sections=figures(out,name,xyz,q,distance,closest,plot_values,grid,bounds)
        spacing=nearest_spacing(xyz)
        spacing['method']=f'Exact nearest other return within full {x1-x0} x {y1-y0} m patch; 256 deterministic lexicographic interior queries with 5 m XY margin. Overlaps/duplicates retained; not independent resolution.'
        measurements[name]={'bounds_lv95':bounds,'dimensions_m':[x1-x0,y1-y0],'point_count':len(xyz),'density_points_per_m2':len(xyz)/((x1-x0)*(y1-y0)),
            'one_m_horizontal_cell_count':stats(density),'classes':counts(records['class_flags']&31),'return_number':counts(records['return_flags']&7),
            'number_of_returns':counts((records['return_flags']>>3)&7),'point_source_id':counts(records['point_source_id']),
            'gps_timescale_dates':{d:dates.count(d) for d in sorted(set(dates))},'xyz_bounds':[xyz.min(0).tolist(),xyz.max(0).tolist()],
            'nearest_spacing':spacing,'query_count':len(q),'query_selection':'lexicographic spread among returns with 2 m XY margin; all classifications, no random population claim',
            'exact_distance_m':stats(distance),'signed_nearest_facet_distance_m':stats(signed),'search_radius_m':stats(radius),
            'query_distance_over_percent':{str(t):float(np.mean(distance>t)*100) for t in (.1,.25,.5,1,2)},
            'distance_by_class':{str(k):stats(distance[(records['class_flags'][indices]&31)==k]) for k in np.unique(records['class_flags']&31)},
            'normals':normal_reports,'sections':sections,'overlapping_xy_candidates':{'bin_width_m':.1,'minimum_gap_m':1,'count':len(candidates),
                'largest_z_gap_m':max([v['z_gap_m'] for v in candidates],default=0),'local_coherent_group_audit':topology_audit,
                'robust_two_sheet_support_count':sum(v['robust_two_sheet_support'] for v in topology_audit),
                'audit_criteria':'Both local planes >=10 points, RMS <=0.15 m, planarity >=0.3, abs(normal.Z)>0.1; common XY at least 0.4 m within both convex footprints (2x stated horizontal sigma), separated >1 m. This remains an evidence screen, not independent accuracy validation.',
                'note':'Finite bin steep slopes, overlapping flights, classification and uncertainty can mimic multiple surfaces. No automatic overhang/non-heightfield assertion.'}}
        if name=='summit_cliff':
            triangles=patch_triangles(grid,bounds);target=np.array([np.mean([x0,x1]),np.mean([y0,y1]),float(np.median(xyz[:,2]))])
            direction=np.array([-.7,-1,.2]);direction/=np.linalg.norm(direction)
            for dist in (60.,180.,600.):
                camera=target+dist*direction
                spec={'name':f'cliff-{dist:g}m','camera_lv95_ln02_m':camera.tolist(),'target_lv95_ln02_m':target.tolist(),'distance_m':dist,'horizontal_fov_degrees':50,'width':1280,'height':720,'near_clip_m':.1,'far_clip':'none','metres_per_target_pixel':2*dist*np.tan(np.radians(25))/1280}
                pq,_=project(q,camera,target);pm,_=project(closest,camera,target)
                spec['projected_query_displacement_pixels']=stats(np.linalg.norm(pq-pm,axis=1));view_specs.append(spec)
                contact=Image.new('RGB',(1280,3*754),'white');draw=ImageDraw.Draw(contact)
                for row,mode in enumerate(('raw','mesh','overlay')):
                    im=render(triangles,xyz,camera,target,mode);path=out/f'cliff-{dist:g}m-{mode}.png';im.save(path)
                    contact.paste(im,(0,row*754));draw.text((8,row*754+725),f'{mode}: {dist:g} m | 50 deg HFOV | measured points 1 screen pixel; no filled raw surface | \u00a9swisstopo',fill='black')
                contact.save(out/f'cliff-{dist:g}m-comparison.png')
    write_json(out/'measurements.json',{'patches':measurements,'views':view_specs})
    files=sorted([*out.glob('*.npy'),*out.glob('*.png'),*out.glob('*-source-indices.json'),out/'measurements.json'])
    manifest={'experiment':'Lab 012C raw LiDAR information retention','parent_012b_identity':baseline['identity'],
        'processing_script_sha256':digest(Path(__file__)),
        'sources':sources,'crs':'EPSG:2056 / LV95; vertical LN02 metres, provenance EPSG:5728; no conversion',
        'patches':PATCHES,'parameters':{'normal_radii_m':RADII,'queries':QUERY_COUNT,'signed_distance':'dot(point-closest,upward closest facet normal); not globally oriented closed-surface inside/outside',
            'topology':'012B native cell centres, diagonal (NW,SW,NE)/(NE,SW,SE); exact adaptive nearest triangle search until distance < excluded XY bound',
            'normals':'3D spherical PCA, unsigned orientation comparisons; deterministic interleaved split repeatability',
            'render':'native triangles, flat analytic shade; raw unconnected one-screen-pixel blue points, z-buffer; no surfels, completion or inferred topology',
            'radiometry':'no new RGB processing; source context retained from 012B','attribution':'\u00a9swisstopo'},
        'toolchain':{'python':sys.version.split()[0],**{k:importlib.metadata.version(k) for k in ('numpy','rasterio','Pillow','matplotlib')}},
        'products':[{'path':p.name,'bytes':p.stat().st_size,'sha256':digest(p)} for p in files]}
    manifest['identity']=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest();write_json(out/'manifest.json',manifest)
    print('IDENTITY',manifest['identity'],'seconds',time.monotonic()-start,flush=True)
    return manifest


def verify(repo,data,out):
    source_catalog(repo,data)
    m=json.loads((out/'manifest.json').read_text(encoding='utf-8'));identity=m.pop('identity')
    if hashlib.sha256(json.dumps(m,sort_keys=True).encode()).hexdigest()!=identity:raise ValueError('Identity mismatch')
    for p in m['products']:
        if digest(out/p['path'])!=p['sha256']:raise ValueError('Changed '+p['path'])
    if digest(Path(__file__))!=m['processing_script_sha256']:raise ValueError('Processing code differs from recorded derivation')
    measurements=json.loads((out/'measurements.json').read_text(encoding='utf-8'))
    frames=0
    for view in measurements['views']:
        camera=np.array(view['camera_lv95_ln02_m']);target=np.array(view['target_lv95_ln02_m'])
        np.testing.assert_allclose(np.linalg.norm(camera-target),view['distance_m'],atol=1e-8)
        screen,depth=project(target[None,:],camera,target);np.testing.assert_allclose(screen,[[640,360]],atol=1e-8)
        for mode in ('raw','mesh','overlay'):
            with Image.open(out/(view['name']+'-'+mode+'.png')) as image:
                if image.size!=(1280,720) or np.asarray(image).std()<1:raise ValueError('Diagnostic frame dimensions or content changed')
            frames+=1
    catalog,source=source_catalog(repo,data);grid=height_grid(catalog,source,'swisssurface3d-raster');samples=0
    for name,b in PATCHES.items():
        xyz=np.load(out/(name+'-xyz.npy'));records=np.load(out/(name+'-records.npy'))
        if not ((xyz[:,0]>=b[0])&(xyz[:,0]<b[2])&(xyz[:,1]>=b[1])&(xyz[:,1]<b[3])).all():raise ValueError('Extraction outside bounds')
        contexts=json.loads((out/(name+'-source-indices.json')).read_text(encoding='utf-8'));cursor=0
        for context in contexts:
            with (source/context['source']).open('rb') as f:
                h=f.read(227);offset=struct.unpack_from('<I',h,96)[0];scale=np.array(struct.unpack_from('<3d',h,131));origin=np.array(struct.unpack_from('<3d',h,155))
                for j in (0,len(context['record_indices'])//2,len(context['record_indices'])-1):
                    f.seek(offset+context['record_indices'][j]*28);raw=np.frombuffer(f.read(28),dtype=LAS_DTYPE)[0]
                    if raw.tobytes()!=records[cursor+j].tobytes():raise ValueError('Original LAS attribute changed')
                    np.testing.assert_array_equal(xyz[cursor+j],np.array([raw[k] for k in ('ix','iy','iz')])*scale+origin);samples+=1
            cursor+=len(context['record_indices'])
        if cursor!=len(xyz):raise ValueError('Index inventory incomplete')
        q=xyz[np.load(out/(name+'-queries.npy'))];result=np.load(out/(name+'-closest.npy'))
        d,closest,n,r=mesh_distances(grid,q[:8]);np.testing.assert_allclose(result[:8,:4],np.column_stack([d,closest]),rtol=0,atol=1e-9)
    result={'result':'PASS','originals':16,'source_las':4,'product_hashes':len(m['products']),'original_record_coordinate_samples':samples,'nearest_surface_rerun_queries':24,'fixed_camera_views':3,'diagnostic_frames':frames,'identity':identity}
    write_json(out/'validation.json',result);return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    repo=Path(__file__).resolve().parents[2];data=resolve_storage_roots(repository_root=repo,require_data=True).data
    out=data/'experiments/earth-lab/riffelhorn-012c/raw-retention-v1'
    print(verify(repo,data,out) if args.verify else build(repo,data,out)['identity'])
