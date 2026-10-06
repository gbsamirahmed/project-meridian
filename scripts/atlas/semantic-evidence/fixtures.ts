/** Tiny evidence fixtures, NOT a semantic registry or inferred map.
 * Native snippets are pinned to retained empirical diagnostics. Symbolic asset
 * selectors describe original support; no geometry is invented from probe bounds.
 */
import { known, unknown } from '../../../src/atlas/terrain/metadata/terrainMetadata';
import type { AssetReference, EntityReference, Knowledge } from '../../../src/atlas/terrain/metadata/terrainMetadata';
import type { ClaimCollection, ClaimContext, ClaimSupport, DefinitionRef,
  EvidenceMode, FeatureRef, SemanticClaim, SemanticDefinition, SemanticEvidenceBundle,
  SemanticMapping, SemanticResource, SemanticValue, TimeExtent, ValueKind } from './contract';
import extract from './empirical-extract.json';

const mountain = 'docs/atlas/source-native-semantic-comparison.md';
const water = 'docs/atlas/water-feature-state-check.md';
const receipt = (href: string, selector?: string): AssetReference => ({ href, selector });
const ref = (id: string): DefinitionRef => ({ id, revision: '1' });
const definitions: SemanticDefinition[] = [];
const vocabularies: Record<string, { id: string; version: ReturnType<typeof known<string>> }> = {
  wc: { id: 'ESA WorldCover nomenclature', version: known('v200/2021 PUM2.0') },
  nrw: { id: 'Welsh Phase1 / JNCC nomenclature', version: known('retained JNCC2008 Welsh column; historical survey labels') },
  geocover: { id: 'GeoCover bedrock/unconsolidated model', version: known('September2026 catalogue') },
  glamos: { id: 'GLAMOS Swiss Glacier Inventory', version: known('SGI2016 r2020') },
  wfd: { id: 'WFD Cycle3 classification', version: known('2019 simplified') },
  jrc: { id: 'JRC Global Surface Water', version: known('v1.5') },
  phi: { id: 'NE Priority Habitat inventory', version: known('retained Sept_26 native fields') },
  ea: { id: 'EA Flood Zones / Recorded Flood Outlines', version: known('retained2026-10-06; source guidance per definition reference') },
  condition: { id: 'Meridian empirical reference-condition fixtures', version: known('1') },
  fixture: { id: 'Meridian TEST vocabulary, not production ontology', version: known('1') },
};
function define(id: string, kind: SemanticDefinition['kind'], label: string, meaning: string,
  reference = mountain, valueKinds?: readonly ValueKind[], qualifications: Pick<SemanticDefinition, 'requiredModes' | 'requiredConditions'> = {}): DefinitionRef {
  definitions.push({ ...ref(id), kind, vocabulary: vocabularies[id.split(':')[0]], label, meaning, reference: receipt(reference), valueKinds, ...qualifications });
  return ref(id);
}
const cover = define('wc:cover', 'property', 'WorldCover class', 'Annual source-native land-cover classification, not homogeneous local exposure.', mountain, ['category']);
const grass = define('wc:30', 'value', 'Grassland', 'Herbaceous vegetation below 5m; grass cover at least 10%; documented native WorldCover PUM v2 table3; not NRW heath identity.');
const habitat = define('nrw:habitat', 'property', 'Welsh Phase1 habitat', 'Historical habitat classification; mosaic composition belongs to original surveyed mosaic, not every Voronoi cell.', mountain, ['category', 'composition']);
const heath = define('nrw:D.1.1', 'value', extract.nrwHeathDefinition.welshName, 'Welsh Phase1 dry acid heath; native D.1.1 retains ecological meaning and survey context.');
const acid = define('nrw:B.1.1', 'value', extract.nrwGrassDefinition.welshName, 'Welsh Phase1 unimproved acid grassland, not generic grass cover.');
const flush = define('nrw:E.2.1', 'value', extract.nrwFlushDefinition.welshName, 'Welsh Phase1 acid flush, not open-water presence.');
const d5 = define('nrw:D.5', 'value', extract.nrwD5Definition.welshName, 'Welsh/JNCC D.5 naming conflicts; wet/dry equivalence unresolved.');
const geology = define('geocover:bedrock-unit', 'property', 'Geological unit', 'Geological interpreted substrate unit, not current exposed material.', mountain, ['descriptor']);
const glacierMember = define('glamos:membership', 'property', 'SGI glacier membership', 'Membership within dated glacier inventory geometry, not exposed ice fraction.', mountain, ['membership']);
const debrisCover = define('glamos:debris', 'property', 'SGI debris-cover membership', 'Dated debris-cover outline associated with underlying sgi-id glacier; glacier membership remains.', mountain, ['membership']);
const wfdMember = define('wfd:membership', 'property', 'WFD assessment-unit membership', 'Named reference/assessment waterbody unit, not instantaneous wetted edge.', water, ['membership'], { requiredConditions: [ref('condition:MHW')] });
const waterDetection = define('jrc:detection', 'property', 'Monthly water detection', 'Native codes0=no observations,1=water not detected,2=water detected; no direct proof of absence.', water, ['detection']);
const occurrence = define('jrc:occurrence', 'property', 'Historical occurrence', 'Water-detection frequency conditional on valid observations; not local probability, area fraction or confidence.', water, ['occurrence']);
const phiHab = define('phi:habitat', 'property', 'Priority Habitat inventory', 'Source-native inventory habitat claim with contributor vintages, not instantaneous water state.', water, ['category']);
const marsh = define('phi:CFPGM', 'value', extract.wetland.mainhabs, 'Coastal/floodplain grazing-marsh habitat inventory; does not assert currently standing open water.', water);
const reeds = define('phi:RBEDS', 'value', 'Reedbeds', 'PHI native reedbed habitat component, not a local fraction or current open-water state.', water);
const saltmarsh = define('phi:SALTM', 'value', 'Coastal saltmarsh', 'PHI native coastal saltmarsh component, distinct contributor epoch in combined polygon.', water);
const floodZone = define('ea:zone', 'property', 'Planning Flood Zone', 'Annual probability/reference-conditioned planning zone, mixed modelled/recorded origins; ignores benefit of defences.', water, ['category'], { requiredModes: ['scenario'], requiredConditions: [ref('condition:planning-AEP')] });
const fz3 = define('ea:FZ3', 'value', 'Flood Zone3', 'At least1%annual river or0.5%annual sea probability, under source planning convention; not current water.', water);
const eventExtent = define('ea:recorded-extent', 'property', 'Recorded Flood Outline', 'Historical event-associated outline, potentially reconstructed maximum; not simultaneous whole-outline wetness.', water, ['membership'], { requiredModes: ['event-record'] });
const mhw = define('condition:MHW', 'condition', 'MHW-derived mapping', 'WFD reference geometry derived from Mean High Water mapping convention; numeric tide/level not established.', water);
const planning = define('condition:planning-AEP', 'condition', 'Flood planning convention', 'Annual-exceedance category under present-day source convention, benefit of defences ignored.', water);
const vegetation = define('fixture:vegetation', 'property', 'Vegetation present', 'Fixture-only broad physical interpretation; not a frozen Atlas vocabulary.', mountain, ['category', 'fraction']);
const exposure = define('fixture:mineral-exposure', 'property', 'Exposed mineral surface', 'Fixture-only CURRENT visible exposure property; geological substrate cannot supply it.', mountain, ['fraction', 'category']);
const wetHeath = define('fixture:wet-heath', 'property', 'Wet heath', 'Fixture-only candidate interpretation used to retain D.5 ambiguity.', mountain, ['category']);
const wetland = define('fixture:wetland', 'property', 'Wetland property', 'Fixture-only broad property, not instantaneous open water.', water, ['category']);

const resources: SemanticResource[] = [];
function product(id: string, version: string, rights: string | Knowledge<string>, attribution: string, record: string): EntityReference {
  const source: EntityReference = { kind: 'source', id: `${id}-source`, revision: known(version) };
  const p: EntityReference = { kind: 'product', id, revision: known(version) };
  const terms = { licence: typeof rights === 'string' ? known(rights) : rights, references: [record, 'docs/atlas/physical-surface-sources.md', record === mountain ? 'docs/atlas/semantic-comparison-sources.json' : 'docs/atlas/water-check-sources.json'], attribution: [attribution], limitations: 'Full primary terms/contributor notices remain linked by the retained source inventory and receipts; this is not a substitute licence.' };
  resources.push({ ref: source, domain: 'semantics', name: `${id} authoritative source`, definition: receipt(record), rights: terms, inputs: [] });
  resources.push({ ref: p, domain: 'semantics', name: `${id} ${version}`, definition: receipt(record), rights: terms, inputs: [source] });
  return p;
}
const wc = product('worldcover', 'v200/2021', 'CC-BY-4.0', '© ESA WorldCover project2021 / Contains modified Copernicus Sentinel data(2021) processed by ESA WorldCover consortium. Native-grid subsets/analysis by Meridian.', mountain);
const nrw = product('nrw-phase1', 'retained-2026-10-06', 'OGL3', 'NRW / Ordnance Survey / JNCC, full notices in semantic-comparison-sources.json', mountain);
const geo = product('geocover', 'dataStatus20260901/retained-2026-10-06', 'swisstopo OGD source-credit terms', '© swisstopo', mountain);
const glamos = product('glamos-sgi2016', 'r2020', 'CC-BY-4.0', 'GLAMOS(2020), Swiss Glacier Inventory2016 r2020; https://doi.glamos.ch/data/inventory/inventory_sgi2016_r2020.html. Meridian subsets/analysis.', mountain);
const wfd = product('wfd-exe', 'Cycle3/class2019/export2024-02-02/retained-2026-10-06', 'OGL3', 'EA2024 / OS Crown/database2024', water);
const jrc = product('jrc-water', 'v1.5/1984-2024', 'Copernicus free reuse with acknowledgement', 'EC JRC/Google; Pekel et al.2016 DOI10.1038/nature20584', water);
const phi = product('priority-habitat', 'Sept_26/retained-2026-10-06', 'OGL3 with contributor CC-BY4 notices', 'Natural England / OS / contributor notices in retained PHI metadata', water);
const flood = product('ea-flood-zones', 'present-day/retained-2026-10-06', 'OGL3', 'EA2025', water);
const rfo = product('ea-recorded-floods', 'retained-2026-10-06/guidance6.2', 'OGL3', 'EA2025', water);
const epoch = (value: string, basis: string): TimeExtent => ({ kind: 'epoch', value, precision: 'year', basis });
const unknownTime: TimeExtent = { kind: 'unknown', reason: 'No exact claim-local acquisition or asserted validity supplied by retained metadata.' };
const support = (file: string, selector: string, meaning: string, grain: string, crs = 'EPSG:27700'): ClaimSupport => ({
  geometry: { kind: 'asset', asset: receipt(file, selector), crs: known({ name: crs, identifier: crs }), interpretation: meaning },
  meaning, grain: known(grain),
});
const mountainReceipt = 'docs/atlas/semantic-comparison-sources.json';
const waterReceipt = 'docs/atlas/water-check-sources.json';
const wcSupport = support(mountainReceipt, 'Tryfan native WorldCover grid; cell assignment WHERE code=30', 'Native grid-cell supports assigned by class binding; NOT all of Tryfan.', 'Nominal10m distributed classification; actual retained angular grid in diagnostics; no homogeneous-cell or local-accuracy guarantee.', 'EPSG:4326');
const nrwSupport = support(mountainReceipt, `nrw-vegetation-full-features.json WHERE original_unique_id=${extract.nrwMosaic.original_unique_id}`, 'Retained Voronoi feature geometry; native mosaic percentages refer to ORIGINAL mosaic support.', 'Historical Phase1 mapping; Voronoi subdivision is preparation, not new survey detail.');
const mosaicSupport = support(mountainReceipt, `ORIGINAL MOSAIC ${extract.nrwMosaic.original_unique_id}; geometry not separately established`, 'Original mosaic denominator/support; do not distribute composition to current Voronoi/probe cells.', 'Original survey mosaic, local shape incompletely known.');
const glacierSupport = support(mountainReceipt, 'glamos.zip SGI_2016_glaciers WHERE sgi-id=B56-07 intersect Riffelhorn window', 'Dated glacier inventory geometry, not exposed ice.', 'Native inventory polygons; no local confidence/instantaneous boundary.', 'EPSG:2056');
const debrisSupport = support(mountainReceipt, 'glamos.zip SGI_2016_debriscover WHERE id=3738', 'Dated debris outline above source-associated glacier.', 'Native outline; overlap does not establish thickness.', 'EPSG:2056');
const exe = support(waterReceipt, 'wfd.geojson WHERE water_body_id=GB510804505600', 'Whole returned reference-unit geometry; not instantaneous water.', 'Simplified WFD reference geometry, MHW-derived convention.');
const context = (s: ClaimSupport, p: EntityReference, modes: readonly EvidenceMode[], t: TimeExtent = unknownTime): ClaimContext => ({
  support: s, time: [{ role: 'nominal-epoch', extent: t }], evidence: {
    modes, description: 'Source-native evidence as retained in the empirical report.', inputs: [{ kind: 'resource', ref: p, role: 'source semantic product' }],
    completeness: 'partial', processing: [], limitations: 'Exact local observation lineage/precision may be unavailable; no new inference.' },
});
const category = (term: DefinitionRef): SemanticValue => ({ kind: 'category', term });
function claim(id: string, property: DefinitionRef, value: SemanticValue, fields: SemanticClaim['native']['fields'], record: string, term?: DefinitionRef): SemanticClaim {
  return { ...ref(id), native: { property, term, fields }, result: { kind: 'assertion', value }, record: receipt(record) };
}
const feature = (namespace: EntityReference, id: string, kind: FeatureRef['kind'] = 'feature'): FeatureRef => ({ namespace, id, kind });
const mappings: SemanticMapping[] = [
  { ...ref('mapping:grass-vegetation'), from: grass, target: vegetation, relationship: 'narrower', method: { method: 'Retained conceptual crosswalk c4da565' }, loss: ['Herbaceous height/cover thresholds and source class meaning are not retained by broad vegetation presence.'], qualification: 'Native class extension is narrower than broad vegetation; not local fraction.' },
  { ...ref('mapping:geology-exposure'), from: geology, target: exposure, relationship: 'unmappable', method: { method: 'Retained false-equivalence test c4da565' }, loss: ['Substrate is not evidence of present exposure.'], qualification: 'Rejected; retain geological claim without asserting exposed surface.' },
  { ...ref('mapping:d5'), from: d5, target: wetHeath, relationship: 'ambiguous', method: { method: 'Retained Welsh/JNCC definition comparison' }, loss: ['Wet/dry ecological distinction unresolved.'], qualification: 'Welsh and JNCC names differ; no repaired native value.' },
  { ...ref('mapping:marsh'), from: marsh, target: wetland, relationship: 'narrower', method: { method: 'Water stress-test crosswalk 052374e' }, loss: ['Specific habitat composition/management/source inventory omitted.'], qualification: 'Broad wetland interpretation only; not standing-water assertion.' },
];
const grassClaim = claim('claim:wc30', cover, category(grass), { code: 30, label: 'Grassland' }, mountain, grass);
const collections: ClaimCollection[] = [
  { ...ref('collection:worldcover'), product: wc, representation: 'raster', context: { ...context(wcSupport, wc, ['classification'], epoch('2021', 'WorldCover annual product epoch; not local acquisition instant.')),
    quality: [{ kind: 'validation', scope: { kind: 'product', description: 'WorldCover validation population, not this cell.' }, metric: 'Global overall accuracy', meaning: 'Reported WorldCover2021 validation population; not local confidence.', value: { kind: 'numeric', value: 76.7, unit: 'percent' }, reference: receipt('docs/atlas/physical-surface-sources.md', 'WorldCover2021 global overall validation') }] },
    claims: [{ ...grassClaim, interpretation: { mapping: ref('mapping:grass-vegetation'), disposition: 'qualified' } }],
    binding: { asset: receipt(mountainReceipt, 'Tryfan WorldCover retained native subset'), assignment: 'For each native cell, select the code template and substitute that native cell support; do not assert the code across collection coverage.', codes: [{ code: 30, claim: ref('claim:wc30') }] } },
  { ...ref('collection:nrw'), product: nrw, representation: 'vector', context: context(nrwSupport, nrw, ['survey-inventory', 'classification']), claims: [
    claim('claim:nrw-mosaic', habitat, { kind: 'composition', components: [{ term: known(acid), fraction: 0.5 }, { term: known(flush), fraction: 0.5 }], denominator: 'Original surveyed mosaic area; not arbitrary probe/current Voronoi area.', support: mosaicSupport }, extract.nrwMosaic, mountain),
    { ...claim('claim:nrw-heath', habitat, category(heath), { code: 'D.1.1', label: extract.nrwHeathDefinition.welshName }, mountain, heath), context: { support: support(mountainReceipt, 'nrw-vegetation-full-features.json WHERE phase1_code=D.1.1 within Tryfan', 'Native dry-acid-heath polygon support.', 'Historic habitat grain/MMU not established locally.') } },
    { ...claim('claim:nrw-d5', habitat, category(d5), { code: 'D.5', welshName: extract.nrwD5Definition.welshName, jnccName: extract.nrwD5Definition.jnccName }, mountain, d5), context: { support: support(mountainReceipt, 'nrw-vegetation-full-features.json WHERE phase1_code=D.5', 'Native D.5 support; definition ambiguity retained.', 'Historical native polygons.') }, interpretation: { mapping: ref('mapping:d5'), disposition: 'unresolved' } },
  ] },
  { ...ref('collection:geology'), product: geo, representation: 'vector', context: context(support(mountainReceipt, 'geocover-bedrock.json WHERE featureId=178895', 'Original bedrock-unit polygon; probe overlap is not entire unit.', 'Native interpreted geological mapping, dataStatus not survey date.', 'EPSG:2056'), geo, ['interpreted-mapping']), claims: [
    { ...claim('claim:geology', geology, { kind: 'descriptor', text: 'Undifferenzierte lithologische Einheit: Serpentinit' }, { ...extract.geocoverNative, featureId: '178895' }, mountain), interpretation: { mapping: ref('mapping:geology-exposure'), disposition: 'rejected' } },
  ] },
  { ...ref('collection:glacier'), product: glamos, representation: 'vector', context: context(glacierSupport, glamos, ['survey-inventory', 'interpreted-mapping']), claims: [
    { ...claim('claim:glacier', glacierMember, { kind: 'membership', feature: feature(glamos, extract.glacier['sgi-id']) }, extract.glacier, mountain), feature: feature(glamos, extract.glacier['sgi-id']), context: { time: [{ role: 'observation', extent: epoch('2015', 'Native year_acq; release2020 and nominal SGI2016 are different.') }] } },
    { ...claim('claim:debris', debrisCover, { kind: 'membership', feature: feature(glamos, extract.glacier['sgi-id']) }, extract.debris, mountain), feature: feature(glamos, extract.glacier['sgi-id']), context: { support: debrisSupport, time: [{ role: 'observation', extent: epoch('2016', 'Native debris year_acq.') }] } },
  ] },
  { ...ref('collection:wfd'), product: wfd, representation: 'vector', context: { ...context(exe, wfd, ['survey-inventory', 'interpreted-mapping'], epoch('2019', 'Cycle3 classification year, NOT current wetted state.')),
    conditions: [{ definition: mhw, native: { convention: 'Mean High Water-derived mapping' }, qualification: 'Reference outline; instantaneous level, tide/time and exact datum unknown.' }] }, claims: [
    { ...claim('claim:wfd', wfdMember, { kind: 'membership', feature: feature(wfd, extract.wfd.water_body_id) }, extract.wfd, water), feature: feature(wfd, extract.wfd.water_body_id) },
  ] },
];

const dated = (month: string): TimeExtent => ({ kind: 'interval', start: `${month}-01`,
  end: `${month}-${month.endsWith('03') ? '31' : '30'}`, precision: 'day', basis: 'Monthly product bin; exact local Landsat exposure times unknown.' });
const detectionClaims: SemanticClaim[] = ['2024-03', '2024-09'].flatMap(month => [0, 1, 2].map(code => ({
  ...ref(`claim:jrc-${month}-${code}`), native: { property: waterDetection, fields: { code, month } },
  result: code === 0 ? { kind: 'gap' as const, reason: 'no-observation' as const, explanation: 'Native0 means no observations; not dry waterbed or absent feature.' }
    : { kind: 'assertion' as const, value: { kind: 'detection' as const, outcome: code === 2 ? 'detected' as const : 'not-detected' as const, target: 'water' } },
  context: { support: support(waterReceipt, `JRC monthly native grid ${month} WHERE code=${code} in frozen Exe footprint`, 'Individual native cell supports assigned by time/code; no entire-probe assertion.', '0.00025degree native distributed grid; nominal Landsat30m, not homogeneous ground.', 'EPSG:4326'),
    time: [{ role: 'observation' as const, extent: dated(month) }] }, record: receipt(water),
})));
collections.push({ ...ref('collection:jrc-monthly'), product: jrc, representation: 'time-series', context: context(support(waterReceipt, 'Retained JRC monthly Exe native windows', 'Shared bounded native grid envelope; actual template support is assigned per cell/time/code.', '0.00025degree native distributed grid.', 'EPSG:4326'), jrc, ['classification', 'detection']), claims: detectionClaims,
  binding: { asset: receipt(waterReceipt, 'Retained native monthly2024-03/09 windows'), assignment: 'Compound time/native-code key selects a template; its support is each matching native cell, not WFD geometry.', codes: detectionClaims.map(c => ({ code: `${c.native.fields.month}:${c.native.fields.code}`, claim: ref(c.id) })) } });
collections.push({ ...ref('collection:jrc-history'), product: jrc, representation: 'records', context: { ...context(support('docs/atlas/water-check-plan.json', 'probes.P1.bounds', 'P1 frozen region, retained native-cell-centre population summary.', 'Native angular cells; region mean is not finer local field.'), jrc, ['derived']),
  time: [{ role: 'observation', extent: { kind: 'interval', start: '1984', end: '2024', precision: 'year', basis: 'v1.5 historical observation period, not continuous validity.' } }],
  evidence: { ...context(exe, jrc, ['derived']).evidence, processing: [{ revision: known('052374e'), method: 'Mean of published native occurrence percentages over retained P1 cell centres, water_compare.py at052374e', record: receipt('docs/atlas/water-check-results.json', 'probes.P1.raster.occurrence') }] } },
  claims: [claim('claim:jrc-occurrence', occurrence, { kind: 'occurrence', value: 0.71883, denominator: 'Arithmetic mean of77 native-cell occurrence percentages, each conditional on valid observations; not pooled counts, physical area fraction or current probability.', period: { kind: 'interval', start: '1984', end: '2024', precision: 'year', basis: 'Retained v1.5 occurrence.' } }, { meanOccurrencePercent: 71.883, cellCentres: 77 }, water)] });
collections.push({ ...ref('collection:wetland'), product: phi, representation: 'vector', context: context(support(waterReceipt, `phi.geojson WHERE uid=${extract.wetland.uid}`, 'Native inventory geometry; no current water saturation inferred.', 'PHI mapping/grain varies by contributor, MMU unknown locally.'), phi, ['survey-inventory']),
  claims: [{ ...claim('claim:wetland', phiHab, category(marsh), extract.wetland, water, marsh), interpretation: { mapping: ref('mapping:marsh'), disposition: 'qualified' }, context: { time: [{ role: 'survey', extent: { kind: 'epoch', value: '2024', precision: 'year', basis: 'Published local Natural England adviser/specialist feedback2024; not exact observation or current validity.' } }] } }] });
collections.push({ ...ref('collection:flood-zone'), product: flood, representation: 'vector', context: { ...context(support(waterReceipt, 'flood.geojson WHERE flood_zone=FZ3 AND origin=modelled intersects P1', 'Planning extent, not observation/current inundation.', 'Native model/record geometries; local model vintage unknown.'), flood, ['model', 'scenario']),
  conditions: [{ definition: planning, native: { flood_zone: 'FZ3', riverAnnualProbabilityAtLeast: '1%', seaAnnualProbabilityAtLeast: '0.5%', defences: 'benefit ignored' }, qualification: 'Source category, not per-location posterior; no exact level/model vintage established.' }] },
  claims: [claim('claim:flood-zone', floodZone, category(fz3), { flood_zone: 'FZ3', origin: 'modelled' }, water, fz3)] });
collections.push({ ...ref('collection:recorded-event'), product: rfo, representation: 'vector', context: { ...context(support(waterReceipt, 'rfo.geojson WHERE rec_out_id=31383', 'Event-associated recorded outline, potentially maximum not simultaneous wetness.', 'Historical survey-derived geometry; no local accuracy/confidence established.'), rfo, ['event-record', 'survey-inventory']),
  time: [{ role: 'event', extent: { kind: 'interval', start: '2014-02-04', end: '2014-02-05', precision: 'day', basis: 'Published event date interval; midnight native encoding is not exact acquisition.' } }] },
  claims: [{ ...claim('claim:recorded-event', eventExtent, { kind: 'membership', feature: feature(rfo, '31383', 'inventory-object') }, { rec_out_id: extract.event.rec_out_id, rec_grp_id: extract.event.rec_grp_id, name: extract.event.name, start_date: extract.event.start_date, end_date: extract.event.end_date, data_src: extract.event.data_src, flood_src: extract.event.flood_src, flood_caus: extract.event.flood_caus, data_qual: extract.event.data_qual, tidal_f: extract.event.tidal_f }, water),
    associations: [feature(rfo, '4124', 'event')] }] });
// One combined native polygon becomes two supported component claims, not one epoch.
const wetlandCollection = collections.find(c => c.id === 'collection:wetland');
const combinedSupport = support(waterReceipt, `phi.geojson WHERE uid=${extract.combinedWetland.uid}`, 'Native combined reedbed/saltmarsh inventory outline; component presence, no area fraction.', 'Same native polygon support; contributor epochs differ.');
if (wetlandCollection) collections[collections.indexOf(wetlandCollection)] = { ...wetlandCollection,
  claims: [...wetlandCollection.claims, ...([{ term: reeds, code: 'RBEDS', year: '2019' }, { term: saltmarsh, code: 'SALTM', year: '2026' }] as const).map(component => ({
    ...claim(`claim:phi-${component.code}`, phiHab, category(component.term), extract.combinedWetland, water, component.term),
    record: receipt(water, `native component ${component.code}, original compound record retained`),
    context: { support: combinedSupport, time: [{ role: 'survey' as const, extent: epoch(component.year, `Published EA saltmarsh dataset contributor vintage for${component.code}; not exact observation time.`) }] },
  }))],
};
// An explicit unperformed inference/evidence-gap request, NOT a source geological exposure assertion.
const gapProduct = product('meridian-gap-ledger', 'contract-fixture-v1', unknown('Owned fixture/gap declaration; no new external data rights grant. Original source licences govern any future input consumption.'), 'Meridian fixture plus original source credits', mountain);
collections.push({ ...ref('collection:gaps'), product: gapProduct, representation: 'records', context: context(support(mountainReceipt, 'Riffelhorn ordinary patch from frozen semantic plan', 'Query footprint; unsupported exposure claim, not asserted geology.', 'No inferred semantic resolution.', 'EPSG:2056'), gapProduct, ['interpreted-mapping']), claims: [{ ...ref('claim:unperformed'), native: { property: exposure, fields: { request: 'current fine mineral exposure', inference: 'not performed' } }, result: { kind: 'gap', reason: 'unsupported', explanation: 'Imagery/geometry exist but no semantic inference performed; geological mapping cannot establish this exposure.' }, record: receipt(mountain) }] });

export const SEMANTIC_EVIDENCE_FIXTURES: SemanticEvidenceBundle = {
  contract: 'atlas-semantic-evidence/v1', resources, definitions, mappings, collections,
};
export const EMPIRICAL_EXTRACT = extract;
