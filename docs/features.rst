Features
========

Geometry
--------
* Triangles a set of triangles
* Polylist a set of polygons with no holes
* Polygons a set of polygons that can contain holes (holes unimplemented, currently an alias for Polylist)
* Lines a set of lines

Source Data
-----------
* Vertex
* Normals
* Multiple texture coordinate sets

Materials
---------
* Shader types: phong, lambert, blinn, constant
* Effect attributes: emission, ambient, diffuse, specular, shininess, reflective, reflectivity, transparent, transparency
* Texture support: Can read from local file, zip archives, or a custom auxiliary file handler
* Loads texture images with PIL if available

Lights
------
* Directional
* Ambient
* Point
* Spot

Cameras
-------
* Perspective

Scenes
------
* Full scene construction
* Transformations: rotate, scale, translate, matrix, lookat (for cameras)
* Supports iterating through a scene, yielding transformed geometry

Controllers
-----------
* Currently experimental (more support coming)
* Morph
* Skin

Additional Features
-------------------
* Fast triangulation of polygons
* Fast computation of normals
