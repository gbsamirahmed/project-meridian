import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import test from 'node:test';
import { createServer } from 'vite';

const server = await createServer({ configFile: false, appType: 'custom', logLevel: 'silent', server: { middlewareMode: true } });
const { SEMANTIC_EVIDENCE_FIXTURES: fixtures, EMPIRICAL_EXTRACT: extract } = await server.ssrLoadModule('/scripts/atlas/semantic-evidence/fixtures.ts');
const { validateSemanticEvidence: validate, resolveContext, definitionKey } = await server.ssrLoadModule('/scripts/atlas/semantic-evidence/validate.ts');
await server.close();
const copy = () => structuredClone(fixtures);
const collection = (b, id) => b.collections.find(c => c.id === `collection:${id}`);
const claim = (b, id) => b.collections.flatMap(c => c.claims).find(c => c.id === `claim:${id}`);
const rejects = (b, pattern) => assert.match(validate(b).join('\n'), pattern);
const known = value => ({ status: 'known', value });
const ref = id => ({ id, revision: '1' });
const sha = file => createHash('sha256').update(readFileSync(file)).digest('hex');

test('all retained evidence fixtures validate without data, network or production registration', () => {
  assert.deepEqual(validate(fixtures), []);
  assert.equal(fixtures.contract, 'atlas-semantic-evidence/v1');
  assert.equal(fixtures.collections.length, 11);
});
test('tiny native extracts match immutable retained reports and receipts', () => {
  for (const r of extract.receipts) assert.equal(sha(r.href), r.sha256);
  const mountain = JSON.parse(readFileSync('docs/atlas/semantic-comparison-results.json', 'utf8'));
  const water = JSON.parse(readFileSync('docs/atlas/water-check-results.json', 'utf8'));
  assert.deepEqual(extract.nrwMosaic, mountain.nrwMosaicRecords[0]);
  assert.deepEqual(extract.glacier, mountain.glamosNativeRecords[0]);
  assert.deepEqual(extract.debris, mountain.glamosNativeRecords[1]);
  assert.deepEqual(extract.wetland, water.probes.find(p => p.id === 'P5').phi.nativeClaims[0]);
  assert.deepEqual(extract.event, water.nativeEventRecords.find(e => e.rec_out_id === 31383));
  assert.deepEqual(extract.wfd, water.probes[0].wfd.nativeIdentities[0]);
  assert.equal(claim(fixtures, 'jrc-occurrence').result.value.value * 100, water.probes[0].raster.occurrence.meanOccurrencePercent);
  assert.match(claim(fixtures, 'wetland').context.time[0].extent.basis, /2024/);
  assert.match(extract.wetland.primsource, /2024/);
  assert.equal(extract.geocoverNative.label, claim(fixtures, 'geology').result.value.text);
});
test('native category remains recoverable with or without common interpretation', () => {
  const b = copy(); const q = claim(b, 'wc30'); delete q.interpretation;
  assert.deepEqual(validate(b), []);
  assert.equal(q.native.fields.code, 30); assert.equal(q.result.value.term.id, 'wc:30');
  q.result.value.term = ref('nrw:D.1.1'); rejects(b, /native category overwritten/);
});
test('all seven directional relationships preserve loss and control interpretation disposition', () => {
  for (const relation of ['compatible', 'broader', 'narrower', 'partial', 'ambiguous', 'incompatible', 'unmappable']) {
    const b = copy(); b.mappings[0].relationship = relation;
    claim(b, 'wc30').interpretation.disposition = relation === 'ambiguous' ? 'unresolved'
      : ['incompatible', 'unmappable'].includes(relation) ? 'rejected' : 'qualified';
    assert.deepEqual(validate(b), [], relation);
    assert.ok(b.mappings[0].loss.length);
    claim(b, 'wc30').interpretation.disposition = relation === 'ambiguous' ? 'qualified' : 'unresolved';
    rejects(b, /mapping disposition/);
  }
});
test('geology does not silently become exposure; ambiguous mapping is not missing evidence', () => {
  const g = claim(fixtures, 'geology'), d = claim(fixtures, 'nrw-d5');
  assert.equal(g.result.kind, 'assertion'); assert.equal(g.interpretation.disposition, 'rejected');
  assert.equal(d.result.kind, 'assertion'); assert.equal(d.interpretation.disposition, 'unresolved');
  const b = copy(); claim(b, 'geology').interpretation.disposition = 'qualified'; rejects(b, /mapping disposition/);
});
test('glacier/debris coexist with one feature identity, independent space/time and native records', () => {
  const c = collection(fixtures, 'glacier'); const [g, d] = c.claims;
  assert.deepEqual(g.feature, d.feature);
  assert.equal(g.feature.id, 'B56-07');
  assert.equal(resolveContext(c.context, g).time[0].extent.value, '2015');
  assert.equal(resolveContext(c.context, d).time[0].extent.value, '2016');
  assert.notDeepEqual(resolveContext(c.context, g).support, resolveContext(c.context, d).support);
});
test('mosaic fractions retain original denominator, not Voronoi cell or confidence', () => {
  const q = claim(fixtures, 'nrw-mosaic');
  assert.equal(q.result.value.kind, 'composition');
  assert.equal(q.result.value.components[0].fraction, 0.5);
  assert.match(q.result.value.denominator, /Original/);
  assert.match(q.result.value.support.meaning, /not distribute/);
  const b = copy(); claim(b, 'nrw-mosaic').result.value.components[0].fraction = 1.1; rejects(b, /proportion outside|composition exceeds/);
});
test('feature namespace/event association differs from current physical state', () => {
  assert.equal(claim(fixtures, 'wfd').feature.id, 'GB510804505600');
  const q = claim(fixtures, 'recorded-event');
  assert.equal(q.associations[0].kind, 'event'); assert.equal(q.associations[0].id, '4124');
  assert.equal(q.result.value.feature.kind, 'inventory-object');
  assert.equal(q.native.fields.data_qual, null); // No invented confidence.
});
test('reference-conditioned native properties cannot be relabelled as observations', () => {
  const b = copy(); collection(b, 'flood-zone').context.conditions = [];
  rejects(b, /scenario requires reference condition|native property requires reference condition/);
  collection(b, 'flood-zone').context.evidence.modes = ['observation']; rejects(b, /requires evidence mode scenario/);
  const c = copy(); delete collection(c, 'wfd').context.conditions; rejects(c, /native property requires reference condition/);
});
test('model and recorded mixed lineage can coexist, without raw-observation masquerade', () => {
  const b = copy(); const c = collection(b, 'flood-zone');
  c.context.evidence.modes.push('event-record'); c.claims[0].native.fields.origin = 'modelled and recorded';
  assert.deepEqual(validate(b), []);
  assert.notEqual(c.context.evidence.modes[0], 'observation');
});
test('quality populations remain scoped; missing local confidence is valid', () => {
  const wc = collection(fixtures, 'worldcover');
  assert.equal(wc.context.quality[0].scope.kind, 'product');
  assert.equal(wc.context.quality[0].value.value, 76.7);
  assert.equal(wc.context.quality[0].value.unit, 'percent');
  const b = copy(); collection(b, 'worldcover').context.quality[0].kind = 'confidence'; rejects(b, /confidence cannot borrow/);
});
test('quality can carry local probability, survey label or class validation without conversion', () => {
  for (const [kind, scope, value] of [['probability','claim',{kind:'numeric',value:0.6,unit:'proportion'}], ['survey','claim',{kind:'label',label:'Fair'}], ['validation','class',{kind:'numeric',value:0.8,unit:'proportion'}]]) {
    const b = copy(); collection(b,'worldcover').context.quality = [{kind, scope:{kind:scope,description:'Synthetic scoped test only'}, metric:'Declared metric',meaning:'Not physical cover fraction',value,reference:{href:'docs/atlas/semantic-evidence-contract.md'}}];
    assert.deepEqual(validate(b), []);
  }
});
test('native no observation, non-detection and unknown inference remain different', () => {
  assert.equal(claim(fixtures, 'jrc-2024-03-0').result.reason, 'no-observation');
  assert.equal(claim(fixtures, 'jrc-2024-03-1').result.value.outcome, 'not-detected');
  assert.equal(claim(fixtures, 'unperformed').result.reason, 'unsupported');
  for (const reason of ['outside-support','no-observation','not-classified','missing-inventory','unsupported','unknown','not-applicable']) {
    const b = copy(); claim(b, 'unperformed').result.reason = reason; assert.deepEqual(validate(b), []);
  }
  const b = copy(); claim(b,'unperformed').result.explanation = ''; rejects(b,/gap explanation/);
});
test('absence/gap cannot assert a successful common mapping', () => {
  const b = copy(); claim(b,'wc30').result = {kind:'gap',reason:'not-classified',explanation:'Synthetic missing classification'};
  rejects(b,/evidence gap cannot assert/);
});
test('time is claim local; unknown, partial epochs, event intervals and publication remain distinct', () => {
  const b = copy(); b.resources[0].dates = [{role:'publication',extent:{kind:'instant',value:'2022-10-01',precision:'day',basis:'Synthetic date, not acquisition'}}];
  assert.deepEqual(validate(b), []);
  assert.equal(collection(b,'worldcover').context.time[0].extent.value, '2021');
  assert.equal(collection(b,'nrw').context.time[0].extent.kind, 'unknown');
  claim(b,'glacier').context.time[0].extent = {kind:'interval',start:'2016',end:'2015',precision:'year',basis:'Synthetic'}; rejects(b,/reversed interval/);
  claim(b,'glacier').context.time[0].extent = {kind:'instant',value:'2024-02-31',precision:'day',basis:'Synthetic'}; rejects(b,/invalid time/);
});
test('combined inventory components keep full native record and distinct contributor times', () => {
  const c=collection(fixtures,'wetland'); const reeds=claim(fixtures,'phi-RBEDS'), salt=claim(fixtures,'phi-SALTM');
  assert.deepEqual(reeds.native.fields,salt.native.fields);
  assert.equal(reeds.native.fields.mainhabs,'Reedbeds,Coastal saltmarsh');
  assert.equal(resolveContext(c.context,reeds).time[0].extent.value,'2019');
  assert.equal(resolveContext(c.context,salt).time[0].extent.value,'2026');
  assert.deepEqual(resolveContext(c.context,reeds).support,resolveContext(c.context,salt).support);
});
test('CSS/display, CRS and terrain policy are outside contract; spatial forms are reusable', () => {
  const examples = [
    {kind:'native-point',crs:{name:'BNG',identifier:'EPSG:27700'},coordinates:[295800,87150]},
    {kind:'native-line',crs:{name:'BNG'},coordinates:[[1,2],[3,4]]},
    {kind:'native-rectangle',crs:{name:'BNG'},bounds:[1,2,3,4],axisOrder:'xy'},
    {kind:'geojson',geometry:{type:'Polygon',coordinates:[[[0,0],[1,0],[1,1],[0,0]]]}},
    {kind:'geojson',geometry:{type:'MultiPolygon',coordinates:[[[[0,0],[1,0],[1,1],[0,0]]]]}},
  ];
  for (const geometry of examples) { const b=copy(); collection(b,'gaps').context.support.geometry=geometry; assert.deepEqual(validate(b),[]); }
  const b=copy(); collection(b,'gaps').context.support.geometry=examples[2]; examples[2].bounds=[4,2,1,4]; rejects(b,/invalid native rectangle/);
});
test('large raster strategy is shared definitions plus binding, never metadata per pixel', () => {
  const c=collection(fixtures,'worldcover'); assert.equal(c.claims.length,1);
  assert.equal(c.binding.codes[0].code,30); assert.match(c.binding.assignment,/each native cell/);
  const b=copy(); collection(b,'worldcover').binding.codes[0].claim=ref('missing'); rejects(b,/binding must reference local/);
});
test('dated repeated detection templates do not require a new product for every month', () => {
  const c=collection(fixtures,'jrc-monthly'); assert.equal(c.claims.length,6);
  const march=resolveContext(c.context,claim(fixtures,'jrc-2024-03-2')).time;
  const sept=resolveContext(c.context,claim(fixtures,'jrc-2024-09-2')).time;
  assert.notDeepEqual(march,sept); assert.equal(c.product.id,'jrc-water');
});
test('contradictory assertions coexist without a truth resolver', () => {
  const b=copy(); const c=collection(b,'jrc-monthly');
  const contradicted=structuredClone(claim(b,'jrc-2024-03-2'));
  contradicted.native.fields.code=1;
  contradicted.id='claim:contradiction'; contradicted.result.value.outcome='not-detected';
  const product = structuredClone(b.resources.find(r => r.ref.id === c.product.id));
  product.ref.id='synthetic-alternative-water'; product.name='Synthetic conflicting source product only';
  b.resources.push(product);
  b.collections.push({...structuredClone(c),id:'collection:synthetic-conflict',product:product.ref,claims:[contradicted],binding:undefined});
  assert.deepEqual(validate(b),[]); // Structural retention, not scientific adjudication.
});
test('future derived claims require recorded inputs and method, with no special truth path', () => {
  const b=copy(); const c=collection(b,'gaps');
  c.context.evidence.modes=['derived'];
  rejects(b,/derived claim requires/);
  c.context.evidence.processing=[{revision:known('v1'),method:'Synthetic future inference fixture',software:{'test-method':'v1'}}];
  c.context.evidence.inputs=[{kind:'claim',ref:ref('claim:wc30'),role:'Synthetic input for contract test, not a real inference'}];
  assert.deepEqual(validate(b),[]);
  c.claims[0].result={kind:'assertion',value:{kind:'fraction',value:0.4,denominator:'Synthetic footprint area',support:c.context.support}};
  assert.deepEqual(validate(b),[]);
  c.context.evidence.inputs=[]; rejects(b,/derived claim requires/);
});
test('probability, fraction and history cannot silently replace each other', () => {
  const b=copy(); claim(b,'jrc-occurrence').result.value={kind:'probability',value:0.71883,event:'Synthetic',basis:'Synthetic'};
  rejects(b,/value kind violates property/);
  claim(b,'jrc-occurrence').result.value={kind:'fraction',value:0.71883,denominator:'Synthetic',support:collection(b,'jrc-history').context.support}; rejects(b,/value kind violates property/);
});
test('nonempty IDs, exact references and immutable revision snapshots', () => {
  const b=copy(); b.definitions.push({...b.definitions[0],meaning:'Silently reinterpreted'}); rejects(b,/duplicate definition identity/);
  b.definitions.at(-1).revision='2'; assert.deepEqual(validate(b),[]);
  assert.equal(claim(b,'wc30').native.property.revision,'1');
  claim(b,'wc30').native.property.revision='missing'; rejects(b,/unresolved definition revision/);
  const c=copy(); c.mappings[0].revision='2'; rejects(c,/unresolved mapping revision/);
  const d=copy(); d.collections[0].product={...d.collections[0].product,revision:known('unknown-product-revision')}; rejects(d,/unresolved resource revision/);
  const e=copy(); e.collections[0].id=''; rejects(e,/required text/);
});
test('unknown source revision/time/rights are honest representable states', () => {
  const b=copy(); const original=b.resources[0].ref;
  const u={...original,revision:{status:'unknown',reason:'Unpinned external source'}};
  b.resources[0].ref=u; b.resources[1].inputs=[u]; b.resources[0].rights.licence={status:'unknown',reason:'Rights unavailable, not permission to consume'};
  assert.deepEqual(validate(b),[]);
  b.resources[0].rights.licence.reason=''; rejects(b,/unknown requires reason/);
});
test('shared context overrides replace complete fields; no accidental temporal merging', () => {
  const c=collection(fixtures,'glacier');
  assert.equal(resolveContext(c.context,c.claims[0]).time.length,1);
  assert.notEqual(resolveContext(c.context,c.claims[0]).time[0].extent.kind,'unknown');
});
test('production snapshot and historical empirical reports remain byte-identical', () => {
  const plan=JSON.parse(readFileSync('docs/atlas/information-display-plan.json','utf8'));
  for(const [file, hash] of Object.entries(plan.productionHashes)) assert.equal(sha(file),hash,file);
  assert.equal(Object.keys(plan.productionHashes).length,113);
  for(const r of extract.receipts) assert.ok(existsSync(r.href));
  assert.equal(definitionKey(ref('fixture:vegetation')), '["fixture:vegetation","1"]');
});
