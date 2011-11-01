"""Comoonics copyset module


here should be some more information about the module, that finds its way inot the onlinedoc

"""

# here is some internal information
# $Id: ComCopyset.py,v 1.8 2011-02-15 14:52:47 marc Exp $
#


__version__ = "$Revision: 1.8 $"
# $Source: /atix/ATIX/CVSROOT/nashead2004/management/comoonics-clustersuite/python/lib/comoonics/enterprisecopy/ComCopyset.py,v $

from xml.dom import Node

from comoonics.ComDataObject import DataObject
from comoonics.ecbase.ComJournaled import JournaledObject
from comoonics.enterprisecopy.ComRequirement import Requirements

_copyset_registry=dict()

def registerCopyset(_type, _class):
    _copyset_registry[_type]=_class

def getCopyset(element, doc):
    """ Factory function to create Copyset Objects"""
    if isinstance(element, Node):
        __type=element.getAttribute("type")
        if not __type:
            raise AttributeError("Attribute @type is not defined in element %s." %element.getAttribute("name"))
        if __type == "partition":
            from ComPartitionCopyset import PartitionCopyset
            cls=PartitionCopyset
        elif __type == "lvm":
            from ComLVMCopyset import LVMCopyset
            cls=LVMCopyset
        elif __type == "filesystem":
            from ComFilesystemCopyset import FilesystemCopyset
            cls=FilesystemCopyset
        elif __type == "bootloader":
            from ComBootloaderCopyset import BootloaderCopyset
            cls=BootloaderCopyset
        elif __type=="storage":
            from comoonics.enterprisecopy.ComStorageCopyset import StorageCopyset
            cls=StorageCopyset
        elif _copyset_registry.has_key(__type):
            cls=_copyset_registry[__type]
        else:
            raise NotImplementedError("Copyset class of type %s is not yet implemented and cannot be instantiated." %(__type))
        return cls(element, doc)
    return Copyset(element, doc)

class Copyset(DataObject, Requirements):
    __logStrLevel__ = "comoonics.enterprisecopy.ComCopyset.Copyset"
    TAGNAME = "copyset"
    def __init__(self, element, doc):
        DataObject.__init__(self, element, doc)
        Requirements.__init__(self, element, doc)

    def doCopy(self):
        """starts the copy process"""
        pass

    def undoCopy(self):
        """ Tries to undo the copy if implemented"""
        pass

    def getSource(self):
        """returns the Source Object"""
        pass

    def getDestination(self):
        """ returns the Destination Object"""
        pass

    def doPre(self):
        super(Copyset, self).doPre()
        if self.getSource():
            self.getSource().doPre()

    def doPost(self):
        super(Copyset, self).doPost()
        if self.getDestination():
            self.getDestination().doPost()

class CopysetJournaled(Copyset, JournaledObject):
    """
    Derives anything from Copyset plus journals all actions.
    Internally CopysetJournaled has a map of undomethods and references to objects that methods should be executed upon.
    If undo is called the journal stack is executed from top to buttom (LIFO) order.
    """
    __logStrLevel__ = "comoonics.enterprisecopy.ComCopyset.CopysetJournaled"

    def __init__(self, element, doc):
        Copyset.__init__(self, element, doc)
        JournaledObject.__init__(self)
        self.__journal__=list()
        self.__undomap__=dict()

    def undoCopy(self):
        """
        just calls replayJournal
        """
        self.replayJournal()

# $Log: ComCopyset.py,v $
# Revision 1.8  2011-02-15 14:52:47  marc
# - changes for ecbase rebase to comoonics.ecbase package
#
# Revision 1.7  2010/03/29 14:09:53  marc
# - extended error handling
#
# Revision 1.6  2010/03/08 12:30:48  marc
# version for comoonics4.6-rc1
#
# Revision 1.5  2008/03/12 09:41:25  marc
# support for a more general constructor
#
# Revision 1.4  2007/09/07 14:36:07  marc
# -added registry implementation.
# -logging
#
# Revision 1.3  2007/03/26 07:53:09  marc
# added Requirements
#
# Revision 1.2  2007/02/09 12:24:13  marc
# added new method and Storage Copyset
#
# Revision 1.1  2006/07/19 14:29:15  marc
# removed the filehierarchie
#
# Revision 1.4  2006/06/30 12:39:46  marc
# added TAGNAME
#
# Revision 1.3  2006/06/30 08:29:51  marc
# added undoCopy method to Copyset
# added CopysetJournaled
#
# Revision 1.2  2006/06/29 13:49:47  marc
# added LVM stuff.
#
# Revision 1.1  2006/06/28 17:25:16  mark
# initial checkin (stable)
#