#########################################################################
#
# Date: Nov 2004 Author: Michel Sanner
#
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI
#
#########################################################################


from NetworkEditor.items import NetworkNode

from scenario.animator import Animator
from scenario.objectAnimator import ObjectAnimator, ObjectAnimatorDescriptor
from scenario.interpolators import Interpolator, ScalarLinearInterpolator

from scenario.VisionInterface.gui import NetworkAnimatorGui


class AnimateScalarWidgets(NetworkNode):
    """When this node is added to a a network, it will build a tree widget
representing all input ports found in the network and all sub-networks that
are bound to either a Dial or a Thumbwheel.  One can then assing a scalar
linear interpolation object to any of these widgets and play he animation.

Input:

Ouput:
"""
    def __init__(self, name='ScalarInterpAnimator', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        self.netAnim = NetworkAnimatorGui()

        code = """def doit(self):
    pass
"""
        self.setFunction(code)


    def afterAddingToNetwork(self):
        self.netAnim.populateTree(self.network)



class AnimatorNode(NetworkNode):
    """Create an animator object from the scenario Python package
Input:
    ObjAnimDescr: object animator descriptors
    play:
    gotoFrame:
Ouput:
"""
    def __init__(self, name='Animator', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='AnimatorDescr', singleConnection=False,
                  name='animatorDescr')
        ip.append(datatype='int', name='play')
        ip.append(datatype='int', name='gotoFrame')

	self.widgetDescr['play'] = {
            'class':'NEButton', 'master':'node',
            'labelCfg':{'text':'play'},
            }
        self.widgetDescr['gotoFrame'] = {
            'class':'NEThumbWheel', 'master':'node',
            'width':80, 'height':20, 'type':'int', 'wheelPad':1,
            'initialValue':0.0,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'got frame:'},
            }

        self.animator = Animator()
        
        code = """def doit(self, animatorDescr, play, gotoFrame):
    for obj in animatorDescr:
        if obj not in self.animator.objectAnimatorDescr:
            self.animator.addObjectAnimator(obj)

        if self.inputPorts[1].hasNewData():
            print 'Running'
            self.animator.run()
        elif self.inputPorts[2].hasNewData():
            print gotoFrame, type(gotoFrame)
            self.animator.gotoFrame(gotoFrame)
"""
        self.setFunction(code)



class ObjectAnimatorNode(NetworkNode):
    """Create an object animator object from the scenario Python package
Input:
    object: object animator descriptors

Ouput:
"""
    def __init__(self, name='Animator', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='None', name='object')
        ip.append(datatype='string', name='method')
        #ip.append(datatype='string', name='posArgs', required=False)
        #ip.append(datatype='string', name='namedArgs', required=False)
        ip.append(datatype='string', name='valueName', required=False)
        ip.append(datatype='float', name='startFrame', required=False)
        ip.append(datatype='float', name='endFrame', required=False)
        ip.append(datatype='Interpolator', name='interpolator', required=False)

        self.widgetDescr['method'] = {
            'class':'NEEntry', 'master':'node', 'width':10,
            'labelCfg':{'text':'method:'}}
        self.widgetDescr['valueName'] = {
            'class':'NEEntry', 'master':'node', 'width':10,
            'labelCfg':{'text':'valueName:'}}
        self.widgetDescr['startFrame'] = {
            'class':'NEThumbWheel', 'master':'node',
            'width':80, 'height':20, 'type':'float', 'wheelPad':1,
            'initialValue':0.0,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'from:'},
            }

        self.widgetDescr['endFrame'] = {
            'class':'NEThumbWheel', 'master':'node',
            'width':80, 'height':20, 'type':'float', 'wheelPad':1,
            'initialValue':0.0,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'to:'},
            }

        op = self.outputPortsDescr
        op.append(datatype='AnimatorDescr', name='AnimatorDescr')
        
        code = """def doit(self, object, method, valueName=None, \
startFrame=0, endFrame=None, interpolator=None):
    function = getattr(object, method)
    obj = ObjectAnimatorDescriptor(object, function, valueName=valueName, \
               startFrame=startFrame, endFrame=endFrame,
               interpolator=interpolator)
    self.outputData(AnimatorDescr=obj)
"""
        self.setFunction(code)



class ScalarLinearInterpolatorNode(NetworkNode):
    """Create an ScalarLinearInterpolator object from the scenario Python package
Input:
    startValue: object animator descriptors
    endValue: object animator descriptors

Ouput:
    interpolator: 
"""
    def __init__(self, name='ScalarLinear', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='float', name='startValue')
        ip.append(datatype='float', name='endValue')

        self.widgetDescr['startValue'] = {
            'class':'NEThumbWheel', 'master':'node',
            'width':80, 'height':20, 'type':'float', 'wheelPad':1,
            'initialValue':0.0,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'from:'},
            }

        self.widgetDescr['endValue'] = {
            'class':'NEThumbWheel', 'master':'node',
            'width':80, 'height':20, 'type':'float', 'wheelPad':1,
            'initialValue':0.0,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'to:'},
            }

        op = self.outputPortsDescr
        op.append(datatype='Interpolator', name='interpolator')
        
        code = """def doit(self, startValue, endValue):
    obj = ScalarLinearInterpolator(startValue, endValue)
    self.outputData(interpolator = obj)
"""
        self.setFunction(code)


from Vision.VPE import NodeLibrary
animlib = NodeLibrary('Scenario', '#664466')

animlib.addNode(AnimateScalarWidgets, 'AnimScalarWidgets', 'output')
animlib.addNode(AnimatorNode, 'Animator', 'output')
animlib.addNode(ObjectAnimatorNode, 'Object Animator', 'Input')
animlib.addNode(ScalarLinearInterpolatorNode, 'Scalar Linear', 'Interpolator')


from NetworkEditor.datatypes import AnyArrayType

class AnimatorDescrType(AnyArrayType):

    def __init__(self, name='AnimatorDescr', color='yellow', shape='diamond',
                 klass=ObjectAnimatorDescriptor):
      
        AnyArrayType.__init__(self, name=name, color=color, shape=shape, 
                              klass=klass)
        

class InterpolatorType(AnyArrayType):

    def __init__(self, name='Interpolator', color='yellow', shape='circle',
                 klass=Interpolator):
      
        AnyArrayType.__init__(self, name=name, color=color, shape=shape, 
                              klass=klass)

animlib.addType( AnimatorDescrType() )
animlib.addType( InterpolatorType() )
