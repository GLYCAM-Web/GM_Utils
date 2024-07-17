##
##  Author Michel F. Sanner Nov 11 2004
##
from SimPy.Simulation import Process, initialize, activate, simulate, now, hold
from time import sleep
import weakref

from scenario.interpolators import Interpolator


class ObjectAnimator(Process):
    """
An AnimatorObject allows to modify a particular attribute of a Python object
during the execution of a scenario.  Instances of this object are instanciated
byt the Animator object from ObjectAnimatorDescriptor objects.
This object is implemented as SimPy Process object.
"""
    def __init__(self, object, function, name, posArgs=None, namedArgs=None,
                 valueName=None, startFrame=None, endFrame=None,
                 interpolator=None, t0value=None, animator=None):
        """
Constructor of the ObjectAnimator object,

arguments:
    object:            Python object on which to operate
    function:          function to called at each step
    name:              Name fo the object animator (used for debugging)
    posArgs=None:      positional arguments for function, defaults to ()
    namedArgs=None:    dict of named argumenst for function, defaults to {}
    valueName=None:    name to be used as a named argument to pass the
                       interpolator value to function
    startFrame=0:      first frame at which this process will trigger
    endFrame=None:     last frame at which this process will trigger
    interpolator=None: interpolation object to compute a value to be passed
                       to function at each step to modify the object):
    t0value=None       Value of the attribute at t=0.0 i.e. before the
                       animation. This value is required when an interpolator
                       is provided but unused for ObjectAnimators with no
                       interpolator
"""
        Process.__init__(self)
        self.object = weakref.ref(object)
        if function is not None:
            assert callable(function)
        self.function = function
        self.name = name
        if posArgs is None:
            posArgs = ()
        self.posArgs = posArgs
        if namedArgs is None:
            namedArgs = {}
        self.namedArgs = namedArgs
        self.valueName = valueName
        if startFrame is None:
            startFrame = 0
        self.startFrame = startFrame
        if endFrame is None:
            endFrame = animator.getLastFrame()
        self.endFrame = endFrame
        if startFrame is not None and endFrame is not None:
            self.nbFrames = float(endFrame-startFrame)
        else:
            self.nbFrames = None

        if interpolator is not None:
            assert isinstance(interpolator, Interpolator)
        self.interpolator = interpolator
        self.animator=animator


    def execute(self):
        yield hold, self, self.startFrame # wait for the first frame
        self.animator.needsRedraw=True
        while True:
            step = now()
            if step > self.endFrame:
                break
            if self.interpolator:
                #self.animator.needsRedraw=True
                stepValue = (step-self.startFrame)/float(self.nbFrames)
                value = self.interpolator.getValue(stepValue)
                if self.valueName:
                    #print 'Event', self.name, step, stepValue, self.valueName, value
                    self.namedArgs.update({self.valueName:value})
                    print 'Event', self.name, self.function, self.posArgs, self.namedArgs 
                    self.function(*self.posArgs, **self.namedArgs)
                else: # interpolator but no name
                    #print 'Event', self.name, stepValue, step, value
                    self.function( *((value,)+self.posArgs), **self.namedArgs)
                self.animator.needsRedraw=True
            else:
                if "Viewer.OneRedraw" in str(self.function):
                    if self.animator.needsRedraw==True:
                        #print 'Event', self.name
                        self.function(*self.posArgs, **self.namedArgs)
                        self.animator.needsRedraw=False
                else:
                    self.namedArgs.update({self.valueName:step})
                    self.function(*self.posArgs, **self.namedArgs)
            
            yield hold, self, 1.

   
class ObjectAnimatorDescriptor:
    """
An AnimatorObjectDescriptor stores all the information needed to instanciate
an AnimatorObject.  These objects can be added to an Animator instance to
define a scenario.
"""
    def __init__(self, object, function, name, posArgs=None, namedArgs=None,
                 valueName=None, startFrame=0, endFrame=None,
                 interpolator=None, t0value=None):
        """
Constructor of the ObjectAnimatorDescriptor object,

arguments:
    object:            Python object on which to operate
    function:          function to called at each step
    name:              Name of this animator,  Thisname has to be unique
                       among the list of ObjectAnimatorDescriptor in an
                       Animator object
    posArgs=None:      positional arguments for function, defaults to ()
    namedArgs=None:    dict of named argumenst for function, defaults to {}
    valueName=None:    name to be used as a named argument to pass the
                       interpolator value to function
    startFrame=None:   first frame at which this process will trigger
    endFrame=None:     last frame at which this process will trigger
    interpolator=None: interpolation object to compute a value to be passed
                       to function at each step to modify the object):
    t0value=None       Value of the attribute at t=0.0 i.e. before the
                       animation. This value is required when an interpolator
                       is provided but unused for ObjectAnimators with no
                       interpolator
"""
        if interpolator is not None:
            assert t0value is not None

        self.name = name
        self.posArgs = (object, function, name)
        if startFrame==0 and endFrame is None:
            self.fullRange = True
        else:
            self.fullRange = False
        self.namedArgs = {'posArgs':posArgs, 'namedArgs':namedArgs,
                          'valueName':valueName, 'startFrame':startFrame,
                          'endFrame':endFrame, 'interpolator':interpolator,
                          't0value':t0value}
        self.animator = None  # will be a weakref to the animator to which is
                              # is added
        self.t0value = t0value
        
        
    def configure(self, **kw):
        for k,v in kw.items():
            if k == 'endFrame':
                assert v>=kw.get('startFrame', self.namedArgs['startFrame'])
                self.namedArgs['endFrame'] = int(v)
                if v > self.animator().endFrame:
                    self.animator().updateEndFrame(v)

            if k == 'startFrame':
                assert v<=kw.get('endFrame', self.namedArgs['endFrame'])
                assert v >= 0
                self.namedArgs['startFrame'] = int(v)
            #FIXME handle other keys
            
    def __repr__(self):
        return "<%s %s, frames %s->%s>"%(self.__class__.__name__,hex(id(self)),
            str(self.namedArgs['startFrame']), str(self.namedArgs['endFrame']))


    def getValueAt(self, frame):
        # return the value of the property for a given point in time
        val = self.t0value
        if val is None: return None

        d = self.namedArgs
        startFrame = d['startFrame']
        if startFrame is None: return val
        if frame < startFrame: return val

        endFrame = d['endFrame']
        if endFrame is None: return val
        interpolator = self.namedArgs['interpolator']
        if frame > endFrame: return interpolator.endValue

        stepValue = (frame-startFrame)/float(endFrame-startFrame)
        return interpolator.getValue(stepValue)


    def setValue(self, value):
        # call the function to set the value
        try:
            kw = {self.namedArgs['valueName']:value}
            #print self.posArgs[1], kw
            self.posArgs[1](**kw)
        except KeyError:
            #print self.posArgs[1], value
            self.posArgs[1](value)

        
    def info(self, indent=''):
        l = [indent+"ObjectAnimatorDescriptor: %s\n"%self.name]
        l.append( indent+"    object: "+repr(self.posArgs[0])+'\n')
        l.append( indent+"    function:"+repr(self.posArgs[1])+'\n')
        l.append( indent+"        posArgs:"+repr(self.namedArgs['posArgs'])+'\n')
        l.append( indent+"        namedArgs:"+repr(self.namedArgs['namedArgs'])+'\n')
        l.append( indent+"        valueName:"+str(self.namedArgs['valueName'])+'\n')
        l.append( indent+"        animator:"+str(self.namedArgs['animator'])+'\n')
        l.append( indent+"    frames:  %s -> %s\n"%(
            self.namedArgs['startFrame'], self.namedArgs['endFrame']))
        l.extend( self.namedArgs['interpolator'].info(indent=indent+'    ') )
        return l

