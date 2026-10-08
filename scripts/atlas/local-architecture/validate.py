"""Protection/navigation/regression receipt for the bounded decision only."""
from pathlib import Path
import ast,hashlib,json,os,re,subprocess,sys,time
from urllib.parse import unquote
R=Path(__file__).resolve().parents[3];H=Path(__file__).parent
BASE='d6a5514cdbee799d9a018b1660080568537428fa'
OUT=R/'docs/research/atlas-local-architecture-validation.json'
LOG=Path('C:/Users/gbsam/Documents/Codex/atlas-local-architecture-decision-v1/regression')
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
sys.stdout.reconfigure(encoding='utf-8');sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
checks=[]
def check(name,ok):checks.append({'check':name,'passed':bool(ok)})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True,encoding='utf-8')
def unchanged():
 tree={line.split('\t')[1]:line.split()[2] for line in git('ls-tree','-r',BASE).splitlines()};keep=[p for p in tree if p not in NAV]
 hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(keep)+'\n',text=True).splitlines()
 return len(hashes)==len(keep) and all(tree[p]==h for p,h in zip(keep,hashes))
check('all starting tracked non-navigation files unchanged',unchanged())
old=read('docs/research/atlas-temporal-integration-baseline.json');b=read('docs/research/atlas-local-architecture-baseline.json');plan=read('scripts/atlas/local-architecture/plan.json');x=read('docs/research/atlas-local-architecture-results.json');decision=read('docs/research/atlas-local-architecture-decisions.json');next_task=read('scripts/atlas/local-architecture/next-task.json')
check('exact clean starting checkpoint confirmed',b['startingCheckpoint']==BASE and b['branch']=='main' and b['divergence']=='0\t0')
check('criteria/workload frozen before comparison',b['frozenBeforeComparisonAndSelection'] and plan['frozenBeforeComparisonAndSelection'] and sha(H/'plan.json')==b['planSha256']==x['planSha256'])
original=Path(plan['externalOutputRoot'])/'original-frozen-plan.json'
check('original frozen plan preserved across LF-only normalization',sha(original)==b['originalPrefreezePlanBytesSha256'] and json.loads(original.read_text(encoding='utf-8-sig'))==plan)
check('four acceptance categories and practical choices frozen',len(plan['criteria']['mandatory'])==8 and len(plan['alternatives'])==3)
check('all representative workload responsibilities recorded',len(plan['workloads'])==13 and all(v['measuredBoundary'] and v['growth'] for v in plan['workloads']))
protected=read('docs/atlas/information-display-plan.json')['productionHashes']
check('all113 protected production hashes unchanged',len(protected)==113 and all(sha(R/p)==h for p,h in protected.items()))
check('all42 canonical research statuses unchanged',len(old['canonicalRows'])==42 and P.admission.canonical_rows((R/'docs/research/atlas-research-state.md').read_text(encoding='utf-8'))==old['canonicalRows'])
check('retained source admission unchanged',P.admission.assess()['sources']==old['sourceAdmission'])
accepted=read('docs/research/atlas-integrity-cost-baseline.json');store=P.DATA/'experiments/atlas/tryfan-regional-pilot-v1'
check('all17 accepted Tryfan store files unchanged',len(accepted['acceptedStoreHashes'])==17 and all(sha(store/p)==h for p,h in accepted['acceptedStoreHashes'].items()))
prepared=P.DATA/old['preparedRootRelative']
check('all6 accepted Riff prepared files unchanged',len(old['preparedHashes'])==6 and all(sha(prepared/p)==h for p,h in old['preparedHashes'].items()))
check('native unit/source receipts unchanged',all(sha(P.DATA/p)==h for p,h in old['unitEvidence'].items()))
check('all66 dated Exe retained files unchanged',len(old['retainedExeDirectory'])==66 and all(sha(P.DATA/'derived/atlas/water-check-v1'/p)==h for p,h in old['retainedExeDirectory'].items()))
temporal=Path(b['previousTemporalStore'])
check('complete accepted temporal external state unchanged',set(b['previousStoreHashes'])=={p.relative_to(temporal).as_posix() for p in temporal.rglob('*') if p.is_file()} and all(sha(temporal/p)==h for p,h in b['previousStoreHashes'].items()))
for name in ['atlas-multi-region','atlas-regional-dependencies']:
 a=read('docs/research/'+name+'-results.json');s=Path(a['store'])
 check(name+' accepted root unchanged',json.loads((s/'current.json').read_text())['generation']==a['history'][-1])
 check(name+' immutable historical objects verified',all(sha(p)==p.stem for d in ['components','publications','membership','artifacts'] for p in (s/d).iterdir() if p.is_file()) and all((s/'publications'/(g+'.json')).exists() for g in a['history']))
for n in range(1,7):check('accepted S'+str(n)+' report present',(R/f'docs/research/tryfan-pilot-s{n}.md').exists())
for n in ['atlas-measured-storage-processing-serving','atlas-component-membership','atlas-component-granularity','atlas-validation-packing','atlas-integrity-cost','atlas-regional-expansion','atlas-riffelhorn-preparation','atlas-riffelhorn-retrieval','atlas-multi-region','atlas-regional-dependencies','atlas-temporal-integration']:
 check(n+' authoritative report retained',(R/f'docs/research/{n}.md').exists())
check('actual metadata counts, not duplicated population',x['population']=={'records':250,'features':38,'temporalRevisions':20,'resultRevisions':192,'memberships':1006,'directInputEdges':200,'generations':5})
check('all192 candidate and qualification comparisons agree',x['agreement'] and x['comparisons']==192 and len(x['queries'])==12 and all(q['qualificationBodiesAgree'] for q in x['queries']))
check('five repetitions per candidate/case',all(len(m['samplesMs'])==5 for q in x['queries'] for m in q['methods'].values()))
check('build/open/fresh process costs included',len(x['sqliteBuildMs'])==5 and len(x['freshProcessHashOpenAndCount']['samplesMs'])==5 and len(x['coldReopenWithWholeIndexHash']['samplesMs'])==5)
check('all actual source metadata identities unchanged',all(sha(Path(p))==h for p,h in x['sourceHashes'].items()))
check('sealed external comparison index remains exact',Path(x['footprint']['sqlitePath']).is_relative_to(Path(plan['externalOutputRoot'])) and sha(Path(x['footprint']['sqlitePath']))==x['footprint']['sqliteSha256'])
check('actual missing/mismatched/corrupt view failures reject',all(x['failures'].values()) and x['rollbackAndReaderIsolation'])
check('logical counters zero ancestry/no scientific payload query',x['ancestryTraversals']==0 and all(q['structural']['ancestryTraversals']==q['structural']['nativePayloadReads']==0 for q in x['queries']))
check('index role and full-validation default concrete','canonical' in decision['authority'] and 'Rebuildable' in decision['queryCatalogue'] and 'Full' in decision['publication'] and 'CLOSED' in decision['integrity'])
check('one unbegun bounded implementation task',next_task['status']=='NOT BEGUN' and next_task['title']==decision['nextTask'] and len(next_task['acceptanceCriteria'])==9)
report=(R/'docs/research/atlas-local-architecture.md').read_text(encoding='utf-8')
check('all31 durable report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,32)))
check('correctness/custody/transaction and projection limits explicit',all(s in report for s in ['DECIDE NOW','PROVISIONAL DIRECTION','DEFER PENDING EVIDENCE','REJECT','root **last**','not a replacement physical-interval oracle','SQLite','single-writer','power-loss','No cross-filesystem/database transaction']))
for p in NAV:
 text=(R/p).read_text(encoding='utf-8')
 check('decision/current next task linked in '+p,all(s in text for s in ['C — DECISION READY',next_task['title'],'Tryfan remains CLOSED / ACCEPTED','atlas-local-architecture.md']))
check('development log append-only',(R/'docs/development-log.md').read_text(encoding='utf-8').startswith(git('show',BASE+':docs/development-log.md')))
allowed=NAV|{'scripts/atlas/local-architecture/'+p for p in ['plan.json','next-task.json','README.md','compare.py','test_compare.py','validate.py']}|{'docs/research/atlas-local-architecture'+s for s in ['.md','-baseline.json','-results.json','-decisions.json','-hardware.json','-data-inventory.json','-validation.json']}
changed=set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()+['docs/research/atlas-local-architecture-validation.json'])
check('exact authorized decision/measurement/navigation file boundary',changed==allowed)
check('no committed payload/database/cache or large fixture',all((R/p).stat().st_size<250000 and not p.endswith(('.sqlite','.db','.tif','.png','.pyc','.npz')) for p in changed if (R/p).exists() and p not in NAV and p!=OUT.relative_to(R).as_posix()))
missing=[]
for p in changed:
 if not (R/p).exists():continue
 if p.endswith('.json'):read(p)
 if p.endswith('.py'):ast.parse((R/p).read_text(encoding='utf-8-sig'))
 if p.endswith('.md'):
  text=(R/p).read_text(encoding='utf-8');text=text[len(git('show',BASE+':'+p)):] if p=='docs/development-log.md' else text
  for link in re.findall(r'\]\(([^)]+)\)',text):
   if link.startswith(('http:','https:','mailto:')):continue
   target=unquote(link.strip('<>')).split('#')[0];f=(R/p).parent/target if target else R/p
   if not f.exists() and f.resolve()!=OUT.resolve():missing.append([p,link])
check('all changed documentation references resolve',not missing)
commands=json.loads((LOG/'commands.json').read_text(encoding='utf-8'));prior=read('docs/research/atlas-temporal-integration-validation.json')['commands']
check('all inherited relevant commands freshly executed',len(commands)==len(prior) and all(c['exitCode']==0 and c['args']==p['args'] for c,p in zip(commands,prior)))
check('438 inherited tests passed',sum(c.get('tests') or 0 for c in commands)==438)
t=time.perf_counter();p=subprocess.run([sys.executable,str(H/'test_compare.py')],cwd=R,capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PROJ_NETWORK':'OFF'});text=p.stdout+p.stderr;(LOG/'comparison-focused.log').write_text(text,encoding='utf-8');m=re.search(r'Ran (\d+) tests?',text);commands.append({'name':'comparison-focused','args':[sys.executable,str(H/'test_compare.py')],'exitCode':p.returncode,'tests':int(m[1]) if m else None,'elapsedSeconds':time.perf_counter()-t});check('eight comparison tests passed',p.returncode==0 and int(m[1])==8)
check('git diff whitespace check',subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0)
check('protected original files unchanged after all tests',unchanged())
result={'schema':'atlas-local-architecture-validation/v1','startingCheckpoint':BASE,'decision':'C — DECISION READY','checks':checks,'passed':sum(c['passed'] for c in checks),'failed':[c['check'] for c in checks if not c['passed']],'tests':sum(c.get('tests') or 0 for c in commands),'commands':commands,'proofHashes':{p:sha(R/p) for p in sorted(changed) if (R/p).exists() and p not in NAV and (R/p)!=OUT},'navigationMissing':missing,'review':'Only bounded comparison/decision/report/navigation changes; no accepted evidence/contracts/production changes or runtime construction. No data acquisition/private access/S7/cloud. Full diff/untracked review required before commit.'}
OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result[k] for k in ['passed','failed','tests','navigationMissing']},indent=2));sys.exit(bool(result['failed']))
