"""Comoonics filesystem module


here should be some more information about the module, that finds its way inot the onlinedoc

"""


# here is some internal information
# $Id: ComFileSystem.py,v 1.9 2011-02-21 16:24:34 marc Exp $
#


__version__ = "$Revision: 1.9 $"
# $Source: /atix/ATIX/CVSROOT/nashead2004/management/comoonics-clustersuite/python/lib/comoonics/storage/ComFileSystem.py,v $

import os.path
import exceptions

from comoonics import ComLog
from comoonics import ComSystem
from comoonics.ecbase import ComUtils
from comoonics.ComExceptions import ComException
from comoonics.ComDataObject import DataObject, NotImplementedYetException

log=ComLog.getLogger("ComFileSystem")

CMD_MKFS="mkfs"
CMD_GFS_MKFS="gfs_mkfs"
CMD_GFS_TOOL="gfs_tool"
CMD_GFS_FSCK="gfs_fsck"
CMD_MOUNT="mount"
CMD_UMOUNT="umount"
CMD_E2LABEL="e2label"
CMD_E4LABEL="e4label"
CMD_E2FSCK="e2fsck"
CMD_E4FSCK="e4fsck"
CMD_TUNEFSOCFS="tunefs.ocfs2 -L"
CMD_OCFS2FSCK="ocfs2.fsck"
CMD_SWAPMKFS="mkswap"
CMD_SWAPON="swapon"
CMD_SWAPOFF="swapoff"

def getFileSystem(element, doc):
    """factory method to ceate a FileSystem object
    returns a FileSystem object that fits to the description in element"
    """
    __type=element.getAttribute("type")
    if __type == "auto":
        return FileSystem(element, doc)
    if __type == "ext2":
        return ext2FileSystem(element, doc)
    if __type == "ext3":
        return ext3FileSystem(element, doc)
    if __type == "ext4":
        return ext4FileSystem(element, doc)
    if __type == "gfs":
        return gfsFileSystem(element, doc)
    if __type == "ocfs2":
        return ocfs2FileSystem(element, doc)
    if __type == "nfs":
        return nfsFileSystem(element, doc)
    if __type == "swap":
        return swapFileSystem(element, doc)
    raise exceptions.NotImplementedError()


class FileSystem(DataObject):
    """ Base class for a filesystem """
    TAGNAME="filesystem"
    def __init__(self, element, doc):
        """ element: DOMElement
        """
        # super
        DataObject.__init__(self, element, doc)

        #Check for mount options
        #__mopt = element.getElementsByTagName(MountOptions.TAGNAME)
        #if len(__mopt):
        #    self.mountOptions=MountOptions(__mopt[0], doc)
        #else:
        #    __node=doc.createElement(MountOptions.TAGNAME)
        #    element.appendChild(__node)
        #    self.mountOptions=MountOptions(__node, doc)
        # FIXME Do we need all of them ?
        self.formattable=0
        self.checked = 0
        self.name = ""
        self.linuxnativefs = 0
        self.maxSizeMB = 8 * 1024 * 1024
        self.maxLabelChars = 16
        self.partedFileSystemType = None
        self.cmd_fsck=None
        self.cmd_mkfs=None
        self.copyable=True
        self.nomountpoint=False
        self.cmd_mount=CMD_MOUNT
        self.cmd_umount=CMD_UMOUNT

    def mount(self, device, mountpoint):
        """ mount a filesystem
        device: ComDevice.Device
        mountpoint: ComMountPoint.MountPoint
        """

        __exclusive=self.getAttribute("exlock", "")
        __mkdir=self.getAttributeBoolean("mkdir", True)

        __mp=mountpoint.getAttribute("name")
        if not os.path.exists(__mp) and __mkdir:
            log.debug("Path %s does not exists. I'll create it." % __mp)
            ComSystem.execMethod(os.makedirs, __mp)

        if __exclusive and __exclusive != "" and os.path.exists(__exclusive):
            raise ComException("lockfile " + __exclusive + " exists!")

        __cmd = self.mkmountcmd(device, mountpoint)
        __rc, __ret = ComSystem.execLocalStatusOutput(__cmd)
        log.debug("mount:" + __cmd + ": " + __ret)
        if __rc != 0:
            raise ComException(__cmd + __ret)
        if __exclusive:
            __fd=open(__exclusive, 'w')
            __fd.write(device.getDevicePath() + " is mounted ")

    def mkmountcmd(self, device, mountpoint):
        return self.cmd_mount + " -t " + self.getAttribute("type")+ " " + mountpoint.getOptionsString() + \
                " " + device.getDevicePath() + " " + mountpoint.getAttribute("name")

    def umountDev(self, device):
        """ umount a filesystem with the use of the device name
        device: ComDevice.Device
        """
        __cmd = self.cmd_umount + " " + device.getDevicePath()
        __rc, __ret = ComSystem.execLocalStatusOutput(__cmd)
        log.debug("umount:" + __cmd + ": " + __ret)
        if __rc != 0:
            raise ComException(__cmd + __ret)
        self.unlinkLockfile()

    def umountDir(self, mountpoint):
        """ umount a filesystem with the use of the mountpoint
        mountpoint: ComMountPoint.MountPoint
        """
        __cmd = self.cmd_umount + " " + mountpoint.getAttribute("name")
        __rc, __ret = ComSystem.execLocalStatusOutput(__cmd)
        log.debug("umount: " + __cmd + ": " + __ret)
        if __rc != 0:
            raise ComException(__cmd + __ret)
        self.unlinkLockfile()

    def getName(self):
        """ returns the filesystem name/type """
        return self.getAttribute("type")

    def formatDevice(self, device):
        """ format device with filesystem (virtual method)
        device: ComDevice.Device
        """
        pass

    def labelDevice(self, device, label):
        """ label device with label (virtual method)
        device: ComDevice.Device
        label: string
        """
        pass

    def checkFs(self, device):
        """ check filesystem on device (virtual method)
        device: ComDevice.Device
        """
        if self.getFsckCmd():
            (__cmd)=self.getFsckCmd()+" "+device.getDeviceName()
            log.debug("checkFs: cmd: %s" %(__cmd))
            ComSystem.execLocalOutput(__cmd)
        else:
            raise NotImplementedYetException("Method checkFs is not implemented by filesystem %s (class: %s)." %(self.getName(), self.__class__.__name__))

    def getLabel(self, device):
        """ return the label on device (virtual method)
        device: ComDevice.Device
        """
        return ""

#    def getBlockSize(self):
#        """ return the blocksize defined in filesystem element
#        see scanOptions
#        """
#        __attr=self.getElement().xpath(self.xmlpath+"/@bsize")
#        return __attr[0].value

    def isFormattable(self):
        """ return if this filesystem type can be formatted
        e.g ext3 is formattable, proc is not
        """
        return self.formattable

    def isCopyable(self):
        """ return if this filesystem type can be copied
        e.g. swap is not copyable but ext3.
        """
        return self.copyable

    def needsNoMountpoint(self):
        """ returns True if that filesystem does not need a mountpoint (e.g. swap)
        """
        return self.nomountpoint

    def getMaxSizeMB(self):
        """ returns maximum size of the filesystem in MB """
        return self.maxSizeMB

    def setFsckCmd(self, cmd):
        self.cmd_fsck=cmd

    def getFsckCmd(self):
        return self.cmd_fsck

    def setMkfsCmd(self, cmd):
        self.cmd_mkfs=cmd

    def getMkfsCmd(self):
        return self.cmd_mkfs

    def scanDevice(self, device):
        # Do we really need this method ?
        """ scans the device (virtual method)
        device: ComDevice.Device
        """
        pass

    def scanOptions(self, device, mountpoint=None):
        """ scans the filesystem for parameters e.g. blocksize (virtual method)
        device: ComDevice.Device
        mountpoint: ComMountPoint.MountPoint
        """
        pass

    def unlinkLockfile(self):
        if self.hasAttribute("exlock"):
            __lockfile=self.getAttribute("exlock")
            os.unlink(__lockfile)

class extFileSystem(FileSystem):
    """ Base class for extended filesystem """
    def __init__(self, element, doc):
        FileSystem.__init__(self, element, doc)
        self.partedFileSystemType = None
        self.formattable = 1
        self.checked = 1
        self.linuxnativefs = 1
        self.maxSizeMB = 8 * 1024 * 1024
        self.setFsckCmd(CMD_E2FSCK+" -y")
        self.labelCmd=CMD_E2LABEL

    def labelDevice(self, device, label):
        __devicePath = device.getDevicePath()
        __cmd = self.labelCmd + " " + __devicePath + " " + label
        __rc, __ret = ComSystem.execLocalStatusOutput(__cmd)
        log.debug("labelDevice: " +  __cmd + ": " + __ret)
        if __rc:
            raise ComException(__cmd + __ret)
        self.setAttribute("label", label)

    def getLabel(self, device):
        return self.getAttribute("label", self.getLabelFromDevice(device))

    def getLabelFromDevice(self, device):
        # BUG: Cannot function!!!!
        __devicePath= device.getDevicePath()
        __cmd = self.labelCmd + " " + __devicePath
        __rc, __ret = ComSystem.execLocalStatusOutput(__cmd)
        log.debug("getLabel: " + __cmd + ": " + __ret)
        if __rc:
            raise ComException(__cmd + __ret)
        return __ret

    def formatDevice(self, device):
        __devicePath = device.getDevicePath()
        __cmd = self.getMkfsCmd() + " " + __devicePath
        __rc, __ret = ComSystem.execLocalStatusOutput(__cmd)
        log.debug("formatDevice: "  + __cmd + ": " + __ret)
        if __rc != 0:
            raise ComException(__cmd + __ret)

    def findLabel(self, label):
        """ try to find Device with label
        returns Device
        """
        import ComDevice
        __cmd="/sbin/findfs LABEL=" + label
        __rc, __path = ComSystem.execLocalGetResult(__cmd)
        if not __rc:
            raise ComException("device with label " + label + "not found")
        return ComDevice.Device(__path[0])

class ext2FileSystem(extFileSystem):
    """ The extended2 filesystem """
    def __init__(self,element, doc):
        extFileSystem.__init__(self,element, doc)
        self.name = "ext2"
        self.setMkfsCmd(CMD_MKFS + " -t ext2 ")
        #self.partedFileSystemType = parted.file_system_type_get("ext2")
        #self.migratetofs = ['ext3']

class ext3FileSystem(extFileSystem):
    """ The extended3 filesystem """
    def __init__(self,element, doc):
        extFileSystem.__init__(self,element, doc)
        self.name = "ext3"
        self.setMkfsCmd(CMD_MKFS + " -t ext3 ")

class ext4FileSystem(extFileSystem):
    """ The extended4 filesystem """
    def __init__(self,element, doc):
        extFileSystem.__init__(self,element, doc)
        self.name = "ext4"
        self.setMkfsCmd(CMD_MKFS + " -t ext4 ")
        self.setFsckCmd(CMD_E4FSCK+" -y")
        self.labelCmd = CMD_E4LABEL

class ocfs2FileSystem(extFileSystem):
    """ The ocfs2 filesystem """
    def __init__(self,element, doc):
        extFileSystem.__init__(self,element, doc)
        self.name = "ocfs2"
        self.setMkfsCmd("yes | " + CMD_MKFS + " -t ocfs2 -F")
        self.labelCmd = CMD_TUNEFSOCFS
        self.setFsckCmd(CMD_OCFS2FSCK + " -y")

class swapFileSystem(FileSystem):
    """ Swap Filesystem """
    def __init__(self, element, doc):
        FileSystem.__init__(self, element, doc)
        self.name="swap"
        self.setMkfsCmd(CMD_SWAPMKFS)
        self.labelCmd=CMD_SWAPMKFS+ " -l "
        
        self.formattable=1
        self.nomountpoint=True
        self.copyable=False
        self.cmd_mount=CMD_SWAPON
        self.cmd_umount=CMD_SWAPOFF
        
    def formatDevice(self, device):
        __devicePath = device.getDevicePath()
        __cmd = self.getMkfsCmd() + " " + __devicePath
        __rc, __ret = ComSystem.execLocalStatusOutput(__cmd)
        log.debug("formatDevice: "  + __cmd + ": " + __ret)
        if __rc != 0:
            raise ComException(__cmd + __ret)

    def mkmountcmd(self, device, mountpoint):
        return self.cmd_mount+" "+device.getDevicePath()
        
class gfsFileSystem(FileSystem):
    """ The Global Filesystem - gfs """
    def __init__(self, element, doc):
        FileSystem.__init__(self, element, doc )
        self.partedFileSystemType = None
        self.formattable = 1
        self.checked = 1
        self.linuxnativefs = 1
        self.maxSizeMB = 8 * 1024 * 1024
        #self.packages = [ "e2fsprogs" ]
        self.name="gfs"
        self.setMkfsCmd(CMD_GFS_MKFS + " -O ")
        self.setFsckCmd(CMD_GFS_FSCK + " -y")

    def formatDevice(self, device):
        __cmd = self.getMkfsCmd() + self.getOptionsString() + device.getDevicePath()
        __rc, __ret = ComSystem.execLocalStatusOutput(__cmd)
        #self.getLog().debug("formatDevice: \n" , __cmd + __ret)
        if __rc != 0:
            raise ComException(__cmd + __ret)

    def getOptionsString(self):
        __optstr=" -j "
        __optstr+= self.getAttribute("journals")
        __optstr+=" -p "
        __optstr+= self.getAttribute("lockproto")
        if self.hasAttribute("clustername") and self.hasAttribute("locktable"):
            __optstr+=" -t "
            __optstr+= self.getAttribute("clustername")
            __optstr+=":"
            __optstr+= self.getAttribute("locktable")
        __optstr+=" -b "
        __optstr+= self.getAttribute("bsize")
        __optstr+=" "
        return __optstr


    def scanOptions(self, device, mountpoint=None):
        """ Scans a mountded gfs and puts the meta information into the DOM
        raises ComException
        """

        if mountpoint:
            __mountpoint=mountpoint.getAttribute("name")
        else:
            __mountpoint, fstype = device.scanMountPoint()
        if not __mountpoint:
            raise ComException("device " + device.getDevicePath() + " is not mounted.")
        __cmd = CMD_GFS_TOOL + " getsb " + __mountpoint
        __rc, __ret = ComSystem.execLocalGetResult(__cmd)
        if __rc != 0:
            raise ComException(__cmd + __ret)

        if __ret[0] == ComSystem.SKIPPED:
            # Just to keep up working when SIMULATING
            self.setAttribute("bsize", "4096")
            self.setAttribute("lockproto", "lock_dlm")
            self.setAttribute("clustername", "testcluster")
            self.setAttribute("journals", "4")
        else:
            __bsize=ComUtils.grepInLines(__ret, "  sb_bsize = ([0-9]*)")[0]
            log.debug("scan Options bsize: " + __bsize)
            self.setAttribute("bsize", __bsize)

            __lockproto=ComUtils.grepInLines(__ret, "  sb_lockproto = (.*)")[0]
            log.debug("scan Options lockproto: " + __lockproto)
            self.setAttribute("lockproto",__lockproto)

            __locktable=ComUtils.grepInLines(__ret, "  sb_locktable = .*?:(.*)")
            if len(__locktable) == 1:
                log.debug("scan Options locktable: " + __locktable[0])
                self.setAttribute("locktable", __locktable[0])

            __clustername=ComUtils.grepInLines(__ret, "  sb_locktable = (.*?):.*")
            if len(__clustername) == 1:
                log.debug("scan Options clustername: " +__clustername[0])
                self.setAttribute("clustername", __clustername[0])

            __cmd = CMD_GFS_TOOL + " df " + __mountpoint
            __rc, __ret = ComSystem.execLocalGetResult(__cmd)
            if __rc != 0:
                raise ComException(__cmd + __ret)
            __journals=ComUtils.grepInLines(__ret, "  Journals = ([0-9]+)")[0]
            log.debug("scan Options Journals: " +__journals)
            self.setAttribute("journals", __journals)

class nfsFileSystem(FileSystem):
    """ Implementation for NFS Filesystems """
    def __init__(self, element, doc):
        FileSystem.__init__(self, element, doc )
        self.partedFileSystemType = None
        self.formattable = 0
        self.checked = 0
        self.linuxnativefs = 1
        self.maxSizeMB = 8 * 1024 * 1024
        #self.packages = [ "e2fsprogs" ]
        self.name="nfs"
    
# $Log: ComFileSystem.py,v $
# Revision 1.9  2011-02-21 16:24:34  marc
# - added class SwapFilesystem
# - added general query for isCopyable
# - made commands more flexible
#
# Revision 1.8  2011/02/17 13:14:26  marc
# add support for labels.
#
# Revision 1.7  2011/02/15 14:54:52  marc
# - changes for ecbase rebase to comoonics.ecbase package
#
# Revision 1.6  2010/11/22 10:23:09  marc
# fixed small test bug
#
# Revision 1.5  2010/09/21 14:21:31  marc
# added NFS Filesystem support
#
# Revision 1.4  2010/03/29 14:13:45  marc
# - fixed bug in labelDevice
# - first tested version for ocfs2
#
# Revision 1.3  2010/03/08 12:30:48  marc
# version for comoonics4.6-rc1
#
# Revision 1.2  2010/02/07 20:32:17  marc
# - added OCFS2 Filesystem
# - new imports
#
# Revision 1.1  2009/09/28 15:13:36  marc
# moved from comoonics here
#
# Revision 1.6  2008/02/19 14:13:16  mark
# add support for type=auto
#
# Revision 1.5  2007/04/23 22:07:42  marc
# added fsck
#
# Revision 1.4  2007/03/26 08:29:17  marc
# - fixed some never used bugs
# - fixed bug with exclusive locking
# - added support for skipped filesystemdetection
# - logging
#
# Revision 1.3  2007/02/28 10:13:59  mark
# added mountpoint mkdir support
#
# Revision 1.2  2006/07/21 15:17:19  mark
# added support for lockex option
#
# Revision 1.1  2006/07/19 14:29:15  marc
# removed the filehierarchie
#
# Revision 1.5  2006/07/03 10:40:24  mark
# some bugfixes
#
# Revision 1.4  2006/06/29 08:23:08  mark
# added comments
# moved MountPoint to ComMountPoint.py
#
# Revision 1.3  2006/06/28 17:24:42  mark
# bug fixes
#
# Revision 1.2  2006/06/27 12:10:37  mark
# backup checkin
#
# Revision 1.1  2006/06/23 07:57:08  mark
# initial checkin (unstable)
#
