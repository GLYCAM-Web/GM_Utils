try:
    import Tkinter

    from scenario.director import Director
    #from scenario.gui import DirectorGUI
    from scenario.actor import Actor
    
    from mglutil.util.callback import CallbackFunction

    from DejaVu.Geom import Geom
    from DejaVu.Camera import Camera
    from DejaVu.Light import Light
    from DejaVu.Clip import ClippingPlane 
    from DejaVu.Viewer import SetCurrentObjectEvent, SetCurrentCameraEvent, SetCurrentLightEvent, SetCurrentClipEvent, AddObjectEvent

    from actor import RedrawActor, getAnimatableAttributes, getActorName
    import numpy
    from SimpleDialog import SimpleDialog
    import weakref
    
    class DejaVuScenario:
        """Class binding a DejaVu Viewer to a Scenario Director """

## This class allows to connect a DejaVu Viewer to a scenario Director
## The DejaVu viewer will have a new attribute director.
## a RedrawActor is added automatically to the director
## The director gets a new attribute .needRedraw that the RerawActor uses to
##   optimize redraw calls
## A menu buttons are added to the Viewer GUI to allow animation of objects
## A callback function is register in the viewer to handle setting the current(
##  Object, Camera, light, ciping plane.
## DejaVu object that are animated get two new attribute:
##   .animatedProperties which is a dict { object.name+'.'+propname : Actor instance }
##   .object.animatableProps which is an list of 2 dictionaries.
##   Both dicts contain {attribute name:{actorDescr}} items. The first
##   dict contains attributes explicitely decalared, the second contains
##   attributes picked up on the fly
##   
        


        def __init__(self, vi, director=None):
            self.application = vi
            if director is None:
                director = Director()
            vi.director = director
            self.menuCreated = False
            self.name = "DejaVuScenario"
            self.fileactorGui = {}


        def start(self):
            director = self.application.director
            director.start()
            self.setDirector()


        def setDirector(self):
            if not self.menuCreated:
                vi = self.application
                director = vi.director

                # add needsRedraw attribute
                director.needsRedraw = False
                # add RedrawActor actor
                actor = RedrawActor(vi)
                #actor.setKeyframe(50,0)
                director.addActor(actor )
                director.redrawActor = actor
                director.gui.setDuration(50)

                # add menu button to ViewerGUI
                # Objects
                self.animObjMenuB = menuB = Tkinter.Menubutton(
                    vi.GUI.inheritF, text='Animate', relief='raise' )
                menuB.menu = Tkinter.Menu(menuB)
                menuB['menu'] = menuB.menu
                menuB.pack(fill='x')

                # Cameras
                self.animCamMenuB = menuB = Tkinter.Menubutton(
                    vi.GUI.CameraProp, text='Animate', relief='raise' )
                menuB.menu = Tkinter.Menu(menuB)
                menuB['menu'] = menuB.menu
                menuB.pack(fill='x')

                # Lights
                self.animLightMenuB = menuB = Tkinter.Menubutton(
                    vi.GUI.LightProp, text='Animate', relief='raise' )
                menuB.menu = Tkinter.Menu(menuB)
                menuB['menu'] = menuB.menu
                menuB.pack(fill='x')

                # Cliping planes
                self.animClipMenuB = menuB = Tkinter.Menubutton(
                    vi.GUI.ClipProp, text='Animate', relief='raise' )
                menuB.menu = Tkinter.Menu(menuB)
                menuB['menu'] = menuB.menu
                menuB.pack(fill='x')

                # expand viewergui to accomodate Animate buttons
                vi.GUI.propertyNoteBook.setnaturalsize(pageNames=(vi.GUI.propertyNoteBook.getcurselection(),))
                vi.GUI.sf.interior().pack(fill = 'both', expand = 1)
                vi.GUI.sf.pack(fill = 'both', expand = 1)

                # register interest in setting current(object, camera, light, clip)
                func = self.setCurrentObjectAttrList_cb
                vi.registerListener(SetCurrentObjectEvent, func)
                vi.registerListener(SetCurrentCameraEvent, func)
                vi.registerListener(SetCurrentLightEvent, func)
                vi.registerListener(SetCurrentClipEvent, func)

                # call the callback once to fill menus for current object
                self.setCurrentObjectAttrList(vi.currentObject)
                self.setCurrentObjectAttrList(vi.currentCamera)
                self.setCurrentObjectAttrList(vi.currentClip)
                self.setCurrentObjectAttrList(vi.currentLight)
                self.menuCreated = True


        def setCurrentObjectAttrList_cb(self, event):
            self.setCurrentObjectAttrList(event.object)


        def setCurrentObjectAttrList(self, object, event=None):

            if not hasattr(object, 'animatableProps'):
                object.animatableProps = getAnimatableAttributes(object)
            if not hasattr(object, 'animatedProperties'):
                object.animatedProperties = {}

            self.createCheckbuttons(object)


        def createCheckbuttons(self, object):
            # get menu button
            if isinstance(object, Geom): menuB = self.animObjMenuB
            elif isinstance(object, Camera): menuB = self.animCamMenuB
            elif isinstance(object, Light): menuB = self.animLightMenuB
            elif isinstance(object, ClippingPlane): menuB = self.animClipMenuB
            else:
                print 'no menu button for object:', object, object.__class__
                return
            
            # clear menu's content
            menuB.menu.delete(0, 'end')

            # get list of properties
            p1 = object.animatableProps[0].keys()
            p1.sort()
            propnames = p1
            #p2 = object.animatableProps[1].keys()
            #p2.sort()
            #propnames = p1+p2
            
            # get dict of currently animated properties for this object
            aprop = object.animatedProperties
            
            for i, name in enumerate(propnames):
                var = Tkinter.IntVar()
                actorname = getActorName(object, name)
                if aprop.has_key(actorname):
                    var.set(1)
                    aprop[actorname].guiVar = var
                cb = CallbackFunction( self.toggleAnimatePropVar, name, var, object)
                menuB.menu.add_checkbutton(
                    label=name, command=cb, variable = var)
            menuB.menu.add_separator()
            cb = CallbackFunction(self.actorFromFile_cb, propnames, object)
            menuB.menu.add_command(
                label="Create Actor From File", command=cb)


        def toggleAnimatePropVar(self, propname, var, object):
            # toggle variable associated with the checkbutton for this
            # object.propname actor
            value = var.get()
            if value:
                self.createActor(object, propname, var)
            else:
                self.deleteActor(object, propname)


        def deleteActor(self, object, propname):
            # delete the actor for object.name
            actorname = getActorName(object, propname)
            actor = object.animatedProperties[actorname]
            self.application.director.deleteActor(actor)
            if object.animatedProperties.has_key(actorname):
                del object.animatedProperties[actorname]

            

        def createActor(self, object, propname, variable = None, check = True,
                        addToDirector = True, actorData=None,
                        redraw = True, valueGenerator = None):
            #if not object.hasBeenCurrent :
            #    self.setCurrentObjectAttrList(object)
            if not hasattr(object, 'animatedProperties'):
                object.animatedProperties = {}
            if not hasattr(object, 'animatableProps'):
                object.animatableProps = getAnimatableAttributes(object)
            # create an actor for object.propname
            descr = object.animatableProps[0][propname]
            actorname = getActorName(object, propname)
            director = object.viewer.director
            newactor = True
            if check:
                for i, a in enumerate(director.actors):
                    if a.name == actorname:
                        text = "Actor %s exists. Do you want to overwrite it?\n"%actorname
                        d = SimpleDialog(director.gui.root, text=text,
                                         buttons=["Yes", "No"],
                                         default=1, title="Overwrite Actor Dialog")
                        result = d.go()

                        if result == 1:
                            return None
                        else:
                            newactor = False #
                            actorind = i
                            break
            #create the actor
            actorClass, args, kw = descr['actor']
            if valueGenerator is not None:
                kw['interp'] = valueGenerator
            if actorData is not None:
                from scenario.actor import FileActor
                actor = FileActor(*(propname, object, actorClass, actorData)+args, **kw)
                actorname = actor.name
            else:
                actor = actorClass( *(propname, object)+args, **kw )
            actor.scenario = self
            object.animatedProperties[actorname] = actor
            if not newactor: # director already has an actor with name "actorname",
                             # and the user wishes to overwrite it
                # replace existing actor whith the new one
                oldactor = director.actors.pop(actorind)
                director.gui.deleteActor(oldactor)
                director.actors.insert(actorind, actor)
                actor._director = weakref.ref(director)
                posy = oldactor._posy
                director.gui.drawActor(actor, posy)
                if oldactor.guiVar:
                    variable = oldactor.guiVar
            
            else:
                if addToDirector:
                    # add actor to the director
                    director.addActor(actor, redraw)
            if variable:
                actor.guiVar = variable
            return actor

        def numarr2str(self, val):
            threshold = numpy.get_printoptions()["threshold"]
            numpy.set_printoptions(threshold=val.size)
            valstr = "array(" + numpy.array2string(val, precision =3, separator =",") + ", '%s')"%val.dtype.char
            #valstr.replace("\n", "\n\t")
            numpy.set_printoptions(threshold=threshold)
            return valstr
           
        def getActorScript(self, actor, indent, actorind):
            lines = []
            lines.append(indent + "vi = sci.application \n")
            object = actor.object
            name = actor.name
            if name == "redraw":
                
                lines.append(indent + "if not director.redrawActor:\n")
                lines.append(indent + "    from DejaVu.scenarioInterface.actor import RedrawActor\n")
                lines.append(indent + "    actor%d = RedrawActor(vi)\n" % actorind)
                lines.append(indent + "    director.addActor(actor%d)\n" % actorind)
                lines.append(indent + "    director.redrawActor = actor%d\n" % actorind)
                return lines, indent
            propname = name.split(".")[-1]
            scenarioname = actor.scenarioname
            from scenario.actor import FileActor
            isFileActor = False
            if isinstance(actor, FileActor):
                isFileActor = True
            else:   
                lines.append(indent + "# keyframe values: \n")
                lines.append(indent + "vals = [] \n")
                for val in actor.keyframeValues:
                    if type(val) == numpy.ndarray:
                        lines.append(indent + "from numpy import array\n")
                        valstr =  indent + "vals.append(" + self.numarr2str(val) + ")"
                    else:
                        try: # value can be a list of arrays
                            nbval = len(val)
                            isarray = False
                            valstr = indent + "vals.append(["
                            for n in range(nbval):
                                if type(val[n]) == numpy.ndarray:
                                    isarray = True
                                    valstr = valstr + self.numarr2str(val[n]) + ","
                                else:
                                    valstr = valstr + "%s"%val[n] + ","
                            valstr = valstr + "])"      
                            if isarray:       
                                lines.append(indent + "from numpy import array\n")
                        except:
                            valstr = indent + "vals.append(%s)" %(val,)
                    lines.append(valstr)
                    lines.append("\n")
                
            if hasattr(object, "fullName"):
                objname = object.fullName
                lines.append(indent+"obj%d = vi.FindObjectByName('%s')\n"%(actorind, objname))
                setCurrentFunc = "vi.SetCurrentObject(obj%d)\n"%actorind
            else:
                objname = object.name
                if isinstance(object, Camera):
                    ind = self.application.cameras.index(object)
                    lines.append(indent + "obj%d = vi.cameras[%d]\n"%(actorind, ind))
                    setCurrentFunc =  "vi.SetCurrentCamera(obj%d)\n"%actorind
                elif isinstance(object, Light):
                    ind = self.application.lights.index(object)
                    lines.append(indent + "obj%d = vi.lights[%d]\n"%(actorind, ind))
                    setCurrentFunc =  "vi.SetCurrentLight(obj%d)\n"%actorind
                elif isinstance(object, ClippingPlane):
                    ind = self.application.clipP.index(object)
                    lines.append(indent + "obj%d = vi.clipP[%d]\n"%(actorind, ind))
                    setCurrentFunc =  "vi.SetCurrentClip(obj%d)\n"%actorind
            lines.append(indent + "if not obj%d: tkMessageBox.showwarning('DejaVu Scenario Warning', 'Object %s does not exist.\\nCannot create actor %s')\n"% (actorind, objname, name))
            
            lines.append(indent + "else: \n")
            indent = indent + "    "
            lines.append(indent + setCurrentFunc)
            if not isFileActor:
                lines.append(indent+"try:\n")
                newindent = indent + "    "
                lines.append(newindent+"actor%d = sci.createActor(obj%d, '%s', redraw=False)\n"% (actorind, actorind, propname))
            
                lines.append(indent+"except:  tkMessageBox.showwarning('DejaVu Scenario warning', 'Could not create actor %s')\n" % name)
                lines.append(indent+"if actor%d:\n"%actorind)
                lines.append(newindent+"actor%d.keyframeValues = vals\n" % actorind)

            return lines, indent
        

        def getNewActors(self):
            # return a dictionary containing all available actors that are not in the
            # scenario's director.
            vi = self.application
            director = vi.director
            autotrackDict = director.autotrackDict
            if not vi.eventListeners.has_key(AddObjectEvent):
                func = self.getNewActor_cb
                vi.registerListener(AddObjectEvent, func)
            newDict = {}
            actornames = map(lambda x: x.name, director.actors[1:])
            
            allobjects = []
            for object in vi.rootObject.AllObjects():
                ## if object.name != "root":
##                     v = hasattr(object, 'vertexSet')
##                     f = hasattr(object, 'faceSet')
##                     if v and f:
##                         numv = len(object.vertexSet)
##                         numf = len(object.faceSet)
##                         if numv == numf == 0:
##                             continue
##                     elif v:
##                         numv = len(object.vertexSet)
##                         if numv == 0:
##                             continue
##                 if not object.visible:
##                     continue
                if object.listed:
                    # FIX THIS: we probably do not need to track all of the objects (too many actors),
                    # currently, do not include Viewer's objects under 'root|misc' and 'selection' objects
                    if object.fullName.find("misc") < 0 and object.fullName.find("selection") < 0:
                        allobjects.append(object)
            for c in vi.cameras:
                allobjects.append(c)
            for lt in vi.lights:
                if lt.enabled:
                    allobjects.append(lt)
            if vi.activeClippingPlanes > 0:
                allobjects.append(vi.currentClip)
                #for cp in vi.clipP:
                #    if cp.enabled:
                #        allobjects.append(cp)
            for object in allobjects:
                #self.setCurrentObjectAttrList(object)
                props = getAnimatableAttributes(object)[0]
                #print "object : ", object, props.keys()
                for propname in props.keys():
                    descr = props[propname]
                    actorname = getActorName(object, propname)
                    if not autotrackDict.has_key(actorname):
                        if not actorname in actornames:
                            # actor 'actorname' does not exist - create it and add to
                            # newDict
                            actorClass, args, kw = descr['actor']
                            actor = actorClass( *(propname, object)+args, **kw )
                            actor.scenario = self
                            #object.animatedProperties[actorname] = actor
                            newDict[actorname] = actor
            return newDict

        def getNewActor_cb(self, event):
            object = event.object
            if object.listed:
                if hasattr(object, "fullName"):
                    if object.fullName.find("selection") >= 0:
                        return
                vi = self.application
                director = vi.director
                autotrackDict = director.autotrackDict
                props = getAnimatableAttributes(object)[0]
                #print "object : ", object, props.keys()
                for propname in props.keys():
                    descr = props[propname]
                    actorname = getActorName(object, propname)
                    if not autotrackDict.has_key(actorname):
                        actorClass, args, kw = descr['actor']
                        actor = actorClass( *(propname, object)+args, **kw )
                        actor.scenario = self
                        #object.animatedProperties[actorname] = actor
                        autotrackDict[actorname] = actor
                        if actor.hasGetFunction:
                            val = actor.getValueFromObject()
                        else:
                            val = None


        def actorFromFile_cb(self, propnames, object):
            
            director = self.application.director
            #from actorFromFile import fromFileForm
            #form = fromFileForm(self, propnames, object, command = director.createFileActor)
            from scenario.fileActorGUI import fileActorGUI
            if object in self.fileactorGui.keys():
                self.fileactorGui[object].show()
            else:
                self.fileactorGui[object] = fileActorGUI(self, propnames, object, director.createActorFromData)
            
                        
        def onAddActorToDirector(self, actor):
            # create check buttons on the Viewer's gui (used when actor is added by
            # 'autotrack; feature
            object = actor.object
            if not hasattr(object, 'animatedProperties'):
                object.animatedProperties = {}
            object.animatedProperties[actor.name] = actor
            self.setCurrentObjectAttrList(object)

        

except ImportError:
    import traceback
    traceback.print_exc()
    traceback.print_stack()
    print 'WARNING: failed to import package scenario'
