'''
Created on 30.03.2011

@author: marc
'''
import unittest
import cStringIO
from comoonics.cmdb.ComSoftwareCMDB import SoftwareCMDB
from comoonics.cmdb.Reports import CSVMainReportPackages

class Test(unittest.TestCase):
    def setUp(self):
        self.software_cmdb=SoftwareCMDB(hostname="axqad107-1", user="cmdb", password="cmdb", database="software_cmdb", table="software_cmdb")
        self.packages=self.software_cmdb.getPackages(["lilr642", "lilr602"], "lilr601", None, 0, 0, ['name LIKE "%GFS-kernel%"'])
        self.differences=self.packages.differences()
        self.report=CSVMainReportPackages(self.differences, "lilr601")

    def tearDown(self):
        pass

    def testReport(self):
        buffer=cStringIO.StringIO()
        self.report.report(outputchannel=buffer)
        print buffer.getvalue()
        expectedstring=""""source: name","name","architecture","main: version","main: subversion","source: version","source: subversion"
"lilr642","GFS-kernel-debuginfo","x86_64","2.6.9","72.2.0.2","not installed","not installed"
"lilr602","GFS-kernel-debuginfo","x86_64","2.6.9","72.2.0.2","not installed","not installed"
"lilr602","GFS-kernel-debuginfo","x86_64","not installed","not installed","2.6.9","80.9.el4_7.5.hotfix.1"
"lilr642","GFS-kernel-largesmp","x86_64","not installed","not installed","2.6.9","80.9.el4_7.1"
"lilr642","GFS-kernel-largesmp","x86_64","2.6.9","80.9.el4_7.5.hotfix.1","not installed","not installed"
"""
        self.assertEquals(buffer.getvalue(), expectedstring)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()