"""Owned evidence records using the existing Atlas model; no app imports."""
import json
from pathlib import Path
import riffelhorn_terrain as terrain
import riffelhorn_support as support

REPO = Path(__file__).resolve().parents[2]


def run(data):
    acquisition = json.loads((REPO/'docs/atlas/global-reference-acquisition.json').read_text(encoding='utf8'))
    assessment = json.loads((REPO/'docs/atlas/global-reference-measurements.json').read_text(encoding='utf8'))
    swiss = json.loads((REPO/'docs/atlas/riffelhorn-support-product.json').read_text(encoding='utf8'))
    known = lambda value: {'status': 'known', 'value': value}
    unknown = lambda reason: {'status': 'unknown', 'reason': reason}
    egm = {'name': 'EGM2008 height', 'identifier': 'EPSG:3855'}
    wgs = {'name': 'WGS 84; documentation states G1150, TIFF identifies generic EPSG:4326', 'identifier': 'EPSG:4326'}
    lv95 = {'name': 'CH1903+ / LV95', 'identifier': 'EPSG:2056'}
    docs = ['docs/atlas/global-reference-assessment.md', 'docs/atlas/global-reference-acquisition.json', 'docs/atlas/global-reference-measurements.json']
    licence = 'https://s3.waw3-1.cloudferro.com/swift/v1/portal_uploads_prod/CSCDA_ESA_Mission-specific_Annex_31_Oct_22_latest.pdf'
    rights = {'licence': known('Copernicus DEM GLO-30 F free/open licence, Annex pp.20-22'), 'references': [licence], 'attribution': ['Use the applicable full unmodified/modified notice and Article 6 obligations in the licence; this summary is not the legal delivery notice.'], 'limitations': 'Derivative hosting permitted subject to attribution, liability, non-endorsement and downstream obligations. Do not substitute restricted GLO-30 R terms or the mirror software licence.'}
    assets = [{'href': '${MERIDIAN_DATA_ROOT}/'+acquisition['assets'][k]['path'], 'sha256': acquisition['assets'][k]['sha256']} for k in ['cop45', 'cop46']]
    source = {
        'id': 'copernicus-glo30-riffelhorn-2021-input-selection', 'name': 'Copernicus GLO-30: retained Riffelhorn inputs from public 2021 COG distribution',
        'authority': known('European Union Copernicus / ESA; WorldDEM basis produced by Airbus with DLR TanDEM-X observations'),
        'dataset': 'Copernicus DEM GLO-30', 'release': known('Public mirror documents 2021 release; exact 2021 sub-release not established'),
        'revision': known(terrain.stable_id(assets)),
        'surface': {'kind': 'dsm', 'description': 'Edited surface model including vegetation/buildings; water/hydrological editing and heterogeneous void filling. Not a bare-earth DTM.'},
        'horizontalReference': known(wgs), 'verticalReference': known(egm), 'elevationUnit': known('metre'),
        'resolution': {'gridSpacing': {'x': 1, 'y': 1, 'unit': 'arcsecond', 'crs': wgs}, 'nominalResolution': known('Retained latitude-band posting is one arcsecond; longitude posting varies with latitude globally.'), 'measurementResolution': unknown('Delivery posting is not independent measurement resolution; radar support, editing and filling vary.'), 'limitations': 'Approximately 21.5 m east-west and 30.9 m north-south here; no metre-scale detail. Exact per-post acquisition and contributing infill are not supplied by the two retained COGs.'},
        'acquisition': known({'description': 'Principal TanDEM-X observations December 2010–January 2015; fill data may have other epochs, no per-post epoch retained.', 'start': '2010-12', 'end': '2015-01'}),
        'coverage': {'scope': 'retained-input-selection', 'area': known({'kind': 'native-rectangle', 'crs': wgs, 'axisOrder': 'xy', 'bounds': [6.9998611111111115, 45.00013888888889, 7.9998611111111115, 47.00013888888889]})},
        'nodata': known('Retained float32 COGs declare no nodata; 10 km comparison fully finite. Public missing tiles can indicate ocean or absent/restricted land, not automatically zero land.'),
        'quality': known('Published global specifications: absolute vertical <4 m LE90, horizontal <6 m CE90; terrain/ice limitations and local residuals matter. Not a local accuracy certificate.'),
        'rights': rights, 'documentation': docs + ['https://registry.opendata.aws/copernicus-dem/', 'https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM'], 'assets': assets,
    }
    contributor = {'kind': 'source', 'id': source['id'], 'revision': source['revision']}
    product = {
        'id': 'copernicus-glo30-public-cog-riffelhorn-selection', 'name': 'Retained Sinergise public COG delivery selection',
        'version': source['release'], 'revision': source['revision'], 'producer': known('Sinergise public Copernicus COG distribution'), 'surface': source['surface'],
        'vertical': {'kind': 'preserved', 'from': contributor, 'reference': known(egm)}, 'elevationUnit': known('metre'),
        'lineage': {'contributors': [contributor], 'contributorList': 'complete', 'spatialMapping': 'uniform',
            'processing': [{'method': 'Remove duplicated east column/south row; lossless float32 COG compression; average overviews. Base elevation posts not resampled by the documented distribution conversion.', 'record': {'href': 'https://copernicus-dem-30m.s3.amazonaws.com/readme.html'}}],
            'limitations': 'Complete immediate published-product contributor, not complete upstream observation/infill provenance. No EDM/FLM/HEM/WBM retained. Public mirror older/restricted compared with latest CDSE release.'},
        'delivery': {'kind': 'raster-file', 'horizontalReference': known(wgs), 'format': 'Float32 Cloud Optimized GeoTIFF; PixelIsPoint, 3600x3600 retained files', 'assets': assets},
        'sourceInformation': {'description': source['resolution']['limitations'], 'informationCeiling': unknown('No delivery zoom applies to this file product; global information support varies.')},
        'spatial': {'coverage': source['coverage']['area'], 'validSupport': unknown('Initial stable-overlap evidence is local; no accepted global Atlas support footprint.'), 'transitionSupport': unknown('No reconciliation performed or transition accepted.')},
        'nodata': source['nodata'], 'rights': rights,
        'generation': {'timestamp': unknown('Upstream generation timestamp not established; asset Last-Modified and acquisition separately retained.'), 'buildRecord': {'href': docs[1]}}, 'documentation': docs,
    }
    mask_asset = {'href': '${MERIDIAN_DATA_ROOT}/experiments/atlas/global-reference-assessment-v1/fields-and-mask.npz', 'sha256': terrain.digest(data/'experiments/atlas/global-reference-assessment-v1/fields-and-mask.npz')}
    swiss_contributor = {'kind': 'product', 'id': swiss['product']['id'], 'revision': swiss['product']['revision']}
    transformation = {'from': {'name': 'LN02 height', 'identifier': 'EPSG:5728'}, 'to': egm,
        'method': assessment['heightDiagnostic']['pipeline'], 'accuracy': unknown('PROJ combined accuracy -1; roundtrip closure is not geodetic accuracy.'), 'limitations': assessment['heightDiagnostic']['limitations']}
    diagnostic = {
        'id': 'riffelhorn-swiss-egm2008-diagnostic', 'name': 'Swiss common-grid height diagnostic, not a deliverable DEM',
        'version': known('global-reference-assessment-v1'), 'revision': known(assessment['identity']), 'producer': known('Meridian offline evaluation'),
        'surface': swiss['source']['surface'], 'vertical': {'kind': 'transformed', 'transformation': transformation}, 'elevationUnit': known('metre'),
        'lineage': {'contributors': [swiss_contributor], 'contributorList': 'complete', 'spatialMapping': 'uniform',
            'processing': [{'method': 'Area-average official LV95 source grid to 25 m diagnostic support; retained product source-mosaic.vrt used, no terrain tile resampling.'}, {'method': 'Defined local-grid height diagnostic, never applied to Swiss source/delivery or AWS.', 'verticalTransformation': transformation, 'record': {'href': docs[2], 'selector': 'heightDiagnostic'}}],
            'limitations': 'Diagnostic only. Original Swiss source and visual product continue to preserve LN02. NPZ also holds other separately identified comparison arrays.'},
        'delivery': {'kind': 'other', 'description': 'NPZ array swissEgm2008Diagnostic, EPSG:2056 grid; not Atlas terrain delivery', 'assets': [{**mask_asset, 'selector': 'swissEgm2008Diagnostic'}]},
        'sourceInformation': {'description': '25 m area averaging for comparison, not the distributed Swiss grid or native resolution.', 'informationCeiling': known('Coarse diagnostic support; regional 0.5 m source information not represented by this averaged array.')},
        'spatial': {'coverage': known({'kind': 'native-rectangle', 'crs': lv95, 'axisOrder': 'xy', 'bounds': [2620000,1087000,2630000,1097000]}), 'validSupport': known({'area': {'kind': 'asset', 'asset': {**mask_asset, 'selector': 'primaryMask'}, 'crs': known(lv95), 'interpretation': 'Independent diagnostic stable-terrain candidates, not proven invariant ground or production support.'}, 'purpose': 'Global-reference comparison', 'basis': 'WorldCover v200, GLAMOS glacier inventory union, source-edge/slope screening; protocol and sensitivity results retained.'}), 'transitionSupport': unknown('Comparison support does not establish integration support.')},
        'nodata': known('Source full-grid finite; support selection stored as a separate boolean mask, not hidden as missing elevations.'), 'rights': swiss['source']['rights'],
        'generation': {'timestamp': unknown('Scientific identity frozen by inputs, tool, arrays and operation; wall-clock timestamp not used as revision.'), 'buildRecord': {'href': docs[2]}}, 'documentation': docs,
    }
    support.save(REPO/'docs/atlas/global-reference-metadata.json', {'schemaVersion': 1, 'source': source, 'product': product, 'heightDiagnostic': diagnostic, 'productionAwsRecord': 'src/atlas/terrain/metadata/terrainMetadataExamples.ts#AWS_VISUAL_PRODUCT', 'roleDecision': 'Copernicus GLO-30 recommended as candidate common/coarse reference; production visual and analytical policies unchanged. Reference role distinct from best available visual representation.'})


if __name__ == '__main__':
    run(terrain.resolve_storage_roots(require_data=True).data)
