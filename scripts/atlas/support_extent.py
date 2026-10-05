"""Inventory/support topology only. Never opens an elevation array or downloads DEMs."""
import argparse,hashlib,io,json,zipfile,time
from pathlib import Path
from collections import deque
import numpy as np
from seam_corridor import feasibility,boundary_cycle,array_hash

REPO=Path(__file__).resolve().parents[2]
CENTRE=(2625000,1092000)
CURRENT=(2620000,1087000,2630000,1097000)

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def identity(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def save(path,obj):
    Path(path).write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n',encoding='utf8')

def connected(mask,seeds):
    """Four-neighbour component flood; excludes diagonal-only contact."""
    reached=np.zeros(mask.shape,bool);q=deque()
    for r,c in np.argwhere(mask&seeds):
        if not reached[r,c]:reached[r,c]=True;q.append((int(r),int(c)))
    rows,cols=mask.shape
    while q:
        r,c=q.popleft()
        for rr,cc in [(r-1,c),(r,c+1),(r+1,c),(r,c-1)]:
            if 0<=rr<rows and 0<=cc<cols and mask[rr,cc] and not reached[rr,cc]:
                reached[rr,cc]=True;q.append((rr,cc))
    return reached

def extent(component,transform):
    r,c=np.where(component)
    west,north=transform*(c.min(),r.min());east,south=transform*(c.max()+1,r.max()+1)
    return [float(west),float(south),float(east),float(north)]

def tile_extent(bounds,margin):
    return [int(np.floor(min(bounds[0]-margin,CURRENT[0])/1000)*1000),
            int(np.floor(min(bounds[1]-margin,CURRENT[1])/1000)*1000),
            int(np.ceil(max(bounds[2]+margin,CURRENT[2])/1000)*1000),
            int(np.ceil(max(bounds[3]+margin,CURRENT[3])/1000)*1000)]

def tiles(bounds):
    if any(int(v)%1000 for v in bounds):raise ValueError('Whole kilometre tiles required')
    return {(x,y) for x in range(bounds[0]//1000,bounds[2]//1000) for y in range(bounds[1]//1000,bounds[3]//1000)}

def estimate(bounds):
    count=len(tiles(bounds));reuse=len(tiles(bounds)&tiles(CURRENT))
    return {'boundsLV95':bounds,'dimensionsKm':[(bounds[2]-bounds[0])/1000,(bounds[3]-bounds[1])/1000],
            'tiles':count,'areaKm2':count,'reuse':reuse,'new':count-reuse,
            'sourceBytesAreaEstimate':round(1667166026*count/100),
            'deliveryBytesAreaEstimate':round(930914852*count/100),
            'deliveryTilesAreaEstimate':round(11429*count/100),
            'notGenerated':True}

def obstruction_path(mask,seeds,targets):
    """Shortest-hop exclusion path to unknown coverage, not a terrain seam."""
    rows,cols=mask.shape;previous=np.full(mask.size,-2,np.int32);q=deque()
    for r,c in np.argwhere(mask&seeds):
        i=int(r*cols+c);previous[i]=-1;q.append(i)
    while q:
        i=q.popleft();r,c=divmod(i,cols)
        if targets[r,c]:
            path=[i]
            while previous[path[-1]]>=0:path.append(int(previous[path[-1]]))
            return np.asarray([divmod(i,cols) for i in path[::-1]],np.int32)
        for rr,cc in [(r-1,c),(r,c+1),(r+1,c),(r,c-1)]:
            if 0<=rr<rows and 0<=cc<cols:
                j=rr*cols+cc
                if mask[rr,cc] and previous[j]==-2:previous[j]=i;q.append(j)
    return None

def run(data,suffix):
    import rasterio,shapefile,pyproj
    from rasterio.features import rasterize
    from rasterio.transform import from_origin
    from rasterio.warp import transform_geom
    from assess_global_reference import buffer_mask
    start=time.perf_counter()
    plan=json.loads((REPO/'docs/atlas/support-extent-plan.json').read_text(encoding='utf8'))
    retained=json.loads((REPO/'docs/atlas/global-reference-acquisition.json').read_text(encoding='utf8'))['assets']
    boundary_root=data/'sources/atlas/riffelhorn/support-extent-assessment-v1'
    boundary=json.loads((boundary_root/'acquisition.json').read_text(encoding='utf8'))
    assert digest(boundary_root/'swiss-boundary-response.json')==boundary['sha256']
    catalogue=json.loads((boundary_root/'catalogue-checks.json').read_text(encoding='utf8'))
    for item in catalogue:
        assert item['assetNotDownloaded']
        assert digest(boundary_root/(item['item']+'.json'))==item['metadataSha256']
    country=json.loads((boundary_root/'swiss-boundary-response.json').read_text(encoding='utf8'))['results'][0]
    assert country['featureId']=='CH'
    bounds=plan['studyBoundsLV95'];features=[];assets={}
    for year in [1973,2016,2023]:
        key='sgi'+str(year);asset=retained[key];file=data/asset['path']
        assert digest(file)==asset['sha256']
        with zipfile.ZipFile(file) as z:
            prefix=f'SGI_{year}'+('' if year==1973 else '_glaciers')
            prj=z.read(prefix+'.prj').decode()
            encoding=z.read(prefix+'.cpg').decode().strip() if prefix+'.cpg' in z.namelist() else 'latin1'
            reader=shapefile.Reader(shp=io.BytesIO(z.read(prefix+'.shp')),dbf=io.BytesIO(z.read(prefix+'.dbf')),encoding=encoding)
            count=0
            for sr in reader.iterShapeRecords():
                x0,y0,x1,y1=sr.shape.bbox
                if x1<bounds[0]-500 or x0>bounds[2]+500 or y1<bounds[1]-500 or y0>bounds[3]+500:continue
                record=sr.record.as_dict()
                features.append({'year':year,'geometry':transform_geom(prj,'EPSG:2056',sr.shape.__geo_interface__),
                    'bbox':list(sr.shape.bbox),'id':record.get('sgi-id',record.get('SGI')),
                    'name':record.get('name'),'acquisitionYear':record.get('year_acq'),'attributes':record})
                count+=1
            assets[key]={k:asset[k] for k in ['path','url','sha256','bytes']}
            assets[key].update({'layer':prefix+'.shp','textEncoding':encoding,'intersectingFeatures':count,'sourceCrs':prj})
    out=data/('experiments/atlas/'+plan['version']+suffix)
    if (out/'manifest.json').exists():raise ValueError('Immutable output exists; use new sibling suffix')
    out.mkdir(parents=True,exist_ok=True)
    result={'baseline':plan['baseline'],'assets':assets,'boundary':boundary,'catalogueChecks':catalogue,'planSha256':hashlib.sha256((REPO/'docs/atlas/support-extent-plan.json').read_text(encoding='utf8').encode()).hexdigest(),
            'heightArraysRead':False,'elevationAssetsAcquired':False,'steps':{},
            'software':{'python':__import__('sys').version.split()[0],'numpy':np.__version__,'rasterio':rasterio.__version__,'gdal':rasterio.__gdal_version__,'pyproj':pyproj.__version__}}
    for step in plan['stepsMetres']:
        transform=from_origin(bounds[0],bounds[3],step,step)
        shape=((bounds[3]-bounds[1])//step,(bounds[2]-bounds[0])//step)
        yy,xx=np.mgrid[:shape[0],:shape[1]];east,north=transform*(xx+.5,yy+.5)
        radius=np.hypot(east-CENTRE[0],north-CENTRE[1]);protected=radius<=1500+step*np.sqrt(2)
        seed=tuple(np.unravel_index(np.argmin((east[:-1,:-1]+step/2-CENTRE[0])**2+(north[:-1,:-1]-step/2-CENTRE[1])**2),(shape[0]-1,shape[1]-1)))
        epochs={year:rasterize([(f['geometry'],1) for f in features if f['year']==year],out_shape=shape,transform=transform,all_touched=True,dtype='uint8').astype(bool) for year in [1973,2016,2023]}
        union=epochs[1973]|epochs[2016]|epochs[2023]
        territory=rasterize([(country['geometry'],1)],out_shape=shape,transform=transform,dtype='uint8').astype(bool)
        conservative_country=~buffer_mask(~territory,step,step)
        rows={'epochsAreaKm2':{str(y):float(a.sum()*step**2/1e6) for y,a in epochs.items()},'cases':{},'epochBorderChecks':{}}
        arrays={str(y):a for y,a in epochs.items()};arrays['country']=territory;arrays['protected']=protected
        for label,mask in [('recent2023',epochs[2023]),('historical1973',epochs[1973]),('unbufferedUnion',union)]:
            path=obstruction_path(mask|protected,protected,~territory)
            rows['epochBorderChecks'][label]={'connectedToUnknownTerritory':path is not None}
            if path is not None:
                r,c=path.T;arrays[label+'-border-obstruction']=path
                rows['epochBorderChecks'][label].update({'steps':len(path),'lengthMetres':int((len(path)-1)*step),
                    'endLV95':[float(east[r[-1],c[-1]]),float(north[r[-1],c[-1]])]})
        for buffer in plan['glacierBuffersMetres']:
            exclusion=buffer_mask(union,buffer,step)
            component=connected(exclusion|protected,protected)
            bbox=extent(component,transform)
            touched=bool(component[0].any() or component[-1].any() or component[:,0].any() or component[:,-1].any())
            minimum=tile_extent(bbox,200+step*np.sqrt(2));robust=tile_extent(bbox,500+step*np.sqrt(2))
            case={'componentBoundsLV95':bbox,'componentAreaKm2':float(component.sum()*step**2/1e6),
                  'touchesStudyEdge':touched,'southBeyondCurrentMetres':max(0,CURRENT[1]-bbox[1]),
                  'eastBeyondCurrentMetres':max(0,bbox[2]-CURRENT[2]),
                  'featuresTouchingComponent':[], 'candidates':{},
                  'minimumExtent':None if touched else minimum,'robustExtent':None if touched else robust,
                  'censoredRectangleCostEstimate':estimate(robust) if touched else None}
            for f in features:
                raster=rasterize([(f['geometry'],1)],out_shape=shape,transform=transform,all_touched=True,dtype='uint8').astype(bool)
                if (raster&component).any():case['featuresTouchingComponent'].append({k:f[k] for k in ['year','id','name','bbox','acquisitionYear']})
            arrays[f'buffer{buffer}']=exclusion;arrays[f'component{buffer}']=component
            choices=[('current',list(CURRENT))]
            choices += [('observedWindow',list(bounds))] if touched else [('minimumInventoryOnly',minimum),('robustInventoryOnly',robust)]
            for label,box in choices:
                edge=np.minimum.reduce([east-box[0],box[2]-east,north-box[1],box[3]-north])-step/2
                item=estimate(box);item['tests']={}
                for guard in plan['edgeGuardsMetres']:
                    permitted=(edge>=guard)&~exclusion&~protected
                    for country_gate in [False,True]:
                        a=permitted&conservative_country if country_gate else permitted
                        yes,reached,path=feasibility(a,np.zeros(shape),seed)
                        name=f'guard{guard}-'+('knownSwissInventorySupport' if country_gate else 'optimisticPlane')
                        entry={'enclosingCycle':bool(yes),'eligibleNodes':int(a.sum())}
                        if not yes:
                            arrays[f'{buffer}-{label}-{name}-escape']=path
                            entry['escapeFaces']=len(path)
                        else:
                            route=boundary_cycle(reached,seed);r,c=route.T
                            assert a[r,c].all()
                            entry['witnessVertices']=len(route)-1
                            entry['sourceEdgeMinimumMetres']=float(edge[r,c].min())
                            entry['protectedClearanceMinimumMetres']=float((radius[r,c]-1500).min())
                            entry['outsideSwissTerritoryVertices']=int((~territory[r,c]).sum())
                            arrays[f'{buffer}-{label}-{name}-cycle']=route
                        item['tests'][name]=entry
                case['candidates'][label]=item
            case['componentOutsideCountryCells']=int((component&~territory).sum())
            case['recentAreaKm2']=float((component&epochs[2023]).sum()*step**2/1e6)
            case['historicalOnlyAreaKm2']=float((component&epochs[1973]&~epochs[2016]&~epochs[2023]).sum()*step**2/1e6)
            case['crossSections']={}
            for line in [1090500,1087000,1085500]:
                r=int((bounds[3]-line)/step)
                indices=np.where(component[r])[0]
                case['crossSections'][str(line)]={'totalExcludedWidthMetres':int(len(indices)*step),
                    'westEastEnvelope':None if not len(indices) else [float(east[r,indices[0]]-step/2),float(east[r,indices[-1]]+step/2)],
                    'notNecessarilySingleGlacier':True}
            path=obstruction_path(exclusion|protected,protected,~territory)
            case['connectedToUnknownTerritory']=path is not None
            if path is not None:arrays[f'{buffer}-border-obstruction']=path
            print('EXTENT',step,buffer,bbox,'censored',touched,'countryConnected',case['componentOutsideCountryCells'],flush=True)
            rows['cases'][str(buffer)]=case
        np.savez_compressed(out/f'grid-{step}m.npz',**arrays)
        rows['arrayHashes']={k:array_hash(a) for k,a in arrays.items()};result['steps'][str(step)]=rows
        if step==25:
            old=data/'experiments/atlas/global-reference-assessment-v1/fields-and-mask.npz'
            with np.load(old) as retained_masks:old_ice=retained_masks['glacier250Mask']
            r0=(bounds[3]-CURRENT[3])//step;c0=(CURRENT[0]-bounds[0])//step
            rows['retained250MaskReproduced']=bool(np.array_equal(arrays['buffer250'][r0:r0+400,c0:c0+400],old_ice))
            assert rows['retained250MaskReproduced']
            render(out,features,transform,arrays,rows,bounds,country['geometry'])
    save(out/'measurements.json',result)
    files=[{'path':p.name,'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file()]
    manifest={'version':plan['version'],'planSha256':result['planSha256'],'toolSha256':hashlib.sha256(Path(__file__).read_text(encoding='utf8').encode()).hexdigest(),
              'inputs':{k:v['sha256'] for k,v in assets.items()},'boundarySha256':boundary['sha256'],
              'catalogueMetadataHashes':{r['item']:r['metadataSha256'] for r in catalogue},
              'helperHashes':{name:hashlib.sha256((REPO/'scripts/atlas'/name).read_text(encoding='utf8').encode()).hexdigest() for name in ['seam_corridor.py','assess_global_reference.py']},
              'files':files,'software':result['software'],
              'noElevationAccess':True,'noAcquisitionRecommendationAccepted':True}
    manifest['identity']=identity(manifest);save(out/'manifest.json',manifest)
    print('DONE',manifest['identity'],round(time.perf_counter()-start,2),flush=True)

def render(out,features,transform,arrays,rows,bounds,country):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle,Circle
    fig,axes=plt.subplots(1,3,figsize=(16,6))
    for ax,buffer in zip(axes,[100,250,500]):
        ax.imshow(np.where(arrays['country'],1,0),extent=[bounds[0],bounds[2],bounds[1],bounds[3]],cmap='Greys_r',alpha=.2)
        ax.imshow(np.where(arrays[f'buffer{buffer}'],1,np.nan),extent=[bounds[0],bounds[2],bounds[1],bounds[3]],cmap='Blues',vmin=0,vmax=1,alpha=.65)
        ax.contour(arrays[f'component{buffer}'],levels=[.5],colors='darkblue',linewidths=.8,extent=[bounds[0],bounds[2],bounds[1],bounds[3]])
        polygons=country['coordinates'] if country['type']=='MultiPolygon' else [country['coordinates']]
        for polygon in polygons:
            line=np.asarray(polygon[0]);ax.plot(line[:,0],line[:,1],color='black',linewidth=.7)
        ax.add_patch(Circle(CENTRE,1500,fill=False,color='red',label='Protected interior'))
        boxes={'current':('orange','Current support'),'observedWindow':('purple','Observed inventory window (NOT acquisition)')}
        for name,(colour,label) in boxes.items():
            if name not in rows['cases'][str(buffer)]['candidates']:continue
            b=rows['cases'][str(buffer)]['candidates'][name]['boundsLV95'];ax.add_patch(Rectangle((b[0],b[1]),b[2]-b[0],b[3]-b[1],fill=False,color=colour,linewidth=1,label=label))
        path=arrays.get(f'{buffer}-border-obstruction')
        if path is not None:
            r,c=path.T;e,n=transform*(c+.5,r+.5);ax.plot(e,n,color='red',lw=1,label='Exclusion path to unknown territory')
        for x in range(bounds[0],bounds[2]+1,1000):ax.axvline(x,color='gray',alpha=.13,lw=.5)
        for y in range(bounds[1],bounds[3]+1,1000):ax.axhline(y,color='gray',alpha=.13,lw=.5)
        for label,e,n in [('Riffelhorn benchmark',2625000,1092000),('Gorner (B56-07)',2629000,1089500),('Theodul (B56-28)',2622300,1088000),('Findel (B56-03)',2633000,1094000)]:
            ax.text(e,n,label,fontsize=7,bbox={'facecolor':'white','alpha':.65,'edgecolor':'none'})
        ax.set_xlim(bounds[0],bounds[2]);ax.set_ylim(bounds[1],bounds[3]);ax.set_aspect('equal');ax.set_title(f'SGI union +{buffer}m; national border black');ax.ticklabel_format(style='plain',useOffset=False);ax.tick_params(labelsize=7);ax.set_xlabel('LV95 easting (m)')
    axes[0].set_ylabel('LV95 northing (m)');axes[-1].legend(loc='upper right',fontsize=7)
    fig.suptitle('Inventory/support feasibility, not a terrain seam; SGI CC BY4.0 / national boundary ©swisstopo')
    fig.tight_layout();fig.savefig(out/'support-extent-map.png',dpi=140);plt.close(fig)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--suffix',default='');args=parser.parse_args()
    import re
    if args.suffix and not re.fullmatch(r'-[a-z0-9-]+',args.suffix):raise ValueError('Named immutable sibling only')
    import riffelhorn_terrain as rt
    run(rt.resolve_storage_roots(require_data=True).data,args.suffix)
