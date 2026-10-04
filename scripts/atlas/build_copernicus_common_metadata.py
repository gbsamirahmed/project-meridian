"""Owned metadata using the existing Atlas model, outside production imports."""
import copy
import json
import copernicus_common as cp
import riffelhorn_terrain as rt
from riffelhorn_support import save

def run():
    data=rt.resolve_storage_roots(require_data=True).data;manifest=cp.verify(data);acq=cp.source_record(data)
    old=json.loads((cp.REPO/'docs/atlas/global-reference-metadata.json').read_text(encoding='utf8'))
    known=lambda v:{'status':'known','value':v}
    unknown=lambda r:{'status':'unknown','reason':r}
    source=copy.deepcopy(old['source']);source['id']='copernicus-glo30-common-2021-local-selection'
    source['name']='Copernicus GLO-30 2021 public COG selection for two z8 common-terrain roots'
    source['revision']=known(acq['identity']);source['assets']=[{'href':'${MERIDIAN_DATA_ROOT}/'+a['path'],'sha256':a['sha256']}for a in acq['assets']]
    source['coverage']['area']['value']['bounds']=[6.9998611111111115,45.00013888888889,8.999861111111111,48.00013888888889]
    source['resolution']['limitations']=source['resolution']['limitations'].replace('two retained','six retained')
    source['nodata']=known('Six retained float32 COGs declare no nodata; selected two-root preparation fully finite. Missing upstream land/ocean tiles are not inferred zero.')
    source['documentation']+=['docs/atlas/copernicus-common-product.md','docs/atlas/copernicus-common-acquisition.json']
    ref={'kind':'source','id':source['id'],'revision':source['revision']}
    area={'kind':'native-rectangle','crs':{'name':'WGS 84 longitude/latitude','identifier':'OGC:CRS84'},'axisOrder':'xy','bounds':list(cp.GEOGRAPHIC)}
    product={'id':cp.VERSION,'name':'Meridian bounded Copernicus common/coarse terrain product','version':known('v1'),'revision':known(manifest['identity']),'producer':known('Meridian'),
        'surface':source['surface'],'vertical':{'kind':'preserved','from':ref,'reference':source['verticalReference']},'elevationUnit':known('metre'),
        'lineage':{'contributors':[ref],'contributorList':'complete','spatialMapping':'uniform','processing':[
            {'method':'Mosaic six whole 2021 COGs preserving source Point registration; horizontal EPSG:4326 to EPSG:3857 bilinear warp to aligned z13 float32 heights. No height or registration adjustment.','software':manifest['processing'],'record':{'href':'docs/atlas/copernicus-common-generation.json'}},
            {'method':'Recursive 2x2 arithmetic means of unencoded heights; float64 accumulation and float32 storage. Uniform Mercator pixel area, not ground-area weighting.','parameters':{'minimumZoom':8,'maximumZoom':13,'threads':1}},
            {'method':'Encode each level independently as lossless RGB PNG Terrarium; no encoded-RGB averaging.','parameters':{'quantizationMetres':1/256}}],
            'limitations':'Complete immediate published dataset contributor; per-post upstream infill/epoch remains unavailable. Coarse averaging suppresses extrema; no structural generalisation.'},
        'delivery':{'kind':'raster-tiles','horizontalReference':known({'name':'WGS 84 / Pseudo-Mercator','identifier':'EPSG:3857'}),'scheme':'xyz','tileSize':[256,256],
            'encoding':{'name':'terrarium','description':'R*256+G+B/256-32768 metres; nearest quantization; EGM2008 unchanged','quantizationIncrement':{'value':1/256,'unit':'metre'}},'format':'lossless RGB PNG',
            'tileTemplate':'${MERIDIAN_DATA_ROOT}/'+cp.PRODUCT+'/tiles/{z}/{x}/{y}.png','zoom':{'min':8,'max':known(13)},
            'availability':'All 2730 descendants of z8/133/90 and z8/133/91. No tiles outside, below z8 or above z13; not a global product.',
            'resampling':known('Finest bilinear source sampling; recursive box-mean parents; renderer overzoom above z13 only.')},
        'sourceInformation':{'description':'One-arcsecond source posts (~21.5 m east/west and 30.9 m north/south near Riffelhorn); measurement resolution unknown. Delivery z13 (~13.28 m there) oversamples these posts.',
            'informationCeiling':known('Source posts bound available information. z12 already undersamples the east/west postings locally; z13 avoids that but adds no observations. No sharp isotropic information zoom is claimed; all higher renderer zoom is overzoom.')},
        'spatial':{'coverage':known(area),'validSupport':known({'area':area,'purpose':'Bounded land-context delivery and preparation evaluation, not scientific ground truth or a validated regional seam','basis':'All source-to-product checks and complete finite root coverage; docs/atlas/copernicus-common-checks.json'}),'transitionSupport':unknown('No Swiss composition, transition or global ocean/polar policy established.')},
        'nodata':known(manifest['delivery']['nodata']),'rights':source['rights'],
        'generation':{'timestamp':known(json.loads((cp.REPO/'docs/atlas/copernicus-common-generation.json').read_text())['generatedAt']),'buildRecord':{'href':'${MERIDIAN_DATA_ROOT}/'+cp.PRODUCT+'/manifest.json','sha256':rt.digest(data/cp.PRODUCT/'manifest.json')}},
        'documentation':['docs/atlas/copernicus-common-product.md','docs/atlas/copernicus-common-product-plan.json','docs/atlas/copernicus-common-checks.json']}
    # Software versions only; scientific numeric parameters live separately.
    product['lineage']['processing'][0]['software']={k:str(v)for k,v in manifest['processing'].items()if k in ['python','numpy','rasterio','gdal','pyproj','proj','pillow']}
    save(cp.REPO/'docs/atlas/copernicus-common-metadata.json',{'schemaVersion':1,'source':source,'product':product})
    save(data/cp.PRODUCT/'atlas-metadata.json',{'schemaVersion':1,'source':source,'product':product})

if __name__=='__main__':run()
