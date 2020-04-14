

#         Case "San Jose"
#             DatabaseConnectionString = "PROVIDER=MSDASQL;driver={SQL Server};server=" & _
#                 "SVCARFTSDBNEW" & _
#                 ";database=" & _
#                 "Mercury" & _
#                 ";uid=WebUser;pwd=Web;"
#             ApplicationSite = "San Jose RFTS"



DSN = 'PROVIDER=MSDASQL;'     + \
      'driver={SQL Server};'  + \
      'server=SVCARFTSDBNEW;' + \
      'database=Mercury;'     + \
      'uid=WebUser;'          + \
      'pwd=Web;'


print 'DSN=', DSN

import pyodbc;
cnxn = pyodbc.connect(DSN)
cursor = cnxn.cursor()


#=============================================================================
# GET list of test runs (selected by TesterList , txtBoard, DTPicker1, DTPicker2)

TesterList = "'SJC-DCTR-PAR-1'"
txtBoard   = 'RF9840_SN008'
DTPicker1  = '12/14/2013'
DTPicker2  = '3/15/2014'

sql = '''SELECT 
        vcBoardNumber, 
        ISNULL(b.vcPartFamily, vcProductFamily) AS vcPartFamily, 
        biSessionID, 
        vctestplanName, 
        dtSessionStartTime, 
        dtSessionEndTime, 
        siStatusID, 
        vcSessionDesc, 
        vcTesterName, 
        bPublished FROM tsSessions a LEFT JOIN JTS_Cache.dbo.tsJTS b ON b.biJobID=a.iJobID WHERE '''
      
sql +=  "bHidden=0 AND vcTesterName IN (" + TesterList + ") AND "
               #                            SJC-DCTR-PAR-1
sql +=  "siStatusID In (2,4,11,12) AND "
sql +=  "vcBoardNumber Like '%" + txtBoard + "%' AND "
               #                 %RF9840_SN008%
sql +=  "dtSessionStartTime BETWEEN \'" + DTPicker1 + "' AND '" + DTPicker2 + "'"
               #                           12/14/2013                   3/15/2014
# ('RF9840_SN008', 'RF9840', 24325L, 'RF9840 Master Spec File II - TxM.xml', datetime.datetime(2014, 3, 6, 14, 25, 46, 20000), None, 12, 'RF9840, SN008  1. RF9840 50ohm TRX1-4 PDE2.1_3.xml  Mike Asker', 'SJC-DCTR-PAR-1', False)
#     RF9840_SN008
#     RF9840
#     24325
#     RF9840 Master Spec File II - TxM.xml
#     2014-03-06 14:25:46.020000
#     None
#     12
#     RF9840, SN008  1. RF9840 50ohm TRX1-4 PDE2.1_3.xml  Mike Asker
#     SJC-DCTR-PAR-1
#     False

sqla = sql

#=============================================================================
#  GET DB LOCATION
sql =  "Select COALESCE(vcDataLocation,'Mercury') from tssessions where bisessionid in (24325)"
#('Mercury_Cache', )
#    Mercury_Cache
#    dbDataLocation = dbDataLocation & ".dbo.sysObjects"    -->>   Mercury_Cache.dbo.sysObjects

#=============================================================================
# GET TEST SPECNAMES LIST
sql = "Select distinct    right(name,len(name)-charindex('_',name,3)) from Mercury_Cache.dbo.sysObjects where name like 't_24325%'"
# (u'test_GSMComposite_v2', )
#     test_GSMComposite_v2
# (u'test_TxMSave50OhmStateAdjustArb1', )
#     test_TxMSave50OhmStateAdjustArb1
# (u'TraceLoss', )
#     TraceLoss     


#=============================================================================
# GET LIST OF COLUMN HEADINGS FOR THE NAMED TEST
TableString = "t_24325_test_GSMComposite_v2"
sql = '''
select b.name, a.Name,  
   colid from mercury_cache.dbo.syscolumns     a Join mercury_cache.dbo.sysobjects b on b.id=a.id 
        where      b.type='u'  and  b.name in( '%s' )  Union select  b.name, a.Name, 
   colid from mercury_archive_1.dbo.syscolumns a Join mercury_archive_1.dbo.sysobjects b on b.id=a.id 
        where  b.type='u'  and  b.name in( '%s' )  union select  b.name, a.Name,
   colid from mercury_archive_2.dbo.syscolumns a Join mercury_archive_2.dbo.sysobjects b on b.id=a.id 
        where  b.type='u'  and  b.name in( '%s' )  order by b.name, colid
'''  % ( TableString, TableString, TableString )
# (u't_24325_test_GSMComposite_v2', u'DataID', 1)
#     t_24325_test_GSMComposite_v2
#     DataID
#     1
# (u't_24325_test_GSMComposite_v2', u'Temperature', 2)
#     t_24325_test_GSMComposite_v2
#     Temperature
#     2
# (u't_24325_test_GSMComposite_v2', u'ModSwitch', 3)
#     t_24325_test_GSMComposite_v2
#     ModSwitch
#     3
#  ...


#=============================================================================
# GET list of Board numbers   (not the part number) by looking at the 
# records with the same session number
sqlx = "Select COALESCE(vcDataLocation,'Mercury_Cache'), vcBoardNumber from tssessions where bisessionid = 24325"
# ('Mercury_Cache', 'RF9840_SN008')
#     Mercury_Cache
#     RF9840_SN008


#=============================================================================
# GET a Count of the number of records for this spec test id name
sqlx = "Select count(*) from Mercury_Cache..SysColumns where ID = (Select ID from Mercury_Cache..SysObjects where Name = 't_24325_test_GSMComposite_v2')"
# (86, )
#     86


#=============================================================================
# GET all matching column records for the named test
colnames = '''[DataID],[Temperature],[ModSwitch],[Frequency],[VSWR],[Phase],
[Logic1Level],[Logic2Level],[Logic3Level],[Logic4Level],[Logic5Level],
[SlotFactor],[DC_Shift],[RFAuxSwitch],[RFInSwitch],[RFOutSwitch],[PS1Level],
[PS2Level],[PS3Level],[PS4Level],[PS5Level],[Arb2Level],[Arb3Level],[Arb1Level],
[Arb1SetMax],[Arb2Switch],[Arb3Switch],[Arb2VI],[Arb3VI],[VmeasChannel],
[DesiredPin],[PinMax],[RecallConditions],[RecallStimulus],[DesiredPout],
[LogicLowLevel],[LogicHighLevel],[ArrayID],[ActualPout],[ActualPin],
[ACPLower200],[ACPLower250],[ACPLower400],[ACPLower600],[ACPLower1200],
[ACPLower1800],[ACPLower3000],[ACPLower6000],[ACPUpper200],[ACPUpper250],
[ACPUpper400],[ACPUpper600],[ACPUpper1200],[ACPUpper1800],[ACPUpper3000],
[ACPUpper6000],[Offset400n],[Offset600n],[Offset1200n],[Offset1800n],
[Offset400p],[Offset600p],[Offset1200p],[Offset1800p],[MaxRMSPhaseError],
[MaxPeakSPhaseError],[PS1ICC],[PS2ICC],[PS3Icc],[PS4Icc],[PS5Icc],[Vmeas],
[Arb1Leveled],[ModulationSetupTime],[PowerUpTime],[BufferBoxTime],
[ArbSetupTime],[ChangeFreqsTime],[SetSwitchesTime],[LevelingTime],
[MeasCurrentTime],[VmeasTime],[ModulationOnTime],[NIDigGSMCompositeTime],
[ModulationOffTime],[numOfDigAvgs]'''
colnames = re.sub('\[DataID\],','',colnames)
sql = 'RF9840_SN008|24325|Select %s from  %s Order by DataID' % ( colnames, TableString )
sql = "Select %s from  %s%s Order by DataID" % ( colnames, "Mercury_Cache.." , "t_24325_test_GSMComposite_v2")



sql = sqla

sql = '''SELECT
        vcBoardNumber, 
        ISNULL(b.vcPartFamily, vcProductFamily) AS vcPartFamily, 
        biSessionID, 
        vctestplanName, 
        dtSessionStartTime, 
        dtSessionEndTime, 
        siStatusID, 
        vcSessionDesc, 
        vcTesterName, 
        bPublished FROM tsSessions a LEFT JOIN JTS_Cache.dbo.tsJTS b ON b.biJobID=a.iJobID '''


sql = '''SELECT distinct
    ISNULL(b.vcPartFamily, vcProductFamily) AS vcMikey
    FROM tsSessions a LEFT JOIN JTS_Cache.dbo.tsJTS b ON b.biJobID=a.iJobID 
    order by vcMikey
      '''

sql = '''SELECT distinct
    vcTesterName
    FROM tsSessions a LEFT JOIN JTS_Cache.dbo.tsJTS b ON b.biJobID=a.iJobID 
    order by vcTesterName
      '''



print sql

sql = re.sub(r'[\r\n]','',sql)

selstr = ''
for row in cursor.execute( sql ):
    print row
#     for r in row:
#         print '   ', r
# 
#     selstr += '[%s],' % row[1]

print selstr


# timestr = row.dtSessionStartTime
# 
# print 'DATETIME =', timestr



cnxn.close()


####  L1694 "Select COALESCE(vcDataLocation,'Mercury') from tssessions where bisessionid in (24325)"
sql =  "Select COALESCE(vcDataLocation,'Mercury') from tssessions where bisessionid in (24325)"


TableString = "t_24325_test_GSMComposite_v2"



####  SQLStrings

####  L1694 "Select COALESCE(vcDataLocation,'Mercury') from tssessions where bisessionid in (24325)"

####  L1740 "Select distinct    right(name,len(name)-charindex('_',name,3)) from Mercury_Cache.dbo.sysObjects where name like 't_24325%'"

####  L4410  Set SQLCollection = RawSQLStatements(Sessions, TestRoutine,          ConditionString, AliasSet)
####                                           24325     test_GSMComposite_v2  ''               test_GSMComposite_v2
####  L2284  "select     b.name,     a.Name,     colid  from     mercury_cache.dbo.syscolumns a Join     mercury_cache.dbo.sysobjects b on b.id=a.id where     b.type='u'     and     b.name in('t_24325_test_GSMComposite_v2')  Union select     b.name,     a.Name,   

#"select     b.name,     a.Name,     colid  from     mercury_cache.dbo.syscolumns a Join     mercury_cache.dbo.sysobjects b on b.id=a.id where     b.type='u'     and     b.name in('t_24325_test_GSMComposite_v2')  Union select     b.name,     a.Name,   

#SQLString = "select b.name, a.Name,  colid from mercury_cache.dbo.syscolumns     a Join mercury_cache.dbo.sysobjects b on b.id=a.id where      b.type='u'  and  b.name in(" & TableString & ")  Union select  b.name, a.Name, 
#            "                        colid from mercury_archive_1.dbo.syscolumns a Join mercury_archive_1.dbo.sysobjects b on b.id=a.id where  b.type='u'  and  b.name in(" & TableString & ")  union select  b.name, a.Name,
#            "                        colid from mercury_archive_2.dbo.syscolumns a Join mercury_archive_2.dbo.sysobjects b on b.id=a.id where  b.type='u'  and  b.name in(" & TableString & ")  order by b.name, colid"




#### L2369  Watch :   : TableString : "t_24325_test_GSMComposite_v2" : String : modMain.RawSQLStatements
#### L2404  Watch :   : SelectString : "Select [DataID]," : String : modMain.RawSQLStatements
#### L2404  "Select [DataID],[Temperature],[ModSwitch],[Frequency],[VSWR],[Phase],[Logic1Level],[Logic2Level],[Logic3Level],[Logic4Level],[Logic5Level],[SlotFactor],[DC_Shift],[RFAuxSwitch],[RFInSwitch],[RFOutSwitch],[PS1Level],[PS2Level],[PS3Level],[PS4Level],[P

####  L2412 SelectString "Select [Temperature],[ModSwitch],[Frequency],[VSWR],[Phase],[Logic1Level],[Logic2Level],[Logic3Level],[Logic4Level],[Logic5Level],[SlotFactor],[DC_Shift],[RFAuxSwitch],[RFInSwitch],[RFOutSwitch],[PS1Level],[PS2Level],[PS3Level],[PS4Level],[PS5Level],


####  L2422   "Select COALESCE(vcDataLocation,'Mercury_Cache'), vcBoardNumber from tssessions where bisessionid = 24325"


####  L2434   "Select count(*) from Mercury_Cache..SysColumns where ID = (Select ID from Mercury_Cache..SysObjects where Name = 't_24325_test_GSMComposite_v2')"

####  L2436    DataResults.Open SQLString, Database
####           dbColumns = DataResults(0)   -->> 86



####  L2472  SQLStrings      : Item 1 : "RF9840_SN008|24325|Select [Temperature],[ModSwitch],[Frequency],[VSWR],[Phase],[Logic1Level],[Logic2Level],[Logic3Level],[Logic4Level],[Logic5Level],[SlotFactor],[DC_Shift],[RFAuxSwit
####    "Select [Temperature],[ModSwitch],[Frequency],[VSWR],[Phase],[Logic1Level],[Logic2Level],[Logic3Level],[Logic4Level],[Logic5Level],[SlotFactor],[DC_Shift],[RFAuxSwitch],[RFInSwitch],[RFOutSwitch],[PS1Level],[PS2Level],[PS3Level],[PS4Level],[PS5Level],[Ar"
####  -->> DataResults




####  L318    "Select [Temperature],[ModSwitch],[Frequency],[VSWR],[Phase],[Logic1Level],[Logic2Level],[Logic3Level],[Logic4Level],[Logic5Level],[SlotFactor],[DC_Shift],[RFAuxSwitch],[RFInSwitch],[RFOutSwitch],[PS1Level],[PS2Level],[PS3Level],[PS4Level],[PS5Level],[Ar"




