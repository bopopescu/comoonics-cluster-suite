"""Comoonics data object module


here should be some more information about the module, that finds its way inot the onlinedoc

"""


# here is some internal information
# $Id: ComDataObject.py,v 1.1 2006-07-19 14:29:15 marc Exp $
#


__version__ = "$Revision: 1.1 $"
# $Source: /atix/ATIX/CVSROOT/nashead2004/management/comoonics-clustersuite/python/lib/comoonics/ComDataObject.py,v $


import exceptions
import copy
import string
from xml.dom import Element, Node
from xml import xpath

import ComLog
from ComExceptions import *


class DataObject:
    TAGNAME="DataObject"
    __logStrLevel__ = "DataObject"

    '''
    static methods
    '''
    
    '''
    Public methods
    '''
    def __init__(self, element, doc=None):
        if element.hasAttribute("refid"):
            __newelement=self.searchReference(element, doc)
            element.parentNode.replaceChild(__newelement, element)
            self.element=__newelement
        else:
            self.element=element
        self.document=doc

    def getElement(self):
        return self.element

    def setElement(self, element):
        self.element=element

    def getDocument(self):
        return self.document

    def setDocument(self, doc):
        self.__dict__['document']=doc

    def getAttribute(self,name,default=None):
        if not self.__dict__.has_key('element') or not self.element.hasAttribute(name) and default:
            return default
        elif not self.__dict__.has_key('element') or not self.element.hasAttribute(name):
            raise exceptions.NameError("No attribute name " + name)
        return self.element.getAttribute(name)

    def hasAttribute(self, name):
        return self.element.hasAttribute(name)

    def setAttribute(self, name, value):
        if not self.element and not isinstance(Element, self.element):
            raise exceptions.IndexError("Element not defined or wrong instance.")
        self.element.setAttribute(name, str(value))

    def updateAttributes(self, frommap):
        '''
        Updates all attribute from frommap that are not already set
        
        frommap - the NamedNodeMap of attributes that are taken as source
        '''
        for i in range(len(frommap)):
            node=frommap.item(i)
            if not self.hasAttribute(node.nodeName) and node.nodeType == Node.ATTRIBUTE_NODE:
                self.getElement().setAttributeNode(node.cloneNode(True))

    def setAttributes(self, nodemap):
        for i in range(len(nodemap)):
            self.setAttribute(nodemap.item(i).nodeName, nodemap.item(i).nodeValue)

    def __copy__(self):
        class EmptyClass: pass
        obj = EmptyClass()
        obj.__class__ = self.__class__
        obj.__dict__.update(self.__dict__)
        return obj

    def __deepcopy__(self, memo):
        class EmptyClass: pass
        obj = EmptyClass()
        obj.__class__ = self.__class__
        obj.__dict__.update(self.__dict__)
        obj.element=self.element.cloneNode(True)
        obj.document=self.document
        return obj
 
    def __str__(self):
        '''
        Return all attributes of element to string
        '''
        str="Classtype: "+self.__class__.__name__+"\nTransient attributes: "
        for attr in self.__dict__.keys():
            str+="%s = %s, " % (attr, self.__dict__[attr])
        str+="\n"
        str+="Elementname: "+self.getElement().tagName
        str+=", persistent Attributes: "
        for i in range(len(self.getElement().attributes)):
            str+="%s = %s, " % (self.getElement().attributes.item(i).name, self.getElement().attributes.item(i).value)
        return str
    
    """
    Privat Methods
    """
    
    def searchReference(self, element, doc):    
        try:
            __xquery='//'
            __xquery+=element.tagName
            __xquery+='[@id="'
            __xquery+=element.getAttribute("refid")
            __xquery+='"]'
            # cloneNode to be safe 
            __element=xpath.Evaluate(__xquery, doc)[0]
            ComLog.getLogger("DataObject").debug("found refid " + \
                                                 element.getAttribute("refid")) 
            __childs=xpath.Evaluate('./*', element)
            __new=__element.cloneNode(True)
            self.appendChildren(__new, __childs)
            return __new 
        except exceptions.Exception:
            raise ComException("Element with id " + element.getAttribute("refid") \
                               + " not found. Query: " + __xquery)
                
    def appendChildren(self, element, nodelist):
        for i in range(len(nodelist)):
            element.appendChild(nodelist[i])
                
                
# $Log: ComDataObject.py,v $
# Revision 1.1  2006-07-19 14:29:15  marc
# removed the filehierarchie
#
# Revision 1.21  2006/07/05 13:06:20  marc
# added getAttribute with default
#
# Revision 1.20  2006/06/30 08:00:52  mark
# bugfixes in ref
#
# Revision 1.19  2006/06/29 13:49:10  marc
# bugfix in updateAttributes
#
# Revision 1.18  2006/06/29 10:38:11  mark
# bug fixes
#
# Revision 1.17  2006/06/29 10:22:48  mark
# bug fixes
#
# Revision 1.16  2006/06/29 09:27:23  mark
# made constructor more fancy
#
# Revision 1.15  2006/06/29 09:13:23  mark
# added support for reference refid attribute
#
# Revision 1.14  2006/06/29 08:44:20  marc
# added updateAttirbutes and minor changes.
#
# Revision 1.13  2006/06/28 17:24:23  mark
# added setAttribues method
#
# Revision 1.12  2006/06/28 13:40:33  marc
# added str() to any attribute value
#
# Revision 1.11  2006/06/27 16:06:28  marc
# changed functionality. Added get/setAttribute for persistent attributes.
#
# Revision 1.10  2006/06/27 14:18:03  marc
# added error exception for setattr if element does not exist.
#
# Revision 1.9  2006/06/27 14:08:56  marc
# bugfixes
#
# Revision 1.8  2006/06/27 12:00:13  mark
# added doc attribute
#
# Revision 1.7  2006/06/27 09:42:32  marc
# added __str__ method
#
# Revision 1.6  2006/06/27 09:09:16  mark
# changed __deepcopy__ to fullfill interface requirements
#
# Revision 1.5  2006/06/27 06:50:05  marc
# added deepcopy and changed copy to only "copy" the elements in depth 1
#
# Revision 1.4  2006/06/26 19:12:18  marc
# added copy method
#
# Revision 1.3  2006/06/26 15:11:19  mark
# added attribute check
#
# Revision 1.2  2006/06/26 14:38:52  marc
# Added generic selectors (getattr, setattr) for any attribute in element
#
# Revision 1.1  2006/06/23 14:08:56  mark
# inital checkin (stable)
#