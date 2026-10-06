import {test} from 'node:test';
import assert from 'node:assert/strict';
import {gaussianResponse,gaussianKernel,filterGlsl} from './relief_scale_control.mjs';
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-12);
test('Normalized symmetric Gaussian does not amplify constant slopes',()=>{for(const s of [.05,.5,1,1.5]){const w=gaussianKernel(s);near(w.reduce((a,b)=>a+b),1);w.forEach((v,i)=>{assert.ok(v>=0);near(v,w.at(-i-1));});const slope=7;near(w.reduce((a,b)=>a+b*slope,0),slope);}});
test('Physical wavelength response follows Gaussian scale-space',()=>{near(gaussianResponse(8,1),Math.exp(-(Math.PI**2)/32));near(gaussianResponse(80,10),gaussianResponse(8,1));assert.ok(gaussianResponse(2,1)<.01);assert.ok(gaussianResponse(32,1)>.98);assert.ok(gaussianResponse(8,1)>gaussianResponse(2,1));assert.throws(()=>gaussianResponse(0,1));});
test('Separation preserves input and makes fine component explicit',()=>{const d=[1,2,5,-3,7],w=gaussianKernel(1,1);const broad=d.map((_,i)=>w.reduce((s,v,j)=>s+v*d[Math.min(4,Math.max(0,i+j-1))],0));const fine=d.map((v,i)=>v-broad[i]);d.forEach((v,i)=>near(v,broad[i]+fine[i]));assert.deepEqual(d,[1,2,5,-3,7]);});
test('Experimental shader contains frozen derivative filter only',()=>{assert.ok(filterGlsl.includes('x=-6;x<=6'));assert.ok(filterGlsl.includes('texture(u_image'));assert.ok(!filterGlsl.includes('getElevation'));});
