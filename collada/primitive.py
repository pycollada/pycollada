####################################################################
#                                                                  #
# THIS FILE IS PART OF THE PyCollada LIBRARY SOURCE CODE.          #
# USE, DISTRIBUTION AND REPRODUCTION OF THIS LIBRARY SOURCE IS     #
# GOVERNED BY A BSD-STYLE SOURCE LICENSE INCLUDED WITH THIS SOURCE #
# IN 'COPYING'. PLEASE READ THESE TERMS BEFORE DISTRIBUTING.       #
#                                                                  #
# THE PyCollada SOURCE CODE IS (C) COPYRIGHT 2009                  #
# by Scopia Visual Interfaces Systems http://www.scopia.es/        #
#                                                                  #
####################################################################

"""Module containing the base class for primitives"""
from collada import DaeObject

class Primitive(DaeObject):
    """Base class for all primitive sets like triangle sets."""

    def bind(self, matrix, materialnodebysymbol):
        """Create a copy of the primitive under the given transform.

        Creates a copy of the primitive with its points transformed
        by the given matrix and with material symbols set according
        to the given mapping

        :Parameters:
          matrix
            A 4x4 numpy float matrix
          materialnodebysymbol
            a dictionary with the material symbols inside the object 
            assigned to MaterialNodes defined in the scene

        """
        pass
