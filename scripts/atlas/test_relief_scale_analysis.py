import unittest,math
import numpy as np
from analyze_relief_scale import blur,kernel,derivative_patch,WORLD
class Tests(unittest.TestCase):
 def test_constant_derivatives_and_input_immutable(self):
  a=np.ones((40,40,2));a[:,:,1]=-3;original=a.copy();b=blur(a,1.4);np.testing.assert_allclose(a,b,atol=1e-14);np.testing.assert_array_equal(a,original)
 def test_discrete_sine_response(self):
  y,x=np.indices((128,128));a=np.stack([np.sin(2*np.pi*x/16),np.zeros_like(x)],axis=-1);w=kernel(1.4);response=sum(v*math.cos(2*math.pi*(i-6)/16) for i,v in enumerate(w));b=blur(a,1.4);np.testing.assert_allclose(b[12:-12,12:-12,0],response*a[12:-12,12:-12,0],atol=1e-14)
 def test_vector_norm_bound_and_oversampled_identity(self):
  rng=np.random.default_rng(812);a=rng.normal(size=(40,40,2));b=blur(a,1.4)
  self.assertLessEqual(float(np.linalg.norm(b,axis=-1).max()),float(np.linalg.norm(a,axis=-1).max())+1e-14)
  np.testing.assert_allclose(blur(a,.17),a,atol=1e-6)
 def test_prepared_flat_patch_remains_flat(self):
  i={'heights':np.full((96,96),200).tolist(),'overscaledZ':14,'canonical':{'z':14,'x':8200,'y':5500},'dim':256};d=derivative_patch(i,8);self.assertLess(d['filteredVectorRms'],1e-14);self.assertEqual(d['stockVectorRms'],0);self.assertGreater(d['deliverySpacingMetres'],0)
 def test_metres_to_derivative_texels(self):
  n=14;tile={'z':n,'x':8200,'y':5500};i={'heights':np.zeros((96,96)).tolist(),'overscaledZ':n,'canonical':tile,'dim':256};d=derivative_patch(i,8);lat=d['tileCentreLatitude'];spacing=WORLD*math.cos(math.radians(lat))/(256*2**n);self.assertAlmostEqual(d['sigmaDerivativeTexels'],8/spacing);self.assertAlmostEqual(d['windowPhysicalSideMetres'],64*spacing)
if __name__=='__main__':unittest.main()
