"""Frozen, offline reference/overlap assessment; no DEM correction or app use.

Requires the retained Swiss VRT, acquisition record and cached AWS tiles.
The mask is independent of elevation differences. Translation fits are only
diagnostics: no estimated correction is applied to any terrain product.
"""
import hashlib
import io
import json
import zipfile
from pathlib import Path
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.merge import merge
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling, transform_geom
import shapefile
import pyproj
from pyproj import Transformer, datadir, network
from pyproj.transformer import TransformerGroup
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import riffelhorn_support as support
import riffelhorn_terrain as terrain
from riffelhorn_reconciliation import gaussian, stats
from check_riffelhorn_support import ReuseAws

REPO = Path(__file__).resolve().parents[2]
VERSION = 'global-reference-assessment-v1'
EXPERIMENT = 'experiments/atlas/' + VERSION
STEP = 25
SIZE = 400


def summary(values):
    values = np.asarray(values)
    values = values[np.isfinite(values)]
    return stats(values) if values.size else {'count': 0}


def sample_posts(values, transform, x, y):
    """GDAL transform describes outer pixel corners even for PixelIsPoint.

    Centre registration is therefore inverse-transform minus half a pixel.
    Caller must provide a mosaic to interpolate across original tile edges.
    """
    px, py = (~transform) * (x, y)
    px, py = np.asarray(px) - .5, np.asarray(py) - .5
    ix, iy = np.floor(px).astype(int), np.floor(py).astype(int)
    if np.any(ix < 0) or np.any(iy < 0) or np.any(ix + 1 >= values.shape[1]) or np.any(iy + 1 >= values.shape[0]):
        raise ValueError('Bilinear sample lacks full source support')
    fx, fy = px - ix, py - iy
    return ((1-fx)*values[iy, ix] + fx*values[iy, ix+1])*(1-fy) + ((1-fx)*values[iy+1, ix] + fx*values[iy+1, ix+1])*fy


def buffer_mask(mask, radius, step=STEP):
    """Euclidean cell-centre buffer of an already all-touched footprint."""
    r = int(np.ceil(radius / step))
    padded = np.pad(mask, r)
    result = np.zeros_like(mask, dtype=bool)
    for dy in range(-r, r+1):
        for dx in range(-r, r+1):
            if dx*dx + dy*dy <= (radius/step)**2:
                result |= padded[r+dy:r+dy+mask.shape[0], r+dx:r+dx+mask.shape[1]]
    return result


def stable_mask(valid, bare, ice, edge_distance, slope, limits=(5, 40)):
    """Independent physical-support screen; deliberately no difference input."""
    return valid & bare & ~ice & (edge_distance >= 200) & (slope >= limits[0]) & (slope <= limits[1])


def conservative_cover(classes, source_transform, source_crs, destination_transform, shape):
    """Any non-bare input excludes the destination cell; missing support too.

    Explicit 255 nodata is distinct from BOTH valid binary classes. GDAL may
    otherwise infer a nodata value from the destination and skip exclusions.
    """
    result = np.full(shape, 255, dtype='uint8')
    reproject((classes != 60).astype('uint8'), result, src_transform=source_transform,
              src_crs=source_crs, src_nodata=255, dst_transform=destination_transform,
              dst_crs=2056, dst_nodata=255, resampling=Resampling.max)
    return result == 0


def fit_translation(difference, east_gradient, north_gradient, mask):
    """Huber robust first-order translation signature, not co-registration.

    Swiss-global = dx*dSwiss/dEast + dy*dSwiss/dNorth + intercept.
    dx/dy describe which higher-quality terrain coordinates a displaced global
    sample resembles; they are NOT an instruction to move either product.
    """
    y = difference[mask]
    x = np.column_stack((east_gradient[mask], north_gradient[mask], np.ones(y.size)))
    if len(y) < 100 or np.linalg.matrix_rank(x) < 3:
        return {'status': 'insufficient support'}
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    for _ in range(50):
        residual = y - x @ beta
        scale = max(.1, 1.4826*np.median(np.abs(residual-np.median(residual))))
        weights = np.minimum(1, 1.345*scale / np.maximum(np.abs(residual), 1e-9))
        root = np.sqrt(weights)
        update = np.linalg.lstsq(x*root[:, None], y*root, rcond=None)[0]
        if np.max(np.abs(update-beta)) < 1e-7:
            beta = update
            break
        beta = update
    return {'status': 'diagnostic only', 'eastSignatureMetres': float(beta[0]),
            'northSignatureMetres': float(beta[1]), 'interceptMetres': float(beta[2]),
            'residual': summary(y-x@beta), 'downweightedFraction': float(np.mean(weights < .999)),
            'designCondition': float(np.linalg.cond(x)), 'coefficients': beta.tolist()}


def glacier_footprints(data, assets, transform):
    # Include a 500 m guard: nearby glaciers outside the selection still buffer
    # into it. This is support classification, not acquisition of more terrain.
    guard = 20
    padded_transform = transform * rasterio.Affine.translation(-guard, -guard)
    shape = (SIZE+2*guard, SIZE+2*guard)
    union = np.zeros(shape, dtype=bool)
    records = {}
    for year in [1973, 2016, 2023]:
        key = 'sgi'+str(year)
        with zipfile.ZipFile(data/assets[key]['path']) as archive:
            prefix = f'SGI_{year}' + ('' if year == 1973 else '_glaciers')
            prj = archive.read(prefix+'.prj').decode('utf8')
            reader = shapefile.Reader(shp=io.BytesIO(archive.read(prefix+'.shp')))
            geometries = []
            for feature in reader.iterShapes():
                geometry = transform_geom(prj, 'EPSG:2056', feature.__geo_interface__)
                # All inventories use LV95; verify via transformed bbox below.
                xs, ys = np.asarray(feature.bbox)[[0, 2]], np.asarray(feature.bbox)[[1, 3]]
                if xs.max() < 2619500 or xs.min() > 2630500 or ys.max() < 1086500 or ys.min() > 1097500:
                    continue
                geometries.append(geometry)
            a = rasterize(((g, 1) for g in geometries), out_shape=shape, transform=padded_transform, all_touched=True, dtype='uint8').astype(bool)
            union |= a
            records[key] = {'layer': prefix+'.shp', 'sourceCrs': prj, 'intersectingFootprints': len(geometries), 'aoiCells': int(a[guard:-guard, guard:-guard].sum())}
    masks = {r: buffer_mask(union, r)[guard:-guard, guard:-guard] for r in [100, 250, 500]}
    return masks, records


def run(data):
    acquisition = json.loads((REPO/'docs/atlas/global-reference-acquisition.json').read_text(encoding='utf8'))
    protocol = json.loads((REPO/'docs/atlas/global-reference-protocol.json').read_text(encoding='utf8'))
    if terrain.stable_id({k: v for k, v in acquisition.items() if k != 'identity'}) != acquisition['identity']:
        raise ValueError('Acquisition identity mismatch')
    if acquisition['protocolSha256'] != terrain.digest(REPO/'docs/atlas/global-reference-protocol.json'):
        raise ValueError('Protocol changed after acquisition')
    assets = acquisition['assets']
    for key, asset in assets.items():
        if terrain.digest(data/asset['path']) != asset['sha256']:
            raise ValueError('Frozen asset changed: '+key)
    swiss_record = json.loads((REPO/'docs/atlas/riffelhorn-support-product.json').read_text(encoding='utf8'))
    for asset in swiss_record['source']['assets']:
        path = data/asset['href'].removeprefix('${MERIDIAN_DATA_ROOT}/')
        if terrain.digest(path) != asset['sha256']:
            raise ValueError('Swiss input changed: '+str(path))
    if terrain.digest(data/support.PRODUCT/'source-mosaic.vrt') != swiss_record['preparationSummary']['sourceMosaicSha256']:
        raise ValueError('Swiss source VRT changed')
    output = data/EXPERIMENT
    output.mkdir(parents=True, exist_ok=True)
    grid_transform = from_bounds(*support.BOUNDS, SIZE, SIZE)
    east, north = np.meshgrid(support.BOUNDS[0]+(np.arange(SIZE)+.5)*STEP, support.BOUNDS[3]-(np.arange(SIZE)+.5)*STEP)
    with rasterio.open(data/support.PRODUCT/'source-mosaic.vrt') as ds:
        if ds.shape != (20000, 20000) or str(ds.crs) != 'EPSG:2056':
            raise ValueError('Unexpected retained Swiss source grid')
        swiss = ds.read(1, out_shape=(SIZE, SIZE), resampling=Resampling.average).astype(float)
    if not np.all(np.isfinite(swiss)) or np.any(swiss == -9999):
        raise ValueError('Invalid Swiss common support')
    print('SWISS averaged to 25 m', flush=True)
    network.set_network_enabled(False)
    for key in ['ln02-grid', 'egm2008-grid']:
        datadir.append_data_dir(str((data/assets[key]['path']).parent))
    operations = TransformerGroup('EPSG:2056+5728', 'EPSG:4326+3855', always_xy=True, allow_ballpark=False)
    if len(operations.transformers) != 1:
        raise ValueError('Expected exactly one local, non-ballpark height route')
    height_operation = operations.transformers[0]
    lon, lat, swiss_egm = height_operation.transform(east, north, swiss, errcheck=True)
    inverse = Transformer.from_pipeline(height_operation.definition)
    re, rn, rh = inverse.transform(lon, lat, swiss_egm, direction='INVERSE', errcheck=True)
    horizontal = Transformer.from_crs(2056, 4326, always_xy=True, allow_ballpark=False)
    lon2, lat2 = horizontal.transform(east, north)
    horizontal_delta = np.hypot((lon-lon2)*111000*np.cos(np.deg2rad(lat)), (lat-lat2)*111000)
    with rasterio.open(data/assets['cop45']['path']) as a, rasterio.open(data/assets['cop46']['path']) as b:
        mosaic, post_transform = merge([a, b])
        cop = sample_posts(mosaic[0], post_transform, lon, lat)
        coarse_checks = []
        for ds in [a, b]:
            full = ds.read(1).astype(float)
            for factor in ds.overviews(1):
                average = full.reshape(full.shape[0]//factor, factor, full.shape[1]//factor, factor).mean(axis=(1, 3))
                overview = ds.read(1, out_shape=average.shape, resampling=Resampling.nearest)
                coarse_checks.append({'asset': ds.name.split('/')[-1], 'factor': factor, 'overviewMinusDirectMean': summary(overview-average)})
    aws_cache = ReuseAws(data)
    # Enforce offline cache reuse, including the older prototype cache.
    original_tile = aws_cache.tile
    def frozen(z, x, y):
        leaf = f'{z}/{x%(2**z)}/{y}.png'
        if not (aws_cache.root/leaf).exists() and not (aws_cache.old.root/leaf).exists():
            raise FileNotFoundError('Missing offline AWS tile: '+leaf)
        return original_tile(z, x, y)
    aws_cache.tile = frozen
    mercator = Transformer.from_crs(2056, 3857, always_xy=True, allow_ballpark=False)
    aws = np.empty_like(swiss)
    for row in range(0, SIZE, 40):
        me, mn = mercator.transform(east[row:row+40], north[row:row+40])
        aws[row:row+40] = aws_cache.at_mercator(me, mn)
    print('Global sources sampled without changing products', flush=True)
    cover_classes = np.zeros((SIZE, SIZE), dtype='uint8')
    with rasterio.open(data/assets['worldcover']['path']) as ds:
        classes = ds.read(1)
        bare = conservative_cover(classes, ds.transform, ds.crs, grid_transform, (SIZE, SIZE))
        reproject(classes, cover_classes, src_transform=ds.transform, src_crs=ds.crs, dst_transform=grid_transform, dst_crs=2056, resampling=Resampling.nearest)
    ice, glacier_records = glacier_footprints(data, assets, grid_transform)
    geometry = gaussian(swiss, 30, step=STEP)
    gradient_n, gradient_e = np.gradient(geometry, STEP)
    gradient_n = -gradient_n
    slope = np.rad2deg(np.arctan(np.hypot(gradient_e, gradient_n)))
    aspect = np.mod(np.rad2deg(np.arctan2(gradient_e, gradient_n)), 360)
    edge_distance = np.minimum.reduce([east-support.BOUNDS[0], support.BOUNDS[2]-east, north-support.BOUNDS[1], support.BOUNDS[3]-north])
    valid = np.isfinite(swiss) & np.isfinite(cop) & np.isfinite(aws)
    primary = stable_mask(valid, bare, ice[250], edge_distance, slope)
    fields = {'awsRaw': swiss-aws, 'copernicusRaw': swiss-cop, 'copernicusCommonHeight': swiss_egm-cop}
    masks = {'primary': primary}
    for radius in [100, 500]:
        masks[f'iceBuffer{radius}'] = stable_mask(valid, bare, ice[radius], edge_distance, slope)
    for low, high in [(3, 45), (10, 35)]:
        masks[f'slope{low}to{high}'] = stable_mask(valid, bare, ice[250], edge_distance, slope, (low, high))
    quadrants = {'NW': (east < 2625000) & (north >= 1092000), 'NE': (east >= 2625000) & (north >= 1092000), 'SW': (east < 2625000) & (north < 1092000), 'SE': (east >= 2625000) & (north < 1092000)}
    checker = ((np.floor((east-2620000)/1000)+np.floor((north-1087000)/1000)) % 2) == 0
    report = {'version': VERSION, 'inputs': acquisition['identity'], 'swissIdentity': swiss_record['product']['revision']['value'],
              'protocol': protocol, 'software': {'numpy': np.__version__, 'rasterio': rasterio.__version__, 'gdal': rasterio.__gdal_version__, 'pyproj': pyproj.__version__, 'proj': pyproj.proj_version_str, 'pyshp': shapefile.__version__},
              'grid': {'crs': 'EPSG:2056', 'bounds': support.BOUNDS, 'spacing': STEP, 'shape': [SIZE, SIZE]},
              'heightDiagnostic': {'description': height_operation.description, 'pipeline': height_operation.definition,
                  'declaredCombinedAccuracyMetres': height_operation.accuracy,
                  'limitations': 'PROJ reports combined accuracy unknown (-1); no centimetre claim. Frame/epoch and 2.5 arcminute geoid interpolation limitations remain. Diagnostic only; AWS height reference unknown.',
                  'deltaEgm2008MinusLn02': summary(swiss_egm-swiss),
                  'roundtripHorizontalMetres': summary(np.hypot(re-east, rn-north)), 'roundtripHeightMetres': summary(rh-swiss),
                  'compoundVersus2dHorizontalMetres': summary(horizontal_delta)},
              'mask': {'glacierInputs': glacier_records, 'allCells': SIZE*SIZE, 'validCells': int(valid.sum()),
                  'conservativeBareCells': int(bare.sum()), 'glacier250Cells': int(ice[250].sum()),
                  'sourceEdgeExcludedCells': int((edge_distance < 200).sum()), 'slopeExcludedCells': int(((slope < 5) | (slope > 40)).sum()),
                  'primaryCells': int(primary.sum()), 'primaryKm2': float(primary.sum()*STEP*STEP/1e6),
                  'quadrantCells': {key: int((primary & q).sum()) for key, q in quadrants.items()},
                  'protectedInteriorCells': int((primary & (np.hypot(east-2625000, north-1092000) <= 1500)).sum()),
                  'nearestCoverClassCounts': {str(c): int((cover_classes == c).sum()) for c in np.unique(cover_classes)},
                  'limitations': 'Stable-terrain candidates, not verified invariant ground. Historic glacier union is conservative; snow, rockfall, land-cover errors, DSM/DTM support and epoch uncertainty remain.'},
              'comparisons': {}, 'coarseOverviewChecks': coarse_checks, 'awsInputs': aws_cache.records}
    for name, difference in fields.items():
        fit = fit_translation(difference, gradient_e, gradient_n, primary)
        item = {'allValid': summary(difference[valid]), 'primary': summary(difference[primary]),
                'glacierExcluded': summary(difference[valid & ice[250]]),
                'otherLandCoverExcluded': summary(difference[valid & ~bare]),
                'protectedInteriorPrimary': summary(difference[primary & (np.hypot(east-2625000, north-1092000) <= 1500)]),
                'largestPrimaryAbsoluteDifferences': [],
                'maskSensitivities': {key: summary(difference[m]) for key, m in masks.items()},
                'quadrants': {key: summary(difference[primary & q]) for key, q in quadrants.items()},
                'translationSignature': fit,
                'sectorSignatures': {key: fit_translation(difference, gradient_e, gradient_n, primary & q) for key, q in quadrants.items()},
                'spatialHoldout': {}, 'bins': {}, 'spatialCorrelation': {}}
        for flat in np.argsort(np.where(primary, np.abs(difference), -1).ravel())[-5:][::-1]:
            row, col = np.unravel_index(flat, difference.shape)
            item['largestPrimaryAbsoluteDifferences'].append({'east': float(east[row, col]), 'north': float(north[row, col]), 'swissLn02': float(swiss[row, col]), 'difference': float(difference[row, col]), 'slopeDegrees': float(slope[row, col])})
        for label, train in [('even', checker), ('odd', ~checker)]:
            fitted = fit_translation(difference, gradient_e, gradient_n, primary & train)
            item['spatialHoldout'][label] = fitted
            if 'coefficients' in fitted:
                dx, dy, dz = fitted['coefficients']
                held = primary & ~train
                item['spatialHoldout'][label]['heldOutResidual'] = summary((difference-dx*gradient_e-dy*gradient_n-dz)[held])
                item['spatialHoldout'][label]['heldOutRaw'] = summary(difference[held])
        roughness = np.abs(swiss-gaussian(swiss, 75, step=STEP))
        for label, field, cuts in [('slope', slope, [5, 10, 20, 30, 40.001]), ('aspect', aspect, list(range(0, 361, 45))), ('height', swiss, [1500, 2500, 3000, 3500, 4500]), ('roughness', roughness, [0, 2, 5, 10, 25, 1000])]:
            item['bins'][label] = [{'range': [lo, hi], 'difference': summary(difference[primary & (field >= lo) & (field < hi)])} for lo, hi in zip(cuts[:-1], cuts[1:])]
        for metres in [100, 250, 500, 1000, 2000]:
            lag = metres//STEP
            pairs = primary[:, :-lag] & primary[:, lag:]
            a, b = difference[:, :-lag][pairs], difference[:, lag:][pairs]
            vertical_pairs = primary[:-lag] & primary[lag:]
            c, d = difference[:-lag][vertical_pairs], difference[lag:][vertical_pairs]
            item['spatialCorrelation'][str(metres)] = {'eastWestPairs': int(a.size), 'eastWest': float(np.corrcoef(a, b)[0, 1]) if a.size > 20 else None, 'northSouthPairs': int(c.size), 'northSouth': float(np.corrcoef(c, d)[0, 1]) if c.size > 20 else None}
        report['comparisons'][name] = item
    arrays = {'swissLn02': swiss, 'swissEgm2008Diagnostic': swiss_egm, 'copernicus': cop, 'aws': aws,
              'slope': slope, 'bareMask': bare, 'glacier250Mask': ice[250], 'edgeMask': edge_distance >= 200,
              'primaryMask': primary, 'coverNearest': cover_classes, **fields, **masks}
    report['arrayHashes'] = {key: hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest() for key, value in sorted(arrays.items())}
    report['toolSha256'] = terrain.repository_text_digest(Path(__file__))
    report['identity'] = terrain.stable_id({'inputs': report['inputs'], 'swiss': report['swissIdentity'], 'tool': report['toolSha256'], 'arrays': report['arrayHashes'], 'pipeline': height_operation.definition})
    np.savez_compressed(output/'fields-and-mask.npz', **arrays)
    support.save(output/'assessment.json', report)
    compact = {k: v for k, v in report.items() if k not in ['awsInputs', 'protocol']}
    compact['awsTileCount'] = len(aws_cache.records)
    compact['fullReportSha256'] = terrain.digest(output/'assessment.json')
    support.save(REPO/'docs/atlas/global-reference-measurements.json', compact)
    fig, axes = plt.subplots(2, 2, figsize=(12, 10), layout='constrained')
    for ax, values, title, cmap, limits in [(axes[0, 0], primary.astype(int), 'Independent stable-terrain candidates', 'Greens', (0, 1)), (axes[0, 1], fields['awsRaw'], 'Swiss LN02 minus AWS (m; datum unknown)', 'RdBu_r', (-120, 120)), (axes[1, 0], fields['copernicusCommonHeight'], 'Swiss EGM2008 diagnostic minus GLO-30 (m)', 'RdBu_r', (-120, 120)), (axes[1, 1], np.where(primary, fields['copernicusCommonHeight'], np.nan), 'Same difference on candidate support', 'RdBu_r', (-50, 50))]:
        im = ax.imshow(values, extent=(0, 10, 0, 10), cmap=cmap, vmin=limits[0], vmax=limits[1])
        ax.set_title(title); ax.set_xlabel('km east from LV95 2620000'); ax.set_ylabel('km north from LV95 1087000')
        fig.colorbar(im, ax=ax, shrink=.75)
        ax.add_patch(plt.Circle((5, 5), 1.5, fill=False, color='black'))
    fig.savefig(output/'reference-fields.png', dpi=140); plt.close(fig)
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), layout='constrained')
    for axis, index, direction in [(axes[0], 200, 'east'), (axes[1], 200, 'north')]:
        for name, a in [('Swiss LN02', swiss), ('Swiss EGM2008 diagnostic', swiss_egm), ('GLO-30 EGM2008', cop), ('AWS unknown reference', aws)]:
            axis.plot((np.arange(SIZE)+.5)*STEP, a[index] if direction == 'east' else a[::-1, index], label=name)
        axis.set_title('Central '+direction+' profile (nearest 25 m centres; not a stable-ground-only transect)')
        axis.set_ylabel('height m'); axis.set_xlabel('distance m'); axis.legend(); axis.grid(alpha=.2)
    fig.savefig(output/'reference-profiles.png', dpi=140); plt.close(fig)
    print('ASSESSMENT', report['identity'], 'support', report['mask']['primaryKm2'], 'km2', flush=True)
    for name, item in report['comparisons'].items():
        print(name, json.dumps({'primary': item['primary'], 'fit': item['translationSignature']}), flush=True)


if __name__ == '__main__':
    run(terrain.resolve_storage_roots(require_data=True).data)
