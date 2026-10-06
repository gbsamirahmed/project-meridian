"""Diagnostic native-support map, not an Atlas layer or semantic harmonisation."""
import argparse,json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm
from shapely.geometry import box
from shapely.geometry.polygon import orient
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch
from semantic_compare import load_features,glamos_features,patch_box,raster_points,WC
import numpy as np

def draw_polygon(ax,g,**kwargs):
    if g.is_empty:return
    if g.geom_type=='Polygon':
        g=orient(g,sign=1.0)
        paths=[]
        for ring in [g.exterior,*g.interiors]:
            xy=np.asarray(ring.coords)[:,:2]
            codes=[MplPath.MOVETO]+[MplPath.LINETO]*(len(xy)-2)+[MplPath.CLOSEPOLY]
            paths.append(MplPath(xy,codes))
        ax.add_patch(PathPatch(MplPath.make_compound_path(*paths),**kwargs))
    elif hasattr(g,'geoms'):
        for part in g.geoms:draw_polygon(ax,part,**kwargs)

def plot(root):
    plan=json.loads(Path('docs/atlas/semantic-comparison-plan.json').read_text())
    fig,axes=plt.subplots(2,2,figsize=(11,10),layout='constrained')
    cmap=ListedColormap(['white','#316b37','#b8a454','#bac388','#d3b282','#a95454','#bdbdbd','#d5e6ed','#347cad','#70a494','#336d63','#ae9eb3'])
    for row,site in enumerate(['tryfan','riffelhorn']):
        s=plan['sites'][site];reg=box(*s['bounds'])
        v,p,w,meta=raster_points(root/(site+'-worldcover.tif'),s['crs'])
        coords=np.array([q.coords[0] for q in p]);mask=reg.covers(p)
        indices=np.array([list(WC).index(int(x)) for x in v[mask]])
        axes[row,0].scatter(coords[mask,0],coords[mask,1],c=indices,cmap=cmap,vmin=-.5,vmax=11.5,marker='s',s=1,rasterized=True)
        axes[row,0].set_title(site+' — WorldCover 2021 native codes')
        ax=axes[row,1]
        if site=='tryfan':
            fs=load_features(root/'nrw-vegetation-full-features.json')
            colours={'A':'#316b37','B':'#bac388','C':'#8fbb78','D':'#bb9fb5','E':'#70a494','G':'#347cad','I':'#bdbdbd','J':'#a95454','N':'white','m':'#e6bd71'}
            for f in fs:
                g=f['geometry'].intersection(reg)
                draw_polygon(ax,g,facecolor=colours.get(f['properties']['phase1_code'][0],'white'),edgecolor='#777777',linewidth=.15)
            ax.set_title('NRW native code families / mosaic (orange) / NA (white)')
        else:
            gl=glamos_features(root,reg)
            for name,colour in [('SGI_2016_glaciers','#a9d3ef'),('SGI_2016_debriscover','#c49a6c')]:
                for f in gl[name]:draw_polygon(ax,f['geometry'].intersection(reg),facecolor=colour,edgecolor='#333333',linewidth=.4)
            for f in load_features(root/'geocover-unconsolidated.json','results'):
                draw_polygon(ax,f['geometry'].intersection(reg),facecolor='none',edgecolor='#8e467e',linewidth=.6)
            ax.set_title('SGI glacier 2015 (blue) / debris 2016 (tan); deposits outline')
        for a in axes[row,:]:
            for patch in s['patches']:
                g=patch_box(patch);draw_polygon(a,g,facecolor='none',edgecolor='black',linewidth=1.2)
                a.annotate(patch['id'],(g.bounds[0],g.bounds[3]),fontsize=7)
            a.set_xlim(s['bounds'][0],s['bounds'][2]);a.set_ylim(s['bounds'][1],s['bounds'][3]);a.set_aspect('equal');a.ticklabel_format(style='plain',useOffset=False);a.tick_params(labelsize=7)
    for ax in axes.flat:ax.title.set_fontsize(9)
    fig.set_layout_engine('constrained',rect=(0,.045,1,.94))
    fig.suptitle('Frozen source-native semantic comparison — colours are diagnostics, not equivalence')
    fig.text(.02,.003,'© ESA WorldCover 2021; modified Sentinel 2021. © NRW / OS AC0000849444. © swisstopo. GLAMOS SGI2016 r2020 CC BY4. Meridian analysis.',fontsize=6)
    fig.text(.02,.022,'WC: green tree; yellow shrub; light-green grass; grey bare/sparse; blue-white snow/ice; blue water; purple moss/lichen. White vector gaps mean no returned claim.',fontsize=6)
    path=root/'native-support.png';fig.savefig(path,dpi=170);plt.close(fig)
    print(path,hashlib.sha256(path.read_bytes()).hexdigest())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);plot(p.parse_args().data)
