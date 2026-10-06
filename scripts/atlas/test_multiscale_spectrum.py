import unittest
import tempfile
from pathlib import Path
import rasterio
from rasterio.transform import from_origin
import numpy as np
from multiscale_spectrum import bands,sample_native
class Tests(unittest.TestCase):
    def test_physical_wavelength_and_parseval(self):
        y,x=np.indices((128,128));a=3*np.sin(2*np.pi*x/16)+4*np.cos(2*np.pi*y/64)
        s=bands(a,2,[4,16,64,256],False,False);self.assertAlmostEqual(s['bands'][2]['rmsMetres'],3/np.sqrt(2));self.assertAlmostEqual(s['bands'][3]['rmsMetres'],4/np.sqrt(2));self.assertAlmostEqual(s['totalWindowCorrectedRms'],5/np.sqrt(2));self.assertAlmostEqual(s['parsevalError'],0)
    def test_plane_removed(self):
        y,x=np.indices((128,128));s=bands(2*x-4*y+20,2,[4,16,64,256]);self.assertLess(s['totalWindowCorrectedRms'],1e-10)
    def test_native_cell_centres_and_xy_orientation(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'plane.tif';y,x=np.indices((8,8));values=3*x+5*y
            with rasterio.open(p,'w',driver='GTiff',width=8,height=8,count=1,dtype='float32',crs='EPSG:2056',transform=from_origin(100,200,1,1)) as ds:ds.write(values.astype('float32'),1)
            a,receipt=sample_native(p,(104,196),4,1)
            np.testing.assert_allclose(a,values[2:6,2:6]);self.assertEqual(receipt['gridSpacing'],[1.,1.])
    def test_missing_support_refused(self):
        a=np.ones((16,16));a[0,0]=np.nan
        with self.assertRaises(ValueError):bands(a,2,[4,16])
if __name__=='__main__':unittest.main()
