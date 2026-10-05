"""Retain small evidence/identity records; large imagery and captures stay external."""
import argparse,json
from collections import Counter
from pathlib import Path
import swissimage_baseline as s

def record(repo,data):
    root=data/'derived/atlas/riffelhorn'/s.VERSION
    captures=data/'experiments/atlas'/s.VERSION/'captures'
    m=json.loads((root/'manifest.json').read_text(encoding='utf8'))
    v=json.loads((root/'verification.json').read_text(encoding='utf8'))
    generation=json.loads((root/'generation.json').read_text(encoding='utf8'))
    source=json.loads((root/'source-diagnostics.json').read_text(encoding='utf8'))
    c=json.loads((captures/'capture.json').read_text(encoding='utf8'))
    signals=json.loads((captures/'signal-diagnostics.json').read_text(encoding='utf8'))
    rebuild=data/'derived/atlas/riffelhorn'/(s.VERSION+'-rebuild')
    assert (root/'manifest.json').read_bytes()==(rebuild/'manifest.json').read_bytes()
    assert len(c['scenes'])==8 and len(c['navigation'])==6 and not c.get('failure') and not c['pageErrors']
    assert all(r.get('status')==200 for r in c['requests'])
    assert all(s.digest(repo/f)==h for f,h in c['productionHashes'].items())
    visual=[]
    for row in c['scenes']:
        assert s.digest(captures/row['filename'])==row['sha256']
        assert row['state']['terrain']=={'source':'terrain-dem','exaggeration':1.45}
        assert row['state']['camera']['center']==row['scene']['center'] and all(abs(row['state']['camera'][k]-row['scene'][k])<1e-12 for k in ['zoom','pitch','bearing'])
        assert all(x==0 for x in row['state']['hillshade']['hillshade-exaggeration'][4::2])
        visual.append({k:row[k] for k in ['mode','scene','filename','sha256']}|
                      {'geometryLevels':sorted({t['z'] for t in row['state']['usedDEMs']}),
                       'imageryLevels':sorted({t['z'] for t in row['state']['usedImagery'] or []})})
    result={'baseline':'6f2eb0217c167630154fe4e9d4aa6c8c5d59a76e','classification':'BASELINE PROOF ESTABLISHED WITH EXPLICIT INTERPRETATION LIMITS',
      'source':{'authority':'swisstopo','product':'SWISSIMAGE 2023 DOP10 RGB orthophoto mosaic',
        'sourceFamily':'swissimage-retained-2023','origin':'already orthorectified/processed upstream; not raw aerial images',
        'acquisition':m['acquisition'],'assets':m['sources'],'retainedNotReacquired':True,
        'distributedSpacingMetres':.1,'nominalUpstreamInformationMetres':.25,'nativeCRS':'EPSG:2056',
        'sourceBounds':m['sourceBounds'],'sourceBytes':generation['sourceBytes'],
        'encoding':'RGB8 COG; internal YCbCr JPEG95; three bands',
        'colourTransfer':'Not calibrated/established; sRGB assumed explicitly for preparation and signal diagnostics',
        'orthorectificationGeometryRevision':'UNKNOWN','rights':m['rights']},
      'product':{k:m[k] for k in ['id','revision','identity','origin','delivery','lineage','software','recipeSha256']},
      'levels':[{k:v for k,v in level.items() if k!='tiles'}|{'tileCount':len(level['tiles'])} for level in m['levels']],
      'storage':generation,'verification':v,'independentFullRebuildManifestIdentical':True,
      'geometry':c['geometry'],'geometrySourceHashesVerified':{'assets':100,'identity':'b24a4fdc7b378ba79d442d0ce216a031dfb95a6bc6eed5ad9c33be61175651f4','vrtSha256':'8b097d62be84e110cdf8efd695f63d685a9069fcad98aae91660b7fb42e17998'},
      'sourcePatches':source['patches'],'sourceDisplay':signals,
      'capture':{'browser':c['browserVersion'],'viewport':c['viewport'],'DPR':c['devicePixelRatio'],'visualIndex':visual,
                 'navigationSequences':2,'navigationLegs':len(c['navigation']),'sampledStates':sum(len(n['frames'])for n in c['navigation']),
                 'requestCounts':dict(Counter(r['kind']for r in c['requests'])),
                 'httpErrors':0,'pageErrors':0,'cancellations':dict(Counter(r['error']for r in c['failures'])),
                 'limitations':'Navigation state telemetry, not a perceptual video or a universal no-popping claim. Common hosted imagery is unpinned and not archived as provider tiles.'},
      'productionUnchanged':{'hashes':c['productionHashes'],'runtimeFilesChanged':False,'analyticalElevation':'independent AWS z15'},
      'externalOutputs':{'product':root.relative_to(data).as_posix(),'captures':captures.relative_to(data).as_posix(),
                         'diagnosticHashes':{n:s.digest(root/n)for n in ['source-diagnostics.json','probe-locations.json','transparent.png']},
                         'captureReportSha256':s.digest(captures/'capture.json'),'signalReportSha256':s.digest(captures/'signal-diagnostics.json')},
      'correctionPerformed':False,'benchmarkExpanded':False,
      'next':'One bounded steep-face acquisition/multiview-support feasibility assessment for these four retained tiles; no additional imagery acquisition, correction or reconstruction implied.'}
    s.save(repo/'docs/atlas/swissimage-source-derived-baseline.json',result)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);a=p.parse_args();record(Path(__file__).resolve().parents[2],a.data)
