"""Lab 012B: native raster surfaces and bounded raw-observation diagnostics."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
from pathlib import Path
import shutil
import struct
import time
from datetime import datetime, timedelta
import numpy as np
import rasterio
from rasterio.windows import Window
from PIL import Image
import experiment_paths  # Establish the existing Earth Lab/common script import path.
from meridian_paths import resolve_storage_roots
from bluesky_012a import digest, write_glb
from observed_surface_height import statistics, window_fields
BOUNDS = (2624000, 1091000, 2626000, 1093000)
SPACING = .5
VERTICAL_ORIGIN = 2500
CHUNK = 500
PATCHES = {
    'summit': (2624810, 1092252),
    'steep_face': (2624805, 1092330),
    'loose_deposits': (2625090, 1091740),
    'alpine_path': (2625240, 1092530),
    'water_edge': (2625070, 1092450),
    'glacial_transition': (2624900, 1091580),
    'ice_interior': (2625000, 1091500),
}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def source_catalog(repo, data):
    catalog = json.loads((repo/'docs/atlas/riffelhorn-data-catalog.json').read_text(encoding='utf-8'))
    source = data/catalog['external_root_relative']
    for record in catalog['assets']:
        if digest(source/record['path']) != record['sha256']:
            raise ValueError('Immutable source changed: ' + record['path'])
        for member in record.get('extracted_members', []):
            if digest(source/member['path']) != member['sha256']:
                raise ValueError('Immutable LAS changed')
    return catalog, source


def height_grid(catalog, source, product):
    grid = np.full((4000, 4000), np.nan, np.float32)
    for record in catalog['assets']:
        if record['product'] != product:
            continue
        with rasterio.open(source/record['path']) as src:
            if src.crs.to_epsg() != 2056 or src.res != (.5, .5):
                raise ValueError('Unexpected height grid')
            r = round((BOUNDS[3]-src.bounds.top)/.5)
            c = round((src.bounds.left-BOUNDS[0])/.5)
            values = src.read(1, masked=True).filled(np.nan)
            grid[r:r+2000, c:c+2000] = values
    if not np.isfinite(grid).all():
        raise ValueError('Incomplete/non-finite height coverage')
    return grid


def sample_grid(grid, x, y):
    """Bilinear interpolation of cell-centre heights, not corner-index sampling."""
    c = (np.asarray(x)-BOUNDS[0])/.5-.5
    r = (BOUNDS[3]-np.asarray(y))/.5-.5
    col, row = np.floor(c).astype(int), np.floor(r).astype(int)
    valid = (col >= 0) & (row >= 0) & (col < grid.shape[1]-1) & (row < grid.shape[0]-1)
    col, row = np.clip(col, 0, grid.shape[1]-2), np.clip(row, 0, grid.shape[0]-2)
    fc, fr = c-col, r-row
    z = grid[row, col]*(1-fc)*(1-fr) + grid[row, col+1]*fc*(1-fr)
    z += grid[row+1, col]*(1-fc)*fr + grid[row+1, col+1]*fc*fr
    return np.where(valid, z, np.nan)


def mesh_arrays(grid, r, c):
    h, w = min(CHUNK, grid.shape[0]-1-r)+1, min(CHUNK, grid.shape[1]-1-c)+1
    ra, ca = max(0, r-1), max(0, c-1)
    apron = grid[ra:min(grid.shape[0], r+h+1), ca:min(grid.shape[1], c+w+1)]
    dy, dx = np.gradient(apron, .5, edge_order=2)
    dx, dy = dx[r-ra:r-ra+h, c-ca:c-ca+w], dy[r-ra:r-ra+h, c-ca:c-ca+w]
    rr, cc = np.mgrid[r:r+h, c:c+w]
    p = np.stack((cc*.5+.25, grid[r:r+h,c:c+w]-VERTICAL_ORIGIN, rr*.5+.25), -1).astype('<f4').reshape(-1,3)
    normal = np.stack((-dx, np.ones_like(dx), -dy), -1)
    normal = (normal/np.linalg.norm(normal,axis=-1,keepdims=True)).astype('<f4').reshape(-1,3)
    uv = np.stack(((cc-c)*.5+.75, (rr-r)*.5+.75), -1).astype('<f4').reshape(-1,2)/251
    start = (np.arange(h-1)[:,None]*w+np.arange(w-1)[None,:]).ravel()
    indices = np.stack((start,start+w,start+1,start+1,start+w,start+w+1),1).astype('<u4').ravel()
    return p, normal, uv, indices


def las_chunks(path):
    """Supported acquired LAS layout only; no meshing or semantic inference."""
    with path.open('rb') as stream:
        header = stream.read(227)
        if header[:4] != b'LASF' or header[24:26] != bytes([1,2]) or header[104] != 1:
            raise ValueError('Expected acquired LAS 1.2 format 1')
        offset = struct.unpack_from('<I', header, 96)[0]
        length, count = struct.unpack_from('<HI', header, 105)
        if length != 28 or not (struct.unpack_from('<H',header,6)[0] & 1):
            raise ValueError('Unexpected point/GPS encoding')
        scales = np.array(struct.unpack_from('<3d',header,131))
        origin = np.array(struct.unpack_from('<3d',header,155))
        dtype = np.dtype({'names':['x','y','z','returns','class','gps'],
                          'formats':['<i4','<i4','<i4','u1','u1','<f8'],
                          'offsets':[0,4,8,14,15,20],'itemsize':28})
        stream.seek(offset)
        seen = 0
        while seen < count:
            points = np.fromfile(stream,dtype=dtype,count=min(250000,count-seen))
            if not len(points):
                raise ValueError('Truncated LAS')
            xyz = np.column_stack([points[k] for k in ('x','y','z')])*scales+origin
            yield xyz, points['class'] & 31, points['returns'] & 7, points['gps']
            seen += len(points)


def nearest_spacing(xyz, queries=256):
    """Exact distances to all patch points for deterministic interior query points."""
    order = np.lexsort((xyz[:,2],xyz[:,1],xyz[:,0]))
    p = xyz[order]
    lo, hi = p[:,:2].min(0)+5, p[:,:2].max(0)-5
    candidates = np.flatnonzero(np.all((p[:,:2] >= lo) & (p[:,:2] <= hi),axis=1))
    selected = candidates[np.linspace(0,len(candidates)-1,min(queries,len(candidates)),dtype=int)]
    horizontal, spatial = [], []
    for start in range(0,len(selected),8):
        ids = selected[start:start+8]
        delta = p[ids,None,:]-p[None,:,:]
        xy = np.sum(delta[:,:,:2]**2,axis=2)
        xyz2 = xy+delta[:,:,2]**2
        xy[np.arange(len(ids)),ids] = np.inf
        xyz2[np.arange(len(ids)),ids] = np.inf
        horizontal.extend(np.sqrt(xy.min(1)))
        spatial.extend(np.sqrt(xyz2.min(1)))
    return {'query_count':len(selected),'horizontal_m':statistics(np.array(horizontal)),
            'three_dimensional_m':statistics(np.array(spatial)),
            'method':'Exact nearest other return within full 60 m patch, queried on deterministic lexicographic spread with 5 m interior margin. Overlapping returns are retained; zero distance is not independent resolution.'}


def triangle_distance(grid, xyz, radius=2):
    """Nearest native mesh triangles in an XY search box; retain distance bounds."""
    distances=[]
    for e,n,z in xyz:
        col=(e-BOUNDS[0])/.5-.5;row=(BOUNDS[3]-n)/.5-.5
        pad=int(np.ceil(radius/.5))+1
        r0=max(0,int(np.floor(row))-pad);r1=min(grid.shape[0]-2,int(np.floor(row))+pad)
        c0=max(0,int(np.floor(col))-pad);c1=min(grid.shape[1]-2,int(np.floor(col))+pad)
        rr,cc=np.mgrid[r0:r1+1,c0:c1+1]
        def vertex(dr,dc):
            return np.stack((BOUNDS[0]+(cc+dc+.5)*.5-e,
                             BOUNDS[3]-(rr+dr+.5)*.5-n,grid[rr+dr,cc+dc].astype(np.float64)-z),-1).reshape(-1,3)
        a,b,c,d=vertex(0,0),vertex(1,0),vertex(0,1),vertex(1,1)
        a,b,c=np.concatenate((a,c)),np.concatenate((b,b)),np.concatenate((c,d))
        ab,ac=b-a,c-a;normal=np.cross(ab,ac)
        projected=-(((-a)*normal).sum(1)/(normal*normal).sum(1))[:,None]*normal
        v=projected-a
        aa=(ab*ab).sum(1);bb=(ab*ac).sum(1);cc2=(ac*ac).sum(1)
        va=(v*ab).sum(1);vb=(v*ac).sum(1);denom=aa*cc2-bb*bb
        u=(cc2*va-bb*vb)/denom;w=(aa*vb-bb*va)/denom
        inside=(u>=0)&(w>=0)&(u+w<=1)
        best=np.where(inside,(projected*projected).sum(1),np.inf)
        for start,end in ((a,b),(b,c),(c,a)):
            edge=end-start;t=np.clip(((-start)*edge).sum(1)/(edge*edge).sum(1),0,1)
            closest=start+t[:,None]*edge
            best=np.minimum(best,(closest*closest).sum(1))
        distances.append(float(np.sqrt(best.min())))
    return np.asarray(distances)


def augment_analysis(out,dsm):
    report=json.loads((out/'analysis.json').read_text())
    for name in PATCHES:
        points=np.load(out/'raw-patches'/f'{name}.npy')
        first=points[(points[:,3]==2)&(points[:,4]==1),:3]
        first=first[np.lexsort((first[:,2],first[:,1],first[:,0]))]
        query=first[np.linspace(0,len(first)-1,min(256,len(first)),dtype=int)]
        distance=triangle_distance(dsm,query)
        report['patches'][name]['native_mesh_vs_ground_first_return']={
            'query_count':len(query),'distance_m':statistics(distance),'at_least_2m_fraction_percent':float(np.mean(distance>=2)*100),
            'method':'Exact closest point on selected native grid triangles in an XY box enclosing ±2 m. Distances below 2 m cannot be beaten by excluded triangles and are exact for the complete mesh. Distances >=2 m are upper bounds with a 2 m lower bound, not exact global distances. Deterministic lexicographic query spread, not a random population estimate.'}
        days,numbers=np.unique(np.floor((points[:,5]+1e9)/86400).astype(np.int64),return_counts=True)
        report['patches'][name]['acquisition_gps_date_counts']={
            (datetime(1980,1,6)+timedelta(days=int(day))).date().isoformat():int(number) for day,number in zip(days,numbers)}
    write_json(out/'analysis.json',report)
    return report


def angle_statistics(values):
    return {key[:-2]+"_degrees" if key.endswith("_m") else key:value for key,value in statistics(values).items()}


def analyse(catalog, source, out, dtm, dsm):
    delta = dsm.astype(np.float64)-dtm
    gy, gx = np.gradient(dtm,.5)
    slope = np.degrees(np.arctan(np.hypot(gx,gy)))
    stats = {'signed_dsm_minus_dtm_m':statistics(delta),
             'absolute_difference_area_percent':{str(t):float(np.mean(np.abs(delta)>t)*100) for t in (.1,.25,.5,1,2,5)},
             'slope_relationship':[]}
    for low, high in ((0,10),(10,30),(30,45),(45,60),(60,90)):
        mask = (slope >= low) & (slope < high)
        stats['slope_relationship'].append({'degrees':[low,high],'cells':int(mask.sum()),'difference_m':statistics(delta[mask])})
    density = np.zeros((4000,4000), np.uint32)
    subsets = {k:[] for k in PATCHES}
    for record in catalog['assets']:
        if record['product'] != 'swisssurface3d':
            continue
        for member in record['extracted_members']:
            for xyz, classes, returns, gps in las_chunks(source/member['path']):
                c = np.clip(((xyz[:,0]-BOUNDS[0])/.5).astype(int),0,3999)
                r = np.clip(((BOUNDS[3]-xyz[:,1])/.5).astype(int),0,3999)
                np.add.at(density,(r,c),1)
                for name,(e,n) in PATCHES.items():
                    mask = (np.abs(xyz[:,0]-e)<30) & (np.abs(xyz[:,1]-n)<30)
                    if mask.any():
                        subsets[name].append(np.column_stack((xyz[mask],classes[mask],returns[mask],gps[mask])))
        print('raw observations scanned',record['tile'],flush=True)
    stats['density_half_m_cells'] = {'cells':density.size,'empty_percent':float(np.mean(density==0)*100),
        'count_percentiles':{str(p):float(x) for p,x in zip((1,5,25,50,75,95,99),np.percentile(density,(1,5,25,50,75,95,99)))},
        'note':'All returns in horizontal cell footprints, not independent observations or cliff surface-area density'}
    stats['patches'] = {}
    (out/'raw-patches').mkdir(exist_ok=True)
    for name, pieces in subsets.items():
        points = np.concatenate(pieces)
        np.save(out/'raw-patches'/f'{name}.npy',points,allow_pickle=False)
        xyz = points[:,:3]
        e,n = PATCHES[name]
        r,c = round((BOUNDS[3]-n)/.5),round((e-BOUNDS[0])/.5)
        terrain = dtm[r-60:r+60,c-60:c+60]
        surface = dsm[r-60:r+60,c-60:c+60]
        predictions = sample_grid(dsm,xyz[:,0],xyz[:,1])
        residual = predictions-xyz[:,2]
        local_slope = np.nan_to_num(sample_grid(slope,xyz[:,0],xyz[:,1]))
        tangent_normal = residual*np.cos(np.radians(local_slope))
        class_stats = {}
        for cls in np.unique(points[:,3]):
            mask = (points[:,3]==cls) & (points[:,4]==1)
            class_stats[str(int(cls))] = {'returns':int(np.sum(points[:,3]==cls)),
                'first_returns':int(mask.sum()),'raster_minus_first_return_z_m':statistics(residual[mask]),
                'approx_tangent_normal_difference_m':statistics(tangent_normal[mask])}
        roughness = {}
        for cells in (3,7,21):
            t = window_fields(terrain,cells)['mean']
            s = window_fields(surface,cells)['mean']
            roughness[str(cells*.5)] = {'dtm_departure_from_local_mean_m':statistics(terrain-t),
                                       'dsm_departure_from_local_mean_m':statistics(surface-s)}
        stats['patches'][name] = {'centre_lv95':[e,n],'bounds_lv95':[e-30,n-30,e+30,n+30],
            'selection':'Fixed source-imagery inspection locations spanning contrasting scenes; labels describe selection context, not point semantic classifications',
            'point_count':len(points),'density_per_m2':len(points)/3600,'class_statistics':class_stats,
            'slope_degrees':angle_statistics(slope[r-60:r+60,c-60:c+60]),'dtm_dsm_difference_m':statistics(surface-terrain),
            'nearest_spacing':nearest_spacing(xyz),'local_mean_departure_scales_m':roughness,
            'xyz_bounds':[xyz.min(0).tolist(),xyz.max(0).tolist()],
            'residual_note':'Bilinear raster-minus-point vertical difference. Cos(slope) approximation projects onto a local terrain normal, not exact 3-D distance or sensor error. Different acquisition/update periods and class selection remain confounds.'}
    write_json(out/'analysis.json',stats)
    diagnostics(out,dtm,dsm,slope,delta,subsets)
    return stats


def diagnostics(out, dtm, dsm, slope, delta, subsets):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1,3,figsize=(16,5))
    for ax,array,title,limits in zip(axes,(dtm,delta,slope),('DTM LN02 (m)','DSM−DTM (m), fixed ±5 m stretch','DTM slope (degrees)'),((2189,2978),(-5,5),(0,90))):
        im=ax.imshow(array[::4,::4],extent=(BOUNDS[0],BOUNDS[2],BOUNDS[1],BOUNDS[3]),vmin=limits[0],vmax=limits[1],cmap='coolwarm' if title.startswith('DSM') else 'viridis')
        ax.set_title(title);fig.colorbar(im,ax=ax)
    fig.suptitle('Lab 012B source/derived overview — ©swisstopo');fig.tight_layout();fig.savefig(out/'overview-analysis.png',dpi=120);plt.close(fig)
    for name,pieces in subsets.items():
        p=np.concatenate(pieces);e,n=PATCHES[name];r,c=round((BOUNDS[3]-n)/.5),round((e-BOUNDS[0])/.5)
        fig,axes=plt.subplots(1,3,figsize=(15,5))
        axes[0].scatter(p[:,0]-e,p[:,1]-n,c=p[:,2],s=.1,cmap='viridis',rasterized=True)
        axes[0].set(title='Raw returns: XY / elevation',aspect='equal',xlabel='east of centre (m)',ylabel='north of centre (m)')
        im=axes[1].imshow((dsm-dtm)[r-60:r+60,c-60:c+60],extent=(-30,30,-30,30),vmin=-5,vmax=5,cmap='coolwarm');fig.colorbar(im,ax=axes[1],label='DSM−DTM (m)')
        strip=np.abs(p[:,1]-n)<.25
        axes[2].scatter(p[strip,0]-e,p[strip,2],s=2,label='raw returns within ±0.25 m northing')
        x=BOUNDS[0]+(np.arange(c-60,c+60)+.5)*.5
        axes[2].plot(x-e,dtm[r,c-60:c+60],label='DTM centre-row');axes[2].plot(x-e,dsm[r,c-60:c+60],label='DSM centre-row')
        axes[2].set(xlabel='east of centre (m)',ylabel='LN02 elevation (m)');axes[2].legend(fontsize=7)
        fig.suptitle(name+'; context label only; raw points + derived rasters — ©swisstopo');fig.tight_layout();fig.savefig(out/(name+'-raw-raster.png'),dpi=140);plt.close(fig)


def textures(catalog, source, out):
    folder=out/'textures';folder.mkdir(exist_ok=True)
    images=[r for r in catalog['assets'] if r['product']=='swissimage-dop10']
    black_locations=[]
    for tr in range(8):
        for tc in range(8):
            x0,y0=tc*2500-5,tr*2500-5
            tile=np.zeros((3,2510,2510),np.uint8)
            for record in images:
                with rasterio.open(source/record['path']) as src:
                    sr=round((BOUNDS[3]-src.bounds.top)/.1);sc=round((src.bounds.left-BOUNDS[0])/.1)
                    left,top=max(x0,sc),max(y0,sr);right,bottom=min(x0+2510,sc+10000),min(y0+2510,sr+10000)
                    if left>=right or top>=bottom:continue
                    tile[:,top-y0:bottom-y0,left-x0:right-x0]=src.read(window=Window(left-sc,top-sr,right-left,bottom-top))
            # Only outside-AOI apron pixels are replicated; no source anomaly is painted over.
            if x0<0:tile[:,:,:5]=tile[:,:,5:6]
            if y0<0:tile[:,:5,:]=tile[:,5:6,:]
            if x0+2510>20000:tile[:,:,-5:]=tile[:,:,-6:-5]
            if y0+2510>20000:tile[:,-5:,:]=tile[:,-6:-5,:]
            Image.fromarray(tile.transpose(1,2,0)).save(folder/f'tile_{tr}_{tc}.png')
            # Count anomalies only in the non-overlapping 2500² core.
            rows,cols=np.where(np.all(tile[:,5:2505,5:2505]==0,axis=0))
            black_locations.extend([[BOUNDS[0]+(tc*2500+int(c)+.5)*.1,BOUNDS[3]-(tr*2500+int(r)+.5)*.1] for r,c in zip(rows,cols)])
        print('native imagery row',tr,flush=True)
    return {'count':len(black_locations),'positions_lv95':black_locations,'handling':'Retained unchanged in lossless PNG decode; outside-AOI apron only is edge replicated.'}


def patch_context(catalog, source, out):
    from PIL import ImageDraw
    canvas=Image.new('RGB',(1800,3*635+30),'white')
    draw=ImageDraw.Draw(canvas)
    for index,(name,(e,n)) in enumerate(PATCHES.items()):
        record=next(r for r in catalog['assets'] if r['product']=='swissimage-dop10' and r['actual_file']['bounds'][0]<=e<r['actual_file']['bounds'][2] and r['actual_file']['bounds'][1]<=n<r['actual_file']['bounds'][3])
        with rasterio.open(source/record['path']) as src:
            col,row=round((e-30-src.bounds.left)/.1),round((src.bounds.top-n-30)/.1)
            rgb=src.read(window=Window(col,row,600,600)).transpose(1,2,0)
        x,y=(index%3)*600,(index//3)*635
        draw.text((x+4,y+5),f'{name}: {e}, {n}; 60 m square, north up',fill='black')
        canvas.paste(Image.fromarray(rgb),(x,y+30))
    draw.text((8,3*635+8),'Source context at unchanged 10 cm distributed samples / 25 cm native information | ©swisstopo',fill='black')
    canvas.save(out/'patch-source-context.png')


def views(dsm):
    suite={'overview':{'position_m':[1000,1000,4600],'target_m':[1000,1000,0]}}
    for name,patch,offset in [('riffelhorn_oblique','summit',(220,-350,260)),('riffelhorn_structure','steep_face',(60,-120,80)),
                              ('loose_deposits','loose_deposits',(80,100,70)),('alpine_path','alpine_path',(70,110,55)),
                              ('water_edge','water_edge',(40,130,80)),('glacial_transition','glacial_transition',(140,160,120))]:
        e,n=PATCHES[patch];z=float(sample_grid(dsm,np.array([e]),np.array([n]))[0])-VERTICAL_ORIGIN
        target=np.array([e-BOUNDS[0],BOUNDS[3]-n,z]);position=target+offset
        suite[name]={'position_m':position.tolist(),'target_m':target.tolist()}
    for item in suite.values():
        distance=float(np.linalg.norm(np.array(item['position_m'])-item['target_m']))
        item['distance_to_target_m']=distance
        item['approx_perpendicular_screen_pixel_m']=2*distance*np.tan(np.radians(25))/1920
        item['horizontal_fov_degrees']=50;item['near_clip_m']=.1;item['far_clip']='Unreal perspective default, no explicit finite far plane'
    return suite


def project(repo, out):
    folder=out/'unreal';(folder/'Content/Python').mkdir(parents=True,exist_ok=True);(folder/'Config').mkdir(exist_ok=True)
    write_json(folder/'RiffelhornLab012B.uproject',{'FileVersion':3,'EngineAssociation':'5.8','Description':'Observed Swiss mountain representations; ©swisstopo','Plugins':[{'Name':'PythonScriptPlugin','Enabled':True},{'Name':'EditorScriptingUtilities','Enabled':True},{'Name':'AndroidFileServer','Enabled':False}]})
    write_json(folder/'lab012b-source.json',{'output_root':str(out)})
    shutil.copy2(repo/'scripts/earth_lab/unreal_riffelhorn_012b.py',folder/'Content/Python/lab012b.py')
    shutil.copy2(repo/'scripts/earth_lab/unreal_bluesky_012a.py',folder/'Content/Python/lab012a_common.py')
    prefix="import sys,unreal\nsys.path.insert(0,unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()+'Python'))\nimport lab012b\n"
    for kind in ('dtm','dsm'):
        (folder/f'Content/Python/setup_{kind}.py').write_text(prefix+f"lab012b.setup('{kind}')\n")
        for state in ('neutral','rgb'):
            (folder/f'Content/Python/capture_{kind}_{state}.py').write_text(prefix+f"unreal.EditorLoadingAndSavingUtils.load_map('/Game/Lab012B/{kind}')\nlab012b.comparisons('{kind}','{state}')\n")
    (folder/'Config/DefaultEngine.ini').write_text('[/Script/Engine.RendererSettings]\nr.DefaultFeature.AutoExposure=False\nr.DefaultFeature.MotionBlur=False\nr.DefaultFeature.Bloom=False\nr.AntiAliasingMethod=0\nr.TextureStreaming=True\n[/Script/Engine.Engine]\nNearClipPlane=10.0\n[/Script/WindowsTargetPlatform.WindowsTargetSettings]\nDefaultGraphicsRHI=DefaultGraphicsRHI_DX11\n')
    return folder


def build(repo,data,out):
    started=time.monotonic();out.mkdir(parents=True,exist_ok=True)
    catalog,source=source_catalog(repo,data)
    dtm=height_grid(catalog,source,'swissalti3d');dsm=height_grid(catalog,source,'swisssurface3d-raster')
    analyse(catalog,source,out,dtm,dsm)
    augment_analysis(out,dsm)
    black=textures(catalog,source,out)
    patch_context(catalog,source,out)
    geometry={}
    for kind,grid in (('dtm',dtm),('dsm',dsm)):
        folder=out/'meshes'/kind;folder.mkdir(parents=True,exist_ok=True);patches=[]
        for tr in range(8):
            for tc in range(8):
                arrays=mesh_arrays(grid,tr*500,tc*500);path=folder/f'tile_{tr}_{tc}.glb';write_glb(path,arrays)
                patches.append({'name':path.stem,'vertices':len(arrays[0]),'triangles':len(arrays[3])//3,'bounds_local_m':[arrays[0].min(0).tolist(),arrays[0].max(0).tolist()]})
            print('native surface mesh row',kind,tr,flush=True)
        geometry[kind]={'patches':patches,'unique_vertices':16000000,'triangles':2*3999**2,'submitted_vertices':sum(p['vertices'] for p in patches),'spacing_m':.5,'simplification':'none','lods':1,'bounds_lv95':[2624000.25,1091000.25,2625999.75,1092999.75]}
    files=sorted([*out.glob('meshes/*/*.glb'),*out.glob('textures/*.png'),*out.glob('raw-patches/*.npy'),out/'analysis.json',out/'overview-analysis.png',out/'patch-source-context.png',*out.glob('*-raw-raster.png')])
    manifest={'experiment':'Lab 012B — Riffelhorn mountain reconstruction','aoi':catalog['aoi'],
        'sources':[{'path':r['path'],'sha256':r['sha256'],'extracted_members':r.get('extracted_members',[])} for r in catalog['assets']],
        'geometry':geometry,'coordinate_frame':{'source':'EPSG:2056 horizontal / LN02 heights (EPSG:5728 provenance)','origin_lv95_northwest':[2624000,1093000],'vertical_origin_ln02_m':2500,'gltf':'X east, Y up, Z south; metres','unreal':'X east, Y south, Z up; centimetres, unit scale 100, no exaggeration'},
        'textures':{'tiles':64,'dimensions':[2510,2510],'apron_m':.5,'native_information_m':.25,'distributed_and_render_sample_m':.1,'policy':'Unchanged decoded RGB, lossless PNG, no sharpening/resizing; sRGB, uncompressed BGRA, simple-average mips, trilinear, clamped, LOD bias 0, fully resident for captures'},
        'black_pixels':black,'views':views(dsm),'licence':catalog['licence'],
        'render_settings':{'width':1920,'height':1080,'fov':50,'lighting':'Unlit colour × fixed analytic normal factor (0.65 + 0.35*max(dot(normal,(0.4,-0.3,0.8660254)),0)); no atmospheric or cast-shadow additions','exposure':'adaptation off, common tone treatment','rhi':'D3D11','geometry':'All native cell centres, same triangle diagonal, no Nanite/LOD/collision/smoothing; pixel-centre outer half-cell border not extrapolated'},
        'toolchain':{k:importlib.metadata.version(k) for k in ('numpy','rasterio','Pillow','matplotlib')},
        'products':[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)} for p in files],
        'temporal_limitations':catalog['temporal_compatibility']}
    manifest['identity']=__import__('hashlib').sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    write_json(out/'lab012b-manifest.json',manifest)
    write_json(out/'preparation-performance.json',{'seconds':time.monotonic()-started,'native_product_bytes':sum(p['bytes'] for p in manifest['products'])})
    project(repo,out)
    return manifest


def verify(repo,data,out):
    catalog,source=source_catalog(repo,data)
    report=json.loads((out/'lab012b-manifest.json').read_text());identity=report.pop('identity')
    if __import__('hashlib').sha256(json.dumps(report,sort_keys=True).encode()).hexdigest()!=identity:raise ValueError('Manifest identity changed')
    for product in report['products']:
        if digest(out/product['path'])!=product['sha256']:raise ValueError('Product changed')
    checks=0
    for kind,product in (('dtm','swissalti3d'),('dsm','swisssurface3d-raster')):
        grid=height_grid(catalog,source,product)
        for tr,tc in ((0,0),(3,3),(7,7)):
            payload=(out/'meshes'/kind/f'tile_{tr}_{tc}.glb').read_bytes();size=struct.unpack_from('<I',payload,12)[0];doc=json.loads(payload[20:20+size]);view=doc['bufferViews'][0]
            positions=np.frombuffer(payload,dtype='<f4',count=doc['accessors'][0]['count']*3,offset=20+size+8+view['byteOffset']).reshape(-1,3)
            r,c=tr*500,tc*500
            np.testing.assert_allclose(positions[0],[c*.5+.25,float(grid[r,c])-2500,r*.5+.25],rtol=0,atol=1e-4);checks+=1
    for tr,tc in ((0,0),(3,3),(7,7)):
        with Image.open(out/'textures'/f'tile_{tr}_{tc}.png') as image:
            for y,x in ((5,5),(1255,1255),(2504,2504)):
                row,col=tr*2500+y-5,tc*2500+x-5
                e,n=BOUNDS[0]+(col+.5)*.1,BOUNDS[3]-(row+.5)*.1
                record=next(r for r in catalog['assets'] if r['product']=='swissimage-dop10' and r['actual_file']['bounds'][0]<=e<r['actual_file']['bounds'][2] and r['actual_file']['bounds'][1]<=n<r['actual_file']['bounds'][3])
                with rasterio.open(source/record['path']) as src:
                    expected=next(src.sample([(e,n)]))
                if tuple(expected)!=image.getpixel((x,y)):raise ValueError('Native texture registration changed')
                checks+=1
    result={'result':'PASS','source_originals':16,'source_las':4,'product_hashes':len(report['products']),'independent_mesh_texture_samples':checks}
    write_json(out/'product-validation.json',result);return result


def validate_captures(out):
    """Check actual exported frames, comparison invariants and attribution."""
    from PIL import ImageDraw
    manifest=json.loads((out/'lab012b-manifest.json').read_text())
    reports={}
    for kind in ('dtm','dsm'):
        for state in ('neutral','rgb'):
            report=json.loads((out/f'captures-{kind}-{state}.json').read_text())
            if len(report['geometry_signature'])!=64:raise ValueError('Missing surface actors')
            for actor in report['geometry_signature']:
                if actor[2:8]!=[0]*6 or actor[8:]!=[1]*3:raise ValueError('Actor transform changed')
            if state=='rgb':
                if len(report['textures'])!=64:raise ValueError('Missing textures')
                if any(t['dimensions']!=[2510,2510] or not t['never_stream'] for t in report['textures']):raise ValueError('Texture representation changed')
            reports[kind,state]=report
        if reports[kind,'neutral']['geometry_signature']!=reports[kind,'rgb']['geometry_signature']:raise ValueError('Material switch changed geometry')
    folder=out/'captures/attributed';folder.mkdir(exist_ok=True)
    products=[];camera_checks=[]
    for view in manifest['views']:
        poses=[];row=Image.new('RGB',(1920,310),'white')
        for index,((kind,state),report) in enumerate(reports.items()):
            records=[r for r in report['captures'] if r['view']==view]
            if len(records)!=1:raise ValueError('Missing/duplicate fixed view')
            record=records[0];poses.append(record['camera_pose_cm_degrees'])
            expected=manifest['views'][view]
            delta=np.asarray(expected['target_m'])-expected['position_m']
            angles=[np.degrees(np.arctan2(delta[2],np.hypot(delta[0],delta[1]))),np.degrees(np.arctan2(delta[1],delta[0])),0,50]
            np.testing.assert_allclose(poses[-1][:3],np.asarray(expected['position_m'])*100,rtol=0,atol=.01)
            np.testing.assert_allclose(poses[-1][3:],angles,rtol=0,atol=.001)
            source=out/'captures/raw'/record['file']
            with Image.open(source) as image:
                if image.size!=(1920,1080):raise ValueError('Capture dimensions changed')
                image=image.convert('RGB')
                values=np.asarray(image)
                if values.max()-values.min()<10:raise ValueError('Blank capture')
                attributed=Image.new('RGB',(1920,1112),'white');attributed.paste(image,(0,0))
                ImageDraw.Draw(attributed).text((8,1090),f'Lab 012B | {view} | {kind} / {state} | native image information 25 cm, distributed grid 10 cm | ©swisstopo',fill='black')
                path=folder/record['file'];attributed.save(path)
                row.paste(image.resize((480,270),Image.Resampling.LANCZOS),(index*480,24))
                ImageDraw.Draw(row).text((index*480+4,5),f'{kind} / {state}',fill='black')
            products.append({'path':source.relative_to(out).as_posix(),'sha256':digest(source),'bytes':source.stat().st_size})
        if any(p!=poses[0] for p in poses):raise ValueError('Comparison camera moved')
        camera_checks.append({'view':view,'identical_pose':poses[0]})
        ImageDraw.Draw(row).text((8,295),f'{view} | 4x reduced inspection contact sheet; full captures retain 1920x1080 | ©swisstopo',fill='black')
        row.save(out/'captures'/f'comparison-{view}.png')
    for kind in ('dtm','dsm'):
        checks=json.loads((out/f'unreal-setup-{kind}.json').read_text())['checks']
        if sum(c['triangles'] for c in checks)!=manifest['geometry'][kind]['triangles']:raise ValueError('Unreal native topology changed')
    result={'result':'PASS','rendered_frames':len(products),'camera_checks':camera_checks,'capture_hashes':products,
            'texture_gpu_bytes_per_rgb_pass':sum(t['gpu_bytes'] for t in reports['dtm','rgb']['textures']),
            'unreal_vertices_per_surface':sum(c['vertices'] for c in json.loads((out/'unreal-setup-dtm.json').read_text())['checks']),
            'note':'Attribution derivatives add a 32-pixel footer without modifying the original frame; contact sheets are reduced inspection previews, not native-resolution outputs.'}
    assets=sorted((out/'unreal/Content/Lab012B').rglob('*.uasset'))+sorted((out/'unreal/Content/Lab012B').rglob('*.umap'))
    inventory={'source_identity':manifest['identity'],'files':[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)} for p in assets]}
    write_json(out/'unreal-assets.json',inventory)
    result['unreal_assets']={'files':len(assets),'bytes':sum(p['bytes'] for p in inventory['files']),'inventory_sha256':digest(out/'unreal-assets.json'),'note':'Compiled adapter assets are platform/editor products; byte-identical canonical rerun is claimed for the 209 offline products, not regenerated Unreal packages.'}
    write_json(out/'capture-validation.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');parser.add_argument('--prepare-renderer',action='store_true');parser.add_argument('--validate-captures',action='store_true');args=parser.parse_args()
    repo=Path(__file__).resolve().parents[2];data=resolve_storage_roots(repository_root=repo,require_data=True).data
    out=data/'experiments/earth-lab/riffelhorn-012b/observed-mountain-v1'
    if args.validate_captures:print(validate_captures(out))
    elif args.verify:print(verify(repo,data,out))
    elif args.prepare_renderer:print(project(repo,out))
    else:print('IDENTITY',build(repo,data,out)['identity'])
