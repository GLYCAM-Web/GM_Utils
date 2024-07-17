##
##  Author Michel F. Sanner May 2007
##

import Tkinter, Pmw, os, weakref

from SimPy.Simulation import now


from scenario.actor import Actor
from scenario.kfSet import KFSet

from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from mglutil.util.packageFilePath import findFilePath
from mglutil.util.callback import CallbackFunction
from scenario.interpolators import VarVectorInterpolator,CompositeInterpolator
import warnings
import tkFileDialog
from copy import copy
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser, \
     kbScrolledListBox
from Pmw import ScrolledText, ScrolledListBox, EntryField
from mglutil.gui.InputForm.Tk.gui import InputForm, InputFormDescr
from scenario.datatypes import BoolType
import tkMessageBox
from mglutil.util.misc import ensureFontCase

BehaviorList = ["noise", "speedUp3F"]

class DirectorGUIActor(Actor):
    """Actor used to update the DirectorGUI
"""
    def __init__(self, gui):
        assert isinstance(gui, DirectorGUI)
        Actor.__init__(self, "Gui Events", gui)
        self.visible = False


    def setValue(self, value):
        #print "directorguiactor value : ", value
        self.object.handleStep(value)


    def getValueAt(self, frame):
        return frame, 0, None


class TimeIntervalMarker:
    """   """
    def __init__(self, director, canvas, coords):
        self.canvas = canvas
        if len(coords) == 3:
            coords.append(coords[1]+12)
        self.coords = coords
        x1, y1, x2, y2 = coords
        #id = canvas.create_rectangle(x1, y1, x2, y2, tags = ("timeInterval"), outline = "blue", fill = "white")
        id = canvas.create_rectangle(x1, y1, x2, y2,  outline = "blue", fill = "white")
        self.id = id
        self.tagname = "timeInterval%d"%id
        canvas.itemconfigure(id, tags = (self.tagname,))
        self.menu = Tkinter.Menu(director.gui.root, title = "Mark Time Interval")
        self.menu.add_command(label= "Delete", command=self.delete_cb)
        self.menu.add_command(label="Add/Edit Text", command=self.edit_cb)
        self.resizeVar = Tkinter.BooleanVar()
        self.resizeVar.set(False)
        self.menu.add_checkbutton(label='Resize Box', var = self.resizeVar,
                                  command=self.resizeBox_cb)
        self.menu.add_command(label="Dismiss")
        canvas.tag_bind(id, '<Button-3>', self.showTimeIntMenu_cb)
        canvas.tag_bind(id, '<Button-1>', self.button1Down)
        
        self.textId = None
        self.root = None
        self._director = weakref.ref(director)
        self.createEntry()
        self.textsize = y2 -y1 - 3
        #print "text size:", self.textsize
        self.textCoords = [x1+2, y1+ (y2-y1)/2]
        self.text = None
        self.Button1Func = None

    def showTimeIntMenu_cb(self, event = None):
        self.menu.post(event.x_root, event.y_root)

    def delete_cb(self):
        self.canvas.delete(self.tagname)
        self._director().gui.deleteTimeIntervalMark(self.id)
        self.cancel_cb()

    def edit_cb(self):
        self.root.deiconify()
        self.placeEntryWidget()
        self.root.lift()
        if self.textId:
            X1, Y1, X2, Y2 = self.canvas.bbox(self.id)
            self.textCoords[0] = X1+2
            self.canvas.coords(self.textId, self.textCoords[0], self.textCoords[1])

    def createEntry(self):
        self.root = root = Tkinter.Toplevel()
        #root.withdraw()
        self.placeEntryWidget()
        fframe = Tkinter.Frame(root, bd=2, relief='groove',)
        fframe.pack(expand=1, fill='both', side = 'top')
        sframe = Tkinter.Frame(root, bd=2, relief='groove',)
        sframe.pack(expand=1, fill='both', side='bottom')
        self.entry = entry = Pmw.EntryField(fframe, labelpos='n', label_text = "Type text:",
                                            #validate = self.checkTextLength,
                                            modifiedcommand=self.pasteText_cb)
        entry.pack(fill='both', expand=1, padx=10, pady=5)
        b1 = Tkinter.Button(sframe, text="Ok", command=self.ok_cb)
        b1.pack(side = "left",fill='both', expand=1)
        b2 = Tkinter.Button(sframe, text="Cancel", command=self.cancel_cb)
        b2.pack(side = "right",fill='both', expand=1)


    def placeEntryWidget(self):
        master = self._director().gui.root
        if master.winfo_ismapped():
            m_width = master.winfo_width()
            m_height = master.winfo_height()
            m_x = master.winfo_rootx()
            m_y = master.winfo_rooty()
            x = m_x + m_width * 0.5
            y = m_y + m_height * 0.5
            self.root.geometry("+%d+%d" % (x, y))
            
    def cancel_cb(self):
        if not self.textId:
            self.canvas.delete(self.id)
        else:
            self.canvas.itemconfigure(self.textId , text = self.text)
        self.root.withdraw()

    def checkTextLength(self, text):
        result = True
        if text and self.textId:
            text = text.strip()
            canvas = self.canvas
            canvas.itemconfigure(self.textId , text = text)
            X1, Y1, X2, Y2 = canvas.bbox(self.id)
            x1, y1,x2,y2 = canvas.bbox(self.textId)
            if (X2-X1) <= (x2-x1)+ 4:
                result = False
                while (X2-X1) <= (x2-x1)+ 4:
                    text = text[:-1]
                    canvas.itemconfigure(self.textId , text = text)
                    x1, y1,x2,y2 = canvas.bbox(self.textId)
                
        return result
            
    
    def pasteText_cb(self):
        txt = self.entry.get()
        txt = txt.strip()
        if not self.textId:
            x, y = self.textCoords
            self.textId = self.canvas.create_text(x, y, text = txt,
                                                  tags = (self.tagname, "timeIntervalText"),
                                                  fill='blue', anchor = 'w',
                                                  font=(ensureFontCase('helvetica'), int(self.textsize)), )
        else:
            self.canvas.itemconfigure(self.textId , text = txt)
        X1, Y1, X2, Y2 = self.canvas.coords(self.id)
        x1, y1,x2,y2 = self.canvas.bbox(self.textId)
        if X2 < x2+2: #  strech the box if text does not fit inside it 
            self.canvas.coords(self.id , X1, Y1, x2+2, Y2)
            self.coords[2] = x2+2
            if self.resizeVar.get(): # move grab handles
                self.canvas.move('right', x2+2-X2, 0)


    def ok_cb(self):
        canvas = self.canvas
        if self.id and self.textId:
            #center text in the box:
            X1, Y1, X2, Y2 = canvas.bbox(self.id)
            x1, y1,x2,y2 = canvas.bbox(self.textId)
            diff = (X2-X1)-(x2-x1)
            canvas.coords(self.textId, X1+diff/2,  self.textCoords[1])
            self.textCoords[0] =  X1+diff/2
            self.text = canvas.itemcget(self.textId, "text")
        self.root.withdraw()

    def button1Down(self, event = None):
        event.stop = True
        canvas = self.canvas
        canvas.tag_bind(self.id, '<Button1-Motion>', self.move)
        canvas.tag_bind(self.id, '<Button1-ButtonRelease>', self.button1Up)
        self.lastx = canvas.canvasx(event.x)
        self.lasty = canvas.canvasy(event.y)
        #return "break" # supposed to stop propagation of the event - does not seem to work
        #self.Button1Func = canvas.bind("<Button-1>")
        #canvas.unbind("<Button-1>")
        self._director().gui.stopSelection = True
    

    def move(self, event=None):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        dx = x - self.lastx
        dy = y - self.lasty
        self.canvas.move(self.id, dx, dy)
        if self.textId:
            self.canvas.move(self.textId, dx, dy)
        if self.resizeVar.get():
            self.canvas.move('grabHandle_%d'%self.id, dx, dy)
        self.lastx = x
        self.lasty = y
        

    def button1Up(self, event=None):
        #if self.Button1Func:
        #    self.canvas.bind("<Button-1>", self.Button1Func)
        self._director().gui.stopSelection = False
        self.canvas.unbind('<Button1-Motion>')
        self.canvas.unbind('<Button1-ButtonRelease>')
        self.update_coords()


    def update_coords(self):
        newcoords = self.canvas.coords(self.id)[:]
        if self.coords != newcoords:
            self.coords = newcoords
            if self.textId:
                self.textCoords = self.canvas.coords(self.textId)[:]
            else:
                x1, y1, x2, y2 = newcoords
                self.textCoords = [x1+2, y1+ (y2-y1)/2]


    def resizeBox_cb(self):
        val = self.resizeVar.get()
        if val: # add 'grab handles', They will be used to resize the box
            x1,y1,x2,y2 = self.coords
            yc = y1 + (y2-y1)/2
            gh1 = self.canvas.create_rectangle(x1-2, yc-2, x1+2, yc+2,
                                               outline='black', fill='black',
                                               tags=(self.tagname, 'grabHandle_%d'%self.id, 'left') )
            
            gh2 = self.canvas.create_rectangle(x2-2, yc-2, x2+2, yc+2,
                                               outline='black', fill='black',
                                               tags=(self.tagname, 'grabHandle_%d'%self.id, 'right') )
            self.canvas.tag_bind('grabHandle_%d'%self.id, '<Button-1>', self.GrabHandleDown)
        else:
            self.canvas.delete('grabHandle_%d'%self.id)

            
    def GrabHandleDown(self, event):
        tag = 'grabHandle_%d'%self.id
        canvas = self.canvas
        #self.Button1Func = canvas.bind("<Button-1>")
        #canvas.unbind("<Button-1>")
        self._director().gui.stopSelection = True
        canvas.tag_bind(tag, '<Button1-Motion>', self.resize)
        canvas.tag_bind(tag, '<Button1-ButtonRelease>',self.GrabHandleUp)
        self.lastx = canvas.canvasx(event.x)
        self.lasty = canvas.canvasy(event.y)
        tags = canvas.gettags(Tkinter.CURRENT)
        self.movingSide = None
        if "right" in tags:
            self.movingSide = 'right'
        elif "left" in tags:
            self.movingSide = 'left'
        

    def GrabHandleUp(self, event):
        #if self.Button1Func:
        #    self.canvas.bind("<Button-1>", self.Button1Func)
        self._director().gui.stopSelection = False
        self.canvas.unbind('<Button1-Motion>')
        self.canvas.unbind('<Button1-ButtonRelease>')
        self.update_coords()
        

    def resize(self, event):
        canvas = self.canvas
        x = canvas.canvasx(event.x)
        dx = x - self.lastx
        X1, Y1, X2, Y2 = canvas.coords(self.id)
        if self.textId:
            bbox = canvas.bbox(self.textId)
            minwidth = bbox[2] - bbox[0]
        else:
            minwidth = 6
        if self.movingSide == "right":
            X2new = X2 + dx
            if X2new - X1 < minwidth:
                X2new = X1 + minwidth
                dx = X2new - X2
            X2 = X2new
        elif self.movingSide == "left":
            X1new = X1 + dx
            if  X2 - X1new < minwidth:
                X1new = X2 - minwidth
                dx = X1new - X1
            X1 = X1new
        canvas.move(self.movingSide, dx, 0)
        canvas.coords(self.id, X1, Y1, X2, Y2)
        if self.textId:
            #center text in the box:
            x1, y1,x2,y2 = canvas.bbox(self.textId)
            diff = (X2-X1)-(x2-x1)
            canvas.coords(self.textId, X1+diff/2,  self.textCoords[1])
            self.textCoords[0] =  X1+diff/2
        self.lastx = x
        
            


class DirectorGUI:
    """DirectorGUI object.
Provides a Tkinter-based Graphical User Interface (GUI) to a Director object
"""

    def __init__(self, director, root=None):
        from scenario.director import Director
        assert isinstance(director, Director)
        self._director = weakref.ref(director)

        # create a process that will treat GUI stuff at each step
        # of the simulation such as moving the time cursor and checking
        # for the stop or pause buttons
        timeCursorProcess = DirectorGUIActor(self)
        director.addActor(timeCursorProcess)
        director.afterAnimation.append(self.stop_cb)

        # create panel if needed
        if root is None:
            root = Tkinter.Toplevel()
            root.title("Director")
            self.ownsMaster = True
        else:
            assert isinstance(root, Tkinter.Toplevel) or\
                   isinstance(root, Tkinter.Frame)
            self.ownsMaster = False

        self.root = root
        self.balloons = Pmw.Balloon(root)

        ##
        ## declare some attributes
        ##
        self.xoff = 56      # space to the left of the time line
        self.fps = 30       # number of frames per second
        self.timeBegin = 0  # time at the begining of the simulation

        self.lastLine = 4000 # difines the size of the canvas???

        # minutes:seconds: frames counters
        self.nbMinutes = 0
        self.nbSeconds = 0
        self.nbFrames = 0

        self.timeOffset = 20
        self.yoff = 40 # space above time line
        self.tickStep = 30
        self.thickLineStep = 30
        self.thickLineL2Step = 10
        self.labelStep = self.fps
        self.scale = 10.0 # 10 pixels between frames???
        self.actorStep = 15 # distance between actor lines

        # marks are created on the start-end line. They mark the start and stop frames
        # that specify a part of animation that gets played.
        # When these marks are only one frame apart, we play the animation from frame 0 to
        # the last keyframe
        
        self.startFrame = 0
        self.stopFrame = 1

        ##
        ## create the GUI elements
        ##

        # create menu bar
        self.mBar = Tkinter.Frame(root, relief=Tkinter.RAISED, borderwidth=2)
        self.menuButtons = {}
        File_button = Tkinter.Menubutton(self.mBar, text='File', underline=0)
        File_button.menu = Tkinter.Menu(File_button)
        File_button['menu'] = File_button.menu
        File_button.pack(side=Tkinter.LEFT, padx="1m")

        File_button.menu.add_command(label='Open...', underline=0,
                                     accelerator='(Ctrl-o)',
                                     command=self.openScenario_cb)
        File_button.menu.add_command(label='Save...', underline=0,
                                     accelerator="(Ctrl-s)",
                                     command=self.saveScenario_cb)

        Edit_button = Tkinter.Menubutton(self.mBar, text='Edit', underline=0)
        Edit_button.menu = Tkinter.Menu(Edit_button)
        Edit_button.menu.configure(postcommand = self.postEditMenu_cb)
        Edit_button['menu'] = Edit_button.menu
        Edit_button.pack(side=Tkinter.LEFT, padx="1m")
        
        Edit_button.menu.add_command(label="Hide actor's names",
                                     command = self.showHideActorsNames_cb)
        Edit_button.menu.add_command(label="Hide up-down arrows",
                                     command = self.showHideUpDownArrows_cb)
        
        Edit_button.menu.add_separator()
        
        Edit_button.menu.add_command(label="Insert frames", state=Tkinter.DISABLED, command = self.insertFrames_cb)
        
        Edit_button.menu.add_separator()
        
        Edit_button.menu.add_command(label="Copy", accelerator="(Ctrl-c)",
                                     command=self.copyKeyFrames_cb, state=Tkinter.DISABLED)

        Edit_button.menu.add_command(label="Paste", command=self.pasteKeyFrames_cb ,
                                     state=Tkinter.DISABLED)

        Edit_button.menu.add_command(label="Linked Paste", state=Tkinter.DISABLED, command = self.pasteLinkKeyFrames_cb)

        Edit_button.menu.add_command(label="Flip Selection", state=Tkinter.DISABLED, command = self.flipSelection_cb)
        Edit_button.menu.add_separator()

        Edit_button.menu.cascadeMenu = Tkinter.Menu(Edit_button.menu , tearoff=1)
        Edit_button.menu.add_cascade(label="Play Mode... ", menu=Edit_button.menu.cascadeMenu)
        self.playModeTK = Tkinter.StringVar()
        self.playModeTK.set("single")
        Edit_button.menu.cascadeMenu.add_radiobutton(label= "play once in one direction",
                                       variable=self.playModeTK, command=self.setPlayMode_cb,
                                       value='single')
        
        Edit_button.menu.cascadeMenu.add_radiobutton(label= "play continuously in one direction",
                                       variable=self.playModeTK, command=self.setPlayMode_cb,
                                       value='continuous')

        Edit_button.menu.add_separator()
        
        Edit_button.menu.add_command(label="Delete", state=Tkinter.DISABLED, command = self.deleteKeyFrames_cb)
        self.menuButtons['Edit'] = Edit_button
        
        Help_button = Tkinter.Menubutton(self.mBar, text='Help', underline=0)
        Help_button.menu = Tkinter.Menu(Help_button)
        Help_button['menu'] = Help_button.menu
        Help_button.pack(side=Tkinter.LEFT, padx="1m")
        self.menuButtons['Help'] = Help_button
        self.createHelpText()
        Help_button.menu.add_command(label="How to ...",
                                     command=self.displayHelpText_cb)
        self.scrollregion=[0 , 0, 4000, 4000]
        self.scrolledCanvas = Pmw.ScrolledCanvas(
            root, canvas_width=600, canvas_bg='white',
            vscrollmode='static', hscrollmode='static',
            horizscrollbar_width=10, vertscrollbar_width=10)

        self.canvas = self.scrolledCanvas.component('canvas')
        self.canvas.configure(scrollregion=tuple(self.scrollregion))
        #self.canvas.bind('<Enter>', self.canvasEnter_cb)
        #self.canvas.bind('<Leave>', self.canvasLeave_cb)

        # bind keyboard events
        self.canvas.focus_set()
        self.canvas.bind('<Control-o>', self.openScenario_cb)
        self.canvas.bind('<Control-s>', self.saveScenario_cb)
        self.canvas.bind('<Control-c>', self.copyKeyFrames_cb)
        self.canvas.bind('<Control-v>', self.pasteKeyFrames_cb)
        
        f = self.bframe = Tkinter.Frame(root)
        
        self.scaleTimeTW = ThumbWheel(
            f, showLabel=0, width=70, height=16, type=float, value=0,
            callback=self.setTimeScaleFactor_cb, continuous=True, oneTurn=10,
            wheelPad=2, reportDelta=True)
        self.scaleTimeTW.pack(side='right', anchor='e')
        self.balloons.bind(self.scaleTimeTW, 'Zoom time line in and out')
                           
        #zoomOut = Tkinter.Button(f, text='-', command=self.zoomout)
        #zoomOut.pack(side='left')
        #zoomIn = Tkinter.Button(f, text='+', command=self.zoomin)
        #zoomIn.pack(side='left')
        
        # get icons
        icondir = findFilePath('icons', 'mglutil.gui.BasicWidgets.Tk')
        PI = Tkinter.PhotoImage
        self.playIcon = PI(file=os.path.join(icondir, "play_fwd.gif"))
        self.gotoStartIcon = PI(file=os.path.join(icondir, "go_to_start.gif"))
        self.gotoEndIcon = PI(file=os.path.join(icondir, "go_to_end.gif"))
        self.playReverseIcon = PI(file=os.path.join(icondir, "play_rev.gif"))
        self.stopIcon = PI(file=os.path.join(icondir, "stop3.gif"))
        self.pauseIcon = PI(file=os.path.join(icondir, "stop2.gif"))
        self.recordIcon = PI(file=os.path.join(icondir, "record.gif"))
        self.record1Icon = PI(file=os.path.join(icondir, "record1.gif"))
        self.cameraIcon = PI(file=os.path.join(icondir, "camera.gif"))
        self.arrowupIcon = PI(file=os.path.join(icondir,"arrowup.gif"))
        self.arrowdownIcon =  PI(file=os.path.join(icondir,"arrowdown.gif"))

        # play controls

        w = Tkinter.Frame(f, borderwidth=2, relief='ridge')
       
        
        icon = self.gotoStartIcon
        self.goStartBT = Tkinter.Button(
            w, image=icon, width=icon.width(), height=icon.height(),
            command=self.begin_cb)
        self.goStartBT.pack(side='left')
        self.balloons.bind(self.goStartBT, 'Move read head to the begining of animation')
        
        
        icon = self.playReverseIcon
        self.reversePlayTK = Tkinter.IntVar()
        self.reversePlayBT = Tkinter.Checkbutton(
            w,  indicatoron=0, image=icon, width=icon.width(),
            height=icon.height(), command=self.reversePlay_cb, variable=self.reversePlayTK)
        self.reversePlayBT.pack(side='left')
        self.balloons.bind(self.reversePlayBT, 'Play Reverse animation')

        icon = self.stopIcon
        self.stopBT = Tkinter.Button(
            w, image=icon, width=icon.width(), height=icon.height(),
            command=self.stop_cb)
        self.stopBT.pack(side='left')
        self.balloons.bind(self.stopBT, 'Stop play back')
        w.pack(side='left', padx=5)

        icon = self.playIcon
        self.playTK = Tkinter.IntVar()
        self.playBT = Tkinter.Checkbutton(
            w,  indicatoron=0, image=icon, width=icon.width(),
            height=icon.height(), command=self.play_cb, variable=self.playTK)
        self.playBT.pack(side='left')
        self.balloons.bind(self.playBT, 'Play animation')

        icon = self.gotoEndIcon
        self.goEndBT = Tkinter.Button(
            w, image=icon, width=icon.width(), height=icon.height(),
            command=self.gotoend_cb)
        self.goEndBT.pack(side='left')
        self.balloons.bind(self.goEndBT, 'Move read head to the end of animation')
        
        rframe = self.rframe = Tkinter.Frame(f, borderwidth=2, relief='ridge')
        icon = self.recordIcon
        self.recordKFBT = Tkinter.Button(rframe,
            image=icon, width=icon.width(), height=icon.height(),
            command=self.recordKeyframe_cb)
        self.recordKFBT.pack(side='left')
        self.balloons.bind(self.recordKFBT, 'Record a keyframe for all actors\nselected for recording')

        ## icon = self.stopIcon
##         self.stopKFBT = Tkinter.Button(
##             w, image=icon, width=icon.width(), height=icon.height(),
##             command=self.stopRecordKeyframe_cb)
##         self.stopKFBT.pack(side='left')
##         self.balloons.bind(self.stopKFBT, 'Stop recording keyframes')
        self.autotrackVar = Tkinter.IntVar()
        self.autotrackBT = Tkinter.Checkbutton(
            rframe,  indicatoron=0, text="AutoTrack", command=self.autotrack_cb, variable=self.autotrackVar)
        self.autotrackBT.pack(side='left')
        self.balloons.bind(self.autotrackBT, 'Set auto tracking on/off')
        rframe.pack(side='left', padx=5)
        
        w = Tkinter.Frame(f, borderwidth=2, relief='ridge')
        self.durationTW = ThumbWheel(
            w, labCfg={'text':'TF:', 'side':'left'}, showLabel=1,
            width=70, height=16, min=1, type=int,
            value=self._director().endFrame, wheelPad=2,
            callback=self.setDuration, continuous=True, oneTurn=100)
        self.durationTW.pack(side='right', anchor='e')
        self.balloons.bind(self.durationTW, 'Total number of frames')

        self.durationFramesTW = ThumbWheel(
            w, labCfg={'text':'F:', 'side':'left'}, showLabel=1, width=50,
            height=16, min=0, max=self.fps-1, type=int, value=self.nbFrames,
            callback=self.setDurationFrames, continuous=True, oneTurn=self.fps,
            wheelPad=2)
        self.durationFramesTW.pack(side='right', anchor='e')
        self.balloons.bind(self.durationFramesTW, 'Number of Frames')

        self.durationSecondsTW = ThumbWheel(
            w, labCfg={'text':'S:', 'side':'left'}, showLabel=1, width=50,
            height=16, min=0, max=59, type=int, value=self.nbSeconds,
            callback=self.setDurationSeconds, continuous=True, oneTurn=60,
            wheelPad=2)
        self.durationSecondsTW.pack(side='right', anchor='e')
        self.balloons.bind(self.durationSecondsTW, 'Number of seconds')

        self.durationMinutesTW = ThumbWheel(
            w, labCfg={'text':'M:', 'side':'left'}, showLabel=1, width=50,
            height=16, min=0, type=int, value=self.nbMinutes,
            callback=self.setDurationMinutes, continuous=True,
            oneTurn=10, wheelPad=2)
        self.durationMinutesTW.pack(side='right', anchor='e')
        self.balloons.bind(self.durationMinutesTW, 'Number of minutes')
        w.pack(side='left', padx=5)

        self.timeIntervalLabels = {}
        #self.setDuration(director.getLastFrameWithChange())
        self.setDuration(director.getLastFrame())
        
        from interpolatorGUI import InterpGUI
        self.interpgui = InterpGUI(self)

        self.allrecording = True
        self.allplaying = True
        self.namesOn = True
        self.upDownArrowsOn = True
        self.drawActors()

        self.mBar.pack(side='top',fill=Tkinter.X)
        self.scrolledCanvas.pack(expand=True, fill='both')
        f.pack(side='bottom', expand=0, fill='x')

        #director.gui = self

        self.actorMenu = Tkinter.Menu(root, title = "Actor Options")
        self.actorMenuItems = ["Record Keyframe", "Delete Actor",
                          "Stop Segment Interpolation",
                          "Add behavior", "Remove behavior",
                          "Dismiss"]
        self.actorMenuDict = {}
        for item in self.actorMenuItems:
            self.actorMenu.add_command(label= item)
        self.actorMenu.entryconfigure("Remove behavior", state=Tkinter.DISABLED)
        # this dictionry will be used to customize the items in the actor menu (see showActorMenu_cb()):
        self.actorMenuDict = {"Move keyframe" :[],
                              "Segment Interpolation" : "Stop Segment Interpolation"}
        
        self.kfMenu = Tkinter.Menu(root, title = "Keyframe Options")
        self.kfMenu.add_command(label = "Delete Keyframe")
        self.kfMenu.add_command(label = "Select Set", state=Tkinter.DISABLED)
        self.kfMenu.add_command(label = "Unlink Set", state=Tkinter.DISABLED)

        self.kfMenu.add_command(label='Dismiss')
        self.autotracking = False
        #self.canvas.bind("<ButtonPress-2>", self.startKFSelection)
        self.canvas.bind("<ButtonPress-1>", self.startKFSelection)
        self.canvas.bind("<ButtonPress-2>", self.startTimeIntSelection)
        self.selectedFrames = {}
        self.selectedIntervals = {}        
        self.pasteBuffer = []
        self.stopSelection = False

        self.kfSets = {}
        self.animationScript = None

        
        
    ##
    ## Callback functions
    ##
    def openScenario_cb(self, file = None, event=None):
        if file is None:
            file = tkFileDialog.askopenfilename(parent = self.root,
                              initialdir = '.', title='Load Scenario',
                              filetypes=[('scenario', '*_scenario.py'), ('all', '*')] )
        if file:
            self.loadAnimation(file)
            self.pasteBuffer = []
            self.selectedFrames = {}
            if len(self.canvas.find_withtag("selection")):
                self.canvas.delete("selection")


    def saveScenario_cb(self, event=None):

        file = tkFileDialog.asksaveasfilename(parent = self.root,
                initialdir = '.', filetypes=[('scenario', '*_scenario.py'),
                                             ('all', '*')],
                initialfile = "my_scenario.py", title='Save Scenario')
        if file:
            self.saveAnimation(self._director(), file)


    def saveAnimation(self, director, filename):
            # saves current scenario in  a script
            #print "saving animation: director:", director, "file:", filename
            lines = []
            lines.append("import tkMessageBox\n")
            lines.append("director = self\n")
            lines.append("curx = director.gui.xoff+director.gui.timeBegin\n")
            lines.append("director.gui.kfSets = {}\n")
            actorsdict = {}
            dataFileParser = False # for FileActors
            for i, actor in enumerate(director.actors[1:]):
                indent = ""
                name = actor.name
                actorsdict[name] = i
                scenarioname = actor.scenarioname
                sci = director.scenarios[scenarioname]
                lines.append(indent + "sci = director.scenarios['%s']\n"%scenarioname)
                if hasattr(actor, "filename"): # FileActor
                    if not dataFileParser:
                        lines.append(indent + "dataFileParsers = {}\n")
                        lines.append(indent + "from scenario.actor import adatFileParser \n")
                        dataFileParser = True
                lines.append(indent + "#creating actor %d - %s\n" %(i, name))
                lines.append(indent+"actor%d = None\n"% i)
                actorlines, indent = sci.getActorScript(actor, indent, i)
                lines.extend(actorlines)
                if actor.visible:
                    sortedFrames = actor.keyframes._sortedKeys
                    if hasattr(actor, "filename"): # FileActor
                        datafile = actor.filename
                        lines.append(indent + "# create actor from file %s \n" % datafile)
                        lines.append(indent + "datafile = '%s'\n" % datafile)
                        lines.append(indent + "if dataFileParsers.has_key(datafile):\n")
                        newindent = indent + "    "
                        lines.append(newindent + "fparser = dataFileParsers[datafile]\n")
                        lines.append(indent + "else:\n")
                        lines.append(newindent + "fparser = adatFileParser(datafile)\n")
                        lines.append(newindent +"dataFileParsers[datafile] = fparser\n")
                        fstr = ""
                        for f in actor.datafields:
                            fstr = fstr+"'%s',"%f
                        lines.append(indent + "data = fparser.getFieldsData([%s])\n" % fstr )
                        propname = actor.name.split(".")[-2]
                        start,end = [0, -1]
                        if len(sortedFrames) == 2:
                            start, end  = sortedFrames
                        lines.append(indent + "actor%d = director.createActorFromData(obj%d, '%s', sci, '%s', [%s], data, start = %d, end = %d)\n" %(i, i, propname, datafile, fstr,start, end))
                    else:
                        lines.append(indent+"if actor%d: \n"%i)
                        indent = indent + "    "
                        kf0 = sortedFrames[0]
                        if kf0 != 0:
                            lines.append(indent + "actor%d.keyframes.clear()\n" % i)
                        lines.append(indent + "actor%d.setKeyframe(%d, valueIndex=%d)\n" % (i, kf0, actor.keyframes[kf0]))
                        for j, kf in enumerate(sortedFrames[1:]):
                            valind = actor.keyframes[kf]
                            vgIndex = None
                            if len(actor.linkedVG[j]):
                                # find out if interpolation interval before kf is linked with
                                #some other interval
                                lvg = min(actor.linkedVG[j])
                                if lvg < j:
                                    vgIndex = lvg
                            if vgIndex is not None:
                                lines.append(indent + "actor%d.setKeyframe(%d, valueIndex=%d, vgIndex=%d)\n"%(i, kf, valind,  vgIndex))
                            else:
                                lines.append(indent + "actor%d.setKeyframe(%d, valueIndex=%d)\n"%(i, kf, valind))
                        lines.append(indent+"actor%d.linkedKeyFrames = %s\n" % (i, actor.linkedKeyFrames))
                        lines.append(indent+"actor%d.kfSetId = %s\n" % (i, actor.kfSetId))
                        if actor.playing == False:
                            lines.append(indent + "actor%d.playing = False\n"%i)
                        if actor.recording == False:
                            lines.append(indent + "actor%d.recording = False\n"%i)
                    #lines.append(indent + "director.gui.drawKeyFrames(actor%d, curx, actor%d._posy)\n"%(i,i))
                    for nvg, vg in enumerate(actor.valueGenerators):
                        if len(vg.behaviors) > 1:
                            addBehavior = True
                            if len(actor.linkedVG[nvg]):
                                if nvg > min(actor.linkedVG[nvg]):
                                    addBehavior = False
                            if addBehavior:
                                for behavior in vg.behaviors[1:]:
                                    behaviorClass = behavior.__class__.__name__
                                    lines.append(indent + "from scenario.interpolators import %s\n" % behaviorClass)
                                    lines.append(indent + "actor%d.valueGenerators[%d].addBehavior(behaviorClass=%s)\n" % (i, nvg, behaviorClass) )
            lines.append("director.gui.selectedFrames = {}\n")
            lines.append("director.gui.pasteBuffer = []\n")
            lines.append("director.gui.redraw()\n")
            if len(self.kfSets):
                lines.append("from scenario.kfSet import KFSet\n")
                for id, kfset in self.kfSets.items():
                    ss = "["
                    for item in kfset.setframes:
                        actor = item[0]
                        ff = item[1:]
                        aind = actorsdict[actor.name]
                        ss = ss + "[actor%d, %s]," % (aind, ff)
                    ss = ss + "]"
                    lines.append("director.gui.kfSets[%d] =  KFSet(%s, %d, director)\n" % (id, ss, id))
            f = open(filename, 'w')
            f.writelines(lines)
            f.close()


    def loadAnimation(self, file):
        # runs a script that was created by "saveAnimation()".
        director = self._director()
        glob = {'self': director}
##         try:
##             execfile( file, glob)
##         except:
##             print "ERROR: could not restore animation from file %s" %file
        for actor in director.actors[:]:
            if actor.visible:
                director.deleteActor(actor)
        director.autotrackDict = {}
        self.autotrackVar.set(0)
        self.autotracking = False
        execfile( file, glob)
        self.animationScript = file


    def begin_cb(self, event=None):
        #print event, self.playTK.get()
        director = self._director() 
        director.gotoFrame(0, set = False)
        redraw = director.redrawActor
        for actor in director.actors:
            if actor.visible and actor.playing:
                value, interval, valGen = actor.getValueAt(0)
                if value is not None:
                    if redraw:
                        director.needsRedraw = True
                    actor.setValue(value)
        if redraw:
            redraw.setValue()
        

    def play_cb(self, event=None):
        #print "play_cb, ", "play=", self.playTK.get(), "reverse=", self.reversePlayTK.get()
        if self.playTK.get() == 1:
            if self.reversePlayTK.get() == 1:
                self.stop_cb()
                return
            if self._director().redrawActor:
                vi = self._director().redrawActor.object
                vi.stopAutoRedraw()
            if self.playModeTK.get() == "continuous":
                while self.playTK.get() == 1:
                    self._director().run()
            else:
               self._director().run()


    def reversePlay_cb(self, event=None):
        #print "reversePlay_cb", "reverse=", self.reversePlayTK.get(), "play=", self.playTK.get()
        if self.reversePlayTK.get() == 1:
            if self.playTK.get() == 1:
                self.stop_cb()
                return
            if self._director().redrawActor:
                vi = self._director().redrawActor.object
                vi.stopAutoRedraw()
            if self.playModeTK.get() == "continuous":
                while self.reversePlayTK.get() == 1:
                    self._director().run(False)
            else:
                self._director().run(False)

    

    def stop_cb(self, event=None):
        #print "in stop_cb", "play=", self.playTK.get(), "reverse=", self.reversePlayTK.get()
        self.playTK.set(0)
        self.reversePlayTK.set(0)
        director = self._director()
        currentFrame = int(now())
        if not director.moveForward:
            end = self._director().getLastFrameWithChange()
            currentFrame = end - currentFrame 
        self._director().currentFrame = currentFrame


    def setPlayMode_cb(self, event=None):
        # callback of Edit -> Play Mode -> ...   menu button
        # sets playback mode:  pressing on "play" or "reverse play" in 'continuous' mode
        # will play the animation continuously in selected direction.
        
        mode = self.playModeTK.get()
        #print "setPlayMode_cb:", mode
        director = self._director()
        if mode == "continuous":
            if self.stop_cb in director.afterAnimation:
                director.afterAnimation.remove(self.stop_cb)
        elif mode == "single":
            if not self.stop_cb in director.afterAnimation:
                director.afterAnimation.append(self.stop_cb)
        #print "setPlayMode_cb:", director.afterAnimation


    def gotoend_cb(self, event=None):
        director = self._director() 
        #director.gotoFrame(director.getLastFrame())
        endframe = director.getLastFrameWithChange()
        director.gotoFrame(endframe, set = False)
        redraw = director.redrawActor
        for actor in director.actors:
            if actor.visible and actor.playing:
                value, interval, valGen = actor.getValueAt(endframe)
                if value is not None:
                    if redraw:
                        director.needsRedraw = True
                    actor.setValue(value)
        if redraw:
            redraw.setValue()


    def recordKeyframe_cb(self, recordactor = None, event=None):
        # Record a keyframe at current timecursor position.
        # If in autotracking mode - record keyframes only for those actors whose
        # recording values have changed (ie current value is different from the last
        # recorded value).
        # In 'regular' mode - record keyframe for all visible actors.
        # If 'recordactor' is specified - record a keyframe for this actor only
        # (even if actor.recording is False).
        
        director = self._director()
        frame = director.currentFrame
        actors = []
        if not recordactor:
            if self.autotracking:
                director = self._director()
                autotrackactors = director.autotrackDict.keys()
                newactors = {}
                for sname in director.scenarios.keys():
                    scenario = director.scenarios[sname]
                    newactors.update(scenario.getNewActors())
            for actor in director.actors:
                if actor.recording:
                    actors.append(actor)
        else:
            actors.append(recordactor)
        curx = self.xoff+self.timeBegin
        for actor in actors:
            #if actor.keyframes.get(frame) is not None:
            #    continue
            posy = actor._posy
            lastKF = actor.getLastFrame()
            value = None
            name = actor.name
            if actor.hasGetFunction:
                value = actor.getValueFromObject()
                if recordactor is None and self.autotracking:
                    if director.autotrackDict.has_key(name):
                        oldval  = actor.getValueAt(frame)[0]
                        ind = autotrackactors.index(name)
                        autotrackactors.pop(ind)
                        if actor.compareValues(oldval, value): #oldval == value
                            continue

                if actor.displayFunction:
                    self.deleteActor(actor)
                    actor.setKeyframe(frame, value)
                    self.drawActor(actor, posy)
                else:
                    self.deleteActorKeyFrames(actor)
                    actor.setKeyframe(frame, value)
                    self.drawKeyFrames(actor, curx, posy)
        
        if recordactor is None  and self.autotracking:           
            for actorname in autotrackactors: # this is a list of all available actors that have not been added to the director
                actor = director.autotrackDict[actorname]
                if not actor.recording:
                    continue
                if actor.hasGetFunction:
                    value = actor.getValueFromObject()
                    oldval  = actor.getValueAt(frame)[0]
                    if not actor.compareValues(oldval, value):
                        # oldval != value - add actor to the director
                        # set the first keyframe value to the oldval
                        actor.keyframeValues[0] = oldval
                        # add new keyframe with value
                        actor.setKeyframe(frame, value)
                        director.addActor(actor)
                        if hasattr(actor, 'scenario'):
                            if hasattr(actor.scenario, 'onAddActorToDirector'):
                                actor.scenario.onAddActorToDirector(actor)
        
            for actorname in newactors.keys():
                actor = newactors[actorname]
            director.autotrackDict.update(newactors)
                
                    
    def autotrack_cb(self):
        if self.autotrackVar.get():
            self.autotracking = True
            director = self._director()
            autotrackDict = director.autotrackDict
            for actor in director.actors:
                if actor.visible:
                    actorname = actor.name
                    if not autotrackDict.has_key(actorname):
                        autotrackDict[actorname] = actor

            for sname in director.scenarios.keys():
                scenario = director.scenarios[sname]
                newactors = scenario.getNewActors()
                if len(newactors):
                    for actorname in newactors.keys():
                        actor = newactors[actorname]
                    autotrackDict.update(newactors)
        else:
            self.autotracking = False


    def createRecordMovieButton(self):
        f = self.rframe
        self.recordMovieVar = Tkinter.IntVar()
        icon = self.cameraIcon
        self.recordMovieBT = Tkinter.Checkbutton(
            f,  indicatoron=0, image=icon, width=icon.width(),
            height=icon.height(), command=self.recordMovie_cb,
            variable=self.recordMovieVar, background="white")
        self.recordMovieBT.pack(side='left')
        self.balloons.bind(self.recordMovieBT, 'Start/Stop movie recording')


    def recordMovie_cb(self):
        val = self.recordMovieVar.get()
        redrawActor = self._director().redrawActor
        if redrawActor:
            if val:
                
                file = tkFileDialog.asksaveasfilename(parent = self.root,
                    initialdir = '.', filetypes=[('mpg', '*.mpg'),
                                                 ('all', '*')],
                    initialfile = "out.mpg", title='Save movie in file:')
                if file:
                    print "recording movie"
                    redrawActor.startRecording(file)
                else:
                    self.recordMovieVar.set(0)

            else:
                print "stopped recording movie"
                redrawActor.stopRecording()
    

    def stopRecordKeyframe_cb(self):
        pass
    

##     def canvasEnter_cb(self, event):
##         self.canvas.bind('<Motion>', self.canvasMotion_cb)


##     def canvasLeave_cb(self, event):
##         self.canvas.unbind('<Motion>')
##         self.balloons.configure(xoffset=0)


##     def canvasMotion_cb(self, event):
##         self.balloons.configure(xoffset=self.canvas.canvasx(event.x))


    def setBalloon_cb (self, event = None):
        # sets xoffset of the balloon widget (is called when mouse pointer enters/leaves an actorline) 
        tt = event.type
        if tt == '7' :# '<Enter>'
            self.balloons.configure(xoffset=self.canvas.canvasx(event.x))
        elif tt == '8': # '<Leave>'
            self.balloons.configure(xoffset=20)
            
        
    def toggleDrawFunction_cb(self, actor, event=None):
        # show/hide function of the selected actor (<ButtonPress-2> on the actor line.)

        self.deleteActors()
        actor.displayFunction = not actor.displayFunction
        self.drawActors()

        
    def setTimeScaleFactor_cb(self, value, event=None):
        self.scale = self.scale * (1.1)**value
        self.redraw()

        
    def mouse1DownTimeCursor(self, event=None):
        # register callbacks for moving time cursor
        canvas = self.canvas
        if self._director().redrawActor:
            vi = self._director().redrawActor.object
            vi.stopAutoRedraw()
        canvas.tag_bind('timeCursor', '<B1-Motion>', self.moveCursor)
        canvas.tag_bind('timeCursor', '<ButtonRelease-1>', self.moveCursorEnd)
        # this will prevent drawing a selection box around keyframes
        #canvas.unbind('<ButtonPress-1>')
        self.stopSelection = True

    
    def mouse3DownTimeCursor(self, event=None):
        # register callbacks for moving time cursor
        canvas = self.canvas
        canvas.tag_bind('timeCursor', '<B3-Motion>', self.moveCursorNoSet)
        canvas.tag_bind('timeCursor', '<ButtonRelease-3>', self.mouse3UpTimeCursor)
        for actor in self._director().actors:
            if actor.playing:
                actor.playing = False
                self.drawActorPlayingButton(actor)


    def mouse3UpTimeCursor(self, event=None):
        for actor in self._director().actors:
            if not actor.playing:
                actor.playing = True
                self.drawActorPlayingButton(actor)
        
        
                
    def moveCursor(self, event=None):
        frame = self.frameFromPosition(self.canvas.canvasx(event.x))
        self._director().gotoFrame( int(frame))


    def moveCursorNoSet(self, event=None):
        frame = self.frameFromPosition(self.canvas.canvasx(event.x))
        self._director().gotoFrame( int(frame), set=False)


    def moveCursorEnd(self, event=None):
        canvas = self.canvas
        canvas.tag_unbind('timeCursor', '<B1-Motion>')
        canvas.tag_unbind('timeCursor', '<ButtonRelease-1>')
        if self._director().redrawActor:
            vi = self._director().redrawActor.object
            vi.startAutoRedraw()
        # resume bindings for making keyframe selection
        #canvas.bind("<ButtonPress-1>", self.startKFSelection)
        self.stopSelection = False


    def mouse1DownStartMark(self, event=None):
        # <Button-1> callback on the Start mark (of start-end play line) 
        canvas = self.canvas
        canvas.tag_bind('startMark', '<B1-Motion>',
                        CallbackFunction(self.moveStartStopMarks, 'startMark', 0))
        canvas.tag_bind('startMark', '<ButtonRelease-1>',
                        CallbackFunction(self.mouse1UpStartStopMarks, 'startMark'))
        # this will prevent drawing a selection box around keyframes
        self.stopSelection = True


    def mouse1DownStopMark(self, event=None):
        # <Button-1> callback on the Stop mark (of start-end play line) 
        canvas = self.canvas
        canvas.tag_bind('stopMark', '<B1-Motion>',
                        CallbackFunction(self.moveStartStopMarks, 'stopMark', 1))
        canvas.tag_bind('stopMark', '<ButtonRelease-1>',
                        CallbackFunction(self.mouse1UpStartStopMarks, 'stopMark'))
        # this will prevent drawing a selection box around keyframes
        self.stopSelection = True


    def moveStartStopMarks(self, tag, frame = 0, event = None):
        # moves the Start/Stop marks that specify the part of animation that gets played
        
        # print "moveStartStopMarks:", tag
        if event is not None:
            frame = int(self.frameFromPosition(self.canvas.canvasx(event.x)))
        y = self.yoff
        canvas = self.canvas
        fill2 = "green3"
        fill1 = "red"
        if tag == 'startMark':
            if frame != self.startFrame:
                if frame >= self.stopFrame:
                    frame = self.stopFrame-1
                elif frame < 0:
                    frame = 0
                dist = (frame - self.startFrame)*self.scale
                x = self.positionFromFrame(frame)
                canvas.coords
                #canvas.coords(tag, x, y, x-3, y-6, x-3, y-13, x+3, y-13, x+3, y-6, x, y)
                canvas.move(tag, dist, 0)
                self.startFrame = frame
                if self.startFrame == 0 and self.stopFrame == 1:
                    fill1 = "green3"
                    canvas.itemconfigure('start_stopLine3', fill=fill1)
                canvas.coords('start_stopLine1', self.xoff, y, x, y)
                cs = canvas.coords('start_stopLine2')
                cs[0] = x
                cs[1] = y
                canvas.coords('start_stopLine2', *cs)
                canvas.itemconfigure('start_stopLine1', fill = fill1)
                canvas.itemconfigure('start_stopLine2', fill = fill2)
                
        elif tag == 'stopMark':
            if frame != self.stopFrame:
                if frame <=self.startFrame:
                    frame = self.startFrame+1
                dist = (frame - self.stopFrame)*self.scale
                canvas.move(tag, dist, 0)
                x = self.positionFromFrame(frame)
                #canvas.coords(tag, x, y, x-3, y-6, x-3, y-13, x+3, y-13, x+3, y-6, x, y)
                self.stopFrame = frame
                if self.startFrame == 0 and self.stopFrame == 1:
                    fill1 = "green3"
                    canvas.itemconfigure('start_stopLine1', fill=fill1)
                cs1 = canvas.coords('start_stopLine2')
                cs1[2] = x 
                canvas.coords('start_stopLine2', *cs1)
                cs2 = canvas.coords('start_stopLine3')
                cs2[0] = x
                canvas.coords('start_stopLine3', *cs2)
                canvas.itemconfigure('start_stopLine2', fill = fill2)
                canvas.itemconfigure('start_stopLine3', fill = fill1)
        if frame > self._director().endFrame: #add time lines
            self.setDuration(frame + 10)


    def mouse1UpStartStopMarks(self, tag, event=None):
        #print "startFrame:", self.startFrame , "stopFrame:", self.stopFrame
        self.stopSelection = False
        self.canvas.tag_unbind(tag, '<B1-Motion>')
        self.canvas.tag_unbind(tag, '<ButtonRelease-1>')


    def showStartStopMarkEntry(self, tag, event=None):
        # <Button-3> callback on the Start/Stop marks that specify the part of animation
        # that gets played. 
        idf = InputFormDescr(title='Move %s'% tag)
        if tag == "startMark":
            val = self.startFrame
            validator = {'validator':'integer', 'min': 0, 'max':self.stopFrame -1, 'minstrict':0 }
            
        elif tag == "stopMark":
            val = self.stopFrame
            validator = {'validator':'integer', 'min': self.startFrame+1,'minstrict':0}
            
        else:
            return
        idf.append({'name': tag,
                    'widgetType': Pmw.EntryField,
                    'required':1,
                    'wcfg':{'labelpos':'w',
                            'entry_width': 8,
                            'label_text': "move to frame:",
                            'value': str(val),
                            'validate': validator},
                    
                    'gridcfg':{'sticky':'we'}
            })
        form=InputForm(self.root, None, idf, blocking = 1)
        res = form.go()
        frame = res.get(tag)
        if frame is not None:
            frame = int(frame)
            if frame != val:
                self.moveStartStopMarks(tag, frame)

        

    def handleStep(self, frame):
        #print 'handle step', now(), frame 
        #self.placeTimeCursor( int(now()) )
        self.placeTimeCursor(int(frame))
        # if the stop button was pressed, the play variable is 0
        if self.playTK.get() == 0 and self.reversePlayTK.get() == 0:
            from SimPy.Simulation import stopSimulation, _stop
            if not _stop:
                print 'simulation stopped'
                stopSimulation()
        


    ## time dials management
    def setDuration(self, timeEnd):
        last = self._director().getLastFrameWithChange()
        if last>timeEnd:
            timeEnd = last
            self.durationTW.set(timeEnd, 0, 0)
        self._director().updateEndFrame(timeEnd, 0)
        timeEnd = self._director().getLastFrame()
        self.durationTW.set(timeEnd, 0)
        self.nbMinutes = timeEnd/(60*self.fps)
        self.durationMinutesTW.set(self.nbMinutes, 0)
        self.nbSeconds = (timeEnd/self.fps)%60
        self.durationSecondsTW.set(self.nbSeconds, 0)
        self.nbFrames = timeEnd%self.fps
        self.durationFramesTW.set(self.nbFrames, 0)
        self.redrawTimeAndFullRange()
        

    def setDurationMinutes(self, val):
        deltaMinutes = val-self.nbMinutes
        self.nbMinutes = val
        timeEnd = self._director().getLastFrame() 
        timeEnd += deltaMinutes*60*self.fps
        self.setDuration(timeEnd)
        self.redrawTimeAndFullRange()


    def setDurationSeconds(self, val):
        deltaSeconds = val-self.nbSeconds
        self.nbSeconds = val
        timeEnd = self._director().getLastFrame() 
        timeEnd += deltaSeconds*self.fps
        self.setDuration(timeEnd)
        self.redrawTimeAndFullRange()


    def setDurationFrames(self, val):
        deltaFrames = val-self.nbFrames
        self.nbFrames = val
        timeEnd = self._director().getLastFrame() 
        timeEnd += deltaFrames
        self.setDuration(timeEnd)
        
        self.redrawTimeAndFullRange()


    def redrawTimeAndFullRange(self):
        # redraw time line and actors that have displays spanning the full
        # range (i.e. fullRange actors or actors with funciton displayed)
        self.redrawTime()
##         self.deleteActors(fullRangeOnly=1)
##         self.drawActors(fullRangeOnly=1)
        canvas = self.canvas
        for actor in self._director().actors:
##             if actor.isFullRange():
            canvas.tag_raise('actor_'+actor.name)
        
        canvas.tag_raise('timeCursor')
        if len(self.timeIntervalLabels):
            for id in self.timeIntervalLabels:
                canvas.tag_raise("timeInterval%d"%id)
        self.drawStartStopLine()


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
        


    def drawStartStopLine(self):
        canvas = self.canvas
        fill1 = "green3"
        fill2 = "red"
        x1 = self.xoff
        x2 = self.positionFromFrame(self.startFrame)
        x3 = self.positionFromFrame(self.stopFrame)
        x4 = self.xoff+self.timeBegin+self.scale*self._director().getLastFrame()
        y = self.yoff
        if self.startFrame == 0 and self.stopFrame == 1:
            fill2 = "green3"
        tag = 'start_stop'
        canvas.delete(tag)
        canvas.create_line(x1, y, x2, y , tags = (tag, 'start_stopLine1',), fill=fill2)
        canvas.create_line(x2, y, x3, y , tags = (tag, 'start_stopLine2',), fill=fill1)
        canvas.create_line(x3, y, x4, y , tags = (tag, 'start_stopLine3',), fill=fill2)
        
        #create marks
        id1 = canvas.create_polygon(x2, y, x2-3, y-6, x2-3, y-13, x2+3, y-13, x2+3, y-6, x2, y,
                                    fill='PaleGreen1', outline='green4', tags = (tag, 'startMark',) )
        id2 = canvas.create_polygon(x3, y, x3-3, y-6, x3-3, y-13, x3+3, y-13, x3+3, y-6, x3, y,
                                    fill='PaleGreen1', outline='green4', tags = (tag, 'stopMark',) )
        self.balloons.tagbind(self.canvas,'start_stopLine3', "start-end play line")
        self.balloons.tagbind(self.canvas,'start_stopLine2', "start-end play line")
        canvas.tag_bind(id1, '<Button-3>', CallbackFunction(self.showStartStopMarkEntry, 'startMark'))
        canvas.tag_bind(id2, '<Button-3>', CallbackFunction(self.showStartStopMarkEntry, 'stopMark'))
        canvas.tag_bind(id1, '<Button-1>', self.mouse1DownStartMark)
        canvas.tag_bind(id2, '<Button-1>', self.mouse1DownStopMark)


    def redraw(self):
        self.redrawTime()
        self.drawStartStopLine()
        self.deleteActors()
        self.drawActors()
        if len(self.timeIntervalLabels):
            for id in self.timeIntervalLabels:
                self.canvas.tag_raise("timeInterval%d"%id)

    ##
    ## drawing functions
    ##
    def frameFromPosition(self, x):
        # compute a the frame closest to this x coordinate
        return round((x - self.xoff - self.timeBegin)/self.scale)


    def positionFromFrame(self, frame):
        # compute the x coordinate for a given frame
        return self.xoff + self.timeBegin + frame*self.scale


    def placeTimeCursor(self, frame=0):
        polCoords, lineCoords = self.getTimeCursorCoords(frame)
        canvas = self.canvas
        canvas.coords(self.readHead, *polCoords)
        canvas.coords(self.cursorLine, *lineCoords)
        
        #m,s,f = self.frameToMSF(frame)
        #self.canvas.itemconfigure(self.cursorLabel,
        #                          text='%02d:%02d:%02d'%(m,s,f))
        # UPDATE IS NEEDED SO THAT CURSOR UPDATES DURING PLAY
        canvas.update()


    def getTimeCursorCoords(self, frame):
        x = self.positionFromFrame(frame)
        #y = self.yoff
        y = self.timeOffset
        polCoords = (x, y, x-3, y-6, x-3, y-13, x+3, y-13, x+3, y-6, x, y)
        yend = self.lastLine
        lineCoords = (x, y, x, self.lastLine)
        return polCoords, lineCoords


    def drawTimeLine(self, drawLevel1=True, drawLevel2=True, drawLabels=True):

        canvas = self.canvas
        timeBegin = self.timeBegin
        timeEnd = self._director().getLastFrame() 
        curx = self.xoff
        #cury = self.yoff
        cury = self.timeOffset
        scale = self.scale
        fps = self.fps
        yend = self.lastLine
        
        # draw vertical lines
        for i in range(int(timeEnd-timeBegin+1)):
            x = curx + timeBegin + scale*i
            if (i%self.thickLineStep) == 0:
                canvas.create_line(x, cury, x, yend, width=1, fill='black',
                              tags=('timeline'))
            elif (i%self.thickLineL2Step) == 0:
                if drawLevel2:
                    canvas.create_line(x, cury, x, yend, width=1, fill='grey75',
                                  tags=('timeline'))
            else:
                if drawLevel1:
                    canvas.create_line(x, cury, x, yend, width=1, fill='grey75',
                                  stipple='gray50', tags=('timeline'))
            if drawLabels: #and
                if i%self.labelStep == 0: # force this label
                    canvas.create_text(x, cury-1, text='%02d:%02d:%02d'%(
                        i/(60*fps),(i/fps)%60,i%fps), anchor='s',
                                  tags=('timeline'), fill='magenta')
                    lastLabPos = x
                else:
                    #further than 40 for last drawn and further than 40 from
                    # next forced
                    if x-lastLabPos > 40 and \
                           (self.fps-(i%self.labelStep))*scale > 40:
                        canvas.create_text(x, cury-1, text='%02d'%(i%fps,),
                                      anchor='s', tags=('timeline'), fill='blue')
                        lastLabPos = x

        # draw horizontal line
        timeLine = canvas.create_line(curx+timeBegin, cury, curx+scale*timeEnd,
                                 cury, width=2, tags=('timeline'))

        # time cursor
        frame = self._director().currentFrame
        polCoords, lineCoords = self.getTimeCursorCoords(frame)
        canvas = self.canvas
        self.readHead = canvas.create_polygon( *polCoords, **{
            'fill':'green', 'width':2, 'tags':('timeCursor',)})
        self.cursorLine = canvas.create_line( *lineCoords, **{
            'fill':'green', 'width':2, 'tags':('timeCursor',)})
        canvas.tag_bind('timeCursor', '<ButtonPress-1>', self.mouse1DownTimeCursor)
        canvas.tag_bind('timeCursor', '<ButtonPress-3>', self.mouse3DownTimeCursor)
        #self.cursorLine = canvas.create_line(x, y, x, ystart, x-25, ystart,
        #     x-25, ystart-boxH, x+25, ystart-boxH, x+25, ystart, x, ystart,
        #     fill='green', width=2, tags=('timeCursor',))
        #m,s,f = self.frameToMSF(self._director().currentFrame)
        #self.cursorLabel = canvas.create_text(x, ystart,text='%02d:%02d:%02d'%(m,s,f),
        #                          anchor='n', fill='red', tags=('timeCursor',))

    def deleteTimeLine(self):
        self.canvas.delete('timeline')
        self.canvas.delete('timeCursor')


    def drawActors(self, fullRangeOnly=False):
        director = self._director()
        posy = self.yoff+self.actorStep
        #add two buttons for toggling playing, recording of all actors
        fill = 'red'
        if not self.allrecording:
            fill = 'black'

        cid = self.canvas.create_oval(self.xoff-12, posy-4, self.xoff-4, posy+4,
                                outline='grey50', width=1,
                                fill=fill, tags=('actorsrecording'))
        self.balloons.tagbind(self.canvas, cid, 'Select all actors for recording keyframes')
        self._recordCheckbuttonId = cid
        self.canvas.tag_bind(cid, '<Button-1>', self.toggleAllActorsRecording)
        fill = "green"
        if not self.allplaying:
            fill = "black"
        cid1 = self.canvas.create_oval(self.xoff-24, posy-4, self.xoff-16, posy+4,
                             outline='grey50', width=1,
                             fill=fill, tags=('actorsplaying'))
        self.balloons.tagbind(self.canvas, cid1, 'Select all actors for playing')
        self._playCheckbuttonId = cid1
        
        self.canvas.tag_bind(cid1, '<Button-1>', self.toggleAllActorsPlaying)
        posy += self.actorStep
        
        for i, actor in enumerate(director.actors):
            if not actor.visible: continue
            posy = self.drawActor(actor, posy, i)
            posy += self.actorStep


    def drawActor(self, actor, posy, actorind = None):

        name = actor.name
        canvas = self.canvas
        director = self._director()
        curx = self.xoff+self.timeBegin
        timeEnd = director.getLastFrame() 
        scale = self.scale
        # draw the actor's grey line.
        cid = canvas.create_line(curx, posy, curx+self.scale*timeEnd*100, posy,
                                 width=2, fill='grey50', tags=('actor_'+name))
        self.balloons.tagbind(canvas, cid, name)
        canvas.tag_bind(cid, '<Button-3>',
                        CallbackFunction(self.showActorMenu_cb, actor, None))
        canvas.tag_bind(cid, '<Button-1>',
                        CallbackFunction(self.selectActorForMoving_cb, actor))
        # this will reconfigure the balloon widget xoofset ,so that it appears close
        # to the mouse pointer when it enters the actors' line.
        #(xoffset is a horizontal distance from the left corner
        # of the canvas item bound to the balloon , default = 20)  
        canvas.tag_bind(cid, '<Enter>', self.setBalloon_cb, add=True)
        canvas.tag_bind(cid, '<Leave>', self.setBalloon_cb, add=True)
        
        # draw buttons that idicate if the actor is recording and playing .
        if len(actor.valueGenerators):
            if actor.hasGetFunction :
                if actor.recording:
                    fill = 'red'
                else: fill = 'black'
                cid1 = canvas.create_oval(curx-12, posy-4, curx-4, posy+4,
                                          outline='grey50', width=1,
                                          fill=fill, tags=('actor_'+name))
                self.balloons.tagbind(canvas, cid1, 'Select actor for recording keyframes')
                actor._recordCheckbuttonId = cid1
                canvas.tag_bind(cid1, '<Button-1>',
                                CallbackFunction(self.toggleActorRecording, actor))
            if actor.playing:
                fill = 'green'
            else:
                fill = 'black'
            cid2 = canvas.create_oval(curx-24, posy-4, curx-16, posy+4,
                                outline='grey50', width=1,
                                fill=fill, tags=('actor_'+name))
            self.balloons.tagbind(canvas, cid2, 'Select actor for playing')
            actor._playCheckbuttonId = cid2
            canvas.tag_bind(cid2, '<Button-1>',
                            CallbackFunction(self.toggleActorPlaying, actor))
        if self.upDownArrowsOn:
            self.addUpDownArrows(actor, posy, actorind)
        
        self.drawKeyFrames(actor, curx, posy, actorind)
        actor._posy = posy

        posy += self.actorStep
        if actor.displayFunction:
            posy = self.drawFunction(actor, posy)
            #posy += (actor.graphHeight+10)*nbvar
            
        if self.namesOn:
            self.showActorName(actor)
        return posy
    
            


    def deleteActors(self):
        for actor in self._director().actors:
            self.deleteActor(actor)
            

    def deleteActor(self, actor):
        #print 'deleting actor', actor.name
        self.canvas.delete('actor_'+actor.name)

    def drawKeyFrames(self, actor, posx, posy, actorind = None):
        frames = actor.keyframes._sortedKeys
        name = actor.name
        canvas = self.canvas
        sf = []
        if self.selectedFrames.has_key(name):
            sf = map(lambda x: x[0], self.selectedFrames[name])
        for i in range(len(frames)):
            fill = "green"
            frame = frames[i]
            end = posx+frame*self.scale
            #print "drawKF:", start, end, posy, name, frame, fill
            if i > 0:
                if not actor.valueGenerators[i-1].active:
                    fill = "grey50"
                start = posx+frames[i-1]*self.scale
                lineid =  canvas.create_line(start, posy, end,
                                          posy, width=3, fill=fill,
                                          tags=('actor_'+name, 'keyframe_line_%s_%d'%(name, frame)))
                self.balloons.tagbind(canvas, lineid, name)
                canvas.tag_bind(lineid, '<Button-3>',
                                CallbackFunction(self.showActorMenu_cb, actor, frame))
                canvas.tag_bind(lineid, '<Button-2>',
                            CallbackFunction(self.toggleDrawFunction_cb, actor))
                canvas.tag_bind(lineid, '<Button-1>',
                                CallbackFunction(self.selectActorForMoving_cb, actor))
            outline = "black"
            valind = actor.keyframes[frame]
            balloontx = None
            if frame in actor.linkedKeyFrames[valind]:
                outline = "red"
                balloontx = "linked kf: "
                for ff in actor.linkedKeyFrames[valind]:
                    if ff != frame:
                        balloontx = balloontx + str(ff) + " "
            cid = canvas.create_oval(end-2, posy-5, end+2, posy+5,
                                outline=outline, width=1,
                                fill="green",
                                tags=('actor_'+name,
                                      'keyframe_%s_%d'%(name, frame)))

            #if frame > 0 :#and frame != frames[-1]:
            canvas.tag_bind(cid, '<Button-3>',
                            CallbackFunction(self.showKFMenu_cb, actor, frame) )

            canvas.tag_bind(cid, '<Button-1>',
                            CallbackFunction(self.selectKeyFrame_cb , actor, frame))

            if balloontx:
                self.balloons.tagbind(canvas, cid, balloontx)

            canvas.tag_raise('keyframe_%s_%d'%(name, frames[i-1]))
            if frame in sf:
                ind = sf.index(frame)
                self.selectedFrames[name][ind] = (frame, cid)
        if len(sf):
            self.markKeyframes(self.selectedFrames[name], actor, posy)


    def toggleActorRecording(self, actor, event=None):
        actor.recording = not actor.recording
        self.drawActorRecordingButton(actor)


    def drawActorRecordingButton(self, actor):
        if not hasattr(actor, "_recordCheckbuttonId"):
            return
        if actor.recording:
            self.canvas.itemconfigure(actor._recordCheckbuttonId, fill='red')
        else:
            self.canvas.itemconfigure(actor._recordCheckbuttonId, fill='black')


    def toggleAllActorsRecording(self, event=None):
        canvas = self.canvas
        director = self._director()
        fill = canvas.itemcget(self._recordCheckbuttonId, 'fill')
        if fill == 'red':
            fill = 'black'
            self.allrecording = 0
        else:
            fill = 'red'
            self.allrecording = 1
        for actor in director.actors:
            if hasattr(actor,'_recordCheckbuttonId'):
                canvas.itemconfigure(actor._recordCheckbuttonId, fill=fill)
                actor.recording = self.allrecording
        canvas.itemconfigure(self._recordCheckbuttonId, fill=fill)
            
    def toggleActorPlaying(self, actor, event=None):
        actor.playing = not actor.playing
        self.drawActorPlayingButton(actor)


    def drawActorPlayingButton(self, actor):
        if not hasattr(actor, "_playCheckbuttonId"):
            return
        if actor.playing:
            self.canvas.itemconfigure(actor._playCheckbuttonId, fill='green')
        else:
            self.canvas.itemconfigure(actor._playCheckbuttonId, fill='black')

    
    def toggleAllActorsPlaying(self, event=None):
        canvas = self.canvas
        director = self._director()
        fill = canvas.itemcget(self._playCheckbuttonId, 'fill')
        if fill == 'green':
            fill = 'black'
            self.allplaying = 0
        else:
            fill = 'green'
            self.allplaying = 1
        for actor in director.actors:
            if hasattr(actor,'_playCheckbuttonId'):
                actor.playing = self.allplaying
                canvas.itemconfigure(actor._playCheckbuttonId, fill=fill)
        canvas.itemconfigure(self._playCheckbuttonId, fill=fill)


    def selectActorForMoving_cb(self, actor, event= None):
        # callback of Button1 press on the actors line. It draws a blue selection box
        # around the actor and binds callbacks for Button1-Motion and Release.
        
        self.stopSelection = True
        name = actor.name
        sortedframes = actor.keyframes._sortedKeys
        canvas = self.canvas
        director = self._director()
        curx = self.xoff+self.timeBegin
        posy = actor._posy
        nvalgen = len(actor.valueGenerators)
        x = canvas.canvasy(event.x)
        x1 = curx-5
        if nvalgen >1:
            x2 = curx+self.scale*actor.getLastFrame()+5
        else:
            x2 = curx+self.scale*director.getLastFrame()
        y1 = posy-7
        y2 = posy+7
        tags = ('actor_'+name, 'actorSelectionBox')
        canvas.create_rectangle(x1, y1, x2, y2, width=1,
                                      outline='RoyalBlue1', fill = 'LightSteelBlue1', tags=tags)
        canvas.lower(tags[1])
        if nvalgen >1:
            canvas.create_line(curx, posy, x2, posy, width=2, fill = "green", tags = tags)
        canvas.create_text(x, y1-17, text=name, anchor='n', fill = 'RoyalBlue1', tags = tags)
        
        canvas.bind('<B1-Motion>', self.moveActorSelectionBox)
        canvas.bind('<ButtonRelease-1>', CallbackFunction(self.endMoveActorSelectionBox, actor))
        self.lastPosy = posy


    def moveActorSelectionBox(self, event = None):
        # button1-motion callback - moves actor's selection box up/down
        canvas = self.canvas
        y = canvas.canvasy(event.y)
        canvas.move('actorSelectionBox',0, y - self.lastPosy) 
        self.lastPosy = y


    def endMoveActorSelectionBox(self, actor, event = None):
        # button1-release callback: moves actor to a new position
        # specified by the location of the actor's selection box.
        
        self.stopSelection = False
        canvas = self.canvas
        y = canvas.canvasy(event.y)
        x = canvas.canvasy(event.x)
        name = actor.name
        items = canvas.find_overlapping(x-7, y-7, x+7, y+7)
        moveto = None
        for it in items:
            tags = canvas.gettags(it)
            #print "tags:", tags
            if len(tags):
                tag0 = tags[0].split("_")
                if len(tag0) == 2:
                    if tag0[0] == "actor" and tag0[1] != name:
                        moveto = tag0[1]
                        break
        if moveto is not None and moveto != name:
            #print "moving actor %s to %s" % (name , moveto) 
            director = self._director()

            for newactorind, aa in enumerate(director.actors):
                if aa.name == moveto:
                    break
            director.actors.remove(actor)
            director.actors.insert(newactorind, actor)
            self.deleteActors()    
            self.drawActors()
        canvas.unbind('<B1-Motion>')
        canvas.unbind('<ButtonRelease-1>')  
        canvas.delete('actorSelectionBox')
        

    def moveActorUpDown(self, actorname, direction = None, actorind = None, event=None):
        # move actor one position up/down

        if direction not in ("down", "up"):
            return
        director = self._director()
        if actorind == None:
            # find current actors position in the director.actors list
            for actorind, aa in enumerate(director.actors):
                if aa.name == actorname:
                    break
        actor = director.actors.pop(actorind)
        if direction == "up":
            director.actors.insert(actorind-1, actor)
        else:
            director.actors.insert(actorind+1, actor)
        self.deleteActors()    
        self.drawActors()


    def showActorMenu_cb(self, actor, frame,  event):
        #print "in showActorMenu:", actor.name, frame , event
        ind1 = self.actorMenu.index("Delete Actor")
        director = self._director()
        
        self.actorMenu.entryconfigure(ind1,
                               command = CallbackFunction(director.deleteActor, actor))
        ind2 = self.actorMenu.index("Record Keyframe")
        if actor.hasGetFunction:
            self.actorMenu.entryconfigure(ind2,
                   command = CallbackFunction(self.recordKeyframe_cb, actor),
                                          state='normal')
        else:
            self.actorMenu.entryconfigure(ind2, state='disabled')
        # get current label of the "Segment Interpolation" menu item
        ind3 = self.actorMenu.index (self.actorMenuDict["Segment Interpolation"])
        frames = actor.keyframes._sortedKeys
        
        if frame is None:
            self.actorMenu.entryconfigure(ind3, state='disabled')
            segment = len(frames)-1
        else:
            self.actorMenu.entryconfigure(ind3, state='normal')
            segment = frames.index(frame)-1
            if actor.valueGenerators[segment].active:
                label = 'Stop Segment Interpolation'
                stopinterpolation = True
            else:
                label = 'Resume Segment Interpolation'
                stopinterpolation = False
            if self.actorMenuDict["Segment Interpolation"] != label:
                self.actorMenuDict["Segment Interpolation"] = label
                self.actorMenu.entryconfigure(ind3, label = label)        
            self.actorMenu.entryconfigure(ind3,
                   command = CallbackFunction(self.toggleSegmentInterpolation, actor, frame, segment,
                                              stopinterpolation = stopinterpolation))
            
            ind4 = self.actorMenu.index("Add behavior")
            self.actorMenu.entryconfigure(ind4,
                            command = CallbackFunction(self.addBehavior_cb, actor, frame, segment))
            ind5 = self.actorMenu.index("Remove behavior")
            if len(actor.valueGenerators[segment].behaviors) > 1:
                self.actorMenu.entryconfigure(ind5, state='normal')
                self.actorMenu.entryconfigure(ind5,
                            command = CallbackFunction(self.removeBehavior_cb, actor, frame, segment))
            else:
               self.actorMenu.entryconfigure(ind5, state='disabled')
        # if specified frame is not visible in the scrolled canvas view
        # add a command to the menu to allow the user to move this
        # keyframe to a new position:

        mvkeyframes = [actor.name]
        for f in (frame, frames[segment]):
            if f is not None:
                if not self.isFrameInView(f):
                    mvkeyframes.append(f)
        oldmvkeyframes = self.actorMenuDict["Move keyframe"]
        if  oldmvkeyframes != mvkeyframes:
            if len(oldmvkeyframes) > 1:
                for f in oldmvkeyframes[1:]:
                    ind = self.actorMenu.index("Move keyframe %i"%f)
                    #print "removing menu item: ind", ind, "kf:", f, 'label:', self.actorMenu.entryconfigure(ind)['label'][-1] 
                    self.actorMenu.delete(ind)
            i = 2
            for f in mvkeyframes[1:]:
                #print "inserting command 'Move keyframe %i' at ind %i" % (f, i)
                self.actorMenu.insert_command(i, label= "Move keyframe %i"%f,
                         command = CallbackFunction(self.showMoveKeyFrameEntry, actor, f))
                i = i+1
            self.actorMenuDict["Move keyframe"] = mvkeyframes
        
        self.actorMenu.post(event.x_root, event.y_root)


    def showMoveKeyFrameEntry(self, actor, frame, event=None):
        # actormenu  "Move keyframe #" callback. Pops an input form with an EntryField
        # to specify the new location of the keyframe. 
        idf = InputFormDescr(title='Move keyframe %d'% frame)
        validator = {'validator':'integer', 'min': 0}
        idf.append({'name': "movekf",
                    'widgetType': Pmw.EntryField,
                    'required':1,
                    'wcfg':{'labelpos':'w',
                            'entry_width': 8,
                            'label_text': "new frame:",
                            'value': str(frame),
                            'validate': validator},
                    
                    'gridcfg':{'sticky':'we'}
            })
##         form=InputForm(self.root, None, idf, blocking = 1)
##         res = form.go()
##         newframe = res.get("movekf")
##         if newframe is not None:
##             newframe = int(newframe)
##             if newframe != frame:
##                 self.selectKeyFrame_cb(actor, frame, event = None, newframe=newframe)

        form=InputForm(self.root, None, idf, blocking = 0, modal = 0)
        def form_cb():
            newframe = form.checkValues()["movekf"]
            form.destroy()
            if newframe is not None:
                newframe = int(newframe)
                if newframe != frame:
                    self.selectKeyFrame_cb(actor, frame, event = None, newframe=newframe)
        idf.entryByName['movekf']['widget'].configure(command=form_cb)

        
    def toggleSegmentInterpolation(self, actor, frame, segment, stopinterpolation = True ):
        canvas = self.canvas
        name = actor.name
        frames = actor.keyframes._sortedKeys
        if stopinterpolation:
            active = False
            fill = "grey50"
        else:
            active = True
            fill = "green"
        # are there any other segments that share the same valueGenerator:
        segments = [(segment, frame),]
        if len(actor.linkedVG[segment]):
            for ind in actor.linkedVG[segment]:
                segments.append((ind, frames[ind+1]))
        for segment, frame in segments:
            actor.valueGenerators[segment].configure(active = active)
            canvas.itemconfigure("keyframe_line_%s_%d"%(name, frame), fill = fill)
        if actor.displayFunction:
            posy = actor._posy + self.actorStep
            self.deleteFunction(actor)
            posy = self.drawFunction(actor, posy)


    def addBehavior_cb(self, actor, frame, segment, event = None):
        frames = actor.keyframes._sortedKeys
        segmentStr = "segment %d (frames %d..%d)" %(segment, frames[segment], frame) 
        idf = InputFormDescr(title='Add behavior')
        idf.append({'name':'behaviors',
                    'widgetType':ListChooser,
                    'required':1,
                    'wcfg':{'entries': map(lambda x: (x,None), BehaviorList), 
                            'title':'Choose a behavior:',
                            'lbwcfg':{'exportselection':0},
                            'mode':'single','withComment':0,
                            },
                    'gridcfg':{'sticky':'we', 'padx':5}})
        
        idf.append({'name': 'level',
                    'widgetType': Pmw.RadioSelect,
                    'listtext':[segmentStr, "all segments"],
                    'defaultValue': segmentStr,
                    'wcfg':{'label_text':'add behavior to :',
                            'labelpos':'nw','buttontype':'radiobutton'},
                    'gridcfg':{'sticky':'we'} }) #,'columnspan':2} 
                    
        
        form=InputForm(self.root, None, idf, blocking = 1)
        res = form.go()
        behavior = res.get('behaviors')
        level = res.get('level')
        #print 'behavior',behavior, 'level', level
        if behavior:
            mod = __import__("scenario.interpolators", globals(), locals(), behavior)
            bclass = getattr(mod, behavior[0])
            if level == "all segments":
                valueGenerators = actor.valueGenerators
            else:
                valueGenerators = [actor.valueGenerators[segment],]
            linkedvg = []
            for i, vg in enumerate(valueGenerators):
                if i in linkedvg:
                    continue
                add = True
                for bh in vg.behaviors:
                    if bh.__class__ == bclass:
                        if len(valueGenerators)> 1:
                            segment = i
                        ans = tkMessageBox.askquestion("Scenario", "Behavior %s exists for actor %s, segment %d.\nDo you want to add another one?"%(behavior[0], actor.name, segment))
                        if ans == "no":
                            add = False
                        break
                if add:
                    if len(actor.linkedVG[i]):
                        linkedvg.extend(actor.linkedVG[i])
                    if not vg.addBehavior(None, bclass):
                        if len(valueGenerators)> 1:
                            segment = i
                        tkMessageBox.showwarning("Scenario warning", "Could not add behavior %s to segment %d:\nexpected %d number of variables, got %d"%(behavior[0], segment, vg.nbvar, bclass.nbvar))
            if actor.displayFunction:
                self.deleteFunction(actor)
                self.drawFunction(actor, actor._posy+self.actorStep)
                    
                                               

    def removeBehavior_cb(self, actor, frame, segment, event = None):
        if len(actor.valueGenerators[segment].behaviors) <2:
            return
        frames = actor.keyframes._sortedKeys
        segmentStr = "segment %d (frames %d..%d)" %(segment, frames[segment], frame) 
        idf = InputFormDescr(title='Remove behavior')
        bl = []
        for i, behavior in enumerate(actor.valueGenerators[segment].behaviors[1:]):
            bl.append((behavior.__class__.__name__, behavior))
            #behaviorDict[behavior.__class__.__name__] = behavior
        idf.append({'name':'behaviors',
                    'widgetType':ListChooser,
                    'required':1,
                    'wcfg':{'entries': bl,
                            'title':'Choose a behavior:',
                            'lbwcfg':{'exportselection':0},
                            'mode':'single','withComment':0,
                            },
                    'gridcfg':{'sticky':'we', 'padx':5}})
        
        idf.append({'name': 'level',
                    'widgetType': Pmw.RadioSelect,
                    'listtext':[segmentStr, "all segments"],
                    'defaultValue': segmentStr,
                    'wcfg':{'label_text':'remove behavior from:',
                            'labelpos':'nw','buttontype':'radiobutton'},
                    'gridcfg':{'sticky':'we'} }) #,'columnspan':2} 
                    
        
        form=InputForm(self.root, None, idf, blocking = 1)
        res = form.go()
        lc = form.descr.entryByName['behaviors']['widget']
        behaviorName = res.get('behaviors')
        level = res.get('level')
        #print 'behavior',behavior, 'level', level
        if behaviorName:
            ind = lc.getInd()[0]
            #behavior =  behaviorDict[behaviorName[0]]
            behavior = bl[ind][1]
            if level == "all segments":
                linkedvg = []
                for i, vg in enumerate(actor.valueGenerators):
                    if i not in linkedvg:
                        if i !=segment:
                            for bh in vg.behaviors[1:]:
                                if bh.__class__.__name__ == behaviorName[0]:
                                   vg.removeBehavior(bh)
                                   break
                        else:
                            vg.removeBehavior(behavior)
            else:
                actor.valueGenerators[segment].removeBehavior(behavior)
            if actor.displayFunction:
                self.deleteFunction(actor)
                self.drawFunction(actor, actor._posy+self.actorStep)


    def isFrameInView(self, frame):
        # returns true if the specified frame is visible in the scrolled canvas view
        maxx = self.scrollregion[2]
        xpos = self.positionFromFrame(frame)*1./maxx
        view = self.scrolledCanvas.xview()
        #print "isFrameInView:  xpos = ", xpos, "view = ", view 
        if xpos < view[0] or xpos > view[1]:
            return False
        else:
            return True
                

    def showKFMenu_cb(self, actor, frame, event):
        ind1 = self.kfMenu.index("Delete Keyframe")
        self.kfMenu.entryconfigure(ind1,
                     command = CallbackFunction(self.deleteKeyFrame, actor, frame))
        self.kfMenu.post(event.x_root, event.y_root)
        ind2 = self.kfMenu.index("Dismiss")
        ind3 = self.kfMenu.index("Select Set")
        ind4 = self.kfMenu.index("Unlink Set")
        if actor.kfSetId.has_key(frame):
            id = self.kfSets[actor.kfSetId[frame]].Id
            self.kfMenu.entryconfigure(ind3, state=Tkinter.NORMAL,
                                  command=CallbackFunction(self.selectKFSet, id))
            self.kfMenu.entryconfigure(ind4, state=Tkinter.NORMAL,
                                  command=CallbackFunction(self.unlinkKFSet, id))
        else:
            self.kfMenu.entryconfigure(ind3, state=Tkinter.DISABLED)
            self.kfMenu.entryconfigure(ind4, state=Tkinter.DISABLED)
            
            
    def selectKFSet(self, kfSetId, event = None):
        
        kfset = self.kfSets[kfSetId]
        canvas = self.canvas
        self.selectedFrames = {}
        canvas.delete("selection")
        for item in kfset.setframes:
            actor = item[0]
            name  = actor.name
            sf = []
            for kf in item[1:]:
                id = canvas.find_withtag("keyframe_%s_%d"%(name, kf))
                if not len(id):
                    print "WARNING: can not select kfset:",  kfSetId
                    self.selectedFrames = {}
                    canvas.delete('selection')
                    return
                sf.append((kf, id[0]))
            self.selectedFrames[name] = sf
            self.markKeyframes(sf, actor, actor._posy)
        self.updateCopyPasteMenus()
        

    def deleteKeyFrame(self, actor, frame, frames = []):
        # remove selected keyframe (keyframes) and interpolation segment to the right of it.
        # lastVal of the value generator to the left of the specified frame is configured to
        # the value of the next (right) keyframe.
        sortedframes = actor.keyframes._sortedKeys
        if not len(frames):
            # check if the specified frame is linked with some other frames.
            frames = [frame]
            valind = actor.keyframes[frame]
            lf =  actor.linkedKeyFrames[valind]
            for f in lf:
                if f != frame:
                    #if f == 0:
                    #    tkMessageBox.showwarning("Scenario warning", "Can not remove frame %d (%s actor), it is linked with frame 0." % (frame, actor.name))
                    #    return
                    frames.append(f)
            if len(frames) > 1:
                # check if we need to unlink the value generators (to the left of the selected
                # keyframes) before they get reconfigured.
                # If the keyframe next (right) to the selected one belongs to a different kfSet,
                # unlink the value generator
                vg = actor.valueGenerators
                for frame in frames:
                    setid1 = actor.kfSetId.get(frame)
                    ind = sortedframes.index(frame)
                    if len(sortedframes)-1 == ind:
                        setid2 = None
                    else:
                        setid2 = actor.kfSetId.get(sortedframes[ind+1])
                    linkedVG = actor.linkedVG
                    if ind > 0:
                        vgind = ind - 1
                        if setid1 != setid2:
                            if len(linkedVG[vgind]):
                                newGen = vg[vgind].clone()
                                vg[vgind] = newGen
                            for ii in linkedVG[vgind]:
                                if vgind in linkedVG[ii]:
                                    linkedVG[ii].remove(vgind)
                            linkedVG[vgind] = []
        frames.sort()
        sf = []
        name = actor.name
        if self.selectedFrames.has_key(name):
            sf = map(lambda x: x[0], self.selectedFrames[name])
        if len(frames) == len(sortedframes):
            # we are about to delete all of the keyframes of the actor,            
            # so we will just remove the actor:
            self._director().deleteActor(actor)
            return
        for frame in frames:
            if frame in sf:
                ind = sf.index(frame)
                self.selectedFrames[name].pop(ind)
                if not len(self.selectedFrames[name]):
                    del(self.selectedFrames[name])
            if len(self.pasteBuffer):
                # check if the frame selected for removal is in the pasteBuffer
                for entry in self.pasteBuffer[1:]:
                    if entry[0].name == name:
                        if frame in entry[1]:
                            # empty paste buffer (?????)
                            self.pasteBuffer = []
                            self.updateCopyPasteMenus()
                        break
            # remove the frame from kfSets
            kfset = None
            if actor.kfSetId.has_key(frame):
                kfset = self.kfSets.get(actor.kfSetId[frame])
                if kfset:
                    kfset.removeKeyFrame(actor.name, frame)
                    if kfset.getNumberOfFrames() == 1:
                        # There is only one frame left in the kfSet - we don't need this set.
                        self.removeKFSet(kfset)
            actor.deleteKeyFrame(frame)
        self.deleteActor(actor)
        self.drawActor(actor, actor._posy)


    def removeKFSet(self, kfset):
        # remove specified kfset from the kfSets dictionary
        linkedkfset = None
        # if the kfset that we are removing is linked to only one other kfset (linkedkfset),
        # there is no point in keeping the linkedkfset keyframes in the set.
        for item in kfset.setframes:
            actor = item[0]
            for kf in item[1:]:
               if actor.kfSetId.has_key(kf):
                   del(actor.kfSetId[kf])
                   if not linkedkfset:
                       valind = actor.keyframes[kf]
                       linkedkf =  actor.linkedKeyFrames[valind][:]
                       if kf in linkedkf:
                           if len(linkedkf) == 2:
                               linkedkf.remove(kf)
                               linkedkfset = actor.kfSetId.get(linkedkf[0])
        del(self.kfSets[kfset.Id])
        if self.kfSets.has_key(linkedkfset):
            for item in self.kfSets[linkedkfset].setframes:
                actor = item[0]
                for kf in item[1:]:
                    if actor.kfSetId.has_key(kf):
                        del(actor.kfSetId[kf])
            del(self.kfSets[linkedkfset])

                                   
    def deleteActorKeyFrames(self, actor):
        #remove all lines and ovals representing selected actor's keyframes
        canvas = self.canvas
        name = actor.name
        for f in actor.keyframes._sortedKeys:
            canvas.delete("keyframe_line_%s_%d"%(name, f))
            canvas.delete("keyframe_%s_%d"%(name, f))


    def drawFunction(self, actor, posy):
        #FIX THIS (do not know how to draw function for composite interpolator)
        interpcl = (CompositeInterpolator,VarVectorInterpolator)
        for cl in  interpcl:
            if  issubclass(actor.interpClass, cl) :
                warnings.warn("Function drawing of actor %s interpolator is not available"%actor.name)
                return posy
        valmin, valrange = self.minMaxRange(actor)
        posx = self.xoff + self.timeBegin
        self.interpgui.configure(graphHeight = actor.graphHeight)
        frames = actor.keyframes._sortedKeys
        nbfunc = []
        # we draw function representing value interpolation for each interval
        # (between two subsequent keyframes). We will draw one circle(dot) representing
        # the keyframe value at the beginning of the graph line of an interval. 
        if len(frames) >1:
            for i in range(1,len(frames)):
                vg = actor.valueGenerators[i-1] # current interval value generator
                if vg.active:
                    drawLastVal = False # we will draw a line/curve for current
                                        # interpolator and a dot corresponding to
                                        # it's firstVal
                    if i == len(frames)-1:
                        # this is the last function interval, we need to draw
                        # a dot corresponding to it's last value:
                        drawLastVal = True
                    else:
                        if not actor.valueGenerators[i].active:
                            # the interpolation of the next interval is stopped, we need to
                            # draw lastVal dot for current valuegenerator:
                            drawLastVal = True
                    newposy = self.interpgui.drawFunctionComponent( \
                        vg, i-1, (frames[i-1], frames[i]),
                        self.scale, actor, posx, posy, valmin, valrange, drawLastVal)
                    if newposy is not None:
                        nbfunc.append(newposy)
                    else:
                        #could not draw the function
                        if actor.displayFunction:
                            actor.displayFunction = False
            if len(nbfunc):       
                posy += max(nbfunc)*(actor.graphHeight+self.actorStep)
        return posy


    def minMaxRange(self, actor):
        # compute min max and range of values for specified actor
        # 
        valGens = actor.valueGenerators
        values = []
        valmin = []
        valmax = []
        valrange = []
        nbvar = 0
        for vg in valGens:
            if vg.active:
                if vg.nbvar > nbvar:
                    nbvar = vg.nbvar
        
        for n in range(nbvar):
            # add an empty list that will contain keyframe values for each interpolator variable 
            # 
            values.append([])
        if isinstance(actor.datatype, BoolType):
            for n in range(nbvar):
                valmin.append(0.0)
                valrange.append(1.0)
            return valmin, valrange
        for vg in valGens:
            if vg.active:
                nfirst = 0
                nlast = 0
                #the first and last values of an interpolator(value generator) can be a 
                # scalar or a sequence. In the latter case, the lengths of firstVal
                # and lastVal may be different
                try:
                    nfirst = len(vg.firstVal)
                    nlast = len(vg.lastVal)
                    if nfirst == nlast:
                        for i in range(nfirst):
                            values[i].extend([vg.firstVal[i], vg.lastVal[i]])
                    else:
                        for i in range(nfirst):
                           values[i].append(vg.firstVal[i])
                        if nfirst < nlast:
                            for j in range(nfirst, nlast):
                               values[j].append(vg.firstVal[i]) 
                        for i in range(nlast):
                            values[i].append(vg.lastVal[i])
                        if nlast < nfirst:
                            for j in range(nlast, nfirst):
                                values[j].append(vg.lastVal[i])
                except:
                    values[0].extend([vg.firstVal, vg.lastVal])
        for val in values: 
            vmin = 99999.
            vmax = 0
            for v in val:
                if v<vmin: vmin = v
                if v>vmax: vmax = v
            valmin.append(vmin)
            valmax.append(vmax)
            vrange = vmax-vmin
            if vrange==0: vrange=1.
            valrange.append(vrange)
        #print valmin, valrange
        return valmin, valrange


    def mouseEnterFunc(self, event=None):
        canvas = self.canvas
        frame = self.frameFromPosition(canvas.canvasx(event.x))
        value = actor.getValueAt(frame)[0]

        ymin, yrange, vnum = params
        try:
            value = value[vnum]
        except TypeError:
            value = value

        # delete previous value text
        if self._funcValId:
            canvas.delete('functionDot')

        # build the new value text string
        if actor.valueFormat:
            valueStr = actor.valueFormat%value
        else:
            valueStr = str(value)

        # create the text on the canvas
        x = self.positionFromFrame(frame)
        scale = self.scale
        graphHeight = actor.graphHeight
        y = actor._posy + self.actorStep + vnum*(actor.graphHeight+self.actorStep) + graphHeight -(
            (value-ymin)/yrange)*graphHeight

        self._funcValId = canvas.create_text(
            x+5, canvas.canvasy(event.y)+5, text=valueStr,
            anchor='n', tags=('functionDot', 'actor_'+actor.name))
        # draw a blue dot on the function
        size = 2
        canvas.create_oval( x-size, y-size, x+size, y+size, fill='yellow',
                       tags=('functionDot', 'actor_'+actor.name))

    
    def deleteFunction(self, actor):
        self.canvas.delete('actorFunc_'+actor.name)


    def getActorByName(self, name):
        # find actor by it's name 
        director = self._director()
        for actor in director.actors:
            if actor.name == name:
                return actor                
        return None


    def getValueGenerator(self, actor, frame):
        if actor:
            return actor.getValueGenerator(frame)
        else:
            return None


    def showHideActorsNames_cb(self):
        # toggle show/hide  name labels for all vilsible actors on the canvas
        self.namesOn = not self.namesOn
        director = self._director()
        labelname1 = "Hide actor's names"
        labelname2 = "Show actor's names"
        menu = self.menuButtons['Edit'].menu
        if self.namesOn:
            ind = menu.index(labelname2)
            menu.entryconfigure(ind, label = labelname1) 
            for actor in director.actors:
                self.showActorName(actor)
        else:
            ind = menu.index(labelname1)
            menu.entryconfigure(ind, label = labelname2)
            self.canvas.delete('actorNameLabel')


    def showHideUpDownArrows_cb(self):
        # toggle show/hide up-down arrows that are used to shift actors 1 position up or down
        self.upDownArrowsOn = not self.upDownArrowsOn
        director = self._director()
        labelname1 = "Hide up-down arrows"
        labelname2 = "Show up-down arrows"
        menu = self.menuButtons['Edit'].menu
        if self.upDownArrowsOn:
            ind = menu.index(labelname2)
            menu.entryconfigure(ind, label = labelname1) 
            for actor in director.actors:
                if actor.visible:
                    self.addUpDownArrows(actor, actor._posy)
        else:
            ind = menu.index(labelname1)
            menu.entryconfigure(ind, label = labelname2)
            self.canvas.delete('updownarrows')


    def addUpDownArrows(self, actor, posy, actorind = None):
        # add up/down arrow icons
        # we will not add "up arrow" to the first visible actor  and "down button" to the last
        #one
        # find first visible actor:

        director = self._director()
        canvas = self.canvas
        curx = self.xoff+self.timeBegin
        name = actor.name
        for aa in director.actors:
            if aa.visible: break
        if aa.name != name:
            cid1 = canvas.create_image(curx-34, posy, image=self.arrowupIcon,
                                       tags=('actor_'+name, 'updownarrows'))
            self.balloons.tagbind(canvas, cid1, 'move actor one position up')
            canvas.tag_bind(cid1, '<Button-1>',
                            CallbackFunction(self.moveActorUpDown, actor.name, "up", actorind))
        # find last visible actor
        for aa in reversed(director.actors):
            if aa.visible: break
        if aa.name != name:
            cid2= canvas.create_image(curx-46, posy, image=self.arrowdownIcon,
                                      tags=('actor_'+name, 'updownarrows'))
            self.balloons.tagbind(canvas, cid2, 'move actor one position down')
            canvas.tag_bind(cid2, '<Button-1>',
                            CallbackFunction(self.moveActorUpDown, actor.name, "down", actorind))

            
    def showActorName(self, actor):
        # add name label to a specified actor

        x = self.xoff+self.timeBegin
        if actor.visible:
            name = actor.name
            y = actor._posy
            id = self.canvas.create_text(
                x+10, y-15, text=name,
                anchor='nw', tags=('actorNameLabel', 'actor_'+name))
        

    def selectKeyFrame_cb(self, actor, frame, event=None, newframe = None):
        # Button-1 callback (mouse is over a keyframe oval). Select keyframe for moving.
        # Register callbacks for moving the keyframe.

        # this will prevent drawing a selection box around keyframes
        canvas = self.canvas
        #canvas.unbind('<ButtonPress-1>')
        self.stopSelection = True
        movingFrames = []
        ctag = "keyframe_%s_%d"%(actor.name, frame)
        kf = actor.keyframes._sortedKeys
        # check if selected frame has linked copies of itself(ie. keyframes that share the same value index).        # If there are such keyframes, we need to move them along with the selected one
        movingFrames = [frame]
        tmp = []
        valind = actor.keyframes[frame]
        if len(actor.linkedKeyFrames[valind]): # frame has copies
            tmp = []
            for f in actor.linkedKeyFrames[valind]:
                if f != frame:
                    tmp.append(f)
            tmp.sort()
            movingFrames.extend(tmp)
        # we cannot move a keyframe over any other keyframe. So we need to compute how far
        # to the left and right each of the linked keyframes can move.
        # Also, we have to move all the linked keyframes the same amount of frames.
        minl = None # number of frames each of the linked keyframes can go to the left
        minr = None # --------------------------------------------------------------right
        numkf = len(kf)
        for f in movingFrames:
            cind = kf.index(f)
            #if cind == 0:
            #    minl = minr = 0
            #    break
            # find closest frames to the left and right of the current keyframe 
            if numkf >=  cind+2: # this is not the last keyframe 
                rframe = kf[cind+1]
                diff = rframe-f-1
                if minr == None:
                    minr = diff
                elif minr > diff:
                    minr = diff
            if cind == 0:
                if f == 0: diff = 0
                else: diff = f
            else:
                lframe = kf[cind-1]
                diff = f-lframe-1
            if minl == None:
                minl = diff
            elif minl > diff:
                minl = diff

        if actor.kfSetId.has_key(frame):
            kfset = self.kfSets[actor.kfSetId[frame]]
            ctag = "keyframe_%s_%d"%(actor.name, frame)
            canvas = self.canvas
            # highlight all keyframes of the set
            for item in kfset.setframes:
                name  = item[0].name
                for kf in item[1:]:
                    canvas.itemconfigure('keyframe_%s_%d'%(name, kf), fill="LightSalmon")
        
        if event is not None:
            # bind callbacks
            canvas.tag_bind(ctag, '<B1-Motion>',
                     CallbackFunction(self.moveKeyFrame, actor, movingFrames, minl, minr))
            canvas.tag_bind(ctag, '<ButtonRelease-1>',
                     CallbackFunction(self.moveKeyFrameEnd, actor, movingFrames))
        else:
            self.moveKeyFrame(actor, movingFrames, minl, minr, None, newframe)
        #print "movingFrames:",movingFrames, "minl:", minl, "minr:", minr
        

    def moveKeyFrame(self, actor, movingFrames, minl, minr, event=None, newframe = None):
        # move a keframe with <Button-1>. It will also move all keyframes linked to the selected one
        # (ie frames that share the same value index)
        name = actor.name
        canvas = self.canvas
        frame = movingFrames[0]
        if event is not None:
            # selected keyframe moved to :
            newframe = self.frameFromPosition(canvas.canvasx(event.x))
        diff = newframe - frame
        if diff < 0:
            if abs(diff) > minl: diff = -minl
        else:
            if minr != None:  
                if diff > minr: diff = minr
        frame = movingFrames[-1]
        sortedframes = actor.keyframes._sortedKeys
        for f in movingFrames:
            # new x coordinate of the moving frame on the canvas:
            newf = f + diff
            x = self.positionFromFrame(newf)    
            ctag = 'keyframe_%s_%d'%(name, f)
            fcoord = canvas.coords(ctag)[:]
            y1 = fcoord[1]
            y2 = fcoord[3]
            canvas.coords(ctag, x-2, y1, x+2, y2)

            # if the frame (f) is the last actor's frame,
            # update the coordinates of the line representing
            # interpolation of the interval before last keyframe:
            if f == sortedframes[-1]:
                ltag = 'keyframe_line_%s_%d'%(name, f)
                lcoord = canvas.coords(ltag)[:]
                if len(lcoord):
                    lcoord[2] = x
                    canvas.coords(ltag, *lcoord)
                    endframe = self._director().endFrame
                    if newf > endframe: #add time lines
                        self.setDuration(newf + 10)
            elif f == sortedframes[0]:
                if len(sortedframes) > 1:
                    ltag = 'keyframe_line_%s_%d'%(name, sortedframes[1])
                    lcoord = canvas.coords(ltag)[:]
                    if len(lcoord):
                        lcoord[0] = x
                        canvas.coords(ltag, *lcoord)
        if event == None:
            self.moveKeyFrameEnd(actor, movingFrames)

            
    def moveKeyFrameEnd(self, actor, movingFrames, event=None):
        # callback for the <ButtonRelease-1> event; end of moving a keyframe with Button1 
        canvas = self.canvas
        frame = movingFrames[0]
        name = actor.name
        kf = actor.keyframes
        ctag = 'keyframe_%s_%d'%(name, frame)
        x = canvas.coords(ctag)[0] + 2
        # new keyframe number:
        newframe = int(self.frameFromPosition(x))
        sf = None
        if self.selectedFrames.has_key(name):
            sf = map(lambda x: x[0], self.selectedFrames[name])
        if frame != newframe: # the selected keyframe has moved
            # update the actor's keyframes, linkedKeyFrames, and selectedFrames
            diff = newframe - frame
            posy = actor._posy
            for f in movingFrames:
                vind = kf[f]
                newf = f + diff
                del(kf[f])
                kf[newf] = vind
                for i, ff in enumerate(actor.linkedKeyFrames[vind]):
                    if ff == f:
                        actor.linkedKeyFrames[vind][i] = newf
                if sf:
                    if f in sf:
                        ind = sf.index(f)
                        self.selectedFrames[name][ind] = (newf, )
                if len(self.pasteBuffer):
                    # check if the moved frame was in the pasteBuffer
                    for entry in self.pasteBuffer[1:]:
                        if entry[0].name == name:
                            if f in entry[1]:
                                # empty paste buffer (?????)
                                self.pasteBuffer = []
                                self.updateCopyPasteMenus()
                            break
                if actor.kfSetId.has_key(f):
                    id = actor.kfSetId[f]
                    del(actor.kfSetId[f])
                    actor.kfSetId[newf] = id
                    self.kfSets[id].updateOneFrame(actor.name, f, newf)
            self.deleteActor(actor)
            self.drawActor(actor, posy)
                        
        canvas.tag_unbind(ctag, '<B1-Motion>')
        canvas.tag_unbind(ctag, '<ButtonRelease-1>')
        # resume bindings for making keyframe selection
        #canvas.bind("<ButtonPress-1>", self.startKFSelection)
        self.stopSelection = False
        if actor.kfSetId.has_key(newframe):
            kfset = self.kfSets[actor.kfSetId[newframe]]
            for item in kfset.setframes:
                name  = item[0].name
                for kf in item[1:]:
                    canvas.itemconfigure('keyframe_%s_%d'%(name, kf), fill="green")


    def startKFSelection(self, event=None):
        # Callback of the middle mouse button. Used for selecting a keyframe or a group of keyframes.
        if self.stopSelection : return
        #print "startKFSelection"
        canvas = self.canvas
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        self.selectionBox = [(x, y),]
        canvas.bind('<B1-Motion>', self.drawSelectionBox)
        canvas.bind('<ButtonRelease-1>', self.endKFSelection)

        
    def drawSelectionBox(self, event = None):
        # draws red selection box
        #print "drawing selection box"
        canvas = self.canvas
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        origx = self.selectionBox[0][0]
        origy = self.selectionBox[0][1]
        if abs(origx-x) > 10 or abs(origy-y) > 10:
            #mouse has moved:
            canvas.delete("selectionBox")
            canvas.create_rectangle(origx, origy, x, y, tags = ("selectionBox"), outline = "red")
            if len(self.selectionBox) == 1:
                self.selectionBox.append((x,y))
            else:
                self.selectionBox[1] = (x, y)


    def endKFSelection(self, event=None):
        # record selected frames
        canvas = self.canvas
        canvas.unbind('<B1-Motion>')
        canvas.unbind('<ButtonRelease-1>')        
        selectedFrames = {}
        canvas.delete('selection')
        if len(self.selectionBox) == 2:
            x = canvas.canvasx(event.x)
            y = canvas.canvasy(event.y)
            origx = self.selectionBox[0][0]
            origy = self.selectionBox[0][1]
            # find all canvas items that are in the selection box: 
            items = canvas.find_overlapping(origx, origy, x, y)
            # select only the ones with tag "keyframe_#####_##"
            for it in items:
                tags = canvas.gettags(it)
                if len(tags) > 1:
                    names = tags[1].split("_")
                    if len(names) == 3 and  names[0] ==  'keyframe':
                        actorName = names[1]
                        if not selectedFrames.has_key(actorName):
                            selectedFrames[actorName] = []
                        ll = (int(names[2]), it)
                        if ll not in selectedFrames[actorName]:
                            selectedFrames[actorName].append(ll)
            # find out if there are frames that belong to any kfset
            if len(selectedFrames):
                selActors = {}
                setid = []
                selectedSetFrames = {}
                for actor in self._director().actors:
                    name = actor.name
                    if selectedFrames.has_key(name):
                        selActors[name] = actor
                        frames = selectedFrames[name]
                        #frames.sort()
                        sframes = []
                        for kf in frames:
                            id = actor.kfSetId.get(kf[0])
                            if id is not None:
                                if not id in setid: setid.append(id)
                                sframes.append(kf[0])
                        if len(setid) > 1:
                            
                            tkMessageBox.showwarning("Scenario warning","Can not select frames that belong to two different sets")
                            self.selectedFrames = {}
                            canvas.delete('selection')
                            canvas.delete("selectionBox")
                            self.updateCopyPasteMenus()
                            return
                        elif len(setid) == 1:
                            if len(sframes):
                                selectedSetFrames[name] = sframes
                if len(setid):
                    # check if we included all of the set frames to the selection
                    kfset = self.kfSets[setid[0]]
                    for item in kfset.setframes:
                        actor = item[0] 
                        if not selectedFrames.has_key(actor.name):
                            selectedFrames[actor.name] = []
                            selActors[actor.name] = actor
                        if not selectedSetFrames.has_key(actor.name):
                            selectedSetFrames[actor.name] = []
                        frames = selectedFrames[actor.name]
                        for kf in item[1:]:
                            if kf not in selectedSetFrames[actor.name]: 
                                id = canvas.find_withtag("keyframe_%s_%d"%(actor.name, kf))
                                frames.append((kf, id[0]))
                                selectedSetFrames[actor.name].append(kf)
                for name, frames in selectedFrames.items():
                    frames.sort()
                    self.markKeyframes(frames, selActors[name])
                self.pasteBuffer = []
                print "selected frames:", selectedFrames
        self.selectedFrames = selectedFrames
        canvas.delete("selectionBox")
        self.updateCopyPasteMenus()


    def markKeyframes(self, selframes, actor, posy=None):
        
        canvas = self.canvas
        name = actor.name
        if posy is None:
            posy = actor._posy
        frames = map(lambda x: x[0], selframes)
        # find intervals containing contiguous in time keyframes:
        # example: sortedKeyFrames  = [5, 12, 20, 28, 35, 40, 55, 65, 70]
        #        selected keyframes = [   12, 20, 28,         55, 65],
        # then intervals = [[12, 20, 28], [55, 65]]
        intervals = actor.findSelectedIntervals(frames)
        for interval in intervals:
            ind1 = frames.index(interval[0])
            it1 = selframes[ind1][1] # the canvas id of the first keyframe of this interval of keyframes.
            x1 = canvas.coords(it1)[0]-2
            y1 = posy-8
            ind2 = frames.index(interval[-1])
            it2 = selframes[ind2][1] # the canvas id of the last keyframe of this interval of keyframes.
            x2 = canvas.coords(it2)[2]+2
            y2 = posy+8
            id = canvas.create_rectangle(x1, y1, x2, y2, tags = ("selection", ), outline = "yellow", fill = "yellow")
            canvas.tag_raise("actor_%s"%name)
            canvas.addtag_withtag("actor_%s"%name, id)
        canvas.tag_bind("selection", "<Button-1>", self.startMoveSelection)
        #canvas.lower("selection")


    def deleteKeyFrames_cb(self, event=None):
        # callback of 'Delete' button from 'Edit' menu (used to delete selected keyframes)
        if not len(self.selectedFrames):
            return
        sf = self.selectedFrames
        allframes = []
        #for ff in sf.values():
        #    allframes.extend(map(lambda x: x[0], ff))
        #if 0 in allframes:
        #    tkMessageBox.showwarning("Scenario warning", "Frame 0 is in the selected set of frames.\nCan not delete selected frames.")
        #    return
        self.selectedFrames = {}            
        self.pasteBuffer = []
        for name, val in sf.items():
            actor = self.getActorByName(name)
            frames = map(lambda x: x[0], val)
            self.deleteKeyFrame(actor, None, frames)
        self.canvas.delete("selection") 
        self.updateCopyPasteMenus()


    def copyKeyFrames_cb(self, event=None):
        # callback of 'Copy' button from 'Edit' menu (used to copy selected keyframes)
        if len(self.selectedFrames):
            self.pasteBuffer = []
            sf = self.selectedFrames
            minf = sf.values()[0][0][0]
            maxf = 0
            for actor in self._director().actors:
                name = actor.name
                if sf.has_key(name):
                    if not actor.recording:
                        tkMessageBox.showwarning("Scenario warning", "Can not copy selected actors: actor %s is not recordable" % name)
                        self.pasteBuffer = []
                        return
                    asf = map(lambda x: x[0], sf[name])
                    if asf[0] < minf: minf = asf[0]
                    if asf[-1] > maxf: maxf = asf[-1]
                    #asf.insert(0, actor)
                    #self.pasteBuffer.append(asf)
                    self.pasteBuffer.append([actor, asf])

            self.pasteBuffer.insert(0, [minf, maxf])
            self.updateCopyPasteMenus()

    
    def postEditMenu_cb(self):
        # Called when the Edit menu button is pressed. Disables/enables paste and insert
        # commands depending on the current time cursor position.
        
        menu = self.menuButtons['Edit'].menu
        
        # location of the time cursor:
        frame = self._director().currentFrame
        insertState = None
        flipState = Tkinter.DISABLED
        # check if we have copied any keyframes
        if not len(self.pasteBuffer):  # no copy
            pasteState = Tkinter.DISABLED
            if len(self.selectedFrames):
               if self.canFlipSelection():
                   flipState = Tkinter.NORMAL
                
        else: # there is a copy
            minf, maxf = self.pasteBuffer[0]
            if frame>= minf and frame <= maxf:
                # time cursor is over the copied keyframes - can't paste
                pasteState = Tkinter.DISABLED
            else:
                # find if the time cursor is placed after last keyframes of the copied
                # actors
                selectedActors = map(lambda x: x[0], self.pasteBuffer[1:])
                maxkf = self._director().getLastFrameWithChange(selectedActors)
                #print "last frame:" , maxkf
                if frame > maxkf: # paste is allowed after the last
                                  # frame of selected actors
                    pasteState = Tkinter.NORMAL
                    insertState = Tkinter.DISABLED
                else:
                    # we can not paste if the time cursor is over a kfset
                    #(exception : only one keyframe is copied)
                    # search the paste area of the selected actors for kfsets
                    overSet = []
                    if sum(map(lambda x: len(x[1]), self.pasteBuffer[1:])) > 1:
                        #number of selected keyframes more than one
                        overSet = self.isTimeCursorOverSet(selectedActors)
                    if len(overSet):
                        pasteState = Tkinter.DISABLED
                    else:
                        # do we have enough room to paste copied keyframes?
                        if self.canPasteSelection(frame, maxkf)[0]: # yes
                            pasteState = Tkinter.NORMAL
                        else: # no
                            pasteState = Tkinter.DISABLED
        if not insertState:
            # check if we can allow frame insertion at the time cursor location
            if self.canInsertFrames(frame):
                insertState = Tkinter.NORMAL
            else:
                insertState=Tkinter.DISABLED
        # update the Paste/Insert menu entries
        menu.entryconfig("Insert frames", state=insertState)
        menu.entryconfig("Paste", state=pasteState)
        menu.entryconfig("Linked Paste", state=pasteState)
        menu.entryconfig("Flip Selection", state=flipState)

            
    def canPasteSelection(self, atFrame, maxkf = None):
        # check if we have enough room to the right of specified frame for pasting copied selection  
        selectedActors = map(lambda x: x[0], self.pasteBuffer[1:])
        minf, maxf = self.pasteBuffer[0]
        if maxkf is None:
            maxkf = self._director().getLastFrameWithChange(selectedActors)
        if atFrame > maxkf:
            return (True, None)
        closestf = maxkf
        for actor in selectedActors:
            interval, k1, k2, vg = actor.getInterval(atFrame)
            if k1 == atFrame:
                return (False, None)
            if k2 is not None:
                closestf = min(k2, closestf)
        nf = maxf -minf + 1
        diff = closestf - (atFrame + nf)
        if diff > 0:
            return (True, diff)
        else: return (False, diff)

    def canInsertFrames(self, atFrame):
        # check if we can allow frame insertion at the time cursor location.
        # we need to search through the range of all actors for intersecting
        # kfsets: 
        overSet = self.isTimeCursorOverSet()
        #print "time cursor is over kfset:", overSet
        # if there are any sets, check if we can move that set when inserting frames(we will move the kfset if less then 50% it's 'width' is to the left of the time cursor)   
        for id in overSet:
            t1, t2 = self.kfSets[id].bbox
            if t1 == 0: # at least one of the kfset's keyframes is 0 - we can't move it
                        # or insert any frames before it  
                return False
            if t1 + (t2-t1)/2 < atFrame :
                # time cursor is over right half of the set  - can't move it;
                # frame insertion is not allowed
                #print "set id: %d" % id, t1, t2 , atFrame, "cant move set"
                return False
        return True

    def isTimeCursorOverSet(self, actors=None):
        # find all kfsets that are under the time cursor. If actors are specified ,check only within the range
        # occupied by the actors
        cursorf = self._director().currentFrame
        allActors = False
        if not actors:
            allActors = True
            actors = self._director().actors
        sets = []
        if  len(self.kfSets):
            for kfset in self.kfSets.values():
                if kfset.isFrameInSet(cursorf):# time cursor is over the set
                    if allActors:
                        sets.append(kfset.Id)
                    else:
                        # check if any of specified actors are in this set:
                        for actor in actors:
                            if actor.name in kfset.setActors:
                                sets.append(kfset.Id)
                                break
        return sets
        

    def pasteKeyFrames_cb(self, event=None):
        # callback of 'Paste' button from 'Edit' menu . Paste copies of selected frames
        # at the location of the time cursor. It should be located after last keyframe of all actors.
        #pasteBuffer = [["copy", minselectedframe, maxselectedframe],
            #               [actor1, [frame1,...frameN] ] ]
        if not len(self.pasteBuffer): return
        cursorf = self._director().currentFrame
        if not self.canPasteSelection(cursorf)[0]:
            return
        self.paste(cursorf, "copy")


    def pasteLinkKeyFrames_cb(self, event=None):
        if not len(self.pasteBuffer): return
        cursorf = self._director().currentFrame
        if not self.canPasteSelection(cursorf)[0]:
            return
        self.paste(cursorf, "link")

        
    def paste(self, atFrame, copytype):
        #
        minf, maxf = self.pasteBuffer[0]
        #for entry in self.pasteBuffer[1:]:
        newFrames = []
        maxkf = 0
        lenframes = 0
        for entry in self.pasteBuffer[1:]:
            actor = entry[0]
            selectedFrames = entry[1]
            lenframes += len(selectedFrames)
            if len(selectedFrames) > 1:
                kfIntervals = selectedFrames[1:]
            else:
                 kfIntervals = []
            sf = []
            for kf in selectedFrames: # create new frames that are copies of selected ones
                newf = kf - minf + atFrame
                vgIndex = None
                if kf in  kfIntervals:
                    # we need to copy the value generator of the interval before kf
                    vgIndex = actor.getInterval(kf)[0] - 1
                if copytype == "copy":
                    value = copy(actor.keyframeValues[actor.keyframes[kf]])
                    actor.setKeyframe(newf, value = value, vgIndex = vgIndex)

                elif copytype == "link":
                    # create linked copies of the selected keyframes,
                    # ie. the keyframes will share the same value indices
                    vind = actor.keyframes[kf]
                    actor.setKeyframe(newf, valueIndex = vind, vgIndex = vgIndex)
                    if len(actor.linkedKeyFrames[vind]):
                        if newf not in actor.linkedKeyFrames[vind]:
                            actor.linkedKeyFrames[vind].append(newf)
                    else:
                        actor.linkedKeyFrames[vind] = [kf, newf]
                sf.append(newf) 
            posy = actor._posy
            self.deleteActor(actor)
            self.selectedFrames[actor.name] = map(lambda x: (x,), sf)
            
            self.drawActor(actor, posy)
            maxkf = max(maxkf, actor.getLastFrame())
            if copytype  == "link":
                newFrames.append([actor, sf])
        # add time lines if necessary        
        if   maxkf > self._director().getLastFrame():
            #print "setting Duration to frame ", frame
            self.setDuration( maxkf + 5)
        if copytype == "link" and lenframes > 1:
            if not len(self.kfSets): id = 0
            else:
                id = max(self.kfSets.keys()) + 1
            self.kfSets[id] = KFSet(newFrames, id, self._director() )
            # find out if we need to create a new kfset for the current selection.
            # Since each keyframe can belong to only one kfset:
            kf = selectedFrames[0]
            if not actor.kfSetId.has_key(kf):
                self.kfSets[id+1] = KFSet(self.pasteBuffer[1:], id+1, self._director() )


    def unlinkKFSet(self, setid):
        kfsets = []
        curx = self.xoff+self.timeBegin
        for item in self.kfSets[setid].setframes:
            actor = item[0]
            frames = item[1:]
            lsetid = actor.unlinkKeyFrames(frames)
            if lsetid:
                if lsetid not in kfsets:
                    kfsets.append(lsetid)
            posy = actor._posy
            self.deleteActorKeyFrames(actor)
            self.drawKeyFrames(actor, curx, posy)
        del(self.kfSets[setid])
        if len(kfsets) > 1:
            print "WARNING:  keyframes of set %d are linked with keyframes of sets:" %(setid,), kfsets
        elif len(kfsets) == 1:
            del(self.kfSets[kfsets[0]] )
        


    def insertFrames_cb(self, event=None):
        # callback of 'Insert Frames' entry under Edit menu
        # pops up an input form for the user to specify the number of frames
        # to be inserted at the current location of the time cursor
        
        frame = self._director().currentFrame
        overSet = self.isTimeCursorOverSet()
        # if the time cursor is over a set(s), check if we can move that set when inserting frames
        for id in overSet:
            t1, t2 = self.kfSets[id].bbox
            if t1 == 0:
                print "WARNING:cannot insert keyframes before keyframe 0 of keyframeset %d (minf = %d, maxf = %d)" % (id, t1, t2), self.kfSets[id].setActors
            if t1 + (t2-t1)/2 < frame :
                # time cursor is over right half of the set  - can't move it;
                # frame insertion is not allowed
                print "WARNING: cannot insert keyframes at current time cursor position %d, keyframeSet (%d) is in the way (minf = %d, maxf = %d)" % (cursorf, id, t1, t2), self.kfSets[id].setActors
                return
        idf = InputFormDescr(title='Insert Frames')
        idf.append({'widgetType':ThumbWheel, 'name':'nframes',
                    'tooltip': """number of frames to insert at current time cursor position""",
                    'gridcfg':{'sticky':'w','column':0,  'columnspan':2},
                    'wcfg':{'oneTurn':50, 'min':0.0, 'lockMin':True,
                            'type':'int', 'precision':1,
                            'wheelPad':1,'width':90,'height':15,
                            'labCfg':{'text':'Number of frames:'},
                            }
                    })
        form=InputForm(self.root, None, idf, blocking = 1)
        res = form.go()
        nframes = res.get('nframes')
        if nframes:
            self.insertAll(nframes, frame, overSet)

            
    def insertAll(self, nframes, atFrame, cursorOverSets):
        # insert nframes at specified frame, i.e move all keyframes (that are to the right of 'atFrame')
        # to atFrame+nframes. If cursorOverSets are specified, we need to move all keyframes that belong
        # to these sets
        
        director = self._director()
        actors = director.actors  #map(lambda x: x[0], self.pasteBuffer[1:])

        kfsets_ = {}
        setActors = []
        # first, shift keyframes of all actors that belong to cursorOverSets:
        for setid in cursorOverSets:
            kfset = self.kfSets[setid]
            startf = kfset.bbox[0]
            for item in kfset.setframes:
                actor = item[0]
                kfsets_.update(self.shiftKeyFrames(actor, startf, nframes))
                setActors.append(actor.name)
        # shift keyframes of the rest of the actors :
        for actor in actors:
            if actor.visible:
                if actor.name not in setActors:
                    kfsets_.update(self.shiftKeyFrames(actor, atFrame, nframes)) 
        # check if the pasteBuffer frames are in the shift region
        if len(self.pasteBuffer):
            minf, maxf = self.pasteBuffer[0]
            if minf >= atFrame:
                # We will have to update the pasteBuffer to contain new frame numbers
                self.pasteBuffer[0][0] = minf + nframes
                self.pasteBuffer[0][1] = maxf + nframes
                for entry in self.pasteBuffer[1:]:
                    for i in range(len(entry[1])):
                        entry[1][i] += nframes
                #print "updated pasteBuffer:", self.pasteBuffer
        if len(kfsets_):
            for kfset in kfsets_.values():
                kfset.updateFrames(nframes)


    def shiftKeyFrames(self, actor, startFrame, nframes):
        #shift all actors frames, that are greater than current time cursor frame, right.
        kfsets_ = {}
        pbf = None
        sf = actor.keyframes._sortedKeys[:]
        if sf[-1]+nframes > self._director().getLastFrame():
            self.setDuration(sf[-1]+nframes + 10)
        sf.reverse() # start moving frames from the last actor's frame
        
        redrawActor = False
        for kframe in sf:
            if kframe >= startFrame:
                valind = actor.keyframes[kframe]
                del(actor.keyframes[kframe])
                newframe = kframe + nframes
                #print "shifting frame %d to %d" % (kframe, newframe), actor.name
                actor.keyframes[newframe] = valind
                # update linkedKeyFrames
                for i, ff in enumerate(actor.linkedKeyFrames[valind]):
                    if ff == kframe:
                        actor.linkedKeyFrames[valind][i] = newframe
                # check if the kframe belongs to any kfSets
                if actor.kfSetId.has_key(kframe):
                    id = actor.kfSetId[kframe]
                    del(actor.kfSetId[kframe])
                    actor.kfSetId[newframe] = id
                    if not kfsets_.has_key(id):
                        kfsets_[id] = self.kfSets[id]
                redrawActor = True
        # check if we moved any selected frames
        if self.selectedFrames.has_key(actor.name):
            selFrames = self.selectedFrames[actor.name]
            for i, kframe in enumerate(selFrames):
                if kframe[0] >= startFrame:
                    selFrames[i] = (kframe[0]+nframes, )
        if redrawActor:
            posy = actor._posy
            self.deleteActor(actor)
            self.drawActor(actor, posy)           
        return kfsets_

    def updateCopyPasteMenus(self):
        """ turns on/off menu entries and menu buttons."""
        
        menu = self.menuButtons['Edit'].menu
       
        if not len(self.selectedFrames):
            menu.entryconfig("Copy", state=Tkinter.DISABLED)
            menu.entryconfig("Delete", state=Tkinter.DISABLED)
        else:
            menu.entryconfig("Copy", state=Tkinter.NORMAL)
            if len(self.kfSets):
                # check if we selected keframes that belong to a kfset:
                nframes = 0
                nsetframes = 0
                for name, frames in self.selectedFrames.items():
                    actor = self.getActorByName(name)
                    for kf in frames:
                        if actor.kfSetId.get(kf[0]):
                            nsetframes += 1
                        else: nframes += 1
                    if nframes and nsetframes:
                        menu.entryconfig("Copy", state=Tkinter.DISABLED)
                        break
            menu.entryconfig("Delete", state=Tkinter.NORMAL)
        if not len(self.pasteBuffer) :
            menu.entryconfig("Paste", state=Tkinter.DISABLED)
            menu.entryconfig("Linked Paste", state=Tkinter.DISABLED)


    def startMoveSelection(self, event=None):
        # callback of <Button-1> press on the yellow selection area
        # Find out how far to the left and right (in number of frames) the current selection
        # can be moved.
        self.stopSelection = True
        director = self._director()
        canvas = self.canvas
        canvas.bind("<ButtonRelease-1>", self.moveSelectionEnd)
        # minf and maxf are the smallest and largest frames in the selection 
        lastf = minf = director.getLastFrame()
        maxf = 0
        lframes = None # number of frames we can move the selection to the left 
        rframes = None # ------------------------------------------------ right

        for actor in director.actors:
            if self.selectedFrames.has_key(actor.name):
                frames = map (lambda x: x[0], self.selectedFrames[actor.name])
                f1 = frames[0]
                f2 = frames[-1]
                # we will not move the selection if it contains the first actors frame ( kf = 0 ):
                #if f1 == 0:
                #    self.sboundaries = [0,0,0,0,0]
                #    return
                minf = min(minf, f1)
                maxf = max(maxf, f2)
                lf, rf = actor.getDistance(frames)
                if lframes is None:
                    lframes = lf
                else:
                    lframes = min(lf, lframes)
                if rframes is None:
                    rframes = rf
                else:
                    rframes = min(rf, rframes)
        
        self.lastx = canvas.canvasx(event.x)
        if rframes is not None:
            self.sboundaries = [minf, maxf, minf-lframes, maxf+rframes, minf]
        else:
            self.sboundaries = [minf, maxf, minf-lframes, None, minf]
        canvas.bind("<Button1-Motion>", self.moveSelection)
        

    def moveSelection(self, event=None):
        # callback of <Button1-Motion> on the yellow selection area
        canvas = self.canvas
        x = canvas.canvasx(event.x)
        diff = x - self.lastx
        nframes = round(diff/self.scale) # distance moved (in number of keyframes)  
        minf, maxf, lframe, rframe, minforig = self.sboundaries
        # the selection bounding box should not go over lframe and rframe 
        if nframes < 0:
            if minf + nframes < lframe + 1:
                nframes = -(minf-lframe - 1)
        elif nframes > 0:
            if rframe is not None:
                if maxf + nframes > rframe -1:
                    nframes = rframe - maxf -1
        if not abs(nframes): return
        diffx = self.scale * nframes
        # move canvas items representing selected frames
        for name, frames in self.selectedFrames.items():
            for f, id in frames:
                canvas.move(id, diffx, 0)
        canvas.move ("selection", diffx, 0)
        self.lastx = self.lastx+diffx
        maxf = maxf + nframes
        self.sboundaries[0] = minf+nframes
        self.sboundaries[1] = maxf
        # add time lines if necessary
        if maxf > self._director().getLastFrame():
            self.setDuration(maxf + 10)
        

    def moveSelectionEnd(self, event=None):
        
        self.stopSelection = False
        canvas = self.canvas
        canvas.unbind("<Button1-Motion>")
        canvas.unbind("<ButtonRelease-1>")
        minf, maxf, lframe, rframe, minforig = self.sboundaries
        nframes = int(minf - minforig)
        if nframes == 0: return #selected frames did not move
        kfsets_ = {}
        director = self._director()
        for actor in director.actors:
            name = actor.name
            if self.selectedFrames.has_key(name):
                selframes = self.selectedFrames[name]
                # update actors keyframes
                kf = map(lambda x: x[0], selframes)
                if nframes > 0:
                    # selection moved to the right.We will update keyframe numbers starting
                    # at the end of keyframe list (in reverse order), so that we do not
                    # overwrite any existing frames
                    kf.reverse()  
                    #print "actor: %s," % (name, ), kf 
                for kframe in kf:
                    valind = actor.keyframes[kframe]
                    del(actor.keyframes[kframe])
                    newframe = kframe+nframes
                    actor.keyframes[newframe] = valind
                    # update linekedKeyFrames
                    for i, ff in enumerate(actor.linkedKeyFrames[valind]):
                        if ff == kframe:
                            actor.linkedKeyFrames[valind][i] = newframe
                    # check if the kframe belongs to any kfSets
                    if actor.kfSetId.has_key(kframe):
                        id = actor.kfSetId[kframe]
                        del(actor.kfSetId[kframe])
                        actor.kfSetId[newframe] = id
                        if not kfsets_.has_key(id):
                            kfsets_[id] = self.kfSets[id]
                # update selectedFrames
                for j in range(len(selframes)):
                    selframes[j]= (selframes[j][0]+ nframes, )
                posy = actor._posy
                self.deleteActor(actor)
                self.drawActor(actor, posy)
        if len(kfsets_):
            for kfset in kfsets_.values():
                kfset.updateFrames(nframes)
        self.pasteBuffer = []
        self.updateCopyPasteMenus()


    def canFlipSelection(self):

        # do not flip the selected set of frames if it containes linked frames (Going to FIX this)
        
        director = self._director()
        allsf = self.selectedFrames
        for actor in director.actors:
            name = actor.name
            if allsf.has_key(name):
                frames = allsf[name]
                #frames.sort()
                for kf in frames:
                    if actor.kfSetId.get(kf[0]) is not None:
                        return False
        return True


    def flipSelection_cb(self, event=None):
        # flips over the selected set of keyframes. Currently works only on "simple"
        # selection (there is no linked keyframes)

        director = self._director()
        allsf = self.selectedFrames
        # find min (leftmost) and max (rightmost) keyframes of the selection:
        minkf = min(map(lambda x: x[0][0], allsf.values()))
        maxkf = max(map(lambda x: x[-1][0], allsf.values()))

        for actorname, sf  in self.selectedFrames.items():
            actor = self.getActorByName(actorname)
            sortedkf = actor.keyframes._sortedKeys[:]
            kf = actor.keyframes
            ff1 = sf[0][0]
            ff2 = sf[-1][0]
            # indices of the leftmost and rightmost selected keyframes of this actor: 
            i1 = sortedkf.index(ff1)
            i2 = sortedkf.index(ff2)
            
            valind = kf.pop(ff2)
            d = maxkf - ff2
            ff1 = minkf + d
            # new, flipped over keyframes:
            kfnew = {ff1:valind}
            #print kfnew

            values = actor.keyframeValues
            vg = actor.valueGenerators
            i = i2-1
            j = i1
            # flip over the keyframes and vg-intervals (starting with the rightmost ones)
            while i >= i1:
                d = ff2 - sortedkf[i]
                ff2 = sortedkf[i]
                valind = kf.pop(ff2)
                kfnew[ff1 + d] = valind
                g = vg.pop(i2-1)
                g.configure(firstVal=values[kfnew[ff1]], lastVal=values[valind])
                vg.insert(j, g)
                ff1 = ff1 + d                
                print i, kfnew
                i = i-1
                j = j+1

            #update actors keyframes with the flipped ones:
            kf.update(kfnew)
            sortedkf = kf._sortedKeys
            # reconfigure the value generator of the interval before the first selected (flipped)
            # keyframe:
            vg[i1-1].configure(lastVal = values[kf[sortedkf[i1]]] )

            # reconfigure the value generator of the interval after the last selected (flipped)
            # keyframe:
            vg[i2].configure(firstVal = values[kf[sortedkf[i2]]] )

            selframes = []
            for i in range(i1, i2+1):
                selframes.append((sortedkf[i],))
            self.selectedFrames[actorname] = selframes    
            posy = actor._posy
            self.deleteActor(actor)
            self.drawActor(actor, posy)

        

    def startTimeIntSelection(self, event=None):
        # Callback of the middle mouse button. Used for creating annotations for a time interval
        
        #find out what has been picked
        canvas = self.canvas
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        self.selectionBox = [(x, y),]
        canvas.bind('<B2-Motion>', self.markTimeInterval)
        canvas.bind('<ButtonRelease-2>', self.endTimeIntSelection)


    def markTimeInterval(self, event=None):
        # draws blue  box to mark time interval
        canvas = self.canvas

        origx = self.selectionBox[0][0]
        origy = self.selectionBox[0][1]
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        if abs(origx-x) > 10 or abs(origy-y) > 10:
            #mouse has moved:
            canvas.delete("markInterval")
            canvas.create_rectangle(origx, origy, x, origy+14, tags=("markInterval", ), outline = "blue")
            if len(self.selectionBox) == 1:
                self.selectionBox.append((x,y))
            else:
                self.selectionBox[1] = (x, y)


    def endTimeIntSelection(self, event= None):
        canvas = self.canvas
        canvas.unbind('<B2-Motion>')
        canvas.unbind('<ButtonRelease-2>')
        canvas.delete("markInterval")
        if len(self.selectionBox) == 2:
            x = canvas.canvasx(event.x)
            #y = canvas.canvasy(event.y)
            origx = self.selectionBox[0][0]
            origy = self.selectionBox[0][1]
            
            textmark=TimeIntervalMarker(self._director(), self.canvas,
                                        [origx, origy, x])
            id = textmark.id
            self.timeIntervalLabels[id] = textmark
            

    def deleteTimeIntervalMark(self, id):
        del(self.timeIntervalLabels[id])


    def createHelpText(self):
        self.helpTxt = helpTxt = []
        
        helpTxt.append(('Record keyframe',
                       """Left-click the time cursor (green vertical line) and\ndrag it to a new position. Modify the value\nof actor(s) selected for recording and:\n   - click the Record button (new keyframe will be\n     recorded for all actors at the time cursor location), or\n   - right-click on an actor and select Record Keyframe\n     from the pull-down menu(a keyframe will be recorded\n     only for the selected actor)."""))
        
        helpTxt.append(('Move keyframe',
                       """Left-click a green keyframe oval and drag it to\na new location."""))
        
        helpTxt.append(('Select keyframes for copying',
                       """Left-click on the canvas (near a keyframe) and drag.\nThis wiil draw a red box around selected frames.\nThe selected keyframes are highlighted in yellow after the\nleft button is released.\nClicking and dragging the yellow area will move the selected\nblock of frames"""))
        helpTxt.append(('Clear selection',
                       """Make a new selection or left-click on the widget canvas.""" ))
        
        helpTxt.append(('Copy  keyframes',
                       """Select keyframe(s). Choose Copy menu entry from \nthe Edit menu. Move time cursor to a new position,\nthen select 'Paste' or 'Linked Paste' from the Edit menu.\nAs a result of a simple 'Paste' the selected keyframes\nare hard-copied to the new time locations along with\ntheir associated values. In the 'Linked Paste' case,\nthe new keyframes will be logically linked with\nthe original ones, i.e., any change made to the\noriginal keyframe(by moving the keyframe in time\nor modifying the actor's value associated with it) will\nbe automatically reflected in the copy(and vice versa).\nThe 'Linked Paste' operation places the original\nand linked keyframes in special blocks (sets),\nwhich enables the user to operate on these\nkeyframes as a whole. For example, left-clicking\non a single frame in such a set will highlight all\nkeyframes belonging to this set.\n Right-clicking will open a menu.\nThe menu will allow the user to delete this single\nkeyframe, select the set (for moving, copying,\ndeleting) and to unlink the set.\nA new single keyframe can be inserted into a set\nof frames by recording or copying."""))

        helpTxt.append(('Insert  frames',
                       """The user can insert frames at the time cursor (vertical green\nline) location by selecting 'Insert frames' from the Edit menu\nThis will bring up an input form for specifying the number\nof frames to be inserted.\nNOTE: the insertion of frames is not allowed inside a linked\nkeyframe set. If the time cursor is placed at the leftmost\npart of a set,the set will be moved the specified amount\nof frames to the right."""))
        
        helpTxt.append(('Display/undisplay function',
                       """Middle-clicking on an actor's line displays/hides\nthe function.\nNOTE: function drawing is not available for some actors."""))
        
        helpTxt.append(('Delete keyframe',
                       """Right-click the keyframe oval to open its pull-down menu,\nchoose Delete keyframe"""))
        
        helpTxt.append(('Delete actor',
                       """Right-click the actor line to open its pull-down menu,\nchoose Delete actor."""))
               
        helpTxt.append(('Select actor for playing', """Clicking the green dot located to the left of the line representing\nan actor, swiches its play mode on/off."""))
        helpTxt.append(('Select actor for recording', """Clicking the red dot located to the left of the line representing\n an actor, swiches its record mode on/off."""))

        helpTxt.append(('Change order of displayed actors', """Use up-down arrows located at the left of the line representing\nan actor to move it one position up or down.\nThe user can also left-click on the actor's line and drag\nthe highlighted blue box up or down to a new position."""))

        helpTxt.append(('Flip selected set of keyframes', """Select keyframes. Choose 'Flip Selection' from the Edit menu.\nNOTE: this feature currently works only on selected frames that \nare not linked to any other frames (via 'Linked Paste'\noperation).""" ))
        
        helpTxt.append(('Auto track feature', """This feature is used for monitoring changes in the application.\nNew actors are automatically created when such a change occurs. """))

    def displayHelpText_cb(self):
        root = Tkinter.Toplevel()
        frame = Tkinter.Frame(root, background='white',borderwidth=2, relief='sunken', padx=5, pady=5)
        fframe = Tkinter.Frame(frame, bd=2, relief='groove',)
        
        frame.pack(expand=1, fill='both')
        fframe.pack(expand=1, fill='both')
        st = None
        slb = None
        items =  map(lambda x: x[0], self.helpTxt)    
        def displayDocumentation_cb():
            selection = slb.curselection()
            if len(selection):
                ind = int(selection[0])
                st.settext(self.helpTxt[ind][1])
               
        slb = kbScrolledListBox(fframe, label_text="How to...",
                                items = items, listbox_exportselection = 0,
                                labelpos='nw',
                                selectioncommand = displayDocumentation_cb,
                                usehullsize=1, hull_width = 150, hull_height = 150)

        slb.pack(side='left', expand=1, fill='both')
        
        st = ScrolledText(fframe, borderframe=1, labelpos='nw',
                          label_text='Documentation',usehullsize=1,
                          hull_width = 350, hull_height = 150, text_wrap = 'none')
        st.pack(side = 'left', expand=1, fill='both')



    def printInfo(self, actorObject = None, withcheck = True):
        # this is only used for debugging ...
        # actorObject parameter should be either Actor class instance,
        # actor index (1...N), or actor name
        
        actor = None
        print "kfSets:", self.kfSets.keys()
        director = self._director()
        if actorObject is not None:
            from scenario.actor import Actor
            if isinstance(actorObject, int):
                if actorObject == 0: actorObject = 1
                i = 0
                for ar in director.actors:
                   if ar.visible:
                      i = i+1 
                      if i == actorObject:
                          actor = ar
                          break
                if not actor:
                    print "No actor found with index %d" % actorObject
                    return
            elif isinstance(actorObject, str):
                for ar in director.actors:
                    if actorObject == ar.name:
                        actor = ar
                        break
                if not actor:
                    print "No actor %s found " % actorObject
                    return
            elif isinstance(actorObject, Actor):
                actor = actorObject
            else:
                print "actorObject parameter should be either Actor class instance, actor index (1...N), or actor name"
                return
        if actor:
            actors = [actor]
        else:
            actors = director.actors
        setIds = []
        for actor in actors:
            if not actor.visible: continue
            print "-------------------"
            print "actor name: ", actor.name
            print "kfSetId:", actor.kfSetId
            print "key frames: ", actor.keyframes._sortedKeys
            print "linkedKeyFrames:", actor.linkedKeyFrames
            print "linkedVG:", actor.linkedVG
            if withcheck:
                print "Checking actor %s valgens..."% actor.name
                if len(actor.linkedVG) != len(actor.valueGenerators):
                    print " len(actor.linkedVG) %d != len(actor.valueGenerators) %d:" %  (len(actor.linkedVG), len(actor.valueGenerators))
                lvg = {}
                for i, vg in enumerate(actor.valueGenerators):
                    if not lvg.has_key(i): lvg[i] = []
                    for j, vvg in enumerate(actor.valueGenerators):
                        if i != j:
                            if vg == vvg:
                                lvg[i].append(j)
                for ind in lvg.keys():
                    actor.linkedVG[ind].sort()
                    if actor.linkedVG[ind] != lvg[ind]:
                        print "...expected linked vgens for interval %d : %s, got %s " % (ind, lvg[ind], actor.linkedVG[ind])
                print "Checking kfSetId..."
                kfsets = {}
                for kf in actor.kfSetId.keys():
                    id = actor.kfSetId[kf]

                    if not kfsets.has_key(id): kfsets[id] = []
                    kfsets[id].append(kf)
                if len(kfsets):
                    for id in kfsets.keys():
                        if not id in setIds: setIds.append(id)
                        if not self.kfSets.has_key(id):
                            print "found %d setId for actor %s. It is not in director.gui.kfSets" % (id, actor.name)
                        else:
                            kfsets[id].sort()
                            actorInSet = False
                            for i, item in enumerate(self.kfSets[id].setframes):
                                if item[0].name == actor.name:
                                   actorInSet = True
                                   if kfsets[id]!= item[1:]:
                                       print "actors frames in set %d : %s, gui.kfSets[%d][%s] = %s" %(id,kfsets[id], actor.name, item[1:] )
                                   break
                            if not actorInSet:
                                print "did not find actor %s in kfSet %d" %(actor.name, id)
                print "Checking linkedKeyFrames ..."
                for item in actor.linkedKeyFrames:
                    sid = [] 
                    for kf in item:
                        if not actor.kfSetId.has_key(kf):
                            print "keyframe %d is in linkedKeyFrames %s , but is not in kfSetId" % (kf, item)
                        else:
                            id = actor.kfSetId[kf]
                            if not id in sid:
                                sid.append(id)
                    if len(sid)!= len(item):
                        print "the linked keyframes %s should be in different sets, they are found in sets: %s" % (item, sid)
        if withcheck:
            print "-------------------"
            print "after checking , allsets: ", setIds


                
if __name__=='__main__':
    from scenario.director import Director
    d = Director()
    dg = DirectorGUI(d)
    from actor import CustomActor

    from datatypes import FloatType
    from interpolators import FloatScalarInterpolator

    class foo:

        def __init__(self):
            self.a= 2.0
            
        def getVal(self):
            return self.a

        def setVal(self, val):
            print "setting val to:", val
            self.a = float(val)

    f = foo()

    # create an actor
    # from DejaVu.scenarioInterface.actor import RedrawActor
    # actor = Actor('test', f, 0.5, FloatType, FloatScalarInterpolator)
    actor = CustomActor('test', f, 0.5, FloatType, FloatScalarInterpolator,
                        setFunction=lambda x, y: x.object.setVal(y), getFunction=f.getVal)
    
    actor.setKeyframe( 20, 10.5)
    actor.recording = True
    actor.playing = True
    #actor = RedrawActor(f)
    #actor.setKeyframe(1000,0)
    d.addActor(actor)
