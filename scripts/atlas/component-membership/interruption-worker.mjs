// Abrupt writer interruption under the candidate's local single-writer/root mechanism.
import {initialize} from './runtime.mjs';
const {core}=await initialize({meter:false});core.publish(process.argv[2],process.argv[3],{failAt:process.argv[4]});
