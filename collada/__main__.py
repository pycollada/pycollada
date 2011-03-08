import unittest2

if __name__ == '__main__':
    suite = unittest2.TestLoader().discover("tests")
    unittest2.TextTestRunner(verbosity=2).run(suite)
