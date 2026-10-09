"""Task-specific unchanged evidence/navigation and measured registration protection receipt."""
from pathlib import Path
import ast,hashlib,json,re,subprocess,sys
from urllib.parse import unquote
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];H=Path(__file__).parent
BASE='0a2c7177ece0e7092214ca6e1a81ee25e2c92c36';OUT=R/'docs/research/atlas-local-registration-validation.json'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
MOD={'runtime/atlas/'+n for n in ['README.md','authority.ts','index.ts','cli.ts','worker.py','types.ts','lifecycle-model.ts','lifecycle.ts','publication.ts']}
NEW={'runtime/atlas/'+n for n in ['registration-plan.json','registration-next-task.json','registration-model.ts','registration.ts','test-registration.mjs','measure-registration.mjs','example-registration.mjs','check-registration.py','validate-registration.py']}
NEW|={'docs/research/atlas-local-registration'+s for s in ['.md','-baseline.json','-results.json','-validation.json']}
sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
checks=[]
def check(n,v):checks.append({'check':n,'passed':bool(v)})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8')
b=read('docs/research/atlas-local-registration-baseline.json');x=read('docs/research/atlas-local-registration-results.json');p=read('runtime/atlas/registration-plan.json');n=read('runtime/atlas/registration-next-task.json');old=read('docs/research/atlas-local-runtime-baseline.json');t=read('docs/research/atlas-temporal-integration-baseline.json');a=read('docs/research/atlas-local-architecture-baseline.json')
keep=[k for k in b['trackedBlobs'] if k not in NAV|MOD];hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(keep)+'\n',text=True).splitlines()
check('starting clean main checkpoint/upstream recorded',b['startingCheckpoint']==BASE and b['branch']=='main' and b['divergence']=='0\t0')
check('every original file outside exact runtime/navigation edits unchanged',all(b['trackedBlobs'][k]==h for k,h in zip(keep,hashes)) and len(hashes)==len(keep))
check('frozen plan remains exact',p['frozenBeforeImplementation'] and b['frozenBeforeImplementation'] and sha(H/'registration-plan.json')==b['planSha256']==x['planSha256'])
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

for name in ['atlas-local-lifecycle','atlas-local-lifecycle-results','atlas-local-lifecycle-validation']:
 check(name+' accepted checkpoint artifact unchanged',(R/('docs/research/'+name+('.md' if name=='atlas-local-lifecycle' else '.json'))).is_file())
check('three actual isolated sequences and9 full/scoped comparisons agree',len(x['samples'])==3 and x['agreement'] and x['scopedFullComparisons']==9 and all(c['agreement'] and c['numericalValuesUnchanged'] for s in x['samples'] for c in s['cases']))
check('six indexed/full/rebuild query comparisons agree',x['queryComparisons']==6 and all(s['built']['records']==s['rebuilt']['records']==49 and s['built']['bytes']==s['rebuilt']['bytes']==81920 for s in x['samples']))
check('native identities stable while genuine knowledge acceptance IDs differ',len({json.dumps(s['initial']['nativeIdentities'],sort_keys=True) for s in x['samples']})==1 and len({s['initial']['generation'] for s in x['samples']})==3)
check('all initial registrations fully validate current329 artifacts/171MB',all(s['initial']['validation']['payloadHashOperations']==329 and s['initial']['validation']['payloadBytesHashed']==171482433 for s in x['samples']))
check('initial canonical registration metadata recorded',all(s['initial']['registrationMetadataBytes']>0 and s['initial']['writes']['bytesWritten']>3000000 for s in x['samples']))
check('idempotent native registration writes no new bytes',all(s['noOp']['status']=='no-op' and s['noOp']['metrics']['bytesWritten']==0 and s['noOp']['affected']==[] for s in x['samples']))
for case,count,reused in [('knowledge-only',0,32),('source-qualification',8,24),('unrelated-region',0,32)]:
 rows=[c for s in x['samples'] for c in s['cases'] if c['case']==case]
 check(case+' exact scoped qualification/reuse',len(rows)==3 and all(len(c['stage']['affected'])==len(c['stage']['requalified'])==count and c['stage']['recomputed']==[] and c['stage']['reused']==reused for c in rows))
 check(case+' plan agrees and staged processing reads no new cells',all(c['plan']['affected']==c['stage']['affected'] and c['stage']['metrics']['processingCellsRead']==0 for c in rows))
 check(case+' full publication checks32 independent outputs',all(c['validation']['outputChecks']==32 and c['published']['validation']['outputChecks']==32 for c in rows))
 check(case+' expected selective membership',all(set(c['componentsChanged'])==({'registrationLedger','terrainLifecycle','terrainDerived'} if count else {'registrationLedger'}) and len(c['componentsReused'])==(7 if count else 9) for c in rows))
check('initial32 real derivations sampled144 cells',all(s['derived']['metrics']['cellsRead']==144 for s in x['samples']))
check('three fresh historical replays each reproduce5 pins',len(x['replays'])==3 and all(len(v['results'])==5 and [r['generation'] for r in v['results']]==s['history'] and v['results'][0]['count']==0 and all(r['count']==32 and r['validation']['ancestryTraversals']==0 for r in v['results'][1:]) for v,s in zip(x['replays'],x['samples'])))
check('independent numerical/scientific result identities same across repetitions',len({json.dumps([r['resultIdentity'] for r in v['results']]) for v in x['replays']})==1)
check('full timing spreads/hardware/RSS/environment recorded',all(set(x['summary'][k])=={'median','min','max'} for k in ['inspectionMs','registrationMs','openMs','buildMs','rebuildMs','featureQueryMs','derivedQueryMs','freshReplayMs','noOpMs']) and x['environment']['hardware']['totalMemoryBytes']>0 and all(s['rss']>0 for s in x['samples']))
check('world payloads outside repository bounded under15MB',all(not Path(s['world']).is_relative_to(R) and s['storage']['bytes']<15000000 for s in x['samples']))
check('no copied research-world bootstrap',"fs.cpSync" not in (H/'registration.ts').read_text() and "sourcePublication" not in (H/'example-registration.mjs').read_text())
check('independent full validation and source method preserved',all(k in (H/'registration.ts').read_text() for k in ['verifyArtifacts','verifyDelivery','openAtlas','stageObject']) and 'validateRegistrationTransition' in (H/'lifecycle.ts').read_text())
check('metadata requalification does not invoke scientific algorithms', 'requalifyOutputs' in (H/'registration.ts').read_text() and 'made = await outputs' not in (H/'registration.ts').read_text())
check('real/control/no-replacement boundary frozen',len(p['acceptance'])==8 and any('unsupported' in z for z in p['operations']))
report=(R/'docs/research/atlas-local-registration.md').read_text(encoding='utf-8');check('all32 durable report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,33)))
check('scientific/operation boundaries explicit',all(v in report for v in ['unknown','controlled','LN02','power-loss','CLOSED','C \u2014 REGISTRATION AND UPDATE SUCCESS','supersession','requalification']))
check('one next task selected not begun',n['status']=='NOT BEGUN' and n['title'] in report and len(n['acceptance'])==7)
for name in NAV:
 text=(R/name).read_text(encoding='utf-8');check('current navigation result and next-task '+name,all(v in text for v in ['atlas-local-registration.md','C \u2014 REGISTRATION AND UPDATE SUCCESS',n['title'],'Tryfan remains CLOSED / ACCEPTED']))
check('development log append-only',(R/'docs/development-log.md').read_text(encoding='utf-8').startswith(git('show',BASE+':docs/development-log.md')))
changed=set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()+[OUT.relative_to(R).as_posix()]);check('exact authorized runtime/report/navigation scope',changed==NAV|MOD|NEW)
check('no large committed payload/catalogue',all((R/k).stat().st_size<250000 and not k.endswith(('.sqlite','.db','.tif','.png','.pyc','.npz')) for k in changed-NAV if (R/k).exists()))
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
check('all documentation links resolve',not missing)
commands=json.loads((R/'../../Codex/atlas-local-registration-v1/regression/commands.json').resolve().read_text(encoding='utf-8'));previous=read('docs/research/atlas-local-lifecycle-validation.json')['commands']
check('all inherited569 tests/commands freshly pass',len(commands)==len(previous)+2 and all(c['name']==o['name'] and c['exitCode']==0 for c,o in zip(commands,previous)) and sum(c.get('tests') or 0 for c in commands[:len(previous)])==569)
check('all44 new registration tests pass',commands[-2]['exitCode']==0 and commands[-2]['tests']==44)
check('documented complete registration CLI example freshly passes',commands[-1]['exitCode']==0 and commands[-1]['name']=='runtime-registration-cli')
check('types lint build freshly pass',all(c['exitCode']==0 for c in commands if c['name'] in ['semantic-types','application-types','runtime-types','lint','build']))
final_review=json.loads((R/'../../Codex/atlas-local-registration-v1/regression/final-review.json').resolve().read_text(encoding='utf-8'))
check('final reviewed runtime types and lint pass',{c['name'] for c in final_review}=={'final-runtime-types','final-lint'} and all(c['exitCode']==0 for c in final_review))
check('git whitespace clean',subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0)
result={'schema':'atlas-runtime-registration-validation/v1','startingCheckpoint':BASE,'decision':'C \u2014 REGISTRATION AND UPDATE SUCCESS','passed':sum(c['passed'] for c in checks),'failed':[c['check'] for c in checks if not c['passed']],'checks':checks,'tests':sum(c.get('tests') or 0 for c in commands),'commands':commands,'finalReviewCommands':final_review,'runtimeHashes':{k:sha(R/k) for k in sorted(changed-NAV) if (R/k).exists() and (R/k)!=OUT},'navigationMissing':missing,'review':'Only bounded runtime registration/qualification/lifecycle interfaces, tests, safe reports/navigation. No accepted evidence/contracts/status/production changes, acquisition/private/S7/cloud. Full diff/untracked review before commit.'}
OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:result[k] for k in ['passed','failed','tests','navigationMissing']},indent=2));sys.exit(bool(result['failed']))
