"""Final bounded cliff estimator/support experiment; no production representation."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from PIL import Image, ImageDraw
import riffelhorn_012d as previous
from riffelhorn_012d import retention, digest, ORIGIN, BOUNDS

PARAMETERS = {
    'output_spacing_m': .125, 'normal_radii_m': [1., 2.], 'minimum_points': 10,
    'minimum_planarity': .3, 'maximum_rms_m': [.1, .15], 'maximum_split_angle_deg': 10.,
    'trim_iterations': 2, 'trim_floor_m': .15, 'trim_mad_multiplier': 3.,
    'plane_anchor_voxel_m': .5, 'minimum_abs_normal_z': .1,
    'plane_prediction_extension_m': .2, 'minimum_plane_anchors': 3,
    'minimum_consensus_weight_fraction': .8, 'maximum_normal_angle_deg': 20.,
    'consensus_perpendicular_tolerance_m': .3, 'huber_delta_perpendicular_m': .1,
    'minimum_consistent_returns': 10, 'support_radius_m': 2.,
    'strong_nearest_return_m': .5, 'strong_xy_hull_margin_m': .2,
    'maximum_edge_plane_departure_m': .3,
    'nominal_source_sigma_xy_m': .2, 'nominal_source_sigma_z_m': .1,
    'source_gap_xy_radius_m': 1., 'source_gap_minimum_z_gap_m': 2.,
    'attribution': '\u00a9 swisstopo',
}
# Diagnostic columns: explicit units; statuses do not imply calibrated probability.
DIAGNOSTIC_COLUMNS = ['support_code', 'reason_code', 'nearby_reliable_planes', 'consensus_planes',
                      'consistent_construction_returns', 'nearest_construction_xyz_m', 'xy_hull_margin_m',
                      'consensus_weight_fraction', 'plane_prediction_rms_perpendicular_m',
                      'normal_inclination_deg', 'height_sigma_nominal_propagation_m', 'flight_count',
                      'proposed_height_ln02_m', 'consensus_normal_e', 'consensus_normal_n', 'consensus_normal_up']
# Support: 0 absent, 1 supported, 2 interpolated, 3 weak (no emitted height).
# Reasons: 0 accepted, 1 no reliable plane, 2 ill-conditioned, 3 no local continuation,
# 4 conflicting heights/orientations, 5 too few distinct plane anchors,
# 6 too few nearby consistent returns, 7 not bracketed in XY.


def robust_plane(points, radius):
    """Trim gross plane departures, then test conditioning and split repeatability."""
    p = np.asarray(points)
    if len(p) < PARAMETERS['minimum_points']:
        return None
    kept = np.ones(len(p), bool)
    for _ in range(PARAMETERS['trim_iterations']):
        normal, _, _ = retention.fit_plane(p[kept])
        signed = (p-p[kept].mean(0)) @ normal
        mad = 1.4826*np.median(abs(signed[kept]-np.median(signed[kept])))
        kept = abs(signed) <= max(PARAMETERS['trim_floor_m'], 3*mad)
        if kept.sum() < PARAMETERS['minimum_points']:
            return None
    sample = p[kept]
    normal, rms, planarity = retention.fit_plane(sample)
    n1, _, _ = retention.fit_plane(sample[::2])
    n2, _, _ = retention.fit_plane(sample[1::2])
    angle = np.degrees(np.arccos(np.clip(abs(n1 @ n2), 0, 1)))
    limit = PARAMETERS['maximum_rms_m'][0 if radius == 1 else 1]
    if rms > limit or planarity < .3 or angle > 10:
        return None
    centre = sample.mean(0)
    return centre, normal, rms, planarity, int(kept.sum()), angle, kept


def derive_planes(points, records, source_indices):
    """Both frozen scales; choose smallest reliable scale per measured anchor."""
    index = previous.Bins(points, 1.)
    rows = []; evidence = np.full((len(points), 2, 9), np.nan)
    for i, q in enumerate(points):
        chosen = None
        for k, radius in enumerate((1., 2.)):
            ids = index.neighbours(q, radius)
            fit = robust_plane(points[ids], radius)
            if fit is None:
                evidence[i, k, 0] = len(ids)
                continue
            centre, normal, rms, planarity, count, angle, kept = fit
            offset = abs((q-centre) @ normal)
            evidence[i, k] = [count, rms, planarity, angle, offset, *normal, radius]
            if offset > .2:
                continue  # isolated anchor is not legitimated by neighbouring plane
            flights = len(np.unique(records['point_source_id'][ids[kept]]))
            row = [*centre, *normal, rms, planarity, count, angle, radius, flights, int(source_indices[i]), *q]
            if chosen is None:
                chosen = row
        if chosen is not None:
            rows.append(chosen)
    # Shared overlapping planes are correlated; cap one anchor per measured 0.5m XYZ voxel.
    selected = {}
    for row in rows:
        key = tuple(np.floor((np.array(row[13:16])-np.r_[ORIGIN, 2800])/.5).astype(int))
        score = (row[10], row[6], -row[7], -row[8], row[12])
        if key not in selected or score < selected[key][0]:
            selected[key] = (score, row)
    return np.array([selected[k][1] for k in sorted(selected)]), evidence


def hull_margin(xy, query):
    polygon = retention.hull(xy-query)
    if len(polygon) < 3:
        return -np.inf
    edges = np.roll(polygon, -1, axis=0)-polygon
    cross = edges[:, 0]*(-polygon[:, 1])-edges[:, 1]*(-polygon[:, 0])
    return float((cross/np.maximum(np.linalg.norm(edges, axis=1), 1e-12)).min())


def weighted_median(values, weights):
    order = np.argsort(values, kind='stable')
    return values[order[np.searchsorted(np.cumsum(weights[order]), weights.sum()/2)]]


def mean_plane_normal(normals, weights, reference):
    # Plane orientation is unsigned: align signs before averaging, including
    # near-vertical estimates whose tiny upward components may change sign.
    aligned = normals*np.where(normals @ reference < 0, -1., 1.)[:, None]
    normal = np.sum(weights[:, None]*aligned, axis=0)
    normal /= np.linalg.norm(normal)
    return normal if normal[2] >= 0 else -normal


class PlaneEstimator:
    """One robust plane-vote scalar height fit, with separate observation support."""
    def __init__(self, planes, points, records):
        self.planes = planes
        self.points = points
        self.records = records
        self.plane_index = previous.Bins(planes[:, :2]-ORIGIN, 1.)
        self.point_index = previous.Bins(points, 1.)

    def query(self, xy):
        diagnostic = np.full(len(DIAGNOSTIC_COLUMNS), np.nan)
        diagnostic[:5] = [0, 1, 0, 0, 0]
        ids = self.plane_index.neighbours(xy-ORIGIN, 2.2)
        if not len(ids):
            return np.nan, diagnostic
        p = self.planes[ids]
        diagnostic[2] = len(p)
        condition = abs(p[:, 5]) >= .1
        if not condition.any():
            diagnostic[:2] = [3, 2]
            return np.nan, diagnostic
        p = p[condition]
        prediction = p[:, 2]-np.sum(p[:, 3:5]*(xy-p[:, :2]), axis=1)/p[:, 5]
        position = np.column_stack([np.tile(xy, (len(p), 1)), prediction])
        separation = np.linalg.norm(position-p[:, :3], axis=1)
        continuation = separation <= p[:, 10]+.2
        if not continuation.any():
            diagnostic[:2] = [3, 3]
            return np.nan, diagnostic
        p, prediction, separation = p[continuation], prediction[continuation], separation[continuation]
        weight = p[:, 7]*np.minimum(p[:, 8], 30)/30*np.exp(-.5*(separation/p[:, 10])**2)/(p[:, 6]**2+.1**2)
        centre_height = weighted_median(prediction, weight)
        # Orientation is chosen by nearest/high-quality contributing plane, not by RGB/provider.
        reference = p[np.argmax(weight), 3:6]
        compatible = (abs((prediction-centre_height)*p[:, 5]) <= .3) & (abs(p[:, 3:6] @ reference) >= np.cos(np.radians(20)))
        fraction = float(weight[compatible].sum()/weight.sum())
        diagnostic[7] = fraction
        diagnostic[3] = int(compatible.sum())
        diagnostic[12] = centre_height
        if fraction < .8:
            diagnostic[:2] = [3, 4]
            return np.nan, diagnostic
        if compatible.sum() < 3:
            diagnostic[:2] = [3, 5]
            return np.nan, diagnostic
        p, prediction, weight = p[compatible], prediction[compatible], weight[compatible]
        # Minimise perpendicular Huber departures from supported planes: scalar Z only.
        z = centre_height
        for _ in range(3):
            residual = abs((z-prediction)*p[:, 5])
            robust = np.minimum(1., .1/np.maximum(residual, 1e-12))
            w = weight*robust*p[:, 5]**2
            z = float(np.sum(w*prediction)/w.sum())
        normal = mean_plane_normal(p[:, 3:6], weight, reference)
        query = np.r_[xy, z]
        near = self.point_index.neighbours(query, 2.)
        consistent = near[abs((self.points[near]-query) @ normal) <= .3]
        diagnostic[4] = len(consistent)
        diagnostic[12:16] = [z, *normal]
        diagnostic[8] = float(np.sqrt(np.average(((z-prediction)*p[:, 5])**2, weights=weight)))
        diagnostic[9] = float(np.degrees(np.arccos(abs(normal[2]))))
        diagnostic[10] = float(np.sqrt(.2**2*np.sum(normal[:2]**2)+.1**2*normal[2]**2)/max(abs(normal[2]), 1e-12))
        if len(consistent):
            diagnostic[5] = float(np.linalg.norm(self.points[consistent]-query, axis=1).min())
            diagnostic[6] = hull_margin(self.points[consistent, :2], xy)
            diagnostic[11] = len(np.unique(self.records['point_source_id'][consistent]))
        if len(consistent) < 10:
            diagnostic[:2] = [3, 6]
            return np.nan, diagnostic
        if diagnostic[6] < -1e-8:
            diagnostic[:2] = [3, 7]
            return np.nan, diagnostic
        strong = diagnostic[5] <= .5 and diagnostic[6] >= .2 and (p[:, 10] == 1).sum() >= 3
        diagnostic[:2] = [1 if strong else 2, 0]
        return z, diagnostic

    def sample(self, xy, progress=False):
        heights = np.empty(len(xy)); evidence = np.empty((len(xy), len(DIAGNOSTIC_COLUMNS)))
        for i, q in enumerate(xy):
            heights[i], evidence[i] = self.query(q)
            if progress and i % 20000 == 0:
                print('orientation-aware nodes', i, '/', len(xy), flush=True)
        return heights, evidence


def supported_faces(vertices, faces, evidence):
    valid = np.isfinite(vertices[faces, 2]).all(1)
    normal = evidence[:, 13:16]
    maximum = np.zeros(len(faces))
    for a, b in ((0, 1), (1, 2), (2, 0)):
        edge = vertices[faces[:, b]]-vertices[faces[:, a]]
        for end in (a, b):
            departure = abs(np.sum(edge*normal[faces[:, end]], axis=1))
            maximum = np.maximum(maximum, np.nan_to_num(departure, nan=np.inf))
    # A smooth-looking bridge inconsistent with its measured endpoint planes is removed.
    return faces[valid & (maximum <= .3)], {'unsupported_vertex_faces': int((~valid).sum()),
                                         'plane_inconsistent_bridge_faces': int((valid & (maximum > .3)).sum())}


def preserve(repo, data):
    parents = previous.source_preservation(repo, data)
    m = json.loads((repo/'docs/earth-lab/riffelhorn-012d-metadata.json').read_text(encoding='utf-8'))
    root = data/'experiments/earth-lab/riffelhorn-012d/adaptive-heightfield-v1'
    for p in m['products']:
        if digest(root/p['path']) != p['sha256']:
            raise ValueError('Frozen 012D product changed: '+p['path'])
    parents['012d'] = {'identity': m['identity'], 'unchanged_products': len(m['products'])}
    return parents, root


def nearest_distance(index, queries):
    answer = []
    for q in queries:
        radius = .5
        while True:
            ids = index.neighbours(q, radius)
            if len(ids):
                answer.append(float(np.linalg.norm(index.points[ids]-q, axis=1).min()))
                break
            radius *= 2
            if radius > 128:
                raise ValueError('No observation within source diagnostic bound')
    return np.array(answer)


def source_gap_audit(xyz, records, split, candidates):
    """Post-fit full-survey sampling audit; never used as construction evidence."""
    result = []
    for item in candidates:
        q = np.array(item['xyz_lv95_ln02'])
        local = np.linalg.norm(xyz[:, :2]-q[:2], axis=1) <= 1.
        rows = np.flatnonzero(local)
        z = np.sort(xyz[rows, 2]); gaps = np.diff(z)
        k = int(np.argmax(gaps))
        maximum = float(gaps[k])
        result.append({'index_012c': item['source_index_012c'], 'xy_radius_m': 1.,
                       'all_survey_returns': len(rows), 'construction_returns': int((split[rows] == 0).sum()),
                       'flights': retention.counts(records['point_source_id'][rows]),
                       'classes': retention.counts(records['class_flags'][rows] & 31),
                       'z_range_ln02_m': [float(z[0]), float(z[-1])], 'largest_unobserved_z_interval_m': maximum,
                       'interval_ln02_m': [float(z[k]), float(z[k+1])],
                       'note': 'Finite XY cylinder; Z gaps are a sampling warning, not proof of a wall or overhang. Full survey is post-fit evidence only.'})
    return result


def figures(out, xyz, split, xy, evidence, surfaces, results, ids, views, sections):
    fig, axes = plt.subplots(2, 2, figsize=(13, 11))
    from matplotlib.colors import ListedColormap, BoundaryNorm
    for ax, values, title, categorical in (
        (axes[0, 0], evidence[:, 0], 'Construction constraints\n0 absent / 1 supported / 2 interpolated / 3 weak', True),
        (axes[0, 1], evidence[:, 1], 'Reason code (see manifest/report)', True),
        (axes[1, 0], evidence[:, 5], 'Nearest consistent construction return (3-D metres)', False),
        (axes[1, 1], evidence[:, 10], 'Nominal propagated height sigma (m)\nnot calibrated local uncertainty', False)):
        values = values if categorical else np.where(np.isfinite(values), np.minimum(values, 2), np.nan)
        if categorical:
            codes = 4 if ax is axes[0, 0] else 8
            cmap = ListedColormap(plt.colormaps['viridis'](np.linspace(0, 1, codes)))
            im = ax.scatter(xy[:, 0]-ORIGIN[0], xy[:, 1]-ORIGIN[1], c=values, s=.3,
                            cmap=cmap, norm=BoundaryNorm(np.arange(codes+1)-.5, codes))
            fig.colorbar(im, ax=ax, ticks=np.arange(codes))
        else:
            im = ax.scatter(xy[:, 0]-ORIGIN[0], xy[:, 1]-ORIGIN[1], c=values, s=.3, cmap='viridis')
            fig.colorbar(im, ax=ax)
        ax.set(title=title, xlabel='east offset (m)', ylabel='north offset (m)', aspect='equal')
    fig.suptitle('012E observability diagnostic independent of held-out fit | © swisstopo')
    fig.tight_layout(); fig.savefig(out/'observability.png', dpi=150); plt.close(fig)
    colours = {'provider': '#888888', '012d_regular': '#b700b7', '012d_adaptive': '#d98b00', 'robust': '#1268ad'}
    fig, axes = plt.subplots(2, 3, figsize=(17, 10))
    for ax, spec in zip(axes.ravel(), sections):
        axis = {'northing': 1, 'easting': 0, 'height_ln02_m': 2}[spec['constant_axis']]
        pos = spec['coordinate']; mask = abs(xyz[:, axis]-pos) <= .1
        dims = [0, 1] if axis == 2 else [1-axis, 2]
        offset = np.array([ORIGIN[d] if d < 2 else 0 for d in dims])
        for code, label, colour in ((0, 'construction', '#333333'), (1, 'held out', '#10a95c')):
            p = xyz[mask & (split == code)][:, dims]-offset
            ax.scatter(p[:, 0], p[:, 1], s=4, c=colour, label=label)
        for name, surface in surfaces.items():
            lines = previous.section_lines(surface.triangles, axis, pos)
            if len(lines):
                ax.add_collection(LineCollection(lines[:, :, dims]-offset, colors=colours[name], linewidths=.8, label=name))
        ax.autoscale(); ax.set_aspect('equal', adjustable='box')
        ax.set(title=f'{spec["constant_axis"]}={pos:.3f}; raw full thickness 0.2m',
               xlabel='east (m)' if dims[0] == 0 else 'north (m)', ylabel='LN02 (m)' if dims[1] == 2 else 'north (m)')
    axes[0, 0].legend(fontsize=7); fig.suptitle('Unchanged 012C/012D sections; missing evidence stays missing | © swisstopo')
    fig.tight_layout(); fig.savefig(out/'sections.png', dpi=150); plt.close(fig)
    fig, axes = plt.subplots(1, 4, figsize=(19, 5))
    for ax, (name, result) in zip(axes, results.items()):
        q = xyz[ids]; im = ax.scatter(q[:, 0]-ORIGIN[0], q[:, 1]-ORIGIN[1], c=np.minimum(result[:, 0], 2), s=3, vmin=0, vmax=2)
        ax.set(title=name+' held-out distance (m, colour cap 2)', aspect='equal'); fig.colorbar(im, ax=ax)
    fig.suptitle('Frozen held-out cohort; hole-edge distances included | © swisstopo')
    fig.tight_layout(); fig.savefig(out/'held-out-maps.png', dpi=130); plt.close(fig)
    for view in views:
        contact = Image.new('RGB', (1280, 4*754), 'white'); draw = ImageDraw.Draw(contact)
        for row, (name, surface) in enumerate(surfaces.items()):
            print('render', view['name'], name, flush=True)
            im = retention.render(surface.triangles, np.empty((0, 3)), np.array(view['camera_lv95_ln02_m']), np.array(view['target_lv95_ln02_m']), 'mesh')
            im.save(out/(view['name']+'-'+name+'.png'))
            contact.paste(im, (0, row*754))
            draw.text((8, row*754+725), f'{name} | {view["distance_m"]:g}m | identical geometry-only conditions | © swisstopo', fill='black')
        contact.save(out/(view['name']+'-comparison.png'))


def build(repo, data, out):
    start = time.monotonic(); parents, root = preserve(repo, data)
    croot = data/'experiments/earth-lab/riffelhorn-012c/raw-retention-v1'
    old = json.loads((root/'measurements.json').read_text(encoding='utf-8'))
    xyz = np.load(croot/'summit_cliff-xyz.npy'); records = np.load(croot/'summit_cliff-records.npy')
    split = np.load(root/'split.npy'); np.testing.assert_array_equal(split, previous.spatial_split(xyz[:, :2]))
    ids = np.load(root/'evaluation-indices.npy'); construction = np.load(root/'construction-audit-indices.npy')
    train = np.flatnonzero((split == 0) & ((records['class_flags'] & 31) == 2))
    out.mkdir(parents=True, exist_ok=True)
    planes, local = derive_planes(xyz[train], records[train], train)
    np.save(out/'construction-local-planes.npy', local); np.save(out/'plane-anchors.npy', planes)
    np.save(out/'construction-source-indices.npy', train)
    print('reliable plane anchors', len(planes), flush=True)
    estimator = PlaneEstimator(planes, xyz[train], records[train])
    xy, shape = previous.regular_xy(.125)
    z, evidence = estimator.sample(xy, progress=True)
    np.save(out/'observability.npy', evidence)
    vertices = np.column_stack([xy, z]); faces, bridge = supported_faces(vertices, previous.grid_faces(shape), evidence)
    np.save(out/'robust-vertices.npy', vertices); np.save(out/'robust-faces.npy', faces)
    surfaces = {}
    for name, prefix in (('provider', 'provider'), ('012d_regular', 'regular_0.125'), ('012d_adaptive', 'adaptive')):
        surfaces[name] = previous.Surface(np.load(root/(prefix+'-vertices.npy')), np.load(root/(prefix+'-faces.npy')))
    surfaces['robust'] = previous.Surface(vertices, faces)
    results = {}; reports = {}
    for name, surface in surfaces.items():
        if name == 'robust':
            result = surface.distances(xyz[ids]); cresult = surface.distances(xyz[construction])
            np.save(out/'robust-held-out.npy', result); np.save(out/'robust-construction.npy', cresult)
        else:
            prefix = {'provider': 'provider', '012d_regular': 'regular_0.125', '012d_adaptive': 'adaptive'}[name]
            result = np.load(root/(prefix+'-held-out.npy')); cresult = np.load(root/(prefix+'-construction-audit.npy'))
        results[name] = result
        q = xyz[ids]
        strata = {'lower_below_2890m': q[:, 2] < 2890, 'upper_at_least_2890m': q[:, 2] >= 2890,
                  'provider_over_0.5m': results['provider'][:, 0] > .5, 'provider_at_most_0.1m': results['provider'][:, 0] <= .1,
                  'class_2': (records['class_flags'][ids] & 31) == 2}
        report = previous.report_errors(q, result, surface.support(q[:, :2]), strata)
        report['provider_same_represented_cohort_m'] = previous.statistics(results['provider'][surface.support(q[:, :2]), 0])
        report['construction_audit'] = previous.report_errors(xyz[construction], cresult, surface.support(xyz[construction, :2]), {})
        reports[name] = report
    # Query constraints on held-out XY after fitting; observations' heights are not passed.
    _, held_evidence = estimator.sample(xyz[ids, :2])
    np.save(out/'held-out-observability.npy', held_evidence)
    for code, label in ((0, 'absent'), (1, 'supported'), (2, 'interpolated'), (3, 'weak')):
        mask = held_evidence[:, 0] == code
        reports['robust'][label+'_query_distance_m'] = previous.statistics(results['robust'][mask, 0])
        reports['robust'][label+'_provider_distance_m'] = previous.statistics(results['provider'][mask, 0])
    candidates = []
    construction_index = previous.Bins(xyz[train], 1.)
    for item in old['supported_012c_geometry_candidates']:
        q = np.array(item['xyz_lv95_ln02'])[None, :]; z19, diag19 = estimator.sample(q[:, :2])
        dist = surfaces['robust'].distances(q)[0, 0]; represented = bool(surfaces['robust'].support(q[:, :2])[0])
        baseline = item['distance_m']['provider']; gain = baseline-dist
        state = ('no accepted height; continuation unresolved' if not represented else 'substantially recovers' if gain >= .25 and dist <= .75*baseline
                 else 'partially recovers' if gain > .05 else 'leaves unresolved')
        # Post-fit diagnostic at the historical measured XYZ, not an estimator
        # hint. This exposes refusals despite reliable lower-face plane evidence.
        context = []
        for radius in (1., 2.):
            neighbours = construction_index.neighbours(q[0], radius)
            fit = robust_plane(xyz[train[neighbours]], radius)
            context.append({'radius_m': radius, 'construction_returns': len(neighbours),
                            'reliable_fit': fit is not None,
                            'rms_m': float(fit[2]) if fit is not None else None,
                            'planarity': float(fit[3]) if fit is not None else None,
                            'normal_abs_z': float(abs(fit[1][2])) if fit is not None else None,
                            'measured_point_plane_offset_m': float(abs((q[0]-fit[0]) @ fit[1])) if fit is not None else None})
        candidates.append({**item, 'robust_distance_m': float(dist), 'robust_represented_xy': represented,
                           'robust_state': state, 'orientation_support_code': int(diag19[0, 0]), 'reason_code': int(diag19[0, 1]),
                           'post_fit_local_construction_orientation': context})
    ambiguous = []
    for item in old['ambiguous_012c_multiple_height_candidates']:
        _, diagnostic = estimator.sample(np.array(item['xy_lv95'])[None, :])
        ambiguous.append({**item, 'robust_support_code': int(diagnostic[0, 0]), 'robust_reason_code': int(diagnostic[0, 1]),
                          'robust_proposed_height_ln02': float(diagnostic[0, 12]) if np.isfinite(diagnostic[0, 12]) else None,
                          'conclusion': 'No new independent topology evidence; selecting a plane or rejecting a conflict cannot establish an overhang.'})
    audit = source_gap_audit(xyz, records, split, old['supported_012c_geometry_candidates'])
    # Original full-survey positions audit gaps in existing provider section surfaces.
    # This audit is post-fit and cannot supply a height/normal to the estimator.
    probes = []
    for spec in old['sections'][:5]:
        axis = 1 if spec['constant_axis'] == 'northing' else 0
        lines = previous.section_lines(surfaces['provider'].triangles, axis, spec['coordinate'])
        for a, b in lines:
            steps = max(2, int(np.ceil(np.linalg.norm(a-b)/.5))+1)
            probes.extend(np.linspace(a, b, steps))
    probes = np.unique(np.asarray(probes), axis=0)
    inside = ((probes[:, :2] > BOUNDS[:2]+2) & (probes[:, :2] < BOUNDS[2:]-2)).all(1)
    probes = probes[inside]
    full_nn = nearest_distance(previous.Bins(xyz, 2.), probes)
    construction_nn = nearest_distance(previous.Bins(xyz[train], 2.), probes)
    np.save(out/'section-full-survey-support.npy', np.column_stack([probes, full_nn, construction_nn]))
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, nn, title in zip(axes, (full_nn, construction_nn), ('Full survey nearest XYZ', 'Construction nearest XYZ')):
        im = ax.scatter(probes[:, 0]-ORIGIN[0], probes[:, 2], c=np.minimum(nn, 5), s=4, vmin=0, vmax=5)
        ax.set(title=title+' (m; cap 5)', xlabel='east offset (m)', ylabel='LN02 m'); fig.colorbar(im, ax=ax)
    fig.suptitle('Provider-face continuation audit; not a ground-truth wall | © swisstopo')
    fig.tight_layout(); fig.savefig(out/'survey-continuation-support.png', dpi=130); plt.close(fig)
    t = surfaces['robust'].triangles; u, v = t[:, 1, :2]-t[:, 0, :2], t[:, 2, :2]-t[:, 0, :2]
    area = float(abs(u[:, 0]*v[:, 1]-u[:, 1]*v[:, 0]).sum()/2)
    edge = np.concatenate([t[:, a]-t[:, b] for a, b in ((0, 1), (1, 2), (2, 0))])
    measurements = {'bounds_lv95': BOUNDS.tolist(), 'vertical_reference': 'LN02 metres, unchanged',
                    'frozen_split_counts': retention.counts(split), 'held_out_interior': len(ids), 'construction_class_2': len(train),
                    'planes': {'anchors': len(planes), 'chosen_radius_m': retention.counts(planes[:, 10]),
                               'rms_m': previous.statistics(planes[:, 6]), 'inclination_deg': previous.statistics(np.degrees(np.arccos(abs(planes[:, 5])))),
                               'near_vertical_abs_nz_under_0.1': int((abs(planes[:, 5]) < .1).sum())},
                    'support': {'codes_at_nodes': retention.counts(evidence[:, 0]), 'reasons_at_nodes': retention.counts(evidence[:, 1]),
                                'codes_at_held_out_xy': retention.counts(held_evidence[:, 0]),
                                'nominal_propagated_height_sigma_m': previous.statistics(evidence[:, 10])},
                    'cost': {'allocated_nodes': len(vertices), 'finite_nodes': int(np.isfinite(z).sum()), 'used_vertices': len(np.unique(faces)),
                             'triangles': len(t), 'node_index_bytes': vertices.nbytes+faces.nbytes,
                             'represented_area_m2': area, 'unsupported_area_m2': 59.5**2-area,
                             'edge_length_m': previous.statistics(np.linalg.norm(edge, axis=1)), **bridge},
                    'held_out': reports, 'supported_19': candidates, 'ambiguous_9': ambiguous, 'full_survey_gap_audit': audit,
                    'provider_section_support': {'probes': len(probes), 'full_raw_nearest_m': previous.statistics(full_nn),
                                                 'construction_nearest_m': previous.statistics(construction_nn),
                                                 'full_raw_over_2m_count': int((full_nn > 2).sum()),
                                                 'construction_only_gap_over_2m_count': int(((construction_nn > 2) & (full_nn <= 2)).sum()),
                                                 'note': 'Unsupported provider continuation can reflect displaced representation, not only missing observations. Full survey diagnostic is independent of fitting.'},
                    'views': old['views'], 'sections': old['sections'], 'diagnostic_columns': DIAGNOSTIC_COLUMNS}
    retention.write_json(out/'measurements.json', measurements)
    figures(out, xyz, split, xy, evidence, surfaces, results, ids, old['views'], old['sections'])
    files = sorted([*out.glob('*.npy'), *out.glob('*.png'), out/'measurements.json'])
    manifest = {'experiment': 'Lab 012E robust cliff heightfield estimation', 'parents': parents,
                'processing_script_sha256': digest(Path(__file__)), 'parameters': PARAMETERS, 'diagnostic_columns': DIAGNOSTIC_COLUMNS,
                'plane_anchor_columns': ['centroid_e','centroid_n','centroid_z','normal_e','normal_n','normal_z','rms_m','planarity','count','split_angle_deg','radius_m','flights','012c_source_index','anchor_e','anchor_n','anchor_z'],
                'crs': 'EPSG:2056 LV95; LN02 metres; unchanged scale/orientation',
                'frozen_inputs': {name: digest(root/name) for name in ('split.npy','evaluation-indices.npy','construction-audit-indices.npy',
                                 'provider-vertices.npy','provider-faces.npy','regular_0.125-vertices.npy','regular_0.125-faces.npy',
                                 'adaptive-vertices.npy','adaptive-faces.npy')},
                'toolchain': {'python': sys.version.split()[0], **{k: importlib.metadata.version(k) for k in ('numpy','rasterio','matplotlib','Pillow')}},
                'products': [{'path': p.name, 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in files]}
    manifest['identity'] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    retention.write_json(out/'manifest.json', manifest)
    retention.write_json(out/'performance.json', {'total_seconds': time.monotonic()-start})
    print('IDENTITY', manifest['identity'], 'seconds', time.monotonic()-start, flush=True)
    return manifest


def verify(repo, data, out):
    parents, root = preserve(repo, data)
    m = json.loads((out/'manifest.json').read_text(encoding='utf-8')); identity = m.pop('identity')
    if hashlib.sha256(json.dumps(m, sort_keys=True).encode()).hexdigest() != identity or m['parents'] != parents:
        raise ValueError('Manifest/parent identity changed')
    if m['processing_script_sha256'] != digest(Path(__file__)):
        raise ValueError('Derivation script changed')
    for p in m['products']:
        if digest(out/p['path']) != p['sha256']: raise ValueError('Product changed: '+p['path'])
    xyz = np.load(data/'experiments/earth-lab/riffelhorn-012c/raw-retention-v1/summit_cliff-xyz.npy')
    split = np.load(root/'split.npy'); np.testing.assert_array_equal(split, previous.spatial_split(xyz[:, :2]))
    train = np.load(out/'construction-source-indices.npy')
    assert (split[train] == 0).all()
    planes = np.load(out/'plane-anchors.npy'); assert (split[planes[:, 12].astype(int)] == 0).all()
    records = np.load(data/'experiments/earth-lab/riffelhorn-012c/raw-retention-v1/summit_cliff-records.npy')
    expected_train = np.flatnonzero((split == 0) & ((records['class_flags'] & 31) == 2))
    np.testing.assert_array_equal(train, expected_train)
    np.testing.assert_array_equal(planes[:, 13:16], xyz[planes[:, 12].astype(int)])
    for name, expected in m['frozen_inputs'].items():
        assert digest(root/name) == expected
    estimator = PlaneEstimator(planes, xyz[train], records[train])
    vertices = np.load(out/'robust-vertices.npy'); faces = np.load(out/'robust-faces.npy'); evidence = np.load(out/'observability.npy')
    samples = np.linspace(0, len(vertices)-1, 20, dtype=int)
    z, diagnostic = estimator.sample(vertices[samples, :2])
    np.testing.assert_allclose(z, vertices[samples, 2], atol=1e-8, equal_nan=True)
    np.testing.assert_allclose(diagnostic, evidence[samples], atol=1e-8, equal_nan=True)
    assert len(np.unique(vertices[:, :2], axis=0)) == len(vertices)
    surface = previous.Surface(vertices, faces); ids = np.load(root/'evaluation-indices.npy')
    np.testing.assert_array_equal(surface.faces, faces)
    assert np.isfinite(vertices[faces]).all()
    samples = np.linspace(0, len(ids)-1, 16, dtype=int)
    distance = surface.distances(xyz[ids[samples]])
    np.testing.assert_allclose(distance, np.load(out/'robust-held-out.npy')[samples], atol=1e-8)
    for j in (0, -1):
        best = np.inf
        for offset in range(0, len(surface.triangles), 4096):
            d, _, _ = retention.triangle_closest(xyz[ids[samples[j]]][None, :], surface.triangles[offset:offset+4096])
            best = min(best, d[0])
        np.testing.assert_allclose(best, distance[j, 0], atol=1e-8)
    old = json.loads((root/'measurements.json').read_text(encoding='utf-8'))
    new = json.loads((out/'measurements.json').read_text(encoding='utf-8'))
    assert old['views'] == new['views'] and old['sections'] == new['sections']
    for view in new['views']:
        for name in ('provider','012d_regular','012d_adaptive','robust'):
            with Image.open(out/(view['name']+'-'+name+'.png')) as im:
                assert im.size == (1280,720) and np.asarray(im).std() > 1
        # Historical comparisons are byte-identical renders, not merely similar settings.
        for new_name, old_name in (('provider','provider'),('012d_regular','regular_0.125'),('012d_adaptive','adaptive')):
            assert digest(out/(view['name']+'-'+new_name+'.png')) == digest(root/(view['name']+'-'+old_name+'.png'))
    return {'result': 'PASS', 'identity': identity, 'originals': 16, 'source_las': 4,
            'frozen_products': {'012b':209,'012c':46,'012d':51}, 'products':len(m['products']),
            'split_points':len(split),'repeated_observability_nodes':20,'repeated_distance_queries':16,
            'global_bruteforce_queries':2,'unchanged_cameras':3,'unchanged_sections':6,'frames':12,
            'byte_identical_historical_frames':9}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--verify', action='store_true'); args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]; data = previous.resolve_storage_roots(repository_root=repo, require_data=True).data
    out = data/'experiments/earth-lab/riffelhorn-012e/robust-plane-heightfield-v1'
    result = verify(repo, data, out) if args.verify else build(repo, data, out)
    print(json.dumps(result if args.verify else {'identity': result['identity']}, indent=2), flush=True)
