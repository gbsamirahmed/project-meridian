"""Protection and navigation receipt; does not write accepted evidence."""
from pathlib import Path
import ast,hashlib,json,re,subprocess,sys
from urllib.parse import unquote
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];H=Path(__file__).parent
BASE='b2a57fdd4c942a79f5a10f8d675ec27ba33c9efc'
OUT=R/'docs/research/atlas-local-runtime-validation.json'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
checks=[]
def check(name,ok):checks.append({'check':name,'passed':bool(ok)})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True,encoding='utf-8')
def unchanged():
 tree={line.split('\t')[1]:line.split()[2] for line in git('ls-tree','-r',BASE).splitlines()};keep=[p for p in tree if p not in NAV]
 hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(keep)+'\n',text=True).splitlines()
 return len(hashes)==len(keep) and all(tree[p]==h for p,h in zip(keep,hashes))
b=read('docs/research/atlas-local-runtime-baseline.json');x=read('docs/research/atlas-local-runtime-results.json');plan=read('runtime/atlas/slice-plan.json');next_task=read('runtime/atlas/next-task.json')
old=read('docs/research/atlas-temporal-integration-baseline.json');arch=read('docs/research/atlas-local-architecture-baseline.json')
check('clean exact starting checkpoint and upstream recorded',b['startingCheckpoint']==BASE and b['branch']=='main' and b['divergence']=='0\t0')
check('all starting tracked non-navigation files unchanged',unchanged())
check('plan frozen before implementation remains exact',b['frozenBeforeImplementation'] and plan['frozenBeforeImplementation'] and sha(H/'slice-plan.json')==b['planSha256']==x['planSha256'])
check('read workflow scope overrides prior wider proposal','narrows' in plan['scopePrecedence'] and 'new publication writer' in plan['exclusions'])
protected=read('docs/atlas/information-display-plan.json')['productionHashes']
check('all113 protected production hashes unchanged',len(protected)==113 and all(sha(R/p)==h for p,h in protected.items()))
check('all42 canonical statuses unchanged',len(old['canonicalRows'])==42 and P.admission.canonical_rows((R/'docs/research/atlas-research-state.md').read_text(encoding='utf-8'))==old['canonicalRows'])
check('retained source admission unchanged',P.admission.assess()['sources']==old['sourceAdmission'])
accepted=read('docs/research/atlas-integrity-cost-baseline.json');store=P.DATA/'experiments/atlas/tryfan-regional-pilot-v1'
check('all17 accepted Tryfan store files unchanged',len(accepted['acceptedStoreHashes'])==17 and all(sha(store/p)==h for p,h in accepted['acceptedStoreHashes'].items()))
prepared=P.DATA/old['preparedRootRelative']
check('all6 accepted Riff prepared files unchanged',len(old['preparedHashes'])==6 and all(sha(prepared/p)==h for p,h in old['preparedHashes'].items()))
check('native unit/source receipts unchanged',all(sha(P.DATA/p)==h for p,h in old['unitEvidence'].items()))
check('all66 retained dated Exe files unchanged',len(old['retainedExeDirectory'])==66 and all(sha(P.DATA/'derived/atlas/water-check-v1'/p)==h for p,h in old['retainedExeDirectory'].items()))
temporal=Path(arch['previousTemporalStore'])
check('complete accepted temporal external state unchanged',set(arch['previousStoreHashes'])=={p.relative_to(temporal).as_posix() for p in temporal.rglob('*') if p.is_file()} and all(sha(temporal/p)==h for p,h in arch['previousStoreHashes'].items()))
selected=Path(b['publicationRoot'])
check('all115 selected publication store files unchanged',len(b['storeHashes'])==115 and set(b['storeHashes'])=={p.relative_to(selected).as_posix() for p in selected.rglob('*') if p.is_file()} and all(sha(selected/p)==h for p,h in b['storeHashes'].items()))
for name in ['atlas-multi-region','atlas-regional-dependencies']:
 a=read('docs/research/'+name+'-results.json');s=Path(a['store'])
 check(name+' root unchanged',json.loads((s/'current.json').read_text())['generation']==a['history'][-1])
 check(name+' historical objects unchanged',all(sha(p)==p.stem for d in ['components','publications','membership','artifacts'] for p in (s/d).iterdir() if p.is_file()))
for n in range(1,7):check('accepted S'+str(n)+' report retained',(R/f'docs/research/tryfan-pilot-s{n}.md').exists())
for name in ['atlas-measured-storage-processing-serving','atlas-component-membership','atlas-component-granularity','atlas-validation-packing','atlas-integrity-cost','atlas-regional-expansion','atlas-riffelhorn-preparation','atlas-riffelhorn-retrieval','atlas-multi-region','atlas-regional-dependencies','atlas-temporal-integration','atlas-local-architecture']:
 check(name+' report preserved',(R/f'docs/research/{name}.md').exists())
check('real population49/seven components/three generations',x['population']=={'records':49,'riffelhorn':44,'tryfanSourceProductDescriptors':5,'components':7,'generations':3})
check('all84 repeated indexed/full-scan comparisons agree',x['agreement'] and x['comparisons']==84 and len(x['queries'])==84)
check('three complete repeated workflow samples',len(x['samples'])==3 and all(s['built']['records']==s['rebuilt']['records']==49 for s in x['samples']))
check('fresh full-validation process measured',all(s['freshProcessFullOpenAndQueryMs']>s['openMs'] for s in x['samples']))
check('full validation includes current payload verification',all(s['validation']['payloadBytesHashed']==171482433 and s['validation']['payloadHashOperations']==329 for s in x['samples']))
check('logical counters distinguish additional preparation reads',all(t in x['samples'][0]['native']['physicalIO'] for t in ['additional','logical']))
check('zero ancestry in every measured query and historical replay',all(q['indexed']['ancestryTraversals']==q['scan']['ancestryTraversals']==0 for q in x['queries']) and all(r['ancestryTraversals']==0 for r in x['replay']))
check('one native body preserves three exact historical pins',[r['generation'] for r in x['replay']]==b['history'] and len({r['evidenceSha256'] for r in x['replay']})==1)
check('full catalogue audits disclosed and measured',all(q['indexed']['catalogueSelectorAuditRecords']==49 and q['indexed']['catalogueBytesHashed']==81920 for q in x['queries']))
check('point and feature candidate reduction measured',all(q['indexed']['candidates']==10 for q in x['queries'] if q['case']=='point-all') and all(q['indexed']['candidates']==1 for q in x['queries'] if q['case']=='bedrock-id'))
check('broad reads and no-result cases retained',all(q['indexed']['candidates']==44 for q in x['queries'] if q['case']=='broad-core') and all(q['resultCount']==0 for q in x['queries'] if q['case']=='outside-point'))
output_root=Path(x['environment']['outputRoot'])
check('all measured80KB catalogues external and sealed',not output_root.is_relative_to(R) and x['summary']['catalogueBytes']==81920 and all(sha(output_root/('measured-'+str(s['repeat']))/'epochs'/s['built']['epoch']/'index.sqlite')==s['built']['sha256'] for s in x['samples']))
check('selected published historical identity frozen',plan['selectedGeneration']==b['history'][0] and plan['historicalGenerations']==b['history'])
report=(R/'docs/research/atlas-local-runtime.md').read_text(encoding='utf-8')
check('all30 report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,31)))
check('scientific and custody limits explicit',all(t in report for t in ['source-product metadata','unknown','power-loss','population-wide','CLOSED','no generation fallback']))
check('one concrete unbegun processing task',next_task['status']=='NOT BEGUN' and next_task['title'] in report and len(next_task['acceptance'])==7)
for p in NAV:
 text=(R/p).read_text(encoding='utf-8')
 check('current runtime result and next-task link in '+p,all(s in text for s in ['C — VERTICAL SLICE SUCCESS','atlas-local-runtime.md',next_task['title'],'Tryfan remains CLOSED / ACCEPTED']))
check('development log append-only',(R/'docs/development-log.md').read_text(encoding='utf-8').startswith(git('show',BASE+':docs/development-log.md')))
runtime={'runtime/atlas/'+n for n in ['authority.ts','cli.ts','errors.ts','index.ts','measure.mjs','next-task.json','README.md','run-checks.py','slice-plan.json','test-runtime.mjs','tsconfig.json','types.ts','validate.py','worker.py','worker.ts']}
allowed=NAV|runtime|{'docs/research/atlas-local-runtime'+s for s in ['.md','-baseline.json','-results.json','-validation.json']}
changed=set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()+[OUT.relative_to(R).as_posix()])
check('exact authorized runtime/report/navigation file boundary',changed==allowed)
check('no large payload/cache committed',all((R/p).stat().st_size<250000 and not p.endswith(('.sqlite','.db','.tif','.png','.pyc','.npz')) for p in changed if (R/p).exists() and p not in NAV))
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
commands=json.loads((R/'../../Codex/atlas-local-runtime-v1/regression/commands.json').resolve().read_text(encoding='utf-8'));prior=read('docs/research/atlas-local-architecture-validation.json')['commands']
check('all inherited regression commands freshly passed',len(commands)==len(prior)+2 and all(c['exitCode']==0 and c['args']==p['args'] for c,p in zip(commands,prior)))
check('446 inherited tests passed',sum(c.get('tests') or 0 for c in commands[:len(prior)])==446)
check('runtime types and62 focused tests passed',commands[-2]['exitCode']==commands[-1]['exitCode']==0 and commands[-1]['tests']==62)
check('git diff whitespace check',subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0)
check('protected original files unchanged after regressions',unchanged())
result={'schema':'atlas-local-runtime-validation/v1','startingCheckpoint':BASE,'decision':'C — VERTICAL SLICE SUCCESS','checks':checks,'passed':sum(c['passed'] for c in checks),'failed':[c['check'] for c in checks if not c['passed']],'tests':sum(c.get('tests') or 0 for c in commands),'commands':commands,'runtimeHashes':{p:sha(R/p) for p in sorted(changed) if (R/p).exists() and p not in NAV and (R/p)!=OUT},'navigationMissing':missing,'review':'Read/index/query runtime plus bounded tests/report/navigation only. No canonical writer, accepted evidence/contracts/production changes, acquisition/private/S7/cloud. Full diff/untracked review required before commit.'}
OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:result[k] for k in ['passed','failed','tests','navigationMissing']},indent=2));sys.exit(bool(result['failed']))
