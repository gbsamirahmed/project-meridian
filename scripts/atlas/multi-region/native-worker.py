"""Read-only prepared-region bridge. No registration or publication writes."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'riffelhorn-retrieval'))
import query as Q

def describe(s):
 return {'schema':'atlas-regional-evidence-registration/v1','region':'riffelhorn','preparationRevision':s.manifest['revision'],'preparationMethod':s.manifest['method'],'support':s.qual['core'],'coordinateQualification':s.qual['coordinateOperation'],'qualification':s.qual['families'],'rightsBoundary':s.qual['rightsBoundary'],'inputs':s.input_manifest['inputs'],'preparedArtifacts':[{'path':'manifest.json','bytes':(s.root/'manifest.json').stat().st_size,'sha256':Q.P.sha(s.root/'manifest.json')}]+s.manifest['artifacts'],'records':[{'identity':r['id'],'family':r['family'],'representation':r['representation'],'product':r['product'],'nativeCrs':r['record']['nativeCrs'] if r['representation']=='vector' else r['record']['native']['crs'],'temporal':s.temporal(r),'preparedAsset':'features.json' if r['representation']=='vector' else 'raster-bindings.json','selector':r['id']} for r in s.records],'semanticDeclarations':sum(len(c['claims']) for c in s.bundle['collections']),'administrative':{'revision':0,'notice':'Initial retained regional registration; no new physical observation'}}

def main():
 root=Path(sys.argv[sys.argv.index('--root')+1]) if '--root' in sys.argv else None
 s=Q.Session(root=root)
 if '--oracle' in sys.argv:print(json.dumps({c['id']:s.query(c['query'],'scan')['answer'] for c in Q.P.load(Q.H/'matrix.json')['cases']},ensure_ascii=False));return
 if '--describe' in sys.argv:print(json.dumps(describe(s),ensure_ascii=False));return
 if '--verify' in sys.argv:print(json.dumps({'verified':True,'setup':s.setup,'inputBytesVerified':sum(a['bytes'] for a in s.input_manifest['inputs'])}));return
 print(json.dumps({'ready':True,'revision':s.manifest['revision'],'setup':s.setup}),flush=True)
 for line in sys.stdin:
  try:
   request=json.loads(line);out=s.query(request['query'],request.get('mode','selective'));print(json.dumps({'value':out},ensure_ascii=False,allow_nan=False),flush=True)
  except Exception as e:print(json.dumps({'error':{'type':type(e).__name__,'message':str(e)}}),flush=True)
if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8')
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);raise SystemExit(1)
