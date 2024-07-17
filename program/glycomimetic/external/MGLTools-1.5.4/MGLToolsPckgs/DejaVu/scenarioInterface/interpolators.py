## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

import numpy.oldnumeric as Numeric
from scenario.interpolators import VarVectorInterpolator,CompositeInterpolator, FloatVectorInterpolator

class MaterialInterpolator(CompositeInterpolator):
    nbvar = 4
    def __init__(self, firstVal, lastVal, interpolation='linear', interpolators=None, active = True):
        if not interpolators:
            interpolators = [VarVectorInterpolator, # for ambient RGB
                          VarVectorInterpolator, # for specular RGB
                          VarVectorInterpolator, # for emissive RGB
                          FloatVectorInterpolator, # for shininess
                          ]

        
        CompositeInterpolator.__init__(self, firstVal, lastVal, interpolators=interpolators,
                                       interpolation=interpolation)

class LightColorInterpolator(CompositeInterpolator):
    nbvar = 3
    def __init__(self, firstVal, lastVal, interpolation='linear', interpolators=None, active = True):
        if not interpolators:
            ## interpolators = [VarVectorInterpolator, # for ambient
##                              VarVectorInterpolator, # for diffuse
##                              VarVectorInterpolator, # for specular
##                              ]
            
            interpolators = [FloatVectorInterpolator, # for ambient
                             FloatVectorInterpolator, # for diffuse
                             FloatVectorInterpolator, # for specular
                             ]
        CompositeInterpolator.__init__(self, firstVal, lastVal, interpolators=interpolators,
                                       interpolation=interpolation)

