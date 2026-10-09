"""Independent direct GeoJSON admission and exact-query oracle; no runtime imports."""
from pathlib import Path
import json,sys,re,hashlib
from shapely.geometry import shape,box,Point
root=Path(sys.argv[1])/'derived/atlas/water-check-v1'
q=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
probes=[box(*b) for b in [[296600,86550,296800,86750],[296750,87000,296950,87200],[297050,87250,297250,87450],[297550,87500,297750,87700],[295700,87050,295900,87250],[296750,88250,296950,88450]]]
study=box(295000,86000,298500,89000);rows=[];inventory={}
for kind,family in [('phi','priority-habitat'),('flood','planning-flood-zone')]:
 p=root/(kind+'.geojson');doc=json.loads(p.read_text(encoding='utf-8'));selected=[]
 for f in doc['features']:
  g=shape(f['geometry']);fields={'featureId':f.get('id'),**f['properties']}
  if not any(g.intersection(b).area>0 for b in probes):continue
  selected.append(f)
  codes=[s.strip() for s in fields['habcodes'].split(',') if s.strip()] if kind=='phi' else [fields['flood_zone']]
  for code in codes:
   identity='exe:claim:'+kind+':'+str(fields['uid'] if kind=='phi' else fields['featureId'])+':'+(code if kind=='phi' else '0')
   feature=kind+':'+str(fields['uid'] if kind=='phi' else fields['featureId'])
   row={'identity':identity,'feature':feature,'family':family,'code':code,'fields':fields,'geometry':f['geometry'],'sourceSha256':hashlib.sha256(p.read_bytes()).hexdigest()}
   ok=all(q.get(k,v)==v for k,v in [('identity',identity),('feature',feature),('nativeClassification',code)]) and ('families' not in q or family in q['families'])
   if 'point' in q:ok=ok and study.contains(Point(*q['point'])) and g.covers(Point(*q['point']))
   if 'area' in q:ok=ok and g.intersection(box(*q['area']).intersection(study)).area>0
   if 'referenceTime' in q:
    t=q['referenceTime']
    if t['role'] in ['survey','contributor'] and kind!='phi':ok=False
    if t['role']=='effective' and kind!='flood':ok=False
    if not t.get('unknown'):ok=False # actual survey/effective/publication remain unknown; vintage checked separately
   if ok:rows.append(row)
 inventory[kind]={'returned':len(doc['features']),'selectedFeatures':len(selected),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
print(json.dumps({'inventory':inventory,'rows':sorted(rows,key=lambda r:r['identity'])},sort_keys=True))
