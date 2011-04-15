from setuptools import find_packages, setup

setup(
    name = "pycollada",
    version = "0.2",
    description = "python library for reading and writing collada documents",
    author = "Jeff Terrace and contributors",
    author_email = 'jterrace@gmail.com',
    platforms=["any"],
    license="BSD",
    install_requires=['lxml', 'numpy'],
    url = "http://pycollada.github.com/",
    test_suite = "collada.tests",
    packages = find_packages()
)
