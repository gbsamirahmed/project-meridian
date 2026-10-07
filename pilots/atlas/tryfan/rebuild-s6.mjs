// S6 acceptance orchestration only: reuse S1-S5; never reconstruct their internals.
import {existsSync} from 'node:fs';import {resolve} from 'node:path';
import {buildRetained,seed} from './catalogue.mjs';import {register,load,storePath} from './generations.mjs';import {publishBaseline} from './derivations.mjs';import {publishDelivery} from './delivery.mjs';import {encode,requireThat} from './identity.mjs';
requireThat(process.argv[2],'invalid-store','Independent rebuild requires explicit store');const store=storePath(resolve(process.argv[2]));requireThat(!existsSync(store),'invalid-store','Independent rebuild requires absent store');
const retained=await buildRetained();const registration=register(store,seed(retained),retained.locators);const baseline=await publishBaseline({store});const serving=await publishDelivery({store});
process.stdout.write(encode({store,registration,baseline,serving,generation:load(store).generation}));
