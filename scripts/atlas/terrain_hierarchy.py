"""Bounded tile hierarchy: native heights, exact preferred tiles, no fusion.

This evaluation entry point is never imported by normal application code.
"""
import argparse
from functools import lru_cache
from io import BytesIO
import json
from pathlib import Path
import re
import threading
from PIL import Image
import numpy as np
import copernicus_common as cp
import riffelhorn_support as sp
import riffelhorn_terrain as rt

VERSION='riffelhorn-terrain-hierarchy-v1'
PRODUCT='derived/atlas/riffelhorn/'+VERSION
EXPERIMENT='experiments/atlas/'+VERSION
REPO=Path(__file__).resolve().parents[2]
POLICY=REPO/'docs/atlas/terrain-hierarchy-policy.json'

def select(strategy,z,swiss_available,gate):
    if strategy not in ['common','H0','H1']:raise ValueError('Unknown strategy')
    return int(swiss_available and strategy!='common' and (strategy=='H0' or z>=gate))

def overzoom(padded,z,x,y):
    """Bilinear cell-centred sampling of encoded z13 signal; never adds detail."""
    factor=2**(z-13)
    xx=((x%factor)*256+(np.arange(256)+.5))/factor-.5+1
    yy=((y%factor)*256+(np.arange(256)+.5))/factor-.5+1
    ix=np.floor(xx).astype(int);iy=np.floor(yy).astype(int)
    wx=xx-ix;wy=yy-iy
    return ((1-wy[:,None])*((1-wx)*padded[iy[:,None],ix]+wx*padded[iy[:,None],ix+1])+wy[:,None]*((1-wx)*padded[iy[:,None]+1,ix]+wx*padded[iy[:,None]+1,ix+1]))

class Hierarchy:
    def __init__(self,data,gate=14,suffix='',verify=True):
        self.data=data;self.gate=gate;self.out=data/(PRODUCT+suffix);self.lock=threading.RLock()
        self.common=cp.verify(data)if verify else json.loads((data/cp.PRODUCT/'manifest.json').read_text())
        self.swiss=sp.verify(data)if verify else json.loads((data/sp.PRODUCT/'manifest.json').read_text())
        expected=json.loads((REPO/'docs/atlas/terrain-hierarchy-plan.json').read_text())['products']
        if expected!={'common':self.common['identity'],'swiss':self.swiss['identity']}:raise ValueError('Frozen parent mismatch')
        self.swiss_files={f['path']:f for f in self.swiss['files']};self.common_files={f['path']:f for f in self.common['files']}
        self.config={'version':VERSION,'parents':expected,'height':'native heterogeneous LN02 / EGM2008, no correction or blending','gate':gate,'toolSha256':rt.repository_text_digest(__file__),'delivery':'XYZ Mercator 256px Terrarium z8-18; common above13 explicitly bilinear overzoom','support':'Swiss complete per-level delivery inventory; no coverage implied by fallback'}
        self.config['identity']=rt.stable_id(self.config)
        self.out.mkdir(parents=True,exist_ok=True)
        old=self.out/'build.json'
        if old.exists()and json.loads(old.read_text())!=self.config:raise ValueError('Immutable configuration changed; separate named sibling required')
        sp.save(old,self.config)

    @lru_cache(maxsize=128)
    def common_array(self,x,y):
        row=self.common_files.get(f'tiles/13/{x}/{y}.png')
        if not row:raise FileNotFoundError('Outside finite common support')
        p=self.data/cp.PRODUCT/row['path']
        if rt.digest(p)!=row['sha256']:raise ValueError('Common input drift')
        return rt.decode(p.read_bytes())

    def padded(self,x,y):
        a=self.common_array(x,y);result=np.pad(a,1,mode='edge')
        # MapLibre also backfills adjacent DEM samples. Clamp only at the finite
        # common product perimeter, never synthesize absent land/ocean terrain.
        for dx,dy in [(dx,dy)for dx in [-1,0,1]for dy in [-1,0,1]if dx or dy]:
            if f'tiles/13/{x+dx}/{y+dy}.png'not in self.common_files:continue
            b=self.common_array(x+dx,y+dy)
            rs=slice(0,1)if dy<0 else slice(257,258)if dy>0 else slice(1,257)
            cs=slice(0,1)if dx<0 else slice(257,258)if dx>0 else slice(1,257)
            br=slice(255,256)if dy<0 else slice(0,1)if dy>0 else slice(0,256)
            bc=slice(255,256)if dx<0 else slice(0,1)if dx>0 else slice(0,256)
            result[rs,cs]=b[br,bc]
        return result

    def tile(self,strategy,z,x,y):
        if not 8<=z<=18:raise FileNotFoundError('No lower/global or higher hierarchy support')
        cx,cy=x//2**max(0,z-13),y//2**max(0,z-13)
        key=f'tiles/{z}/{x}/{y}.png'
        if (z<=13 and key not in self.common_files)or(z>13 and f'tiles/13/{cx}/{cy}.png'not in self.common_files):raise FileNotFoundError('Outside finite context')
        label=select(strategy,z,key in self.swiss_files,self.gate)
        leaf=f'{strategy}/{z}/{x}/{y}'
        p=self.out/f'tiles/{leaf}.png';receipt=self.out/f'receipts/{leaf}.json'
        with self.lock:
            if p.exists():
                row=json.loads(receipt.read_text());body=p.read_bytes()
                if row['configIdentity']!=self.config['identity']or rt.digest(p)!=row['sha256']or row['contributor']!=label:raise ValueError('Cached tile drift')
                return body,row
            if label:
                src=self.data/sp.PRODUCT/key;row=self.swiss_files[key]
                if rt.digest(src)!=row['sha256']:raise ValueError('Swiss input drift')
                body=src.read_bytes();method='exact Swiss delivery bytes'
            elif z<=13:
                src=self.data/cp.PRODUCT/key;row=self.common_files[key]
                if rt.digest(src)!=row['sha256']:raise ValueError('Common input drift')
                body=src.read_bytes();method='exact common delivery bytes'
            else:
                body=rt.encode(overzoom(self.padded(cx,cy),z,x,y));method='cell-centred bilinear z13 encoded common signal; independent Terrarium re-encoding'
            mask=self.out/f'contributors/{leaf}.png';mask.parent.mkdir(parents=True,exist_ok=True)
            Image.fromarray(np.full((256,256),label,dtype='uint8')).save(mask,compress_level=6)
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
            row={'strategy':strategy,'z':z,'x':x,'y':y,'contributor':label,'heightReference':'LN02'if label else 'EGM2008','method':method,'configIdentity':self.config['identity'],'path':p.relative_to(self.out).as_posix(),'sha256':rt.digest(p),'bytes':len(body),'maskPath':mask.relative_to(self.out).as_posix(),'maskSha256':rt.digest(mask)}
            sp.save(receipt,row);return body,row

    def inventory(self):
        rows=[]
        for p in sorted((self.out/'receipts').rglob('*.json')):
            row=json.loads(p.read_text());tile=self.out/row['path'];mask=self.out/row['maskPath']
            if rt.digest(tile)!=row['sha256']or rt.digest(mask)!=row['maskSha256']or not np.all(np.asarray(Image.open(mask))==row['contributor']):raise ValueError('Contributor inventory drift')
            rows.append(row)
        value={'config':self.config,'files':rows,'coverage':'Sparse evaluated tile inventory within finite common parents, not full z8-18 generation','maskLabels':{'0':'Copernicus EGM2008','1':'swissALTI3D LN02'},'weights':'No blended cells. Labels are contributor identity, not confidence.'}
        value['identity']=rt.stable_id(value);sp.save(self.out/'manifest.json',value);return value

def serve(h,port):
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            match=re.fullmatch(r'/tiles/(common|H0|H1)/(\d+)/(\d+)/(\d+)\.png',self.path)
            try:
                if not match:raise FileNotFoundError('Unsupported path')
                body,row=h.tile(match[1],*map(int,match.groups()[1:]));status=200
            except FileNotFoundError:body=b'';row={};status=404
            except Exception as e:print('TILE ERROR',repr(e),flush=True);body=b'';row={};status=500
            self.send_response(status);self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Expose-Headers','X-Meridian-Contributor,X-Meridian-Height,X-Meridian-Build')
            self.send_header('Cache-Control','public,max-age=3600'if status==200 else 'no-store');self.send_header('Content-Type','image/png');self.send_header('Content-Length',str(len(body)))
            if row:
                self.send_header('X-Meridian-Contributor',str(row['contributor']));self.send_header('X-Meridian-Height',row['heightReference']);self.send_header('X-Meridian-Build',h.config['identity'])
            self.end_headers()
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
        def log_message(self,*args):pass
    print('SERVING',port,h.config['identity'],flush=True)
    try:ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
    finally:h.inventory()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['serve','inventory']);p.add_argument('--gate',type=int,default=14);p.add_argument('--port',type=int,default=4183);p.add_argument('--suffix',default='');a=p.parse_args()
    if a.gate not in range(12,19)or(a.suffix and not re.fullmatch(r'-[a-z0-9-]+',a.suffix)):raise ValueError('Bounded gate/named sibling only')
    h=Hierarchy(rt.resolve_storage_roots(require_data=True).data,a.gate,a.suffix)
    if a.command=='serve':serve(h,a.port)
    else:print('INVENTORY',h.inventory()['identity'])
