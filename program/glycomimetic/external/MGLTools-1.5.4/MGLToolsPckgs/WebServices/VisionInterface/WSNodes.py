# $Header: /opt/cvs/WebServices/VisionInterface/WSNodes.py,v 1.35 2008/07/03 22:45:42 vareille Exp $
#
# $Id: WSNodes.py,v 1.35 2008/07/03 22:45:42 vareille Exp $

import os,time, urllib, tkMessageBox, webbrowser
from NetworkEditor.items import NetworkNode, FunctionNode
from Vision import UserLibBuild
from urlparse import urlparse


def Get_Opal_WS(url):
    """
Retruns the list of available Opal Web Services
output - list of Opal Web Services
"""
    #print "url", url
    if not url:
        tkMessageBox.showerror("Error!","No URL was provided")
        return
    opener = urllib.FancyURLopener({}) 
    servlet = opener.open(url)
    text = servlet.read()
    text = text.split('<ul>')
    text = text[1:]
    services = []
    for line in text[:-1]:
        #print "Line: " + line
        tmp_text = line.split(url)
        #print "tmp_text: " + str(tmp_text)
        port = tmp_text[-1].split('?wsdl')       
        #print "port: " + str(port)
        wsdl_url = port[0].split('href="')[-1]   + "?wsdl"
        #print "wsdl_url: " + str(wsdl_url)
        if ( isOpalService(wsdl_url) ):
            #print "adding a service: " + str(wsdl_url)
            services.append(wsdl_url[:-5])
        #else: do nothing just skeep it
#        from ZSI.wstools import WSDLTools
#        reader = WSDLTools.WSDLReader()
#        try:
#            wsdl = reader.loadFromURL(wsdl_url)
#            print "the wsdl from the reader is: " + wsdl
#            wsdl.services['AppService']
#            services.append(wsdl_url[:-5]) # to remove "?wsdl" part
#        except:
#            #print "No getAppMetadata for " + wsdl_url
#            # pass
#            raise
    return services

def isOpalService(wsdl_url):
    """
Given a wsdl_url which point to a wsdl it return true 
if the wsdl pointed by the url is a Opal Service
    """
    filehandle = urllib.urlopen(wsdl_url)
    string = filehandle.read()
    if ( string.find("wsdl:service name=\"AppService\"") != -1 ):
        return True
    else:
        return False
    

def addOpalServerAsCategory(host):
    """
Adds Category named `host` to Web Services Libary. 
If the Nodes in `host` Category already exist, this function updates them.
"""

    services = Get_Opal_WS(host+'/servlet/AxisServlet')
    if not services:
        print "No Opal web service is found on ", host
        return
    #print "services", services

    short_name = host.split('http://')[-1]
    short_name = short_name.split('.')
    short_name = short_name[0] + "." + short_name[1]
    for service in services:
        serviceName = service.split('/')[-1]
        serviceName = serviceName.replace('.','_')
        serverName = urlparse(service)[1]
        serverName = serverName.replace('.','_')
        #serverName = serverName.replace(':','_')
        serverName = serverName.split(':')[0]
        serviceOpalWrap = serviceName + "_" + serverName
        #print serviceOpalWrap
        if wslib.libraryDescr.has_key(host):
            for node in wslib.libraryDescr[host]['nodes']:
                if node.name == serviceOpalWrap:
                    wslib.deleteNodeFromCategoryFrame(host, FunctionNode, nodeName=serviceOpalWrap)
        from WebServices.OpalWrapper import OpalWrapper
        wrapper = OpalWrapper()
        wrap = wrapper.generate( service )
        if wrap is not None:
            mod = __import__('__main__')
            for modItemName in set(dir(mod)).difference(dir()):
                locals()[modItemName] = getattr(mod, modItemName)
            exec(wrap)
            #print "wrap: ", wrap
            lServiceOpalClass = eval(serviceOpalWrap)
            lServiceOpalClass.sourceCode = wrap
            setattr(mod, serviceOpalWrap, lServiceOpalClass)
            wslib.addNode(FunctionNode, serviceOpalWrap, host, 
                          kw={'functionOrString':serviceOpalWrap,
                              'host':host
                             }
                         )



class GetWSNode(NetworkNode):
    """Drug and drop 'Load WS' node into a network to load web services.
Input Port: host (bound to ComboBox widget)
Change to host as needed to load additional web services.
"""
    def __init__(self, name='WS_List', host=None, **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True
        self.widgetDescr['host'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':['http://ws.nbcr.net/opal', 'http://nbcrdemo.ucsd.edu:8080/opal'],
            'initialValue':'http://ws.nbcr.net/opal',
            'entryfield_entry_width':18,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'Host:'},
            }                   
        self.inputPortsDescr.append( {'name':'host', 'datatype':'string'} )
        code = """def doit(self, host):   
    addOpalServerAsCategory(host)            
"""
        if code:
            self.setFunction(code)


class OpalServiceNode(NetworkNode):
    """A generic Opal Web Service Node that extends NetworkEditor.items.NetworkNode 
and impliments common functionalty among Opal Web Service Nodes.
    http://nbcr.net/services/opal
    """
    def __init__(self, service=None, **kw):
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True
        from mglutil.web.services.AppService_client import AppServiceLocator, launchJobRequest, \
getOutputsRequest, queryStatusRequest
        from mglutil.web.services.AppService_types import ns0
        self.appLocator = AppServiceLocator()
        self.req = launchJobRequest()        
        self.inputFile = ns0.InputFileType_Def('inputFile')   

        self.widgetDescr['outputURL'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'labelCfg':{'text':'output URL'},
            }    
        self.inputPortsDescr.append(datatype='boolean', name='outputURL')            
        self.outputPortsDescr.append(datatype='string', name='URL')    
        if service:   
            self.constrkw['service'] = `service`
            self.service = service
            self.host =  self.service[:7+self.service[7:].find('/')] #to get rid of part after http://ws.nbcr.net:8080
            
    def runws(self):
        """
        Runs Opal Web Service on a given port:
            Returns resp if succeeded or
            prints obID and resp._baseURL message if failed, and returns ""
        """
        appServicePort = self.appLocator.getAppServicePort(self.service)
        try:
            self.resp = appServicePort.launchJob(self.req)
            jobID = self.resp._jobID
            self.resp = appServicePort.queryStatus(queryStatusRequest(jobID))
        except Exception, inst:
            from ZSI import FaultException
            if isinstance(inst, FaultException):
                tmp_str = inst.fault.AsSOAP()
                tmp_str = tmp_str.split('<message>')
                tmp_str = tmp_str[1].split('</message>')
                if len(tmp_str[0]) > 500:
                    print tmp_str[0]
                    tmp_str[0] = tmp_str[0][0:500] + '...'
                tkMessageBox.showerror("ERROR: ",tmp_str[0])
                self.resp = None
                return

        while self.resp._code != 8:
            time.sleep(1)
            self.resp = appServicePort.queryStatus(queryStatusRequest(jobID))
            if self.resp._code == 4:
                print "jobID:",jobID, 'failed on', self.resp._baseURL
                opener = urllib.FancyURLopener({}) 
                errorMsg = opener.open(self.resp._baseURL+"/std.err").read()
                tkMessageBox.showerror("Error!",errorMsg)
                webbrowser.open(self.host + '/' + jobID)
                return ""
        self.outurl = self.host + '/' + jobID
        self.resp = appServicePort.getOutputs(getOutputsRequest(jobID))

                        
class pdb2pqrNode(OpalServiceNode):
    """Web Service for pdb2pqr 
Input Ports
either
    input_file: string that holds the path to the input file supported by Babel
or
    input_mol: MolKit.Molecule instance
    
    options: command line options (bound to Entry widget)

Output Ports
    output_file_url: URL of the output file
"""
    def __init__(self, name='pdb2pqr', service=None, **kw):
        kw['name']=name
        OpalServiceNode.__init__(self, service=service, **kw )        
        self.inputPortsDescr.append(datatype='string', name='input_file')
        self.inputPortsDescr.append(datatype='Molecule', name='input_mol')
        
        self.widgetDescr['options'] = {'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'options:'},
            'labelGridCfg':{'sticky':'e'},
             'width':10,
             }
        self.inputPortsDescr.append( {'name':'options', 'datatype':'string',
                                     'required':False})
        
        self.widgetDescr['ff'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':['amber', 'charmm', 'parse' ],
            'fixedChoices':True,
            'initialValue':'amber',
            'entryfield_entry_width':7,
            'labelCfg':{'text':'forcefield:'},
            }
        self.inputPortsDescr.append(datatype='string', name='ff')
                            
        self.outputPortsDescr.append(datatype='string', name='output_file_url')
        code = """def doit(self, outputURL, input_file, input_mol, options, ff ):    
    if input_mol:
        self.inputPorts[1].required = False
        input_file_base = os.path.basename(input_mol.parser.filename)
        self.inputFile._name = input_file_base
        sampleFileString = ''
        for line in input_mol.parser.allLines:
            sampleFileString += line
    else:
        self.inputPorts[2].required = False
        input_file_base = os.path.basename(input_file)
        self.inputFile._name = input_file_base
        sampleFile = open(input_file, 'r')
        sampleFileString = sampleFile.read()
        sampleFile.close()

    options = options + ' --ff='+ff + ' ' + input_file_base + ' ' + input_file_base +'.pqr'
    self.req._argList = options
    inputFiles = []
    self.inputFile._contents = sampleFileString
    inputFiles.append(self.inputFile)
    self.req._inputFile = inputFiles
    self.runws()
    output_file_url = None
    if self.resp:
        for files in self.resp._outputFile:
            if files._url[-4:] == input_file_base +'.pqr':
                output_file_url = files._url
        if not output_file_url:
            self.outputData(URL = self.outurl)
            return
        print outputURL, self.outurl
        if not outputURL:
            import urllib
            opener = urllib.FancyURLopener({})
            in_file = opener.open(output_file_url)
            self.outputData(URL = self.outurl, output_file_url = in_file.read())
        else:
            self.outputData(URL = self.outurl, output_file_url=output_file_url)
"""     
        if code:
            self.setFunction(code)
        
        codeAfterConnect_input_mol = """def afterConnect(self, conn):
    # self refers to the port
    # conn is the connection that has been created
    self.node.getInputPortByName('input_file').required = False
"""    
        self.inputPortsDescr[2]['afterConnect']= codeAfterConnect_input_mol

        codeAfterConnect_input_file = """def afterConnect(self, conn):
    # self refers to the port
    # conn is the connection that has been created
    self.node.getInputPortByName('input_mol').required = False
"""    
        self.inputPortsDescr[1]['afterConnect']= codeAfterConnect_input_file   

class DownloadNode(NetworkNode):
    """Downloads remote files from the URL.
Input Ports
    url: URL for the remote file
Output Ports
    output: string containing the contents of the remote file
"""
    def __init__(self, name='Download', host = None, **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        
        self.widgetDescr['url'] = {'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'URL'},
                    }
        self.inputPortsDescr.append( {'name':'url', 'datatype':'string'} )

        self.outputPortsDescr.append(datatype='string', name='output')
        
        code = """def doit(self, url):   
            opener = urllib.FancyURLopener({})
            in_file = opener.open(url)
            self.outputData(output=in_file.read())
"""
        if code:
            self.setFunction(code)



class WebBrowserNode(NetworkNode):
    """Opens a URL with default Web Browser.
Input Ports
    url: URL
"""
    def __init__(self, name='Download', host = None, **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        
        self.widgetDescr['url'] = {'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'URL'},
                    }
        self.inputPortsDescr.append( {'name':'url', 'datatype':'string'} )
        
        code = """def doit(self, url,):   
            url = self.getInputPortByName('url').data
            webbrowser.open(url)
"""
        if code:
            self.setFunction(code)

from Vision.VPE import NodeLibrary
wslib = NodeLibrary('Web Services', '#d7fdf9')
wslib.addNode(GetWSNode, 'Load WS', 'Generic')
wslib.addNode(DownloadNode, 'Download', 'Generic')
wslib.addNode(WebBrowserNode, 'WebBrowser', 'Generic')
#addOpalServerAsCategory('http://ws.nbcr.net/opal')
#addOpalServerAsCategory('http://nbcrdemo.ucsd.edu:8080/opal')

try:
    UserLibBuild.addTypes(wslib, 'MolKit.VisionInterface.MolKitTypes')
except:
    pass
