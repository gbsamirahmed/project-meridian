// Isolated opt-in adapter; normal Vite configuration never imports this module.
import {regionalParentEvaluationPlugin} from './regional_parent_evaluation.mjs';
export function twoBandEvaluationPlugin(provider) {
  if (!['transition','common','regional','hard'].includes(provider)) throw new Error('Frozen controls only');
  const base=regionalParentEvaluationPlugin('regional');
  return {...base,name:'two-band-evaluation-only',load(id) {
    const code=base.load(id);
    return code?.replaceAll('127.0.0.1:4184','127.0.0.1:4185').replaceAll('/tiles/regional/','/tiles/'+provider+'/');
  }};
}
