"""Frozen real-fixture full/grouped/selective comparison with explicit startup costs."""
import json,statistics,subprocess,sys,time,tracemalloc
from pathlib import Path
import query as Q
summary=lambda xs:{'median':statistics.median(xs),'min':min(xs),'max':max(xs),'runs':len(xs)}
s=Q.Session();matrix=Q.P.load(Q.H/'matrix.json');rows=[];hashes={};agree=True
for c in matrix['cases']:
 oracle=s.query(c['query'],'scan')['answer'];hashes[c['id']]=Q.P.digest(Q.P.canonical(oracle))
 for mode in matrix['organisations']:
  repeats=[s.query(c['query'],mode) for _ in range(matrix['warmRepetitions'])]
  same=all(q['answer']==oracle for q in repeats);Q.P.require(same,'oracle disagreement '+c['id']+mode);agree&=same
  counters={k:v for k,v in repeats[0]['metrics'].items() if k!='elapsedSeconds'};Q.P.require(all({k:v for k,v in q['metrics'].items() if k!='elapsedSeconds'}==counters for q in repeats),'unstable structural counters')
  rows.append({'case':c['id'],'query':c['query'],'organisation':mode,'agreement':same,'metrics':counters,'elapsedSeconds':summary([q['metrics']['elapsedSeconds'] for q in repeats]),'answerSha256':hashes[c['id']]})
fresh=[]
for n in range(matrix['freshProcessRepetitions']):
 start=time.perf_counter();p=subprocess.run([sys.executable,str(Q.H/'query.py'),'--matrix'],cwd=Q.R,capture_output=True,text=True,encoding='utf-8');Q.P.require(p.returncode==0,p.stderr);r=json.loads(p.stdout);Q.P.require(r['answers']==hashes,'fresh-process disagreement');fresh.append({'setup':r['setup'],'processAndMatrixSeconds':time.perf_counter()-start,'answerHashesAgree':True})
tracemalloc.start();memory_session=Q.Session();_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
pop=Q.P.load(Q.R/'docs/research/atlas-riffelhorn-retrieval-population.json');core_pairs=sum(Q.shape(a['native']['geometry']).intersection(Q.shape(b['native']['geometry'])).intersection(Q.CORE).area>0 for i,a in enumerate(s.features) for b in s.features[i+1:])
x={'schema':'atlas-riffelhorn-retrieval-results/v1','startingCheckpoint':matrix.get('startingCheckpoint',Q.P.load(Q.H/'plan.json')['startingCheckpoint']),'preparedRevision':s.manifest['revision'],'matrixSha256':Q.P.sha(Q.H/'matrix.json'),'planSha256':Q.P.sha(Q.H/'plan.json'),'sourceImplementationSha256':Q.P.sha(Q.H/'query.py'),'realPopulation':pop,'fullFeaturePairsIntersectingInsideCore':core_pairs,'observations':rows,'agreement':agree,'comparableRepeatedQueries':len(rows)*matrix['warmRepetitions'],'matrixCases':len(matrix['cases']),'organisations':matrix['organisations'],'freshProcessRuns':fresh,'setup':s.setup,'freshSetupSeconds':summary([q['setup']['elapsedSeconds'] for q in fresh]),'freshProcessAndMatrixSeconds':summary([q['processAndMatrixSeconds'] for q in fresh]),'pythonTrackedStartupPeakBytes':peak,'memoryLimit':'Python tracked allocation peak includes validation/reconstruction/transient JSON; excludes native GDAL/PROJ/GEOS and Node child RSS; not whole-process memory','timingLimit':'five warm repetitions per case/organisation, three fresh processes. Filesystem/OS cache not cleared; genuine process-cold, not disk-cold. Query timing includes answer UTF8 encoding; no claim tiny differences imply scaling.','byteLimit':'candidateRecordBytesRepresented is an equivalent JSON byte proxy, not actual bytes reread. metadataFileReads per warm query are0; startup parses all five prepared members after full verification. decodedPayloadBytes measures returned native window buffers, not compressed physical block I/O.','syntheticPopulationExpansion':False,'persistentIndexBytes':0,'decision':'C - PROOF SUCCESS','nextTask':Q.P.load(Q.H/'next-task.json')}
(Q.R/'docs/research/atlas-riffelhorn-retrieval-results.json').write_bytes(Q.P.canonical(x));print(json.dumps({'cases':x['matrixCases'],'comparisons':x['comparableRepeatedQueries'],'agreement':agree,'freshSetup':x['freshSetupSeconds'],'memory':peak}))
