import weakref

class KFSet:
    """A container for a set of keyframes created by 'linked paste/insert' operation. This
       enables the user to operate on these keyframes as a whole.
       For example, right-clicking on a single frame in such a set will
       highlight all keyframes belonging to this set and open a menu. 
       The menu will allow the user to delete either this single keyframe or the 
       whole set, or select the set for moving, which will cause a yellow filled box to 
       be drawn around this set. Clicking and dragging this box will move the 
       whole block of frames"""

    def __init__(self, selection, id, director):

        # selection  is a list: [ [actor1, [kf1, ...kfN]],...]
        self.Id =  id
        self._director = weakref.ref(director)
        minf = director.getLastFrame()
        maxf = 0
        self.setActors = setActors = []
        self.setframes = setframes = []
        for item in selection:
            actor = item[0]
            if actor:
                kf = [actor,]
                kf.extend(item[1])
                minf = min(minf, kf[1])
                maxf = max(maxf, kf[-1])
                setframes.append(kf)
                setActors.append(actor.name)
                for ff in item[1]:
                    actor.kfSetId[ff] = id
        self.bbox = [minf, maxf]


    def isFrameInSet(self, keyframe):
        if keyframe >= self.bbox[0] and keyframe <= self.bbox[1]:
            return True
        else:
            return False


    def computeBbox(self):
        minf = maxf = self.setframes[0][1]
        for item in self.setframes:
            minf = min(minf, min(item[1:]))
            maxf = max(maxf, max(item[1:]))
        self.bbox = [minf, maxf]
            

    def updateOneFrame (self, actorname, kfold, kfnew):
        if not self.isFrameInSet(kfold):
            print "WARNING: keyframe %d is not in KFSet %d:" % (kfold, self.Id)
        minf, maxf = self.bbox
        for item in self.setframes:
            if item[0].name == actorname:
                ind = item.index(kfold)
                item[ind] = kfnew
                if kfold == minf or kfold == maxf:
                    #find new bbox
                    self.computeBbox()
                else:
                    if kfnew < minf: self.bbox[0] = kfnew
                    elif kfnew > maxf: self.bbox[1] = kfnew
                break


    def updateFrames(self, nframes):
        for item in self.setframes:
            for i in range(1, len(item)):
                item[i] += nframes
        self.bbox[0] += nframes
        self.bbox[1] += nframes


    def getNumberOfFrames(self):
        return sum(map (lambda x: len(x)-1, self.setframes))


    def removeKeyFrame(self, actorname, frame):
        minf, maxf = self.bbox
        findMinMax = False
        removeItem = None
        if frame == minf or frame == maxf:
            findMinMax = True
            minf = self.bbox[1]
            maxf = 0
        for i, item in enumerate(self.setframes):
            if item[0].name == actorname:
                if len(item) == 2:
                    # remember to remove this actor entry from self.setframes
                    removeItem = i
                    self.setActors.remove(actorname)
                    continue
                else:
                    item.remove(frame)
            if findMinMax:
                minf = min(minf, item[1])
                maxf = max(maxf, item[-1]) 
        if findMinMax:
            self.bbox = [minf, maxf]
        if removeItem is not None:
            self.setframes.pop(removeItem)


    def addFrame(self, actorname, frame):
        # we will only add a keyframe to the set if it falls between
        # two existing frames of the actor
        if not self.isFrameInSet(frame):
            return False
        for item in self.setframes:
            if item[0].name == actorname:
                nkf = len(item) - 1
                if nkf == 1: # just one keyframe
                    return False
                for i in range(1, nkf):
                    if frame > item[i] and frame < item[i+1]: 
                        item.insert(i+1,frame)
                        return True
        return False

    
            
        
