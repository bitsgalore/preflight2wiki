#! /usr/bin/env python3

# Analyse user-defined set of PDF documents with Apache Preflight and return results
# as formatted table in Markdown (PHP Extra) or Atlassian Confluence Wiki format
# Johan van der Knijff, KB/ National Library of the Netherlands
#

import imp
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
import subprocess as sub
import argparse
from collections import defaultdict


def main_is_frozen():
    return (hasattr(sys, "frozen") or # new py2exe
            hasattr(sys, "importers") # old py2exe
            or imp.is_frozen("__main__")) # tools/freeze
    
def get_main_dir():
    if main_is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(sys.argv[0])

def errorExit(msg):
    msgString=("ERROR: " +msg + "\n")
    sys.stderr.write(msgString)
    sys.exit()
    
def checkFileExists(fileIn):
    # Check if file exists and exit if not
    if os.path.isfile(fileIn)==False:
        msg=fileIn + " does not exist!"
        errorExit(msg)

def url2FileName(url):

    # Parse URL for file name (only yields meaningful result if last part of url
    # points to file name)

    urlSplitted=url.split("/")
    urlElts=len(urlSplitted)
    name=urlSplitted[urlElts-1]
    return(name)

def getConfiguration(configFile):

    # What is the location of this script?
    appPath=os.path.abspath(get_main_dir())

    # Parse XML tree
    try:
        tree = ET.parse(configFile)
        config = tree.getroot()
    except Exception:
        msg="error parsing " + configFile
        errorExit(msg)
    
    # Locate configuration elements
    javaElement=config.find("java")
    
    # Get corresponding text values
    java=os.path.normpath(javaElement.text)
    preflightApp=addPath(appPath + "/preflight/","preflight-app.jar") # To config file!
    #probatronApp=addPath(appPath + "/probatron/","probatron.jar")
    probatronApp="dummy"
        
    # Check if all files exist, and exit if not
    checkFileExists(java)
    checkFileExists(preflightApp)
    #checkFileExists(probatronApp)
            
    return(java,preflightApp,probatronApp)
    
def launchSubProcess(systemString):
    # Launch subprocess and return exit code, stdout and stderr
    try:
        # Execute command line; stdout + stderr redirected to objects
        # 'output' and 'errors'.
        p = sub.Popen(systemString,stdout=sub.PIPE,stderr=sub.PIPE, shell=True)
        output, errors = p.communicate()
                
        # Decode to UTF8
        outputAsString=output.decode('utf-8')
        errorsAsString=errors.decode('utf-8')
                
        exitStatus=p.returncode
  
    except Exception:
        # I don't even want to to start thinking how one might end up here ...
        exitStatus=-99
        outputAsString=""
        errorsAsString=""
    
    return exitStatus,outputAsString,errorsAsString

def constructFileName(fileIn,pathOut,extOut,suffixOut):
    # Construct filename by replacing path by pathOut,
    # adding suffix and extension
    
    fileInTail=os.path.split(fileIn)[1]

    baseNameIn=os.path.splitext(fileInTail)[0]
    baseNameOut=baseNameIn + suffixOut + "." + extOut
    fileOut=addPath(pathOut,baseNameOut)

    return(fileOut)

def addPath(pathIn,fileIn):
    result=os.path.normpath(pathIn+ "/" + fileIn)
    return(result)

def parseCommandLine():
    # Create parser
    parser = argparse.ArgumentParser(description="Analyse PDFs at user-defined URLs and report results as Markdown table")
 
    # Add arguments
    parser.add_argument('fileIn', action="store", help="input file, each line contains URL that points to a PDF")
    parser.add_argument('outputMode', action="store", help="output mode, allowed values are 'markdown' or 'confluence'")
    
    # Parse arguments
    args=parser.parse_args()
    
    # Normalise all file paths
    args.fileIn=os.path.normpath(args.fileIn)
    
    return(args)
    
    
def downloadFile(url):

    # File name from URL (this will give unexpected results if URL calls cgi script!)
    fileName=url2FileName(url)
    
    # Open URL location, response to file-like object 'response'                            
    response = urllib.request.urlopen(url)

    # Output URL (can be different from inURL in case of redirection)
    outURL=response.geturl()
    
    # HTTP headers
    headers = response.info()
    
    # Data (i.e. the actual object that is retrieved)
    data = response.read()
        
    # Save to file using original name
    f = open(fileName, 'wb')
    f.write(data)
    f.close()
    
    return(fileName)
    
def runPreflight(file,java,preflightApp):
    
    # Construct name for output file
    fileOut = constructFileName(file,".","xml","")
     
    #Preflight command line
    preflightSysString = '"' + java + '"' + " -jar " + preflightApp + " xml " + '"' + file + '"'
        
    try:
        preflightExitStatus,preflightStdOut,preflightStdErr=launchSubProcess(preflightSysString)
        with open(fileOut, "w") as text_file:
            text_file.write(preflightStdOut)
    except:
        status="fail"
        description="Error running Preflight"
        errorExit(description)
    
    return(fileOut)
    
def getErrorsExceptions(preflightXML):
    
    # Parse Preflight's output and return all errors and exceptions as a dictionary
    
    errorsDictionary = defaultdict(list)
    exceptionsDictionary=defaultdict(list)
       
    # Parse preflight XML output and extract error messages
    try:
        tree=ET.parse(preflightXML)
        root = tree.getroot()
        errorsElt = root.find('errors')
        exceptionsElt = root.find('exceptionThrown')
        
        if exceptionsElt != None:
            # Loops over 'exceptionThrown' element
            for element in exceptionsElt:
                if element.tag == 'message':
                    message = element.text
                    exceptionsDictionary["Exception"].append(message)
        
        if errorsElt != None:
            # Loops over 'error' elements
            for element in errorsElt:
                # Loop over items within each 'error' element
                for subelement in element:
                    if subelement.tag == 'code':
                        code = subelement.text
                    elif subelement.tag == 'details':
                        details = subelement.text
                        
                # Error codes + details go to dictionary, so we can sort them later
                # Each item is a list, because each error code can have multiple occurrences with
                # different reported details
                               
                errorsDictionary[code].append(details)
                                        
    except:
        errorExit("Unexpected error: " + str(sys.exc_info()[0]))
      
    # Merge exceptions and errors dictionaries
    errorsExceptions = dict(list( errorsDictionary.items()) + list(exceptionsDictionary.items()))
    
    return(errorsExceptions)    

def errorsToMarkdown(file, url, errors):
    
    # Errors and exceptions as formatted table row using PHP Markdown Extra markup 
    #tableRow = "|[" + file + "](" + url + ")| |"
    tableRow = "|[" + file + "](" + url + ")|"
            
    for key in sorted(errors.keys()):
        noMessages=len(errors[key])
        for message in range(noMessages):
            # Escape any asterisks in output because they will mass up Markdown rendering
            messageCleaned=errors[key][message].replace('*','\*')
            tableRow += ("%s: %s" % (key, messageCleaned)) + "<br>"
        
    tableRow += "\n"
    
    return(tableRow)

def errorsToConfluence(file, url, errors):
    
    # Errors and exceptions as formatted table row using Confluence Wiki markup 
    #tableRow = "|[" + file + " |" + url + "]| |"
    tableRow = "|[" + file + " |" + url + "]|"
            
    for key in sorted(errors.keys()):
        noMessages=len(errors[key])
        for message in range(noMessages):
            messageCleaned=errors[key][message]
            tableRow += ("%s: %s" % (key, messageCleaned)) + " \\\\"
    tableRow += "\n"
    
    return(tableRow)
    
def main():

    # Get input from command line
    args=parseCommandLine()
    fileIn=args.fileIn
    outputMode=args.outputMode

    # Configuration

    # What is the location of this script/executable
    appPath=os.path.abspath(get_main_dir())
    
    # Configuration file
    configFile=os.path.abspath(appPath + "/config.xml")
        
    # Check if config file exists, and exit if not
    checkFileExists(configFile)
    
    # Get Java location from config file 
    java,preflightApp,probatronApp=getConfiguration(configFile)

    # I/O
    
    f = open(fileIn, 'r')
    urls=f.readlines()
    f.close()
    
    # Output table header rows
    
    if outputMode == "markdown":
        #tableHeader = "|Test file|Acrobat Preflight error(s)|Apache Preflight Error(s)|\n"
        #tableHeader += "|:---|:---|:---\n"
        tableHeader = "|File|Apache Preflight Error(s)|\n"
        tableHeader += "|:---|:---\n"
    elif outputMode == "confluence":
        #tableHeader = "|*Test file*|*Acrobat Preflight error(s)*|*Apache Preflight Error(s)*|\n"
        tableHeader = "|*File*|*Apache Preflight Error(s)*|\n"
    else:
        errorExit('Unknown output mode "'+ outputMode + '"')
    
    sys.stdout.write(tableHeader)
    
    for url in urls:
    
        #print(url)
        url=url.strip()
        
        # Retrieve file
        fileName = downloadFile(url)
  
        # Analyse file with Preflight
        namePreflight = runPreflight(fileName,java,preflightApp)
    
        # Process Preflight output
        errorsExceptions = getErrorsExceptions(namePreflight)

        # Results as formatted table row
        
        if outputMode == "markdown":
            tableRow = errorsToMarkdown(fileName, url, errorsExceptions)
        elif outputMode == "confluence":
            tableRow = errorsToConfluence(fileName, url, errorsExceptions)
   
        sys.stdout.write(tableRow)
          
main()