Installation
============

github
-------

The source code for pycollada is available on github here: https://github.com/pycollada/pycollada

To pull a read-only copy, you can clone the repository::

   git clone git://github.com/pycollada/pycollada.git pycollada


Python Package Index
--------------------

pycollada is available as a package at: http://pypi.python.org/pypi/pycollada/

You can also use easy_install::

   easy_install pycollada

On Mac OS X, try this if you get an error installing lxml::

   export ARCHFLAGS="arch i386 -arch x86_64"
   easy_install pycollada

On Ubuntu, install these dependencies first::

   apt-get install python-lxml python-numpy python-dateutil
   easy_install pycollada
