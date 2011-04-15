Loading A Collada Document
==========================

Collada documents can be loaded with the :class:`.Collada` class::

    mesh = Collada('file.dae')
    
Zip archives are also supported. The archive will be searched for
a dae file.

The constructor can also accept a file-like object::

    f = open('file.dae')
    mesh = Collada(f)
    
Note that this will also work with the `StringIO` module. When
loading from non-file sources, the `aux_file_loader` parameter can
be passed to the constructor. This is useful if loading from
an unusual source, like a database::

    dae_file = open('file.dae')
    dae_data = dae_file.read()
    texture_file = open('texture.jpg')
    texture_data = texture_file.read()
    
    def my_aux_loader(filename):
        if filename == 'texture.jpg':
            return texture_data
        return None
    
    mesh = Collada(StringIO(dae_data), aux_file_loader=my_aux_loader)
    
When using the Collada object (see :ref:`structure`), if you try and
read a texture, the `my_aux_loader` function will be invoked.

Loading a collada document can result in an exception being thrown.
For a list of possible exceptions, see :ref:`exception-summary`.
Sometimes, you may want to ignore some exceptions and let the loader
try to continue loading the file. For example, the following will
ignore errors about broken references and features that pycollada
doesn't support::

    mesh = Collada('file.dae', ignore=[DaeUnsupportedError, DaeBrokenRefError])
    
If any errors occurred during the load, you can find them in :attr:`.Collada.errors`.