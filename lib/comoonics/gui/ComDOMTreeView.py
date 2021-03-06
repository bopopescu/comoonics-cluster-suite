#!/usr/bin/env python
'''
Tree View/Generic Tree Model

This test is designed to demonstrate creating a new type of tree model
in python for use with the new tree widget in gtk 2.0.
'''

import gtk
import gobject
from xml.dom.minidom import parseString 
import xml.dom.minidom
import xml.parsers.xmlproc.utils
from xml.dom.ext.reader import Sax2
import xml.dom
import sys
import os
import urllib2
import urllib
from xml.dom.NodeFilter import NodeFilter
from xml.dom.ext import PrettyPrint

sys.path.append("../../")

from comoonics import ComLog

def acceptElements(model, iter):
    if not model.get_value(iter, DOMModel.COLUMN_NODE):
        return False
    node=model.get_value(iter, DOMModel.COLUMN_NODE).get_data(DOMTreeModel.NODE_KEY)
    #print "Filter Node %s" % node.nodeName
    if node.nodeType == node.ELEMENT_NODE:
        return True
    else:
        return False
        
def acceptAttributes(model, iter):
    if not model.get_value(iter, DOMModel.COLUMN_NODE):
        return False
    node=model.get_value(iter, DOMModel.COLUMN_NODE).get_data(DOMTreeModel.NODE_KEY)
    print "Filter Node %s" % node
    if node.nodeType == node.ATTRIBUTE_NODE:
        return True
    else:
        return False

__logStrLevel__="DOMTreeView"

class DOMModel:
    NODE_KEY="node"
    (
      COLUMN_NAME,
      COLUMN_VALUE,
      COLUMN_EDITABLE,
      COLUMN_NODE
     ) = range(4)
     
    def __init__(self, doc):
         self.document=doc


class DOMTreeModel(gtk.TreeStore, DOMModel):
    def __init__(self, node, doc):
        gtk.TreeStore.__init__(self, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_BOOLEAN, gobject.TYPE_OBJECT)
        DOMModel.__init__(self, doc)
        self.createStoreModelFromNode(node)
        self.document=doc

    def createStoreModelFromNode(self, node, parent=None):
        iter=self.append(parent)
        gobj=gobject.GObject()
        gobj.set_data(DOMTreeModel.NODE_KEY, node)
        self.set_value(iter, DOMModel.COLUMN_NAME, node.nodeName)
        self.set_value(iter, DOMModel.COLUMN_VALUE, node.nodeValue)
        self.set_value(iter, DOMModel.COLUMN_EDITABLE, False)
        self.set_value(iter, DOMModel.COLUMN_NODE, gobj)
        for child in node.childNodes:
            self.createStoreModelFromNode(child, iter)

class DOMListModel(gtk.ListStore, DOMModel):
    def __init__(self, node, doc):
        gtk.ListStore.__init__(self, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_BOOLEAN, gobject.TYPE_OBJECT)
        DOMModel.__init__(self, doc)
        self.createStoreModelFromNode(node)

    def createStoreModelFromNode(self, node):
        iter=self.append()
        ComLog.getLogger(__logStrLevel__).debug("Node: %s, %s" % (node, node.attributes))
        gobj=gobject.GObject()
        gobj.set_data(DOMTreeModel.NODE_KEY, node)
        self.set_value(iter, DOMModel.COLUMN_NAME, node.nodeName)
        self.set_value(iter, DOMModel.COLUMN_VALUE, node.nodeValue)
        self.set_value(iter, DOMModel.COLUMN_EDITABLE, True)
        self.set_value(iter, DOMModel.COLUMN_NODE, gobj)

        if node.attributes and len(node.attributes) > 0:
            for child in node.attributes:
                self.createStoreModelFromNode(child)
         
class DOMNodeView(gtk.TreeView):
    def __init__(self, edit=False, editfunc=None):
        gtk.TreeView.__init__(self)
        renderer = gtk.CellRendererText()
        renderer.set_data("column", DOMModel.COLUMN_NAME)
        renderer.set_property("xalign", 0.0)
        if edit:
            renderer.connect("edited", editfunc, self)

        column = gtk.TreeViewColumn("Name", renderer, text=DOMModel.COLUMN_NAME)
        #column = gtk_tree_view_get_column(GTK_TREE_VIEW(treeview), col_offset - 1);
        column.set_clickable(True)
        # self.get_selection().set_mode(gtk.SELECTION_SINGLE)

        self.append_column(column)

       #column = gtk_tree_view_get_column(GTK_TREE_VIEW(treeview), col_offset - 1);
        column = gtk.TreeViewColumn("Value", renderer, text=DOMModel.COLUMN_VALUE, editable=DOMModel.COLUMN_EDITABLE)
        #column = gtk_tree_view_get_column(GTK_TREE_VIEW(treeview), col_offset - 1);
        column.set_clickable(True)
        # self.get_selection().set_mode(gtk.SELECTION_SINGLE)

        self.append_column(column)

class DOMTreeViewTest(gtk.Window):
    DOM_QNAME="enterprisecopy"
    contextid=1
    title="Comoonics XML Editor"
    def __init__(self, filename, parent=None):
        gtk.Window.__init__(self)
        try:
            self.set_screen(parent.get_screen())
        except AttributeError:
            self.connect('destroy', lambda *w: gtk.main_quit())
        self.updateTitle(filename)
        self.set_default_size(650, 400)
        self.set_border_width(8)

        menubar = self.create_main_menu()
        menubar.show()
        self.statusbar = gtk.Statusbar()
        
        (doc, dtd) = self.openFile(filename)
        self.dtd=dtd
        node=doc.documentElement
        # create model
        # create treeview
        self.__treeview = DOMNodeView()
        self.__treeview.set_rules_hint(True)
        self.__treeview.get_selection().set_mode(gtk.SELECTION_SINGLE)
        self.__listview = DOMNodeView(True, self.edit_attribute)
        self.__listview.set_rules_hint(True)
        self.__listview.get_selection().set_mode(gtk.SELECTION_SINGLE)

        self.initFromDOMNode(node, doc)

        # expand all rows after the treeview widget has been realized
        self.__treeview.connect('realize', lambda tv: tv.expand_all())
        self.__treeview.connect_object("button-press-event", self.button_press, self.__treeview)
        
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self.__treeview)

        framel = gtk.Frame()
        framel.set_shadow_type(gtk.SHADOW_IN)
        framel.set_size_request(200, 200)
        framel.add(sw)
        
        framer = gtk.Frame()
        framer.set_shadow_type(gtk.SHADOW_IN)
        framer.set_size_request(200, 200)
        framer.add(self.__listview)
        
        hpaned = gtk.HPaned()
        hpaned.add1(framel)
        hpaned.add2(framer)
        vbox = gtk.VBox(False, 8)
        vbox.pack_start(menubar, False, False)
        vbox.add(hpaned)
        vbox.pack_start(self.statusbar, False, False)
        self.add(vbox)
        self.show_all()
        self.statusbar.push(self.contextid, "init succeeded")

    def updateTitle(self, filename):
        self.set_title("%s(%s)" % (self.title, filename))

    def initFromDOMNode(self, node, doc):
        self.doc=doc
        self.__basemodell=DOMTreeModel(node, doc)
        self.__basemodelr=DOMListModel(node, doc)
        modelfilterl=self.__basemodell.filter_new()
        modelfilterl.set_visible_func(acceptElements)
        modelfilterr=self.__basemodelr.filter_new()
        modelfilterr.set_visible_func(acceptAttributes)
        self.__treeview.set_model(modelfilterl)
        self.__treeview.get_selection().connect("changed", self.selection_changed, self.__basemodelr, modelfilterr)
        self.__listview.set_model(modelfilterr)

    def newFromDTDFile(self, dtd_filename, doc_element):
        # Here we need to create the dtd-object and create an empty document with the basename of the dtd
        #dom = xml.dom.minidom.getDOMImplementation()
        #type = dom.createDocumentType(self.DOM_QNAME, None, dtd_filename)
        #doc = dom.createDocument(None, self.DOM_QNAME, type)
        dtd = xml.parsers.xmlproc.utils.load_dtd(dtd_filename)
        if doc_element:
            doc = self.createDocElementFromName(doc_element, dtd_filename)
        else:
            doc = self.createDocElementFromName(self.dtd.get_elements()[0], dtd_filename)

        self.doc=doc
        self.dtd=dtd
        self.updateTitle("new")
        self.status("new document with dtdbase %s succeeded" % dtd_filename)

        return (doc, dtd)

    def createDocElementFromName(self, docname, dtd_filename):
        dom = xml.dom.minidom.getDOMImplementation()
        type = dom.createDocumentType(docname, None, dtd_filename)
        doc = dom.createDocument(None, docname, type)
        return doc

    def openFile(self, filename):
        reader = Sax2.Reader(validate=1)
        stream = open(filename)
        doc = reader.fromStream(stream)
        dtd = reader.parser._parser.get_dtd()
        self.filename=filename
        self.updateTitle(filename)
        self.status("open of file %s succeeded" % filename)
        return (doc, dtd)

    def openURI(self, uri):
        ComLog.getLogger(__logStrLevel__).debug("openURI(%s)" % uri)
        self.updateTitle(filename)
        self.status("open of file %s succeeded" % uri)
        return self.openFile(filename)
    
    def saveFile(self, _uri=None):
        if not _uri:
            _uri=self.filename
        ComLog.getLogger(__logStrLevel__).debug("file: %s" % _uri)
        stream=open(_uri,"w+")
        PrettyPrint(self.__basemodell.document, stream)
        self.filename=_uri
        self.status("save to file %s succeeded" % _uri)
        self.updateTitle(sefl.filename)
        
    def selection_changed(self, selection, dest, filter):
        (model, iter) = selection.get_selected()
        ComLog.getLogger(__logStrLevel__).debug("Selection changed %s, %s, %s %s" % (model, iter, dest, filter))
        dest.clear()
        if iter:
            dest.createStoreModelFromNode(model.get_value(iter, DOMModel.COLUMN_NODE).get_data(DOMModel.NODE_KEY))
        if filter:
            filter.refilter()
            
    def add_element(self, item, model, piter, name, iter=None):
        self.status("Menu Add Element... " + name + " pressed menuitem %s, model %s, piter %s, iter %s" % (item, model, piter, iter))
        if iter:
            value = model.get_value(iter, DOMModel.COLUMN_NODE)
            ref_node=value.get_data(DOMModel.NODE_KEY)
            ref_node=ref_node.nextSibling
            citer=model.convert_iter_to_child_iter(iter)
        else:
            citer=None
            ref_node=None
        value=model.get_value(piter, DOMModel.COLUMN_NODE)
        parent_node=value.get_data(DOMModel.NODE_KEY)
        ComLog.getLogger(__logStrLevel__).debug("parentnode: %s" % parent_node)
        node=self.__basemodell.document.createElement(name)
        parent_node.insertBefore(node, ref_node)
        cpiter=model.convert_iter_to_child_iter(piter)
        iter_newnode=model.get_model().insert_after(cpiter, citer)
        gobj=gobject.GObject()
        gobj.set_data(DOMTreeModel.NODE_KEY, node)
        model.get_model().set_value(iter_newnode, DOMModel.COLUMN_NAME, node.nodeName)
        model.get_model().set_value(iter_newnode, DOMModel.COLUMN_VALUE, node.nodeValue)
        model.get_model().set_value(iter_newnode, DOMModel.COLUMN_EDITABLE, False)
        model.get_model().set_value(iter_newnode, DOMModel.COLUMN_NODE, gobj)
        
    def insert_element(self, item, model, iter, name):
        self.status("Menu Insert Element... " + name + " pressed menuitem %s, model %s, iter %s" % (item, model, iter))
        piter=model.iter_parent(iter)
        self.add_element(item, model, piter, name, iter)

    def delete_element(self, item, model, iter):
        self.status("Menu Delete Element... pressed menuitem %s, model %s" % (item, model))
        value = model.get_value(iter, DOMModel.COLUMN_NODE)
        ref_node=value.get_data(DOMModel.NODE_KEY)
        piter=model.iter_parent(iter)
        value=model.get_value(piter, DOMModel.COLUMN_NODE)
        parent_node=value.get_data(DOMModel.NODE_KEY)
        ComLog.getLogger(__logStrLevel__).debug("parentnode: %s" % parent_node)
        parent_node.removeChild(ref_node)
        citer=model.convert_iter_to_child_iter(iter)
        model.get_model().remove(citer)
    
    def add_attribute(self, item, model, iter, name):
        self.status("Menu Add Attribute... " + name + " pressed menuitem %s, model %s, iter %s" % (item, model, iter))
        value = model.get_value(iter, DOMModel.COLUMN_NODE)
        ref_node=value.get_data(DOMModel.NODE_KEY)
        ref_node.setAttributeNode(self.doc.createAttribute(name))
        ref_node.setAttribute(name, "unset")
        ComLog.getLogger(__logStrLevel__).debug("ref_node: %s" % ref_node)
        self.__basemodelr.clear()
        self.__basemodelr.createStoreModelFromNode(ref_node)

    def delete_attribute(self, item, model, iter, name):
        self.status("Menu Delete attribute... " + name + " pressed menuitem %s, model %s, iter %s" % (item, model, iter))
        value = model.get_value(iter, DOMModel.COLUMN_NODE)
        ref_node=value.get_data(DOMModel.NODE_KEY)
        ref_node.removeAttribute(name)
        ComLog.getLogger(__logStrLevel__).debug("ref_node: %s" % ref_node)
        self.__basemodelr.clear()
        self.__basemodelr.createStoreModelFromNode(ref_node)
    
    def edit_attribute(self, cell, path_string, new_text, view):
        model=view.get_model()
        self.status("Menu Edit attribute... " + path_string + " pressed cell %s, model %s, new_text %s" % (cell, model, new_text))
        iter = model.get_iter_from_string(path_string)
        piter= model.iter_parent(iter)
        parent_node=model.get_value(iter, DOMModel.COLUMN_NODE).get_data(DOMModel.NODE_KEY)
        value = model.get_value(iter, DOMModel.COLUMN_NODE)
        ref_node=value.get_data(DOMModel.NODE_KEY)
        ComLog.getLogger(__logStrLevel__).debug("Path: %s" % (path_string))
        
        ComLog.getLogger(__logStrLevel__).debug("ref_node: %s" % ref_node)
        ref_node.nodeValue=new_text
        citer=model.convert_iter_to_child_iter(iter)
        model.get_model().set(citer, DOMModel.COLUMN_VALUE, new_text)
            
    def button_press(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            try:
                path, column, cell_x, cell_y = widget.get_path_at_pos(int(event.x), int(event.y))
                iter = widget.get_model().get_iter(path)
                selection = widget.get_selection()
                selection.select_path(path)
            except TypeError, e:
                return False
            __menu = gtk.Menu()
            __model, __i = widget.get_selection().get_selected()
            #Add Attribute
            __item=AddAttributeMenuItem(widget.get_selection(), self.dtd)
            __item.registerListener(self)
            __menu.append(__item)
            #Delete Attribute
            __item=DeleteAttributeMenuItem(widget.get_selection())
            __item.registerListener(self)
            __menu.append(__item)
            #Add Child Element
            __item=AddElementMenuItem(widget.get_selection(), self.dtd)
            __menu.append(__item)
            __item.registerListener(self)
            #Insert Element
            __item=InsertElementMenuItem(widget.get_selection(), self.dtd)
            __menu.append(__item)
            __item.registerListener(self)
            #Delete Element
            __item=DeleteElementMenuItem(widget.get_selection())
            __menu.append(__item)
            __item.registerListener(self)
            __menu.popup(None, None, None, event.button, event.time)
    
    def file_new(self, number, menuitem):
        ComLog.getLogger(__logStrLevel__).debug("file_new pressed %s, %s." %(number, menuitem))
        dialog=gtk.FileChooserDialog("Choose DTD file to open", self, gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_OK, gtk.RESPONSE_OK,
                gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        dtd_filter=gtk.FileFilter()
        dtd_filter.add_pattern("*.dtd")
        dtd_filter.set_name("DTD-Filter")
        dialog.add_filter(dtd_filter)
        element_chooser = gtk.combo_box_new_text()
        active=0
        for i in range(len(self.dtd.get_elements())):
            element_txt=self.dtd.get_elements()[i]
            if element_txt == self.doc.documentElement.tagName:
                active=i
            element_chooser.append_text(element_txt)
        element_chooser.set_active(active)
        element_chooser.show ()
        dialog.set_extra_widget(element_chooser)
        ComLog.getLogger(__logStrLevel__).debug("Systemid: %s" % self.doc.doctype.systemId)
        dialog.connect("selection-changed", self.dtd_changed, element_chooser)
        dialog.set_filename(self.doc.doctype.systemId)
        response=dialog.run()
        dtd_file=dialog.get_filename()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            ComLog.getLogger(__logStrLevel__).debug("File: %s, rootnode: %s" % (dtd_file, element_chooser.get_active_text()))
            (doc, dtd) = self.newFromDTDFile(dtd_file, element_chooser.get_active_text())
            self.dtd=dtd
            self.initFromDOMNode(doc.documentElement, doc)
            self.updateTitle(filename)
    
    def dtd_changed(self, filedialog, chooser):
        ComLog.getLogger(__logStrLevel__).debug("dtd changed pressed %s, %s." %(filedialog, chooser))
        try:
            self.newFromDTDFile(filedialog.get_filename())
            chooser.get_model().clear()
            for element_txt in self.dtd.get_elements():
                chooser.append_text(element_txt)
        except:
            pass
        
    def file_open(self, number, menuitem):
        ComLog.getLogger(__logStrLevel__).debug("file open pressed %s, %s." %(number, menuitem))
        dialog=gtk.FileChooserDialog("Choose file to open", self, gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_OK, gtk.RESPONSE_OK,
                gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        xml_filter=gtk.FileFilter()
        xml_filter.add_pattern("*.xml")
        xml_filter.set_name("XML-Filter")
        conf_filter=gtk.FileFilter()
        conf_filter.add_pattern("*.conf")
        conf_filter.set_name("Conf-Filter")
        dialog.add_filter(xml_filter)
        dialog.add_filter(conf_filter)
        response=dialog.run()
        file=dialog.get_filename()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            ComLog.getLogger(__logStrLevel__).debug("File: %s" % file)
            (doc, dtd) = self.openFile(file)
            self.dtd=dtd
            self.initFromDOMNode(doc.documentElement, doc)
        
    def file_save(self, number, menuitem):
        ComLog.getLogger(__logStrLevel__).debug("file save pressed %s, %s." %(number, menuitem))
        self.saveFile()
        
    def file_save_as(self, number, menuitem):
        ComLog.getLogger(__logStrLevel__).debug("file save as pressed %s, %s." %(number, menuitem))
        dialog=gtk.FileChooserDialog("Choose file to open", self, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_OK, gtk.RESPONSE_OK,
                gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        xml_filter=gtk.FileFilter()
        xml_filter.add_pattern("*.xml")
        xml_filter.set_name("XML-Filter")
        conf_filter=gtk.FileFilter()
        conf_filter.add_pattern("*.conf")
        conf_filter.set_name("Conf-Filter")
        dialog.add_filter(xml_filter)
        dialog.add_filter(conf_filter)
        dialog.set_current_name(self.filename)
        response=dialog.run()
        file=dialog.get_filename()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            ComLog.getLogger(__logStrLevel__).debug("File: %s" % file)
            self.saveFile(file)
    
    """ 
    private methods
    """
    def status(self, text):
        self.statusbar.push(self.contextid, text)
    
    def create_main_menu(self):
        # This is the ItemFactoryEntry structure used to generate new menus.
        # Item 1: The menu path. The letter after the underscore indicates an
        #         accelerator key once the menu is open.
        # Item 2: The accelerator key for the entry
        # Item 3: The callback.
        # Item 4: The callback action.  This changes the parameters with
        #         which the callback is called.  The default is 0.
        # Item 5: The item type, used to define what kind of an item it is.
        #       Here are the possible values:
        #       NULL               -> "<Item>"
        #       ""                 -> "<Item>"
        #       "<Title>"          -> create a title item
        #       "<Item>"           -> create a simple item
        #       "<CheckItem>"      -> create a check item
        #       "<ToggleItem>"     -> create a toggle item
        #       "<RadioItem>"      -> create a radio item
        #       <path>             -> path of a radio item to link against
        #       "<Separator>"      -> create a separator
        #       "<Branch>"         -> create an item to hold sub items (optional)
        #       "<LastBranch>"     -> create a right justified branch 
        __menu_items=(
            ( "/_File",         None,         None, 0, "<Branch>" ),
            ( "/File/_New",     "<control>N", self.file_new, 0, None ),
            ( "/File/_Open",    "<control>O", self.file_open, 0, None ),
            ( "/File/_Save",    "<control>S", self.file_save, 0, None ),
            ( "/File/Save _As", None,         self.file_save_as, 0, None ),
            ( "/File/sep1",     None,         None, 0, "<Separator>" ),
            ( "/File/Quit",     "<control>Q", gtk.main_quit, 0, None ),
            ( "/_Options",      None,         None, 0, "<Branch>" ),
            ( "/Options/Test",  None,         None, 0, None ),
            ( "/_Help",         None,         None, 0, "<LastBranch>" ),
            ( "/_Help/About",   None,         None, 0, None ),
            )
        
        __accel_group = gtk.AccelGroup()

        # This function initializes the item factory.
        # Param 1: The type of menu - can be MenuBar, Menu,
        #          or OptionMenu.
        # Param 2: The path of the menu.
        # Param 3: A reference to an AccelGroup. The item factory sets up
        #          the accelerator table while generating menus.
        self.item_factory = gtk.ItemFactory(gtk.MenuBar, "<main>", __accel_group)

        # This method generates the menu items. Pass to the item factory
        #  the list of menu items
        self.item_factory.create_items(__menu_items)

        # Attach the new accelerator group to the window.
        self.add_accel_group(__accel_group)

        # Finally, return the actual menu bar created by the item factory.
        return self.item_factory.get_widget("<main>")

class AddElementMenuItem(gtk.MenuItem):
    def __init__(self, selection, dtd, label="add Child Element..."):
        gtk.MenuItem.__init__(self, label)       
        self.items=list()
        self.set_submenu(self.createMenu(selection, dtd))
        self.show()  
        
    
    def registerListener(self, listener):
        for i in range(len(self.items)):
            self.items[i][0].connect("activate", listener.add_element, \
                                     self.items[i][1], self.items[i][2], self.items[i][3])

    def createMenu(self, selection, dtd):
        __menu = gtk.Menu()
        __model, __i = selection.get_selected()
        __node = __model.get(__i, DOMModel.COLUMN_NODE)[0]
        __attr = ContentModelHelper(dtd).getValidElementNamesAppend(__node.get_data(DOMTreeModel.NODE_KEY))
        for i in range(len(__attr)):
            __item = gtk.MenuItem(__attr[i])
            __menu.append(__item)
            self.items.append([__item, __model, __i, __attr[i]])
            __item.show()
        __menu.show()
        return __menu
    
class InsertElementMenuItem(gtk.MenuItem):
    def __init__(self, selection, dtd, label="insert Element..."):
        gtk.MenuItem.__init__(self, label)       
        self.items=list()
        __item = self.createMenu(selection, dtd)
        if __item:
            self.set_submenu(__item)
            self.show()  
        
    
    def registerListener(self, listener):
        for i in range(len(self.items)):
            self.items[i][0].connect("activate", listener.insert_element, \
                                     self.items[i][1], self.items[i][2], self.items[i][3])

    def createMenu(self, selection, dtd):
        __menu = gtk.Menu()
        __model, __i = selection.get_selected()
        __node = __model.get(__i, DOMModel.COLUMN_NODE)[0]
        if not __node.get_data(DOMTreeModel.NODE_KEY).parentNode.nodeType == __node.get_data(DOMTreeModel.NODE_KEY).parentNode.ELEMENT_NODE:
            return None
        ComLog.getLogger(__logStrLevel__).debug( __node.get_data(DOMTreeModel.NODE_KEY).parentNode)
        __attr = ContentModelHelper(dtd). \
            getValidElementNamesInsert(__node.get_data(DOMTreeModel.NODE_KEY))
        for i in range(len(__attr)):
            __item = gtk.MenuItem(__attr[i])
            __menu.append(__item)
            self.items.append([__item, __model, __i, __attr[i]])
            __item.show()
        __menu.show()
        return __menu
    

class DeleteElementMenuItem(gtk.MenuItem):
    def __init__(self, selection, label="delete"):
        gtk.MenuItem.__init__(self, label)
        self.selection=selection
        self.show()
        
    def registerListener(self, listener):
        __model, __i = self.selection.get_selected()
        self.connect("activate", listener.delete_element,  __model, __i)    
        
class AddAttributeMenuItem(gtk.MenuItem):
    def __init__(self, selection, dtd, label="add Attribute..."):
        gtk.MenuItem.__init__(self, label)
        self.items=list()
        self.set_submenu(self.createMenu(selection, dtd))
        self.show()  
        
    def registerListener(self, listener):
        for i in range(len(self.items)):
            self.items[i][0].connect("activate", listener.add_attribute, \
                                     self.items[i][1], self.items[i][2], self.items[i][3])    
        
    def createMenu(self, selection, dtd):
        __menu = gtk.Menu()
        __model, __i = selection.get_selected()
        __node = __model.get(__i, DOMModel.COLUMN_NODE)[0].get_data(DOMTreeModel.NODE_KEY)
        __attr = dtd.get_elem(__node.tagName).get_attr_list()
        for i in range(len(__attr)):
            if not __node.hasAttribute(__attr[i]):
                __item = gtk.MenuItem(__attr[i])
                __menu.append(__item)
                self.items.append([__item, __model, __i, __attr[i]])
                __item.show()
        __menu.show()
        return __menu
       
    
class DeleteAttributeMenuItem(gtk.MenuItem):
    def __init__(self, selection, label="delete Attribute..."):
        gtk.MenuItem.__init__(self, label)
        self.items=list()
        self.set_submenu(self.createMenu(selection))
        self.show()           
            
    def registerListener(self, listener):
        for i in range(len(self.items)):
            self.items[i][0].connect("activate", listener.delete_attribute, \
                                     self.items[i][1], self.items[i][2], self.items[i][3])    
            
    def createMenu(self, selection):
        __menu = gtk.Menu()
        __model, __i = selection.get_selected()
        __node = __model.get(__i, DOMModel.COLUMN_NODE)[0]
        __elem= __node.get_data(DOMTreeModel.NODE_KEY)
        __attr = __elem.attributes
        for i in range(len(__attr)):
            __item = gtk.MenuItem(__attr[i].name)
            self.items.append([__item, __model, __i, __attr[i].name])
            __menu.append(__item)
            __item.show()
        __menu.show()
        return __menu
            
            
class ContentModelHelper:
    def __init__(self, dtd):
        self.dtd=dtd
    
    def getValidElementNamesAppend(self, element):
        ComLog.getLogger(__logStrLevel__).debug("in getValidElementNamesAppend")
        __elem=self.dtd.get_elem(element.tagName)
        __state=__elem.get_start_state()
        __nodes=element.childNodes
        for i in range(len(__nodes)):
            if __nodes[i].nodeType != __nodes[i].ELEMENT_NODE:
                continue
            ComLog.getLogger(__logStrLevel__).debug("found element %s" %__nodes[i].tagName)
            __state=__elem.next_state(__state, __nodes[i].tagName)
        return __elem.get_valid_elements(__state)
        
    def getValidElementNamesInsert(self, element):
        ComLog.getLogger(__logStrLevel__).debug("in getValidElementNamesInsert")
        ret=list()
        oelement=element
        parent=element.parentNode
        __elem=self.dtd.get_elem(parent.tagName)
        __state=__elem.get_start_state()
        __nodes=[element]
        # get all element up to the current
        while element.previousSibling:
            element = element.previousSibling 
            if element.nodeType == element.ELEMENT_NODE:
                __nodes.append(element)
        __nodes.reverse()
        
        # go to the current element state
        for i in range(len(__nodes)):
            ComLog.getLogger(__logStrLevel__).debug("found element %s" %__nodes[i].tagName)
            #if __elem.final_state(__state):
            #   return ret
            __state=__elem.next_state(__state, __nodes[i].tagName)
       
        # get all valid elements in that state 
        __elements=__elem.get_valid_elements(__state)
        ComLog.getLogger(__logStrLevel__).debug("valid elements " + str(__elements))
        
        # test all valid elements
        for i in range(len(__elements)):
            is_valid=True
            ComLog.getLogger(__logStrLevel__).debug("testing element " + __elements[i])
            #save the start element
            element=oelement
            try: 
                # get new test state 
                ComLog.getLogger(__logStrLevel__).debug("new state with element " + __elements[i])
                __tstate=__elem.next_state(__state, __elements[i])
                # test the whole branch with new element inserted
                while element.nextSibling:
                    element=element.nextSibling
                    if element.nodeType == element.ELEMENT_NODE:
                        ComLog.getLogger(__logStrLevel__).debug("new state with element " + element.tagName)
                        __tstate=__elem.next_state(__tstate, element.tagName)
                        ComLog.getLogger(__logStrLevel__).debug("state is  " + str(__tstate) + " " + \
                                                                str(__elem.final_state(__tstate)))
                        if __elem.final_state(__tstate) == 0:
                            ComLog.getLogger(__logStrLevel__).debug("state is final " + element.tagName)
                            is_valid=False
                            break
                if is_valid:
                    ret.append(__elements[i])
            except KeyError, e:
                ComLog.getLogger(__logStrLevel__).debug("element : " + __elements[i])
                ComLog.getLogger(__logStrLevel__).debug(e)
                continue
            ComLog.getLogger(__logStrLevel__).debug(ret)
        return ret
        
    def getValidElementNames2(self, element):
        __elem=self.dtd.get_elem(element.tagName)
        __sstate=__elem.get_start_state()
        __elementlist=list()
        __nodes=element.childNodes
        self.fillList(__elementlist, __elem, __sstate)
        return __elementlist
    
    def fillList(self, elements, element, state): 
        __el = element.get_valid_elements(state)
        for i in range(len(__el)):
            ComLog.getLogger(__logStrLevel__).debug("processing " + __el[i])
            if not elements.count(__el[i]):
                ComLog.getLogger(__logStrLevel__).debug(__el[i] + " is not in " + str(elements))
                elements.append(__el[i])
                if not element.final_state(state):
                    ComLog.getLogger(__logStrLevel__).debug("calling fillist with next state")
                    self.fillList(elements, element, element.next_state(state, __el[i]))
       
        
        

def main():
    #filename="/tmp/cluster.conf"
    filename="../../../test/gfs-node1-clonetest.xml"
    if len(sys.argv) > 1:
        filename=sys.argv[1]
    dtv=DOMTreeViewTest(filename)
    gtk.main()

if __name__ == '__main__':
    main()

################################
# $Log: ComDOMTreeView.py,v $
# Revision 1.2  2006-07-24 09:58:55  marc
# new gui addons.
#
# Revision 1.1  2006/07/19 14:29:15  marc
# removed the filehierarchie
#
# Revision 1.17  2006/07/18 12:12:12  marc
# new is now working better. Using infos already here.
#
# Revision 1.16  2006/07/18 11:08:10  mark
# bug fixes
#
# Revision 1.15  2006/07/17 15:22:09  marc
# new menu is running now
#
# Revision 1.14  2006/07/17 11:11:32  mark
# implemented newFromDTDFile
#
# Revision 1.13  2006/07/17 10:11:01  marc
# added Log Tag
# print => ComLog.getLogger()..
#