import sys
from setuptools import find_packages, setup

install_requires = []

try: import numpy
except ImportError: install_requires.append('numpy')

if sys.version_info[0] > 2:
    install_requires.append('python-dateutil>=2.0')
else:
    import unittest
    if not hasattr(unittest.TestCase, "assertIsNone"):
        install_requires.append('unittest2')
    install_requires.append('python-dateutil==1.5')

setup(
    name = "pycollada",
    version = "0.5",
    description = "python library for reading and writing collada documents",
    author = "Jeff Terrace and contributors",
    author_email = 'jterrace@gmail.com',
    platforms=["any"],
    license="BSD",
    install_requires=install_requires,
    extras_require = {
        'prettyprint': ["lxml"],
        'validation': ["lxml"]
    },
    url = "http://pycollada.readthedocs.org/",
    test_suite = "collada.tests",
    packages = find_packages()
)
