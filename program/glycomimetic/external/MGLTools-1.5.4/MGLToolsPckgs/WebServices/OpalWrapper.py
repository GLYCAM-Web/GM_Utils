import copy
import os
import OpalUtil

from WebServices import AppService_client
from WebServices.AppService_types import ns0
from urlparse import urlparse


tab = "  "

class OpalWrapper(object):
  """docstring for OpalWrapper"""
  
  def __init__(self):
    pass

  def generate(self,url):
    self.url = url
    self.metadata = self.getAppMetadata(url)
    #setting up for local execution
    executable = self.getAppConfig(url)._binaryLocation
    # assuming the server is a unix
    executable = executable.rpartition("/")[2]
    if self.which(executable) == None:
        self.executable = ""
    else:
        self.executable = self.which(executable)
    #print "found an executable: " + self.which(executable)
    #building the class
    classdec = self.buildClassDeclaration(self.metadata,self.url)
    if(self.metadata._types):
      initmethod = self.buildInitMethod(self.metadata,self.url)
      callmethod = self.buildCallMethod(self.metadata)
    else:
      initmethod = self.buildDefaultInitMethod(self.url)
      callmethod = self.buildDefaultCallMethod()
    retclass = ""
    for i in classdec:
      retclass+=(str(i)+"\n")
    allmethods = []
    allmethods.extend(initmethod)
    allmethods.extend(callmethod)
    for i in allmethods:
      retclass+=(tab+str(i)+"\n")
    return retclass
  
  def getAppMetadata(self,url):
    """docstring for getAppMetadata"""
    appLocator = AppService_client.AppServiceLocator()
    appServicePort = appLocator.getAppServicePort(url)
    req = AppService_client.getAppMetadataRequest()
    metadata = appServicePort.getAppMetadata(req)
    return metadata

  def getAppConfig(self,url):
    """
        getAppConfig description: give the URL of the service it returns the appConfig of that service
    """
    appLocator = AppService_client.AppServiceLocator()
    appServicePort = appLocator.getAppServicePort(url)
    req = AppService_client.getAppConfigRequest()
    metadata = appServicePort.getAppConfig(req)
    return metadata

  def buildClassDeclaration(self,metadata,url):
    """docstring for buildClassDeclaration"""
    myclassname = url.split('/')[-1].replace('-','_')
    myclassname = myclassname.replace('.','_') 
    #LC 042308 added the server name to the generated classname 
    servername = urlparse(url)[1]
    servername = servername.replace('.','_')
    #servername = servername.replace(':','_') 
    servername = servername.split(':')[0]
    myclassname = myclassname + "_" + servername
    myret = []
    myret.append('class %s(object):' % myclassname)
    params = {}
    try:
      rawlist = metadata._types._flags._flag
      for i in rawlist:
        myhash = {}
        myhash = {'type':'boolean'}
        myhash['default'] = 'True' if str(i._default)=='1' else 'False'
        myhash['description'] = str(i._textDesc) if i._textDesc else 'No Description'
        params[str(i._id).replace('-','_')] = copy.deepcopy(myhash)
    except AttributeError:
      pass
    try:
      rawlist = metadata._types._taggedParams._param
      for i in rawlist:
        myhash = {}
        if i._value:
          myhash['type'] = 'selection'
          myhash['values'] = [str(z) for z in i._value]
        else:
          myhash['type'] = str(i._paramType)
        if(str(i._paramType)=="FILE"):
          myhash['ioType'] = str(i._ioType)
        myhash['description'] = str(i._textDesc) if i._textDesc else 'No Description'
        myhash['default'] = str(i._default) if i._default else None
        params[str(i._id).replace('-','_')] = copy.deepcopy(myhash)
    except AttributeError:
      pass
    try:
      rawlist = metadata._types._untaggedParams._param
      for i in rawlist:
        myhash = {}
        myhash['type'] = str(i._paramType)
        if(str(i._paramType)=="FILE"):
          myhash['ioType'] = str(i._ioType)
        myhash['description'] = str(i._textDesc)
        myhash['default'] = str(i._default) if i._default else None
        params[str(i._id).replace('-','_')] = copy.deepcopy(myhash)
    except AttributeError:
      pass
    myret.append(tab+'params='+str(params))
    return myret
  
  def buildInitMethod(self,metadata,url):
    """docstring for buildInitMethod"""
    myret = []
    myret = ['def __init__(self):',\
            tab+'self.url=\''+url+'\'',\
            tab+'from WebServices.AppService_client import AppServiceLocator,getAppMetadataRequest',\
            tab+'appLocator = AppServiceLocator()',\
            tab+'appServicePort = appLocator.getAppServicePort(self.url)',\
            tab+'req = getAppMetadataRequest()',\
            tab+'self.metadata = appServicePort.getAppMetadata(req)'
    ]
#    params = {}
    try:
      rawlist = metadata._types._flags._flag
      flaglist = [str(i._id) for i in rawlist]
#      for i in rawlist:
#        myhash = {'type':'boolean'}
#        myhash['default'] = 'True' if str(i._default)=='1' else 'False'
#        myhash['description'] = str(i._textDesc) if i._textDesc else 'No Description'
#        params[str(i._id)] = copy.deepcopy(myhash)
    except AttributeError:
      flaglist = []
    try:
      rawlist = metadata._types._taggedParams._param
      taglist = [str(i._id) for i in rawlist]
#      for i in rawlist:
#        myhash = {}
#        if i._value:
#          myhash['type'] = 'selection'
#          myhash['values'] = [str(z) for z in i._value]
#        else:
#          myhash['type'] = str(i._paramType)
#        myhash['description'] = str(i._textDesc) if i._textDesc else 'No Description'
#        myhash['default'] = str(i._default) if i._default else None
#        params[str(i._id)] = copy.deepcopy(myhash)
    except AttributeError:
      taglist = []
    try:
      rawlist = metadata._types._untaggedParams._param
      untaglist = [str(i._id) for i in rawlist]
#      for i in rawlist:
#        myhash = {}
#        myhash['type'] = str(i._paramType)
#        myhash['description'] = str(i._textDesc)
#        myhash['default'] = str(i._default) if i._default else None
#        params[str(i._id)] = copy.deepcopy(myhash)
    except AttributeError:
      untaglist = []
    if flaglist:
      myret.append(tab+'self.flags='+str(flaglist))
    else:
      myret.append(tab+'self.flags=[]') 
    if taglist:
      myret.append(tab+'self.taggedparams='+str(taglist))
    else:
      myret.append(tab+'self.taggedparams=[]')
    if untaglist:
      myret.append(tab+'self.untaggedparams='+str(untaglist))
    else:
      myret.append(tab+'self.untaggedparams=[]')
#    myret.append(tab+'self.params='+str(params))
    return myret
  
  def buildCallMethod(self,metadata):
    """docstring for buildCallMethod"""
    myret = []
    try:
      rawlist = metadata._types._flags._flag
      flaglist = [(str(i._id),True) if i._default else (str(i._id),False) for i in rawlist]
    except AttributeError:
      flaglist = []
    try:
      rawlist = metadata._types._taggedParams._param
      taglist = [(str(i._id),"'"+str(i._default)+"'") if i._default else (str(i._id),"''") for i in rawlist]
    except AttributeError:
      taglist = []
    try:
      rawlist = metadata._types._untaggedParams._param
      untaglist = [(str(i._id),"''") for i in rawlist]
    except AttributeError:
      untaglist = []
    myparams = []
    myparams.extend(flaglist)
    myparams.extend(taglist)
    myparams.extend(untaglist)
    myparams=map(lambda x: (x[0].replace('-','_'),x[1]),myparams)
    # add call function start to return array
    myret.append('def __call__(self,'+','.join('='.join((i[0],str(i[1]))) for i in myparams)+',localRun=False, execPath=' + repr(self.executable) + '):')
    # add variable assignment lines
    myret.extend([tab+'self._'+i[0]+'='+i[0] for i in myparams])
    # add boilerplate
    myret.extend([tab+'myflags=[]',\
                  tab+'mytaggedparams=[]',\
                  tab+'myuntaggedparams=[]',\
                  tab+'for i in self.flags:',\
                  tab+tab+'varname=\'_\' + i.replace(\'-\',\'_\')',\
                  tab+tab+'if getattr(self,varname):',\
                  tab+tab+tab+'myflags.append(i)',\
                  tab+'for i in self.taggedparams:',\
                  tab+tab+'varname=\'_\' + i.replace(\'-\',\'_\')',\
                  tab+tab+'if getattr(self,varname):',\
                  tab+tab+tab+'mytaggedparams.append((i,getattr(self,varname)))',\
                  tab+'for i in self.untaggedparams:',\
                  tab+tab+'varname=\'_\' + i.replace(\'-\',\'_\')',\
                  tab+tab+'if getattr(self,varname):',\
                  tab+tab+tab+'myuntaggedparams.append((i,getattr(self,varname)))',\
                  tab+'from WebServices import OpalUtil',\
                  tab+'myOpalUtil = OpalUtil.OpalUtil(self._vpe)',\
                  tab+'outurls = myOpalUtil.launchJob(self.url,myflags,mytaggedparams,myuntaggedparams,self.metadata,localRun,execPath)',\
                  tab+'return outurls'])
    return myret
  
  def buildDefaultInitMethod(self,url):
    """docstring for buildDefaultInit"""
    myret = ['def __init__(self):',\
            tab+'self.url=\''+url+'\'',\
            tab+'from WebServices.AppService_client import AppServiceLocator,getAppMetadataRequest',\
            tab+'appLocator = AppServiceLocator()',\
            tab+'appServicePort = appLocator.getAppServicePort(self.url)',\
            tab+'req = getAppMetadataRequest()',\
            tab+'self.metadata = appServicePort.getAppMetadata(req)'
    ]
    myret.append(tab+'self.commandline=\'\'')
    myret.append(tab+'self.inputfiles=[]')
    return myret
  
  def buildDefaultCallMethod(self):
    """docstring for buildDefaultCallMethod"""
    myret = ["def __call__(self,commandline='',inputfiles=[], numProcs='1',localRun=False,execPath=" + repr(self.executable) + "):",\
              tab+'from WebServices import OpalUtil',\
              tab+'from string import atoi',\
              tab+'myOpalUtil = OpalUtil.OpalUtil(self._vpe)',\
              tab+'outurls = myOpalUtil.launchBasicJob(self.url,commandline,inputfiles,atoi(numProcs),localRun,execPath)',\
              tab+'return outurls']
    return myret

  def which (self, filename):
    """
        which definition: given an executable if found on the current path it return the full path to the executable
                        otherwise it returns ""
    """
    if not os.environ.has_key('PATH') or os.environ['PATH'] == '':
      p = os.defpath
    else:
      p = os.environ['PATH']
    pathlist = p.split (os.pathsep)
    for path in pathlist:
      f = os.path.join(path, filename)
      if os.access(f, os.X_OK):
        return f
      #let's try harder to look for the command .bat .sh .exe 
      #expecially for windows
      fAlternative = f + '.exe'
      if os.access(fAlternative, os.X_OK):
        return fAlternative
      fAlternative = f + '.sh'
      if os.access(fAlternative, os.X_OK):
        return fAlternative
      fAlternative = f + '.bat'
      if os.access(fAlternative, os.X_OK):
        return fAlternative
    return ""


#wrap = OpalWrapper()
#print wrap.generate('http://ws.nbcr.net/opal/services/Pdb2pqrOpalService')

