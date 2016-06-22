if __name__ == '__main__':
    import os
    import glob
    import unittest
    test_file_strings = glob.glob('test_*.py')
    module_strings = [str[0:-3] for str in test_file_strings]
    suites = [unittest.defaultTestLoader.loadTestsFromName(str) for str
              in module_strings]
    test_suite = unittest.TestSuite(suites)

    unittest.TextTestRunner(verbosity=2).run(test_suite)
