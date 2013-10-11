"""Comoonics mountpoint module

here should be some more information about the module, that finds its way inot the onlinedoc

"""


# here is some internal information
# $Id: ComMountpoint.py,v 1.2 2010-02-09 21:48:51 mark Exp $
#


__version__ = "$Revision: 1.2 $"
# $Source: /atix/ATIX/CVSROOT/nashead2004/management/comoonics-clustersuite/python/lib/comoonics/storage/ComMountpoint.py,v $


import xml.dom
from comoonics.ComDataObject import  DataObject

class MountPoint(DataObject):
    TAGNAME="mountpoint"
    def __init__(self, element, doc):
        DataObject.__init__(self, element, doc)

    def getOptionsString(self):
        __opts="-o "
        __attr=self.getElement().getElementsByTagName("option")
        if not (__attr.length):
            return __opts + "defaults"
        for i in range(__attr.length):
            __opts+=__attr.item(i).getAttribute("name")
            if __attr.item(i).hasAttribute("value"):
                __opts+="="
                __opts+=__attr.item(i).getAttribute("value")
            if i+1 < __attr.length:
                __opts+=","
        return __opts
