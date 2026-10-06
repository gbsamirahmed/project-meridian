"""Asset-free tests of telemetry interpretation and frozen audit scope."""
import json, math, tempfile, unittest
from pathlib import Path
import numpy as np
from PIL import Image
from analyze_multiscale import centre_level, signal

class Tests(unittest.TestCase):
    def test_centre_level_ignores_finer_offscreen_tiles(self):
        location=[-3.999,53.115]
        def tile(z):
            return {'z':z,'x':math.floor((location[0]+180)/360*2**z),'y':math.floor((1-math.asinh(math.tan(math.radians(location[1])))/math.pi)/2*2**z)}
        wrong=tile(18);wrong['x']+=1
        self.assertEqual(centre_level([tile(9),tile(13),wrong,None],location),13)
        self.assertIsNone(centre_level([wrong],location))
        self.assertIsNone(centre_level([],location))
    def test_capture_signal_preserves_constant_and_detects_variation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.png'
            Image.new('RGB',(1440,900),(128,128,128)).save(p)
            constant=signal(p)
            self.assertEqual(constant['samplePixels'],160000)
            self.assertEqual(constant['gradientMeanSquare'],0)
            a=np.full((900,1440,3),128,dtype=np.uint8);a[250:650,720:920]=255
            Image.fromarray(a).save(p)
            self.assertGreater(signal(p)['gradientMeanSquare'],0)
    def test_frozen_scope_and_camera_progression(self):
        p=json.loads((Path(__file__).resolve().parents[2]/'docs/atlas/multiscale-representation-plan.json').read_text())
        self.assertEqual(p['baseline'],'e3edd0f32ca109175cb456581abb804dc542519c')
        self.assertEqual(len(p['scenes']),22)
        for site in ['tryfan','riffelhorn']:
            scenes=[s for s in p['scenes'] if s['site']==site and s['pitch']==0]
            self.assertEqual([s['targetMetresPerCssPixel'] for s in scenes],[128,32,8,2,.5,.125])
            np.testing.assert_allclose(np.diff([s['zoom'] for s in scenes]),2,rtol=0,atol=1e-12)
        self.assertTrue(all(k.startswith('src/') for k in p['productionHashes']))

if __name__=='__main__':unittest.main()
