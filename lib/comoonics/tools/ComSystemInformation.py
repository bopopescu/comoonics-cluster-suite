"""ComSystemInformation

Classes to automatically collect informations of this system.

"""


# here is some internal information
# $Id: ComSystemInformation.py,v 1.1 2011-02-15 14:58:21 marc Exp $
#
import re
import os

from comoonics import ComLog
from comoonics import ComSystem
from comoonics.ComExceptions import ComException

class SystemInformationNotFound(ComException):
    pass

__version__ = "$Revision: 1.1 $"
# $Source: /atix/ATIX/CVSROOT/nashead2004/management/comoonics-clustersuite/python/lib/comoonics/tools/ComSystemInformation.py,v $

class SystemType(object):
    """
    EnumClass representing possible types of systems
    Possible types are SINGLE, CLUSTER, UNKNOWN
    """
    strtypes=[ "singleserver", "cluster", "unknown"]
    def __init__(self, itype):
        self.itype=itype
    def __str__(self):
        return self.strtypes[self.itype]

class SystemTypes(object):
    SINGLE=SystemType(0)
    CLUSTER=SystemType(1)
    UNKNOWN=SystemType(2)

def getSystemInformation(*args, **kwds):
    if RHOpensharedrootSystemInformation.check(*args, **kwds):
        return RHOpensharedrootSystemInformation(*args, **kwds)
    elif RedhatClusterSystemInformation.check(*args, **kwds):
        return RedhatClusterSystemInformation(*args, **kwds)
    elif RedhatSystemInformation.check(*args, **kwds):
        return RedhatSystemInformation(*args, **kwds)
    elif RPMLinuxSystemInformation.check(*args, **kwds):
        return RPMLinuxSystemInformation(*args, **kwds)
    elif LinuxSystemInformation.check(*args, **kwds):
        return LinuxSystemInformation(*args, **kwds)
    raise SystemInformationNotFound("Could not find system information for this system")

class SystemInformation(object):
    log=ComLog.getLogger("SystemInformation")
    """
    Abstract class that can be instantiated as it calls a factory through the constructor and returns an
    apropriate Instance of the SystemInformationclass representing your system
    First only LinuxSystemInformation is possible.
    """
    def check(*args, **kwds):
        """
        Static method that returns true if this system is of that type
        """
        return False
    check=staticmethod(check)

    def __init__(self, *args, **kwds):
        """
        The constructor instantiating an object of class SystemInformation
        """
        self.architecture="unknown"
        self.operatingsystem="unknown"
        self.kernelversion="unknown"
        self.name="unknown"
        self.type=SystemTypes.UNKNOWN
        self.uptime=0
        self.installedsoftware=list()
        self.features=list()

    def getFeatures(self):
        """
        Returns a list of features enabled in this system
        """
        return self.features

    def getArchitecture(self):
        """
        Returns a string representation of the architecture of this SystemInformation instance
        """
        return self.architecture
    def getOperatingsystem(self):
        """
        Returns the string representation of the operatingsystem
        """
        return self.operatingsystem

    def getKernelversion(self):
        """
        Returns a string representation of the installed kernelversion
        """
        return self.kernelversion

    def getType(self):
        """
        Returns the SystemType of this system
        """
        return self.type

    def getName(self):
        """
        Returns the Name of this system
        """
        return self.name

    def getUptime(self):
        """
        Returns the uptime of this system as string
        """
        return self.uptime

    def getInstalledSoftware(self, name=None):
        """
        Returns a list of installed software
        """
        self.updateInstalledSoftware(name)
        return self.installedsoftware

    def updateInstalledSoftware(self, name=None):
        """
        protected method that updates the installedsoftwarelist
        Does nothing here
        """
        pass

    def report(self, actions=None, destination=None):
        """
        executes a system report for this implementation
        """
        pass

    def isCluster(self):
        """
        returns true if this system is a cluster
        """
        return self.type == SystemTypes.CLUSTER
    def isSingle(self):
        """
        returns true if this system is a cluster
        """
        return self.type == SystemTypes.SINGLE
    def isUnknown(self):
        """
        returns true if this system is a cluster
        """
        return self.type == SystemTypes.UNKNOWN

    def __str__(self):
        return "%s %s<%s> %s %s %s" %(self.getOperatingsystem(), self.getName(), self.getType().__str__(),
                                      self.getKernelversion(), self.getUptime(), self.getArchitecture())

class LinuxSystemInformation(SystemInformation):
    """
    Implementation of an unknown Linux System
    """
    def check(*args, **kwds):
        ret=False
        SystemInformation.log.debug("LinuxSystemInformation: check(args: %s, kwds: %s)" %(args, kwds))
        try:
            if not kwds and not args:
                out = os.uname()[0]
                if re.compile("linux", re.I).search(out):
                    ret=True
            elif kwds.has_key("operatingsystem") and \
                (re.compile("linux", re.I).search(kwds["operatingsystem"]) or \
                 re.compile("centos", re.I).search(kwds["operatingsystem"]) or \
                 re.compile("fedora", re.I).search(kwds["operatingsystem"]) or \
                 re.compile("redhat", re.I).search(kwds["operatingsystem"])):
#                SystemInformation.log.debug("checking from keywords for LinuxSystemInformation %s" %(kwds))
                ret=True
        finally:
            return ret
    check=staticmethod(check)

    def __init__(self, *args, **kwds):
        super(LinuxSystemInformation, self).__init__(*args, **kwds)
        self.features.append("linux")
        if not kwds and not args:
            (self.operatingsystem, self.name, self.kernelversion, self.kerneltime, self.architecture)=os.uname()
            fs=open("/proc/uptime", "r")
            self.uptime=fs.readline().splitlines()[0].split(".")[0]
            fs.close()
            self.type=SystemTypes.SINGLE
        elif kwds:
            self.__dict__.update(dict(kwds))
            self.type=SystemTypes.SINGLE

class RPMLinuxSystemInformation(LinuxSystemInformation):
    RPM_CMD="rpm"
    def check(*args, **kwds):
        ret=False
        try:
            if not kwds and not args:
                ComSystem.execLocalOutput("%s -qf $(which rpm)" %(RPMLinuxSystemInformation.RPM_CMD))
                ret= True
            elif kwds.has_key("operatingsystem") and  \
                (re.compile("suse", re.I).search(kwds["operatingsystem"]) or \
                 re.compile("centos", re.I).search(kwds["operatingsystem"]) or \
                 re.compile("fedora", re.I).search(kwds["operatingsystem"]) or \
                 re.compile("redhat", re.I).search(kwds["operatingsystem"]) or \
                 re.compile("red hat", re.I).search(kwds["operatingsystem"])):
                ret=True
        finally:
            return ret
    check=staticmethod(check)

    def __init__(self, *args, **kwds):
        super(RPMLinuxSystemInformation, self).__init__(*args, **kwds)
        self.features.append("rpm")
        if kwds:
            self.__dict__.update(dict(kwds))
            self.type=SystemTypes.SINGLE

    def updateInstalledSoftware(self, name=None):
        import rpm
        ts=rpm.ts()
        mi=ts.dbMatch()
        if name:
            mi.pattern("name", rpm.RPMMIRE_GLOB, name)
        for hdr in mi:
            self.installedsoftware.append(hdr)

class RedhatSystemInformation(RPMLinuxSystemInformation):
    REDHAT_RELEASE_FILE="/etc/redhat-release"
    def check(*args, **kwds):
        ret=False
        try:
            if not kwds and not args:
                ret=os.path.exists(RedhatSystemInformation.REDHAT_RELEASE_FILE)
            elif kwds.has_key("operatingsystem") and \
                 (re.compile("centos", re.I).search(kwds["operatingsystem"]) or \
                  re.compile("fedora", re.I).search(kwds["operatingsystem"]) or \
                  re.compile("red hat", re.I).search(kwds["operatingsystem"]) or \
                  re.compile("redhat", re.I).search(kwds["operatingsystem"])):
                ret=True
        finally:
            return ret
    check=staticmethod(check)

    def __init__(self, *args, **kwds):
        super(RedhatSystemInformation, self).__init__(*args, **kwds)
        self.features.append("redhat")
        if not kwds and not args:
            f=file(self.REDHAT_RELEASE_FILE, "r")
            self.operatingsystem=f.readline().splitlines(False)[0]
            f.close()
        else:
            self.__dict__.update(dict(kwds))
            self.type=SystemTypes.SINGLE

class RedhatClusterSystemInformation(RedhatSystemInformation):
    REDHAT_CLUSTER_CONF="/etc/cluster/cluster.conf"
    CLUSTAT_CMD="/usr/sbin/clustat"
    XPATH_CLUSTERNAME="/cluster/@name"
    def check(*args, **kwds):
        ret=False
        try:
            if not kwds and not args:
#                SystemInformation.log.debug("Checking for cluster availability")
                if os.path.exists(RedhatClusterSystemInformation.REDHAT_CLUSTER_CONF) and ComSystem.execLocal("%s >/dev/null 2>&1" %(RedhatClusterSystemInformation.CLUSTAT_CMD))==0:
#                    SystemInformation.log.debug("OK")
                    ret=True
#                else:
#                    SystemInformation.log.debug("FAILED")
            else:
                if kwds.has_key("type") and kwds["type"]=="cluster":
                    ret=True
        finally:
            return ret
    def __init__(self, *args, **kwds):
        from comoonics import XmlTools
        super(RedhatClusterSystemInformation, self).__init__(*args, **kwds)
        self.features.append("redhatcluster")
        if not kwds and not args:
            if os.path.exists(self.REDHAT_CLUSTER_CONF):
                self.cluster_conf=XmlTools.parseXMLFile(self.REDHAT_CLUSTER_CONF)
                self.type=SystemTypes.CLUSTER
                self.name=self.getClusterName()
        else:
            self.__dict__.update(dict(kwds))
            self.type=SystemTypes.CLUSTER

    def getClusterName(self):
        """
        FIXME (marc): Should go in some cluster api (ccs_xml_query!!)
            Cluster->getClusterName()
              |
              -> RedhatCluster->getClusterName()
        """
        from comoonics import XmlTools
        if self.type==SystemTypes.CLUSTER:
            return XmlTools.evaluateXPath(self.XPATH_CLUSTERNAME, self.cluster_conf)[0]
        else:
            return "unknown"

    check=staticmethod(check)


class RHOpensharedrootSystemInformation(RedhatClusterSystemInformation):
    OSR_RELEASE="/etc/comoonics-release"

    def check(*args, **kwds):
        ret=False
        try:
            if not kwds and not args:
#                SystemInformation.log.debug("Checking for cluster availability")
                if os.path.exists(RHOpensharedrootSystemInformation.OSR_RELEASE):
#                    SystemInformation.log.debug("OK")
                    ret=True
#                else:
#                    SystemInformation.log.debug("FAILED")
            else:
                if kwds.has_key("type") and kwds["type"]=="osrcluster":
                    ret=True
        finally:
            return ret

    def __init__(self, *args, **kwds):
        super(RHOpensharedrootSystemInformation, self).__init__(*args, **kwds)
        self.features.append("opensharedroot")
        self.type=SystemTypes.CLUSTER
        if not kwds and not args:
            pass
        else:
            self.__dict__.update(dict(kwds))

    check=staticmethod(check)
