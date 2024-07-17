from NetworkEditor.macros import MacroNode
from NetworkEditor.widgets import NEDial, NEThumbWheel

import Pmw, Tkinter
from mglutil.gui.BasicWidgets.Tk.TreeWidget.tree import TreeView
from scenario.objectAnimator import ObjectAnimator, ObjectAnimatorDescriptor
from scenario.interpolators import Interpolator, ScalarLinearInterpolator
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from scenario.animator import Animator
from mglutil.util.callback import CallBackFunction


class EditorGUI:

    def __init__(self, netAnim, objectAnimatorDescr, master=None):

        self.netAnim = netAnim
        self.ownsMaster = False
        self.objectAnimatorDescr = objectAnimatorDescr
        
        if master is None:
            master = Tkinter.Toplevel()
            master.title('interpolator')
            self.ownsMaster = True
            master.protocol('WM_DELETE_WINDOW', lambda: 1)

        self.master = master
        self.buildGUI()
        self.show()
        

    def buildGUI(self, ):

        self.editorMaster = Pmw.ScrolledFrame(self.master,
             borderframe=1, horizscrollbar_width=7, vscrollmode='none',
             frame_relief='flat',
             frame_borderwidth=0, horizflex='fixed',
             vertflex='elastic')

        m = self.editorFrame = Tkinter.Frame(self.editorMaster.interior(),
                                              relief='sunken', width=300)

        self.editorLabel = Tkinter.Label(m, text='Scalar Linear Interpolator')
        self.editorLabel.pack()

        # create Frame range group
        w = Pmw.Group(m, tag_text='Frame')
        w.pack(padx = 6, pady = 6) #,fill = 'both', expand = 1, )

        
        fromframe = ThumbWheel(master=w.interior(), width=100, height=30,
                               labCfg={'side':'top', 'text':'From'})
        fromframe.pack(padx = 2, pady=2)
        val=self.objectAnimatorDescr.namedArgs['startFrame']
        if val is not None:
            fromframe.set(val)
        cb = CallBackFunction( self.updateObjAnimDescr, 'fromframe', fromframe)
        fromframe.callbacks.SetCallback(cb)
        
        toframe = ThumbWheel(master=w.interior(), width=100, height=30,
                             labCfg={'side':'top', 'text':'To'})
        toframe.pack(padx=2, pady=2)
        val=self.objectAnimatorDescr.namedArgs['endFrame']
        if val is not None:
            toframe.set(val)
        cb = CallBackFunction( self.updateObjAnimDescr, 'toframe', toframe)
        toframe.callbacks.SetCallback(cb)

        # FIXME we need a checkbutton for value==None for each of these
        # create value range group
        w = Pmw.Group(m, tag_text='Values')
        w.pack(padx = 6, pady = 6)#,fill = 'both', expand = 1)
        fromval = ThumbWheel(master=w.interior(), width=100, height=30,
                           labCfg={'side':'top', 'text':'From'})
        fromval.pack(padx = 2, pady=2)
        interp = self.objectAnimatorDescr.namedArgs['interpolator']
        fromval.set(interp.startValue)
        cb = CallBackFunction( self.updateObjAnimDescr, 'fromvalue', fromval)
        fromval.callbacks.SetCallback(cb)

        toval = ThumbWheel(master=w.interior(), width=100, height=30,
                           labCfg={'side':'top', 'text':'To'})
        toval.pack(padx=2, pady=2)
        toval.set(interp.endValue)
        cb = CallBackFunction( self.updateObjAnimDescr, 'tovalue', toval)
        toval.callbacks.SetCallback(cb)

        self.editorFrame.pack(expand=1, fill='both')

        
    def updateObjAnimDescr(self, what, widget, event=None):
        # what can be fromframe, toframe, fromvalue or tovalue (string
        # widget is the sthumbwheel widget from the editor panel from
        # which we get the value
        if what=='fromframe':
            self.objectAnimatorDescr.namedArgs['startFrame'] = widget.get()
        elif what=='toframe':
            val = widget.get()
            self.objectAnimatorDescr.namedArgs['endFrame'] = val
            animator = self.objectAnimatorDescr.animator()
            animator.updateEndFrame(val)
            self.netAnim.lastFrameLabelVar.set(
                'Last Frame: %g'%animator.getLastFrame())
        elif what=='fromvalue':
            interp = self.objectAnimatorDescr.namedArgs['interpolator']
            interp.configure(startValue=widget.get())
        elif what=='tovalue':
            interp = self.objectAnimatorDescr.namedArgs['interpolator']
            interp.configure(endValue=widget.get()) 


    def show(self, packOpts=None):
        if packOpts is None:
            packOpts = {'expand':1, 'fill':'both'}
        apply( self.editorMaster.pack, (), packOpts )


    def hide(self):
        self.editorMaster.forget()


    def destroy(self):
        if self.ownsMaster:
            self.master.destroy()
        else:
            self.editorMaster.destroy()



class NetworkAnimatorGui:

    def __init__(self, name='Widget Animator', master=None):

        self.name = name
        self.ownsMaster = False
        self.animator = Animator()
        self.currentEditor = None
        
        if master is None:
            master = Tkinter.Toplevel()
            master.title(self.name)
            self.ownsMaster = True
            master.protocol('WM_DELETE_WINDOW', lambda: 1)

        self.master = master
        self.widgetTree = None 
        self.buildGUI()
        self.editorGUI = {} # key: widget from the network (e.g. Dial),
                            # value: EditorGUI instance


    def buildGUI(self):
        ## build menu
        self.menuBar = Tkinter.Frame(self.master, relief='raised',
                                     borderwidth=2)
        self.menuBar.pack(side='top',fill='x')

        menuB = Tkinter.Menubutton(self.menuBar, text='File', underline=0)
        menuB.pack(side=Tkinter.LEFT, padx="1m")
        menuB.menu = Tkinter.Menu(menuB)
        menuB['menu'] = menuB.menu
        
        menuB.menu.add_command(label="Read", #command=self.read,
                               state=Tkinter.DISABLED)
        menuB.menu.add_command(label="Write", #command=self.write,
                               state=Tkinter.DISABLED)
        
        menuB = Tkinter.Menubutton(self.menuBar, text='interpolators',
                                   underline=0)
        menuB.pack(side=Tkinter.LEFT, padx="1m")
        menuB.menu = Tkinter.Menu(menuB)
        menuB['menu'] = menuB.menu
        
        menuB.menu.add_command(label="None", command=self.setNoInterp_cb,
                               underline=0 )
        menuB.menu.add_command(label="Linear", command=self.setLinearInterp_cb,
                               underline=0 )
        
        self.buttonBar = Tkinter.Frame(self.master, relief='raised',
                                       borderwidth=2)
        self.buttonBar.pack(side='top',fill='x')
        button = Tkinter.Button(self.buttonBar, text='Play', command=self.run)
        button.pack(side='left')

        self.lastFrameLabelVar = Tkinter.StringVar()
        self.lastFrameLabelVar.set('Last Frame: %g'%self.animator.getLastFrame())
        label = Tkinter.Label(self.buttonBar, 
                              textvariable=self.lastFrameLabelVar)
        label.pack(side='left')

        self.currentFrameLabelVar = Tkinter.StringVar()
        self.currentFrameLabelVar.set('cur. Frame: 0')
        label = Tkinter.Label(self.buttonBar, 
                              textvariable=self.currentFrameLabelVar)
        label.pack(side='left')
        
        # create paned widget, left side will hold the Tree of widgets
        # right side will hold the GUI for the interpolator associated
        self.top = Pmw.PanedWidget(self.master, orient='horizontal',
                                   hull_relief='sunken',
                                   hull_width=460, hull_height=300,
                                   )

 	self.treePane = self.top.add('widgetTree', min=30, size=200)
        self.editorPane = self.top.add('editorPage',  min=100, size=100)

        self.treeFrame = Pmw.ScrolledFrame(self.treePane,
             borderframe=1, horizscrollbar_width=7, vscrollmode='none',
             frame_relief='flat',
             frame_borderwidth=0, horizflex='fixed',
             vertflex='elastic')
        self.treeFrame.pack(expand=1, fill='both')

        self.top.pack(expand=1, fill='both')

        # build the Tree
        self.widgetTree = TreeView(master=self.treeFrame.interior(),
                                   displayValue=False, nohistory=True,
                                   mode='single')
        self.widgetTree.setAction(event='select',
                                  function=self.selectNode_cb)

        # add descriptor to update label
        self.curFrameAnim = ObjectAnimatorDescriptor(
            self, self.setCurrentFrame, 'curFrame',
            startFrame=0, endFrame=self.animator.getLastFrame())
        self.animator.addObjectAnimator(self.curFrameAnim)

        # descriptor of update Tk
        self.updateTkAnim = ObjectAnimatorDescriptor(
            self, self.master.update, 'updateTk',
            startFrame=0, endFrame=self.animator.getLastFrame())
        self.animator.addObjectAnimator(self.updateTkAnim)


    def run(self, event=None):
        last = self.animator.getLastFrame()
        self.curFrameAnim.namedArgs['endFrame'] = last 
        self.updateTkAnim.namedArgs['endFrame'] = last 
        self.animator.run()


    def setCurrentFrame(self):
        from SimPy.Simulation import now
        self.currentFrameLabelVar.set('cur. Frame: %g'%now())


    def populateTree(self, net, parent=None):
        """
recursively traverse the network and sub-networks to build a tree of
all widgets for each node in each network.
"""
        tree = self.widgetTree
##         for root in tree.roots:
##             tree.deleteNode(root)
            
        netNode = tree.addNode(parent=parent, object=net, name=net.name)
        for node in net.nodes:
            if isinstance(node, MacroNode):
                self.populateTree( node.macroNetwork, netNode )
            else:
                nbWidgets=0
                for p in node.inputPorts:
                    if isinstance(p.widget, NEDial) or \
                       isinstance(p.widget, NEThumbWheel):
                        nbWidgets += 1
                if nbWidgets==0:
                    continue
                nodeNode = tree.addNode(parent=netNode, object=node,
                                        name=node.name)
                for p in node.inputPorts:
                    if p.widget:
                        widgetNode = tree.addNode(
                            parent=nodeNode, object=p.widget,
                            name=p.widget.name)


    def selectNode_cb(self, node):
        # called when we click on a widget
        # it it is a leaf node (i.e.a  widget) we want to configure
        # the interpolator editor for this Vision widget
        self.setEditor(None)
        if node.object:
            if len(node.children)==0:
                widget = node.object
                if self.editorGUI.has_key(widget):
                    self.setEditor(widget)


    def setLinearInterp_cb(self, event=None):
        widget = self.widgetTree.GetSelected().object
        if self.editorGUI.has_key(widget):
            return

        interp = ScalarLinearInterpolator(0., 1., float)
        port = widget.port
        node = port.node
        net = node.network
        name = "%s.%s.%s"%(net.name,node.name,port.name)
        animDescr = ObjectAnimatorDescriptor(
            widget, widget.set, name,
            endFrame=self.animator.getLastFrame(), interpolator=interp)

        self.editorGUI[widget] = EditorGUI(self, animDescr,
                                           master=self.editorPane)
        self.animator.addObjectAnimator( animDescr )
        self.setEditor(widget)


    def setNoInterp_cb(self, event=None):
        # create and assign, or delete the interpolator associated with
        # a widget
        widget = self.widgetTree.GetSelected().object
        if self.editorGUI.has_key(widget):
            animDescr = self.editorGUI[widget].objectAnimatorDescr
            self.animator.delObjectAnimator( animDescr )
            if self.currentEditor==self.editorGUI[widget]:
                self.currentEditor.destroy()
                self.currentEditor = None


    def setEditor(self, widget):

        if self.currentEditor is not None:
            self.currentEditor.hide()

        if widget is not None:
            self.currentEditor = editor = self.editorGUI[widget]
            editor.show()
        


## netAnim = NetworkAnimatorGui()
## netAnim.populateTree(net())

#execfile("findWidgets.py")
#netAnim.animator.run()
#objanim1 = netAnim.animator.objectAnimatorDescr[0]
#objanim2 = netAnim.animator.objectAnimatorDescr[1]
#interp1 = objanim1.namedArgs['interpolator']
#interp2 = objanim2.namedArgs['interpolator']
