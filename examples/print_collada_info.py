#!/usr/bin/env python

import sys

import collada


def inspectController(controller):
    """Display contents of a controller object found in the scene."""
    print(
        f"    Controller (id={controller.skin.id}) (type={type(controller).__name__})"
    )
    print(
        "       Vertex weights:%d, joints:%d"
        % (len(controller), len(controller.joint_matrices))
    )
    for controlled_prim in controller.primitives():
        print("       Primitive", type(controlled_prim.primitive).__name__)


def inspectGeometry(obj):
    """Display contents of a geometry object found in the scene."""
    materials = set()
    for prim in obj.primitives():
        materials.add(prim.material)

    print("    Geometry (id=%s): %d primitives" % (obj.original.id, len(obj)))
    for prim in obj.primitives():
        print(
            "        Primitive (type=%s): len=%d vertices=%d"
            % (type(prim).__name__, len(prim), len(prim.vertex))
        )
    for mat in materials:
        if mat:
            inspectMaterial(mat)


def inspectMaterial(mat):
    """Display material contents."""
    print(f"        Material {mat.effect.id}: shading {mat.effect.shadingtype}")
    for prop in mat.effect.supported:
        value = getattr(mat.effect, prop)
        # it can be a float, a color (tuple) or a Map ( a texture )
        if isinstance(value, collada.material.Map):
            colladaimage = value.sampler.surface.image
            # Accessing this attribute forces the loading of the image
            # using PIL if available. Unless it is already loaded.
            img = colladaimage.pilimage
            if img:  # can read and PIL available
                print(
                    f"            {prop} = Texture {colladaimage.id}:",
                    img.format,
                    img.mode,
                    img.size,
                )
            else:
                print(
                    f"            {prop} = Texture {colladaimage.id}: (not available)"
                )
        else:
            print(f"            {prop} =", value)


def inspectCollada(col):
    # Display the file contents
    print("File Contents:")
    print("  Geometry:")
    if col.scene is not None:
        for geom in col.scene.objects("geometry"):
            inspectGeometry(geom)
    print("  Controllers:")
    if col.scene is not None:
        for controller in col.scene.objects("controller"):
            inspectController(controller)
    print("  Cameras:")
    if col.scene is not None:
        for cam in col.scene.objects("camera"):
            print(f"    Camera {cam.original.id}: ")
    print("  Lights:")
    if col.scene is not None:
        for light in col.scene.objects("light"):
            print(f"    Light {light.original.id}: color =", light.color)

    if not col.errors:
        print("File read without errors")
    else:
        print("Errors:")
        for error in col.errors:
            print(" ", error)


if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "misc/base.zip"

    # open COLLADA file ignoring some errors in case they appear
    col = collada.Collada(
        filename, ignore=[collada.DaeUnsupportedError, collada.DaeBrokenRefError]
    )
    inspectCollada(col)
