// Research-only filtering of derived relief. Never changes terrain DEMs or geometry shaders.
export function gaussianResponse(wavelengthMetres,sigmaMetres){
 if(!(wavelengthMetres>0)||!(sigmaMetres>=0))throw new Error('Invalid physical filter scale');
 return Math.exp(-.5*(2*Math.PI*sigmaMetres/wavelengthMetres)**2);
}
export function gaussianKernel(sigma,radius=6){
 if(!(sigma>0)||!Number.isInteger(radius)||radius<0)throw new Error('Invalid kernel');
 const w=Array.from({length:2*radius+1},(_,i)=>Math.exp(-.5*((i-radius)/sigma)**2)),sum=w.reduce((a,b)=>a+b,0);
 return w.map(v=>v/sum);
}
export const filterGlsl=`
uniform vec2 u_research_relief; // nominal map-plane m/CSS pixel, control enabled
float researchMercY(float latitude) {
 return (1.0-log(tan(0.7853981633974483+radians(latitude)*0.5))/3.141592653589793)*0.5;
}
vec4 researchRelief(vec2 uv, vec2 size) {
 float latitude=mix(u_latrange[1],u_latrange[0],1.0-v_pos.y);
 float spacing=40075016.6855785*abs(researchMercY(u_latrange[0])-researchMercY(u_latrange[1]))*cos(radians(latitude))/(size.y-2.0);
 float sigma=u_research_relief.x/spacing;
 vec2 total=vec2(0.0);float weight=0.0;
 for(int y=-6;y<=6;y++)for(int x=-6;x<=6;x++){
  vec2 offset=vec2(float(x),float(y));float w=exp(-0.5*dot(offset,offset)/(sigma*sigma));
  total+=texture(u_image,uv+offset/size).rg*w;weight+=w;
 }
 return vec4(total/weight,1.0,1.0);
}
`;
export function installReliefHook({glsl}){
 const proto=WebGL2RenderingContext.prototype,source=proto.shaderSource,draw=proto.drawElements,drawArrays=proto.drawArrays;
 const locations=new WeakMap();globalThis.__researchRelief={enabled:false,patched:0,draws:0,shaderSources:[]};
 proto.shaderSource=function(shader,text){
  if(text.includes('igor_hillshade')){
   const pattern=/vec4\s+pixel\s*=\s*texture\s*\(\s*u_image\s*,\s*texturePos\s*\)\s*;/;
   if(!pattern.test(text))throw new Error('Pinned hillshade fragment no longer matches');
   text=text.replace(/void\s+main\s*\(\s*\)\s*\{/,glsl+'\nvoid main() {').replace(pattern,'vec4 pixel = u_research_relief.y > 0.5 ? researchRelief(texturePos,size) : texture(u_image,texturePos);');
   globalThis.__researchRelief.patched++;globalThis.__researchRelief.shaderSources.push(text);
  }
  return source.call(this,shader,text);
 };
 function uniform(gl){
  const program=gl.getParameter(gl.CURRENT_PROGRAM);if(!program)return;
  let location=locations.get(program);if(location===undefined){location=gl.getUniformLocation(program,'u_research_relief');locations.set(program,location);}
  if(location!==null){const m=globalThis.__atlasEvaluationMap;if(m){const mpp=40075016.6855785*Math.cos(m.getCenter().lat*Math.PI/180)/(512*2**m.getZoom());gl.uniform2f(location,mpp,globalThis.__researchRelief.enabled?1:0);globalThis.__researchRelief.draws++;}}
 }
 proto.drawElements=function(...args){uniform(this);return draw.apply(this,args);};
 proto.drawArrays=function(...args){uniform(this);return drawArrays.apply(this,args);};
}
