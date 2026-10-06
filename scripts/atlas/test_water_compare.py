"""Asset-independent checks of water comparison mathematics and semantic safeguards."""
import unittest
import numpy as np
from shapely.geometry import box
from pyproj import Transformer
from water_compare import native_codes, monthly_meaning, occurrence_summary, decode_monthly, event_period, union_area, grouped_areas, CROSSWALK
class WaterComparisonTests(unittest.TestCase):
 def test_native_mixed_codes_preserve_both(self):self.assertEqual(native_codes('RBEDS, SALTM'),['RBEDS','SALTM'])
 def test_no_observation_is_not_non_detection(self):self.assertNotEqual(monthly_meaning(0),monthly_meaning(1))
 def test_monthly_counts(self):self.assertEqual(decode_monthly([0,0,1,2]),{'no observations':2,'water not detected':1,'water detected':1})
 def test_unknown_monthly_code_rejected(self):
  with self.assertRaises(KeyError):monthly_meaning(255)
 def test_occurrence_nodata_not_zero(self):
  d=occurrence_summary(np.array([0,20,100,255]));self.assertEqual(d['noData255'],1);self.assertEqual(d['notWater0'],1);self.assertEqual(d['meanOccurrencePercent'],40)
 def test_occurrence_invalid_rejected(self):
  with self.assertRaises(ValueError):occurrence_summary([101])
 def test_event_unknown_not_future_flood(self):self.assertEqual(event_period({'start_date':'2050-01-01','end_date':'2050-01-01'})['status'],'unknown event time')
 def test_event_missing_time(self):self.assertEqual(event_period({'start_date':None,'end_date':None})['status'],'unknown event time')
 def test_event_reversed_rejected(self):
  with self.assertRaises(ValueError):event_period({'start_date':'2020-02-02','end_date':'2020-02-01'})
 def test_event_interval_kept(self):self.assertEqual(event_period({'start_date':'1960-10-01','end_date':'1960-10-31'})['nativeEnd'],'1960-10-31')
 def test_intersection_not_bbox_overlap(self):self.assertEqual(union_area([(box(10,10,20,20),{})],box(0,0,5,5)),0)
 def test_overlapping_records_not_double_counted(self):self.assertEqual(union_area([(box(0,0,2,2),{}),(box(1,0,3,2),{})],box(0,0,3,2)),6)
 def test_grouped_native_properties(self):self.assertEqual(grouped_areas([(box(0,0,2,2),{'kind':'FZ3'})],box(0,0,1,1),'kind'),{'FZ3':1.0})
 def test_bng_round_trip_and_axis_order(self):
  f=Transformer.from_crs(27700,4326,always_xy=True);r=Transformer.from_crs(4326,27700,always_xy=True)
  lon,lat=f.transform(297150,87350);self.assertTrue(-3.5<lon<-3.3);self.assertTrue(50.6<lat<50.8);x,y=r.transform(lon,lat);self.assertAlmostEqual(x,297150,delta=.002);self.assertAlmostEqual(y,87350,delta=.002)
 def test_crosswalk_losses_explicit(self):self.assertTrue(all(c['loss'] and c['relationship'] for c in CROSSWALK))
 def test_scenario_cannot_be_current_state(self):self.assertEqual(next(c for c in CROSSWALK if c['native']=='WFD / PHI / Flood Zones')['relationship'],'incompatible')
if __name__=='__main__':unittest.main()
