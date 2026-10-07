// Read-only, loopback-only S4 transport; no source selection or publication here.
import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { performance } from 'node:perf_hooks';
import { openDelivery } from './delivery.mjs';
import { encode,requireThat } from './identity.mjs';
const staticFiles=new Map([['/','index.html'],['/client/view.mjs','view.mjs']]);
const bad=['invalid-request','invalid-coordinate','invalid-crs','invalid-support','invalid-policy','invalid-reference','invalid-generation-id'];
const missing=['generation-missing','reference-missing','asset-missing','historical-result-missing'];
export async function startServer({port=4191,...options}={}) {
 const start=performance.now(),delivery=await openDelivery(options),first=await delivery.pin();
 const metrics={requests:0,errors:0,responses:[],startupMilliseconds:performance.now()-start};
 const server=createServer(async(req,res)=>{
  const began=performance.now();metrics.requests++;let body;
  function send(code,value,mime='application/json',headers={}) {
   body=Buffer.isBuffer(value)?value:Buffer.from(typeof value==='string'?value:encode(value));
   res.writeHead(code,{'Content-Type':mime,'Content-Length':body.length,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',...headers});res.end(body);
   if(metrics.responses.length<1000)metrics.responses.push({status:code,bytes:body.length,milliseconds:performance.now()-began});
  }
  try {
   const path=new URL(req.url,'http://127.0.0.1').pathname;
   requireThat(!req.headers.origin || req.headers.origin===`http://127.0.0.1:${server.address().port}`,'invalid-request','Same-origin local consumer required');
   if(req.method==='GET' && staticFiles.has(path)){send(200,readFileSync(join(import.meta.dirname,'client',staticFiles.get(path))),path==='/'?'text/html; charset=utf-8':'text/javascript; charset=utf-8',{'Content-Security-Policy':"default-src 'self'; connect-src 'self'; img-src 'self' blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; object-src 'none'; base-uri 'none'"});return;}
   if(req.method==='GET' && path==='/pilot/v1/current'){send(200,await delivery.pin());return;}
   const match=path.match(/^\/pilot\/v1\/g\/([a-f0-9]{64})\/(manifest|query|provenance\/([a-f0-9]{64})|assets\/([a-f0-9]{64})|terrain\/(terrain-common|terrain-regional)\/(\d+)\/(\d+)\/(\d+)\.png)$/);
   requireThat(match,'asset-missing','Unknown pilot route');
   const [,g,operation,reference,asset,family,z,x,y]=match;
   if(operation==='query') {
    requireThat(req.method==='POST' && req.headers['content-type']?.split(';')[0]==='application/json','invalid-request','Read query requires POST JSON');
    let size=0,chunks=[];for await(const c of req){size+=c.length;requireThat(size<=65536,'invalid-request','Query body exceeds64 KiB');chunks.push(c);}
    let request;try{request=JSON.parse(Buffer.concat(chunks).toString('utf8'));}catch{requireThat(false,'invalid-request','Malformed query JSON');}
    const answer=await delivery.query(g,request);send(answer.status==='unavailable'?503:200,answer);return;
   }
   requireThat(req.method==='GET','invalid-request','Read-only GET required');
   if(operation==='manifest')send(200,await delivery.manifest(g));
   else if(reference)send(200,await delivery.provenance(g,reference));
   else {
    const r=await delivery.bytes(g,asset,family?{family,z:+z,x:+x,y:+y}:undefined);
    const headers={ETag:'"'+r.sha256+'"','Cache-Control':'private, max-age=31536000, immutable',Link:'<'+r.rightsURL+'>; rel="license"','X-Atlas-Generation':g};
    // Reverify bytes even for a conditional/cache response; external mutation is not accepted.
    if(req.headers['if-none-match']===headers.ETag){res.writeHead(304,headers);res.end();}else send(200,r.body,r.mime,headers);
   }
  }catch(e){metrics.errors++;send(bad.includes(e.code)?400:missing.includes(e.code)?404:503,{protocol:'atlas-tryfan-serving/v1',error:{code:e.code??'serving-unavailable',message:bad.includes(e.code)?e.message:'Requested qualified state/address is unavailable; inspect local developer diagnostics.'}});}
 });
 server.keepAliveTimeout=60000;server.keepAliveTimeoutBuffer=1000;
 server.requestTimeout=30000;server.headersTimeout=10000;
 await new Promise((r,j)=>{server.once('error',j);server.listen(port,'127.0.0.1',r);});
 return {url:'http://127.0.0.1:'+server.address().port,initialGeneration:first.generation,metrics,delivery,
  close:async()=>{await new Promise(r=>{server.close(r);server.closeIdleConnections();});await delivery.close();}};
}
if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href) {
 const args=process.argv.slice(2),options={};for(let i=0;i<args.length;i+=2){const k=args[i];requireThat(['--port','--store','--data-root'].includes(k)&&args[i+1],'invalid-request','Explicit server options required');options[k==='--port'?'port':k==='--store'?'store':'dataRoot']=k==='--port'?Number(args[i+1]):args[i+1];}
 const s=await startServer(options);console.log(encode({url:s.url,generation:s.initialGeneration}).trim());
 const stop=async()=>{await s.close();process.exit(0);};process.on('SIGTERM',stop);process.on('SIGINT',stop);
}
