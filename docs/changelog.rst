pycollada Changelog
###################

0.7.1 (2020-01-23)
==================

Bug Fixes
=========
* Fix package_data in 0.7 release.


0.7 (2019-10-10)
****************

Bug Fixes
=========
* Fix bug with namespaces with xml.etree.
* Fix bug when parsing whitespace-only numerical elements.

Backwards Compatibility Notes
=============================
* Support for Python 3.3 and 3.4 has been dropped.


0.6 (2017-11-19)
****************

New Features
============
* tristrips and trifans are now supported.
* Add support for Python 3.6

Bug Fixes
=========
* Fix python-dateutil dependency setup.
* Fix flaky test (#61).

Backwards Compatibility Notes
=============================
* Drop support for Python 2.6 and 3.2.

0.5 (2017-03-16)
****************

New Features
============
* Added function to get effect properties from underneath the technique tag.
* Add example how to visualize DAE file using OpenGL API.

Bug Fixes
=========
* Fix Python 3 image loading.
* Fix missing import.
* changed string_ to unicode_ for numpy string array parsers.
* changed itervalues() to values() for compatibility with python3.
* Change iteritems() to items() in getInputList. Add test. Fixes #40.
* Fixing conversion from unsupported texcoord. input.
* use 'from PIL import Image' instead of 'import Image'.
* Fix case where getitem is called before normal indices are set up.
* Fixed shader compilation error. Old GLSL compilers do not like precision statement.
* Apply patch to fix ctypes-usage issue.
* Convert some Windows-style files to Unix format (linebreaks).
* Fix the bug with relative path to default dae file.

0.4 (2012-07-31)
****************

Backwards Compatibility Notes
=============================
* Python 2.5 is no longer supported. Supported versions are now 2.6, 2.7 and 3.2.

New Features
============
* Added support for reading the opaque attribute from <transparent> tag.
* Normals and texture coordinate indices are now available in shapes (Triangle and Polygon).
* Library is now compatible with python's built-in ElementTree API instead of requiring lxml. lxml is still recommended.
* Added support for Python 3.2. Supported versions are now 2.6, 2.7 and 3.2.
* Added support for index_of_refraction in <effect>.
* Added optional parameter to Collada that does XML schema validation when saving.
* Automatically corrects broken files that don't have correct xfov, yfov, and aspect ratio in cameras.

Bug Fixes
=========
* Fix the default value for transparency in Effect. Now correctly defaults to 1.0 when opaque mode is A_ONE, and 0.0 when opaque mode is RGB_ZERO.
* Fixed bug where BoundPolylist was not returning the correct length value.
* Removed support for RGB from Effect since it's not valid in the spec. If an RGB is given, a fourth A channel is automatically added as 1.0.
* Made instance_geometry not write an empty bind_material if it's empty since it breaks validation.
* Made saving strip out empty <library_*> tags since it breaks validation.

0.3 (2011-08-31)
****************

Backwards Compatibility Notes
=============================
* If using the old Camera object, this has been changed to an abstract class
  with types for PerspectiveCamera and OrthographicCamera
* If using the old Collada.assetInfo dictionary to read asset information, this
  has been changed to an object. See documentation for more information.

New Features
============
* Added support for bump maps inside the extra tag of an effect
* Added texbinormal and textangent to triangle sets
* Added a method to generate texture tangents and binormals
* Added detection for double_sided
* Added an optional parameter to specify what filename inside an archive to use when loading from zip
* Added support for loading multiple sets of library_* nodes
* Refactored asset information into a separate module. Fixed #12
* Refactored Camera into PerspectiveCamera and OrthographicCamera, inheriting from Camera

Bug Fixes
=========
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
******************
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
******************
* Fixed bug with saving existing files that didn't have some library_ tags.

0.2 (2011-04-15)
****************
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
****************
* Initial release
* Triangles geometry
* Reads vertices and normals
* Multiple texture coordinate channels
* Phong and Lambert Materials
* Texture support using PIL
* Scene suppport for geometry, material and camera instances
* Transforms (matrix, rotate, scale, translate)

Releasing
#########

#. Generate log::

       git log $(git describe --tags --abbrev=0)..HEAD --pretty=format:"* %s"

   Add this to docs/changelog.rst.

#. Update setup.py to change version to new version.

#. Update docs/conf.py to change version string to new version.

#. Commit changes.

#. Tag version::

       git tag v0.x HEAD
       git push origin master
       git push --tags


#. Build source distribution::

       python setup.py sdist
       twine upload dist/pycollada-0.7.tar.gz -u user -p "pass"
