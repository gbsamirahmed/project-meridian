"""Task-specific protection/navigation and measured workflow receipt."""
from pathlib import Path
import ast,hashlib,json,re,subprocess,sys
from urllib.parse import unquote
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];H=Path(__file__).parent
BASE='5842fde7d86c5623906721cd21e67aeb80552c6f'
OUT=R/'docs/research/atlas-local-lifecycle-validation.json'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
MOD={'runtime/atlas/'+n for n in ['authority.ts','index.ts','cli.ts','worker.py','worker.ts','types.ts','README.md']}
NEW={'runtime/atlas/'+n for n in ['lifecycle-plan.json','lifecycle-next-task.json','lifecycle-model.ts','lifecycle.ts','publication.ts','terrain-worker.py','test-lifecycle.mjs','measure-lifecycle.mjs','example-lifecycle.mjs','check-lifecycle.py','validate-lifecycle.py']}
NEW|={'docs/research/atlas-local-lifecycle'+s for s in ['.md','-baseline.json','-results.json','-validation.json']}
sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
checks=[]
def check(n,v):checks.append({'check':n,'passed':bool(v)})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8')
b=read('docs/research/atlas-local-lifecycle-baseline.json');x=read('docs/research/atlas-local-lifecycle-results.json');p=read('runtime/atlas/lifecycle-plan.json');n=read('runtime/atlas/lifecycle-next-task.json');old=read('docs/research/atlas-local-runtime-baseline.json');t=read('docs/research/atlas-temporal-integration-baseline.json');a=read('docs/research/atlas-local-architecture-baseline.json')
keep=[k for k in b['trackedBlobs'] if k not in NAV|MOD]
hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(keep)+'\n',text=True).splitlines()
check('starting clean main checkpoint/upstream recorded',b['startingCheckpoint']==BASE and b['branch']=='main' and b['divergence']=='0\t0')
check('all original files outside narrow runtime/navigation edits unchanged',all(b['trackedBlobs'][k]==h for k,h in zip(keep,hashes)) and len(hashes)==len(keep))
check('frozen plan predates implementation and remains exact',p['frozenBeforeImplementation'] and b['frozenBeforeImplementation'] and sha(H/'lifecycle-plan.json')==b['planSha256']==x['planSha256'])
prod=read('docs/atlas/information-display-plan.json')['productionHashes'];check('all113 protected production hashes unchanged',len(prod)==113 and all(sha(R/k)==v for k,v in prod.items()))
check('all42 canonical research statuses unchanged',len(t['canonicalRows'])==42 and P.admission.canonical_rows((R/'docs/research/atlas-research-state.md').read_text(encoding='utf-8'))==t['canonicalRows'])
check('retained original source admission unchanged',P.admission.assess()['sources']==t['sourceAdmission'])
s=P.DATA/'experiments/atlas/tryfan-regional-pilot-v1';d=read('docs/research/atlas-integrity-cost-baseline.json')
check('all17 accepted Tryfan files unchanged',all(sha(s/k)==v for k,v in d['acceptedStoreHashes'].items()))
s=P.DATA/t['preparedRootRelative'];check('all6 accepted prepared Riffelhorn artifacts unchanged',len(t['preparedHashes'])==6 and all(sha(s/k)==v for k,v in t['preparedHashes'].items()))
check('native unit/source receipts unchanged',all(sha(P.DATA/k)==v for k,v in t['unitEvidence'].items()))
check('all66 retained Exe temporal files unchanged',len(t['retainedExeDirectory'])==66 and all(sha(P.DATA/'derived/atlas/water-check-v1'/k)==v for k,v in t['retainedExeDirectory'].items()))
s=Path(a['previousTemporalStore']);check('complete accepted temporal state unchanged',set(a['previousStoreHashes'])=={f.relative_to(s).as_posix() for f in s.rglob('*') if f.is_file()} and all(sha(s/k)==v for k,v in a['previousStoreHashes'].items()))
s=Path(old['publicationRoot']);check('all115 accepted multi-region publication files unchanged',len(old['storeHashes'])==115 and set(old['storeHashes'])=={f.relative_to(s).as_posix() for f in s.rglob('*') if f.is_file()} and all(sha(s/k)==v for k,v in old['storeHashes'].items()))
for name in ['atlas-multi-region','atlas-regional-dependencies']:
 q=read('docs/research/'+name+'-results.json');s=Path(q['store']);check(name+' root/history retained',json.loads((s/'current.json').read_bytes())['generation']==q['history'][-1] and all(sha(f)==f.stem for folder in ['components','publications','membership','artifacts'] for f in (s/folder).iterdir() if f.is_file()))
for i in range(1,7):check('accepted S'+str(i)+' report unchanged and present',(R/f'docs/research/tryfan-pilot-s{i}.md').is_file())
for name in ['atlas-component-membership','atlas-component-granularity','atlas-validation-packing','atlas-integrity-cost','atlas-regional-expansion','atlas-riffelhorn-preparation','atlas-riffelhorn-retrieval','atlas-multi-region','atlas-regional-dependencies','atlas-temporal-integration','atlas-local-architecture','atlas-local-runtime']:
 check(name+' primary evidence unchanged and present',(R/f'docs/research/{name}.md').is_file())
check('population is16 actual accepted probes/32 outputs',x['population']=={'probes':16,'outputs':32,'registeredDtmSources':4,'consumedDtmSources':1,'baseRecords':49,'members':9} and p['population']['probes']==[z for z in read('scripts/atlas/regional-dependencies/plan.json')['sampling']['probes'] if 'cluster' in z['id']])
check('three isolated deterministic initial publications identical',len(x['samples'])==3 and len({s['initial']['generation'] for s in x['samples']})==1)
check('all21 selective/full comparisons agree',x['agreement'] and x['selectiveFullComparisons']==21 and all(o['agreement'] and o['scoped']['activeIdentity']==o['full']['activeIdentity'] for s in x['samples'] for o in s['observations']))
check('96 actual accepted numerical comparisons recorded',x['acceptedNumericalComparisons']==96 and 'accepted numerical oracle disagreement' in (H/'measure-lifecycle.mjs').read_text())
expected={'no-op':(0,32,0),'local-qualification':(8,24,36),'parameter':(2,30,9),'unrelated-region':(0,32,0),'global-qualification':(32,0,144),'identical-notice':(0,32,0)}
for name,(count,reused,cells) in expected.items():
 rows=[o for s in x['samples'] for o in s['observations'] if o['case']==name]
 check(name+' exact closure/reuse/processing cells',len(rows)==3 and all(len(o['scoped']['affected'])==count and len(o['scoped']['recomputed'])==count and o['scoped']['reused']==reused and o['scoped']['metrics']['cellsRead']==cells for o in rows))
check('every full comparison samples all144 native cells',all(o['full']['metrics']['cellsRead']==144 for s in x['samples'] for o in s['observations']))
check('initial complete current payload validation retained',all(s['initial']['validation']['payloadBytesHashed']==171482433 and s['initial']['validation']['payloadHashOperations']==329 for s in x['samples']))
check('full native publication validation is not receipt-based',all(s['initialPublication']['validation']['outputChecks']==32 and s['initialPublication']['validation']['payloadBytesHashed']>=217013031 for s in x['samples']))
check('native and derived query measurements present',all(s['queryMs']>0 and s['derivedMs']>0 and s['openMs']>0 for s in x['samples']))
check('all catalogue builds/rebuilds disposable80KB/49 records',all(s['built']['bytes']==s['rebuilt']['bytes']==81920 and s['built']['records']==s['rebuilt']['records']==49 for s in x['samples']))
check('metadata reads and write counters explicit',all('artifactMetadataReads' in o['scoped']['metrics'] and 'writes' in o['scoped']['metrics'] for s in x['samples'] for o in s['observations']))
check('no-op writes no canonical object',all(o['scoped']['metrics']['writes']['bytesWritten']==0 for s in x['samples'] for o in s['observations'] if o['case'] in ['no-op','identical-notice']))
check('source-use-slope-ratio graph explicit and finite',all(s['graph']['registeredSourceNodes']==4 and s['graph']['qualifiedUseNodes']==16 and s['graph']['derivedNodes']==32 and len(s['graph']['edges'])==48 and s['graph']['maximumDepth']==3 and s['graph']['crossRegionEdges']==0 for s in x['samples']))
check('local/parameter notices replace two components and reuse seven',all(len(o['membersChanged'])==2 and len(o['membersReused'])==7 for s in x['samples'] for o in s['observations'] if o['case'] in ['local-qualification','parameter','global-qualification']))
check('unrelated region only replaces its registration',all(o['membersChanged']==['tryfanRegistration'] and len(o['membersReused'])==8 for s in x['samples'] for o in s['observations'] if o['case']=='unrelated-region'))
check('three fresh historical processes each reproduce six pinned generations',len(x['replays'])==3 and all(len(v['results'])==6 and [r['generation'] for r in v['results']]==s['history'] and v['results'][0]['count']==0 and all(r['count']==32 and r['validation']['ancestryTraversals']==0 for r in v['results'][1:]) for v,s in zip(x['replays'],x['samples'])))
check('historical exact result identities repeat',len({json.dumps([(r['generation'],r['identity']) for r in v['results']]) for v in x['replays']})==1)
check('all generated worlds external and bounded under10MB each',all(not Path(s['world']).is_relative_to(R) and s['finalStorage']['bytes']<10000000 for s in x['samples']))
check('method and independent oracle frozen content unchanged',sha(R/p['method']['file'])==p['method']['sha256'] and sha(R/'scripts/atlas/regional-dependencies/sample.py')=='9a2c914c272b8f010ee92293bd82fd056af922da9c74966d2eb2d6f4462f6bbb')
report=(R/'docs/research/atlas-local-lifecycle.md').read_text(encoding='utf-8');check('all32 required durable report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,33)))
check('scientific and operation boundaries explicit',all(v in report for v in ['unknown','administrative','LN02','power-loss','population-wide','CLOSED','C \u2014 LIFECYCLE INTEGRATION SUCCESS']))
check('one specific next task selected but not begun',n['status']=='NOT BEGUN' and n['title'] in report and len(n['acceptance'])==7)
for name in NAV:
 text=(R/name).read_text(encoding='utf-8');check('current result/next-task preserved in '+name,all(v in text for v in ['atlas-local-lifecycle.md','C \u2014 LIFECYCLE INTEGRATION SUCCESS',n['title'],'Tryfan remains CLOSED / ACCEPTED']))
check('development log append-only',(R/'docs/development-log.md').read_text(encoding='utf-8').startswith(git('show',BASE+':docs/development-log.md')))
changed=set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()+[OUT.relative_to(R).as_posix()]);check('only exact authorized runtime/report/navigation boundary',changed==NAV|MOD|NEW)
check('no unnecessary large committed payloads',all((R/k).stat().st_size<250000 and not k.endswith(('.sqlite','.db','.tif','.png','.pyc','.npz')) for k in changed-NAV if (R/k).exists()))
missing=[]
for name in changed:
 f=R/name
 if not f.exists():continue
 if name.endswith('.json'):read(name)
 if name.endswith('.py'):ast.parse(f.read_text(encoding='utf-8'))
 if name.endswith('.md'):
  text=f.read_text(encoding='utf-8');text=text[len(git('show',BASE+':'+name)):] if name=='docs/development-log.md' else text
  for link in re.findall(r'\]\(([^)]+)\)',text):
   if link.startswith(('http:','https:','mailto:')):continue
   pth=unquote(link.strip('<>')).split('#')[0];target=f.parent/pth if pth else f
   if not target.exists() and target.resolve()!=OUT.resolve():missing.append([name,link])
check('all changed documentation links resolve',not missing)
commands=json.loads((R/'../../Codex/atlas-local-lifecycle-v1/regression/commands.json').resolve().read_text(encoding='utf-8'));prior=read('docs/research/atlas-local-runtime-validation.json')['commands']
check('all inherited508-test commands freshly passed',len(commands)==len(prior)+2 and all(c['args']==o['args'] and c['exitCode']==0 for c,o in zip(commands,prior)) and sum(c.get('tests') or 0 for c in commands[:len(prior)])==508)
check('61 lifecycle tests freshly passed',commands[-2]['exitCode']==0 and commands[-2]['tests']==61)
check('documented full CLI example freshly passed',commands[-1]['exitCode']==0 and commands[-1]['name']=='runtime-cli-example')
check('types lint and build passed',all(c['exitCode']==0 for c in commands if c['name'] in ['semantic-types','application-types','runtime-types','lint','build']))
check('git diff whitespace clean',subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0)
result={'schema':'atlas-local-lifecycle-validation/v1','startingCheckpoint':BASE,'decision':'C \u2014 LIFECYCLE INTEGRATION SUCCESS','checks':checks,'passed':sum(c['passed'] for c in checks),'failed':[c['check'] for c in checks if not c['passed']],'tests':sum(c.get('tests') or 0 for c in commands),'commands':commands,'runtimeHashes':{k:sha(R/k) for k in sorted(changed-NAV) if (R/k).exists() and (R/k)!=OUT},'navigationMissing':missing,'review':'Bounded runtime processing/writer/library/CLI, tests, safe reports/navigation only. No accepted files/contracts/status/production edits, acquisition/private/S7/cloud; full diff and untracked review before commit.'}
OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:result[k] for k in ['passed','failed','tests','navigationMissing']},indent=2));sys.exit(bool(result['failed']))
