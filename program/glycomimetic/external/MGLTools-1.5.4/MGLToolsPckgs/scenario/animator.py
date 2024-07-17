##
##  Author Michel F. Sanner Nov 11 2004
##
from SimPy.Simulation import Process, initialize, activate, simulate, now, hold
#from SimPy.SimulationStep import Process, initialize, activate, simulate, now, hold, simulate, startStepping, stopStepping

from time import sleep
import weakref, warnings

from scenario.objectAnimator import ObjectAnimator, ObjectAnimatorDescriptor

class Animator:
    """
"""
    def __init__(self):

        self.objectAnimatorDescr = []
        self.currentFrame = 0
        self.endFrame = 10
        self.needsRedraw=False
        self.gui = None # will be set when a gui is created
        
        # FIXME should have a set and delete method to check type etc
        self.afterAnimation = [] # list of fucntions to be called after
                                 # play ends
        
    def addObjectAnimator(self, objAnimatorDescr):

        for objAnim in self.objectAnimatorDescr:
            if objAnim.name==objAnimatorDescr.name:
                msg = "Animator already contains an object animator named "+\
                      objAnimatorDescr.name
                warnings.warn(msg)
                return
                              
        assert isinstance(objAnimatorDescr, ObjectAnimatorDescriptor)
        objAnimatorDescr.animator = weakref.ref(self)
        self.objectAnimatorDescr.append( objAnimatorDescr)
        end = objAnimatorDescr.namedArgs['endFrame']
        self.updateEndFrame(end)
        if self.gui:
            self.gui().redraw()

    def delObjectAnimator(self, objAnimatorDescr):

        self.objectAnimatorDescr.remove(objAnimatorDescr)
        #FIXME need to fix the endFrame
        

    def getLastFrame(self):
        # returns number of frames in the simulation
        return self.endFrame


    def getLastFrameWithChange(self):
        # returns the last frame in which a value changes
        last = 0
        for descr in self.objectAnimatorDescr:
            if descr.namedArgs['endFrame']>last:
                last = descr.namedArgs['endFrame']
        return last

    
    def updateEndFrame(self, end, updateGUI=1):
        if end > self.endFrame:
            self.endFrame = end
            if self.gui and updateGUI:
                self.gui().setDuration(end)
        elif end >= self.getLastFrameWithChange():
            self.endFrame = end
            if self.gui and updateGUI:
                self.gui().setDuration(end)


    def run(self):
        if len(self.objectAnimatorDescr)==0:
            return
        initialize()
        for p in self.objectAnimatorDescr:
            p.namedArgs['animator'] = self
            if "Viewer.OneRedraw" in str(p.posArgs):
                proc = ObjectAnimator(*p.posArgs, **p.namedArgs)
                activate(proc, proc.execute(), at=0.0, prior=False)
            else:
                proc = ObjectAnimator(*p.posArgs, **p.namedArgs)
                activate(proc, proc.execute(), at=0.0, prior=True)
        #print 'simulate', self.endFrame
        simulate(until=self.endFrame)
        
        # call callback after animation completes
        for f in self.afterAnimation:
            f()


    def setValuesAt(self, frame):
        #print 'setting initial values'
        for p in self.objectAnimatorDescr:
            val = p.getValueAt(frame)
            if val is not None:
                p.setValue(val)


    def gotoFrame(self, frame):
        if frame<0 or frame>self.endFrame or frame==self.currentFrame: return
        self.setValuesAt(frame)
        if self.gui():
            self.gui().placeTimeCursor(frame)
        self.currentFrame = frame
##         # I can;t jump to a fame directly
##         # if I modify startFrame the interpolator will divide by 0
##         if len(self.objectAnimatorDescr)==0:
##             return
##         initialize()
##         for p in self.objectAnimatorDescr:
##             namedArgs = p.namedArgs.copy()
##             if namedArgs['interpolator'] is None:
##                 namedArgs['startFrame'] = namedArgs['endFrame'] = frame
##             #namedArgs['startFrame'] = namedArgs['endFrame'] = frame
## ##             if namedArgs['interpolator'] is not None:
## ##                 if namedArgs['interpolator'].sequential is True:
## ##                     namedArgs['startFrame'] = p['startingFrame']
                    
##             proc = apply( ObjectAnimator, p.posArgs, namedArgs)
##             activate(proc, proc.execute()) # at 0.0?
##         simulate(frame)
