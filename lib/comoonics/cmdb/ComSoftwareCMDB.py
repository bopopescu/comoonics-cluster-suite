"""
Class for the software_cmdb

Methods for comparing systems and the like
"""
# here is some internal information
# $Id: ComSoftwareCMDB.py,v 1.8 2007-03-14 16:51:42 marc Exp $
#

import os
from comoonics.cmdb.ComBaseDB import BaseDB
from comoonics import ComLog

class SoftwareCMDB(BaseDB):
    """
    Class for the software_cmdb
    """
    NOT_INSTALLED_STRING="not installed"
    SELECT_FOR_SOFTWARE=("channel",
                         "channelversion",
                         "name",
                         "version",
                         "subversion",
                         "architecture",
                         "sw_type")
    COMPARE_2_SOFTWARE=("name",
                        "version",
                        "subversion",
                        "architecture")

    log=ComLog.getLogger("SoftwareCMDB")

    def getAllColnamesNotInstalled(colnames, colparts, sourcenames):
         ret_colnames=list()
         ilen=len(sourcenames)
         jlen=len(colnames)
         klen=len(colparts)
#         self.log.debug("ilen: %u, jlen: %u, klen: %u" %(ilen, jlen, klen))
         basecolnames=list(colnames)
         for i in range(ilen):
             copy_colnames=""
             for j in range(jlen):
                 if j>=klen*i and j<klen*(i+1):
                     copy_colnames+="\""+SoftwareCMDB.NOT_INSTALLED_STRING+"\" AS "+colnames[j]+", "
                 else:
                     copy_colnames+="rpms"+str(i)+"."+colparts[j%klen]+" AS "+colnames[i]+", "
#             self.log.debug("getAllColnamesNotInstalled: "+copy_colnames[:-2])
             ret_colnames.append(copy_colnames[:-2])
         return ret_colnames

    getAllColnamesNotInstalled=staticmethod(getAllColnamesNotInstalled)

    def __init__(self, **kwds):
        """
        Creates a Software CMDB class giving methods to deal with the sql table "software_cmdb"
        __init__(hostname=.., user=.., password=.., database=.., tablename=..)
        __init__(dbhandle=.., tablename=..)
        """
        if not kwds.has_key("tablename"):
            kwds["tablename"]="software_cmdb"
        super(SoftwareCMDB, self).__init__(**kwds)

    def getClusters(self):
        query="SELECT DISTINCT clustername FROM %s" %(self.tablename)
        rs=self.selectQuery(query)
        row=rs.fetch_row()
        clusters=list()
        while row:
            clusters.append(row[0][0])
            row=rs.fetch_row()
        return clusters

    def getSoftwareForCategory(self, category, select="*", limitup=0, limitdown=0, where=None, orderby=None):
        from ComSource import Source
        source=Source(dbhandle=self.db)
        sname=source.getSourceForCategory(category)
        return self.getSoftware(sname, select, limitup, limitdown, where)

    def getSoftware(self, clustername, select="*", limitup=0, limitdown=0, where=None, orderby=None):
        if where==None:
            where=list()
        limit=BaseDB.getLimit(limitup, limitdown)
        where.append("clustername=\"%s\"" %(clustername))
        self.log.debug("where: %s" %(where))
        whereclause=BaseDB.resolveWhere(where)
        orderbyclause=BaseDB.resolveOrderBy(orderby)
        self.log.debug("whereclause: %s" %(whereclause))
        query="SELECT DISTINCT %s FROM %s %s %s %s;" %(", ".join(select), self.tablename, whereclause, orderbyclause, limit)
        self.log.debug("query: %s" %(query))
        return self.selectQuery(query)

    def getColnamesForDiff(sourcenames, colnames=COMPARE_2_SOFTWARE):
        colnames_ret=list()
        colnames_ret.append(colnames[0])
        for sourcename in sourcenames:
            for colname in colnames[1:]:
                colnames_ret.append(colname+"_"+BaseDB.formatToSQLCompat(sourcename))
        return colnames_ret
    getColnamesForDiff=staticmethod(getColnamesForDiff)

    def getDiffsFromCategories(self, categories, limitup=0, limitdown=0, where=None, orderby=None, Diffs=True, NotInstalled=True):
        """
        Returns a resultset of differences of the given categories.
        Parameter are the sourcesnames to compare
        RESTRICTION: Right now only the first 2 categories can be compared (SHOULD BE FIXED)
        """
        from ComSource import Source
        sources=list()
        source=Source(dbhandle=self.db)
        for category in categories:
            sname=source.getSourceForCategory(category)
            if sname:
                sources.append(sname)
        if len(sources) == 0:
            return None
        else:
            return self.getDiffsFromSources(sources, SoftwareCMDB.getColnamesForDiff(categories), limitup, limitdown, where, orderby, Diffs, NotInstalled)

    def getDiffsFromSources(self, sourcenames, colnames=None, limitup=0, limitdown=0, where=None, orderby=None, Diffs=True, NotInstalled=True):
        """
        Returns a resultset of differences of the given sourcenames.
        Parameter are the sourcesnames to compare
        RESTRICTION: Right now only the first 2 sourcenames can be compared (SHOULD BE FIXED)
        """
        orderbyclause=BaseDB.resolveOrderBy(orderby)
        limit=BaseDB.getLimit(limitup, limitdown)
        self.log.debug("where: %s" %(where))
        self.log.debug("orderbyclause: %s, limit: %s, diffs: %s, notinstalled: %s" %(orderbyclause, limit, Diffs, NotInstalled))
        if not colnames:
            self.log.debug("getting colnames")
            colnames=self.getColnamesForDiff(sourcenames)
        j=0
#        ComLog.getLogger().debug("query %s" % query)
        queries=list()
        if Diffs:
            queries.append(self.selectQueryOnlyDiffs(sourcenames, colnames, SoftwareCMDB.COMPARE_2_SOFTWARE, where))

        if NotInstalled:
            queries+=self.selectQueriesNotInstalled(sourcenames, colnames, SoftwareCMDB.COMPARE_2_SOFTWARE, where)
        union="\n UNION \n".join(queries)
        if orderbyclause and orderbyclause!="":
            union+="\n"+orderbyclause
        if limit and limit != "":
            union+="\n"+limit
        self.log.debug("union: "+union)
        return self.selectQuery(union)

    def selectQueriesNotInstalled(self, sourcenames, allcolnamesr, colnames=COMPARE_2_SOFTWARE, where=None):
        queries=list()
#        querycolumns=SoftwareCMDB.getAllColnamesNotInstalled(colnames[1:], SoftwareCMDB.COMPARE_2_SOFTWARE[1:], sourcenames)
#        self.log.debug("querycolumns: %s" %(querycolumns))
        allcolnames=list()
        allcolnames.append(colnames[0])
        for i in range(len(sourcenames)):
            for colname in colnames[1:]:
                allcolnames.append("%s."+colname)
        #allcolnamesr=colnames
        #allcolnamesr=SoftwareCMDB.getColnamesForDiff(sourcenames, colnames)
        notinstalled=list()
        dbs=list()
        for i in range(len(sourcenames)):
            dbs.append("rpms"+str(i))
        self.log.debug("dbs[%u]: %s" %(len(dbs), dbs))
        self.log.debug("allcolnamesr[%u]: %s" %(len(allcolnamesr), allcolnamesr))
        self.log.debug("allcolnames[%u]: %s" %(len(allcolnames), allcolnames))
        l=len(colnames[1:])
        self.log.debug("colnames/l[%u]:%s" %(l, colnames))
        m=len(sourcenames)
        self.log.debug("sourcenames/m[%u]:%s" %(m, sourcenames))
        p=0
        for i in range(len(sourcenames)*(len(sourcenames)-1)):
            qname="q%u" %(i)
            j=i%l
            n=i%m
            if n==0:
                for k in range(l):
                    notinstalled.append("\""+SoftwareCMDB.NOT_INSTALLED_STRING+"\"")
            newcolnames=list(allcolnames[1:])
            newdbs=list(dbs)
            newdbs2=list()
            for k in range(len(notinstalled)):
#                self.log.debug("newcolnames[%u], j=%u, k=%u, len(notinstalled)=%u" %((n*len(notinstalled)+k)%len(allcolnames[1:]), j, k, len(notinstalled)))
                newcolnames[(n*len(notinstalled)+k)%len(allcolnames[1:])]=notinstalled[k]
                if k%l==0:
                    self.log.debug("[%u] dbs removing: k mod l: %u, k mod m: %u, n: %u, dbs[%u], %s/%s=removing" %(i, k%l, k%m, n, (n%m)%len(newdbs), newdbs[(n%m)%len(newdbs)], newdbs))
                    newdbs2.append(newdbs[(n%m)%len(newdbs)])
                    del newdbs[(n%m)%len(newdbs)]
            selectcols=list()
            joins=list()
            whereequals=list()
            wherenot=list()
            o=0
            for k in range(len(allcolnamesr[1:])):
                selectcols.append(newcolnames[k]+" AS "+allcolnamesr[k+1])
                if k%l==0 and newcolnames[k].find(SoftwareCMDB.NOT_INSTALLED_STRING)<0:
#                    self.log.debug("add join and whereequals k mod m %u; %u, m:%u" %(k%m, len(notinstalled), m))
                    if len(joins)==0:
                        joins.append("   FROM "+self.tablename+" AS %s")
                    else:
                        joins.append("   JOIN "+self.tablename+" AS %s USING (name, architecture) ")
                    whereequals.append("%s.clustername=\""+sourcenames[o]+"\"")
                    o+=1
                elif k%l==0:
                    wherenot.append(" AND (%s.name,%s.architecture) NOT IN (SELECT %s.name, %s.architecture FROM "+self.tablename+" AS %s WHERE %s.clustername=\""+sourcenames[o]+"\")")
                    o+=1
            o=0
            for k in range(len(selectcols)):
                if selectcols[k].find(SoftwareCMDB.NOT_INSTALLED_STRING)<0:
#                    self.log.debug("k: %u, o: %u, selectcols[k]: %s, newdbs: %s" %(k, o, selectcols[k], newdbs))
                    selectcols[k]=selectcols[k] %(newdbs[o])
                    if k%l==l-1:
                        o+=1
            self.log.debug("joins: %s, whereequals: %s, newdbs: %s" %(joins, whereequals, newdbs))
            for k in range(len(joins)):
                joins[k]=joins[k] %(newdbs[k])
                whereequals[k]=whereequals[k] %(newdbs[k])

            for k in range(len(wherenot)):
                wherenot[k]=wherenot[k] %(newdbs[0], newdbs[0], qname+newdbs2[k], qname+newdbs2[k], qname+newdbs2[k], qname+newdbs2[k])

            whererest=""
            if where and type(where)==str and where!="":
                whererest="\n   AND "+newdbs[0]+"."+where
            elif where and type(where)==list:
                thestr="\n   AND "+newdbs[0]+"."
                whererest=thestr+thestr.join(where)

            queries.append("SELECT "+newdbs[0]+"."+allcolnames[0]+" AS "+allcolnamesr[0]+", \n      "+", ".join(selectcols)+\
                           "\n"+"\n".join(joins)+\
                           "\n   WHERE "+\
                           " AND ".join(whereequals)+\
                           "\n   "+\
                           "\n   ".join(wherenot)+
                           whererest)
        return queries

    def selectQueryOnlyDiffs(self, sourcenames, allcolnamesr, colnames=COMPARE_2_SOFTWARE, where=None):
        """
        Returns the select query that only filters differences between installed Software.
        See selectNotInstalledQuery.
        """
        j=0
        version_unequalcols=list()
        subversion_unequalcols=list()
        joins=list()
        columns=list()
        dbs=list()
        wherelst=list()
        for i in range(len(sourcenames)):
            formatedname=self.formatToSQLCompat(sourcenames[i])
            columns.append("rpms"+str(i)+"."+colnames[1]+" AS "+allcolnamesr[j+1]+", rpms"+str(i)+"."+colnames[2]+" AS "+\
                           allcolnamesr[j+2]+", rpms"+str(i)+"."+colnames[3]+" AS "+allcolnamesr[j+3])
            dbs.append(self.tablename+" AS rpms"+str(i))
            if i > 0:
                joins.append("JOIN "+dbs[i]+" USING (name, architecture) ")
            wherelst.append("rpms"+str(i)+".clustername=\""+sourcenames[i]+"\"")
            version_unequalcols.append("rpms"+str(i)+".version")
            subversion_unequalcols.append("rpms"+str(i)+".subversion")

            j+=3

        whererest=""
        if where and type(where)==str and where!="":
            whererest="\n   AND rpms0."+where
        elif where and type(where)==list:
            whererest="\n   AND rpms0."+"\n   AND rpms0.".join(where)

        query="SELECT rpms0."+colnames[0]+" AS "+allcolnamesr[0]+", "+','.join(columns)+"\n FROM "+dbs[0]+"\n"+\
              "\n ".join(joins)+\
              "\n WHERE "+" AND ".join(wherelst)+"\n   AND ("+\
              " OR ".join(BaseDB.BinOperatorFromList(version_unequalcols, "!="))+"\n   OR "+\
              " OR ".join(BaseDB.BinOperatorFromList(subversion_unequalcols, "!="))+")"+\
              whererest
        return query

    def updateRPM(self, rpm, name, channelname, channelversion):
        """
        Updates the given rpmheader in the software_cmdb of this cluster
        rpm: the rpm-header defined by python-rpm with extensions like in ComDSL (channelname and -version)
        name: the name of the cluster/system
        """
        insertquery="INSERT INTO %s VALUES(\"rpm\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\");" \
                    %(self.tablename, name, channelname, channelversion, rpm["name"], rpm["version"], rpm["release"], rpm["arch"])
        updatequery="UPDATE %s SET clustername=\"%s\", channel=\"%s\", channelversion=\"%s\", name=\"%s\", version=\"%s\", subversion=\"%s\", architecture=\"%s\" WHERE clustername=\"%s\" AND name=\"%s\";" \
                    %(self.tablename, name, channelname, channelversion, rpm["name"], rpm["version"], rpm["release"], rpm["arch"], name, rpm["name"])
        selectquery="SELECT name, version, subversion AS \"release\", architecture AS \"arch\", channel AS channelname, channelversion FROM %s WHERE clustername=\"%s\" AND name=\"%s\" AND architecture=\"%s\";" \
                    %(self.tablename, name, rpm["name"], rpm["arch"])
        #    ComLog.getLogger().debug("select %s" % selectquery)
        super(SoftwareCMDB, self).updateRPM(insertquery, updatequery, selectquery, rpm,
                                               ["version", "release", "channelname", "channelversion"],
                                               { "channelname": channelname, "channelversion": channelversion})

def test():
    colnames=["name", "c1", "c2", "c3"]
    sources=["s1", "s2", "s3"]
    softwarecmdb=SoftwareCMDB(hostname="localhost", user="atix", password="atix", database="atix_cmdb")
    print "Testing getColnamesForDiff"
    allcolnames=SoftwareCMDB.getColnamesForDiff(sources, colnames)
    print allcolnames

    print "Testing selectQueriesNotInstalled:"
    queries=softwarecmdb.selectQueriesNotInstalled(sources, allcolnames, colnames)
    for i in range(len(queries)):
        print "[%u]:%s" %(i, queries[i])
    print "%u queries" %(len(queries))

if __name__ == '__main__':
    test()

# $Log: ComSoftwareCMDB.py,v $
# Revision 1.8  2007-03-14 16:51:42  marc
# fixed AND instead of OR in OnlyDiffs Join
#
# Revision 1.7  2007/03/14 15:26:34  marc
# compatible with mysql3 dialect and ambigousness. (RHEL4 has mysql3) (4th)
#
# Revision 1.6  2007/03/14 15:11:37  marc
# compatible with mysql3 dialect and ambigousness. (RHEL4 has mysql3) (3rd)
#
# Revision 1.5  2007/03/14 14:57:21  marc
# compatible with mysql3 dialect and ambigousness. (RHEL4 has mysql3)
#
# Revision 1.4  2007/03/14 14:37:24  marc
# compatible with mysql3 dialect and ambigousness. (RHEL4 has mysql3)
#
# Revision 1.3  2007/03/14 13:16:48  marc
# added support for comparing multiple n>2 sources
#
# Revision 1.2  2007/03/05 16:10:30  marc
# first rpm version
#
# Revision 1.1  2007/02/23 12:42:23  marc
# initial revision
#
