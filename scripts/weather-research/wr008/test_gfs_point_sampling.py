"""Synthetic mathematical/guard cases; opt-in real replay is separately labelled."""
import copy
import json
import math
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np
import gfs_point_sampling as pilot


class SyntheticSampling(unittest.TestCase):
    def setUp(self):
        self.m = copy.deepcopy(json.loads(pilot.field.PIN.read_text())["expected"])
        self.m.update(Ni=8,Nj=5,numberOfPoints=40,iDirectionIncrementInDegrees=45,
                      jDirectionIncrementInDegrees=45,longitudeOfLastGridPointInDegrees=315)
        self.values = np.arange(40,dtype=float).reshape(5,8)
        self.mask = np.zeros((5,8),dtype=bool)
        self.sampler = pilot.Sampler(self.values,self.mask,self.m)

    def q(self, lat=0, lon=0, method="BILINEAR"):
        return self.sampler.query({"latitude":lat,"longitude":lon,"method":method})

    def test_exact_node(self):
        for method in ["NEAREST","BILINEAR"]:
            self.assertEqual(self.q(0,90,method)["temperature_K"],self.values[2,2])

    def test_halfway_tie_east(self): self.assertEqual(self.q(0,22.5,"NEAREST")["nodes"][0]["column"],1)
    def test_halfway_tie_south(self): self.assertEqual(self.q(22.5,0,"NEAREST")["nodes"][0]["row"],2)

    def test_axis_nearest_is_not_geodesic_nearest(self):
        # Synthetic coarse-grid counterexample using spherical angular distance.
        # A northward node is closer geographically than the axis-tie result.
        selected=self.q(22.5,22.5,"NEAREST")["nodes"][0]
        self.assertEqual(selected["latitude"],0)
        lat,dlon=math.radians(22.5),math.radians(22.5)
        cos_south=math.cos(lat)*math.cos(dlon)
        cos_north=math.sin(lat)*math.sin(math.radians(45))+math.cos(lat)*math.cos(math.radians(45))*math.cos(dlon)
        self.assertGreater(cos_north,cos_south)

    def test_halfway_not_language_bankers_rounding(self):
        self.assertEqual([pilot.half_up(x) for x in [.5,1.5,2.5]],[1,2,3])
        self.assertEqual(pilot.half_up(math.nextafter(.5,0)),0)
        self.assertEqual(pilot.half_up(math.nextafter(.5,1)),1)

    def test_four_weights(self):
        result=self.q(22.5,22.5)
        self.assertEqual([n["weight"] for n in result["nodes"]],[.25]*4)
        self.assertEqual(result["weight_sum"],1)

    def test_constant(self):
        self.values[:]=273.125
        for lat,lon in [(10,20),(0,-22.5),(-45,370),(45,-100)]:
            self.assertEqual(self.q(lat,lon)["temperature_K"],273.125)

    def test_affine(self):
        rows,cols=np.indices(self.values.shape)
        self.values[:]=100+3*rows+2*cols
        for r,c in [(1.2,1.3),(2.7,4.2),(2,3)]:
            self.assertAlmostEqual(self.q(90-r*45,c*45)["temperature_K"],100+3*r+2*c,places=12)

    def test_convex_bounds(self):
        result=self.q(12,26)
        self.assertGreaterEqual(result["temperature_K"],min(n["temperature_K"] for n in result["nodes"]))
        self.assertLessEqual(result["temperature_K"],max(n["temperature_K"] for n in result["nodes"]))

    def test_wrap_equivalence(self):
        for method in ["NEAREST","BILINEAR"]:
            results=[self.q(10,lon,method) for lon in [-22.5,337.5,697.5]]
            self.assertEqual(results[0]["nodes"],results[1]["nodes"])
            self.assertEqual(results[0]["temperature_K"],results[2]["temperature_K"])

    def test_wrap_sub_ulp_endpoint(self):
        self.assertEqual(self.q(0,-5e-324,"NEAREST")["normalised_coordinate"]["longitude_0_360"],0)

    def test_periodic_seam(self):
        result=self.q(0,337.5)
        self.assertEqual([n["column"] for n in result["nodes"]],[7,0,7,0])
        self.assertEqual(result["temperature_K"],(self.values[2,7]+self.values[2,0])/2)

    def test_antimeridian(self):
        self.assertEqual(self.q(0,180)["nodes"],self.q(0,-180)["nodes"])

    def test_nearest_pole_canonical_node(self):
        for lat,row in [(90,0),(-90,4)]:
            self.assertEqual(self.q(lat,123,"NEAREST")["nodes"][0]["column"],0)
            self.assertEqual(self.q(lat,123,"NEAREST")["nodes"][0]["row"],row)

    def test_bilinear_poles_explicitly_unsupported(self):
        for lat in [-90,90]: self.assertEqual(self.q(lat)["status"],"UNSUPPORTED_POLAR_CAP_BILINEAR")

    def test_bilinear_polar_caps_explicitly_unsupported(self):
        for lat in [-60,60]: self.assertEqual(self.q(lat)["status"],"UNSUPPORTED_POLAR_CAP_BILINEAR")

    def test_bilinear_endpoints_use_nonpolar_rows(self):
        for lat in [-45,45]:
            self.assertEqual(self.q(lat)["status"],"OK")
            self.assertTrue(all(n["row"] not in [0,4] for n in self.q(lat)["nodes"]))

    def test_latitude_not_periodic(self):
        for lat in [-91,91,360]: self.assertEqual(self.q(lat)["status"],"LATITUDE_OUT_OF_RANGE")

    def test_nonfinite(self):
        for lat,lon in [(math.nan,0),(math.inf,0),(0,math.nan),(0,-math.inf)]:
            self.assertEqual(self.q(lat,lon)["status"],"NONFINITE_COORDINATE")
            pilot.field.canonical(self.q(lat,lon))  # Receipt explicitly encodes failure without nonstandard JSON.

    def test_huge_integer_overflow(self): self.assertEqual(self.q(0,10**1000)["status"],"NONFINITE_COORDINATE")
    def test_unsupported_method(self): self.assertEqual(self.q(method="CUBIC")["status"],"UNSUPPORTED_METHOD")

    def test_malformed_structures(self):
        for q in [None,[],{},[0,0],{"latitude":0,"longitude":0}, {"latitude":0,"longitude":0,"method":"NEAREST","time":0}]:
            self.assertEqual(self.sampler.query(q)["status"],"MALFORMED_QUERY")

    def test_invalid_coordinate_types(self):
        for lat,lon in [(True,0),(0,False),("0",0),(0,None)]:
            self.assertEqual(self.q(lat,lon)["status"],"INVALID_COORDINATE_TYPE")

    def test_masked_nearest(self):
        self.mask[2,0]=True
        self.assertEqual(self.q(method="NEAREST")["status"],"MISSING_CONTRIBUTING_NODE")

    def test_masked_bilinear_no_renormalisation(self):
        self.mask[2,1]=True
        self.assertEqual(self.q(10,20)["status"],"MISSING_CONTRIBUTING_NODE")

    def test_zero_weight_node_missing_conservatively_rejected(self):
        self.mask[3,1]=True
        self.assertEqual(self.q(0,0)["status"],"MISSING_CONTRIBUTING_NODE")

    def test_nonfinite_unmasked_node(self):
        self.values[2,0]=math.nan
        self.assertEqual(self.q(method="NEAREST")["status"],"UNINTERPRETABLE_NODE")

    def test_immutability_order_and_determinism(self):
        before=self.values.tobytes(),self.mask.tobytes()
        self.values.setflags(write=False); self.mask.setflags(write=False)
        expected=[self.q(10,20),self.q(0,-22.5)]
        self.assertEqual(expected,[self.q(10,20),self.q(0,-22.5)])
        self.assertEqual(expected,list(reversed([self.q(0,-22.5),self.q(10,20)])))
        self.assertEqual(before,(self.values.tobytes(),self.mask.tobytes()))

    def test_wrong_array_orientation(self):
        with self.assertRaises(pilot.field.IntegrityError): pilot.Sampler(self.values.T,self.mask,self.m)

    def test_unknown_scanning_mode(self):
        self.m["scanningMode"]=64
        with self.assertRaises(pilot.field.IntegrityError): pilot.Grid(self.m)

    def test_incomplete_global_grid(self):
        self.m["Ni"]=9
        with self.assertRaises(pilot.field.IntegrityError): pilot.Grid(self.m)

    def test_unfrozen_profile(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name)/"synthetic-profile.json"; p.write_text('{}')
            with self.assertRaises(pilot.field.IntegrityError): pilot.validate_pins(p)

    def test_reference_resource_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as name:
            output=Path(name)/"reference.json"; resources=Path(name)/"reference-resources.json"
            resources.write_bytes(b"synthetic-original")
            with self.assertRaises(pilot.field.IntegrityError): pilot.reference(Path(name)/"absent.grib2",{},output)
            self.assertEqual(resources.read_bytes(),b"synthetic-original")

    def test_no_independent_query_silently_dropped(self):
        q=self.q();q["id"]="test"
        with self.assertRaises(pilot.field.IntegrityError): pilot.comparison([q],{"queries":[]},self.sampler.grid)

    def test_decoder_sample_disagreement(self):
        q=self.q(method="NEAREST");q["id"]="test"
        ref={"id":"test","status":"OK","indices":[[2,0]],"weights":[1],"temperature_K":999}
        with self.assertRaises(pilot.field.IntegrityError): pilot.comparison([q],{"queries":[ref]},self.sampler.grid)

    def test_independent_nonfinite_weight_rejected(self):
        q=self.q(method="NEAREST");q["id"]="test"
        ref={"id":"test","status":"OK","indices":[[2,0]],"weights":[math.nan],"temperature_K":16}
        with self.assertRaisesRegex(pilot.field.IntegrityError,"weight disagreement"):
            pilot.comparison([q],{"queries":[ref]},self.sampler.grid)


@unittest.skipUnless(os.environ.get("MERIDIAN_WR007_INPUT") and os.environ.get("MERIDIAN_WR007_GDAL_PYTHON"),
                     "Opt-in pinned real field and independent GDAL interpreter required")
class RealFieldReplay(unittest.TestCase):
    def test_real_queries_independent_comparison_and_reproducibility(self):
        source=Path(os.environ["MERIDIAN_WR007_INPUT"]); initial=pilot.field.digest(source)
        with tempfile.TemporaryDirectory() as name:
            paths=[Path(name)/f"sampling-{i}.json" for i in range(2)]
            results=[pilot.run(source,os.environ["MERIDIAN_WR007_GDAL_PYTHON"],p) for p in paths]
            self.assertEqual(paths[0].read_bytes(),paths[1].read_bytes())
            for result in results:
                self.assertEqual(len(result["queries"]),47)
                self.assertEqual(result["comparison"]["nearest_comparisons"],19)
                self.assertEqual(result["comparison"]["bilinear_comparisons"],15)
                self.assertEqual(result["comparison"]["unexplained_disagreements"],0)
                self.assertEqual(sum(q["status"]=="UNSUPPORTED_POLAR_CAP_BILINEAR" for q in result["queries"]),4)
                self.assertTrue(result["input_and_arrays_unchanged"])
                rows={q["id"]:q for q in result["queries"]}
                for method in ["NEAREST","BILINEAR"]:
                    self.assertEqual(rows['antimeridian:'+method]["nodes"],rows['antimeridian-plus360-equivalent:'+method]["nodes"])
            accepted=pilot.HERE/"sampling-receipt.json"
            if accepted.exists(): self.assertEqual(pilot.field.digest(paths[0]),json.loads(accepted.read_text())["full_receipt_sha256"])
            with self.assertRaises(pilot.field.IntegrityError):
                pilot.run(source,os.environ["MERIDIAN_WR007_GDAL_PYTHON"],paths[0])
        self.assertEqual(pilot.field.digest(source),initial)


if __name__ == "__main__": unittest.main()
