##
##  Author Michel F. Sanner May 2007
##
from SimPy.Simulation import Process, initialize, activate, simulate, now, hold

from time import sleep
import weakref, warnings

from actor import Actor
from scenario.gui import DirectorGUI


class ActorProcess(Process):
    """
An ActorProcess is a SimPY Process object that gets created each time a
simulation is run.
"""
    def __init__(self, actor):
        """
Constructor of the ActorProcess object,

arguments:
    Actor:             An instance of an Action object
"""
        Process.__init__(self)
        self.actor = actor
        

    def execute(self):
        actor = self.actor
        if actor.playing:
            # FIXME we should wait for the first frame with values change
            yield hold, self, 0 # wait for the first frame
            director = actor._director()
            while True:
                frame = now()
                if not director.moveForward:
                    # director.maxFrame is computed in director.run(), before activate()
                    frame = director.maxFrame - frame

                value, inter, valGen = actor.getValueAt(frame)
                if valGen == None:
                    if inter == -1: # this is the case when the first keyframe != 0 and
                                    # the time cursor is over the interval before it -
                                    # there is no interpolation
                        value = None
                elif valGen != -1:
                    if not valGen.active: value = None
                if value is not None:
                    # pre-step callback
                    try:
                        f, args, kw = actor.preStep_cb
                        f( *args, **kw)
                    except TypeError:
                        pass
                    if actor.scenarioname == "DejaVuScenario":
                        director.needsRedraw = True
                    #print "setting frame %d value of actor %s" % (frame, actor.name)
                    actor.setValue(value)

                    # post-step callback
                    try:
                        f, args, kw = actor.postStep_cb
                        f( *args, **kw)
                    except TypeError:
                        pass
                # Fixme we should wait for the next frame with values change
                yield hold, self, 1.


                
class RedrawActorProcess(ActorProcess):
    
    def execute(self):
        actor = self.actor
        # FIXME we should wait for the first frame with values change
        yield hold, self, 0 # wait for the first frame

        while True:
            frame = now()

            try:
                f, args, kw = actor.preStep_cb
                f( *args, **kw)
            except TypeError:
                pass
            #print "setting frame %d value of actor %s" % (frame, actor.name)
            actor.setValue()
            # post-step callback
            try:
                f, args, kw = actor.postStep_cb
                f( *args, **kw)
            except TypeError:
                pass
            # Fixme we should wait for the next frame with values change
            yield hold, self, 1.



class Director:
    """
"""
    def __init__(self):

        self.actors = []
        self.currentFrame = 0
        self.endFrame = 0

        self.gui = None # will be set when a gui is created
        self.recordingActors = []  # list of actors with recording flag on
           # i.e. actor.recording!='stopped'
        # FIXME should have a set and delete method to check type etc
        self.afterAnimation = [] # list of functions to be called after
                                 # play ends
        self.scenarios = {}
        self.autotrackDict = {}
        self.redrawActor = None
        self.moveForward = True
        self.maxFrame = 0
        self.needsRedraw = False
        

    def addScenario(self, name, scenario):
        self.scenarios[name] = scenario


    def start(self):
        if self.gui is None:
            gui = DirectorGUI(self)
            gui.root.protocol('WM_DELETE_WINDOW', gui.root.withdraw)
            self.gui = gui
            for scenario in self.scenarios.values():
                scenario.setDirector()
        else:
            self.gui.root.deiconify()



    def addActor(self, actor, redraw = True):

        for objAnim in self.actors:
            if objAnim.name==actor.name:
                msg = "Scenario already contains an actor named "+\
                      actor.name
                warnings.warn(msg)
                return
                              
        assert isinstance(actor, Actor)
        actor._director = weakref.ref(self)

        self.actors.append( actor )
        lastFrame = actor.getLastFrame()
        if lastFrame >= self.endFrame:
            self.updateEndFrame(lastFrame)
        if self.gui and redraw:
            self.gui.redraw()
        actor.onAddToDirector()


    def deleteActor(self, actor):
        # delete this actor and all its actions
        name = actor.name
        if self.gui:
            self.gui.deleteActors()
        if actor in self.actors:
            self.actors.remove(actor)
        if hasattr(actor, "guiVar"):
            if actor.guiVar:
                actor.guiVar.set(0)
        if hasattr(actor.object, "animatedProperties"):
            del actor.object.animatedProperties[name]
        if self.gui:
            if self.gui.selectedFrames.has_key(name):
                self.gui.selectedFrames.pop(name)
            if self.gui.autotracking:
                if self.autotrackDict.has_key(name):
                    self.autotrackDict.pop(name)
                    # this will update the dictioanary with a new "clean"
                    # version of the deleted actor.
                    self.autotrackDict.update(actor.scenario.getNewActors())
                
            self.gui.drawActors()
        if len(actor.kfSetId):
            for kf, setId in actor.kfSetId.items():
                kfset = self.gui.kfSets.get(setId)
                if kfset:
                    kfset.removeKeyFrame(name, kf)
                    if kfset.getNumberOfFrames() == 1:
                        # remove the set
                        self.gui.removeKFSet(kfset)

        #if actor.getLastFrame()==self.getLastFrame():
        #    self.updateEndFrame( self.getLastFrameWithChange() )
        

    def getLastFrame(self):
        # returns number of frames in the simulation
        return self.endFrame

    
    def getLastFrameWithChange(self, actors = None):
        # returns the last frame in which a value changes
        if not actors:
            actors = self.actors
        last = 0 
        for actor in actors:
            #if actor.isFullRange(): continue
            if actor.visible:
                lastFrame = actor.getLastFrame()
                if lastFrame>last:
                    last = lastFrame
        return last


    def updateEndFrame(self, end, updateGUI=1):
        if not end:
            return
        
        if end > self.endFrame:
            self.endFrame = end
            if self.gui and updateGUI:
                self.gui.setDuration(end)

        else:
            last = self.getLastFrameWithChange()
            if end < last+10 : # when recording we want to make sure there are frame to the right
                self.endFrame = last +10
            else:
                self.endFrame = end
            if self.gui and updateGUI:
                self.gui.setDuration(self.endFrame)

    def run(self, forward = True):
        if len(self.actors)==0:
            return
        initialize()
        redraw = self.redrawActor
        start = 0
        #end = self.endFrame
        self.maxFrame = self.getLastFrameWithChange()
        end = self.maxFrame
        gui = self.gui
        if gui:
            if not (gui.startFrame == 0 and gui.stopFrame == 1):
                start = gui.startFrame
                end = gui.stopFrame
                self.maxFrame = end + start
        self.moveForward = forward
        if redraw:
            proc = RedrawActorProcess(redraw)
            activate(proc, proc.execute(), at=start, prior=True)
            #print 'activated redraw', 
        for actor in self.actors:
            if actor.name != "redraw":
                proc = ActorProcess(actor)
                activate(proc, proc.execute(), at=start, prior=True)
                #print 'activated ', actor.name, action
        #print 'simulate', self.endFrame
        simulate(until=end)
        #self.currentFrame = self.endFrame
        if forward:
            #self.currentFrame = self.endFrame
            self.currentFrame = end
        else:
           self.currentFrame = start
        # call callback after animation completes
        for f in self.afterAnimation:
            f()
        if self.redrawActor:
            vi = self.redrawActor.object
            vi.startAutoRedraw()


    def setValuesAt(self, frame, actor = None):
        #print 'setValuesAt:', frame, self.needsRedraw
        redraw = self.redrawActor
        if actor:
            actors = [actor]
        else:
            actors = self.actors
        for actor in actors:
            if actor.name != "redraw" and  actor.playing:
                if len(actor.valueGenerators):
                    value, interval, valGen = actor.getValueAt(frame)
                    if valGen == None: # do not set the value
                        value = None
                    elif valGen != -1:
                        if not valGen.active: value = None
                    if value is not None:
                        if redraw:
                            self.needsRedraw = True
                        actor.setValue(value)
                                
        if redraw:
            redraw.setValue()

    def gotoFrame(self, frame, set=True):
        if frame<0:
            frame = 0
        elif frame>self.endFrame:
            frame = self.endFrame
        if frame==self.currentFrame:
            return
        self.currentFrame = frame
        if set:
            self.setValuesAt(frame)
        if self.gui:
            self.gui.placeTimeCursor(frame)
            
    # OLD, not used   
    def createFileActor(self, obj, name, scenarioName, function = None,
                        file = None, functionName = "func", nsteps = 0,
                        start = 0, end=-1):
        # Create a special actor whose valueGenerator is based on a function that
        # accepts an integer and returns a value ( function(step) -> value).
        # (nsteps - 1) is the maximum integer accepted by the function.
        # The function can be either imported from a file ( file = "somename.py")
        # or be passed as an argument to this method (function = somefunction).
        # THe function can also be a numeric array or a list.

        # obj - animatable object
        # name - the object's name
        # scenarioName - the name of a scenario interface that "knows" how to create a regular
        # actor for this object (i.e has createActor() method).
        # start - first keyframe of the actor
        # end - last keyframe of the actor ( if end == -1, then the number of frames between
        # first and last keyframes is nsteps-1, or one step per each keyframe).

        from scenario.interpolators import ReadDataInterpolator
        scenario = self.scenarios.get(scenarioName)
        actor = None
        if function is not None:
            if type(function).__name__ in ('ndarray', 'list'):
                if nsteps > 0:
                    nsteps = min(nsteps, len(function))
                else:
                    nsteps = len(function)
            else:
                assert callable(function)
                if nsteps <= 0:
                    warnings.warn("createFileActor(): Number of steps (nsteps) should be > 0 %s ")
                    return None

        elif file is not None:
            import os
            if not os.path.exists(file):
                warnings.warn("createFileActor(): file %s does not exist" % file)
                return None
            modname = os.path.splitext(os.path.basename(file))[0]
            # import function "func" and "nsteps" from the specified module
            mod = __import__(modname)
            if not hasattr(mod, functionName):
                warnings.warn("createFileActor(): Could not import function %s from file %s " % (functionName, file))
                return None
            function = getattr(mod, functionName)
            if nsteps == 0:
                if not hasattr(mod, "nsteps"):
                    warnings.warn("createFileActor(): Number of steps (nsteps) is not specified in file %s " % file)
                    return None
                nsteps=mod.nsteps
            
        if function is None:
            warnings.warn("createFileActor(): Could not create file actor %s - no file or function specified" % name)
            return None
        # get the first and last values returned by the function
        if type(function).__name__ in ('ndarray', 'list'):
            firstVal = function[0]
            lastVal = function[-1]
        else:
            firstVal = function(0)
            lastVal = function(nsteps-1)
        if scenario is not None:
            # create an actor with ReadDataInterpolator valuegenerator
            #try:
            actor = scenario.createActor(obj, name, check=False, addToDirector=False,
                        valueGenerator = (ReadDataInterpolator, (firstVal, firstVal),{}))
            #except:
            #    warnings.warn("Failed to create file actor %s" % name)
            #    return None
            
            if actor:
                if start != 0:
                    actor.keyframes[start] = actor.keyframes[0]
                    #actor.keyframes.pop(0)
                    del(actor.keyframes[0])
                if end < 0:
                    nbframes = nsteps + end
                else:
                    nbframes = end - start
                actor.setKeyframe(start+nbframes, value = lastVal)
                actor.valueGenerators[0].behaviors[0].configure(function = function, nsteps=nsteps)
                oldname = actor.name
                name = oldname + ".file"
                if hasattr(obj, "animatedProperties"):
                    if obj.animatedProperties.has_key(oldname):
                        del (obj.animatedProperties[oldname])
                    obj.animatedProperties[name] = actor
                    
                actor.name = name
                actor.hasGetFunction = False
                actor.recording = False
                
                    
                self.addActor(actor)
        return actor
            


    def createActorFromData(self, obj, propname, scenarioInterface,filename, fields,
                            data, start = 0, end=-1):
        # Create a special actor whose valueGenerator returns values from a data 
        # sequence such as list ar numpy array, This data is read from a file (.adat)->
        # see actor.py/adatFileParser

        # obj - animatable object
        # propname - the object's animated property name
        # scenarioInterface - scenario interface that is n self.scenarios and "knows" how
        # to create a regular actor for this object (i.e has createActor() method).
        # start - first keyframe of the actor
        # end - last keyframe of the actor ( if end == -1, then the number of frames between
        # first and last keyframes is len(data)-1, or one data step per each keyframe).

        if data is None:
            print "createActorFromData: data is None"
            return

        assert scenarioInterface in self.scenarios.values()
        actor = None
        if data is not None:
            assert type(data).__name__ in ('ndarray', 'list')
            nsteps = len(data)
            firstVal = data[0]
            lastVal =  data[nsteps-1]
            #print filename, len(data), data[0], propname
            # create an actor with ReadDataInterpolator valuegenerator
            #try:

            # this will create file actor with two keyframes : "0" and "nsteps-1" 
            actor = scenarioInterface.createActor(obj, propname, check=False,
                                                  addToDirector=False,
                                                  actorData = (filename, data))
            actor.datafields = fields
            #except:
            #    warnings.warn("Failed to create file actor %s" % propname)
            #    return None
            if actor:
                self.addActor(actor)
                #print "start=", start, "end=", end, "nsteps=", nsteps
                if end == -1:
                    end = start + nsteps - 1
                if end != nsteps-1:
                    if self.gui:
                        #this will move "nsteps-1" keyframe  to "end" keyframe 
                        self.gui.selectKeyFrame_cb(actor, nsteps-1, newframe=end)
                if start != 0:
                    if self.gui:
                        # this will move "0" keyframe to "start" keyframe
                        self.gui.selectKeyFrame_cb(actor,0,newframe=start) 
                    
        return actor
            




if __name__=='__main__':
    from datatypes import FloatType
    from interpolators import FloatScalarInterpolator

    class foo:

        def __init__(self):
            self.a= 2.0

    f = foo()

    # create an actor
    actor = Actor('test', f, 0.5, FloatType, FloatScalarInterpolator)
    assert len(actor.keyframeValues) == 1
    assert actor.keyframeValues[0] == 0.5

    # create a director
    d = Director()
    d.addActor(actor)
    
    # run the animation
    print "Run keyframe 0"
    d.run()

    # add a keyframe
    actor.setKeyframe( 10, 10.5)
    print "Run keyframe 0 and 1"
    d.run()

    # add a keyframe at 15
    actor.setKeyframe( 20, 10.5)
    actor.setKeyframe( 25, 5.5)
    assert len(actor.valueGenerators)==4
    assert len(actor.keyframes)==4
    print "Run keyframe 0,1,2,3"
    d.run()

    # stop interpolation between keyframe 1 and 2 (i.e interval 1)
    actor.setValueGenerator( None, segment=1)
    print "Run keyframe 0,1 and 2,3"
    d.run()
    
