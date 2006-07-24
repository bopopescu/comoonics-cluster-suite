""" Comoonics partition copyset module


here should be some more information about the module, that finds its way inot the onlinedoc

"""


# here is some internal information
# $Id: ComPartitionCopyset.py,v 1.2 2006-07-20 10:25:10 mark Exp $
#


__version__ = "$Revision: 1.2 $"
# $Source: /atix/ATIX/CVSROOT/nashead2004/management/comoonics-clustersuite/python/lib/comoonics/enterprisecopy/ComPartitionCopyset.py,v $

import os
import re
import xml.dom
import exceptions
from xml import xpath

from ComCopyset import *
from comoonics.ComDisk import Disk
from comoonics.ComExceptions import *
from comoonics import ComSystem

class PartitionCopyset(CopysetJournaled):
    def __init__(self, element, doc):
        CopysetJournaled.__init__(self, element, doc)
        try:
            __source=xpath.Evaluate('source/disk', element)[0]
            self.source=Disk(__source, doc)
        except Exception:
            raise ComException("source for copyset not defined")
        try:
            __dest=xpath.Evaluate('destination/disk', element)[0]
            self.destination=Disk(__dest, doc)
        except Exception:
            raise ComException("destination for copyset not defined")
        self.addToUndoMap(self.source.__class__.__name__, "savePartitionTable", "restorePartitionTable")
        self.addToUndoMap(self.source.__class__.__name__, "noPartitionTable", "deletePartitionTable")
        
    def doCopy(self):
        __tmp=os.tempnam("/tmp")
        if not self.needPartitionTableUpdate():
            ComLog.getLogger("Copyset").debug("partition tables are the same. No need to update")
        else:
            if self.destination.hasPartitionTable():
                self.destination.savePartitionTable(__tmp)
                self.journal(self.destination, "savePartitionTable", __tmp)
            else:
                self.journal(self.destination, "noPartitionTable")
            if self.source.hasPartitionTable():
                __cmd = self.source.getDumpStdout() 
                __cmd += " | "
                __cmd += self.destination.getRestoreStdin(True)
                __rc, __ret = ComSystem.execLocalStatusOutput(__cmd)
                ComLog.getLogger("Copyset").debug(__cmd + ": " + __ret)
                if __rc != 0:
                    raise ComException(__cmd + __ret)
            else:
                if not self.destination.deletePartitionTable():
                    raise ComException("Partition table on device %s coud not be deleted", 
                                       self.destination.getDeviceName())
    
    def needPartitionTableUpdate(self):
        """ compares the partition tables of source and destination
        returns True if they are not the same """
        n_table=list()
        d_table=self.destination.getPartitionTable()
        s_table=self.source.getPartitionTable()
        for i in range(len(s_table)):
            n_table.append(re.sub(self.source.getDeviceName(), \
                                  self.destination.getDeviceName(), \
                                  s_table[i]))
        if d_table == n_table:
            return False
        else: 
            return True
        

# $Log: ComPartitionCopyset.py,v $
# Revision 1.2  2006-07-20 10:25:10  mark
# added check for update
#
# Revision 1.1  2006/07/19 14:29:15  marc
# removed the filehierarchie
#
# Revision 1.4  2006/07/05 12:30:02  mark
# added --force to partition copy
#
# Revision 1.3  2006/07/03 14:32:38  mark
# added undo
#
# Revision 1.2  2006/07/03 09:28:17  mark
# added support for empty partition tables
#
# Revision 1.1  2006/06/28 17:25:16  mark
# initial checkin (stable)
#