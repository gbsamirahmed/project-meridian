"""Run unchanged native-window scenarios with only their query owner substituted."""
import sys
import unittest
from adapter import NativeSession
import test_window

if __name__=='__main__':
    test_window.WindowShared=NativeSession
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_window))
    sys.exit(not result.wasSuccessful())
