# Author: Wes Goodman
# Module for launching Opal jobs within Vision
import sys
import time
import httplib
import os
import shutil
import subprocess
import tempfile

try:
  from AppService_client import AppServiceLocator, launchJobRequest, getOutputsRequest, queryStatusRequest
  from AppService_types import ns0
except:
  from WebServices.AppService_client import AppServiceLocator, launchJobRequest, \
       getOutputsRequest, queryStatusRequest
  from WebServices.AppService_types import ns0

from ZSI.TC import String

class OpalUtil(object):
    """
    OpalUtil: Static class containing generic utility wrappers for exectuting Opal Web Service calls
    """
    def __init__(self, vpe):
        """
          initialize OpalUtil object
        """
        self.vpe = vpe


    def launchJob(self,url,flags,taggedparams,untaggedparams,meta,localRun=False,executable=''):
        """
          launchJob description:
          @input:
            -url: for application endpoint
            -flags: list of flag ids for the application
            -taggedparams: list of tuples: [(tag_id,value),...]
            -untaggedparams: list of tuples: [(tag_id,value),...]
            #-files: list of tuples of the form: [(name, filehandle),...]
            -meta: getAppMetadata output object
          @output:
            -returns tuple: (job code, status message, output url)
        """
        # build two hashes: flaghash, taggedhash from xml
        #  Index on id, value will be tag    
        flaghash = self.buildHash(meta,'flags')
        taggedhash = self.buildHash(meta,'taggedParams')
        separator = meta._types._taggedParams._separator
        if ( separator == None ):
            separator=' '
        # map from flag ids to flag tags
        flagtags = map(lambda x: flaghash[x],flags)
        command = ' '.join(flagtags)
        inputFiles = []
        for (tagid,val) in taggedparams:
            #let's create the tagged params part of the command line 
            taggedobject = self.getTaggedParam(meta,tagid)
            if (taggedobject._paramType=='FILE') and (taggedobject._ioType=='INPUT'):
                inputFiles.append(val)
                command += ' '+taggedobject._tag+separator+os.path.basename(val)
            else:
                #this is not an input file handle normally
                command += ' '+taggedobject._tag+separator+val
        for (tagid,val) in untaggedparams:
            #now let's see the untagged part of the command line
            #match id to ioType
            #  if input, determine if file or string
            #  if output, just put the string
            untaggedobject = self.getUntaggedParam(meta,tagid)
            if (untaggedobject._paramType=='FILE') and (untaggedobject._ioType=='INPUT'):
                inputFiles.append(val)
                command += ' '+os.path.basename(val)
            else:
                command += ' '+val
        print "Going to execute command: " + command
        #common code
        if (localRun==False):
            #print "Local run is: " + str(localRun) + " running remotely"
            results = self.executeWebJob(url, command, inputFiles, None)
        else :
            results = self.executeLocal(url, command, inputFiles, executable)
        return results

    def getUntaggedParam(self,meta,tagid):
        """
        getUntaggedParam description:
        @input:
          -meta: application's metadata
          -tagid: id for parameter
        @output:
          -returns param object
        """
        untaggedlist = meta._types._untaggedParams._param
        for i in untaggedlist:
            if(i._id==tagid):
                return i
        return "NOT AN UNTAGGED PARAM"


    def getTaggedParam(self,meta,tagid):
        """
        getTaggedParam description:
        @input:
          -meta: application's metadata
          -tagid: id for parameter
        @output:
          -returns param object
        """
        taggedlist = meta._types._taggedParams._param
        for i in taggedlist:
            if(i._id==tagid):
                return i
        return "NOT AN UNTAGGED PARAM"


    def buildHash(self,meta,tagtype):
        """
        buildHash description:
        @input:
          -meta: application's metadata
          -id: an ID to use to know where to start building the hash
        @output:
          -returns hash[param_id] = param_tag
        """
        if(tagtype=='flags'):
            mylist = meta._types._flags._flag
        elif(tagtype=='taggedParams'):
            mylist = meta._types._taggedParams._param
        myhash = {}
        for i in mylist:
            myhash[str(i._id)] = str(i._tag)
        return myhash

    def launchBasicJob(self,url,commandline,inFilesPath,numProcs=None,localRun=False,executable=''):
        """
        launchBasicJob description:
        @input:
          -url: for application endpoint
          -inFilesPath: list of input files, an array of strings containing the paths
        """
        if (localRun==False):
            results = self.executeWebJob(url, commandline, inFilesPath, numProcs)
        else :
            #local execution do not support number of cpu
            results = self.executeLocal(url, commandline, inFilesPath, executable)
        return results


    def executeWebJob(self, url, commandline, inFilesPath, numProcs):
        """ 
            executeWebJob description:
            it execute a job through OpalInterface
            @input:
                -url: the url where to reach the Opal service
                -commandline the command line to use for the execution
                -inputFiles an array of input file to upload, it should contains an array of string with the path to the file
                -numProcs the number of processors to use
        """
        inputFiles = []
        for i in inFilesPath:
            inputFile = ns0.InputFileType_Def('inputFile')
            inputFile._name = os.path.basename(i)
            infile = open(i, "r")
            infileString = infile.read()
            infile.close()
            inputFile._contents = infileString
            inputFiles.append(inputFile)
        appLocator = AppServiceLocator()
        appServicePort = appLocator.getAppServicePort(url)
        req = launchJobRequest()
        req._argList = commandline
        req._inputFile = inputFiles
        req._numProcs = numProcs
        resp = appServicePort.launchJob(req)
        jobID = resp._jobID
        status = resp._status._code
        while(status!=4 and status!=8):
            status = appServicePort.queryStatus(queryStatusRequest(jobID))._code
            if self.vpe.updateGuiCycle() is False:
                status = 4
        if(status==8):
            #Job completed successfully
            resp = appServicePort.getOutputs(getOutputsRequest(jobID))
            outurls = [str(resp._stdOut),str(resp._stdErr)]
            if(resp._outputFile!=None):
                for i in resp._outputFile:
                    outurls.append(str(i._url))
        else:
            #Job died or something else went wrong
            resp = appServicePort.getOutputs(getOutputsRequest(jobID))
            outurls = [str(resp._stdOut),str(resp._stdErr)]
        return tuple(outurls)


    def executeLocal(self, url, command, inputFiles, executable):
        """
            executeLocal description:
            this functions is used to exectute a job on the local machine
            @input:
                -url: the url where to reach the Opal service
                -commandline the command line to use for the execution
                -inputFiles an array of input file to upload to the server (array of strings path)
                -numProcs the number of processors to use
        """
        #setting up workind dir and input files
        #workingDir = os.tempnam()
        workingDir = tempfile.mkdtemp()
        print "the temporary directory is: " + workingDir
        #workingDir = workingDir + '/app' + str(int(time.time()*100 ))
        #os.mkdir(workingDir)
        for i in inputFiles:
            shutil.copy(i,workingDir)
        #setting up input and error file
        output = open(workingDir + os.sep + 'stdout.txt', 'w')
        error = open(workingDir + os.sep + 'stderr.txt', 'w')
        #working directory
        cwd = os.getcwd()
        os.chdir(workingDir)
        #environmental variables
        pythonpath = os.getenv('PYTHONPATH')
        pythonhome = os.getenv('PYTHONHOME')
        pathorig = os.getenv('PATH')
        if ( pathorig.partition(':')[0].find('MGL') ): # there is the MGL python let's remove it
            os.putenv('PATH',pathorig.partition(':')[2])
        os.unsetenv('PYTHONPATH')
        os.unsetenv('PYTHONHOME')
        cmdExec=executable + ' ' + command
        #print 'going to exectute: ' + cmdExec + ' with input files: ' + str(inputFiles)
        p = subprocess.Popen(cmdExec.split(), stdout=output, stderr=error)
        while p.poll() == None:
            self.vpe.updateGuiCycle()
            time.sleep(0.5)
        #job finished cleaning up 
        #files
        output.close()
        error.close()
        #evironment variables
        if pythonpath != None:
            os.putenv('PYTHONPATH', pythonpath)
        if pythonhome != None:
            os.putenv('PYTHONHOME', pythonhome)
        os.putenv('PATH', pathorig)
        #going back to previous working dir
        os.chdir(cwd)
        outputFiles=[]
        for i in os.listdir(workingDir):
            #outputFiles.append('file://' + workingDir + '/' + i)
            outputFiles.append(workingDir +  os.sep + i)
        return outputFiles



