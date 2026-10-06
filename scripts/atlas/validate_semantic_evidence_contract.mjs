/** Offline declaration receipt. Does not execute ingestion or inference. */
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createServer } from 'vite';
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const server = await createServer({ configFile: false, appType: 'custom', logLevel: 'silent', server: { middlewareMode: true } });
const { SEMANTIC_EVIDENCE_FIXTURES: bundle, EMPIRICAL_EXTRACT: extract } = await server.ssrLoadModule('/scripts/atlas/semantic-evidence/fixtures.ts');
const { validateSemanticEvidence } = await server.ssrLoadModule('/scripts/atlas/semantic-evidence/validate.ts');
await server.close();
const errors = validateSemanticEvidence(bundle);
for (const r of extract.receipts) if (sha(readFileSync(r.href)) !== r.sha256) errors.push(`Changed empirical receipt: ${r.href}`);
const plan = JSON.parse(readFileSync('docs/atlas/information-display-plan.json','utf8'));
for (const [path, hash] of Object.entries(plan.productionHashes)) if (sha(readFileSync(path)) !== hash) errors.push(`Changed production source: ${path}`);
const productionDiff = execFileSync('git', ['diff', '052374e', '--', 'src'], { encoding:'utf8' });
if (productionDiff.trim()) errors.push('Production source tree differs from starting checkpoint');
const files = [
  'scripts/atlas/semantic-evidence/contract.ts', 'scripts/atlas/semantic-evidence/validate.ts',
  'scripts/atlas/semantic-evidence/fixtures.ts', 'scripts/atlas/semantic-evidence/empirical-extract.json',
  'scripts/atlas/semantic-evidence/tsconfig.json', 'scripts/atlas/test_semantic_evidence_contract.mjs',
  'scripts/atlas/validate_semantic_evidence_contract.mjs',
];
const receipt = {
  contract: bundle.contract, startingCheckpoint:'052374e07d613a549f5a88640b42932f97a7f896',
  evidenceCheckpoints:['75ea9d8','c4da565','052374e'],
  fixtureCounts:{ resources:bundle.resources.length, definitions:bundle.definitions.length,
    mappings:bundle.mappings.length, collections:bundle.collections.length,
    claims:bundle.collections.reduce((n,c)=>n+c.claims.length,0) },
  fixtureJsonSha256:sha(JSON.stringify(bundle)),
  code:files.map(href=>({href,sha256:sha(readFileSync(href))})),
  retainedEvidence:extract.receipts,
  protectedProductionHashesChecked:Object.keys(plan.productionHashes).length,
  productionSourceDiffEmpty:!productionDiff.trim(), errors,
  scope:'Owned declaration integrity only; no source-truth, rights-clearance or ingestion validation.',
};
process.stdout.write(`${JSON.stringify(receipt,null,2)}\n`);
if(errors.length) process.exitCode=1;
