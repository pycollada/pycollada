import numpy

from collada import DaeMalformedError

def toUnitVec(vec):
    return vec / numpy.sqrt(numpy.vdot(vec, vec))

def checkSource( source, components, maxindex):
    """Check if a source objects complies with the needed `components` and has the needed length

    :Parameters:
      source
        A `Source` instance coming from the `Geometry` oject
      components
        A tuple describing the needed channels like ('X','Y','Z')
      maxindex
        The maximum index that refers to this source

    """
    if len(source.data) <= maxindex:
        raise DaeMalformedError(
            "Indexes (maxindex=%d) for source '%s' (len=%d) go beyond the limits of the source"
            % (maxindex, source.id, len(source.data)) )

    #some files will write sources with no named parameters
    #by spec, these params should just be skipped, but we need to
    #adapt to the failed output of others...
    if len(source.components) == len(components) and \
            source.components == (None,)*len(components):
        source.components = components
    
    if source.components != components:
        raise DaeMalformedError('Wrong format in source %s'%source.id)
    return source

def normalize_v3(arr):
    ''' Normalize a numpy array of 3 component vectors shape=(n,3) '''
    lens = numpy.sqrt( arr[:,0]**2 + arr[:,1]**2 + arr[:,2]**2 )
    arr[:,0] /= lens
    arr[:,1] /= lens
    arr[:,2] /= lens
