import Tkinter
from scenario.animator import Animator
from scenario.objectAnimator import ObjectAnimatorDescriptor
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
import weakref
from mglutil.util.callback import CallBackFunction

class AnimatorGUI:

    def __init__(self, animator, root=None):
        assert isinstance(animator, Animator)
        self.animator = weakref.ref(animator)

        timeCursorProcess = ObjectAnimatorDescriptor(
            self, self.handleStep, 'GUI events', valueName='frame')
        animator.addObjectAnimator(timeCursorProcess)
        animator.afterAnimation.append(self.stop_cb)
            
        if root is None:
            root = Tkinter.Toplevel()
            root.title("Animator")
        else:
            assert isinstance(root, Tkinter.Toplevel) or\
                   isinstance(root, Tkinter.Frame)

        self.root = root

        self.xoff = 80  # space to the left of the time line
        self.fps = 30   # number of frames per second
        self.timeBegin = 0  # time at the begining of the simulation
        self.timeEnd = 200  # time at the end of the simulation

        # mibutes:seconds: frames counters
        self.nbMinutes = 0
        self.nbSeconds = 0
        self.nbFrames = 0

        self.timeY = 240
        self.timeY2 = self.timeY-5
        self.tickStep = 30
        self.thickLineStep = 30
        self.thickLineL2Step = 10
        self.labelStep = self.fps
        self.scale = 10.0
        
        self.canvas = Tkinter. Canvas(root, width=600, bg='white')
        self.canvas.pack(expand=True, fill='both')
        
        self.canvas.bind("<Any-ButtonPress-1>", self.mouse1Down)

        f = self.bframe = Tkinter.Frame(root)
        
        zoomOut = Tkinter.Button(f, text='-', command=self.zoomout)
        zoomOut.pack(side='left')
        zoomIn = Tkinter.Button(f, text='+', command=self.zoomin)
        zoomIn.pack(side='left')

        # play controls
        self.stopBT = Tkinter.Button(f, text=' |<- ', command=self.begin_cb)
        self.stopBT.pack(side='left')

        b = self.playTK = Tkinter.IntVar()
        self.playBT = Tkinter.Checkbutton(f, text='Play', indicatoron=0,
                                          command=self.play_cb, variable=b)
        self.playBT.pack(side='left')

        self.stopBT = Tkinter.Button(f, text='Stop', command=self.stop_cb)
        self.stopBT.pack(side='left')

        self.durationTW = ThumbWheel(
            f, labCfg={'text':'duration:', 'side':'left'}, showLabel=1,
            width=70, height=16, min=1, type=int, value=self.timeEnd,
            callback=self.setDuration, continuous=True, oneTurn=100,
            wheelPad=2)
        self.durationTW.pack(side='right', anchor='e')

        self.durationFramesTW = ThumbWheel(
            f, labCfg={'text':'F:', 'side':'left'}, showLabel=1, width=70,
            height=16, min=0, max=self.fps-1, type=int, value=self.nbFrames,
            callback=self.setDurationFrames, continuous=True, oneTurn=self.fps,
            wheelPad=2)
        self.durationFramesTW.pack(side='right', anchor='e')

        self.durationSecondsTW = ThumbWheel(
            f, labCfg={'text':'S:', 'side':'left'}, showLabel=1, width=70,
            height=16, min=0, max=59, type=int, value=self.nbSeconds,
            callback=self.setDurationSeconds, continuous=True, oneTurn=60,
            wheelPad=2)
        self.durationSecondsTW.pack(side='right', anchor='e')

        self.durationMinutesTW = ThumbWheel(
            f, labCfg={'text':'M:', 'side':'left'}, showLabel=1, width=70,
            height=16, min=0, type=int, value=self.nbMinutes,
            callback=self.setDurationMinutes, continuous=True,
            oneTurn=10, wheelPad=2)
        self.durationMinutesTW.pack(side='right', anchor='e')

        self.setDuration(animator.getLastFrameWithChange())

        self.drawObjectAnimators()

        f.pack(side='bottom', expand=1, fill='x')

        animator.gui = weakref.ref(self)


    def mouse1Down(self, event=None):
        canvas = self.canvas
        x0 = canvas.canvasx(event.x)-5
        y0 = canvas.canvasy(event.y)-5
        items = canvas.find_overlapping(x0, y0, x0+5, y0+5)
        for item in items:
            if item==self.cursorLine or item==self.cursorLabel:
                canvas.bind("<B1-Motion>", self.moveCursor)
                canvas.bind("<ButtonRelease-1>", self.moveCursorEnd)
                break


    def positionToFrame(self, x):
        # compute a the frame closest to this x coordinate
        return round((x - self.xoff - self.timeBegin)/self.scale)

    
    def moveCursor(self,event=None):
        frame = self.positionToFrame(event.x)
        self.animator().gotoFrame( frame )


    def moveCursorEnd(self,event=None):
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")


    def play_cb(self, event=None):
        #print event, self.playTK.get()
        self.animator().run()
        

    def begin_cb(self, event=None):
        #print event, self.playTK.get()
        self.animator().gotoFrame(0)


    def stop_cb(self, event=None):
        #print event, self.playTK.get()
        self.playTK.set(0)


    def frameToMSF(self, frame):
        m = frame/(60*self.fps)
        s = (frame/self.fps)%60
        f = frame%self.fps
        return m,s,f
    

    def handleStep(self, frame=0, *args, **kw):
        self.placeTimeCursor(frame)

        # if the stop button was pressed, the play variable is 0
        if self.playTK.get()==0:
            print 'simulation stopped'
            from SimPy.Simulation import stopSimulation
            stopSimulation()


    def placeTimeCursor(self, frame=0):
        #print frame, args, kw
        deltaFrame = frame-self.animator().currentFrame
        self.canvas.move('timeCursor', self.scale*deltaFrame,0)
        self.animator().currentFrame=frame
        m,s,f = self.frameToMSF(frame)
        self.canvas.itemconfigure(self.cursorLabel,
                                  text='%02d:%02d:%02d'%(m,s,f))
        self.canvas.update_idletasks()
        #self.canvas.update()
        

    def setDuration(self, timeEnd):
        last = self.animator().getLastFrameWithChange()
        if last>timeEnd:
            timeEnd = last
            self.durationTW.set(self.timeEnd, 0, 0)

        self.animator().updateEndFrame(timeEnd, 0)
        self.timeEnd = timeEnd
        self.durationTW.set(self.timeEnd, 0)
        self.nbMinutes = timeEnd/(60*self.fps)
        self.durationMinutesTW.set(self.nbMinutes, 0)
        self.nbSeconds = (self.timeEnd/self.fps)%60
        self.durationSecondsTW.set(self.nbSeconds, 0)
        self.nbFrames = self.timeEnd%self.fps
        self.durationFramesTW.set(self.nbFrames, 0)
        self.redrawTimeAndFullRange()
        

    def setDurationMinutes(self, val):
        deltaMinutes = val-self.nbMinutes
        self.nbMinutes = val
        self.timeEnd += deltaMinutes*60*self.fps
        self.setDuration(self.timeEnd)
        self.redrawTimeAndFullRange()


    def setDurationSeconds(self, val):
        deltaSeconds = val-self.nbSeconds
        self.nbSeconds = val
        self.timeEnd += deltaSeconds*self.fps
        self.setDuration(self.timeEnd)
        self.redrawTimeAndFullRange()


    def setDurationFrames(self, val):
        deltaFrames = val-self.nbFrames
        self.nbFrames = val
        self.timeEnd += deltaFrames
        self.setDuration(self.timeEnd)
        self.redrawTimeAndFullRange()

        
    def drawTimeLine(self, drawLevel1=True, drawLevel2=True, drawLabels=True):
        # draw horizontal line
        c = self.canvas
        timeBegin = self.timeBegin
        timeEnd = self.timeEnd
        xoff = self.xoff
        scale = self.scale
        timeY = self.timeY
        fps = self.fps
        timeLine = c.create_line(xoff+timeBegin, timeY, xoff+scale*timeEnd,
                                 timeY, width=2, tags=('timeline'))

        # draw vertical lines
        for i in range(timeEnd-timeBegin+1):
            x = xoff + timeBegin + scale*i
            if (i%self.thickLineStep) == 0:
                c.create_line(x, timeY, x, 0, width=1, fill='black',
                              tags=('timeline'))
            elif (i%self.thickLineL2Step) == 0:
                if drawLevel2:
                    c.create_line(x, timeY, x, 0, width=1, fill='grey75',
                                  tags=('timeline'))
            else:
                if drawLevel1:
                    c.create_line(x, timeY, x, 0, width=1, fill='grey75',
                                  stipple='gray50', tags=('timeline'))
            if drawLabels: #and
                if i%self.labelStep == 0: # force this label
                    c.create_text(x, timeY+1, text='%02d:%02d:%02d'%(
                        i/(60*fps),(i/fps)%60,i%fps), anchor='n',
                                  tags=('timeline'), fill='magenta')
                    lastLabPos = x
                else:
                    #further than 40 for last drawn and further than 40 from
                    # next forced
                    if x-lastLabPos > 40 and \
                           (self.fps-(i%self.labelStep))*scale > 40:
                        c.create_text(x, timeY+1, text='%02d'%(i%fps,),
                                      anchor='n', tags=('timeline'), fill='blue')
                        lastLabPos = x

        c.tag_raise(timeLine)

        # time cursor
        x = xoff + timeBegin + self.animator().currentFrame*self.scale
        boxH=15
        yend = timeY+17
        self.cursorLine = c.create_line(x, 0, x, yend, x-25, yend,
             x-25, yend+boxH, x+25, yend+boxH, x+25, yend, x, yend,
             fill='green', width=2, tags=('timeCursor',))
        m,s,f = self.frameToMSF(self.animator().currentFrame)
        self.cursorLabel = c.create_text(x, yend,text='%02d:%02d:%02d'%(m,s,f),
                                  anchor='n', fill='red', tags=('timeCursor',))


    def deleteTimeLine(self):
        self.canvas.delete('timeline')
        self.canvas.delete('timeCursor')


    def redrawTimeLine(self):
        self.deleteTimeLine()
        self.drawTimeLine()


    def redraw(self):
        self.redrawTimeLine()
        self.deleteObjectAnimators()
        self.drawObjectAnimators()


    def redrawTimeAndFullRange(self):
        self.redrawTimeLine()
        self.deleteObjectAnimators(fullRangeOnly=1)
        self.drawObjectAnimators(fullRangeOnly=1)
        c = self.canvas
        for p in self.animator().objectAnimatorDescr:
            if not p.fullRange:
                c.tag_raise('objectAnimator_'+p.posArgs[2])
        c.tag_raise('timeCursor')
        

    def zoomin(self):
        self.scale*=1.1
        self.redrawTime()


    def zoomout(self):
        self.scale*=0.9
        self.redrawTime()


    def redrawTime(self):
        drawLevel1 = drawLevel2 = drawLabels = False
        scale = self.scale
        if scale>4.0:
            drawLevel1=True
        if scale*self.thickLineL2Step>4.0:
            drawLevel2=True
        if scale*self.labelStep>4.0:
            drawLabels=True

        self.deleteTimeLine()
        self.drawTimeLine(drawLevel1, drawLevel2, drawLabels)


    def deleteObjectAnimators(self, fullRangeOnly=False):
        for descr in self.animator().objectAnimatorDescr:
            if fullRangeOnly and not descr.fullRange: continue
            self.canvas.delete('objectAnimator_'+descr.posArgs[2])

        
    def drawObjectAnimators(self, fullRangeOnly=False):
        animator = self.animator()
        for i, descr in enumerate(animator.objectAnimatorDescr):
            if fullRangeOnly and not descr.fullRange: continue
            name = descr.posArgs[2]
            d = descr.namedArgs
            start = d.get('startFrame', 0)
            end = d.get('endFrame', None)
            if end is None:
                end = animator.getLastFrame()
                          
            c = self.canvas
            posy = self.timeY - 15 - 20*i
            descr.posy = posy
            scale = self.scale
            x = self.xoff + self.timeBegin 
            id = c.create_rectangle(x+start*scale, posy-5,
                                    x+end*scale, posy+5,
                                    outline='orange', fill='yellow',
                                    tags=('objectAnimator_'+name,))
            
            descr.cid = id
            if not descr.fullRange:
                c.tag_bind(id, "<Any-Enter>", self.mouseEnter)
                c.tag_bind(id, "<Any-Leave>", self.mouseLeave)
                c.tag_bind(id, "<Any-Motion>", self.configCursor)
                cb = CallBackFunction(self.mouse1DownOnActor, descr)
                c.tag_bind(id, "<ButtonPress-1>", cb)
                cb = CallBackFunction(self.mouse1UpOnActor, descr)
                c.tag_bind(id, "<ButtonRelease-1>", cb)
            
            c.create_text(x+scale*(end-start)*.5, posy-5, text=name,
                          anchor='n', tags=('objectAnimator_'+name,))


    def configCursor(self, event=None):
        c = self.canvas
        bb = c.bbox(Tkinter.CURRENT)
        if event.x-bb[0]<5:
            c.configure(cursor='left_tee')
            self.action = 'moveStart'
        elif bb[2]-event.x<5:
            c.configure(cursor='right_tee')
            self.action = 'moveEnd'
        else:
            c.configure(cursor='sb_h_double_arrow')
            self.action = 'moveActor'


    def mouseEnter(self, event=None):
        self.canvas.itemconfigure(Tkinter.CURRENT, fill='red')


    def mouseLeave(self, event=None):
        c = self.canvas
        c.itemconfigure(Tkinter.CURRENT, fill='yellow')
        c.tag_unbind(id, "<Any-Motion>")
        c.configure(cursor='')
                    

    def mouse1UpOnActor(self, descr, event=None):
        c = self.canvas
        c.tag_bind(descr.cid, "<Any-Motion>", self.configCursor)


    def mouse1DownOnActor(self, descr, event=None):
        c = self.canvas
        self.currentDescr = descr
        self.mouseDownFrame = self.positionToFrame(event.x)
        c.tag_bind(Tkinter.CURRENT, "<B1-Motion>", self.moveActor)
        c.tag_bind(Tkinter.CURRENT, "<ButtonRelease-1>", self.moveActorEnd)
        # unbind motion cb to prevent action from changing
        c.tag_unbind(descr.cid, "<Any-Motion>")


    def moveActor(self, event=None):
        # moves and resizes object animators
        frame = self.positionToFrame(event.x)
        deltaFrames = int(frame-self.mouseDownFrame)
        if deltaFrames==0: return
        descr = self.currentDescr
        d = descr.namedArgs
        startFrame = d['startFrame']
        endFrame = d['endFrame']
        if startFrame+deltaFrames < 0:
            deltaFrames -= (startFrame+deltaFrames)
        self.mouseDownFrame += deltaFrames
        name = descr.posArgs[2]

        if self.action=='moveActor':
            startFrame += deltaFrames
            endFrame += deltaFrames
            self.canvas.move('objectAnimator_'+name, self.scale*deltaFrames,0) 
            descr.configure(startFrame=startFrame, endFrame=endFrame)
        else:
            x = self.xoff + self.timeBegin
            posy = descr.posy
            scale = self.scale
            if self.action=='moveStart':
                startFrame += deltaFrames
                self.canvas.coords(descr.cid, x+startFrame*scale, posy-5,
                                   x+endFrame*scale, posy+5)
                descr.configure(startFrame=startFrame)
            elif self.action=='moveEnd':
                endFrame += deltaFrames
                self.canvas.coords(descr.cid, x+startFrame*scale, posy-5,
                                   x+endFrame*scale, posy+5)
                descr.configure(endFrame=endFrame)

        # set the value for this object animator as it might change
        # if time cursor overlap with the object animator changed
        cFrame = self.animator().currentFrame
        descr.setValue(descr.getValueAt(cFrame))


    def moveActorEnd(self,event=None):
        del self.action
        self.currentDescr = None
        self.canvas.tag_unbind(Tkinter.CURRENT, "<B1-Motion>")
        self.canvas.tag_unbind(Tkinter.CURRENT, "<ButtonRelease-1>")


if __name__=='__main__':
    from DejaVu import Viewer
    from DejaVu.Spheres import Spheres
    from scenario.interpolators import ScalarLinearInterpolator
    vi = Viewer()
    sph = Spheres('spheres', vertices =((0,0,0),(5.,0.,0.)),
                  materials=((.5,0,0),),
                  radii=5.0, quality=30,
                  inheritLineWidth=0, lineWidth=10,
                  inheritMaterial=False)
    vi.AddObject(sph)
    
    a = Animator()

    ag = AnimatorGUI(a)

    proc0 = ObjectAnimatorDescriptor(vi, vi.OneRedraw, "redraw")
    a.addObjectAnimator(proc0)

    objd = ObjectAnimatorDescriptor(
        sph, sph.Set, valueName='radii', name="sphere radius",
        startFrame=5, endFrame=40, t0value=5.0,
        interpolator=ScalarLinearInterpolator(0.6,3.5))
    a.addObjectAnimator(objd)

