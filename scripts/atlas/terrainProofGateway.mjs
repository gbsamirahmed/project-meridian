// Evaluation-only stream: every XYZ request uses canonical registry -> selector -> adapter.
// No normal Vite/runtime import. Whole-tile eligibility, no source mixing within a tile.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

export function tileFootprint(z,x,y) {
  const lon=x=>x/2**z*360-180,lat=y=>Math.atan(Math.sinh(Math.PI*(1-2*y/2**z)))*180/Math.PI;
  // Sub-micrometre roundoff guard on coincident declared tile edges; not source extrapolation.
  const e=1e-12,w=lon(x)+e,r=lon(x+1)-e,s=lat(y+1)+e,n=lat(y)-e;
  return {kind:'geojson',geometry:{type:'Polygon',coordinates:[[[w,s],[r,s],[r,n],[w,n],[w,s]]]}};
}

export function createTerrainProofGateway({registry,selectTerrain,adaptTerrainToMapLibre,productRoots,legacyCache='http://127.0.0.1:4187',port=4186,commonOnly=false}) {
  const records=[];
  const server=createServer(async(req,res)=>{
    // The declared local product URL also works as an ordinary asset delivery endpoint.
    // Primary proof requests use /terrain and always execute selection/adapter below.
    const raw=/^\/regional\/(\d+)\/(\d+)\/(\d+)\.png$/.exec(req.url);
    if(raw){
      const [z,x,y]=raw.slice(1).map(Number);
      const bindings=registry.hierarchy.products.filter(b=>productRoots[b.product.id]&&b.product.delivery.kind==='raster-tiles'
        &&decodeURIComponent(new URL(b.product.delivery.tileTemplate).pathname).replace('{z}',z).replace('{x}',x).replace('{y}',y)===req.url);
      if(bindings.length!==1||z<0||z>17||x<0||y<0||x>=2**z||y>=2**z){res.writeHead(404).end();return;}
      try{const body=await readFile(path.join(productRoots[bindings[0].product.id],'tiles',String(z),String(x),`${y}.png`));
        res.writeHead(200,{'content-type':'image/png','content-length':body.length,'access-control-allow-origin':'*','x-terrain-product':bindings[0].product.id}).end(body);
      }catch{res.writeHead(404).end();}return;
    }
    const match=/^\/terrain\/(\d+)\/(\d+)\/(\d+)\.png$/.exec(req.url);
    if(!match){res.writeHead(404).end();return;}
    const [z,x,y]=match.slice(1).map(Number);
    if(!Number.isInteger(z)||z<0||z>17||x<0||y<0||x>=2**z||y>=2**z){res.writeHead(400).end();return;}
    const decision=selectTerrain(registry,{footprint:tileFootprint(z,x,y),scale:{scheme:registry.hierarchy.common.levelScheme,requestedLevel:`z${z}`},provenanceRequirement:'product-lineage',...(commonOnly?{family:registry.hierarchy.common.id}:{})});
    const record={z,x,y,decision};records.push(record);
    try{
      if(decision.status!=='selected'){res.writeHead(404).end('Explicit unavailable');return;}
      const delivery=adaptTerrainToMapLibre(registry,decision);record.delivery=delivery;
      const root=productRoots[decision.product.id];let body;
      if(root){
        if(delivery.maxzoom<z)throw new Error('Local product requires explicit renderer overzoom; endpoint cannot fabricate a level');
        body=await readFile(path.join(root,'tiles',String(z),String(x),`${y}.png`));
      }else{
        // Sole declared legacy control. Verify adapter endpoint before delegating cache/resampling.
        if(delivery.tiles[0]!=='https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png')throw new Error('Unregistered remote delivery');
        const response=await fetch(`${legacyCache}/aws/${z}/${x}/${y}.png`);if(!response.ok)throw new Error(`Legacy cache ${response.status}`);body=Buffer.from(await response.arrayBuffer());
      }
      record.status=200;record.bytes=body.length;
      res.writeHead(200,{'content-type':'image/png','content-length':body.length,'access-control-allow-origin':'*','cache-control':'public, max-age=3600','x-terrain-family':decision.family,'x-terrain-product':decision.product.id,'x-terrain-level':decision.level,'x-terrain-reason':decision.reason}).end(body);
    }catch(error){record.status=502;record.error=String(error);if(!res.headersSent)res.writeHead(502).end(String(error));}
  });
  return {records,listen:()=>new Promise(resolve=>server.listen(port,'127.0.0.1',resolve)),close:()=>new Promise(resolve=>server.close(resolve))};
}
