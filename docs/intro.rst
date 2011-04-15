Introduction
============

**pycollada** is a python module for creating, editing and loading
`COLLADA <http://www.collada.org/>`_, which is a COLLAborative Design Activity
for establishing an interchange file format for interactive 3D applications.

The library allows you to load a COLLADA file and interact with it as a python object.
In addition, it supports creating a collada python object from scratch, as well as
in-place editing.

pycollada uses `lxml <http://lxml.de/>`_ for XML loading, construction, and saving.
`numpy <http://numpy.scipy.org/>`_ is used for numerical arrays. Both of these libraries
are impleted in C/C++ which makes pycollada quite fast.

pycollada was originally written by Alejandro Conty Estevez of Scopia Visual Interfaces
Systems in 2009. Since 2011, the library is now maintained by Jeff Terrace. For a list
of additional contributors, see the AUTHORS file included with distribution.
