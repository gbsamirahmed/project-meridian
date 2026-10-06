"""Offline native-claim comparison; no image classification or application imports."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import fiona
import numpy as np
import rasterio
import xlrd
from pyproj import Geod, Transformer
from shapely import force_2d, points
from shapely.geometry import box, shape, mapping
from shapely.ops import unary_union
from shapely.strtree import STRtree

WC = {0:'No data',10:'Tree cover',20:'Shrubland',30:'Grassland',40:'Cropland',50:'Built-up',60:'Bare / sparse vegetation',70:'Snow and ice',80:'Permanent water bodies',90:'Herbaceous wetland',95:'Mangroves',100:'Moss and lichen'}
PLAN = Path('docs/atlas/semantic-comparison-plan.json')
PLAN_SHA = '62739330a5931120dbdcf14743b5be6f8acc5da5dfc3acbe6747e0aaa0daacd7'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')

def patch_box(p):
    x,y=p['centre']; r=p['side']/2
    return box(x-r,y-r,x+r,y+r)

def mosaic(label):
    """Published composition, never a spatial allocation or confidence."""
    return [{'percent':float(n),'code':c.strip()} for n,c in re.findall(r'(\d+(?:\.\d+)?)%\s*([^,]+)',label)]

def nrw_mapping(code, label):
    if label.startswith('Mosaic of:'):
        return {'relation':'PARTIAL OVERLAP','concept':'mixed habitat composition','loss':'Components and percentages belong to original mosaic support; no within-patch fractions or locations.'}
    if code=='?':
        return {'relation':'UNMAPPABLE','concept':None,'loss':'Original habitat code illegible; other mosaic components remain known.'}
    if code=='NA':
        return {'relation':'UNMAPPABLE','concept':None,'loss':'Not accessed land: observation absence, not physical absence.'}
    if code.startswith('A.') or code in ['D.1.1','D.2']:
        return {'relation':'NARROWER','concept':'woody vegetation','loss':'Growth form, planting, ecology and mixed ground cover.'}
    if code=='C.2':
        return {'relation':'PARTIAL OVERLAP','concept':'vegetation / ledge habitat','loss':'Ecological habitat and landform; not a pure vegetation fraction.'}
    if code.startswith(('B.','C.')) or code=='D.3':
        return {'relation':'NARROWER','concept':'nonwoody vegetation','loss':'Species, management, substrate and ecological conditions.'}
    if code=='D.5':
        return {'relation':'PARTIAL OVERLAP','concept':'vegetation','loss':'Mixed heath/grassland and conflicting Welsh/JNCC wet/dry names.'}
    if code.startswith('E.'):
        return {'relation':'PARTIAL OVERLAP','concept':'vegetation / wet substrate','loss':'Mire ecology and hydrological regime; not equivalent to open water.'}
    if code.startswith('G.'):
        return {'relation':'NARROWER','concept':'water','loss':'Standing/running distinction; no contemporaneous inundation extent.'}
    if code.startswith('I.'):
        return {'relation':'NARROWER','concept':'mineral exposure inventory','loss':'Rock/scree and acid/neutral distinction; exposure inventory not bare-percentage field.'}
    if code=='J.3.6':
        return {'relation':'NARROWER','concept':'artificial structure','loss':'Building identity versus general built cover.'}
    return {'relation':'UNMAPPABLE','concept':None,'loss':'Legend interpretation not established.'}

def checked_geometry(g, identity):
    geom=force_2d(shape(g))
    if not geom.is_valid:
        raise ValueError('Invalid native geometry: '+str(identity))
    return geom

def load_features(path, key='features'):
    data=json.loads(path.read_text(encoding='utf-8'))
    if 'totalFeatures' in data and data['totalFeatures']!=len(data[key]):
        raise ValueError('Truncated WFS response')
    result=[]
    for f in data[key]:
        identity=f.get('id',f.get('featureId'))
        result.append({'id':identity,'properties':f['properties'],'geometry':checked_geometry(f['geometry'],identity)})
    return result

def vector_summary(fs, region, label):
    groups=defaultdict(list); intersecting=[]
    for f in fs:
        g=f['geometry'].intersection(region)
        if g.area<=0: continue
        key=str(label(f['properties']))
        groups[key].append(g);intersecting.append(f)
    raw_areas={k:unary_union(gs).area for k,gs in sorted(groups.items())}
    areas={k:round(v,3) for k,v in raw_areas.items()}
    union=unary_union([f['geometry'].intersection(region) for f in intersecting])
    return {'featureIds':sorted([str(f['id']) for f in intersecting]),'nativeAreaM2':areas,'unionAreaM2':round(union.area,3),'uncoveredAreaM2':round(region.area-union.area,3),'groupOverlapM2':round(max(0,sum(raw_areas.values())-union.area),3)}

def raster_points(path, crs):
    with rasterio.open(path) as src:
        data=src.read(1);tr=src.transform
        rows,cols=np.indices(data.shape)
        lon=tr.c+(cols+.5)*tr.a; lat=tr.f+(rows+.5)*tr.e
        transformer=Transformer.from_crs(src.crs,crs,always_xy=True)
        x,y=transformer.transform(lon,lat)
        try:
            used=transformer.get_last_used_operation()
            operation={'description':used.description,'declaredAccuracyM':used.accuracy}
        except RuntimeError:
            operation={'description':transformer.description,'declaredAccuracyM':transformer.accuracy}
        geod=Geod(ellps='WGS84'); weights=[]
        for row in range(data.shape[0]):
            lo=tr.c;la=tr.f+row*tr.e
            area,_=geod.polygon_area_perimeter([lo,lo+tr.a,lo+tr.a,lo],[la,la,la+tr.e,la+tr.e])
            weights.append(abs(area))
        area=np.broadcast_to(np.array(weights)[:,None],data.shape).flatten()
        east=geod.inv(tr.c,tr.f,tr.c+tr.a,tr.f)[2]
        north=abs(geod.inv(tr.c,tr.f,tr.c,tr.f+tr.e)[2])
        return data.flatten(),points(np.asarray(x).flatten(),np.asarray(y).flatten()),area,{'projectionOperation':operation,'crs':str(src.crs),'shape':list(data.shape),'angularStep':abs(tr.a),'topRowCellDimensionsM':[round(east,3),round(north,3)],'nodata':src.nodata}

def point_pairs(values, pts, weights, fs, label):
    out=defaultdict(float); matched=np.zeros(len(pts),dtype=bool)
    if fs:
        tree=STRtree([f['geometry'] for f in fs])
        # Point covered by polygon, including its boundary; retain multiple claims.
        pairs=tree.query(pts,predicate='intersects')
        for pi,fi in pairs.T:
            key=str(int(values[pi]))+' | '+str(label(fs[fi]['properties']))
            out[key]+=float(weights[pi]);matched[pi]=True
    return {'nativePairsM2':{k:round(v,3) for k,v in sorted(out.items())},'unmatchedCentreAreaM2':round(float(weights[~matched].sum()),3),'warning':'Cell-centre area approximation; multiple vector claims remain multiple, not exclusive. No accuracy or simultaneity implied.'}

def glamos_features(root, region):
    out={}
    for layer in ['SGI_2016_glaciers','SGI_2016_debriscover']:
        fs=[];raw=[]
        with fiona.open('zip://'+str(root/'glamos.zip'),layer=layer) as src:
            if src.crs.to_epsg()!=2056:raise ValueError('Unexpected GLAMOS CRS')
            for f in src.filter(bbox=region.bounds):
                g=checked_geometry(f['geometry'],f['id'])
                if g.intersection(region).area<=0:continue
                props=dict(f['properties']);fs.append({'id':f['id'],'properties':props,'geometry':g})
                raw.append({'type':'Feature','id':f['id'],'properties':props,'geometry':mapping(g)})
        save(root/(layer+'-subset.json'),{'type':'FeatureCollection','nativeCrs':'EPSG:2056','features':raw})
        out[layer]=fs
    return out

def legend(root):
    sheet=xlrd.open_workbook(root/'jncc-codes.xls').sheet_by_name('Habitat list')
    result={}
    for i in range(1,sheet.nrows):
        row=sheet.row_values(i);code=str(row[6]).strip()
        if code:result[code]={'welshName':str(row[7]),'jnccCode':str(row[0]),'jnccName':str(row[5])}
    return result

def compare(root):
    if sha(PLAN)!=PLAN_SHA:raise ValueError('Frozen plan changed')
    receipt=json.loads((root/'acquisition.json').read_text())
    frozen_sources=Path('docs/atlas/semantic-comparison-sources.json')
    if frozen_sources.exists():
        for f in json.loads(frozen_sources.read_text(encoding='utf-8'))['files']:
            if f.get('sha256') and sha(root/f['file'])!=f['sha256']:
                raise ValueError('Frozen source identity differs: '+f['file'])
    for f in receipt['files']:
        if f.get('sha256') and sha(root/f['file'])!=f['sha256']:raise ValueError('Source hash changed: '+f['file'])
    plan=json.loads(PLAN.read_text());leg=legend(root)
    nrw=load_features(root/'nrw-vegetation-full-features.json')
    surveys=load_features(root/'nrw-survey-area.json')
    bedrock=load_features(root/'geocover-bedrock.json','results')
    unco=load_features(root/'geocover-unconsolidated.json','results')
    gl=glamos_features(root,box(*plan['sites']['riffelhorn']['bounds']))
    results={'planSha256':PLAN_SHA,'method':'Native grid cell-centres, ellipsoidal cell area; metre-CRS vector intersections. No semantic resampling. Centre-area and polygon areas have different boundary support.','sites':{},'sourceReceipts':receipt}
    native_codes={f['properties']['phase1_code'] for f in nrw}
    native_codes.update(c['code'] for f in nrw for c in mosaic(f['properties']['label']))
    results['nrwLegend']={c:leg.get(c,{'meaning':'not established'}) for c in sorted(native_codes) if c!='mosaic'}
    results['nrwCrosswalk']=[{'code':c,**nrw_mapping(c,'')} for c in sorted(native_codes) if c!='mosaic']
    results['nrwRecordCounts']={'vegetation':len(nrw),'surveyAreas':len(surveys),'geocoverBedrock':len(bedrock),'geocoverUnconsolidated':len(unco)}
    results['nrwMosaicRecords']=[{'id':f['id'],**{k:f['properties'].get(k) for k in ['label','phase1_code','voronoi_uid','mosaicpoly','original_unique_id','survey','area_ha']}} for f in nrw if f['properties']['label'].startswith('Mosaic of:')]
    results['nrwMosaics']=sorted({f['properties']['label'] for f in nrw if f['properties']['label'].startswith('Mosaic of:')})
    results['glamosNativeRecords']=[{'layer':name,'id':f['id'],**f['properties']} for name,fs in gl.items() for f in fs]
    for site,s in plan['sites'].items():
        vals,pts,weights,grid=raster_points(root/(site+'-worldcover.tif'),s['crs'])
        regions={'window':box(*s['bounds']),**{p['id']:patch_box(p) for p in s['patches']}}
        layers=({'nrw':(nrw,lambda p:p['phase1_code']+' | '+p['label']),'surveyArea':(surveys,lambda p:p['areaname']+' | '+p['surveydates'])} if site=='tryfan' else {'bedrock':(bedrock,lambda p:p['label']),'unconsolidated':(unco,lambda p:p['label']),'glacier':(gl['SGI_2016_glaciers'],lambda p:p['sgi-id']+' | '+str(p['year_acq'])),'debris':(gl['SGI_2016_debriscover'],lambda p:p['sgi-id']+' | '+str(p['year_acq']))})
        output={'grid':grid,'regions':{}}
        for name,reg in regions.items():
            mask=reg.covers(pts);v=vals[mask];p=pts[mask];w=weights[mask]
            stats={'bounds':list(reg.bounds),'polygonAreaM2':reg.area,'rasterCentreAreaM2':round(float(w.sum()),3),'rasterCells':int(mask.sum()),'worldcover':{str(c):{'label':WC[int(c)],'cells':int((v==c).sum()),'centreAreaM2':round(float(w[v==c].sum()),3)} for c in np.unique(v)},'vectors':{}}
            for layer,(fs,label) in layers.items():
                stats['vectors'][layer]={'areas':vector_summary(fs,reg,label),'pairs':point_pairs(v,p,w,fs,label)}
            if site=='riffelhorn':
                gu=unary_union([f['geometry'] for f in gl['SGI_2016_glaciers']]);du=unary_union([f['geometry'] for f in gl['SGI_2016_debriscover']])
                stats['debrisWithinGlacierM2']=round(reg.intersection(gu).intersection(du).area,3)
            output['regions'][name]=stats
        results['sites'][site]=output
    results['crosswalkScope']='Native claim -> common property, not source -> winner. Broader/narrower refer to semantic extension, not grain.'
    results['worldcoverCrosswalk']={str(c):{'native':WC[c],'concept':('woody vegetation' if c in [10,20,95] else 'nonwoody vegetation' if c in [30,100] else 'artificial cover' if c==50 else 'mineral exposure with sparse vegetation' if c==60 else 'persistent snow/ice cover' if c==70 else 'persistent water cover' if c==80 else 'vegetated wetland' if c==90 else None),'relation':('COMPATIBLE' if c in [50,60,70,80,90] else 'NARROWER' if c in [10,20,30,95,100] else 'UNMAPPABLE')} for c in WC}
    results['otherCrosswalk']=[{'native':'WorldCover 60','target':'exposed bedrock or scree specifically','relation':'PARTIAL OVERLAP','loss':'soil/sand/rock and sparse vegetation cannot be separated'}, {'native':'WorldCover 70','target':'persistent ice cover only','relation':'BROADER','loss':'snow versus ice'}, {'native':'WorldCover 70','target':'glacier membership','relation':'AMBIGUOUS','loss':'no object identity; snow and debris distinctions'}, {'native':'GeoCover bedrock unit','target':'current exposed rock cover','relation':'UNMAPPABLE','loss':'subsurface/geological claim cannot establish exposure'}, {'native':'GLAMOS SGI glacier outline','target':'glacier inventory membership at feature epoch','relation':'COMPATIBLE','loss':'none for membership; geometric/epoch uncertainty remains'}, {'native':'GLAMOS debris cover','target':'loose mineral cover above identified glacier','relation':'NARROWER','loss':'source material and glacier identity if reduced to mineral-only category'}]
    save(root/'results.json',results)
    print('Results saved',root/'results.json')
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--publish',action='store_true',help='Write the lightweight repository summary, never source payloads')
    args=parser.parse_args();result=compare(args.data)
    if args.publish:
        result.pop('sourceReceipts')
        result['sourceManifest']='semantic-comparison-sources.json'
        result['sourceManifestSha256']=sha('docs/atlas/semantic-comparison-sources.json')
        save('docs/atlas/semantic-comparison-results.json',result)
