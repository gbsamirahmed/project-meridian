"""Assessment guards and established relevant regression commands; no fixture preparation."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys
from urllib.parse import unquote
R=Path(__file__).resolve().parents[3];H=Path(__file__).parent
sys.stdout.reconfigure(encoding='utf-8');sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
BASE='aa920d97a6436dd94d86b1de724d9231c745effd';OUT='docs/research/atlas-regional-expansion-validation.json'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
LOG=Path('C:/Users/gbsam/Documents/Codex/atlas-regional-expansion-assessment/regression');LOG.mkdir(parents=True,exist_ok=True)
checks=[];errors=[];commands=[]
def check(n,ok):
 checks.append(dict(check=n,passed=bool(ok)))
 if not ok:errors.append(n)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8')
tracked=git('ls-tree','-r','--name-only',BASE).splitlines();keep=[p for p in tracked if p not in NAV];tree={s.split('\t')[1]:s.split()[2] for s in git('ls-tree','-r',BASE).splitlines()}
def intact():
 hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(keep)+'\n',text=True).splitlines();return len(hashes)==len(keep) and all(h==tree[p] for p,h in zip(keep,hashes))
check('all original non-navigation files unchanged before regression',intact())
old=git('show',BASE+':docs/research/atlas-research-state.md');check('all42 research statuses unchanged',len(P.admission.canonical_rows(old))==42 and P.admission.canonical_rows(old)==P.admission.canonical_rows((R/'docs/research/atlas-research-state.md').read_text(encoding='utf-8')))
protected=read('docs/atlas/information-display-plan.json')['productionHashes'];check('all113 protected production hashes',len(protected)==113 and all(sha(R/p)==h for p,h in protected.items()))
accepted=read('docs/research/atlas-integrity-cost-baseline.json');store=P.DATA/'experiments/atlas/tryfan-regional-pilot-v1';check('all17 accepted store files unchanged',len(accepted['acceptedStoreHashes'])==17 and all(sha(store/p)==h for p,h in accepted['acceptedStoreHashes'].items()))
before=P.admission.assess()['sources'];check('all1575 admitted retained files',before['uniqueFiles']==1575)
plan=read('scripts/atlas/regional-expansion/plan.json');b=read('docs/research/atlas-regional-expansion-baseline.json');x=read('docs/research/atlas-regional-expansion-inventory.json');s=read('docs/research/atlas-regional-expansion-fixture.json')
check('frozen criteria identities match',sha(H/'plan.json')==b['planSha256']==x['planSha256']);check('exact starting checkpoint',b['startingCheckpoint']==plan['startingCheckpoint']==x['startingCheckpoint']==BASE)
check('foundations present and byte-identical',all(sha(R/p)==h for p,h in b['foundationsSha256'].items()))
check('all ten mandatory criteria recovered',len(plan['mandatoryCriteria'])==10 and set(s['mandatoryCriteriaResults'])=={v['id'] for v in plan['mandatoryCriteria']})
check('no acceptance fixture implemented',s['status']=='SPECIFICATION ONLY - NOT CONSTRUCTED' and s['nextTask']['status']=='NOT BEGUN')
check('explicit supports4 and9',[(r['crs'],r['areaKm2']) for r in s['supports']]==[('EPSG:2056',4),('EPSG:27700',9)])
check('exact twelve distinct selected inputs',len(s['inputs'])==s['distinctInputFiles']==len({a['path'] for a in s['inputs']})==12)
check('exact120347916 bytes available and matched',s['nativeInputBytes']==sum(a['bytes'] for a in s['inputs'])==120347916 and all((P.DATA/a['path']).stat().st_size==a['bytes'] and sha(P.DATA/a['path'])==a['sha256'] for a in s['inputs']))
check('input paths limited to public named geography',all(a['path'].startswith(('sources/atlas/riffelhorn/','derived/atlas/semantic-comparison-v1/')) for a in s['inputs']))
core=[a for a in x['sourceAvailability'] if a['selectedCoreInput']];check('four current native DTM headers',len(core)==4 and all(a['currentFullHash'] and a['header']['crs']=='EPSG:2056' and a['header']['shape']==[2000,2000] and a['header']['resolution']==[.5,.5] for a in core))
check('Swiss source bounds match exact core area',sum((a['support'][2]-a['support'][0])*(a['support'][3]-a['support'][1]) for a in core)==4000000)
sem={Path(a['path']).name:a for a in x['semanticInputs']};check('native218x312WorldCover grid',sem['riffelhorn-worldcover.tif']['header']['shape']==[218,312] and sem['riffelhorn-worldcover.tif']['header']['crs']=='EPSG:4326');check('23and8validGeoCoverfeatures',[(sem[n]['records'],sem[n]['geometryValid']) for n in ['geocover-bedrock.json','geocover-unconsolidated.json']]==[(23,True),(8,True)])
check('oneand6GLAMOSsource selection independently reproduced',[(a['records'],a['offlineSelectionIdentical'],a['nativeCrs']) for a in x['glamosOriginalVerification']]==[(1,True,'EPSG:2056'),(6,True,'EPSG:2056')]);check('GLAMOSfeature dates not release year',sem['SGI_2016_glaciers-subset.json']['featureYears']==[2015] and sem['SGI_2016_debriscover-subset.json']['featureYears']==[2016])
check('five existing preparation identities verified',len(x['knownPreparationInventory'])==5 and sum(p['payloadFilesStatChecked'] for p in x['knownPreparationInventory'])==16632);check('106 retained original support entries available',len(x['sourceAvailability'])==106 and all(r['availability']=='VERIFIED' for r in x['sourceAvailability']))
check('all16 original Swiss catalogue assets retained',len(x['additionalOriginalSources'])==16 and all(a['availability']=='VERIFIED' for a in x['additionalOriginalSources']))
check('all four accountability labels',set(x['statusVocabulary'])=={'VERIFIED','DOCUMENTED BUT NOT INDEPENDENTLY VERIFIED','UNKNOWN','NOT APPLICABLE'})
check('exact one next bounded task',s['nextTask']['title']=='Atlas retained Riffelhorn qualified regional fixture preparation proof' and len(s['nextTask']['acceptanceCriteria'])==12 and s['nextTask']['acceptanceCriteria']==s['acceptanceConditions'])
report=(R/'docs/research/atlas-regional-expansion.md').read_text(encoding='utf-8');check('all28 report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,29)));check('all four decision classifications',all('## '+str(i)+'. '+t in report for i,t in [(21,'DECIDE NOW'),(22,'PROVISIONAL DIRECTION'),(23,'DEFER PENDING EVIDENCE'),(24,'REJECT')]))
check('source-selection does not reopen validation',all(t in report for t in ['receipt optimisation remains CLOSED','Full validation remains','No new datasets','No blocker to this qualified']))
for p in NAV:check('result and exactlyone next in '+p,'C - ASSESSMENT RESOLVED' in (R/p).read_text(encoding='utf-8') and s['nextTask']['title'] in (R/p).read_text(encoding='utf-8'))
check('append-only development history',(R/'docs/development-log.md').read_text(encoding='utf-8').startswith(git('show',BASE+':docs/development-log.md')+'\n'))
def run(n,args):
 q=subprocess.run(args,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONIOENCODING':'utf-8'});(LOG/(n+'.log')).write_text(q.stdout+q.stderr,encoding='utf-8',newline='\n');check(n,q.returncode==0);m=re.search(r'^(?:#|\u2139) tests (\d+)',q.stdout,re.M) or re.search(r'Ran (\d+) tests?',q.stderr);commands.append(dict(name=n,args=args,exitCode=q.returncode,tests=int(m[1]) if m else None));print(n,q.returncode,flush=True)
 if q.returncode:print((q.stdout+q.stderr)[-2200:],flush=True)
run('assessment-inventory-reproduction',[sys.executable,str(H/'inventory.py'),'--check'])
# Established relevant coverage. No closed receipt/packing benchmark is re-executed.
selected={'assessment','s6','s1-s5','native','planning','frozen','qualified','persistent','exe','semantic-types','lint','build','diff'}
for c in read('docs/research/atlas-integrity-cost-validation.json')['commands']:
 if c['name'] in selected:run(c['name'],c['args'])
run('application-types',['node','node_modules/typescript/bin/tsc','-b','--pretty','false'])
changed=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
allowed={OUT,*['docs/research/atlas-regional-expansion'+t for t in ['.md','-inventory.json','-baseline.json','-fixture.json']]}|{'scripts/atlas/regional-expansion/'+t for t in ['plan.json','inventory.py','validate.py','README.md']}
check('assessment-only change allowlist',all(p in allowed|NAV for p in changed));check('small outputs no payloads',all((R/p).stat().st_size<150000 and not p.endswith(('.png','.tif','.las','.zip','.npz','.db','.pyc')) for p in changed if p not in NAV))
missing=[]
for p in changed:
 if not p.endswith('.md'):continue
 text=(R/p).read_text(encoding='utf-8')
 if p=='docs/development-log.md':text=text[len(git('show',BASE+':docs/development-log.md')):]
 for link in re.findall(r'\]\(([^)]+)\)',text):
  if link.startswith(('http:','https:','mailto:')):continue
  target=unquote(link.strip('<>')).split('#')[0];f=(R/p).parent/target if target else R/p
  if not f.exists() and f.resolve()!=(R/OUT).resolve():missing.append([p,link])
check('local report references resolve',not missing);check('original non-navigation bytes unchanged after validation',intact());check('all admitted source inventory unchanged',P.admission.assess()['sources']==before);check('accepted store unchanged after validation',all(sha(store/p)==h for p,h in accepted['acceptedStoreHashes'].items()));check('all113 production hashes unchanged after validation',all(sha(R/p)==h for p,h in protected.items()));check('all12 selected native hashes unchanged after validation',all(sha(P.DATA/a['path'])==a['sha256'] for a in s['inputs']))
state=json.loads(subprocess.check_output(['node','pilots/atlas/tryfan/cli.mjs','inspect'],cwd=R,text=True,encoding='utf-8'));check('accepted current and310evidence hashes unchanged',state['generation']==accepted['current'] and state['verification']==accepted['sources'])
receipt=dict(schema='atlas-regional-expansion-validation/v1',startingCheckpoint=BASE,checks=checks,errors=errors,commands=commands,testCount=sum(c['tests'] or 0 for c in commands),preservedTrackedFiles=len(keep),changedPaths=changed,canonicalThreads=42,protectedHashes=113,acceptedPilotUnchanged=not errors,sourceAdmission=before,retainedVerification=state['verification'],publishedGeneration=state['generation'],missingReferences=missing,decision=s['decision'],nextTask=s['nextTask']['title'],nextTaskStatus='NOT BEGUN',assessmentHashes={p:sha(R/p) for p in changed if p not in NAV and p!=OUT})
(R/OUT).write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(dict(checks=len(checks),tests=receipt['testCount'],errors=errors)),flush=True)
if errors:raise SystemExit(1)
