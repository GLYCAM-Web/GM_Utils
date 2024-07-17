##
##  Author Michel F. Sanner May 2007
##
import weakref
from sortedDict import SortedDict
from interpolators import Interpolator, BehaviorList
from datatypes import DataType
import types

class Actor:
    """
An Actor is an object that will modify an attribute of a Python Object
over the course of time.
Actors can be added to a Director object. The Director will only allow
the addition of actors with a unique name in its list of actors.

An Actor is created with:
   - a name
   - a given Python object
optionally:
   - an initial value
   - a datatype used to validate value for keyframes
   - default interpolator amd how to create it

The actor has a datatype which is used to valide values for this actor.
Values are stored in a list called value keyframeValues.

Keyframes are stored in a sortedDict whered the key is a frame number
and the value is an index into actor.keyframeValues

Actor.valueGenerators provides a list of interpolator objects, one for
each segment between 2 consecutive keyframes. Setting one of these
interpolators to None in this list results in no interpolation (i.e.
no value will be sent to the Python object for these frames).

Actors can be made active/inactive for playback.
Actors that know how to retrieve the value from the Python object
can be made active/inactive for recording keyframes.
"""

    def __init__(self, name, object, initialValue=None, datatype=None, interp=None):

	self.object = object
        self.name = name # actor name, has to be unique in Director.actors
        self._director = None  # will be a weakref to the director when added
        self.hasGetFunction = False # set to true is actor knows how to get the
                                    # value from the object
        self.recording = False # true if this actor will record keyframes
        self.playing = True  #true if the actor will set the values

        if datatype is not None:
            assert issubclass(datatype, DataType)
            self.datatype = datatype()
        else:
            self.datatype = None

        self.keyframeValues = [initialValue]
        #print "initial kf value: ", initialValue 
        self.keyframes = SortedDict()
        self.keyframes[0] = 0    # value of key frames are in keyframeValues
        # array of interpolators, one for each segment
        self.valueGenerators = []

        self.nbvar = None    # number of variable that are interpolated
        self.varnames = []
        self.activeVars = [] # list of booleans allowing to turn particular
                             # variables on or off
        self.interpClass = None
        if interp is not None:
            try:
                interpClass, args, kw = interp
                assert issubclass(interpClass, Interpolator)
                assert isinstance(args, tuple)
                assert isinstance(kw, dict)
            except TypeError:
                interpClass = interp
                assert issubclass(interpClass, Interpolator)
                args = (initialValue, initialValue)
                kw = {}
            interpolator = interpClass( *args, **kw) 
            bl = BehaviorList(*args, **{'actor':self})
            bl.addBehavior(interpolator)
            bl.configure(active = False)
            self.valueGenerators.append( bl )
            
            self.nbvar = interpClass.nbvar
            self.varnames = interpClass.varnames
            if self.nbvar:
                self.activeVars = [1]*self.nbvar
            self.interpClass = interpClass
##         else:
##             self.valueGenerators = [None]
##             self.nbvar = 0
##             self.varnames = []
##             self.activeVars = []

        # FIXME should really be sub-classed methods
        self.preStep_cb = None
        self.postStep_cb = None

        # GUI variable
        self.visible = True
        self.displayFunction = False
        self.graphHeight = 40
        self.valueFormat = None
        self.scenarioname = None
        self.linkedKeyFrames = [[],] # a list of lists of key frames that share the value:
                                     # there is list in the linkedKeyFrames for each item
                                     # in self.keyframeValues list. It will be empty []
                                     # if the corresponding value is not shared between
                                     # keyframes.
        # example: self.keyframes = {10: 0, 23:1, 40:2 , 50:0}
        #          self.keyframeValues = [a, b, c]
        #          self.linkedKeyFrames = [[10, 50],[],[]]
        #          i.e keyframeValues[0] is shared by keyframes 10 and 50
        
        self.linkedVG = [[],] # a list of lists(one for each interpolation segment)
                              # containing indices of segments that have
                              # the same value generator.
        # example: self.valueGenerators = [vg1,  vg2, vg3, vg1, vg4, vg2]
        #                   segmentinds = [ 0 ,   1,   2,   3,   4,  5  ]
        #                 self.linkedVG = [[3,],[5,], [], [0,], [], [1] ]
        self.kfSetId = {}


    def isFullRange(self):
        if len(self.valueGenerators) ==0 or \
           (self.valueGenerators[0].active and \
            self.valueGenerators[-1].active): return True
        return False


    def getLastFrame(self):
        # if not interpolation right of last keyframe, last keyframe is there
        # else last keyframe is end of animation
        if self._director:
            last = self._director().getLastFrame()
            
        if len(self.valueGenerators):
            last = self.keyframes._sortedKeys[-1]

        return last


    def getValueGenerator(self, frame):
        # return the value geenrator for any given frame
        inter, k1, k2, valGen = self.getInterval(frame)
        return valGen


    def setValueGenerator(self, generator, segment=0):
        # set a value generator for an interval
        assert generator is None or isinstance(generator, Interpolator)
        vg = self.valueGenerators
        assert segment < len(vg)
        oldGenerator = vg[segment]
        vg[segment] = generator
        return oldGenerator
    
        
    def getInterval(self, frame):
        # return the index of the interval between keyframes k1, k2
        # into which frame falls and the value generator for this interval
        # interval start at k1 and go to the frame before k2
        # k2 is None for the interval beyond the last 
        # generator can be None when there is not interpolation
        keys = self.keyframes._sortedKeys
        interval = -1
        if frame < 0:
            raise ValueError, "got negative frame number"
        else:
            for k in keys:
                if k<=frame:
                    interval += 1
                else:
                    break
        if interval<len(keys)-1:
            k2 = keys[interval+1]
        else:
            k2 = None
        if interval == -1:
            k1 = None
            valgen = None
        else:
            k1 = keys[interval]
            valgen = self.valueGenerators[interval]

        return interval, k1, k2, valgen


    def setKeyframe(self, frame, value=None, valueIndex=None, vgIndex = None):
        # set a keyframe at position: frame
        # if there is a keyframe there, overwrite it
        # if value is specified add the value to the list
        # else use the value self.keyframeValues[valueIndex]
        
        #print "in setKeyframe: frame:", frame, "valueIndex=", valueIndex, "vgIndex =", vgIndex 
        assert isinstance(frame, int)
        
        if valueIndex:
            assert valueIndex>=0 and valueIndex<len(self.keyframeValues)
        # we need to do this before we update self.keyframes
        linkinterval = False
        if vgIndex is not None and valueIndex is not None:
            linkinterval = True
        copyinterval = False
        if vgIndex is not None and valueIndex is None:
            copyinterval = True
        interval, k1, k2, valGen = self.getInterval(frame)
        
        if frame == k1: #overwrite keyframe
            if value is None:
                if valueIndex is not None:
                    assert valueIndex>=0 and valueIndex<len(self.keyframeValues)
                    value = self.keyframeValues[valueIndex]
            if value is not None:
                self.keyframeValues[self.keyframes[frame]] = value
                # look for other frames with the same value index:
                valind = self.keyframes[frame]
                samevalframes = [frame]
                for f in self.linkedKeyFrames[valind]:
                    if f != frame:
                        samevalframes.append(f)
                for i, frame in enumerate(samevalframes):
                    if i > 0:
                        interval, k1, k2, valGen = self.getInterval(frame)
                    if k2 == None and len(self.keyframes)-1 == interval:
                        # this is the last interval
                        valGen.configure(firstVal = value, lastVal = value)
                    else:
                        valGen.configure(firstVal = value)
                    if interval > 0:
                        # find and update the interpolator for the interval before current
                        _valGen = self.getValueGenerator(self.keyframes._sortedKeys[interval-1])
                        _valGen.configure(lastVal = value)
                        
            return
        #print interval, k1, k2, valGen
        # find out if current interval is linked with some other intervals:
        segments = [[interval, frame],]
        linkedVG = self.linkedVG
        if interval >= 0:
            diff = frame - k1
            kf = self.keyframes
            skf = kf._sortedKeys
            if len(linkedVG[interval]):
                for ii in linkedVG[interval]:
                    kk1 = skf[ii]
                    kk2 = skf[ii+1]
                    if  kf[kk1] == kf[k1] and kf[kk2] == kf[k2]:  
                        if kk2 - kk1 == k2- k1:
                            segments.append([ii, kk1+diff])
                segments.sort()
                segments.reverse()
                
        if value is None:
            value = self.keyframeValues[valueIndex]
        else:
##             # datatypes are incompatible with numpy - FIX THIS
##             if self.datatype.valide(value):
##                 self.keyframes[frame] = len(self.keyframeValues)
##                 self.keyframeValues.append(value)
##             else:
##                 print 'WARNING: bad keyframe value', value, 'at:', frame, self.datatype
##                 return
            valueIndex = len(self.keyframeValues)
            self.keyframeValues.append(value)
            self.linkedKeyFrames.append([])
        # update value generators
        if linkinterval:
            newGen = self.valueGenerators[vgIndex]
        elif copyinterval:
            newGen  = self.valueGenerators[vgIndex].clone()
            newGen.configure(lastVal=value)
        else:
            if interval < 0:  # the first actors' keyframe != 0; a new keyframe is created on
                              # the interval before current first keyframe.
                # we will clone the first available value generator:
                
                valGen = self.valueGenerators[0]
                newGen = valGen.clone()
                newGen.configure(firstVal = value, lastVal=valGen.firstVal, active = True)
            else:    
                newGen = valGen.clone()
                newGen.configure(lastVal=value, active = True)
        if interval >= 0:
            valGen.configure(firstVal=value)
        if k2 is None:
            valGen.configure(lastVal=value)

        nsegments = len(segments)
        # find all existing kfSets for this actor
        setid = []
        if len(self.kfSetId):
            for id in self.kfSetId.values():
                if id not in setid:
                    setid.append(id)
        for interval, frame in segments:
            # insert new value generator for interval between k1 and frame:
            if interval < 0: interval = 0
            self.valueGenerators.insert(interval, newGen)
            self.keyframes[frame] = valueIndex
            if nsegments > 1: # we are adding more than 1 frame with the same value index 
                if frame not in self.linkedKeyFrames[valueIndex]:
                    self.linkedKeyFrames[valueIndex].append(frame)
            # this frame might be behind the last one of the animation
            if self._director:
                if self._director().getLastFrame() <= frame:
                    self._director().updateEndFrame( frame )
            
            if linkinterval:
                lvg = [vgIndex]
                lvg.extend(linkedVG[vgIndex])
                for item in lvg:
                   linkedVG[item].append(interval)
                linkedVG.insert(interval, lvg )
                if vgIndex > interval: vgIndex = vgIndex +1
            else:
                linkedVG.insert(interval+1, [])
            # update linkedVG
            for i, item in enumerate(linkedVG):
                for j, vgind in enumerate(item):
                    if vgind > interval:
                        linkedVG[i][j] = vgind+1
            # check if the frame gets inside any of the kfSets:
            if len(setid):
                if self._director:
                    director = self._director()
                    for id in setid: 
                        kfset = director.gui.kfSets[id]
                        if kfset.addFrame(self.name, frame):
                            self.kfSetId[frame] = id
        if vgIndex == None and nsegments > 1: 
            # we need to link all new segments
            kf = self.keyframes._sortedKeys
            lintervals = []
            for item in segments:
                frame = item[1]
                lintervals.append(kf.index(frame))
            for i in lintervals:
                for j in lintervals:
                    if i != j:
                        linkedVG[i].append(j)
        #print "value generators:", self.valueGenerators
        #print "keyframes:", self.keyframes
        #print "linekdKF:", self.linkedKeyFrames
        #print "linkedVG:", self.linkedVG 


    def getValueAt(self, frame):
        # return the (value, interval, valGen) tuple
        # interval is the index of the interval between keyframes in which
        # frame falls. valGen is a value generator object such as an
        # interpolator
        # both interval, valGen are -1 on keyframe positions

        if self.keyframes.has_key(frame):
            return self.keyframeValues[self.keyframes[frame]], -1, -1
        
	# find the interval for this frame
        interval, k1, k2, valGen = self.getInterval(frame)
        if interval < 0:
            value = self.keyframeValues[self.keyframes[k2]]
            return value, -1, None
        if not valGen.active:
            value = self.keyframeValues[self.keyframes[k1]]
            return value, interval, valGen
        else:
            if k2 is None:
                if self._director is not None:
                    k2 = self._director().getLastFrame()
                else:
                    k2 = 0
        if k1==k2:
            fraction = 1.0
        else:
            fraction = (frame-k1)/float(k2-k1)
        value = valGen.getValue(fraction)
        return value, interval, valGen


    def setValue(self, value):
        # is called at each time step if the actor's readMode is active
        from SimPy.Simulation import now
        print 'setting ', self.name, 'for', self.name, 'at:', now(), 'to', value

    def deleteKeyFrame(self, frame):
        # remove specified keyframe and the interpolation segment to the right
        # of it.
        if not self.keyframes.has_key(frame):
            print "Warning no keyframe %d found for actor %s"%(frame, self.name)
            return
        #if frame == 0:
        #    print "Warning: Can not remove keyframe 0 of actor", self.name
        #    return
        frames = self.keyframes._sortedKeys
        vg = self.valueGenerators
        linkedVG = self.linkedVG
        linkedKF = self.linkedKeyFrames

        # delete valuegenerator of the interval to the right of the selected frame:
        ind = frames.index(frame)
        isLast = False
        if ind == len(frames)-1: # we are removing the last valuegenerator
            isLast = True
        valgen = vg.pop(ind)
        # value generator of the interval to the left of the selected frame:
        if ind > 0:
            valgenl = vg[ind-1]
        else:
            valgenl = None
        # update linkedVG:
        # remove all occurences of the deleted valuegenerator index from linkedVG lists: 
        for lvg in linkedVG[ind]:
            if ind in linkedVG[lvg]:
                linkedVG[lvg].remove(ind)
        linkedVG.pop(ind)
        # reindex linkedVG:
        for i, item in enumerate(linkedVG):
            for j, vgind in enumerate(item):
                if vgind > ind:
                    linkedVG[i][j] = vgind-1
        valind = self.keyframes[frame]
        del(self.keyframes[frame])
        # remove the keyframe value from self.keyframeValues list:
        #if not self.keyframes.values().count(valind):
        if len(linkedKF[valind]):
            #remove frame from the list of linked frames:
            linkedKF[valind].remove(frame)
        if not len(linkedKF[valind]):
            # there is no other key frame that shares the value - remove the value
            value = self.keyframeValues.pop(valind)
            linkedKF.pop(valind)
            # update the value indices of the self.keyframes dict:
            for f, i in self.keyframes.items():
                if i > valind:
                   self.keyframes[f] = i-1
        elif len(linkedKF[valind]) == 1:
            linkedKF[valind] = []
        # reconfigure value generator (valgenl) of the interval to the left of the
        # deleted keyframe
        if valgenl:
            if isLast:
                valgenl.configure(lastVal = valgenl.firstVal, active = False)
            else:
                valgenl.configure(lastVal = valgen.lastVal)
        if self.kfSetId.has_key(frame):
            del(self.kfSetId[frame])


    def compareValues(self, oldval, newval):
        res = False
        if self.datatype is not None:
            res = self.datatype.isEqual(oldval, newval)
        return res


    def findSelectedIntervals(self, frames):
        # group contiguously selected keyframes:
        # example:
        # if all frames of the actor are : ff = [5, 12, 20, 28, 35, 40, 55, 65, 70]
        # and  the selected frames are          [   12, 20, 28,         55, 65],
        # we group them like this: sf = [[12, 20, 28], [55, 65]]
        tmp = []
        ff = self.keyframes._sortedKeys # all actor's frames 
        ind2 = 0
        sf = []
        nframes = len(frames)
        for ind1, f1 in enumerate(ff):
            if ind2 < nframes:
                if f1 == frames[ind2]:
                    ind2 = ind2 +1
                    tmp.append(f1)
                else:
                   if len(tmp):
                       sf.append(tmp)
                       tmp = []
            else:
                break
        if len(tmp):
            sf.append(tmp)
            
        return sf


    def getDistance (self, frames):
        # find out how far to the left/right can selected group of keyframes move
        kf = self.keyframes._sortedKeys
        intervals = self.findSelectedIntervals(frames)
        lframes = None # number of frames we can move the selection to the left 
        rframes = None # ------------------------------------------------ right
        for interval in intervals:
            f1 = interval[0]
            f2 = interval[-1]
            ind1 = kf.index(f1)
            ind2 = kf.index(f2)
            if ind1 == 0 : # this is the very first actor's keyframe 
                lf  = -1
            else:
                lf = kf[ind1-1]
            if lframes is None:
                lframes = f1 - lf
            else:
                lframes = min(f1 - lf, lframes)
            if ind2 !=len(kf)-1: # not last key frame of the actor
                if rframes is None:
                    rframes = kf[ind2+1] - f2
                else:
                    rframes = min(kf[ind2+1] - f2, rframes)
        return lframes, rframes

            
    def unlinkKeyFrames(self, frames):
        kfset = None # if specified keyframes are linked with keyframes from only one
                     # other kfset , this variable (kfset).
        nframes = len(frames)
        sortedkf = self.keyframes._sortedKeys
        
        for ff in frames:
            valind = self.keyframes[ff]
            value = self.keyframeValues[valind]
            self.keyframeValues.append(value)
            self.linkedKeyFrames.append([])
            self.keyframes[ff] = len(self.keyframeValues) - 1
            if ff in self.linkedKeyFrames[valind]:
                self.linkedKeyFrames[valind].remove(ff)
            setid = self.kfSetId.get(ff)
            if setid is not None:
                del(self.kfSetId[ff])
            if len(self.linkedKeyFrames[valind]) == 1:
                lf = self.linkedKeyFrames[valind].pop(0)
                lsetid = self.kfSetId.get(lf)
                if lsetid is not None:
                    if kfset is None:
                        kfset = lsetid
                    if kfset != lsetid:
                        print "WARNING : keyframes of set %d are linked with keyframes of %d and %d sets" %(setid, kfset, lsetid) 
                    del(self.kfSetId[lf])
            
        if nframes > 1:
            ind = sortedkf.index(frames[0])
            for i in range (nframes-1):
                vg = self.valueGenerators[ind]
                lvg = self.linkedVG[ind]
                if len(lvg):
                    #newvg = vg.__class__(vg.firstVal, vg.lastVal, vg.interpolation)
                    newvg = vg.clone()
                    self.valueGenerators[ind] = newvg
                    for lvgind in lvg:
                        self.linkedVG[lvgind].remove(ind)
                    self.linkedVG[ind] = []
                ind = ind+1
        return kfset


    def onAddToDirector(self):
        pass


    def replaceInterpolator(self, interpolator, segment = 0,
                            updateKeyFrames = True, nbframes = 0):
        
        assert isinstance(interpolator, Interpolator)
        vg = self.valueGenerators
        assert segment < len(vg)
        oldinterpolator = vg[segment].behaviors[0]
        sortedframes = self.keyframes._sortedKeys
        kf1 = sortedframes[segment]
        if segment == len(sortedframes)-1:
            kf2 = None
        else:
            kf2 = sortedframes[segment+1]
        print "kf1=", kf1, "kf2=", kf2
        if kf2 is None:
           #last interval - add a keyframe ???
           if nbframes == 0: nbframes = 50
           kf2 = kf1 + nbframes
           self.setKeyframe(kf2, value = self.getValueAt(kf2)[0])
           if self._director is not None:
               gui = self._director().gui
               if gui is not None:
                   gui.deleteActor(self)
                   gui.drawActor(self, self._posy)
           
        if updateKeyFrames:
            # set the keyframe values to the values returned by the value generator at 0 and 1
            # fractions
            vg[segment].behaviors[0]= None
            self.setKeyframe(kf1, value = interpolator.getValue(0))
            self.setKeyframe(kf2, value = interpolator.getValue(1))
            vg[segment].behaviors[0] = interpolator
        else:
            vg[segment].behaviors[0] = interpolator
            # configure first and last values of the interpolator
            vg[segment].configure(firstVal = self.keyframeValues[self.keyframes[kf1]])
            vg[segment].configure(lastVal = self.keyframeValues[self.keyframes[kf2]])
        return oldinterpolator



class CustomActor(Actor):

    def __init__(self, name, object, initialValue=None, datatype=None,
                 interp=None, setFunction=None, getFunction=None):
        """
Constructor of the Actor object,

arguments:
    object:            Python object on which to operate
    name:              Name of this Actor,  This name has to be unique
                       among the list of ActorDescriptor in an Director
    setFunction:       function to called at each time step.
                       The function will be called using  func(*(actor,value))
    getFunction=None:  [optional] function that can be called to get the
                       current value of the attribute managed by this actor
                       The function and its arguments have to be specified as a
                       3-tuple (func, *args, **kw). It will be called using
                       func(*(object,)+args), **kw) if it is a function
                       or func(*args, **kw) if it is a method
   interp              interpreter class
   initialValue        initial value of the attribute
   dataType            type of the attribute value 
   """
        
        self.getFuncTuple = None
        self.hasGetFunction = False
        if setFunction:
            assert callable(setFunction)
        self.setFunction = setFunction

        if getFunction:
            self.getFuncTuple = self.checkFunction(getFunction)
            
        self.object = object
        if initialValue is None:
            if self.getFuncTuple:
                initialValue = self.getValueFromObject()
        Actor.__init__(self, name, object, datatype=datatype,
                       initialValue=initialValue, interp=interp)
        if self.getFuncTuple:
            self.hasGetFunction = True

    def checkFunction(self, function):
        # check that functionTuple is of form (func, (), {})
        try:
            f, args, kw = function
            assert callable(f)
            assert isinstance(args, tuple)
            assert isinstance(kw, dict)
        except TypeError:
            assert callable(function)
            f, args, kw = function, (), {}
        return f, args, kw

   
    def getValueFromObject(self):
        # this function gets the current value of the attribute from the object
        # and returns it
        if not self.getFuncTuple:
            return None
        f, args, kw = self.getFuncTuple
        if type(f) == types.FunctionType or type(f) == types.BuiltinFunctionType:
            # add object as first argument to functions
            return f(*(self.object,)+args, **kw)
        elif type(f) == types.MethodType:
            return f(*args, **kw)


    def setValue(self, value):
        # call the function to set the value on the object
        if self.setFunction:
            self.setFunction( *(self, value) )

import os
import warnings
import numpy

class FileActor(Actor):
    """ special actor class created from file data"""
    
    def __init__(self, name, object, baseclass, actordata , *args, **kw):

        if kw.has_key('getFunction'):
            kw['getFunction'] = None
        filename = actordata[0]
        from scenario.interpolators import ReadDataInterpolator
        data = actordata[1]
        if data is not None:
            assert type(data).__name__ in ('ndarray', 'list')
            firstVal = data[0]
            lastVal =  data[-1]
        kw['interp'] = (ReadDataInterpolator, (firstVal, firstVal),{})
        kw['initialValue'] = firstVal
        #print "FileActor:kw ", kw
        self._baseactor = apply(baseclass, (name, object)+args, kw)
        self.filename = os.path.abspath(filename)
        oldname = self.name
        self.name = oldname + ".file"
        self.hasGetFunction = False
        # create a second frame
        self.setKeyframe(len(data)-1, value = lastVal)
        self.valueGenerators[0].behaviors[0].configure(function = data)
        self.recording = False
        self.datafields = None
                         
        

    def __getattr__(self, name):
        return getattr(self._baseactor, name)

    def  setValue(self, value):
      self._baseactor.setValue(value)  


class adatFileParser:
    """Class to parse .adat files contaning actors data.
    File format description:
    NSTEPS nsteps
    FIELDS fieldname1, fieldname2, .....fieldnameN
    TYPES type1, type2, .....typeN
    FRAME 0
    val01, val02, ....val0N
    valK1, valK2, ....valKN
    
    FRAME 1
    val01, val02, ....val0N
    valL1, valL2, ....valLN
     ...................
    FRAME nsteps-1
    val01, val02, ....val0N
    valM1, valM2, ....valMN
    
    Example:

    NSTEPS 50
    FIELDS r g b x y z
    TYPES float float float float float float
    FRAME 0
    0.0 0.0 1.0 0.5 1.0 0.2
    0.0 0.9 0.9 0.5 1.5 0.2 
    .........
    FRAME 49
    1.0 0.0 0.0 1.0 1.5 0.5
    """
    # supported data types : 
    dtypesDict = {'int': int, 'int32': int, 'int64': int, 'float': float, "float32":float, "float64":float, "bool":bool}
    
    def __init__(self, file):
        self.data = {}
        self.nsteps = 0
        self.fields = []
        self.dtypes = []
        self.file = None
        if (os.path.exists(file)):
            self.file = file
        else:
            warnings.warn("File %s does not exist" % file)
        if self.file:
            self.readAdatFile(file)


    def readAdatFile(self, file):
        f=open(file, "r")

        for i in range(3):
            line = f.readline().split()
            if line[0] == "NSTEPS":
                nsteps = self.nsteps= int(line[1])
            elif line[0] == "FIELDS":
                fields = self.fields = line[1:]
            elif line[0] == "TYPES":
                for n in range(1, len(line)):
                   dtypes = self.dtypes = line[1:]
            else:
                warnings.warn("adatFileParser: Wrong file format %s; First 3 lines should contain NSTEPS,FIELDS and TYPES\n" % file)
                return
        if not nsteps:
            warnings.warn("adatFileParser: NSTEPS is not specified %s \n" % file)
            return
        if not len(fields):
            warnings.warn("adatFileParser: FIELDS are not specified %s \n" % file)
            return
        if not len(dtypes):
            warnings.warn("adatFileParser: TYPES are not specified %s \n" % file)
            return
        assert len(dtypes) == len(fields)
        for tp in dtypes:
            if not self.dtypesDict.has_key(tp):
                warnings.warn("adatFileParser: type %s is not supported \n" % fld)
                return
        framedata = {}
        for fld in fields:
            
            self.data[fld] = []
            framedata[fld] = []
        lines = f.readlines()
        assert lines[0].startswith("FRAME")
        frame = 0
        nlines = len(lines)
        #print "nlines:", len(lines)
        #print "nsteps:", nsteps
        for line in lines[1:]:
            if line.startswith("FRAME"):
                for i, fld in enumerate(fields):
                    t = getattr(numpy, dtypes[i])
                    if len(framedata[fld])>1:
                        self.data[fld].append(numpy.array(framedata[fld], dtype = t))
                    else:
                        self.data[fld].append(framedata[fld][0])
                    framedata[fld] = []
                frame = frame+1
            else:
                for i, st in enumerate(line.split()):
                    framedata[fields[i]].append(self.dtypesDict[dtypes[i]](st))

        # last frame            
        for i, fld in enumerate(fields):
            t = getattr(numpy, dtypes[i])
            if len(framedata[fld])>1:
                self.data[fld].append(numpy.array(framedata[fld], dtype = t))
            else:
                self.data[fld].append(framedata[fld][0])
            
        #print "last line", line
        #print "last frame" , frame
        f.close()

    
    def getFieldsData(self, fields):
        # fileds can be a string corresponding to one field or a list of fields
        # Examples : "radii",   ['r', 'g', 'b']

        # returns a list of values of the specified field(s)
        # if len(fields) > 1 , create a numpy array from each frame data :
        # frame0 = numpy.array([[Fieldval1, Fieldval2, ....FildvalN],
        #                       ...................................
        #                       [Fieldval1, Fieldval2, ....FildvalN]] )
        # ..................................................
        # frameNsteps-1 = numpy.array([[Fieldval1, Fieldval2, ....FildvalN],
        #                               ...................................
        #                              [Fieldval1, Fieldval2, ....FildvalN]] )
        # return [frame0, .....,frameNsteps-1]
        
        if fields is None:
            return None
        if len(self.data) == 0: return None
        import types
        if type(fields) == types.StringType:
           fields = [fields]
           nfields = 1
        else:
            nfields = len(fields)

        for f in fields:
            if f not in self.fields:
                warnings.warn("field %s is not known" % f)
                return None
        data = self.data
        if nfields == 1 :
            return data[fields[0]]
        elif nfields > 1:
            res = []
            for i in range(self.nsteps):
                if hasattr(data[fields[0]][i], "__len__"):
                    framedatalen = len(data[fields[0]][i])
                    for f in fields:
                        assert len(data[f][i]) == framedatalen
                    arr = numpy.concatenate((data[fields[0]][i], data[fields[1]][i]))
                    for f in fields[2:]:
                        arr = numpy.concatenate((arr, data[f][i]))
                    arr = arr.reshape(nfields, framedatalen).transpose()
                    res.append(arr)
                else:
                    arr = []
                    for f in fields:
                        arr.append(data[f][i])
                    ind = self.fields.index(f)
                    t = getattr(numpy, self.dtypes[ind])
                    res.append(numpy.array([arr], dtype = t))
            return res
        
    

    


        
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

    assert len(actor.keyframes)==1
    k,v = actor.keyframes.items()[0]
    assert k==0
    assert v==0

    # check that frame 0 is in interval
    inter, k1, k2, valGen = actor.getInterval(0)
    assert inter==0
    assert k1==0
    assert k2==None

    # check that frame 10 is in interval
    inter, k1, k2, valGen = actor.getInterval(10)
    assert inter==0
    assert k1==0
    assert k2==None

    # check the values we get at 0
    val, inter, valGen = actor.getValueAt(0)
    assert val==0.5
    assert inter==-1
    assert valGen==-1

    # add a keyframe at 10
    actor.setKeyframe( 10, 10.5)
    assert len(actor.keyframeValues) == 2
    assert actor.keyframeValues[1] == 10.5

    # make sure the actor's last frame is correct
    assert actor.getLastFrame()==10
    
    # check the keyframe positions
    assert actor.keyframes[0]==0
    assert actor.keyframes[10]==1

    # check the starting and ending values of the interpolators
    assert actor.valueGenerators[0].firstVal==0.5
    assert actor.valueGenerators[0].lastVal==10.5
    assert actor.valueGenerators[1].firstVal==10.5
    assert actor.valueGenerators[1].lastVal==10.5

    # check that we get the right interval for 0, 5 and 15
    inter, k1, k2, valGen = actor.getInterval(0)
    assert inter==0
    assert k1==0
    assert k2==10
    assert valGen==actor.valueGenerators[0]
    
    inter, k1, k2, valGen = actor.getInterval(5)
    assert inter==0
    assert k1==0
    assert k2==10
    assert valGen==actor.valueGenerators[0]

    # at 10 we should get the second interval
    inter, k1, k2, valGen = actor.getInterval(10)
    assert inter==1
    assert k1==10
    assert k2==None
    assert valGen==actor.valueGenerators[1]
    
    inter, k1, k2, valGen = actor.getInterval(15)
    assert inter==1
    assert k1==10
    assert k2==None
    assert valGen==actor.valueGenerators[1]
    
    # check the values we get
    val, inter, valGen = actor.getValueAt(0)
    assert val==0.5
    assert inter==-1 # we are on a keyframe
    assert valGen==-1 

    val, inter, valGen = actor.getValueAt(10)
    assert val==10.5
    assert inter==-1
    assert valGen==-1
    
    val, inter, valGen = actor.getValueAt(5)
    assert val==5.5
    assert inter==0
    assert valGen==actor.valueGenerators[0]
    
    
    # add a keyframe at 20

    # insert a keyframe at 15
