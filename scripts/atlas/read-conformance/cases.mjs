import fs from 'node:fs';
import {point, sourceIdentity, slopeIdentity, ratioIdentity} from '../../../runtime/atlas/retrieval-cases.mjs';

export const publications = {
  before: {root: 'registrationWorld', generation: '65989736a06f72182fba9d9ad9d47955869f51ce943ef120effcad2df91352fd'},
  after: {root: 'registrationWorld', generation: '5d364e9947040f705699416e9094d8ad59463b5b2c2fcae2e3efdf79a7410289'},
  legacy: {root: 'legacyWorld', generation: '7f956d3bb640fb7262a3c46b1666306c88aff3418e966d39536882530350acf8'},
};

/** Requests reuse accepted anchors. Expected answers are never authored here. */
export function referenceCases() {
  const matrix = JSON.parse(fs.readFileSync(new URL('../riffelhorn-retrieval/matrix.json', import.meta.url), 'utf8'));
  const cases = matrix.cases.filter(row => !row.query.associated).map(row => ({
    id: `native-${row.id}`, publication: 'after', operation: 'retrieve',
    origin: `scripts/atlas/riffelhorn-retrieval/matrix.json#${row.id}`,
    tags: ['native', ...(row.id.includes('unknown') ? ['unknown'] : [])],
    query: {region: 'riffelhorn', ...row.query,
      ...(row.query.point || row.query.area ? {crs: row.query.crs ?? 'EPSG:2056'} : {})},
  }));
  function add(id, query, tags = [], publication = 'after') {
    cases.push({id, publication, operation: 'retrieve', tags,
      origin: 'runtime/atlas/retrieval-cases.mjs; runtime/atlas/test-retrieval.mjs', query});
  }
  const spatial = {region: 'riffelhorn', evidenceClass: 'derived', crs: 'EPSG:2056'};
  add('derived-anchor', {...spatial, point}, ['derived', 'spatial']);
  add('derived-adjacent-absent', {...spatial, point: [point[0] + .25, point[1]]}, ['absent', 'spatial']);
  add('derived-consumed-cells', {...spatial, point, spatialSupport: 'consumed'}, ['derived', 'spatial']);
  add('derived-consumed-boundary', {...spatial, point: [point[0] - .75, point[1]], spatialSupport: 'consumed'}, ['boundary']);
  add('derived-slope', {region: 'riffelhorn', identity: slopeIdentity}, ['method', 'identity']);
  add('derived-area-ratio', {region: 'riffelhorn', identity: ratioIdentity}, ['method', 'identity']);
  add('source-exact', {region: 'riffelhorn', identity: sourceIdentity}, ['identity', 'qualification']);
  for (const depth of ['direct', 'transitive']) {
    add(`source-dependents-${depth}`, {region: 'riffelhorn', point, crs: 'EPSG:2056', relatedTo: {identity: sourceIdentity, direction: 'dependents', depth}}, ['lineage']);
    add(`ratio-inputs-${depth}`, {relatedTo: {identity: ratioIdentity, direction: 'inputs', depth}}, ['lineage']);
  }
  add('derived-unknown-epoch', {region: 'riffelhorn', identity: slopeIdentity, evidenceClass: 'derived', time: {role: 'evidence-epoch', unknown: true}}, ['unknown']);
  add('derived-finite-epoch-absent', {region: 'riffelhorn', evidenceClass: 'derived', time: {role: 'evidence-epoch', start: 2024, end: 2024}}, ['absent', 'time']);
  add('derived-feature-absent', {region: 'riffelhorn', evidenceClass: 'derived', feature: 'glaciers:683'}, ['absent', 'feature']);
  add('crs84-point', {region: 'riffelhorn', point: [7.754736144063116, 45.97462853866641], crs: 'OGC:CRS84'}, ['crs']);
  add('knowledge-unknown-after', {region: 'riffelhorn', knowledge: {unknown: true}}, ['unknown', 'knowledge']);
  add('knowledge-exact-after', {region: 'riffelhorn', identity: sourceIdentity, knowledge: {revision: 'fcbac3e76a5e15da463361e57161c4d6a6a24377f5c2bef9be322d6301012a0f'}}, ['knowledge']);
  add('knowledge-accepted-instant', {region: 'riffelhorn', identity: sourceIdentity, knowledge: {start: '2026-10-09T02:07:06.400Z', end: '2026-10-09T02:07:06.400Z'}}, ['knowledge']);
  add('source-before-qualification', {region: 'riffelhorn', identity: sourceIdentity}, ['historical', 'qualification'], 'before');
  add('slope-before-requalification', {region: 'riffelhorn', identity: slopeIdentity}, ['historical', 'method'], 'before');
  add('legacy-unknown-knowledge', {region: 'riffelhorn', identity: 'glaciers:683', knowledge: {unknown: true}}, ['historical', 'unknown'], 'legacy');
  add('legacy-known-knowledge-absent', {region: 'riffelhorn', identity: 'glaciers:683', knowledge: {start: '1900-01-01T00:00:00.000Z', end: '2100-01-01T00:00:00.000Z'}}, ['historical', 'absent'], 'legacy');
  add('legacy-no-derived-state', {region: 'riffelhorn', identity: slopeIdentity}, ['historical', 'absent'], 'legacy');
  for (const [id, query] of [
    ['standalone-association', {region: 'riffelhorn', feature: 'glaciers:683', associated: true}],
    ['invented-family', {families: ['invented']}],
    ['inferred-crs', {region: 'riffelhorn', point}],
    ['wrong-crs', {region: 'riffelhorn', point, crs: 'EPSG:3857'}],
    ['physical-exact-date', {time: {role: 'evidence-epoch', start: '2021-01-01', end: '2021-12-31'}}],
    ['unknown-is-absent', {time: {role: 'evidence-epoch', absent: true}}],
    ['open-knowledge-interval', {knowledge: {start: '2026-01-01T00:00:00.000Z'}}],
    ['missing-relationship', {relatedTo: {identity: 'absent', direction: 'inputs', depth: 'direct'}}],
    ['arbitrary-sql', {sql: 'SELECT *'}],
  ]) add(`unsupported-${id}`, query, ['unsupported']);
  return {schema: 'meridian-atlas-read-requests/v1', cases};
}
