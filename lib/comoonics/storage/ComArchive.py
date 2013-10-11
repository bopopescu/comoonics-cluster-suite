"""Comoonics archive module


here should be some more information about the module, that finds its way inot the onlinedoc

"""

# here is some internal information
# $Id $
#


__version__ = "$Revision: 1.5 $"
# $Source: /atix/ATIX/CVSROOT/nashead2004/management/comoonics-clustersuite/python/lib/comoonics/storage/ComArchive.py,v $

import os
import shutil
import tempfile
from xml.dom import Node

import tarfile
from tarfile import TarInfo

from comoonics import ComSystem
from comoonics.ComDataObject import DataObject
from comoonics import ComLog
from comoonics.ComExceptions import ComException
from comoonics.ComProperties import Properties


__all__ = ["Archive", "ArchiveHandlerFactory", "ArchiveHandler"]

class ArchiveException(ComException):pass

class Archive(DataObject):
   log=ComLog.getLogger("comoonics.ComArchive.Archive")
   '''
   Internal Exception classes
   '''
   class ArchiveException(ComException): pass

   '''
   Interface/Wrapper class for all archiv handler
   provides methods to access archives
   method types are
      - get/addDOMElement:   get and store DOMElements in Archive
      - getFileObj:         get FileObjects from Archive
      - extract/addFile:     extract and store file/directory in Archive
   IDEA: define iterator class to walk though DOMElements defined as ArchiveChild
      - has/getNextFileInfo   returns a XML defined FileInfo to work with
   '''

   __logStrLevel__ = "Archive"
   ''' Static methods '''

   def __init__(self, element, doc):
      super(Archive, self).__init__(element, doc)
      Archive.log.debug("getArchiveHandler(%s, %s, %s, %s, %s)" %(self.getAttribute("name"), self.getAttribute("format"), \
          self.getAttribute("type"), self.getAttribute("compression", default="none"), self.getProperties()))
      self.ahandler=ArchiveHandlerFactory.getArchiveHandler \
         (self.getAttribute("name"), self.getAttribute("format"), \
          self.getAttribute("type"), self.getAttribute("compression", default="none"), self.getProperties())
      self.child=self.element.firstChild

   def closeAll(self):
      ''' closes all open fds '''
      self.ahandler.closeAll()

   def getDOMElement(self, name):
      '''returns a DOM Element from the given member name'''
      from comoonics import XmlTools
      file=self.ahandler.getFileObj(name)
      doc=XmlTools.parseXMLFP(file)
      self.ahandler.closeAll()
      return doc.documentElement

   def getNextDOMElement(self):
      ''' returns a DOM representation of the next defined file
         <file name="filename.xml"/>
      '''
      from comoonics import XmlTools
      file=self.getNextFileObj()
      # there is no nextElement
      if file == None:
         return None

      doc=XmlTools.parseXMLFP(file)
      self.ahandler.closeAll()
      return doc.documentElement


   def addNextDOMElement(self, element):
      """ adds this element to the next file element in this archive """
      self.addDOMElement(element)

   def addDOMElement(self, element, name=None):
      '''adds an DOM Element as member name'''
      from comoonics import XmlTools
      if name == None:
         name=self.getNextFileName()
      fd, path = tempfile.mkstemp()
      file = os.fdopen(fd, "w")
      XmlTools.toPrettyXMLFP(element, file)
      file.close()
      try:
         self.ahandler.addFile(path, name)
         os.unlink(path)
      except Exception, e:
         os.unlink(path)
         ComLog.debugTraceLog(Archive.log)
         raise e

   def getFileObj(self, name):
      ''' returns a fileobject of an archiv member '''
      return self.ahandler.getFileObj(name)

   def getNextFileName(self):
      """ returns the name of the next file in the archive as stated by the file element """
      while self.child != None:
         # This is not an element
         if self.child.nodeType != Node.ELEMENT_NODE:
            self.child=self.child.nextSibling
            continue
         # This is not a file
         if self.child.tagName != "file":
            self.child=self.child.nextSibling
            continue
         else:
            break
      # there is no other child
      if self.child == None:
         return None
      filename=self.child.getAttribute("name")
      self.child=self.child.nextSibling
      return filename

   def getNextFileObj(self):
      ''' returns a fileobject of the next defined file
         <file name="filename.xml"/>
      '''
      file = self.getFileObj(self.getNextFileName())
      return file


   def addFile(self, name, arcname=None, recursive=True):
      ''' appends a file or dirctory to archiv'''
      self.ahandler.addFile(name, arcname, recursive)

   def extractFile(self, name, dest):
      ''' extracts a file or directory from archiv' to destination dest '''
      self.ahandler.extractFile(name, dest)

   def createArchive(self, source, cdir=None):
      ''' creates an archive from the whole source tree '''
      Archive.log.debug("createArchive(%s, %s)" % (source, cdir))
      self.ahandler.createArchive(source, cdir)

   def extractArchive(self, dest):
      ''' extracts the whole archive to dest'''
      self.ahandler.extractArchive(dest)

   def getMemberInfo(self, name):
      ''' returns a memberinfo object of an archiv menber '''
      pass

   def hasMember(self, name):
      ''' checks wether archive hosts member file
         returns True/False
      '''
      return self.ahandler.hasMember(name)


class ArchiveMemberInfo(DataObject, TarInfo):
   ''' Member of an Archivee'''
   pass

#FIXME: methods should rais a kind of NotImlementedError by default
class ArchiveHandler(object):
   ''' Baseclass for archiv handlers'''
   NONE="none"

   FORMAT=NONE
   COMPRESSION=NONE
   TYPE=NONE

   __logStrLevel__ = "ArchiveHandler"

   def __init__(self, name, properties=None):
      if type(properties)==dict:
         properties=Properties(**properties)
      self.name=name
      self.properties=properties

   def closeAll(self):
      pass

   def getProperties(self):
      return self.properties

   def getFileObj(self, name):
      ''' returns a fileobject of an archiv member '''
      pass

   def addFile(self, name, arcname=None, recursive=True):
      ''' appends a file or dirctory to archiv'''
      pass

   def extractFile(self, name, dest):
      ''' extracts a file or directory from archiv' to destination dest '''
      pass

   def createArchive(self, source, cdir):
      ''' creates an archive from the whole source tree
         if cdir is defined, archive handler will first change
         into cdir directory
      '''
      pass

   def extractArchive(self, dest):
      ''' extracts the whole archive to dest'''
      pass

   def getMemberInfo(self, name):
      ''' returns a memberinfo object of an archiv menber '''
      pass

   def hasMember(self, name):
      ''' checks wether archive hosts member file
         returns True/False
      '''
      pass

   def __niy(self):
      ''' default behavior is NotImplementedError '''
      raise NotImplementedError()

'''
Archive Handlers
'''


''' ArchiveeHandler for tar files '''
class TarArchiveHandler(ArchiveHandler):
   FORMAT="tar"
   TYPE="file"
   TAR="/bin/tar"

   def __init__(self, name, properties=None):
      super(TarArchiveHandler, self).__init__(name, properties)
      self.tarfile=name
      self.compression=""
      self.compressionmode=""

   def getCommandOptions(self):
      """
      Returns the options for the tar command and also the supported options. Xattrs, selinux, acls
      """
      _opts=[]

      if self.getProperties():
         for _property in self.getProperties().keys():
            _value=self.getProperties()[_property].getValue()
            if _value=="":
               if len(_property)==1:
                  _opts.append("-%s" %_property)
               else:
                  _opts.append("--%s" %_property)
            else:
               if len(_property)==1:
                  _opts.append("-%s %s" %(_property, _value))
               else:
                  _opts.append("--%s %s" %(_property, _value))
      return _opts

   def closeAll(self):
      ''' closes all open fds '''
      self.tarf.close()

   def getFileObj(self, name):
      ''' returns a fileobject of an archiv member '''
      self.tarf=tarfile.open(self.tarfile, "r"+self.compressionmode)
      file=self.tarf.extractfile(os.path.normpath(name))
      return file

   def extractFile(self, name, dest):
      ''' extracts a file or directory from archiv' to destination dest '''
      __cmd = TarArchiveHandler.TAR +" "+" ".join(self.getCommandOptions())+" -x " + self.compression + " -f " \
            + self.tarfile + " -C " + dest + " " + name
      __rc, __rv = ComSystem.execLocalGetResult(__cmd)
      if __rc >> 8 != 0:
         raise RuntimeError("running %s failed" %__cmd)

   def addFile(self, name, arcname=None, recursive=True):
      ''' appends a file or dirctory to archiv'''
      try:
         tarf=tarfile.open(self.tarfile, "a:"+self.compressionmode)
      except IOError:
         tarf=tarfile.open(self.tarfile, "w:"+self.compressionmode)
      except tarfile.ReadError:
         tarf=tarfile.open(self.tarfile, "w:"+self.compressionmode)
      tarf.add(os.path.normpath(name), os.path.normpath(arcname), recursive)
      tarf.close()


   def createArchive(self, source, cdir=None):
      ''' creates an archive from the whole source tree
         stays in the same filesystem
       '''
      if not cdir:
         cdir=os.getcwd()
      __cmd = TarArchiveHandler.TAR +" "+" ".join(self.getCommandOptions())+" -c --one-file-system " + self.compression + " -f " \
            + self.tarfile + " -C " + cdir + " " + source
      __rc, __rv = ComSystem.execLocalGetResult(__cmd)
      if __rc >> 8 != 0:
         raise RuntimeError("running %s failed" %__cmd)


   def extractArchive(self, dest):
      ''' extracts the whole archive to dest'''
      self.extractFile("", dest)


   def hasMember(self, name):
      ''' checks if archive has a member named name '''
      tarf = tarfile.open(self.tarfile, "r"+self.compressionmode)
      try:
         tarf.getmember(os.path.normpath(name))
         tarf.close()
      except KeyError:
         tarf.close()
         return False
      return True


''' Archive Handler for gzip compressed tar files '''
class TarGzArchiveHandler(TarArchiveHandler):
   COMPRESSION="gzip"
   def __init__(self, name, properties=None):
      TarArchiveHandler.__init__(self, name, properties)
      self.compression="-z "
      self.compressionmode=":gz"


''' Archive Handler for bzip2 compressed tar files '''
class TarBz2ArchiveHandler(TarArchiveHandler):
   COMPRESSION="bz2"
   def __init__(self, name, properties=None):
      TarArchiveHandler.__init__(self, name, properties)
      self.compression="-j "
      self.compressionmode=":bz2"


''' Simple Archive Handler - uses local file system '''
class SimpleArchiveHandler(ArchiveHandler):
   FORMAT="simple"
   TYPE="file"
   def __init__(self, name, properties=None):
      ArchiveHandler.__init__(self, name, properties)
      self.path="/tmp/" + name
      if os.path.exists(self.path) and not os.path.isdir(self.path):
         raise ArchiveException("Path %s already exists" %(self.path))

   def hasMember(self, name):
      return os.path.exists(self.path+"/"+name)

   def extractFile(self, name, dest):
      ''' extracts a file or dirctory from archiv'''
      try:
         os.mkdir(dest+"/"+os.path.dirname(name))
      except: pass
      shutil.copy2(self.path+"/"+name, dest+"/"+os.path.dirname(name))

   def getFileObj(self, name):
      ''' returns a fileobject of an archiv member '''
      try:
         Archive.log.debug("open(%s)" %(self.path+"/"+name))
         file = open(self.path+"/"+name, "r")
      except:
         raise ArchiveException("Cannot open %s." %(self.path+"/"+name))
      return file

   def addFile(self, name, arcname=None,recursive=True):
      ''' adds a file or directory to archiv'''
      try:
         os.mkdir(self.path+"/"+os.path.dirname(name))
      except: pass
      shutil.copy2(name, self.path+"/"+arcname)

   def createArchive(self, source, cdir=None):
      ''' creates an archive from the whole source tree
         stays in the same filesystem
         @source: is the sourcedirectory to copy from
         @cdir:   is a chdir directory to change to
       '''
#      try:
#         os.mkdir(self.path+"/"+os.path.dirname(cdir))
#      except: pass
      if cdir !=None:
         Archive.log.debug("changing to directory "+cdir)
         os.chdir(cdir)
      Archive.log.debug("Copy from "+source+" to "+self.path+"/")
      shutil.copytree(source, self.path+"/")


class IncompatibleArchiveHandlerClass(ComException):
   def __str__(self):
      return "The Class "+self.value.__name__+" is incompatible to register to ArchiveHandlerFactory"

''' Factory class for ArchiveHandler '''
class ArchiveHandlerFactoryClass:
   """
   Factory for different archive type handlers
   """

   '''
   Internal Exception classes
   '''

   __logStrLevel__ = "ArchiveHandlerFactory"
   log=ComLog.getLogger("comoonics.ComArchive.ArchiveHandlerFactory")

   """ The static registry for all registered handlers """
   _registry=dict()

   def __init__(self):
      """
      Default constructor that pre registers all default classes
      """
      self.registerArchiveHandler(SimpleArchiveHandler)
      self.registerArchiveHandler(TarArchiveHandler)
      self.registerArchiveHandler(TarGzArchiveHandler)
      self.registerArchiveHandler(TarBz2ArchiveHandler)

   def registerArchiveHandler(self, theclass):
      if type(theclass)!=type:
         raise IncompatibleArchiveHandlerClass(theclass)
      instance=object.__new__(theclass)
      if not isinstance(instance, ArchiveHandler):
         raise IncompatibleArchiveHandlerClass(theclass)
      #self.log.debug("ComArchive.registerArchiveHandler(%s)" %(theclass))
      if not self._registry.has_key(theclass.FORMAT):
         self._registry[theclass.FORMAT]=dict()
      if not self._registry[theclass.FORMAT].has_key(theclass.TYPE):
         self._registry[theclass.FORMAT][theclass.TYPE]=dict()
      self._registry[theclass.FORMAT][theclass.TYPE][theclass.COMPRESSION]=theclass

   def getArchiveHandler(self, name, hndlrformat, hndlrtype=ArchiveHandler.NONE, compression=ArchiveHandler.NONE, properties=None):
      """
      Returns the handler registered for the given format and type combination
      """
      if self._registry.has_key(hndlrformat) and \
         self._registry[hndlrformat].has_key(hndlrtype) and \
         self._registry[hndlrformat][hndlrtype].has_key(compression):
         instance=object.__new__(self._registry[hndlrformat][hndlrtype][compression])
         instance.__init__(name, properties)
         return instance
      else:
         raise ArchiveException("No ArchiveHandler found for %s, %s, %s, %s" %(name, hndlrformat, hndlrtype, compression))

   def listArchiveHandlerNames(self):
      """
      Returns a list of names of all registered archive handlers.
      """
      return self._registry.keys()

   def listArchiveHandlers(self):
      """
      Returns a list of all registered archive handlers.
      """
      return self._registry.values()
   
   def __str__(self):
      return "%s" %(self._registry)

"""
The ArchiveHandlerFactory
Concept:
Is a static reference to ArchiveHandlerFactoryClass that holds registered ArchiveImplementations.
Every Implementation registers with a formatname and other optional Parameters like i.e. compression or type.
By default the following implementations are registered:
format     compression        Class
simple     "none"/None        SimpleArchiveHandler
tar       "none"/None        TarArchiveHandler
tar       "gzip"            TarGzArchiveHandler
tar       "bz2"            TarBz2ArchiveHandler

otherwise it raises an ArchiveException("No ArchiveHandler found for %s" %(format))

New handler should best register in their automatically executed __init__.py Module of their module
with given format, [type] and [compression] if needed.. I.e.
__init.py__:
ArchiveHandler.registerArchiveHandler(handlerClass)
format, type, compression are defined in the class itself over the static attributes:
FORMAT, TYPE, COMPRESSION
all default to NONE
"""
global ArchiveHandlerFactory
ArchiveHandlerFactory=ArchiveHandlerFactoryClass()
