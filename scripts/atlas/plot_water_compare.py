"""Small native-claim support map; colours do not establish semantic equivalence."""
import argparse,json
from pathlib import Path
import numpy as np,rasterio,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch,Rectangle
from matplotlib.colors import ListedColormap,BoundaryNorm
from pyproj import Transformer
from shapely.geometry import box
from shapely.geometry.polygon import orient
from water_compare import read_vectors,native_codes

def draw(ax,g,color,alpha=1):
 if g.is_empty:return
 if g.geom_type=='Polygon':
  g=orient(g,sign=1);verts=[];codes=[]
  for ring in [g.exterior,*g.interiors]:
   v=list(ring.coords);verts.extend(v);codes.extend([MPath.MOVETO]+[MPath.LINETO]*(len(v)-2)+[MPath.CLOSEPOLY])
  ax.add_patch(PathPatch(MPath(verts,codes),facecolor=color,edgecolor='none',alpha=alpha))
 elif hasattr(g,'geoms'):
  for h in g.geoms:draw(ax,h,color,alpha)

def main(root,out):
 p=json.loads(Path('docs/atlas/water-check-plan.json').read_text());b=box(*p['bounds']);fs={k:read_vectors(root,k) for k in ['wfd','phi','flood','rfo']};fig,axs=plt.subplots(2,3,figsize=(12,8),layout='constrained')
 for ax in axs.flat:
  ax.set_xlim(p['bounds'][0],p['bounds'][2]);ax.set_ylim(p['bounds'][1],p['bounds'][3]);ax.set_aspect('equal');ax.ticklabel_format(style='plain',useOffset=False);ax.tick_params(labelsize=7)
  for q in p['probes']:
   x,y,x2,y2=q['bounds'];ax.add_patch(Rectangle((x,y),x2-x,y2-y,fill=False,edgecolor='black',lw=.6,zorder=8));ax.text(x2+12,y2,q['id'],fontsize=7,zorder=9)
 for g,_ in fs['wfd']:draw(axs[0,0],g.intersection(b),'#9abacb')
 axs[0,0].set_title('WFD EXE: MHW-derived assessment boundary',fontsize=9)
 colors={'MUDFL':'#bdaf94','CFPGM':'#a5bd78','SALTM':'#bc93b4','RBEDS':'#68855e','LFENS':'#75a997'}
 for g,v in fs['phi']:
  codes=native_codes(v['habcodes']);draw(axs[0,1],g.intersection(b),colors.get(codes[0],'#dedede'))
 axs[0,1].set_title('PHI: habitats (mixed codes retained in JSON)',fontsize=9)
 for g,v in fs['flood']:draw(axs[0,2],g.intersection(b),'#96c3de' if v['flood_zone']=='FZ2' else '#536d99')
 axs[0,2].set_title('Planning zones: FZ2 light / FZ3 dark',fontsize=9)
 for ax,name,title in [(axs[1,0],'monthly-2024-03','March 2024 detection'),(axs[1,1],'monthly-2024-09','September 2024 detection')]:
  with rasterio.open(root/(name+'.tif')) as src:
   a=src.read(1);yy,xx=np.indices((src.height+1,src.width+1));lon,lat=src.transform*(xx,yy);x,y=Transformer.from_crs(4326,27700,always_xy=True).transform(lon,lat)
   ax.pcolormesh(x,y,a,cmap=ListedColormap(['#b8b8b8','#fafafa','#468aba']),norm=BoundaryNorm([-.5,.5,1.5,2.5],3),shading='flat',rasterized=True)
  ax.set_title(title+' (grey unobserved, blue detected)',fontsize=9)
 for g,v in fs['rfo']:draw(axs[1,2],g.intersection(b),'#bc6852',.18)
 axs[1,2].set_title('RFO: overlapping historical event records',fontsize=9)
 fig.suptitle('Upper Exe fixed probes: distinct native propositions, not simultaneous truth',fontsize=12)
 fig.supxlabel('British National Grid eastings / northings (metres). Source: EA / NE / OS; EC JRC/Google. See rights manifest.',fontsize=8)
 fig.savefig(out,dpi=110,metadata={'Software':'Meridian water-check-v1'});plt.close(fig)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.data,a.out)
