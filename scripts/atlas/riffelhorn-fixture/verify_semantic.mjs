/** Check only owned prepared declarations with the existing frozen contract.
 * Python also reconstructs the exact native preparation; this is not a hostile JSON schema.
 */
import { readFileSync } from 'node:fs';
import { createServer } from 'vite';
const server = await createServer({ configFile: false, appType: 'custom', logLevel: 'silent', server: { middlewareMode: true } });
try {
  const { validateSemanticEvidence } = await server.ssrLoadModule('/scripts/atlas/semantic-evidence/validate.ts');
  const errors = validateSemanticEvidence(JSON.parse(readFileSync(process.argv[2], 'utf8')));
  if (errors.length) throw new Error(errors.join('\n'));
  process.stdout.write('Frozen semantic contract passed\n');
} catch (error) {
  process.stderr.write(String(error) + '\n');
  process.exitCode = 1;
} finally {
  await server.close();
}
