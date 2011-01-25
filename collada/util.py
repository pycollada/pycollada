import numpy

def toUnitVec(vec):
    return vec / numpy.sqrt(numpy.vdot(vec, vec))
