## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

import Tkinter
import Pmw
from mglutil.util.callback import CallbackFunction
import numpy.oldnumeric as Numeric
#from scenario.interpolators import RotationInterpolator
from scenario.datatypes import BoolType
import types

class InterpGUI:

    def __init__(self, gui=None,graphHeight=40):

        if not gui:
            scrolledCanvas = Pmw.ScrolledCanvas(
                root, canvas_width=600, canvas_bg='white',
                vscrollmode='static', hscrollmode='static',
                horizscrollbar_width=10, vertscrollbar_width=10)
            self.canvas = scrolledCanvas.component('canvas')
            self.scale = 10.0
        else:
            self.canvas = gui.canvas
            self.scale = gui.scale
        self.gui = gui
        self.graphHeight = graphHeight
        self._funcValId = None
        self.ovalSize = 2
        self.status = None
        self.Button1Func = None # this variable is used to save the function that has been bound to
                                # <Button-1> event of the canvas widget
        self.updatingIntervals = []

    def configure(self, **kw):
        h = kw.get("graphHeight")
        if h is not None:
            self.graphHeight = h

    
    def drawFunctionComponent(self, valgen, indx, frames, scale, actor, posx, posy, ymin, yrange,drawLastVal=False ):
        name = actor.name
        c = self.canvas
        firstVal = valgen.firstVal
        #lastVal = valgen.lastVal
        #print  "drawFunctionComponent:", valgen, frames, posy, ymin, yrange, self.graphHeight
        # FIX: VarVectorInterpolator:
        # values are 2d arrays - do not know how to draw this..
        if isinstance(firstVal, Numeric.ArrayType):
            if len(firstVal.shape) == 2:
                print "WARNING: cannot draw function for interval %d of actor %s between frames: " % (indx, name),  frames
                return None
        graphHeight = self.graphHeight
        lcoords = []
        nbvar = valgen.nbvar
        if nbvar > 4:
            nbvar = 4

        everyPoint = True
        if  hasattr(valgen, "invertVal"): # FIX THIS
            # this is true for the Rotation interpolator:
            vv = valgen.getValue(0.5) # this is needed to see if we had to invert values
            if valgen.invertVal:
                # this happens when the lastVal was inverted for computing
                # interpolation values for this interval
                # (RotationInterpolator.getValue() in interpolators.py)
                everyPoint = False 
        lcoords = self.computeLineCoords(frames[0], frames[1], valgen, posx, posy, ymin, yrange, nbvar, everyPoint = everyPoint)
        alterFuction = True
        if  hasattr(valgen, "alterFunction"):
            alterFuction = valgen.alterFunction
        for n, coords in enumerate(lcoords):        
            funcId = 'actorFunc_'+name+'_%d'%n
            cid = c.create_line( *coords, **{'width':1,
                'tags':('actor_'+name, 'actorFunc_'+name, "%s_%d"% (funcId, indx)) } )
            cb = CallbackFunction(self.mouseEnterFunc, valgen, name, ymin[n], yrange[n], n, frames, posy)
            c.tag_bind(cid, '<Enter>', cb)
            size = self.ovalSize
            # draw an oval repesenting value of a keyframe
            for i,t,f  in zip((0, len(coords)-2), ("firstVal", "lastVal"), frames):
                dotId = funcId+"_dot%d"%f
                if t == "lastVal":
                    if not drawLastVal:
                        continue
                x = coords[i]
                y = coords[i+1]
                #print "creating oval:", x, y, t

                c.create_oval( x-size,y-size, x+size, y+size, fill='black',
                      tags=('actor_'+name, 'actorFunc_'+name, dotId, t, "frame_%d"%f))
            
                c.tag_bind(dotId , '<Enter>',
                           CallbackFunction(self.showFuncDotVal, valgen, name ,n))
                if alterFuction:
                    c.tag_bind(dotId, '<Button-1>',
                           CallbackFunction(self.selectDotVal, indx, actor, n, frames))
                    c.tag_bind(dotId, '<B1-Motion>',
                           CallbackFunction(self.moveFuncDotVal, valgen, name, n, posy, ymin[n], yrange[n]))
                    c.tag_bind(dotId , '<ButtonRelease-1>',
                           CallbackFunction(self.setFuncDotVal, valgen, actor, frames, n, posx, posy, ymin, yrange))

        ## can't use tool tip as it takes over enter event hence we loose
        ## the ability to display the numerical value
        #name = actor.actions[0].interpolator.varnames[vnum]
        #self.balloons.tagbind(c, funcId, name, '+')
        #posy = posy + (graphHeight+10)*nbvar
        if self.scale != scale:
            self.scale = scale
        return nbvar


    def mouseEnterFunc(self, valgen, name, ymin, yrange, vnum, frames, posy, event=None):
        # show the interpolator value when mouse is over the function
        c = self.canvas
        if self.gui:
            frame = self.gui.frameFromPosition(c.canvasx(event.x))
            scale = self.gui.scale
        else:
            frame = self.frameFromPosition(c.canvasx(event.x))
            scale = self.scale
        f1, f2 = frames
        #print "mouseEnterFunc :",  params, valgen
        fraction  = (frame-f1)/float(f2-f1)
        value = valgen.getValue(fraction)
        try:
            value = value[vnum]
        except:
            value = value
        # delete previous value text
        if self._funcValId:
            c.delete('functionDot')

        # build the new value text string
        valueStr = valgen.formatValue(value)

        # create the text on the canvas
        ## x = self.positionFromFrame(frame)
        graphHeight = self.graphHeight
        ## y = posy + 10 + vnum*(graphHeight+10) + graphHeight -(
##             (value-ymin)/yrange)*graphHeight
##         y = posy + vnum*graphHeight + graphHeight -(
##              (value-ymin)/yrange)*graphHeight
        x = c.canvasx(event.x)
        y = c.canvasy(event.y)
        self._funcValId = c.create_text(
            x+5, y-20, text=valueStr,
            anchor='n', tags=('functionDot', 'actor_'+name))
        # draw a blue dot on the function
        size = 2
        c.create_oval( x-size, y-size, x+size, y+size, fill='yellow',
                       tags=('functionDot', 'actor_'+name))


    def showFuncDotVal(self, valgen, name, n, event = None):
        # show the interpolator value when mouse is over a function dot
        c = self.canvas
        tags = c.gettags(Tkinter.CURRENT)
        
        if 'firstVal' in tags:
            val = valgen.firstVal
        elif 'lastVal' in tags:
            val = valgen.lastVal
            
        if valgen.nbvar > 1:
            try:
                val = val[n]
            except:
                val = val[0]
        else:
            if hasattr(val, '__len__'):
                val = val[n]
        x = c.canvasx(event.x)
        y = c.canvasy(event.y)
        if self._funcValId:
            c.delete('functionDot')
        valueStr = valgen.formatValue(val)
        self._funcValId = c.create_text(
            x+5, y-20, text=valueStr,
            anchor='n', tags=('functionDot', 'actor_'+name))


    def selectDotVal(self, indx, actor, n, frames, event = None):
        # select the function dot for moving it up-down
        c = self.canvas
        f1, f2 = frames
        name = actor.name
        self.Button1Func = c.bind("<Button-1>")
        c.unbind("<Button-1>")
        dottag = "actorFunc_"+name+"_%d"%n+"_dot%d"%f1
        #alldots = c.find_withtag(dottag)
        #print "all dots:", alldots, f1, f2
        tags = c.gettags(Tkinter.CURRENT)
        if 'firstVal' in tags:
            firstVal = True
            kf = f1
        elif 'lastVal' in tags:
            firstVal = False
            kf = f2
        dotid = c.find_withtag(Tkinter.CURRENT)[0]
        vgindx = [indx,]
        self.movingItems = [[dotid, None, None]]
        self.updatingIntervals = [[None, None]]
        linkedkf = actor.linkedKeyFrames[actor.keyframes[kf]]
        if len(linkedkf):
            for ff in linkedkf:
                if ff != kf:
                    vgindx.append(actor.getInterval(ff)[0])
                    self.movingItems.append([c.find_withtag("actorFunc_"+name+"_%d"%n+"_dot%d"%ff)[0], None, None])
                    self.updatingIntervals.append([None, None])
        # need to move the function lines along with the dot.
        for i, indx in enumerate(vgindx):
            linetag1 = "actorFunc_"+name+"_%d_%d"% (n, indx)
            lineid1 = c.find_withtag(linetag1)
            if not firstVal and i == 0:
                self.movingItems[i][2] = lineid1[0]
                self.updatingIntervals[i][1] = indx
            else:
                if len(lineid1):
                    self.movingItems[i][1] = lineid1[0]
                    self.updatingIntervals[i][0] = indx
                if indx > 0:
                    linetag2 = "actorFunc_"+name+"_%d_%d"% (n, indx-1)
                    lineid2 = c.find_withtag(linetag2)
                    if len(lineid2):
                        self.movingItems[i][2] = lineid2[0]
                        self.updatingIntervals[i][1] = indx-1

        self.status = None
        c.tag_unbind(dottag , '<Enter>')
        #print "moving items:", self.movingItems


    def moveFuncDotVal(self, valgen, name, n, posy, valmin, valrange,event=None):
        # move the function dot up_down to change it's value
        c = self.canvas
        size = self.ovalSize
        graphHeight =  self.graphHeight
        y = c.canvasy(event.y)
        ymin = posy + (graphHeight+10)*n
        ymax = ymin + graphHeight
        if y < ymin: y = ymin
        if y > ymax: y = ymax
        for mi in self.movingItems:
            dotid = mi[0]
            coords = c.coords(dotid)[:]
            c.coords(dotid, coords[0], y-size, coords[2], y+size)
            if mi[1]:
                #modifying coords of the line to the right of selected dot:
                lid = mi[1]
                lcoords = c.coords(lid)[:]
                nc = len(lcoords)
                c.coords(lid, lcoords[0], y, lcoords[nc-2], lcoords[nc-1] )
                #c.itemconfig(lid, stipple='gray75', width=1)
            if mi[2]:
                #modifying coords of the line to the right of selected dot:
                lid = mi[2]
                lcoords = c.coords(lid)[:]
                nc = len(lcoords)
                c.coords(lid, lcoords[0], lcoords[1], lcoords[nc-2], y )
            #c.itemconfig(lid, stipple='gray75', width=1)
        
        val = (valrange*1.0) * (ymin+graphHeight-y)/graphHeight + valmin
        valueStr = valgen.formatValue(val)
        if self._funcValId:
            c.delete('functionDot')
        x = coords[0]
        self._funcValId = c.create_text(
            x+5, y-20, text=valueStr,
            anchor='n', tags=('functionDot', 'actor_'+name))
        self.status = "moving"

    
    def setFuncDotVal(self, valgen, actor, frames, n, posx, posy, valmin, valrange, event=None):
        # callback function - called on the release of Button1 (mouse on the function dot).
        # The interpolator values are modified.

        name = actor.name
        f1, f2 = frames
        c = self.canvas
        if self.Button1Func:
            self.canvas.bind("<Button-1>", self.Button1Func)
        if self.status == "moving":
            dotid = self.movingItems[0][0]
            y = c.coords(dotid)[1] + self.ovalSize
            graphHeight =  self.graphHeight
            posyn = posy + (graphHeight+10)*n
            val = (valrange[n]*1.0) * (posyn+graphHeight-y)/graphHeight + valmin[n]
            if isinstance(actor.datatype, BoolType):
                if val != 0.0 and val != 1.0:
                    size = self.ovalSize
                    if val >= 0.5:
                        val = 1.0
                        y1 = posyn - size
                        y2 = posyn + size
                    else:
                        val = 0.0
                        y1 = posyn + graphHeight - size
                        y2 = posyn + graphHeight + size
                    for item in self.movingItems:
                        dotcoords = c.coords(item[0])
                        dotcoords[1] = y1
                        dotcoords[3] = y2
                        c.coords(item[0], *dotcoords)
            tags = c.gettags(dotid)
            nbvar = valgen.nbvar
            if 'firstVal' in tags:
                firstVal = valgen.firstVal
                if hasattr(firstVal, "__len__"):
                    firstVal[n] = val
                else:
                    firstVal = val
                actor.setKeyframe( f1, firstVal)
                #if self.movingItems[0][1]:
                #    lineid = self.movingItems[1]
                    #c.itemconfig(lineid, stipple='', width=1)
                # need to set value of the interpolator for the interval before current frame

            elif 'lastVal' in tags:
                #print "in setFuncDotVal: lastval", f1, f2, self.movingItems
                lastVal = valgen.lastVal
                if hasattr(lastVal, "__len__"):
                    lastVal[n] = val
                else:
                    lastVal = val
                   
                actor.setKeyframe(f2, lastVal)
                
            # location of the time cursor:
            director = self.gui._director()
            tcframe = director.currentFrame
            
            updatingIntervals = self.updatingIntervals
            allFrames = actor.keyframes._sortedKeys
            # we need to redo the function lines for the linked intervals
            for i, item in enumerate(self.movingItems):
                for j, lineid in enumerate(item[1:]):
                    if lineid:
                        vgind = updatingIntervals[i][j]
                        ff1 = allFrames[vgind]
                        ff2 = allFrames[vgind+1]
                        if tcframe >= ff1 and tcframe <= ff2:
                            # update the actors value at the current time cursor position
                            director.setValuesAt(tcframe, actor)
                        vg = actor.valueGenerators[vgind]
                        if vg.active:
                            nbvar = min(vg.nbvar, 4)
                            lcoords = self.computeLineCoords(ff1, ff2, vg, posx, posy, valmin, valrange, nbvar, everyPoint = True)

                            c.coords(lineid , *lcoords[n])
                       
        dottag = "actorFunc_"+name+"_%d"%n+"_dot%d"%f1
        cb = CallbackFunction(self.showFuncDotVal, valgen, name ,n)
        c.tag_bind(dottag , '<Enter>', cb)
        c.tag_raise(dottag)
        self.status = None


    def computeLineCoords(self, f1, f2, valgen, posx, posy, valmin, valrange, nbvar=1, everyPoint= False):
        #print "computeLineCoords:", f1, f2, valgen, posx, posy, valmin, valrange, nbvar
        lcoords = []
        graphHeight =  self.graphHeight
        scale = self.scale
        for i in range(nbvar):
            lcoords.append([])
        if everyPoint:
            y = valgen.getValue(0.5)
            sequence = False
            if hasattr(y, "__len__"):
               sequence = True
            boolean = False
            if type(y) == types.BooleanType:
                 boolean = True
            fd = float(f2 - f1)
            for x in range(f1, f2+1):
                fraction  = (x-f1)/fd
                x = posx+x*scale
                y = valgen.getValue(fraction)
                if boolean:
                    y = float(y)
                if sequence:
                    
                    for nv in range(nbvar):
                        _posy = posy + (graphHeight+10)*nv
                        if len(y) < nv+1: _y = y[0]
                        else : _y = y[nv]
                        lcoords[nv].extend([x, _posy + graphHeight - ((_y - valmin[nv])/(valrange[nv]*1.0))*graphHeight])
                else:
                    lcoords[0].extend([x, posy + graphHeight - ((y-valmin[0])/(valrange[0]*1.0))*graphHeight])
                    
        else:
            firstVal = valgen.firstVal
            lastVal = valgen.lastVal
            for x, y in zip((f1, f2), (firstVal, lastVal)):
                for i in range(nbvar):
                    _posy = posy + (graphHeight+10)*i
                    lcoords[i].append(posx+x*scale)
                    if hasattr(y, "__len__"):
                        if len(y) == 1:
                            yi = y[0]
                        else:
                            yi = y[i]
                    else:
                        yi = y
                    lcoords[i].append( _posy + graphHeight - ((yi-valmin[i])/(valrange[i]*1.0))*graphHeight )
        return lcoords 


                
    def frameFromPosition(self, x):
        # compute a the frame closest to this x coordinate
        return round(x/self.scale)

    


