""" Comoonics copy object module


here should be some more information about the module, that finds its way inot the onlinedoc

"""

# here is some internal information
# $Id: ComCopyObject.py,v 1.10 2011-02-15 14:52:47 marc Exp $
#


__version__ = "$Revision: 1.10 $"
# $Source: /atix/ATIX/CVSROOT/nashead2004/management/comoonics-clustersuite/python/lib/comoonics/enterprisecopy/ComCopyObject.py,v $

from comoonics.ComDataObject import DataObject
from comoonics.ComExceptions import ComException
from comoonics.ecbase.ComJournaled import JournaledObject
from comoonics import ComLog
from ComRequirement import Requirements

from xml.dom import Node

class UnsupportedCopyObjectException(ComException): pass
class UnsupportedMetadataException(ComException): pass

#def getCopyObject(element, doc):
#    """ Factory function to create Copy Objects"""
#    __type=element.getAttribute("type")
#    #print "getCopyObject(%s)" %(element.tagName)
#    if __type == "filesystem":
#        from ComFilesystemCopyObject import FilesystemCopyObject
#        return FilesystemCopyObject(element, doc)
#    elif __type == "lvm":
#        from ComLVMCopyObject import LVMCopyObject
#        return LVMCopyObject(element, doc)
#    elif __type == "backup":
#        from ComArchivCopyObject import ArchivCopyObject
#        return ArchivCopyObject(element, doc)
#    else:
#        raise UnsupportedCopyObjectException("Unsupported CopyObject type %s in element %s" % (__type, element.tagName))

_copyobject_registry=dict()

def registerCopyObject(_type, _class):
    _copyobject_registry[_type]=_class

def getCopyObject(element, doc):
    """ Factory function to create Copyset Objects"""
    if isinstance(element, Node):
        __type=element.getAttribute("type")
        #print "getCopyObject(%s)" %(element.tagName)
        if __type == "disk":
            from ComPartitionCopyObject import PartitionCopyObject
            cls=PartitionCopyObject
        elif __type == "filesystem":
            from ComFilesystemCopyObject import FilesystemCopyObject
            cls=FilesystemCopyObject
        elif __type == "lvm":
            from ComLVMCopyObject import LVMCopyObject
            cls=LVMCopyObject
        elif __type == "backup":
            from ComArchiveCopyObject import ArchiveCopyObject
            cls=ArchiveCopyObject
        elif _copyobject_registry.has_key(__type):
            cls=_copyobject_registry[__type]
            #from ComPathCopyObject import PathCopyObject
            #cls=PathCopyObject
        else:
            raise UnsupportedCopyObjectException("Unsupported CopyObject type %s in element %s" % (__type, element.tagName))
        ComLog.getLogger(CopyObject.__logStrLevel__).debug("Returning new object %s" %(cls))
        return cls(element, doc)
    else:
        raise UnsupportedCopyObjectException("Wrong parameters passed to factory method getCopyObject. Expected element, doc.")

class CopyObject(DataObject, Requirements):
    """ Base Class for all source and destination objects"""
    __logStrLevel__ = "comoonics.enterprisecopy.ComCopyObject.CopyObject"

    def __init__(self, element, doc):
        DataObject.__init__(self, element, doc)
        Requirements.__init__(self, element, doc)

    def prepareAsSource(self):
        ''' prepare CopyObject as source '''
        pass

    def cleanupSource(self):
        ''' do source specific cleanup '''
        pass

    def cleanupDest(self):
        ''' do destination specific cleanup '''
        pass

    def prepareAsDest(self):
        ''' prepare CopyObject as destination '''
        pass

    def getMetaData(self):
        ''' returns the metadata element '''
        pass

    def updateMetaData(self, element):
        ''' updates meta data information '''
        pass


class CopyObjectJournaled(CopyObject, JournaledObject):
    """
    Derives anything from Copyset plus journals all actions.
    Internally CopysetJournaled has a map of undomethods and references to objects that methods should be executed upon.
    If undo is called the journal stack is executed from top to buttom (LIFO) order.
    """
    __logStrLevel__ = "CopysetJournaled"

    def __init__(self, element, doc):
        CopyObject.__init__(self, element, doc)
        JournaledObject.__init__(self)
        self.__journal__=list()
        self.__undomap__=dict()

    def cleanup(self):
        """
        just calls replayJournal
        """
        self.replayJournal()
# $Log: ComCopyObject.py,v $
# Revision 1.10  2011-02-15 14:52:47  marc
# - changes for ecbase rebase to comoonics.ecbase package
#
# Revision 1.9  2010/03/08 12:30:48  marc
# version for comoonics4.6-rc1
#
# Revision 1.8  2008/03/12 09:40:53  marc
# support for a more general constructor
#
# Revision 1.7  2007/09/07 14:35:33  marc
# added registry implementation for all sets.
#
# Revision 1.6  2007/03/26 07:52:25  marc
# added Requirements for CopyObjects
#
# Revision 1.5  2006/12/08 09:38:36  mark
# added support for PartitionCopyObject
#
# Revision 1.4  2006/11/27 09:47:17  mark
# some fixes
#
# Revision 1.3  2006/11/24 11:12:19  mark
# added getMetaData
# added updateMetaData
# added __new__
#
# Revision 1.2  2006/11/23 14:14:45  marc
# removed factory method
#
# Revision 1.1  2006/07/19 14:29:15  marc
# removed the filehierarchie
#
# Revision 1.3  2006/07/06 11:53:43  mark
# added class CopyObjectJournaled
#
# Revision 1.2  2006/06/29 13:52:49  marc
# added lvm stuff
#
# Revision 1.1  2006/06/28 17:25:16  mark
# initial checkin (stable)
#