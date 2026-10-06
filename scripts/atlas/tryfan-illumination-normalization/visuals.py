"""Matched spatial baseline diagnostics only; no corrected pixels after failed gate."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path(__file__).resolve().parents[3]/'docs/research'

def generate(arrays,result):
    rgb,scl,mu,eligible,blocked,horizon=arrays
    fig,axes=plt.subplots(2,3,figsize=(10,6),constrained_layout=True)
    titles=['Unchanged L2A RGB (fixed010 transfer)','Source SCL:2 shadow,4 vegetation,5 not-vegetated','Local incidence mu (documented mean Sun)','Eligible cells (9242); excluded remain source','Model blockers within1km (132); not shadow truth','Fixed500m folds: eligible SCL4 / SCL5']
    display=np.clip((rgb-.02)/.28,0,1)
    axes[0,0].imshow(display,interpolation='nearest')
    from matplotlib.colors import ListedColormap,BoundaryNorm
    classv=np.where(scl==2,0,np.where(scl==4,1,2));axes[0,1].imshow(classv,cmap=ListedColormap(['#333333','#4c9954','#c3aa73']),vmin=0,vmax=2,interpolation='nearest')
    im=axes[0,2].imshow(mu,cmap='viridis',vmin=0,vmax=1,interpolation='nearest');fig.colorbar(im,ax=axes[0,2],shrink=.7)
    axes[1,0].imshow(eligible,cmap='gray',vmin=0,vmax=1,interpolation='nearest')
    axes[1,1].imshow(blocked,cmap=ListedColormap(['#dddddd','#81227c']),vmin=0,vmax=1,interpolation='nearest')
    axes[1,2].imshow(display,interpolation='nearest');axes[1,2].axhline(49.5,c='yellow',lw=1);axes[1,2].axvline(49.5,c='yellow',lw=1)
    for i,name in enumerate(['NW','NE','SW','SE']):
        row=[v for v in result['gate']['folds'] if v['heldout']==name]
        x=24.5 if i%2==0 else 74.5;y=24.5 if i<2 else 74.5
        axes[1,2].text(x,y,f'{name}\n{row[0]["heldoutCells"]} / {row[1]["heldoutCells"]}',ha='center',va='center',color='white',bbox={'facecolor':'black','alpha':.65,'pad':2})
    for ax,title in zip(axes.ravel(),titles):
        ax.set_title(title,fontsize=8);ax.set_xticks([]);ax.set_yticks([])
    fig.suptitle('Tryfan frozen1km core, north up: INCONCLUSIVE before correction (SE SCL5:12<20)',fontsize=11)
    fig.savefig(OUT/'tryfan-illumination-normalization-baseline.png',dpi=120,metadata={'Software':'Meridian retained baseline/v1'});plt.close(fig)
    fig,axes=plt.subplots(2,4,figsize=(10,5),constrained_layout=True)
    yy,xx=np.indices((100,100));fold=(yy>=50)*2+(xx>=50)
    bright=rgb@np.array([.2126,.7152,.0722])
    for r,cls in enumerate([4,5]):
        for c,name in enumerate(['NW','NE','SW','SE']):
            m=eligible&(scl==cls)&(fold==c)
            axes[r,c].scatter(mu[m],bright[m],s=2,alpha=.3,c='#25415b',rasterized=True)
            axes[r,c].set_xlim(.3,1);axes[r,c].set_ylim(0,.2);axes[r,c].set_title(f'SCL{cls} {name}, n={m.sum()}',fontsize=9)
            axes[r,c].set_xlabel('mu',fontsize=8)
            if c==0:axes[r,c].set_ylabel('Unchanged RGB brightness',fontsize=8)
    fig.suptitle('Baseline only: identical axes; covariance does not identify illumination cause',fontsize=11)
    fig.savefig(OUT/'tryfan-illumination-normalization-association.png',dpi=120,metadata={'Software':'Meridian retained baseline/v1'});plt.close(fig)
