"""Local Bluesky evaluation only: immutable ZIPs, native tiled RGB and DSM meshes."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import shutil
import struct
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import rasterio
from rasterio.windows import Window
from PIL import Image

import experiment_paths
from meridian_paths import resolve_storage_roots

RGB = {"rgb25":("25-RGB.zip",.25,4000),"rgb125":("12.5-RGB.zip",.125,8000),"rgb5":("5cm-RGB.zip",.05,20000)}
BOUNDS = (456000,339000,457000,340000)
CHUNK = 500  # DSM intervals: 125m; only last patch is 499 intervals.


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def locate(root,name):
    matches=list(root.rglob(name))
    # Exclude extracted/generated copies; preserve the original downloaded archive.
    if len(matches)!=1: raise ValueError(f"Expected one immutable {name}, found {len(matches)}")
    return matches[0]


def world_edges(values,width,height):
    a,d,b,e,c,f=values
    if b!=0 or d!=0 or a<=0 or e>=0: raise ValueError('Unexpected rotation/orientation')
    return (c-a/2,f+e*(height-.5),c+a*(width-.5),f-e/2)


def extract(archive,folder):
    folder.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            if Path(info.filename).name!=info.filename: raise ValueError('Unexpected archive paths')
            target=folder/info.filename
            if target.exists():
                with z.open(info) as src:
                    h=hashlib.sha256()
                    for block in iter(lambda:src.read(1024*1024),b''): h.update(block)
                if digest(target)!=h.hexdigest(): raise ValueError('Retained extraction changed')
            else:
                with z.open(info) as src,target.open('wb') as dst: shutil.copyfileobj(src,dst)


def validate(root,output):
    records={}
    for key,(name,res,size) in RGB.items():
        archive=locate(root,name); folder=output/'vendor-extracted'/key
        extract(archive,folder)
        values=[float(x) for x in (folder/'SK5639.jgw').read_text().split()]
        with rasterio.open(folder/'SK5639.jpg') as src:
            if (src.width,src.height,src.count,src.dtypes)!=(size,size,3,('uint8',)*3): raise ValueError('Unexpected imagery dimensions/bands')
            bounds=world_edges(values,size,size)
            if not np.allclose(bounds,BOUNDS,atol=1e-8,rtol=0): raise ValueError('Footprints differ')
            if abs(values[0]-res)>1e-10 or abs(values[3]+res)>1e-10: raise ValueError('Resolution mismatch')
            if tuple(src.bounds)!=BOUNDS: raise ValueError('GDAL and world-file interpretation differ')
            preview=src.read(out_shape=(3,1000,1000))
            embedded=src.tags();compression=src.tags(ns='IMAGE_STRUCTURE')
        Image.fromarray(preview.transpose(1,2,0)).save(output/f'{key}-inspection-overview.png')
        tab=(folder/'SK5639.tab').read_text() if (folder/'SK5639.tab').exists() else None
        xml={}
        if (folder/'SK5639.xml').exists():
            xml={n.tag.split('}')[-1]:n.text.strip() for n in ET.parse(folder/'SK5639.xml').iter() if n.text and n.text.strip() and not list(n)}
        crs_text=(folder/'SK5639.prj').read_text() if (folder/'SK5639.prj').exists() else None
        records[key]={"archive":'${MERIDIAN_DATA_ROOT}/'+archive.relative_to(root).as_posix(),"archive_sha256":digest(archive),
            "contained_files":[{"name":p.name,"bytes":p.stat().st_size,"sha256":digest(p)} for p in sorted(folder.iterdir())],
            "dimensions":[size,size],"bands":3,"dtype":"uint8","format":"JPEG; lossy vendor compression; renderer tiles are lossless decoded pixels",
            "pixel_size_m":res,"bounds":list(bounds),"world_file_pixel_centre":[values[4],values[5]],
            "crs":"OSGB36 British National Grid; EPSG:27700 convention","crs_evidence":"vendor PRJ/TAB" if crs_text else "vendor XML osgb:BNG and kmRectangle",
            "vendor_wkt":crs_text,"nodata":"No nodata mask/value supplied; black pixels remain data","orientation":"north at row 0; east at increasing column",
            "acquisition_metadata":xml,"date":"2018-09-01" if key=='rgb5' else "not supplied",
            "embedded_metadata":embedded,"image_structure":compression,
            "inconsistencies":(["TAB references SK5609.jpg; actual file, world file and TAB BNG coordinates identify SK5639"] if key=='rgb25' else [])+
                (["TAB control points differ from world-file pixel centres by (-resolution/2,+resolution/2); world-file centre convention is used"] if tab else []),
            "pixels_per_m2":1/res**2,"pixels_per_dsm_cell":(.25/res)**2,"uncompressed_rgb_bytes":size*size*3}
    archive=locate(root,'25cm-DSM-sample.zip'); folder=output/'vendor-extracted/dsm'; extract(archive,folder)
    with rasterio.open(folder/'SK5639_25cm_DSM.asc') as src:
        a=src.read(1,masked=True)
        if src.shape!=(4000,4000) or tuple(src.bounds)!=BOUNDS or src.res!=(.25,.25): raise ValueError('DSM footprint/grid mismatch')
        if np.ma.getmaskarray(a).any() or not np.isfinite(a).all(): raise ValueError('DSM has missing cells; do not invent heights')
        dsm=np.asarray(a,dtype=np.float32)
        records['dsm']={"archive":'${MERIDIAN_DATA_ROOT}/'+archive.relative_to(root).as_posix(),"archive_sha256":digest(archive),
            "contained_files":[{"name":p.name,"bytes":p.stat().st_size,"sha256":digest(p)} for p in folder.iterdir()],
            "dimensions":[4000,4000],"bands":1,"dtype":src.dtypes[0],"format":"ESRI ASCII grid, decimal heights",
            "pixel_size_m":.25,"bounds":list(src.bounds),"transform":list(src.transform)[:6],"nodata_value":src.nodata,"nodata_cells":0,
            "crs":"No DSM PRJ supplied; BNG interpretation supported by exact SK5639 grid bounds and paired sample packaging",
            "vertical_units":"Not encoded by ASCII header; metres used as an explicit sample-evaluation assumption; absolute vertical datum unspecified",
            "acquisition_date":"not supplied; co-acquisition with RGB not established","minimum":float(dsm.min()),"maximum":float(dsm.max())}
    registration={"all_pixel_edge_bounds_equal":True,"dsm_first_centre_bng":[456000.125,339999.875],
        "rgb_centres_in_first_dsm_cell":{k:records[k]['world_file_pixel_centre'] for k in RGB},
        "ratios_per_axis":{k:int(round(.25/records[k]['pixel_size_m'])) for k in RGB},
        "explanation":"DSM and 25cm RGB centres coincide. 12.5cm has four centres ±0.0625m about each DSM centre. 5cm has 25 centres at offsets -0.10,-0.05,0,+0.05,+0.10m on each axis. Edge footprints agree; this is numerical registration, not independent orthorectification-accuracy validation."}
    return records,registration,dsm


def mesh_arrays(dsm,r,c):
    h=min(CHUNK,3999-r)+1; w=min(CHUNK,3999-c)+1
    z=dsm[r:r+h,c:c+w]
    # Normals from the common whole DSM, restricted using a one-cell apron.
    ra=max(0,r-1); ca=max(0,c-1)
    block=dsm[ra:min(4000,r+h+1),ca:min(4000,c+w+1)]
    dy,dx=np.gradient(block,.25,edge_order=2)
    dx=dx[r-ra:r-ra+h,c-ca:c-ca+w];dy=dy[r-ra:r-ra+h,c-ca:c-ca+w]
    rr,cc=np.mgrid[r:r+h,c:c+w]
    positions=np.stack((cc*.25+.125,z-70,rr*.25+.125),axis=-1).astype('<f4').reshape(-1,3)
    normals=np.stack((-dx,np.ones_like(dx),-dy),axis=-1)
    normals=(normals/np.linalg.norm(normals,axis=-1,keepdims=True)).astype('<f4').reshape(-1,3)
    uv=np.stack(((cc-c)*.25+.375,(rr-r)*.25+.375),axis=-1).astype('<f4').reshape(-1,2)/125.5
    start=(np.arange(h-1)[:,None]*w+np.arange(w-1)[None,:]).ravel()
    triangles=np.stack((start,start+w,start+1,start+1,start+w,start+w+1),axis=1).astype('<u4').reshape(-1)
    return positions,normals,uv,triangles


def write_glb(path,arrays):
    positions,normals,uv,indices=arrays
    blobs=[x.tobytes() for x in arrays]; offsets=np.cumsum([0]+[len(x) for x in blobs[:-1]])
    views=[{"buffer":0,"byteOffset":int(o),"byteLength":len(b),"target":34963 if i==3 else 34962} for i,(o,b) in enumerate(zip(offsets,blobs))]
    accessors=[{"bufferView":i,"componentType":5125 if i==3 else 5126,"count":len(x),"type":('VEC3','VEC3','VEC2','SCALAR')[i]} for i,x in enumerate(arrays)]
    accessors[0].update(min=positions.min(0).tolist(),max=positions.max(0).tolist())
    doc={"asset":{"version":"2.0","generator":"Meridian Lab 012A native DSM"},"buffers":[{"byteLength":sum(map(len,blobs))}],
         "bufferViews":views,"accessors":accessors,"meshes":[{"name":path.stem,"primitives":[{"attributes":{"POSITION":0,"NORMAL":1,"TEXCOORD_0":2},"indices":3}]}],
         "nodes":[{"mesh":0}],"scenes":[{"nodes":[0]}],"scene":0}
    j=json.dumps(doc,separators=(',',':')).encode(); j+=b' '*((-len(j))%4)
    b=b''.join(blobs);b+=b'\0'*((-len(b))%4)
    with path.open('wb') as f:
        f.write(struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(b)))
        f.write(struct.pack('<II',len(j),0x4e4f534a)); f.write(j)
        f.write(struct.pack('<II',len(b),0x004e4942)); f.write(b)


def tiled_rgb(output,key,res):
    per=int(round(125/res)); apron=int(round(.25/res)); dimension=int(round(1000/res))
    folder=output/'textures'/key;folder.mkdir(parents=True,exist_ok=True)
    with rasterio.Env(GDAL_CACHEMAX=64*1024*1024),rasterio.open(output/'vendor-extracted'/key/'SK5639.jpg') as src:
        for tr in range(8):
            y=max(0,tr*per-apron);yend=min(dimension,(tr+1)*per+apron)
            # Decode a bounded row strip once; never decode the 20k image whole.
            strip=src.read(window=Window(0,y,dimension,yend-y))
            for tc in range(8):
                x=max(0,tc*per-apron);xend=min(dimension,(tc+1)*per+apron)
                tile=strip[:, :, x:xend].transpose(1,2,0)
                tile=np.pad(tile,((max(0,apron-tr*per),max(0,(tr+1)*per+apron-dimension)),
                                 (max(0,apron-tc*per),max(0,(tc+1)*per+apron-dimension)),(0,0)),mode='edge')
                Image.fromarray(tile).save(folder/f'tile_{tr}_{tc}.png')
            print('native texture strip',key,tr,flush=True)


def source_comparison(output):
    """Matched 20m native-data crops; diagnostic figure only, never a texture."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    regions=((425,520,'residential roof/garden'),(650,155,'urban roof/road'),(920,860,'parking/linear features'))
    fig,axes=plt.subplots(3,3,figsize=(15,15))
    for row,(x,y,label) in enumerate(regions):
        for col,(key,(_,res,_)) in enumerate(RGB.items()):
            with rasterio.open(output/'vendor-extracted'/key/'SK5639.jpg') as src:
                data=src.read(window=Window(round((x-10)/res),round((y-10)/res),round(20/res),round(20/res)))
            ax=axes[row,col]
            ax.imshow(data.transpose(1,2,0),extent=(x-10,x+10,y+10,y-10),interpolation='nearest')
            ax.set(title=f'{label} / {res}m native',xlabel='east from tile origin (m)',ylabel='south from tile origin (m)')
    fig.tight_layout();fig.savefig(output/'source-patch-comparison.png',dpi=120);plt.close(fig)


def build(root,output,geometry=True):
    output.mkdir(parents=True,exist_ok=True)
    sources,registration,dsm=validate(root,output)
    for key,(_,res,_) in RGB.items(): tiled_rgb(output,key,res)
    source_comparison(output)
    patches=[]; (output/'meshes').mkdir(exist_ok=True)
    for tr in range(8):
        for tc in range(8):
            arrays=mesh_arrays(dsm,tr*CHUNK,tc*CHUNK)
            path=output/'meshes'/f'tile_{tr}_{tc}.glb'
            if geometry: write_glb(path,arrays)
            patches.append({"name":path.stem,"row":tr,"column":tc,"vertices":len(arrays[0]),"triangles":len(arrays[3])//3,
                            "bounds_local_m":[arrays[0].min(0).tolist(),arrays[0].max(0).tolist()],"sha256":digest(path)})
        print('native mesh row',tr,flush=True)
    views={"overview":{"position_m":[500,520,1250],"target_m":[500,500,0]},
           "moderate":{"position_m":[430,680,230],"target_m":[430,500,15]},
           "low":{"position_m":[430,610,65],"target_m":[430,500,15]},
           "close":{"position_m":[402,543,36],"target_m":[425,520,12]}}
    report={"experiment":"Lab 012A — Bluesky high-resolution aerial reconstruction","sources":sources,"registration":registration,
        "toolchain":{name:importlib.metadata.version(name) for name in ('numpy','rasterio','Pillow','matplotlib')},
        "rights":"Local research/evaluation only. Archives contain copyright but no redistribution licence. No vendor imagery or renders are published by this Lab.",
        "confounds":"25cm/12.5cm imagery and DSM acquisition dates are unspecified; same-date/same-sensor derivation from 5cm is not established. Resolution/source comparisons are not a clean causal optical-resolution experiment.",
        "coordinate_frame":{"origin_bng":[456000,340000],"vertical_origin_assumed_m":70,"unreal":"X east, Y south, Z up; centimetres; no vertical exaggeration",
                            "gltf":"X east, Y up, Z south; metres; installed Unreal GLTF ConvertVec3 swaps Y/Z"},
        "geometry":{"unique_measured_vertices":16000000,"triangles":2*3999**2,"patches":patches,"submitted_vertices_including_shared_seams":sum(p['vertices'] for p in patches),
                    "spacing_m":.25,"smoothing":"none","simplification":"none; one triangulated common DSM across variants; imported LOD0 only",
                    "surface_bounds_bng":[456000.125,339000.125,456999.875,339999.875],"edge_limitation":"DSM samples are cell centres. Mesh spans 999.75m; outer 0.125m half-cell borders are not invented/extrapolated."},
        "textures":{"tiles_per_variant":64,"tile_footprint_m":125,"apron_m":.25,"dimensions_with_apron":{k:[int(125/res)+2*int(.25/res)]*2 for k,(_,res,_) in RGB.items()},
                    "policy":"Lossless PNG from full-size JPEG decode windows; no sharpening/downsampling. Out-of-AOI apron replicates edge texels only. Unreal sRGB, uncompressed, simple-average mipmaps, trilinear, clamped; natural mip selection may reduce effective detail at distance.",
                    "mip_base_bgra_bytes_per_variant":{k:64*(int(125/res)+2*int(.25/res))**2*4 for k,(_,res,_) in RGB.items()}},
        "views":views,"render_settings":{"width":1920,"height":1080,"horizontal_fov_degrees":50,"materials":"All variants unlit with identical analytic normal shading: colour*(0.65+0.35*max(dot(normal,(0.4,-0.3,0.8660254)),0)); neutral linear colour 0.5",
                                            "rhi":"Direct3D11 / SM5; separate variant processes for bounded memory",
                                            "atmosphere":"none","exposure":"fixed; adaptation disabled; identical engine tone treatment","geometry":"fixed LOD0; no Nanite/adaptive geometry"},
        "limitations":["Photogrammetric DSM is a heightfield: no vertical facades/overhangs, cannot create omitted subcell geometry","Orthophoto shadows are baked; extra analytic shading is identical across variants","EPSG convention/footprint verified, not independent survey-accuracy or absolute vertical-datum validation","Urban/suburban sample does not establish mountain surface observability"]}
    for view in report['views'].values():
        distance=float(np.linalg.norm(np.array(view['position_m'])-view['target_m']))
        view['distance_to_target_m']=distance
        view['approx_perpendicular_screen_pixel_m']=2*distance*np.tan(np.radians(25))/1920
        view['source_texels_per_screen_pixel']={k:view['approx_perpendicular_screen_pixel_m']/res for k,(_,res,_) in RGB.items()}
    # Canonical identity excludes mutable Unreal assets, later captures and caches.
    products=sorted((output/'textures').rglob('*.png'))+[output/f'{key}-inspection-overview.png' for key in RGB]+[output/'source-patch-comparison.png']
    report['products']=[{"path":p.relative_to(output).as_posix(),"bytes":p.stat().st_size,"sha256":digest(p)} for p in products]+[{"path":'meshes/'+p['name']+'.glb',"sha256":p['sha256'],"bytes":(output/'meshes'/ (p['name']+'.glb')).stat().st_size} for p in patches]
    report['identity']=hashlib.sha256(json.dumps(report,sort_keys=True).encode()).hexdigest()
    (output/'lab012a-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def project(repo,output):
    folder=output/'unreal'; (folder/'Content/Python').mkdir(parents=True,exist_ok=True); (folder/'Config').mkdir(exist_ok=True)
    descriptor={"FileVersion":3,"EngineAssociation":"5.8","Description":"Local Bluesky Lab 012A evaluation; no redistribution",
        "Plugins":[{"Name":"PythonScriptPlugin","Enabled":True},{"Name":"EditorScriptingUtilities","Enabled":True},{"Name":"AndroidFileServer","Enabled":False}]}
    (folder/'BlueskyLab012A.uproject').write_text(json.dumps(descriptor,indent=2))
    (folder/'lab012a-source.json').write_text(json.dumps({"output_root":str(output)},indent=2))
    shutil.copy2(repo/'scripts/earth_lab/unreal_bluesky_012a.py',folder/'Content/Python/lab012a.py')
    prefix="import sys,unreal\nsys.path.insert(0,unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()+'Python'))\nimport lab012a\n"
    (folder/'Content/Python/setup_all.py').write_text(prefix+'lab012a.setup()\n')
    (folder/'Content/Python/capture_all.py').write_text(prefix+"unreal.EditorLoadingAndSavingUtils.load_map('/Game/Lab012A/Lab012A')\nlab012a.comparisons()\n")
    for state in ('neutral','rgb25','rgb125','rgb5'):
        (folder/f'Content/Python/capture_{state}.py').write_text(prefix+"unreal.EditorLoadingAndSavingUtils.load_map('/Game/Lab012A/Lab012A')\n"+f"lab012a.comparisons(states=('{state}',),output_file='captures-{state}.json')\n")
    (folder/'Config/DefaultEngine.ini').write_text('[/Script/Engine.RendererSettings]\nr.DefaultFeature.AutoExposure=False\nr.DefaultFeature.MotionBlur=False\nr.DefaultFeature.Bloom=False\nr.AntiAliasingMethod=0\nr.TextureStreaming=True\n[/Script/WindowsTargetPlatform.WindowsTargetSettings]\nDefaultGraphicsRHI=DefaultGraphicsRHI_DX11\n')
    return folder


def verify_products(root,output):
    """Check all retained hashes plus independent native-value/registration samples."""
    report=json.loads((output/'lab012a-manifest.json').read_text())
    identity=report.pop('identity')
    if hashlib.sha256(json.dumps(report,sort_keys=True).encode()).hexdigest()!=identity: raise ValueError('Manifest identity differs')
    for source in report['sources'].values():
        archive=root/source['archive'].split('${MERIDIAN_DATA_ROOT}/')[1]
        if digest(archive)!=source['archive_sha256']: raise ValueError('Source archive changed')
    for product in report['products']:
        if digest(output/product['path'])!=product['sha256']: raise ValueError('Product hash differs: '+product['path'])
    source_pixel_checks=0
    for key,(_,res,_) in RGB.items():
        per=round(125/res);apron=round(.25/res)
        with rasterio.open(output/'vendor-extracted'/key/'SK5639.jpg') as src:
            for tr,tc in ((0,0),(3,3),(7,7)):
                with Image.open(output/'textures'/key/f'tile_{tr}_{tc}.png') as image:
                    for y,x in ((apron,apron),(per//2,per//2),(per,per)):
                        sy=tr*per+y-apron;sx=tc*per+x-apron
                        expected=src.read(window=Window(sx,sy,1,1))[:,0,0]
                        if tuple(expected)!=image.getpixel((x,y)): raise ValueError('Native RGB pixel changed')
                        source_pixel_checks+=1
    with rasterio.open(output/'vendor-extracted/dsm/SK5639_25cm_DSM.asc') as src:
        for tr,tc in ((0,0),(3,3),(7,7)):
            data=(output/'meshes'/f'tile_{tr}_{tc}.glb').read_bytes()
            size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size])
            pos=np.frombuffer(data,dtype='<f4',count=doc['accessors'][0]['count']*3,offset=20+size+8).reshape(-1,3)
            r,c=tr*500,tc*500
            expected_z=float(src.read(1,window=Window(c,r,1,1))[0,0])-70
            np.testing.assert_allclose(pos[0],[c*.25+.125,expected_z,r*.25+.125],atol=1e-5,rtol=0)
    result={'result':'PASS','archive_hashes':4,'product_hashes':len(report['products']),
            'native_rgb_pixel_checks':source_pixel_checks,'independent_dsm_mesh_samples':3}
    (output/'product-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--validate-only',action='store_true');mode.add_argument('--verify-products',action='store_true')
    mode.add_argument('--prepare-renderer',action='store_true');args=parser.parse_args()
    repo=Path(__file__).resolve().parents[2];root=resolve_storage_roots(repository_root=repo,require_data=True).data
    out=root/'experiments/earth-lab/bluesky-012a/native-surface-v1';out.mkdir(parents=True,exist_ok=True)
    if args.prepare_renderer:
        if not (out/'lab012a-manifest.json').is_file(): raise ValueError('Build native products first')
        print(project(repo,out))
    elif args.verify_products:
        print(json.dumps(verify_products(root,out),indent=2))
    elif args.validate_only:
        sources,registration,_=validate(root,out)
        report={"sources":sources,"registration":registration}
        (out/'source-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    else:
        report=build(root,out); print('IDENTITY',report['identity']); print('PROJECT',project(repo,out))
