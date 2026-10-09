"""Fixed-operation whole-core longitude enclosure, not a replacement CRS engine."""
import math
import pyproj
pyproj.network.set_network_enabled(False)

WINDOW = [2554, 0, 366, 3600]
PIPELINE = "proj=pipeline step inv proj=somerc lat_0=46.9524055555556 lon_0=7.43958333333333 k_0=1 x_0=2600000 y_0=1200000 ellps=bessel step proj=push v_3 step proj=cart ellps=bessel step proj=helmert x=674.374 y=15.056 z=405.346 step inv proj=cart ellps=WGS84 step proj=pop v_3 step proj=unitconvert xy_in=rad xy_out=deg"


def derive():
    # Query geometries are intersected with the core BEFORE this native conversion.
    # Enclose the entire rectangle with a metre of arithmetic/clipping guard.
    x0, x1 = 23999, 26001
    y0, y1 = -109001, -106999
    a = 6377397.155; f = 1 / 299.1528128
    es = f * (2-f); e = math.sqrt(es); phi0 = math.radians(46.9524055555556)
    c = math.sqrt(1 + es * math.cos(phi0)**4 / (1-es))
    p0 = math.asin(math.sin(phi0)/c)
    R = a*math.sqrt(1-es)/(1-es*math.sin(phi0)**2)
    F = lambda p: math.log(math.tan(math.pi/4+p/2))-e/2*math.log((1+e*math.sin(p))/(1-e*math.sin(p)))
    K = math.log(math.tan(math.pi/4+p0/2))-c*F(phi0)
    assert 6300000 < R < 6500000 and 1 < c < 1.01
    assert .72 < math.sin(p0) < .74 and .67 < math.cos(p0) < .70
    u0,u1 = y0/6300000,y1/6500000
    s0,s1 = math.tanh(u0),math.tanh(u1)
    assert -.0174 < s0 <= s1 < -.0164
    assert math.sqrt(1-s0*s0) > .9998 and math.cos(x1/6300000) > .99999
    z0,z1 = .70*s0+.72*.9998*.99999, .67*s1+.74
    assert .68 < math.sqrt(1-z1*z1) <= math.sqrt(1-z0*z0) < .71
    l0 = math.asin(.9998*math.sin(x0/6500000)/.71)/1.01
    l1 = math.asin(math.sin(x1/6300000)/.68)
    b0,b1 = 7.43958333333333+math.degrees(l0),7.43958333333333+math.degrees(l1)
    t0,t1 = (math.log(math.tan(math.pi/4+math.asin(z0)/2))-K)/c,(math.log(math.tan(math.pi/4+math.asin(z1)/2))-K)/c
    # F'=(1-e²)/(cos(phi)*(1-e²*sin²(phi))) > 0: unique inverse root.
    assert F(math.radians(40)) < t0 < t1 < F(math.radians(60))
    # Bessel zero-height Cartesian horizontal radius >= a*cos(60) > 3.15 Mm.
    # An XY translation of norm T turns that vector by at most asin(T/r).
    delta = math.degrees(math.asin(math.hypot(674.374,15.056)/(6300000*.5)))
    assert 7.71 < b0-delta and b1+delta < 7.81
    tr=pyproj.Transformer.from_crs('EPSG:2056','EPSG:4326',always_xy=True)
    if pyproj.proj_version_str != '9.5.1' or tr.definition != PIPELINE:
        raise ValueError('Closure needs review for this PROJ version/operation; no sampled fallback.')
    return {'proof':'whole-core-longitude-strip/v1','operation':PIPELINE,'proj':'9.5.1',
            'core':[2624000,1091000,2626000,1093000],'inputGuardMetres':1,
            'besselLongitudeEnclosure':[b0,b1],'translationAngleDegrees':delta,
            'reservedLongitudeDegrees':[7.71,7.81],'sourceWindow':WINDOW,
            'rows':'all source rows retained; no latitude/corner-extremum approximation'}

if __name__=='__main__':
    import json
    print(json.dumps(derive(),sort_keys=True,indent=2))
