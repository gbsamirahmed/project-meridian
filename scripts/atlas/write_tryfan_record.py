"""Lightweight deterministic record from the retained prepared manifest."""
import argparse,json
from pathlib import Path
import riffelhorn_terrain as rt
from tryfan_product import PRODUCT
from riffelhorn_support import save

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);a=p.parse_args()
    path=a.data/PRODUCT/'manifest.json';m=json.loads(path.read_text());m['manifestSha256']=rt.digest(path);m['tileCount']=len(m.pop('files'))
    m['levels']=[{k:v for k,v in r.items() if k not in ['completeTileCoordinates','partialTiles']}|{'partialTileCount':len(r['partialTiles'])}for r in m['levels']]
    save(Path(__file__).resolve().parents[2]/'src/atlas/terrain/metadata/tryfanProductRecord.json',m)
