pycollada Changelog
===================

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
* Fixed bug with saving existing files that didn't have some library_ tags.

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