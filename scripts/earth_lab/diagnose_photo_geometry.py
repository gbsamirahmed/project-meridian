"""Generate plan/profile diagnostics for an Earth Lab photographic benchmark.

This is a read-only analysis of a source DTM. It does not inspect or modify Unreal.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import LightSource
from pyproj import Geod, Transformer


@dataclass(frozen=True)
class Profile:
    name: str
    distances_m: np.ndarray
    eastings: np.ndarray
    northings: np.ndarray
    elevations_m: np.ndarray
    target_distance_m: float | None = None


def bilinear_sample(data, transform, eastings, northings):
    """Sample a north-up raster at BNG coordinates using pixel-centre bilinear interpolation."""
    cols = (eastings - transform.c) / transform.a - 0.5
    rows = (northings - transform.f) / transform.e - 0.5
    if np.any(cols < 0) or np.any(rows < 0) or np.any(cols > data.shape[1] - 1) or np.any(rows > data.shape[0] - 1):
        raise ValueError("Requested profile leaves the source DTM")
    c0 = np.floor(cols).astype(int)
    r0 = np.floor(rows).astype(int)
    c1 = np.minimum(c0 + 1, data.shape[1] - 1)
    r1 = np.minimum(r0 + 1, data.shape[0] - 1)
    fc = cols - c0
    fr = rows - r0
    return (data[r0,c0]*(1-fr)*(1-fc)+data[r0,c1]*(1-fr)*fc+data[r1,c0]*fr*(1-fc)+data[r1,c1]*fr*fc).astype(float)


def bng_bearing_distance(start_e, start_n, end_e, end_n):
    de, dn = end_e - start_e, end_n - start_n
    return math.degrees(math.atan2(de, dn)) % 360.0, math.hypot(de, dn)


def profile_between(name, start, end, data, transform, spacing_m=1.0):
    _, length = bng_bearing_distance(*start, *end)
    distances = np.linspace(0.0, length, max(2, int(math.ceil(length / spacing_m)) + 1))
    fraction = distances / length
    eastings = start[0] + (end[0] - start[0]) * fraction
    northings = start[1] + (end[1] - start[1]) * fraction
    return Profile(name, distances, eastings, northings, bilinear_sample(data, transform, eastings, northings), length)


def heading_profile(name, start_wgs84, heading_degrees, bounds, data, transform, to_bng, geod, spacing_m=1.0, maximum_m=5000.0):
    latitude, longitude = start_wgs84
    trial = np.arange(0.0, maximum_m + spacing_m, spacing_m)
    positions = [geod.fwd(longitude, latitude, heading_degrees, float(distance)) for distance in trial]
    lons = np.array([position[0] for position in positions])
    lats = np.array([position[1] for position in positions])
    eastings, northings = to_bng.transform(lons, lats)
    west, south, east, north = bounds
    inside = (eastings >= west + 0.5) & (eastings <= east - 0.5) & (northings >= south + 0.5) & (northings <= north - 0.5)
    outside = np.flatnonzero(~inside)
    end_index = int(outside[0] - 1) if outside.size else len(trial) - 1
    if end_index < 2:
        raise ValueError("Published heading exits the AOI immediately")
    distances = trial[:end_index+1]
    eastings, northings = eastings[:end_index+1], northings[:end_index+1]
    return Profile(name, distances, eastings, northings, bilinear_sample(data, transform, eastings, northings))


def smooth(values, window=11):
    kernel = np.ones(window, dtype=float) / window
    padded = np.pad(values, (window // 2, window // 2), mode="edge")
    return np.convolve(padded, kernel, mode="valid")[:len(values)]


def local_ridges(profile, minimum_prominence_m=3.0):
    values, candidates, flank = smooth(profile.elevations_m), [], 50
    for index in range(flank, len(values) - flank):
        if values[index] < values[index-1] or values[index] <= values[index+1]:
            continue
        left_low = float(np.min(values[index-flank:index]))
        right_low = float(np.min(values[index+1:index+flank+1]))
        prominence = float(values[index] - max(left_low, right_low))
        if prominence >= minimum_prominence_m:
            candidates.append((prominence, index))
    selected = []
    for prominence, index in sorted(candidates, reverse=True):
        if all(abs(profile.distances_m[index] - profile.distances_m[other]) >= 50.0 for _, other in selected):
            selected.append((prominence, index))
        if len(selected) == 6:
            break
    return [{"distance_m":float(profile.distances_m[i]),"elevation_m_odn":float(profile.elevations_m[i]),"easting":float(profile.eastings[i]),"northing":float(profile.northings[i]),"prominence_m_approximately":float(p)} for p,i in sorted(selected,key=lambda item:item[1])]


def line_of_sight(profile, eye_height_m):
    if profile.target_distance_m is None:
        raise ValueError("Line-of-sight analysis requires a target profile")
    eye = float(profile.elevations_m[0] + eye_height_m)
    target = float(profile.elevations_m[-1])
    sightline = eye + (target-eye) * (profile.distances_m/profile.target_distance_m)
    clearance = profile.elevations_m - sightline
    interior = np.arange(1,len(clearance)-1)
    max_index = int(interior[np.argmax(clearance[interior])])
    terrain_angles = np.degrees(np.arctan2(profile.elevations_m[1:-1]-eye,profile.distances_m[1:-1]))
    horizon_index = int(np.argmax(terrain_angles))+1
    return {
      "eye_elevation_m_odn":eye,
      "target_elevation_m_odn":target,
      "target_elevation_angle_degrees":math.degrees(math.atan2(target-eye,profile.target_distance_m)),
      "maximum_intervening_clearance_above_sightline_m":float(clearance[max_index]),
      "maximum_clearance_point":{"distance_m":float(profile.distances_m[max_index]),"elevation_m_odn":float(profile.elevations_m[max_index]),"easting":float(profile.eastings[max_index]),"northing":float(profile.northings[max_index])},
      "maximum_intervening_terrain_angle_degrees":float(terrain_angles[horizon_index-1]),
      "intervening_horizon_point":{"distance_m":float(profile.distances_m[horizon_index]),"elevation_m_odn":float(profile.elevations_m[horizon_index]),"easting":float(profile.eastings[horizon_index]),"northing":float(profile.northings[horizon_index])},
      "line_of_sight_clear":bool(clearance[max_index] <= 0.25),
      "clearance_tolerance_m":0.25,
    }


def open_ray_horizon(profile, eye_height_m):
    eye = float(profile.elevations_m[0]+eye_height_m)
    angles = np.degrees(np.arctan2(profile.elevations_m[1:]-eye,profile.distances_m[1:]))
    index = int(np.argmax(angles))+1
    return {"eye_elevation_m_odn":eye,"maximum_terrain_angle_degrees":float(angles[index-1]),"horizon_distance_m":float(profile.distances_m[index]),"horizon_elevation_m_odn":float(profile.elevations_m[index]),"horizon_easting":float(profile.eastings[index]),"horizon_northing":float(profile.northings[index])}


def grid_ray(start, grid_bearing_degrees, length_m, data, transform):
    radians = math.radians(grid_bearing_degrees)
    end = (start[0]+math.sin(radians)*length_m,start[1]+math.cos(radians)*length_m)
    return profile_between(f"grid-{grid_bearing_degrees:.3f}",start,end,data,transform)


def run(terrain_root, benchmark_path, output_root, summit_bng):
    benchmark=json.loads(benchmark_path.read_text(encoding="utf-8"))
    bounds=tuple(float(v) for v in benchmark["terrain"]["bounds"])
    observer,target=benchmark["observer"],benchmark["view"]["target"]
    camera_bng=(float(observer["bng"]["easting"]),float(observer["bng"]["northing"]))
    target_bng=(float(target["bng"]["easting"]),float(target["bng"]["northing"]))
    camera_wgs=(float(observer["wgs84"]["latitude"]),float(observer["wgs84"]["longitude"]))
    target_wgs=(float(target["wgs84"]["latitude"]),float(target["wgs84"]["longitude"]))
    published_heading=float(benchmark["view"]["published_heading_degrees"])
    eye_height=float(observer["eye_height_m"])
    dtm_path=terrain_root/"rasters"/"tryfan-004-dtm-1m.tif"
    with rasterio.open(dtm_path) as source:
        if source.crs.to_epsg()!=27700: raise ValueError(f"Expected EPSG:27700 DTM, found {source.crs}")
        data,transform=source.read(1),source.transform
        raster_bounds=(float(source.bounds.left),float(source.bounds.bottom),float(source.bounds.right),float(source.bounds.top))
    if not np.allclose(bounds,raster_bounds,atol=1e-6): raise ValueError(f"Benchmark bounds {bounds} differ from DTM {raster_bounds}")
    to_bng=Transformer.from_crs("EPSG:4326","EPSG:27700",always_xy=True)
    to_wgs=Transformer.from_crs("EPSG:27700","EPSG:4326",always_xy=True)
    geod=Geod(ellps="WGS84")
    summit_lon,summit_lat=to_wgs.transform(*summit_bng)
    summit_wgs=(float(summit_lat),float(summit_lon))
    depicted=profile_between("Camera to published depicted-place coordinate",camera_bng,target_bng,data,transform)
    summit=profile_between("Camera to canonical Tryfan summit",camera_bng,summit_bng,data,transform)
    heading=heading_profile("Published 247 degree heading",camera_wgs,published_heading,bounds,data,transform,to_bng,geod)
    def bearings(end_bng,end_wgs):
        az,_,gd=geod.inv(camera_wgs[1],camera_wgs[0],end_wgs[1],end_wgs[0])
        gb,dist=bng_bearing_distance(*camera_bng,*end_bng)
        return {"wgs84_geodesic_bearing_degrees":float(az%360),"wgs84_geodesic_distance_m":float(gd),"bng_grid_bearing_degrees":float(gb),"bng_grid_distance_m":float(dist)}
    depicted_bearings,bearing_summit=bearings(target_bng,target_wgs),bearings(summit_bng,summit_wgs)
    depicted_los,summit_los=line_of_sight(depicted,eye_height),line_of_sight(summit,eye_height)
    heading_horizon=open_ray_horizon(heading,eye_height)
    right_scan=[]
    current=depicted_bearings["bng_grid_bearing_degrees"]
    for offset in (0.,5.,10.,15.,20.,25.,30.):
        horizon=open_ray_horizon(grid_ray(camera_bng,current+offset,400.,data,transform),eye_height)
        right_scan.append({"right_offset_degrees":offset,"bng_grid_bearing_degrees":current+offset,**horizon})
    output_root.mkdir(parents=True,exist_ok=True)
    plan_path=output_root/"lab004a-geographic-plan.png"
    profile_path=output_root/"lab004a-terrain-profiles.png"
    report_path=output_root/"lab004a-geographic-diagnostic.json"

    fig,axis=plt.subplots(figsize=(11,10),constrained_layout=True)
    shade=LightSource(azdeg=315,altdeg=40).hillshade(data,vert_exag=1.5,dx=1.,dy=1.)
    axis.imshow(shade,cmap="gray",extent=[bounds[0],bounds[2],bounds[1],bounds[3]],origin="upper")
    low,high=np.percentile(data,[2,98])
    axis.imshow(data,cmap="terrain",alpha=.45,vmin=low,vmax=high,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],origin="upper")
    for profile,label,colour in [(heading,"Published heading 247°","#e4572e"),(depicted,"Camera → depicted place","#4c78a8"),(summit,"Camera → canonical summit","#f2cf5b")]:
        axis.plot(profile.eastings,profile.northings,color=colour,linewidth=2,label=label)
    for point,label,marker,colour in [(camera_bng,"Tony Edwards camera","o","#ff4d4d"),(target_bng,"Published depicted place","s","#55aaff"),(summit_bng,"Canonical Tryfan summit","^","#ffe066")]:
        axis.scatter(*point,marker=marker,s=85,color=colour,edgecolor="black",zorder=5)
        axis.annotate(label,point,xytext=(7,7),textcoords="offset points",fontsize=9,bbox={"facecolor":"white","alpha":.75,"edgecolor":"none"})
    axis.annotate("N",xy=(bounds[2]-120,bounds[3]-100),xytext=(bounds[2]-120,bounds[3]-420),ha="center",va="center",fontsize=16,fontweight="bold",arrowprops={"arrowstyle":"-|>","linewidth":2,"color":"black"})
    axis.set(xlim=(bounds[0],bounds[2]),ylim=(bounds[1],bounds[3]),xlabel="BNG easting (m)",ylabel="BNG northing (m)",title="Lab 004A geographic diagnostic — source 1 m DTM, north up")
    axis.set_aspect("equal");axis.legend(loc="lower left",fontsize=8,framealpha=.9)
    fig.savefig(plan_path,dpi=180);plt.close(fig)

    fig,axes=plt.subplots(3,1,figsize=(13,11),constrained_layout=True)
    for axis,(profile,los,horizon) in zip(axes,[(heading,None,heading_horizon),(depicted,depicted_los,None),(summit,summit_los,None)]):
        axis.fill_between(profile.distances_m,profile.elevations_m,float(np.min(profile.elevations_m))-20,color="#6f8d54",alpha=.65)
        axis.plot(profile.distances_m,profile.elevations_m,color="#263b24",linewidth=1.2,label="Source DTM")
        for ridge in local_ridges(profile)[:4]: axis.scatter(ridge["distance_m"],ridge["elevation_m_odn"],s=22,color="#8c2d04")
        if los:
            eye,target_e=los["eye_elevation_m_odn"],los["target_elevation_m_odn"]
            line=eye+(target_e-eye)*(profile.distances_m/profile.target_distance_m)
            axis.plot(profile.distances_m,line,color="#2f6fff",linestyle="--",linewidth=1.4,label="Eye-to-target line")
            point=los["maximum_clearance_point"]
            axis.scatter(point["distance_m"],point["elevation_m_odn"],marker="x",s=55,color="#d62728",label="Maximum intervening clearance")
            axis.text(.99,.96,f"Target angle {los['target_elevation_angle_degrees']:.2f}°\nMax terrain above LOS {los['maximum_intervening_clearance_above_sightline_m']:.2f} m\nLOS {'clear' if los['line_of_sight_clear'] else 'obstructed'}",transform=axis.transAxes,ha="right",va="top",bbox={"facecolor":"white","alpha":.85,"edgecolor":"#777"},fontsize=9)
        else:
            axis.scatter(horizon["horizon_distance_m"],horizon["horizon_elevation_m_odn"],marker="x",s=55,color="#d62728",label="Maximum terrain angle")
            axis.text(.99,.96,f"AOI ray length {profile.distances_m[-1]:.0f} m\nHorizon angle {horizon['maximum_terrain_angle_degrees']:.2f}°\nHorizon distance {horizon['horizon_distance_m']:.0f} m",transform=axis.transAxes,ha="right",va="top",bbox={"facecolor":"white","alpha":.85,"edgecolor":"#777"},fontsize=9)
        axis.set_title(profile.name);axis.set_ylabel("Elevation (m ODN)");axis.grid(True,alpha=.25);axis.legend(loc="lower right",fontsize=8)
    axes[-1].set_xlabel("Distance from published camera coordinate (m)")
    fig.savefig(profile_path,dpi=180);plt.close(fig)

    report={
      "schema_version":1,"source_dtm":str(dtm_path.resolve()),"benchmark_metadata":str(benchmark_path.resolve()),"aoi_bounds_bng":list(bounds),"eye_height_m":eye_height,
      "positions":{
       "camera":{"wgs84":{"latitude":camera_wgs[0],"longitude":camera_wgs[1]},"bng":{"easting":camera_bng[0],"northing":camera_bng[1]},"source_dtm_elevation_m_odn":float(depicted.elevations_m[0])},
       "published_depicted_place":{"wgs84":{"latitude":target_wgs[0],"longitude":target_wgs[1]},"bng":{"easting":target_bng[0],"northing":target_bng[1]},"source_dtm_elevation_m_odn":float(depicted.elevations_m[-1])},
       "canonical_tryfan_summit":{"wgs84":{"latitude":summit_wgs[0],"longitude":summit_wgs[1]},"bng":{"easting":summit_bng[0],"northing":summit_bng[1]},"source_dtm_elevation_m_odn":float(summit.elevations_m[-1])}},
      "rays":{
       "published_heading":{"published_heading_degrees":published_heading,"aoi_profile_length_m":float(heading.distances_m[-1]),"horizon":heading_horizon,"local_ridges":local_ridges(heading)},
       "camera_to_depicted_place":{"bearings_and_distances":depicted_bearings,"line_of_sight":depicted_los,"local_ridges":local_ridges(depicted)},
       "camera_to_canonical_summit":{"bearings_and_distances":bearing_summit,"line_of_sight":summit_los,"local_ridges":local_ridges(summit)}},
      "current_camera_right_foreground_scan":{"basis":"0-30 degrees clockwise/right of camera-to-depicted-place BNG grid bearing, sampled to 400 m","samples":right_scan},
      "metadata_interpretation":{"camera_position":"Where the camera was located; may be GPS-derived or a contributor's best-effort map placement.","depicted_place":"Approximate primary-subject location; for a mountain this may be an approximate centre, not the summit or exact frame centre.","heading":"Optional photographer view direction in degrees; stored independently and need not equal camera-to-subject bearing.","precision_warning":"Decimal display does not establish survey-grade accuracy; precision depends on the original GPS or map placement."},
      "outputs":{"plan_png":str(plan_path.resolve()),"profiles_png":str(profile_path.resolve())}}
    report_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terrain-root",type=Path,required=True)
    parser.add_argument("--benchmark",type=Path,required=True)
    parser.add_argument("--output-root",type=Path,required=True)
    parser.add_argument("--summit-easting",type=float,default=266405.)
    parser.add_argument("--summit-northing",type=float,default=359387.)
    args=parser.parse_args()
    print(json.dumps(run(args.terrain_root,args.benchmark,args.output_root,(args.summit_easting,args.summit_northing)),indent=2))


if __name__=="__main__":
    main()
