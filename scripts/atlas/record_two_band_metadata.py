"""Lightweight metadata for the frozen diagnostic, using existing Atlas model."""
import json
from pathlib import Path
import two_band_transition as tb

repo=tb.REPO
data=Path('C:/Users/gbsam/Documents/Projects/meridian-data')
build=json.loads((data/tb.PRODUCT/'build.json').read_text())
spec=json.loads(tb.SPEC.read_text())
common=json.loads((repo/'docs/atlas/copernicus-common-metadata.json').read_text())['product']
regional=json.loads((repo/'docs/atlas/riffelhorn-support-product.json').read_text())['product']
parents=json.loads((repo/'docs/atlas/regional-parent-product.json').read_text())['product']
k=lambda value:{'status':'known','value':value}
u=lambda reason:{'status':'unknown','reason':reason}
contributors=[{'kind':'product','id':p['id'],'revision':p['revision']} for p in [regional,parents,common]]
root='${MERIDIAN_DATA_ROOT}/'+tb.PRODUCT
footprint={'kind':'asset','asset':{'href':'docs/atlas/riffelhorn-final-reconciliation-experiment.json'},
 'crs':k({'identifier':'EPSG:2056','name':'CH1903+ / LV95'}),
 'interpretation':'Exact analytic radius, centre and support selection in frozen specification; not a rectangle expanded into valid source coverage.'}
rights={'licence':k('Combined underlying swisstopo open geodata terms and applicable Copernicus GLO-30 F modified-product licence obligations'),
 'references':sorted(set(regional['rights']['references']+common['rights']['references'])),
 'attribution':regional['rights']['attribution']+common['rights']['attribution'],
 'limitations':'Synthetic multi-source local evaluation. Retain all applicable full modified-product notices before any distribution/adoption. No production adoption.'}
product={'id':tb.VERSION,'name':'Riffelhorn protected-priority two-band synthetic visual transition',
 'version':k('v1-frozen-1500-3000-4000'),'revision':k(build['identity']),'producer':k('Meridian'),
 'surface':{'kind':'heterogeneous','description':'DTM-derived Swiss family, edited-DSM-derived common family, and explicitly synthetic signed two-band transition/parents.'},
 'vertical':{'kind':'heterogeneous','parts':[
   {'contributor':contributors[0],'reference':k({'identifier':'EPSG:5728','name':'LN02 height'})},
   {'contributor':contributors[1],'reference':k({'identifier':'EPSG:5728','name':'LN02 height'})},
   {'contributor':contributors[2],'reference':k({'identifier':'EPSG:3855','name':'EGM2008 height'})}],
   'description':'No height transformation or registration/bias correction. Mixed scalar has no common physical vertical CRS; synthetic visual representation only, never analytical elevation.'},
 'elevationUnit':k('metre'),
 'lineage':{'contributors':contributors,'contributorList':'complete','spatialMapping':'mask',
   'contributionMask':{'asset':{'href':root+'/contributions/{strategy}/{z}/{x}/{y}.npz'},'contributors':contributors,
     'interpretation':'broadWeight=b, detailWeight=d, categorical labels, changeProxy, changeClassificationKnown. b/d are geometric controls, not confidence/convex source percentages. Reconstruct with signed full operator and immutable broad/fine inputs. z10/11 mean influences require recursive parent operator.'},
   'processing':[{'method':'Frozen z12 broad controls, same recursive 2x2 uniform Mercator pixel-area means, strict complete cells, bilinear centre prolongation.',
      'record':{'href':'docs/atlas/riffelhorn-final-reconciliation-experiment.json','sha256':build['specSha256']},'software':build['software']},
     {'method':spec['formula'],'parameters':{'protectedRadiusM':1500,'broadEndpointM':4000,'detailTaperStartM':3000,'broadControlZoom':12}},
     {'method':spec['coarseParents'],'parameters':{'lowestDerivedZoom':10}},
     {'method':'Encode each level independently to nearest Terrarium step; no encoded RGB averaging or source modification.'}],
   'limitations':'Upstream per-cell epoch unknown. SGI historical union 250m is a retained change proxy, not an observed dated change. Pure products remain immutable; mixed outputs not observations.'},
 'delivery':{'kind':'raster-tiles','horizontalReference':k({'identifier':'EPSG:3857','name':'WGS 84 / Pseudo-Mercator'}),
    'scheme':'xyz','tileSize':[256,256],'encoding':{'name':'terrarium','description':'R*256+G+B/256-32768; quantisation preserves declared native or heterogeneous semantics','quantizationIncrement':{'value':1/256,'unit':'metre'}},
    'format':'lossless RGB PNG','tileTemplate':root+'/tiles/transition/{z}/{x}/{y}.png',
    'zoom':{'min':8,'max':k(18)},'availability':'Sparse deterministic evaluated inventory; finite common context. Common at8/9, derived parents10/11, frozen transition12-18. Not a national/global asset.',
    'resampling':k('Existing native delivery signal, z12 broad restriction/prolongation, explicit common z13 bilinear overzoom, unencoded transition parents. No new observations.')},
 'sourceInformation':{'description':'Swiss distributed0.5m grid is not independent measurement resolution. Copernicus one-arcsecond posts; z13delivery is interpolated signal. Broad z12~26.56m nearRiffelhorn is diagnostic representation scale.',
    'informationCeiling':k('Pure source ceilings inherited; signed composition adds synthetic representation, not measured information. Common above13 is overzoom; no universal source-information zoom.')},
 'spatial':{'coverage':k({'kind':'asset','asset':{'href':root+'/manifest.json'},'crs':k({'identifier':'EPSG:3857','name':'WGS 84 / Pseudo-Mercator'}),'interpretation':'Inventory tile footprints only; within these, classification/support and frozen radius determine source identity.'}),
    'validSupport':k({'area':footprint,'purpose':'Frozen diagnostic within radius4km plus finite common context','basis':'Complete full annulus/interpolation preflight at12-18; retained manifest support, no missing Swiss fill.'}),
    'protectedInterior':regional['spatial']['protectedInterior'],
    'transitionSupport':k({'area':footprint,'purpose':'Synthetic broad accommodation1500-4000m, independent regional residual taper3000-4000m','basis':'Engineering test support only. Does not establish physical seamline, stable corridor, accuracy or acceptable production transition.'})},
 'nodata':k('Incomplete Swiss or broad interpolation support is a failure; source-edge extrapolation/AWS padding forbidden. Outside4km exact common at12-18. Below10 handoff and finite perimeter remain explicit limitations.'),
 'rights':rights,'generation':{'timestamp':u('Sparse evaluated inventory generated over bounded sessions; immutable recipe and final inventory hashes identify it.'),'buildRecord':{'href':root+'/manifest.json'}},
 'documentation':['docs/atlas/protected-priority-two-band-transition.md','docs/atlas/riffelhorn-final-reconciliation-experiment.json']}
record={'schemaVersion':1,'product':product,'frozenSpecificationSha256':build['specSha256'],'sourceProductIdentities':spec['inputs'],'build':build,
 'terminalRule':'Proceed next to Terrain Hierarchy Contract with result/limitations explicit; no further Riffelhorn method experiment.'}
tb.sp.save(repo/'docs/atlas/two-band-product.json',record)
print('METADATA',build['identity'])
