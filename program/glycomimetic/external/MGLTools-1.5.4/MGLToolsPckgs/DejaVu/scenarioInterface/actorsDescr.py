## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

from DejaVu.Transformable import Transformable
from DejaVu.Displayable import Displayable
from DejaVu.Geom import Geom
from DejaVu.Cylinders import Cylinders
from DejaVu.Light import Light
from DejaVu.Spheres import Spheres
from DejaVu.Clip import ClippingPlane
from DejaVu.Camera import Camera
from DejaVu.Materials import propertyNum

from scenario.interpolators import VarVectorInterpolator, FloatVectorInterpolator,\
     IntScalarInterpolator, RotationInterpolator,\
     BooleanInterpolator, FloatVarScalarInterpolator, FloatScalarInterpolator, ReadDataInterpolator
from scenario.datatypes import FloatType, IntType, BoolType,IntVectorType,\
     FloatVectorType, IntVarType, FloatVarType, VarVectorType

from actor import DejaVuActor, DejaVuMaterialActor,  DejaVuScissorActor, \
     DejaVuClipZActor, DejaVuFogActor, DejaVuLightColorActor, DejaVuSpheresRadiiActor,\
     DejaVuRotationActor

from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel

import numpy.oldnumeric as Numeric
id4x4 = Numeric.identity(4).astype('f')
from numpy import copy

actorsDescr = {

    Transformable: {
        'rotation': {
    #'actor': (DejaVuActor, (), {'interp': RotationInterpolator, 'datatype': FloatVectorType} )
    'actor': (DejaVuRotationActor, (), {})
            } ,

    
        'translation': {
            'actor': (DejaVuActor, (), {'interp':FloatVectorInterpolator,
                                        'datatype': FloatVectorType} )
            },
        'scale': {
            'actor': (DejaVuActor, (), {'interp':FloatVectorInterpolator,
                                        'datatype': FloatVectorType} )
            },
        'pivot': {
            'actor': (DejaVuActor, (), {'interp': FloatVectorInterpolator,
                                        'datatype': FloatVectorType} )
            }
        },

   Displayable: {
        'colors':{
            'actor': (DejaVuActor, (),
              {
                'setFunction':\
                lambda actor, value: actor.object.Set(materials=value, inheritMaterial=0),
                'getFunction':(lambda x,y: copy(x.materials[y].prop[1][:, :3]), (1028,), {}),
                'interp': VarVectorInterpolator,
                'datatype':VarVectorType
               },
                      ),
                 },
        'lineWidth': {
        'actor': (DejaVuActor, (),
                  {'setFunction': \
               lambda actor, value: actor.object.Set(lineWidth=value, inheritLineWidth=0),
                   'interp': IntScalarInterpolator, 'datatype':IntType})
                     },
        
        'pointWidth': {
              'actor': (DejaVuActor, (),
                        {'setFunction': \
               lambda actor, value: actor.object.Set(pointWidth=value, inheritPointWidth=0),
                         'interp': IntScalarInterpolator, 'datatype':IntType})
                     },
        },
    
    Geom:  {
       'material': {
            'actor': (DejaVuMaterialActor, (), {} ),

            },
        'opacity': {
            'actor': (DejaVuActor, (),
              {'setFunction': \
               lambda actor, value: actor.object.Set(opacity=value, transparent='implicit',
                                                     inheritMaterial=0),
               'getFunction':(
                   lambda x,y: x.materials[y].prop[propertyNum['opacity']], (1028,), {}
                             ),
               'interp': FloatVarScalarInterpolator,
               'datatype': FloatVarType
               }
                      ),
                  },
        
        'visible': {
    'actor': (DejaVuActor, (), {'interp': BooleanInterpolator, 'datatype': BoolType})
                     },
        
        'scissor': {
              'actor': (DejaVuActor, (), {'interp': BooleanInterpolator, 'datatype': BoolType})
                     }, # turns the scissor on/off.
        
        'scissorResize': {
              'actor': ( DejaVuScissorActor, (), {}),             
              },
       
     'xyz':{
            'actor': (DejaVuActor, (),
              {
                'setFunction': lambda actor, value: actor.object.Set(vertices=value),
                'getFunction':(lambda obj: obj.vertexSet.vertices.array, (), {}),
                'interp': VarVectorInterpolator,
                'datatype':VarVectorType
               },
                      ),
           },

##        'function':{
##     'actor':(DejaVuActor, (), {'setFunction': None, 'getFunction': None,
##                                'interp':ReadDataInterpolator, 'datatype': None})  
##                   }

        },


        Spheres: {
        'radii':   {
             'actor': (DejaVuSpheresRadiiActor, (), {}),
                    },
         },

        Cylinders: {
         'radii':   {
             'actor': (DejaVuActor, (),
                       {'setFunction': lambda actor, value: actor.object.Set(radii=list(value)),
                        'getFunction':(lambda obj: obj.vertexSet.radii.array, (), {}),
                        'interp': FloatVectorInterpolator,
                        'datatype': FloatVectorType} 
                       ),
                    },
          },

        Camera:{
         'clipZ':{
             'actor': (DejaVuClipZActor, (), {} ),
                       },
         
         'fog':{
             'actor': (DejaVuFogActor, (), {} ),
            },
         
         'backgroundColor': {
              'actor': (DejaVuActor, (),
                         #(lambda c, value: c.Set(color=value),  ),
               {'setFunction': lambda actor, value: (actor.object.Set(color=value), actor.object.Redraw()),
                        
                'getFunction':(getattr, ('backgroundColor',), {}),
                'interp': FloatVectorInterpolator,
                'datatype': FloatVectorType
                },
                        ),
              
              },

         'fieldOfView': {
              'actor': (DejaVuActor, (),
                         #(lambda c, value: c.Set(color=value),  ),
               {'setFunction': lambda actor, value: (actor.object.Set(fov=value), actor.object.Redraw()),
                        
                'getFunction':(getattr, ('fovy',), {}),
                'interp': FloatScalarInterpolator,
                'datatype': FloatType
                },
                        ),
              
              },
         

         }, 

        ClippingPlane: {
            'visible': {
              'actor': (DejaVuActor, (), {'interp': BooleanInterpolator, 'datatype': BoolType
                                          })
                     },
            'color': {
              'actor': (DejaVuActor, (), {'interp': FloatVectorInterpolator,
                                          'datatype': FloatVectorType 
                                          })
    
                            },
            },

    Light: {
        'visible': {
              'actor': (DejaVuActor, (), {'interp': BooleanInterpolator, 'datatype': BoolType
                                          })
                     },

        'color': {
               'actor':(DejaVuLightColorActor, (), {}),
               },
          
    'direction': { 'actor': (DejaVuActor, (), {'interp': FloatVectorInterpolator,
                                               'datatype': FloatVectorType} )
                   }
        }
    }

