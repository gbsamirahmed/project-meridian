// Evaluation-only registration of the immutable Swiss pyramid; no runtime/provider branches.
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
const hash=b=>createHash('sha256').update(b).digest('hex');
const known=value=>({status:'known',value});
const unknown=reason=>({status:'unknown',reason});

/** Trace the exact tile union boundary, so footprint queries can cross internal tile edges. */
export function tileArea(files,z){
 const cells=new Set();
 for(const f of files){const m=/^tiles\/(\d+)\/(\d+)\/(\d+)\.png$/.exec(f.path);if(!m||Number(m[1])!==z)continue;
  cells.add(`${Number(m[2])},${Number(m[3])}`);}
 const lon=x=>x/2**z*360-180,lat=y=>Math.atan(Math.sinh(Math.PI*(1-2*y/2**z)))*180/Math.PI;
 const edges=new Map();
 const edge=(x,y,a,b)=>{const k=`${x},${y}`;if(edges.has(k))throw new Error('Corner-touching support requires explicit polygon partition');edges.set(k,`${a},${b}`);};
 for(const k of cells){const [x,y]=k.split(',').map(Number);
  if(!cells.has(`${x},${y-1}`))edge(x,y,x+1,y);
  if(!cells.has(`${x+1},${y}`))edge(x+1,y,x+1,y+1);
  if(!cells.has(`${x},${y+1}`))edge(x+1,y+1,x,y+1);
  if(!cells.has(`${x-1},${y}`))edge(x,y+1,x,y);
 }
 const rings=[];
 while(edges.size){const start=edges.keys().next().value;let k=start;const ring=[];
  do{const [x,y]=k.split(',').map(Number);ring.push([lon(x),lat(y)]);const next=edges.get(k);if(!next)throw new Error('Open support boundary');edges.delete(k);k=next;}while(k!==start);
  ring.push(ring[0]);rings.push(ring);
 }
 // Frozen Swiss complete inventories are connected and hole-free; refuse guessing otherwise.
 if(rings.length>1)throw new Error('Multiple support rings require explicit hole classification');
 return {kind:'geojson',geometry:{type:'MultiPolygon',coordinates:rings.map(r=>[r])}};
}

export async function swissGeometry(loader,data){
 const {PRODUCTION_TERRAIN_HIERARCHY,productionTerrainRegistry}=await loader.ssrLoadModule('/src/atlas/terrain/runtime/productionTerrainHierarchy.ts');
 const {registerTerrainHierarchy}=await loader.ssrLoadModule('/src/atlas/terrain/runtime/terrainRegistry.ts');
 const {selectTerrain}=await loader.ssrLoadModule('/src/atlas/terrain/runtime/terrainSelector.ts');
 const {adaptTerrainToMapLibre}=await loader.ssrLoadModule('/src/atlas/map/terrainDeliveryAdapter.ts');
 const h=structuredClone(PRODUCTION_TERRAIN_HIERARCHY);h.id='swissimage-frozen-geometry';h.revision='1';
 const productRoots={},resolvedAreas=[],levels=[],identities=[];
 for(const [name,zs]of [['riffelhorn-regional-parents-v1',[12,13]],['riffelhorn-swiss-support-v1',[14,15,16,17,18]]]){
  const root=path.join(data,'derived/atlas/riffelhorn',name),bytes=await readFile(path.join(root,'manifest.json'));
  const manifest=JSON.parse(bytes),metadata=JSON.parse(await readFile(path.join(root,'atlas-metadata.json'),'utf8'));
  const product=metadata.product??metadata;
  if(product.revision.value!==manifest.identity)throw new Error('Geometry revision mismatch');
  // Verify every delivered geometry tile before viewing; immutable inputs are never written.
  for(const f of manifest.files.filter(f=>f.path.startsWith('tiles/'))){if(hash(await readFile(path.join(root,f.path)))!==f.sha256)throw new Error(`Geometry hash mismatch ${f.path}`);}
  identities.push({product:product.id,revision:manifest.identity,manifestSha256:hash(bytes),verifiedTiles:manifest.files.filter(f=>f.path.startsWith('tiles/')).length});
  productRoots[product.id]=root;
  if(product.spatial.validSupport.value.area.kind==='asset')resolvedAreas.push({asset:product.spatial.validSupport.value.area.asset,area:tileArea(manifest.files,Math.max(...zs))});
  h.products.push({product,identity:{kind:'immutable-prepared',revision:manifest.identity,preparation:{href:`meridian-data://${name}/atlas-metadata.json`},contentManifest:{sha256:hash(bytes),hashScope:'manifest-bytes',record:{href:`meridian-data://${name}/manifest.json`}}},origin:{kind:'source-derived',sourceFamily:'frozen-swiss-regional'},validation:[],limitations:[]});
  for(const z of zs){const area=tileArea(manifest.files,z);if(!area.geometry.coordinates.length)continue;
   levels.push({id:`z${z}`,order:z,representation:{kind:'raster-dem-heightfield',product:{kind:'product',id:product.id,revision:product.revision},context:'Frozen appearance geometry, same for both imagery cases'},derivation:z<14?'regional-derived-parent':'resampled',
    support:{state:'complete',validSupport:known({area,purpose:'Only delivered complete Swiss tiles',basis:'Hash-verified immutable delivery inventory'}),interpretation:'No regional value outside complete tiles'},parentOperation:known({method:product.delivery.resampling.status==='known'?product.delivery.resampling.value:'Declared existing same-source resampling; see immutable processing lineage'}),sampleSpacing:unknown('Delivery level is not measurement resolution')});}
 }
 for(let i=1;i<levels.length;i++)levels[i].parent={family:'swiss-regional',level:levels[i-1].id};
 h.regional=[{id:'swiss-regional',role:'regional',sourceFamily:'frozen-swiss-regional',levelScheme:h.common.levelScheme,levels,informationCeiling:unknown('Existing Swiss source information semantics retained in products; mesh/delivery distinct'),overzoom:{allowed:true,description:'No added observations'},limitations:[]}];
 h.selection.regionalOrder=['swiss-regional'];
 const registry=registerTerrainHierarchy(h,{...productionTerrainRegistry.options,resolvedAreas,scaleLevels:Array.from({length:19},(_,order)=>({scheme:h.common.levelScheme,id:`z${order}`,order})),legacyCommon:{...productionTerrainRegistry.options.legacyCommon,addressingExtent:{kind:'native-rectangle',crs:{name:'OGC:CRS84',identifier:'OGC:CRS84'},axisOrder:'xy',bounds:[-180,-85.0511287798066,180,85.0511287798066]}}});
 return {registry,selectTerrain,adaptTerrainToMapLibre,productRoots,identities};
}
