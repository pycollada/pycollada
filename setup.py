import sys
from setuptools import find_packages, setup

install_requires = ['python-dateutil>=2.2']

try: import numpy
except ImportError: install_requires.append('numpy')

if sys.version_info[0] < 3:
    import unittest
    if not hasattr(unittest.TestCase, "assertIsNone"):
        install_requires.append('unittest2')

setup(
    name = "pycollada",
    version = "0.7.1",
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
    packages = find_packages(),
    package_data={'collada': ['resources/*.xml']}
)
