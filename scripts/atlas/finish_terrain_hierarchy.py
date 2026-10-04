"""Verify sparse evaluated products and generate owned metadata/renderer summary."""
import argparse,copy,json,time,platform
from pathlib import Path
import numpy as np
from PIL import __version__ as pillow_version
import terrain_hierarchy as h
import riffelhorn_terrain as rt
import riffelhorn_support as sp

def known(x):return {'status':'known','value':x}
def unknown(x):return {'status':'unknown','reason':x}

def finish(data,suffix,rebuild=False):
    hierarchy=h.Hierarchy(data,14,suffix,verify=False);manifest=hierarchy.inventory();out=data/h.EXPERIMENT
    if rebuild:
        rebuilt=h.Hierarchy(data,14,suffix+'-rebuild',verify=False);start=time.perf_counter()
        for row in manifest['files']:
            body,other=rebuilt.tile(row['strategy'],row['z'],row['x'],row['y'])
            if other!=row:raise ValueError('Deterministic tile or mask rebuild differs')
        second=rebuilt.inventory()
        if second['identity']!=manifest['identity']:raise ValueError('Deterministic product rebuild differs')
        record_path=out/'rebuild.json'
        record=json.loads(record_path.read_text())if record_path.exists()else None
        if record and record['identity']==manifest['identity']:
            # Preserve first independent generation timing; a cached recheck is different.
            record['lastVerificationSeconds']=time.perf_counter()-start
        else:record={'identity':manifest['identity'],'tilesAndMasksMatched':len(manifest['files']),'seconds':time.perf_counter()-start}
        sp.save(record_path,record)
    reproducibility=json.loads((out/'rebuild.json').read_text())
    if reproducibility['identity']!=manifest['identity']or reproducibility['tilesAndMasksMatched']!=len(manifest['files']):raise ValueError('Stale independent rebuild record')
    # Original bytes whenever a source tile is copied, and explicit overzoom error.
    err=0;counts={};bytes_total=0;mask_bytes=0
    for row in manifest['files']:
        key=f"tiles/{row['z']}/{row['x']}/{row['y']}.png"
        if row['contributor']:
            if row['sha256']!=hierarchy.swiss_files[key]['sha256']:raise ValueError('Swiss tile modified')
        elif row['z']<=13:
            if row['sha256']!=hierarchy.common_files[key]['sha256']:raise ValueError('Common tile modified')
        else:
            z,x,y=row['z'],row['x'],row['y'];factor=2**(z-13)
            reference=h.overzoom(hierarchy.padded(x//factor,y//factor),z,x,y)
            a=rt.decode((hierarchy.out/row['path']).read_bytes());err=max(err,float(np.max(abs(a-reference))))
        group=f"{row['strategy']}/z{row['z']}/label{row['contributor']}";counts[group]=counts.get(group,0)+1
        bytes_total+=row['bytes'];mask_bytes+=(hierarchy.out/row['maskPath']).stat().st_size
    result={'baseline':'74ea75b1577fbdd7a85af3a1989ac8aee42c54f0','configuration':hierarchy.config,'identity':manifest['identity'],'manifestSha256':rt.digest(hierarchy.out/'manifest.json'),'tiles':len(manifest['files']),'terrainBytes':bytes_total,'maskBytes':mask_bytes,'counts':counts,'overzoomQuantizationMaxM':err,'exactSwissBytes':True,'exactCommonThroughZ13':True,'rebuild':reproducibility,'scope':'Sparse numeric/capture/requested inventory, not full delivered area or global generation'}
    # Potential regional area is delivery support, not an accepted seam or source area.
    result['eligibleRegionalByLevel']={}
    for z in range(12,19):
        count=sum(key.startswith(f'tiles/{z}/')for key in hierarchy.swiss_files)
        result['eligibleRegionalByLevel'][str(z)]={'completeTiles':count,'areaMercatorM2':count*(rt.WORLD/2**z)**2,'H0RegionalTiles':count,'H1RegionalTiles':count if z>=14 else 0,'mixedProductCells':0}
    result['areaInterpretation']='Projected Mercator area of full original Swiss per-level delivery support; not physical land area, sampled inventory area, confidence, or validated transition support.'
    result['software']={'python':platform.python_version(),'numpy':np.__version__,'pillow':pillow_version}
    product=copy.deepcopy(json.loads((h.REPO/'docs/atlas/copernicus-common-metadata.json').read_text())['product'])
    swiss=json.loads((h.REPO/'docs/atlas/riffelhorn-support-product.json').read_text())['product'];common=copy.deepcopy(product)
    refs=[{'kind':'product','id':p['id'],'revision':p['revision']}for p in [common,swiss]]
    base='${MERIDIAN_DATA_ROOT}/'+h.PRODUCT+suffix+'/'
    asset={'href':base+'manifest.json','sha256':result['manifestSha256']}
    product.update({'id':h.VERSION+suffix,'name':'Bounded native-height Copernicus / Swiss hierarchy evaluation','version':known('v1'),'revision':known(manifest['identity']),'surface':{'kind':'heterogeneous','description':'Selected Copernicus edited DSM and Swiss DTM. No scientific harmonization or mixed-cell fusion.'},'vertical':{'kind':'heterogeneous','parts':[{'contributor':refs[0],'reference':known({'name':'EGM2008 height','identifier':'EPSG:3855'})},{'contributor':refs[1],'reference':known({'name':'LN02 height','identifier':'EPSG:5728'})}],'description':'Pure tiles retain native heights; globally no single vertical reference. No accepted vertical transformation.'}})
    product['lineage']={'contributors':refs,'contributorList':'complete','spatialMapping':'mask','contributionMask':{'asset':asset,'interpretation':'files[].maskPath is a lossless constant uint8 label per tile/cell: 0 common EGM2008, 1 Swiss LN02. Strategy and zoom are required to interpret spatial contribution; labels are not confidence. No blended cells.','contributors':refs},'processing':[{'method':'Fixed evaluation tile selection by actual per-level Swiss delivery support and H0 / H1 requested DEM level policy','parameters':{'regionalTileGate':14,'heightCorrection':False,'blending':False},'record':{'href':'docs/atlas/terrain-hierarchy-policy.json'}},{'method':'Common-only delivery above z13: neighbor-backfilled cell-centred bilinear resampling of encoded z13; independent nearest Terrarium re-encoding','parameters':{'maximumDeliveryZoom':18,'quantizationIncrementM':1/256}}],'limitations':'Complete immediate product contributors; upstream epoch/measurement limitations inherited. Sparse tested tiles only. Masks identify contributors but do not establish scientific comparability.'}
    for step in product['lineage']['processing']:step['software']=result['software']
    product['delivery'].update({'tileTemplate':base+'tiles/{strategy}/{z}/{x}/{y}.png','zoom':{'min':8,'max':known(18)},'availability':'Only evaluated sparse tile inventory; generator serves finite common two-root descendants z8-18. Swiss available complete original delivery tiles only, subject to strategy gate. No z0-7 or outer fallback.','resampling':known('Exact input PNG bytes through original levels; common above13 explicitly bilinear overzoom. No new observations.')})
    product['sourceInformation']={'description':'Common source is one-arcsecond GLO-30; Swiss distributed grid is 0.5 m. Neither delivery zoom nor contributor label implies independent measurement resolution.','informationCeiling':known('Common z13 signal is resampled at z14-18. Swiss z14-18 retains its previously prepared signal; meaningful visible gain in evaluated close/detail views. No universal perceptual threshold.')}
    product['spatial']={'coverage':known({'kind':'asset','asset':asset,'crs':known({'name':'WGS 84 / Pseudo-Mercator','identifier':'EPSG:3857'}),'interpretation':'files[].strategy/z/x/y defines per-policy sparse XYZ tile coverage, not complete source coverage.'}),'validSupport':unknown('Experiment shows hard spatial/LOD discontinuities; not accepted as navigation-ready hierarchy.'),'protectedInterior':swiss['spatial']['protectedInterior'],'transitionSupport':unknown('Additional support is not a validated seam. H0/H1 retain a hard join; no transition representation accepted.')}
    product['fallback']={'product':refs[0],'when':'Regional tile unavailable or excluded by requested-level gate, within finite common context','behavior':'Pure native-height common tile or explicitly overzoomed common signal; not extension of Swiss coverage.'}
    product['rights']['references']=list(dict.fromkeys(common['rights']['references']+swiss['rights']['references']))
    product['rights']['attribution']=list(dict.fromkeys(common['rights']['attribution']+swiss['rights']['attribution']))
    product['rights']['licence']=known('Contributor-specific Copernicus DEM GLO-30 F terms and swisstopo reuse terms; no unified software licence substitutes for these data rights.')
    product['generation']={'timestamp':unknown('Deterministic lazy evaluated inventory; timestamps intentionally excluded from immutable identity.'),'buildRecord':asset}
    product['documentation']=['docs/atlas/terrain-hierarchy-prototype.md','docs/atlas/terrain-hierarchy-policy.json']
    sp.save(hierarchy.out/'atlas-metadata.json',product)
    sp.save(h.REPO/'docs/atlas/terrain-hierarchy-product.json',{'product':product,'checks':result})
    captures={}
    for folder,provider in [('discovery','common'),('discovery','H0'),('captures','H1'),('captures','H0'),('navigation','H1')]:
        p=out/folder/(provider+'.json')
        if not p.exists():continue
        raw=json.loads(p.read_text());key=folder+'/'+provider
        rows=[]
        for r in raw['records']:
            state=r['state'];rows.append({'scene':r['scene'],'camera':state['camera'],'bounds':state['bounds'],'centerExaggeratedMapLibreElevation':state['centerElevation'],'usedDEMLevels':sorted(set(t['z']for t in state.get('usedDEMs',[]))),'geometryLevels':sorted(set(t['z']for t in state['visibleDEMs']['terrain-dem'])),'reliefLevels':sorted(set(t['z']for t in state['visibleDEMs']['terrain-analysis-dem'])),'newTileResponses':r['newTileResponses'],'captureSha256':r['sha256'],'filename':r['filename']})
        captures[key]={'browserVersion':raw['browserVersion'],'viewport':raw['viewport'],'records':rows,'navigation':[{**r,'frames':[{**frame,'levels':sorted(set(frame['levels']))}for frame in r['frames']]}for r in raw.get('navigation',[])],'responses':len(raw['responses']),'statusCounts':{str(s):sum(r['status']==s for r in raw['responses'])for s in set(r['status']for r in raw['responses'])},'contributorResponseCounts':{str(s):sum(r.get('contributor')==s for r in raw['responses'])for s in set(r.get('contributor')for r in raw['responses'])},'responseBytes':sum(r.get('bytes',0)for r in raw['responses']),'failedRequests':raw['failedRequests'],'pageErrors':raw['pageErrors'],'failure':raw.get('failure'),'sourceReportSha256':rt.digest(p)}
    sp.save(h.REPO/'docs/atlas/terrain-hierarchy-renderer.json',captures)
    print(json.dumps({k:result[k]for k in ['identity','tiles','terrainBytes','maskBytes','overzoomQuantizationMaxM','rebuild']},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--suffix',default='-discovery');p.add_argument('--rebuild',action='store_true');a=p.parse_args();finish(rt.resolve_storage_roots(require_data=True).data,a.suffix,a.rebuild)
