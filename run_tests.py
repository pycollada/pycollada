import virtualenv
import textwrap
import os
import subprocess
import stat
import sys

"""Script for setting up multiple virtual python environments
to test pycollada with various package configurations."""

CURDIR = os.path.dirname(__file__)

def get_python_venv(base_dir, python_version, unique_name, force=False):
    """Creates a python virtual environment and then returns the path to
    the python binary inside the environment.
    
    base_dir - directory to create the virtual environment
    python_version - version of python to use
    unique_name - a name for this virtual environment
    force - whether or not to force creating the virtualenv if already exists
    
    """
    
    output = virtualenv.create_bootstrap_script(textwrap.dedent("""
    import os, subprocess
    def after_install(options, home_dir):
        etc = join(home_dir, 'etc')
        if not os.path.exists(etc):
            os.makedirs(etc)
    """), python_version=python_version)
    
    bootstrap_script = os.path.join(base_dir, 'bootstrap%s.py' % unique_name)
    
    if force or not os.path.isfile(bootstrap_script):
        f = open(bootstrap_script, 'w')
        f.write(output)
        f.close()
        os.chmod(bootstrap_script, 0700)
    
    venv_dir = os.path.join(base_dir, 'venv%s' % unique_name)
    
    if force or not os.path.isdir(venv_dir):
        ret = subprocess.call([bootstrap_script, '--no-site-packages', '-p', 'python%s' % python_version, venv_dir])
        if ret != 0:
            print >> sys.stderr, 'Creating virtualenv for python version', python_version, 'with xml?', lxml, 'failed. Cannot Continue'
            sys.exit(1)
    
    return os.path.join(venv_dir, 'bin', 'python')

def main():
    testdir = os.path.join(CURDIR, '__testing')
    try:
        os.mkdir(testdir)
    except OSError:
        pass
    
    python_testers = []
    python_testers.append(('python 2.6 with lxml', ('numpy', 'lxml', 'unittest2'), get_python_venv(testdir, '2.6', 'lxml26')))
    python_testers.append(('python 2.7 with lxml', ('numpy', 'lxml', 'unittest2'), get_python_venv(testdir, '2.7', 'lxml27')))
    python_testers.append(('python 3.2 with lxml', ('numpy', 'lxml'), get_python_venv(testdir, '3.2', 'lxml32')))
    python_testers.append(('python 2.6 without lxml', ('numpy', 'unittest2'), get_python_venv(testdir, '2.6', 'nolxml26')))
    python_testers.append(('python 2.7 without lxml', ('numpy', 'unittest2'), get_python_venv(testdir, '2.7', 'nolxml27')))
    python_testers.append(('python 3.2 without lxml', ('numpy',), get_python_venv(testdir, '3.2', 'nolxml32')))
    
    pycollada_setup = os.path.join(CURDIR, 'setup.py')
    for description, install_packages, pythonbin in python_testers:
        for install_package in install_packages:
            ret = subprocess.call([os.path.join(os.path.dirname(pythonbin), 'easy_install'), install_package])
            if ret != 0:
                print >> sys.stderr, 'Failed to install', install_package, 'for', description, '. Cannot continue.'
                sys.exit(1)
        
        ret = subprocess.call([pythonbin, pycollada_setup, 'install'])
        if ret != 0:
            print >> sys.stderr, 'Setting up pycollada for', description, 'failed. Cannot continue.'
            sys.exit(1)

    pycollada_tests = os.path.join(CURDIR, 'collada', '__main__.py')
    failed = 0
    succeeded = 0
    for description, install_packages, pythonbin in python_testers:
        ret = subprocess.call([pythonbin, pycollada_tests])
        if ret != 0:
            failed += 1
        else:
            succeeded += 1
    
    print
    print succeeded, '/', succeeded + failed, 'tests passed.'

if __name__ == '__main__':
    main()
