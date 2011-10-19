'''
Created on Apr 28, 2009

@author: marc
'''
import sys
sys.path.append('/usr/lib/python%s/site-packages/oldxml' % sys.version[:3])
import unittest
import baseSetup as setup

class test_Cdsl(unittest.TestCase):
    def test_A_CdslDestPaths(self):
        for cdsl in repository.getCdsls():
            dp1=cdsl.getDestPaths()
            dp2=setupCdsls.results[cdsl.src][3]
            self.assertEquals(dp1, dp2, "Destinationpaths for cdsl %s are not equal: %s != %s" %(cdsl.src, dp1, dp2))
#            print "destpaths(%s): %s" %(cdsl, cdsl.getDestPaths())

    def test_B_CdslSourcePaths(self):
        for cdsl in repository.getCdsls():
            sp1=cdsl.getSourcePaths()
            sp2=setupCdsls.results[cdsl.src][2]
            self.assertEquals(sp1, sp2, "Sourcepaths for cdsl %s are not equal: %s != %s" %(cdsl.src, sp1, sp2))
#            print "sourcepaths(%s): %s" %(cdsl, cdsl.getSourcePaths())    
            
    def test_D_getChilds(self):
        from comoonics.cdsl.ComCdslRepository import CdslNotFoundException
        try:
            cdsl = repository.getCdsl("hd/sd")
            resultchilds= [ "hd/sd/hd",
                            "hd/sd/hf" ]
            for child in cdsl.getChilds():
                self.assertTrue(child.src in resultchilds, "Could not find child cdsl %s for parent cdsl %s." %(cdsl, child))
        except CdslNotFoundException:
            self.assert_("Could not find cdsl under \"hd/sd\".")

    def test_E_CdslsCreate(self):
        from comoonics.cdsl import cmpbysubdirs
        _cdsls=repository.getCdsls()
        _cdsls.sort(cmpbysubdirs)
        for _cdsl in _cdsls:
#            print "+ %s\n" %_cdsl
            _cdsl.commit(force=True)
            self.assertTrue(_cdsl.exists(), "%s CDSL %s does not exist!" %(_cdsl.type, _cdsl))

    def test_F_CdslsValidate(self):
        from comoonics.cdsl.ComCdslValidate import CdslValidate
        validate=CdslValidate(repository, setupCluster.clusterInfos[0])
        _added, _removed=validate.validate(onfilesystem=False, update=False, root=setup.tmppath)
#        print "Validate.."
        self.assertTrue(len(_added)==0 and len(_removed)==0, "Cdslsearch didn't succeed. Added %s, Removed %s" %(_added, _removed))
#        print "Ok\n"
        _cdsls=repository.getCdsls()
#        print "-%s" %_cdsls[-1]
        _removed_cdsl=repository.delete(_cdsls[-1])
        _added, _removed=validate.validate(onfilesystem=True, update=True, root=setup.tmppath)
        self.assertEquals(_added[0].src, _removed_cdsl.src, "The removed cdsl %s is different from the added one %s" %(_added[0].src, _removed_cdsl.src))
        for backupfile in validate.backupfiles:
            os.remove(backupfile)

    def test_G_CdslValidate(self):
        from comoonics.cdsl.ComCdslValidate import CdslValidate
        import shutil
        import StringIO
        _cdsls=repository.getCdsls()
        shutil.move(os.path.join(repository.workingdir, repository.resource), os.path.join(repository.workingdir, repository.resource+".bak"))
        file(os.path.join(repository.workingdir, repository.resource), "w+") 
        validate=CdslValidate(repository, setupCluster.clusterInfos[0])
        _added, _removed=validate.validate(onfilesystem=True, update=True, root=setup.tmppath)
        identical=True
        buf1=StringIO.StringIO()
        buf2=StringIO.StringIO()
        for _cdsl in repository.getCdsls():
            buf2.write("%s, " %_cdsl)
            
        for _cdsl in _cdsls:
            buf1.write("%s, " %_cdsl)
            if not repository.hasCdsl(_cdsl.src):
                identical=False
        if len(_cdsls) != len(repository.cdsls):
            identical=False
        self.failUnless(identical, "The cdsls in the reconstructed repository and old cdsls are not the same. %s!=%s"%(buf1.getvalue(), buf2.getvalue()) )
        os.remove(os.path.join(repository.workingdir, repository.resource+".bak"))
        for backupfile in validate.backupfiles:
            os.remove(backupfile)
    
    def test_Y_CdslsDeleteNoForce(self):
        import shutil
        from comoonics.cdsl import cmpbysubdirs
        from comoonics.ComPath import Path
        wpath=Path()
        _cdslsrev=repository.getCdsls()
        _cdslsrev.sort(cmpbysubdirs)
        _cdslsrev.reverse()
        for _cdsl in _cdslsrev:
#            print "- %s\n" %_cdsl.src
            _cdsl.delete(recursive=True, force=False, symbolic=True)
            _files2remove=list()
            if _cdsl.isHostdependent():
                for nodeid in setupCluster.clusterInfos[0].getNodeIdentifiers('id'):
                    _file="%s.%s" %(_cdsl.src, nodeid)
                    _files2remove.append(_file)
                _files2remove.append("%s.%s" %(_cdsl.src, "default"))
            wpath.pushd(setupCdsls.repository.workingdir)
            for _file in _files2remove:
#                print "- %s" %_file
                if os.path.isdir(_file):
                    shutil.rmtree(_file)
#                    os.removedirs(_file)
                else:
                    os.remove(_file)
            wpath.popd()
            self.assertFalse(_cdsl.exists(), "%s CDSL %s does exist although it was removed before." %(_cdsl.type, _cdsl))
            for __cdsl in setupCdsls.repository.getCdsls():
                self.assertTrue(__cdsl.exists(), "The still existent %s cdsl %s does not exist any more. Deleted %s" %(__cdsl.type, __cdsl, _cdsl))
        setupCdsls._createRepository(setupCluster.clusterInfos[0])
        setupCdsls._createCDSLFiles(setup.tmppath)
        _cdsls=repository.getCdsls()
        _cdsls.sort(cmpbysubdirs)
        for _cdsl in _cdsls:
            _cdsl.commit(force=True)

    def test_Z_CdslsDelete(self):
        from comoonics.cdsl import cmpbysubdirs
        _cdslsrev=repository.getCdsls()
        _cdslsrev.sort(cmpbysubdirs)
        _cdslsrev.reverse()
        for _cdsl in _cdslsrev:
#            print "- %s\n" %_cdsl.src
            _cdsl.delete(recursive=False, symbolic=False, force=False)
            self.assertFalse(_cdsl.exists(), "%s CDSL %s exists although it was removed before." %(_cdsl.type, _cdsl))
            for __cdsl in  repository.getCdsls():
                self.assertTrue(__cdsl.exists(), "The still existant %s cdsl %s does not exist any more." %(__cdsl.type, __cdsl))

from comoonics.cdsl import getCdslRepository
import os
#import sys;sys.argv = ['', 'Test.testName']
olddir=os.path.realpath(os.curdir)
os.chdir(setup.tmppath)
setupCluster=setup.SetupCluster()        
if __name__ == "__main__":
    repository=getCdslRepository(root=setup.tmppath, usenodeids="True")  
    setupCdsls=setup.SetupCDSLs(repository)
    repository.buildInfrastructure(setupCluster.clusterInfos[0])
    setupCdsls.setupCDSLInfrastructure(setup.tmppath, repository, setupCluster.clusterInfos[0])
    module=setup.MyTestProgram(module=test_Cdsl(methodName='run'))
    if module.result.wasSuccessful():
        setupCdsls.cleanUpInfrastructure(setup.tmppath, repository, setupCluster.clusterInfos[0])
        setup.cleanup()
    os.chdir(olddir)
    sys.exit(module.result.wasSuccessful())    
