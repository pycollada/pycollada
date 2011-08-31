Changelog
=========

0.3 (2011-08-31)
----------------

Backwards Compatibility Notes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* If using the old Camera object, this has been changed to an abstract class
  with types for PerspectiveCamera and OrthographicCamera
* If using the old Collada.assetInfo dictionary to read asset information, this
  has been changed to an object. See documentation for more information.

New Features
^^^^^^^^^^^^
* Added support for bump maps inside the extra tag of an effect
* Added texbinormal and textangent to triangle sets
* Added a method to generate texture tangents and binormals
* Added detection for double_sided
* Added an optional parameter to specify what filename inside an archive to use when loading from zip
* Added support for loading multiple sets of library_* nodes
* Refactored asset information into a separate module. Fixed #12
* Refactored Camera into PerspectiveCamera and OrthographicCamera, inheriting from Camera

Bug Fixes
^^^^^^^^^
* Changed Collada IndexedLists attributes to be properties. Fixed Issue #14
* Updated scene to use a local scope when nodes are instantiated inside a scene
* Changed parsing to raise DaeMalformedError when an lxml parser exception is thrown
* Fixed bug when loading an <image> tag local to an <effect> not showing up in Collada.images
* Fixed bug when loading an empty <polygons>
* Fixed bug in if statement when loading morph controllers
* Fixed bug when triangulating a length-0 polylist
* Updated install instructions for OS X and Ubuntu problems
* Fixed bugs in IndexedList from Issue #13
* Fixed a bug where using the same map twice in an effect would cause incorrrect output
* Changed geometry export to delete any sources in the vertices tag that no longer exist
* Changed library output to not output emtpy library nodes so validator doesn't complain
* Add same checks in scene loading that was done in library_nodes loading so that if nodes are not found yet while loading, it will keep trying
* Changed the way library_nodes is loaded so that if a referenced node from instance_node is not loaded yet, it will keep trying
* Fixed bug where a triangles xml node would try to set an attribute to None
* Fixed bug in handling joints that influence 0 vertices

0.2.2 (2011-05-03)
------------------
* Changed the way instance_node is handled to actually maintain the mapping so it's not lost when saving
* Added setdata function to CImage and made Effect compare only image path
* Fixed a bug when rewriting geometry sources
* Change primitive sources to point to the <vertices> tag when possible since other importers don't like not having a <vertices> tag
* Export source data with only 7 decimal precision for better file size
* Prevent NaN from being the result of a normalize_v3 call
* Fixed bug where effect was not correctly reading all four color values
* Fixed a bug where a triangleset would not create its xml node when generated from a polylist
* Big speed increases for converting numpy data to strings
* Moved getInputs function to Primitive
* Added functions to triangleset to generate normals and get an input list
* Fixed bug in saving a scene node if there was no id
* Fixed some bugs/optimizations with saving
* Added function to test if an Effect is almost equal to another Effect
* Adding dynamic dependencies to setup.py

0.2.1 (2011-04-15)
------------------
* Fixed bug with saving existing files that didn't have some library\_ tags.

0.2 (2011-04-15)
----------------
* Many bugfixes
* polylist support
* polygons support without holes
* lines support
* blinn and constant material support
* More effect attributes
* Better support for auxiliary texture files
* Lights (directional, ambient, point, spot)
* lookat transform
* Experimental controller support (skin, morph)
* polygons/polylist can be triangulated
* Automatic computation of per-vertex normals


0.1 (2009-02-08)
----------------
* Initial release
* Triangles geometry
* Reads vertices and normals
* Multiple texture coordinate channels
* Phong and Lambert Materials
* Texture support using PIL
* Scene suppport for geometry, material and camera instances
* Transforms (matrix, rotate, scale, translate)