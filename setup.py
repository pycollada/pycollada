from setuptools import find_packages, setup

install_requires = []

try: import lxml
except ImportError: install_requires.append('lxml')

try: import numpy
except ImportError: install_requires.append('numpy')

try: import dateutil
except ImportError: install_requires.append('python-dateutil')

setup(
    name = "pycollada",
    version = "0.3",
    description = "python library for reading and writing collada documents",
    author = "Jeff Terrace and contributors",
    author_email = 'jterrace@gmail.com',
    platforms=["any"],
    license="BSD",
    install_requires=install_requires,
    url = "http://pycollada.github.com/",
    test_suite = "collada.tests",
    packages = find_packages()
)
