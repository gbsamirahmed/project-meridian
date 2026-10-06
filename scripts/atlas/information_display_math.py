"""Research-only local sampling math. No production policy or data processing."""
import math
import numpy as np
R=6378137.0
WORLD=2*math.pi*R

def metres_per_pixel(latitude,zoom,tile_size=512):
    if abs(latitude)>85.0511287798066 or tile_size<=0:raise ValueError('Invalid Mercator scale')
    return WORLD*math.cos(math.radians(latitude))/(tile_size*2**zoom)

def applied_ratio(css,backing):
    if any(v<=0 for v in [*css,*backing]):raise ValueError('Invalid raster size')
    return [backing[i]/css[i] for i in range(2)]

def enu(origin,point,exaggeration=1):
    if exaggeration<=0:raise ValueError('Invalid exaggeration')
    if any(v is None or not math.isfinite(v) for v in [*origin,*point]):raise ValueError('Unavailable coordinates')
    return np.array([(point[0]-origin[0])*math.pi/180*R*math.cos(math.radians(origin[1])),(point[1]-origin[1])*math.pi/180*R,(point[2]-origin[2])/exaggeration])

def jacobian(origin,stencil,exaggeration=1):
    h=stencil['step']
    if h<=0:raise ValueError('Invalid finite-difference step')
    vector=lambda key:enu(origin,stencil[key]['xyz'],exaggeration)
    return np.column_stack([(vector('east')-vector('west'))/(2*h),(vector('south')-vector('north'))/(2*h)])

def singular(matrix):return np.linalg.svd(matrix,compute_uv=False).tolist()

def footprint(j,ratio=(1,1)):
    if np.shape(j)!=(3,2) or any(v<=0 for v in ratio):raise ValueError('Invalid footprint')
    a=j[:2,:];s=singular(j);sa=singular(a)
    if sa[1]<=1e-12:raise ValueError('Singular map-plane mapping')
    gradient=np.linalg.solve(a.T,j[2,:]);normal=np.array([-gradient[0],-gradient[1],1]);normal/=np.linalg.norm(normal)
    stretch=math.sqrt(1+float(gradient@gradient));slope=math.degrees(math.atan(math.sqrt(float(gradient@gradient))))
    return {'jacobianMetresPerCssPixel':j.tolist(),'mapPrincipalMetresPerCssPixel':sa,'surfacePrincipalMetresPerCssPixel':s,'surfacePrincipalMetresPerFramebufferPixel':singular(j@np.diag(1/np.asarray(ratio))),'mapPrincipalMetresPerFramebufferPixel':singular(a@np.diag(1/np.asarray(ratio))),'physicalGradientEN':gradient.tolist(),'normalENU':normal.tolist(),'slopeDegrees':slope,'downslopeAspectDegrees':None if slope<1e-9 else math.degrees(math.atan2(-gradient[0],-gradient[1]))%360,'mapToSurfacePrincipalStretch':[stretch,1],'surfaceAreaPerCssPixel':float(np.prod(s)),'mapCondition':sa[0]/sa[1]}

def sample_projection(j,spacing,ratio=(1,1)):
    """Isotropic local map-plane grid spacing; no optical/acquisition model."""
    if spacing<=0:raise ValueError('Invalid sample spacing')
    a=j[:2,:];forward=np.linalg.inv(a)*spacing
    return {'mapPlaneSpacingMetres':spacing,'cssPixelsPerSamplePrincipal':singular(forward),'framebufferPixelsPerSamplePrincipal':singular(np.diag(ratio)@forward),'samplesPerFramebufferPixelPrincipal':singular(a@np.diag(1/np.asarray(ratio))/spacing)}

def wavelength_projection(j,wavelength,ratio=(1,1)):
    if wavelength<=0:raise ValueError('Invalid wavelength')
    a=singular(j);b=singular(j@np.diag(1/np.asarray(ratio)))
    return {'surfaceWavelengthMetres':wavelength,'projectedCssPixelRange':[wavelength/a[0],wavelength/a[1]],'projectedFramebufferPixelRange':[wavelength/b[0],wavelength/b[1]]}

def containing_tile(tiles,location):
    found=[]
    for t in tiles or []:
        if t is None:continue
        z=t['z'];x=(location[0]+180)/360*2**z;y=(1-math.asinh(math.tan(math.radians(location[1])))/math.pi)/2*2**z
        if t['x']<=x<t['x']+1 and t['y']<=y<t['y']+1:found.append(t)
    return max(found,key=lambda t:t['z']) if found else None
