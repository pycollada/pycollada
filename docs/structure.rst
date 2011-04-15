.. _structure:

Collada Object Structure
========================

After loading a collada document, all of the information about the
file is stored within the Collada object. For example, consider the
following code::

    >>> from collada import *
    >>> mesh = Collada('duck_triangles.dae')
    >>> mesh
    <Collada geometries=1>
    
This sample file is located in `collada/tests/data` of the pycollada
distribution. We can now explore the attributes of the :class:`.Collada`
class.

Let's see what :attr:`.Collada.geometries` it has::

    >>> mesh.geometries
    [<Geometry id=LOD3spShape-lib, 1 primitives>]

Each geometry has a number of :class:`.Source` objects that contain raw
source data like an array of floats. It then has a number of :class:`.Primitive`
objects contained. Let's inspect them::

    >>> geom = mesh.geometries[0]
    >>> geom.primitives
    [<TriangleSet length=4212>]

In this case, there is only a single primitive contained in the geometry and it's
a set of triangles. The :class:`.TriangleSet` object lets us get at the vertex,
normal, and texture coordinate information. There are index properties that index
into the source arrays, and the sources are also automatically mapped for you.
You can iterate over the triangle set to yield individual :class:`.Triangle`
objects::

    >>> triset = geom.primitives[0]
    >>> trilist = list(triset)
    >>> len(trilist)
    4212
    >>> trilist[0]
    <Triangle ([-23.93639946  11.53530025  30.61249924], [-18.72640038  10.1079998   26.6814003 ], [-15.69919968  11.42780018  34.23210144], "blinn3SG")>

The triangle object has the vertex, normal, and texture coordinate data associated
with the triangle, as well as the material it references. Iterating over the triangle
set is convenient, but it can be slow for large meshes. Instead, you can access the
numpy arrays in the set. For example, to get the vertex, normal, and texture coordinate
for the first triangle in the set::

    >>> triset.vertex[triset.vertex_index][0]
    array([[-23.93639946,  11.53530025,  30.61249924],
           [-18.72640038,  10.1079998 ,  26.6814003 ],
           [-15.69919968,  11.42780018,  34.23210144]], dtype=float32)
    >>> triset.normal[triset.normal_index][0]
    array([[-0.192109  , -0.934569  ,  0.299458  ],
           [-0.06315   , -0.99362302,  0.093407  ],
           [-0.11695   , -0.92131299,  0.37081599]], dtype=float32)
    >>> triset.texcoordset[0][triset.texcoord_indexset[0]][0]
    array([[ 0.866606  ,  0.39892399],
           [ 0.87138402,  0.39761901],
           [ 0.87415999,  0.398826  ]], dtype=float32)

These are numpy arrays which allows for fast retrieval and computations.

The collada object also has arrays for accessing :class:`.Camera`, :class:`.Light`,
:class:`.Effect`, :class:`.Material`, and :class:`.Scene` objects::

    >>> mesh.cameras
    [<Camera id=cameraShape1>]
    >>> mesh.lights
    [<DirectionalLight id=directionalLightShape1-lib>]
    >>> mesh.effects
    [<Effect id=blinn3-fx type=blinn>]
    >>> mesh.materials
    [<Material id=blinn3 effect=blinn3-fx>]
    >>> mesh.scenes
    [<Scene id=VisualSceneNode nodes=3>]

A collada scene is a graph that contains nodes. Each node can have transformations
and a list of child nodes. A child node can be another node or an instance of a geometry,
light, camera, etc. The default scene is contained in the :attr:`.Collada.scene` attribute.
Let's take a look::

    >>> mesh.scene
    <Scene id=VisualSceneNode nodes=3>
    >>> mesh.scene.nodes
    [<Node transforms=3, children=1>, <Node transforms=4, children=1>, <Node transforms=4, children=1>]

We could write code to iterate through the scene, applying transformations on bound objects,
but the Scene object already does this for you via its :meth:`.Scene.objects` method. For
example, to find all of the instantiated geometries in a scene and have them bound to a
material and transformation::

    >>> boundgeoms = list(mesh.scene.objects('geometry'))
    >>> boundgeoms
    [<BoundGeometry id=LOD3spShape-lib, 1 primitives>]

Notice that we get a :class:`.BoundGeometry` here. We can also pass in `light`, `camera`, or
`controller` to get back a :class:`.BoundLight`, :class:`.BoundCamera`, or :class:`.BoundController`,
respectively. The bound geometry is very similar to the geometry we looked through above. We can use
the iterative method::

    >>> boundprims = list(boundgeoms[0].primitives())
    >>> boundprims
    [<BoundTriangleSet length=4212>]
    >>> boundtrilist = list(boundprims[0])
    >>> boundtrilist[0]
    <Triangle ([-23.93639946 -30.61249924  11.53530025], [-18.72640038 -26.6814003   10.1079998 ], [-15.69919968 -34.23210144  11.42780018], "<Material id=blinn3 effect=blinn3-fx>")>

or by accessing the numpy arrays directly::

    >>> boundprims[0].vertex[boundprims[0].vertex_index][0]
    array([[-23.93639946, -30.61249924,  11.53530025],
           [-18.72640038, -26.6814003 ,  10.1079998 ],
           [-15.69919968, -34.23210144,  11.42780018]], dtype=float32)

In this case, the triangle is identical to above. This is because the collada duck example only has
identity transformations. We can inspect these in the scene::

    >>> mesh.scene.nodes[0].transforms
    [<RotateTransform (0.0, 0.0, 1.0) angle=0.0>, <RotateTransform (0.0, 1.0, 0.0) angle=0.0>, <RotateTransform (1.0, 0.0, 0.0) angle=0.0>]
    >>> mesh.scene.nodes[0].children
    [<GeometryNode geometry=LOD3spShape-lib>]

