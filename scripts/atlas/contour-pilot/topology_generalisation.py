"""Conservative family-wide acceptance, not per-feature topology assurances.

Simplify stitched masters before clipping. No snapping, offsets or seam repair.
The caller must supply every potentially interacting contour, not isolated tiles.
"""
import shapely
from shapely.geometry import LineString, Polygon


def validate_family(originals, candidates, tolerance):
    if len(originals) != len(candidates):
        return False, 'feature count changed'
    for a, b in zip(originals, candidates):
        if not a.is_simple or not b.is_simple or b.is_empty:
            return False, 'non-simple line'
        if a.is_ring != b.is_ring or (a.is_ring and len(b.coords) < 4):
            return False, 'ring collapsed'
        if a.coords[0] != b.coords[0] or a.coords[-1] != b.coords[-1]:
            return False, 'endpoint/anchor moved'
        if not (a is b or a.equals_exact(b,0.)) and a.hausdorff_distance(b) > tolerance + 1e-9:
            return False, 'displacement exceeded'
    # Include both geometries: detect removed as well as introduced relationships.
    tree = shapely.STRtree(originals + candidates)
    n = len(originals)
    pairs = set()
    for i, line in enumerate(originals + candidates):
        for j in tree.query(line, predicate='intersects'):
            a, b = sorted((i % n, int(j) % n))
            if a != b: pairs.add((a, b))
    for i, j in sorted(pairs):
        if originals[i] is candidates[i] and originals[j] is candidates[j]: continue
        if originals[i].relate(originals[j]) != candidates[i].relate(candidates[j]):
            return False, 'inter-line relationship changed'
        if originals[i].intersects(originals[j]):
            before = shapely.normalize(originals[i].intersection(originals[j]))
            after = shapely.normalize(candidates[i].intersection(candidates[j]))
            if not before.equals_exact(after,1e-9):
                return False, 'shared intersection moved'
    rings = [i for i, line in enumerate(originals) if line.is_ring]
    polygons_a = [Polygon(originals[i]) for i in rings]
    polygons_b = [Polygon(candidates[i]) for i in rings]
    if any(not poly.is_valid for poly in polygons_a + polygons_b):
        return False, 'invalid ring interior'
    for i in range(len(rings)):
        for j in range(i):
            if originals[rings[i]] is candidates[rings[i]] and originals[rings[j]] is candidates[rings[j]]:
                continue
            if polygons_a[i].relate(polygons_a[j]) != polygons_b[i].relate(polygons_b[j]):
                return False, 'ring nesting changed'
    return True, None


def conservative_simplify(lines, tolerances=(2., 1., .5, .25)):
    """Deterministic serial backoff, reverting an unsafe feature to its original.

    Validates the complete supplied family after each accepted edit. This method
    prioritises validity over compression and is intentionally not a production
    simplifier. Exact predicates supplement (not replace) numerical qualifications.
    """
    originals = [LineString(line) for line in lines]
    valid, reason = validate_family(originals, originals, 0.)
    if not valid: raise ValueError('Invalid baseline: ' + reason)
    chosen = originals.copy()
    rejection_reasons = {}
    accepted_tolerances = []
    for index, original in enumerate(originals):
        accepted = 0.
        for tolerance in tolerances:
            if tolerance <= 0 or tolerance > 2:
                raise ValueError('Only positive tolerances up to 2 m are reviewed')
            candidate = original.simplify(tolerance, preserve_topology=True)
            if len(candidate.coords) >= len(original.coords): continue
            trial = chosen.copy(); trial[index] = candidate
            valid, reason = validate_family(originals, trial, max(tolerances))
            if valid:
                chosen = trial; accepted = tolerance
                break
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
        accepted_tolerances.append(accepted)
    valid, reason = validate_family(originals, chosen, max(tolerances))
    if not valid: raise ValueError('Final topology check failed: ' + reason)
    return [list(line.coords) for line in chosen], {
        'originalVertices': sum(len(line.coords) for line in originals),
        'candidateVertices': sum(len(line.coords) for line in chosen),
        'rejectedCandidatesByReason': rejection_reasons,
        'acceptedTolerancesMetres': accepted_tolerances,
        'topologyAcceptedWithinSuppliedFamily': True,
        'maxDisplacementMetres': max((0. if a is b or a.equals_exact(b,0.) else
            a.hausdorff_distance(b) for a, b in zip(originals, chosen)), default=0.),
    }
