import os
import sys
from setuptools import find_packages, setup

install_requires = ['python-dateutil>=2.2', 'numpy']

if sys.version_info[0] < 3:
    import unittest
    if not hasattr(unittest.TestCase, "assertIsNone"):
        install_requires.append('unittest2')

readme_path = os.path.join(os.path.split(__file__)[0], "README.markdown")
with open(readme_path, "r") as f:
    readme_text = f.read()

setup(
    name="pycollada",
    version="0.8",
    description="python library for reading and writing collada documents",
    author="Jeff Terrace and contributors",
    author_email='jterrace@gmail.com',
    long_description=readme_text,
    long_description_content_type="text/markdown",
    platforms=["any"],
    license="BSD",
    install_requires=install_requires,
    extras_require={
        'prettyprint': ["lxml"],
        'validation': ["lxml"]
    },
    url="http://pycollada.readthedocs.org/",
    project_urls={"Source": "https://github.com/pycollada/pycollada"},
    test_suite="collada.tests",
    packages=find_packages(),
    package_data={'collada': ['resources/*.xml']}
)
