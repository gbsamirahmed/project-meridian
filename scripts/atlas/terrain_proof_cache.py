"""Loopback-only legacy AWS control/overzoom cache, not terrain reconciliation."""
import argparse,re
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import numpy as np
import riffelhorn_terrain as rt

def serve(root,port):
    cache=rt.AwsCache(root)
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            match=re.fullmatch(r'/aws/(\d+)/(\d+)/(\d+)\.png',self.path)
            if not match:self.send_error(404);return
            z,x,y=map(int,match.groups())
            if not 0<=z<=17 or not 0<=x<2**z or not 0<=y<2**z:self.send_error(400);return
            try:
                if z<=15:
                    cache.tile(z,x,y);body=(Path(root)/f'{z}/{x}/{y}.png').read_bytes()
                else:
                    # Explicit rendering overzoom of legacy z15. Not new observations.
                    f=2**(15-z);i,j=np.meshgrid(np.arange(256),np.arange(256));a=cache.sample_pixels(15,(x*256+i+.5)*f-.5,(y*256+j+.5)*f-.5);body=rt.encode(a)
                self.send_response(200);self.send_header('Content-Type','image/png');self.send_header('Content-Length',str(len(body)));self.send_header('Access-Control-Allow-Origin','*');self.end_headers();self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
            except Exception as e:self.send_error(502,str(e))
        def log_message(self,*args):pass
    print('CACHE',port,flush=True);ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--port',type=int,default=4187);a=p.parse_args();serve(a.root,a.port)
