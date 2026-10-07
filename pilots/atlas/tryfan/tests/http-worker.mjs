// Test writer only; consumers never import S1 internals.
import { load,register } from '../generations.mjs';
import { encode } from '../identity.mjs';
const store=process.argv[2],s=load(store);console.log(encode(register(store,{...s.value,parent:s.generation},s.locators)));
