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
        raise DaeMalformedError('Indexes for %s go beyond the limits of the source'%source.id)
    if source.components != components:
        raise DaeMalformedError('Wrong format in source %s'%source.id)
    return source
