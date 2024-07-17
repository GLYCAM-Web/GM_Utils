from NetworkEditor.items import NetworkNode
from idlelib.EditorWindow import EditorWindow
from IPython.kernel import client
import Tkinter, types, inspect, warnings

class IPmec(NetworkNode):
    """A node for connecting to a running MultiEngineController object

inputs:
    furl: foolscap URL or the controller, empty string will pick up default engine
    cmds: python code to executed in all engines. typically imports of needed things
    
outputs:
    mec: a MEC instance
"""
    def afterAddingToNetwork(self):
        NetworkNode.afterAddingToNetwork(self)
        top = Tkinter.Toplevel()
        top.withdraw()
        ed = EditorWindow(root=top)
        ed.top.withdraw()
        self.top = ed.top
        self.editorDialogue = ed
        b=Tkinter.Button(master=ed.status_bar,
                         text='Apply', command=self.applyCmd)
        b.pack(side='left')
        
    def __init__(self, name='MEC', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.mec = None
        self.mecCode = ""

        self.widgetDescr['furl'] = {
            'class':'NEEntry', 'master':'node', 'labelCfg':{'text':'furl:'},
            'initialValue':''}

        self.widgetDescr['codeEditor'] = {
            'class':'NECheckButton', 'master':'node',
            'initialValue':0, 'labelCfg':{'text':'code editor'},
            }

        self.inputPortsDescr.append(datatype='string', name='furl')
        self.inputPortsDescr.append(datatype='int', name='codeEditor')
        
        self.outputPortsDescr.append(datatype=None, name='mec')

        code = """def doit(self, furl, codeEditor):
        
    if self.inputPorts[1].hasNewData():
        if codeEditor:
            self.show()
        else:
            self.hide()

    if self.inputPorts[0].hasNewData():
        if furl=='':
            furl = None
        self.mec = client.MultiEngineClient(furl)
        nbProc = len(self.mec.get_ids())
        self.rename('mec_%dproc'%nbProc)
        self.applyCmd()
        
    self.outputData(mec=self.mec)
"""
        self.setFunction(code)

            
    def applyCmd(self, event=None):
        self.mecCode = self.editorDialogue.io.text.get("1.0", 'end')
        for line in self.mecCode.split('\n'):
            if len(line):
                print self.mec.execute(line)

    def pass_cb(self, event=None):
        pass

    def show(self, event=None):
        # reset source code
        self.editorDialogue.io.text.delete("1.0", "end")
        self.editorDialogue.io.text.insert("1.0", self.mecCode)
        self.top.deiconify()

    def hide(self, event=None):
        self.top.withdraw()



class IPScatter(NetworkNode):
    """A node for distributing data to engines of a MEC

inputs:
    data: vector of data to be scattered
    varname: name of the variable holding the partial vectors onm the engines
    mec: MEC instance
    
outputs:
    mec: a MEC instance
"""
    def __init__(self, name='Scatter', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.widgetDescr['varname'] = {
            'class': 'NEEntry', 'width':10,
            'initialValue':'v0',
            'labelGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'variable name'},
            }
        self.inputPortsDescr.append(datatype='list', name='data')
        self.inputPortsDescr.append(datatype='string', name='varname')
        self.inputPortsDescr.append(datatype=None, name='mec')

        self.outputPortsDescr.append(datatype=None, name='mec')
        self.outputPortsDescr.append(datatype='string', name='varname')
        
        code = """def doit(self, data, varname, mec):
    print mec.scatter(varname, data)
    self.outputData(varname=varname, mec=mec)
"""
                
        self.setFunction(code)



class IPGather(NetworkNode):
    """A node for retrieving data from engines

inputs:
    varname: name of the variable holding the partial vectors onm the engines
    mec: MEC instance
    
outputs:
    data: gathered data
"""
    def __init__(self, name='Gather', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.widgetDescr['varname'] = {
            'class': 'NEEntry', 'width':10,
            'initialValue':'v0',
            'labelGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'variable name'},
            }
        self.inputPortsDescr.append(datatype='string', name='varname')
        self.inputPortsDescr.append(datatype=None, name='mec')

        self.outputPortsDescr.append(datatype=list, name='data')
        
        code = """def doit(self, data, varname, mec):
    print mec.gather(varname)
    self.outputData(varname=varname, data=data)
"""
                
        self.setFunction(code)
   

class IPPull(NetworkNode):
    """A node for fetching data from engines of a MEC

inputs:
    varname: name of the variable holding the partial vectors onm the engines
    mec: MEC instance
    
outputs:
    data: a single list of all data from all engines
    dataPerEngine: a list of data from each engine
"""
    def __init__(self, name='Pull', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.inputPortsDescr.append(datatype='string', name='varname')
        self.inputPortsDescr.append(datatype=None, name='mec')

        self.outputPortsDescr.append(datatype=None, name='data')
        self.outputPortsDescr.append(datatype='list', name='dataPerEngine')

        code = """def doit(self, varname, mec):
    vall = []
    vperengine = []
    for engine in mec.get_ids():
        v = mec.pull(varname, [engine])
        vall.extend(v)
        vperengine.append(v)
    self.outputData(data=vall, dataPerEngine=vperengine)
"""

        self.setFunction(code)

   

class IPPush(NetworkNode):
    """A node for sending python objects to the engines of a MEC

inputs:
    objects: objects to be sent to the MEC engines
    mec: MEC instance
    
outputs:
"""
    def __init__(self, name='Push', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.inputPortsDescr.append(datatype=None, name='object',
                                    singleConnection=False)
        self.inputPortsDescr.append(datatype=None, name='mec')

        code = """def doit(self, objects, mec):
    for obj in ojbects:
        print mec.push(obj)
"""

        self.setFunction(code)

   

class IPPushFunction(NetworkNode):
    """A node for sending python functions to the engines of a MEC

inputs:
    function: function to be sent to the MEC engines
    mec: MEC instance
    
outputs:
"""
    def __init__(self, name='Push Func', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.inputPortsDescr.append(datatype=None, name='function')
        self.inputPortsDescr.append(datatype=None, name='mec')

        code = """def doit(self, function, mec):
    for obj in ojbects:
        print mec.push_function(dict(function.__name__=function.__name__))
"""

        self.setFunction(code)


class IPRunFunction(NetworkNode):
    """Node to run a function in parallel in MEC engines

inputs:
    mec: Multi Engine Controller
    scatter: index of the arguement to be scattered across engines
    command: name or instance of the function to execute
    importString: statements to execute before command definition
    
output:
    result: values returned by the function
"""
    def __init__(self, functionOrString=None, importString=None,
                 posArgsNames=[], namedArgs={},
                 name='PRunFunc', **kw):
        if kw.has_key('name') is False:
            kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        if type(functionOrString) == types.StringType:
            # we add __main__ to the scope of the local function
            # the folowing code is similar to: "from __main__ import *"
            # but it doesn't raise any warning, and its probably more local
            # and self and in1 are still known in the scope of the eval function
            mod = __import__('__main__')
            for modItemName in set(dir(mod)).difference(dir()):
                locals()[modItemName] = getattr(mod, modItemName)
            if importString is not None:
                exec(importString)
            if kw.has_key('masternet') is True:
                masterNet = kw['masternet']  
            function = eval(functionOrString)
        else:
            function = functionOrString

        if hasattr(function, 'name'):
            self.funcname = function.name
        elif hasattr(function, '__name__'):
            self.funcname = function.__name__
        else:
            self.funcname = function.__class__.__name__ 

        if inspect.isclass(function) is True:
            function = function()

        self.function = function # function to be called

        self.posArgsNames = posArgsNames
        self.namedArgs = namedArgs # dict:  key: arg name, value: arg default
        self.defaultNamedArgs = [] # used for Pmv
        self.defaultNamedArgsdefaults = [] # used for Pmv
        
        ip = self.inputPortsDescr
        ip.append(datatype=None, name='mec')
        ip.append(datatype='int', name='scatter')
        
        codeBeforeDisconnect = """def beforeDisconnect(self, c):
    # upon disconnecting we want to set the attribute function to None
    c.port2.node.function = None
    # remove all ports beyond the 'function' and 'importString' input ports
    for p in c.port2.node.inputPorts[2:]:
        c.port2.node.deletePort(p)
"""

        self.widgetDescr['command'] = {
            'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'function'}}
            
        self.widgetDescr['importString'] = {
            'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'import'}}
            
        ip.append(name='command', required=True, datatype='None',
                  beforeDisconnect=codeBeforeDisconnect)

        ip.append(name='importString', required=False, datatype='string',
                  beforeDisconnect=codeBeforeDisconnect)

        self.outputPortsDescr.append(datatype='None', name='result')

        code = """def doit(self, mec, scatter, command, importString='', *args):
    functionOrString = command
    import types
    if type(functionOrString) == types.StringType:
        # we add __main__ to the scope of the local function
        # the folowing code is similar to: "from __main__ import *"
        # but it doesn't raise any warning, and its probably more local
        # and self and in1 are still known in the scope of the eval function
        mod = __import__('__main__')
        for modItemName in set(dir(mod)).difference(dir()):
            locals()[modItemName] = getattr(mod, modItemName)
        if importString != '':
            exec(importString)
            print mec.execute(importString)
            
        function = eval(functionOrString)
    else:
        function = functionOrString
        functionOrString = None

    if function is None:
        return
    #if function is not self.function:
    if self.constrkw.has_key('functionOrString') is False \
      or ( self.constrkw['functionOrString'] != "\'"+functionOrString+"\'" \
      and self.constrkw['functionOrString'] != functionOrString ):
        # remember current function
        self.function = function
        if hasattr(function, 'name'):
            self.funcname = function.name
            self.rename('PRun '+ self.funcname)
        elif hasattr(function, '__name__'):
            self.funcname = function.__name__
            self.rename('PRun '+ self.funcname)
        else:
            self.funcname = function.__class__.__name__ 
            self.rename('PRun '+ self.funcname)

        print 'L pushing function', self.funcname
        print mec.push_function({self.funcname:function})
        print 'pulling', mec.execute('print %s'%self.funcname)
        
        # remove all ports beyond the function and the importString input ports 
        for p in self.inputPorts[4:]:
            self.deletePort(p, updateSignature=False)

        # get arguments description
        from inspect import getargspec
        if hasattr(function, '__call__') and hasattr(function.__call__, 'im_func'): 
            args = getargspec(function.__call__.im_func)
        else:
            args = getargspec(function)

        if len(args[0])>0 and args[0][0] == 'self':
            args[0].pop(0) # get rid of self

        allNames = args[0]

        defaultValues = args[3]
        if defaultValues is None:
            defaultValues = []
        nbNamesArgs = len(defaultValues)
        if nbNamesArgs > 0:
            self.posArgsNames = args[0][:-nbNamesArgs]
        else:
            self.posArgsNames = args[0]
        d = {}
        for name, val in zip(args[0][-nbNamesArgs:], defaultValues):
            d[name] = val
        for name, val in zip(self.defaultNamedArgs, self.defaultNamedArgsdefaults):
            d[name] = val

        self.namedArgs = d

        # create widgets and ports for arguments
        if hasattr(function, 'params') and type(function.params) == types.DictType:
            argsDescription = function.params
        else:
            argsDescription = {}
        self.buildPortsForPositionalAndNamedArgs(self.posArgsNames, self.namedArgs,
                                                 argsDescription=argsDescription)

        # create the constructor arguments such that when the node is restored
        # from file it will have all the info it needs

        if functionOrString is not None:
            if type(functionOrString) == types.StringType:
                self.constrkw['functionOrString'] = "\'"+functionOrString+"\'"
            else:
                self.constrkw['functionOrString'] = functionOrString
            if importString is not None:
                self.constrkw['importString'] ="\'"+ importString+"\'"
            else:
                self.constrkw['importString'] ="\'\'"
        elif hasattr(function, 'name'):
            # case of a Pmv command
            self.constrkw['command'] = 'masterNet.editor.vf.%s'%function.name
        elif hasattr(function, '__name__'):
            # a function is not savable, so we are trying to save something
            self.constrkw['functionOrString'] = function.__name__
        else:
            # a function is not savable, so we are trying to save something
            self.constrkw['functionOrString'] = function.__class__.__name__

        self.constrkw['posArgsNames'] = str(self.posArgsNames)
        self.constrkw['namedArgs'] = str(self.namedArgs)
        
    elif self.function is not None:
        # get all positional arguments
        sig = ""
        numArg = 0
        for pn in self.posArgsNames:
            if numArg==scatter:
                print 'L scattering', pn, locals()[pn]
                print mec.scatter(pn, locals()[pn])
                print 'pull ',mec.pull(pn)
            else:
                print 'pushing', pn, locals()[pn]
                print mec.push({pn:locals()[pn]})
                print 'pull', mec.pull(pn)

            sig += pn+', '
            numArg += 1

        # build named arguments
        for arg in self.namedArgs.keys():
            if numArg==scatter:
                print mec.scatter(arg, locals()[arg])
            else:
                #print mec.push(dict(arg=locals()[arg]))
                mec[arg] = locals()[arg]
            sig += arg+'=' + arg+ ', '
            numArg += 1

        # call function

        #print mec.push(dict(posargs=poargs))
        #print mec.push(dict(kw=kw))
        s =  'result = %s('%self.funcname + sig[:-2]+' )'
        print 'EXECUTING2', s
        print mec.execute(s)
        
##         try:
##             if hasattr(function,'__call__') and hasattr(function.__call__, 'im_func'):
##                 s = 'result = %s.__call__('%self.funcname + sig[:-2]+' )'
##                 print 'EXECUTING1', s
##                 print mec.execute( s )
##             else:
##                 s =  'result = %s('%self.funcname + sig[:-2]+' )'
##                 print 'EXECUTING2', s
##                 print mec.execute(s)
##         except Exception, e:
##             warnings.warn(e)
##             result = None
        result = mec.gather('result')
        self.outputData(result=result)
"""
        if code: self.setFunction(code)


    def buildPortsForPositionalAndNamedArgs(self, args, namedArgs, argsDescription={}):
        lAllPortNames = args + namedArgs.keys()
        for name in lAllPortNames:
            if name in args:
                ipdescr = {'name':name, 'required':True}
                if argsDescription.get(name):
                    lHasDefaultValue = True
                    val = argsDescription[name]['default']
                else:
                    lHasDefaultValue = False
            else:
                ipdescr = {'name':name, 'required':False}
                lHasDefaultValue = True
                val = namedArgs[name]

            if lHasDefaultValue is False:
                # create port
                ip = apply( self.addInputPort, (), ipdescr )
            else:
                dtype = 'None'
                if argsDescription.get(name) and argsDescription[name]['type']=='selection':
                    dtype = 'string'
                    self.widgetDescr[name] = {
                        'class': 'NEComboBox',
                        'initialValue':val,
                        'choices':argsDescription[name]['values'],
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
                elif argsDescription.get(name) \
                  and argsDescription[name]['type']=='FILE' \
                  and (   argsDescription[name]['ioType']=='INPUT' \
                       or argsDescription[name]['ioType']=='INOUT'):
                    dtype = 'string'
                    self.widgetDescr[name] = {
                        'class': 'NEEntryWithFileBrowser',
                        'initialValue':val,
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
                elif type(val) is types.BooleanType:
                    dtype = 'boolean'
                    self.widgetDescr[name] = {
                        'class': 'NECheckButton',
                        'initialValue':val==True,
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
                elif type(val) in [ types.IntType, types.LongType]:
                    dtype = 'int'
                    self.widgetDescr[name] = {
                        'class': 'NEDial', 'size':50,
                        'showLabel':1, 'oneTurn':1, 'type':'int',
                        'initialValue':val,
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
                elif type(val) in [types.FloatType, types.FloatType]:
                    dtype = 'float'
                    self.widgetDescr[name] = {
                        'class': 'NEDial', 'size':50,
                        'showLabel':1, 'oneTurn':1, 'type':'float',
                        'initialValue':val,
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
                elif type(val) is types.StringType:
                    dtype = 'string'
                    self.widgetDescr[name] = {
                        'class': 'NEEntry', 'width':10,
                        'initialValue':val,
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
    
                if argsDescription.get(name):
                    self.widgetDescr[name]['labelBalloon'] = argsDescription[name]['description']

                ipdescr.update({'datatype':dtype,
                        'balloon':'Defaults to'+str(val),
                        'singleConnection':True})

                # create port
                ip = apply( self.addInputPort, (), ipdescr )
                # create widget if necessary
                if dtype != 'None':
                    ip.createWidget(descr=self.widgetDescr[name])


class IPmap(NetworkNode):
    """A node for mapping a function to a sequence of data in parallel

inputs:
    function: function to apply to the data
    data: data 
    mec: MEC instance
    
outputs:
    data: data resulting from the mapping operation

example: parallel_result = mec.map(lambda x:x**10, range(32))
"""
    def __init__(self, name='Map', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.inputPortsDescr.append(datatype=None, name='function')
        self.inputPortsDescr.append(datatype=None, name='data')
        self.inputPortsDescr.append(datatype=None, name='mec')

        self.outputPortsDescr.append(datatype=None, name='data')

        code = """def doit(self, function, data, mec):
    assert callable(function)
    result = mec.map(function, data)
    self.outputData(data=result)
"""

        self.setFunction(code)


from Vision.VPE import NodeLibrary
iplib = NodeLibrary('IPython', 'grey75')

iplib.addNode(IPmec, 'MEC', 'Objects')
iplib.addNode(IPPull, 'Pull', 'Communication')
iplib.addNode(IPPush, 'Push', 'Communication')
iplib.addNode(IPPull, 'Push Func', 'Communication')
iplib.addNode(IPScatter, 'Scatter', 'Communication')
iplib.addNode(IPGather, 'Gather', 'Communication')
iplib.addNode(IPmap, 'PMap', 'Mapper')
iplib.addNode(IPRunFunction, 'PRunFunc', 'Mapper')

## TYPES to define
## MEC
## function

## TODO
# vlocking flag for mec
# starting engines and controler locally if none found
# 
