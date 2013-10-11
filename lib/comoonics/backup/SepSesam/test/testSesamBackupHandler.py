'''
Created on 06.08.2013

@author: marc
'''
import unittest

class Test(unittest.TestCase):
   backupproperties1={
                     "cmd": "./sm_cmd",
                     "client": "testclient",
                     "group": "testgroup",
                     "level": "D",
                     "waitcount": "1"}
   backupproperties2={
                     "cmd": "./sm_cmd",
                     "client": "testclient",
                     "job": "testjob",
                     "level": "D",
                     "waitcount": "1"}
   taskname="task123"
   def testSesamBackupHandler1(self):
      import comoonics.backup.SepSesam
      self.assertRaises(comoonics.backup.SepSesam.SepSesam.SepSesamIsNotInstalledError, 
                        comoonics.backup.SepSesam.SepSesamBackupHandler.SepSesamBackupHandler, self.taskname, {"client":self.backupproperties1["client"]})
      
   def testSesamBackupHandler2(self):
      import comoonics.backup.SepSesam
      self.assertRaises(TypeError, 
                        comoonics.backup.SepSesam.SepSesamBackupHandler.SepSesamBackupHandler, None, {"cmd": self.backupproperties1["cmd"]})
      
   def testSesamBackupHandler3(self):
      import comoonics.backup.SepSesam
      self.assertTrue(comoonics.backup.SepSesam.SepSesamBackupHandler.SepSesamBackupHandler(self.taskname, self.backupproperties1))
      
   def testSesamBackupGroupCreate(self):
      self.backupproperties1.update({"taskname": self.taskname})
      self.assertMultiLineEqual(self._testSesamAction(self.taskname, self.backupproperties1, 
                                                      "createArchive", "/tmp", None, True), 
                                """add task %(taskname)s -G %(group)s -c %(client)s -s /tmp
STATUS=SUCCESS MSG="SC20130809061320239@9DdOQVSaem6"
remove task %(taskname)s
""" %self.backupproperties1)
   
   def testSesamBackupGroup(self):
      self.assertMultiLineEqual(self._testSesamAction("", self.backupproperties1, 
                                                      "createArchive", "/tmp", None, False), 
                                """STATUS=SUCCESS MSG="SC20130809061320239@9DdOQVSaem6"
""" %self.backupproperties1)
   
   def testSesamBackupJobCreate(self):
      if self.backupproperties2.has_key("group"): del self.backupproperties2["group"]
      self.backupproperties2.update({"taskname": self.taskname})
      self.assertMultiLineEqual(self._testSesamAction(self.taskname, self.backupproperties2, 
                                                      "createArchive", "/tmp", None, True), 
                                """add task %(taskname)s -c %(client)s -j %(job)s -s /tmp
STATUS=SUCCESS MSG="SC20130809061320239@9DdOQVSaem6"
remove task %(taskname)s
""" %self.backupproperties2)
      
   def testSesamBackupJob(self):
      if self.backupproperties2.has_key("group"): del self.backupproperties2["group"]
      self.backupproperties2.update({"taskname": self.taskname})
      self.assertMultiLineEqual(self._testSesamAction(self.taskname, self.backupproperties2, 
                                                      "createArchive", "/tmp", None, False), 
                                """STATUS=SUCCESS MSG="SC20130809061320239@9DdOQVSaem6"
""" %self.backupproperties2)
      
   def testSesamBackupJobAnon(self):
      if self.backupproperties2.has_key("group"): del self.backupproperties2["group"]
      if self.backupproperties2.has_key("taskname"): del self.backupproperties2["taskname"]
      self.assertMultiLineEqual(self._testSesamAction("", self.backupproperties2, 
                                                      "createArchive", "/tmp", None, False), 
                                """STATUS=SUCCESS MSG="SC20130809061320239@9DdOQVSaem6"
""" %self.backupproperties2)
   
   def _testSesamAction(self, jobname, properties, action, *args):
      import comoonics.backup.SepSesam
      handler=comoonics.backup.SepSesam.SepSesamBackupHandler.SepSesamBackupHandler(jobname, properties)
      getattr(handler, action)(*args)
      return handler.getLastOutput()

if __name__ == "__main__":
   #import sys;sys.argv = ['', 'Test.testName']
   unittest.main()