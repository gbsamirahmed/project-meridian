"""Offline native-claim comparisons for the frozen water check, not a semantic contract.
Polygon intersections are geometric support; native raster centre counts are not accuracy.
"""
import argparse, collections, hashlib, json
from pathlib import Path
import numpy as np, rasterio
from pyproj import Transformer
from shapely import contains_xy
from shapely.geometry import box, shape
from shapely.ops import unary_union
from water_sources import PLAN, PLAN_HASH, sha, save

def read_vectors(root,key):
 d=json.loads((root/(key+'.geojson')).read_text())
 if d.get('crs',{}).get('properties',{}).get('name')!='urn:ogc:def:crs:EPSG::27700':raise ValueError('Native vector CRS must be explicit BNG')
 if d.get('numberMatched')!=len(d['features']):raise ValueError('Incomplete vector query')
 fs=[]
 for f in d['features']:
  g=shape(f['geometry'])
  if not g.is_valid:raise ValueError('Invalid native geometry; no silent repair')
  fs.append((g,{'featureId':f.get('id'),**f['properties']}))
 return fs

def union_area(features,region):
 return float(unary_union([g.intersection(region) for g,_ in features]).area) if features else 0.0

def grouped_areas(features,region,field):
 groups=collections.defaultdict(list)
 for g,p in features:
  if g.intersects(region):groups[str(p.get(field))].append((g,p))
 return {k:round(union_area(v,region),3) for k,v in sorted(groups.items())}

def native_codes(value):
 return [c.strip() for c in str(value).split(',') if c.strip()]

def monthly_meaning(code):
 # Source-native GSW history, including explicit no-observation code.
 return {0:'no observations',1:'water not detected',2:'water detected'}[int(code)]

def occurrence_summary(values):
 v=np.asarray(values);ok=v!=255;v=v[ok]
 if np.any((v<0)|(v>100)):raise ValueError('Unknown occurrence code')
 return {'cellCentres':int(len(values)),'noData255':int((~ok).sum()),'notWater0':int((v==0).sum()),'positiveOccurrence1to99':int(((v>0)&(v<100)).sum()),'occurrence100':int((v==100).sum()),'meanOccurrencePercent':round(float(v.mean()),3) if len(v) else None,'positiveRange':list(map(int,[v[v>0].min(),v[v>0].max()])) if np.any(v>0) else None}

def decode_monthly(values):
 c=collections.Counter(map(int,values));return {monthly_meaning(k):c[k] for k in sorted(c)}

def event_period(p):
 a,b=p.get('start_date'),p.get('end_date')
 if not a or not b or a.startswith('2050') or b.startswith('2050'):return {'status':'unknown event time','nativeStart':a,'nativeEnd':b}
 if b<a:raise ValueError('Reversed event dates')
 return {'status':'published event interval; timestamp precision not established','nativeStart':a,'nativeEnd':b}

# Deliberately small research crosswalk. Loss never replaces native properties.
CROSSWALK = [
 {'native':'WFD GB510804505600 EXE','concept':'named waterbody / assessment-unit membership','relationship':'compatible','loss':'Identity needs its WFD namespace; administrative segmentation, heavily-modified designation and source reference boundary remain native. Not instantaneous wet extent.'},
 {'native':'WFD MHW-derived polygon','concept':'reference waterbody boundary','relationship':'compatible','loss':'OS/UWWTD source convention and simplification must remain; actual survey date/tidal datum details unknown.'},
 {'native':'GSW monthly code2','concept':'dated water-detection claim','relationship':'compatible','loss':'Month/cell and classification lineage mandatory; no instantaneous edge, depth, tide or feature identity.'},
 {'native':'GSW occurrence1-100','concept':'historical water-detection occurrence','relationship':'compatible','loss':'Keep numeric value and observation-conditioned period; binary water discards history, no present-state equivalence.'},
 {'native':'PHI SALTM','concept':'wetland-related habitat property','relationship':'narrower','loss':'Saltmarsh vegetation, saline/intertidal context and habitat ontology lost in broad wetland label; not open-water state.'},
 {'native':'PHI RBEDS','concept':'wetland-related vegetation property','relationship':'narrower','loss':'Reed vegetation/ecological definition and mixed-habitat co-membership lost.'},
 {'native':'PHI CFPGM','concept':'wetland-related habitat property','relationship':'partial','loss':'Periodically inundated pasture/meadow, ditch system and management meaning not equivalent to saturated/open water everywhere.'},
 {'native':'PHI MUDFL','concept':'intertidal habitat claim','relationship':'compatible','loss':'Fine sediment/ecology and native extent/grain remain; current water presence cannot be inferred.'},
 {'native':'FZ2/FZ3','concept':'reference-conditioned planning probability-zone claim','relationship':'compatible','loss':'AEP/source/defence convention and mixed origins retained; this is neither a dated inundation state nor local pixel confidence.'},
 {'native':'RFO outline/event group','concept':'historical event-associated inundation record','relationship':'compatible','loss':'Event ID, interval, boundary evidence, cause and quality retained; footprint need not be synchronous maximum at every point.'},
 {'native':'WFD / PHI / Flood Zones','concept':'water present now','relationship':'incompatible','loss':'Reference/habitat/scenario claim cannot be relabelled as current observed state.'},
 {'native':'GSW monthly code0','concept':'physical water absence','relationship':'unmappable','loss':'No valid observations; physical state unknown.'},
 {'native':'PHI combined RBEDS,SALTM','concept':'one dominant exclusive surface class','relationship':'ambiguous','loss':'Native co-membership provides no fractional split or dominant label.'},
 {'native':'current state unknown','concept':'water-related property','relationship':'broader','loss':'Generic water-related category merges feature, state, habitat and scenario; deliberately rejected as sole interpretation.'}]

def analyse(root,out):
 if sha(PLAN)!=PLAN_HASH:raise ValueError('Plan changed')
 plan=json.loads(PLAN.read_text());receipt=json.loads((root/'acquisition.json').read_text())
 pinned=json.loads(Path('docs/atlas/water-check-sources.json').read_text())
 pinnedHashes={f['file']:f['sha256'] for f in pinned['files'] if f.get('sha256')}
 receiptHashes={f['file']:f['sha256'] for f in receipt['files'] if f.get('sha256')}
 if pinnedHashes!=receiptHashes:raise ValueError('External receipt differs from Git-pinned source identity')
 for f in receipt['files']:
  if f.get('sha256') and sha(root/f['file'])!=f['sha256']:raise ValueError('Source hash mismatch '+f['file'])
 if not receipt['freezeOrderVerified']:raise ValueError('Freeze order failed')
 note=json.loads(Path('docs/atlas/water-check-acquisition-note.json').read_text())
 rfoReceipt=next(f for f in receipt['files'] if f['file']=='rfo.geojson')
 if rfoReceipt['retrievedUtc']<=note['recordedUtc']:raise ValueError('RFO addition must precede its retrieval')
 fs={k:read_vectors(root,k) for k in ['wfd','phi','flood','rfo']}
 region=box(*plan['bounds']);counts={k:{'returned':len(v),'exactIntersections':sum(g.intersects(region) for g,_ in v),'positiveAreaIntersections':sum(g.intersection(region).area>0 for g,_ in v)} for k,v in fs.items()}
 rasters={};coords=None
 for n in ['occurrence','monthly-2024-03','monthly-2024-09']:
  with rasterio.open(root/(n+'.tif')) as src:
   if str(src.crs)!='EPSG:4326':raise ValueError('Expected native geographic grid')
   a=src.read(1);rows,cols=np.indices(a.shape);xx,yy=src.transform*(cols+.5,rows+.5)
   x,y=Transformer.from_crs(4326,27700,always_xy=True).transform(xx,yy)
   if coords is not None and not (np.array_equal(x,coords[0]) and np.array_equal(y,coords[1])):raise ValueError('Native raster grids differ')
   coords=x,y;rasters[n]=a
 x,y=coords
 def raster_stats(r):
  m=contains_xy(r,x,y);a=rasters['monthly-2024-03'][m];b=rasters['monthly-2024-09'][m]
  both=(a!=0)&(b!=0)
  return {'occurrence':occurrence_summary(rasters['occurrence'][m]),'March2024':decode_monthly(a),'September2024':decode_monthly(b),'bothMonthsObserved':int(both.sum()),'MarchDetectedSeptemberNotDetected':int(((a==2)&(b==1)).sum()),'SeptemberDetectedMarchNotDetected':int(((a==1)&(b==2)).sum()),'anyMonthUnobserved':int(((a==0)|(b==0)).sum())}
 probes=[]
 for p in plan['probes']:
  r=box(*p['bounds']);hits={k:[(g,props) for g,props in v if g.intersection(r).area>0] for k,v in fs.items()}
  probes.append({'id':p['id'],'name':p['name'],'bounds':p['bounds'],'areaM2':r.area,'wfd':{'areaM2':round(union_area(hits['wfd'],r),3),'nativeIdentities':[{k:q.get(k) for k in ['featureId','water_body_id','water_body_name','classification_year','export_date']} for _,q in hits['wfd']]},'phi':{'nativeHabitatsAreaM2':grouped_areas(hits['phi'],r,'mainhabs'),'nativeClaims':[{k:q.get(k) for k in ['featureId','uid','mainhabs','habcodes','addhabs','primsource','version']} for _,q in hits['phi']]},'flood':{'zonesAreaM2':grouped_areas(hits['flood'],r,'flood_zone'),'originAreaM2':grouped_areas(hits['flood'],r,'origin')},'rfo':{'unionAreaM2':round(union_area(hits['rfo'],r),3),'claims':[{**q,'interpretedTime':event_period(q),'intersectionAreaM2':round(g.intersection(r).area,3)} for g,q in hits['rfo']]},'raster':raster_stats(r)})
 wfd=unary_union([g.intersection(region) for g,_ in fs['wfd']]);fz=unary_union([g.intersection(region) for g,_ in fs['flood']]);hab={}
 for code in ['MUDFL','SALTM','RBEDS','CFPGM']:
  h=unary_union([g.intersection(region) for g,p in fs['phi'] if code in native_codes(p.get('habcodes',''))]);hab[code]={'unionAreaM2':round(h.area,3),'withinWfdAreaM2':round(h.intersection(wfd).area,3),'withinFloodZoneAreaM2':round(h.intersection(fz).area,3),'raster':raster_stats(h)}
 rfos=[{**p,'interpretedTime':event_period(p),'withinBenchmarkAreaM2':round(g.intersection(region).area,3)} for g,p in fs['rfo'] if g.intersection(region).area>0]
 result={'planSha256':PLAN_HASH,'acquisitionNoteSha256':sha('docs/atlas/water-check-acquisition-note.json'),'sourceFiles':{f['file']:f['sha256'] for f in receipt['files'] if f.get('sha256')},'crs':'EPSG:27700','counts':counts,'benchmark':{'areaM2':region.area,'wfdAreaM2':round(wfd.area,3),'floodZoneUnionAreaM2':round(fz.area,3),'habitatsAreaM2':grouped_areas(fs['phi'],region,'mainhabs'),'floodZonesAreaM2':grouped_areas(fs['flood'],region,'flood_zone'),'floodOriginsAreaM2':grouped_areas(fs['flood'],region,'origin'),'raster':raster_stats(region)},'habitatWaterComparisons':hab,'probes':probes,'nativeEventRecords':rfos,'crosswalk':CROSSWALK,'method':'Exact native polygon intersection/unions in BNG; transformed native raster centre counts, no raster resampling, confidence estimation, classification or hydrological modelling. Overlap is support, not truth or simultaneous state. No-observations excluded from paired detected/non-detected comparisons.'}
 save(out,result);print('Diagnostic SHA256',sha(out));print('Native support', counts, 'frozen probes',len(probes))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();analyse(a.data,a.out)
