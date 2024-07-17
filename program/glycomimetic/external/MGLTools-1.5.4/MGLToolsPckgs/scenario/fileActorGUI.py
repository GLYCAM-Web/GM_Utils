
import Tkinter
import Pmw
import tkFileDialog
from scenario.actor import adatFileParser
from os import path

class fileActorGUI:
    """ A class to build a GUI form to get the user's input for creating an actor from file data"""

    def __init__(self, scenario, propnames, object, command=None):
        # place some widgets on a Toplevel window
        master = Tkinter.Toplevel(scenario.application.master)
        self.scenario = scenario
        master.title("FileActor")
        self.master = master
        self.master.protocol('WM_DELETE_WINDOW', self.withdraw)
        self.file = ""
        #master.protocol('WM_DELETE_WINDOW', self.dismissCreateActor_cb )
        frame = self.frame = Tkinter.Frame(master, borderwidth=1, relief='ridge')
        self.padx = self.pady = 2
        frame.pack(fill='both', expand = 1, pady=self.pady, padx=self.padx)
        
        oname = ""
        if object:
            oname = object.fullName
            
        l = Tkinter.Label(frame, text = "Object: %s" % oname)
        l.grid(column=0, row=0, sticky='we')
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        
        self.fileB = Tkinter.Button(frame, text='data file:',
                           command=self.openFile_cb)
        self.fileB.grid(column=0, row=1,sticky='we')
        
        self.fileEF = Pmw.EntryField(frame, command = self.getFileName_cb,
                                     entry_width=12,
                                     value = self.file)
        self.fileEF.grid(column=1, row=1,sticky='we')
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(1, weight=1)

        self.chooser =Pmw.ComboBox(frame, labelpos ='n',
                              label_text='Select actor: ',
                              entryfield_value=propnames[0],
                              scrolledlist_items=propnames,
                              #fliparrow=1,
                              selectioncommand=self.updateCheckButtons_cb
                                   )
        self.chooser.grid(column=0, row=2, columnspan =2, sticky='we')#, rowspan=3)
        frame.rowconfigure(2, weight=1)
        
        self.fieldsGroup = Pmw.Group(frame, tag_text="Select actor's data field(s):" )
        groupinter = self.fieldsGroup.interior()
        self.fieldsGroup.grid(column=0, row=3, columnspan =2, sticky="we")
        frame.rowconfigure(3, weight=1)
        
        self.startEF = Pmw.EntryField(frame, labelpos = 'n',
                            label_text = 'start frame: ',
                            entry_width = 8,
                            value = 0,
                            validate = {'validator': 'numeric'})
        self.startEF.grid(column = 0, row = 4,sticky='we')

        self.endEF = Pmw.EntryField(frame, labelpos = 'n',
                            label_text = 'end frame: ',
                            entry_width = 8, )
                            #validate = {'validator': 'numeric'})
        self.endEF.grid(column = 1, row = 4,sticky='we')
        frame.rowconfigure(4, weight=1)
        
        b = self.createB = Tkinter.Button(frame, text='Create File Actor',
                           command=self.getValues_cb)
        b.grid(column=0, row=5, columnspan = 2, sticky='we')
        frame.rowconfigure(5, weight=1)        
        
        self.frame = frame
        self.command = command
        self.object = object
        self.file = None
        self.selectedFields = {}
        self.checkbuttons = {}
        self.shown = True
        self.fileParser = None


    def updateCheckButtons_cb(self, val):

        selected = []
        if self.selectedFields.has_key(val):
            selected = self.selectedFields[val]
        for f, val in self.checkbuttons.items():
            if f in selected:
                val.set(1)
            else: val.set(0)

    def openFile_cb(self):
        #open file dialog
        file = tkFileDialog.askopenfilename(parent = self.master,
                                            initialdir = '.', title='Actor file',
                                            filetypes=[('', '*.adat'), ('all', '*')] ,
                                            initialfile = self.file)
        if file:
            file = path.abspath(file)
            if self.file != file:
                self.readFile(file)
                self.fileEF.setentry(file)


    def getFileName_cb(self):
        # callback of the File name entry 
        name = self.fileEF.get()
        if name:
            file = path.abspath(name)
            if self.file != file:
                self.file = file
                self.readFile(file)


    def readFile(self, file):
        # called every time a new file is entered and parsed: a new set of checkbuttons
        # corresponding to file data fields is created. 
        self.fileParser = adatFileParser(file)
        fields = self.fileParser.fields
        if len(fields) and len(self.fileParser.data):
            self.file = file
            groupinter = self.fieldsGroup.interior()
            #for k,w in groupinter.children.items():
            #    w.pack_forget()
            # remove old checkbuttons
            for c in groupinter.children.values(): c.destroy()
            #print "groupinter.children",  groupinter.children
            self.checkbuttons = {}
            # create new checkbuttons
            for f in fields:
                var = Tkinter.IntVar()
                var.set(0)
                #print "field:", f
                w = Tkinter.Checkbutton(groupinter, text=f,
                                        variable = var)
                w.pack(padx=2, pady = 2, anchor = "w", side="top")
                self.checkbuttons[f] = var
            self.endEF.setentry(self.fileParser.nsteps-1)
            self.startEF.setentry(0)


    
    def getValues_cb(self):
        # get the input form values and call the command to create an actor
        if not self.fileParser:
            return
        actor = self.chooser.get()
        #print "actor:", actor
        try:
            kf1 = int(self.startEF.get())
        except:
            kf1 = 0
        #print "start frame:", kf1
        try:
            kf2 = int(self.endEF.get())
        except:
            kf2 = -1
        #print "end frame:", kf2
        
        fields = self.fileParser.fields
        selected = []
        for f in fields:
            if self.checkbuttons[f].get():
               selected.append(f)
        if len(selected):
            self.selectedFields[actor] = selected
            if self.command is not None:
                data = self.fileParser.getFieldsData(selected)
                self.command(self.object, actor, self.scenario,
                             self.file, selected, data, start = kf1, end = kf2)


    def show(self):
        # show the input form
        if not self.shown:
            self.master.deiconify()
            self.shown = True



    def withdraw(self):
        # hide the input form
        if self.shown:
            self.master.withdraw()
            self.shown = False


##     def updateWindowSize(self):
##         #fw = self.frame.winfo_width()
##         fh = self.frame.winfo_height()+self.pady*2
##         msize = self.master.geometry().split("+")[0].split("x")
##         mw = int(msize[0])
##         mh = int(msize[1])
        
##         if mh > fh:
##             self.master.geometry('%dx%d' % (mw, fh))
            
