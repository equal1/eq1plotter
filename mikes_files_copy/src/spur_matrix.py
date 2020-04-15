#!/usr/bin/python

# Load the libraries 
import sys, time
#sys.path.append(r'/projects/sw/user/masker/pygram/src')
sys.path.append(r'/projects/sw/release')
sys.path.append(r'N:\sw\release')
from pygram_dev import *

###################################################################
###################################################################
## New imports for all the excel reading and writing functions
#    from xlrd import open_workbook
#    from xlwt import *
#    from xlutils.copy import *
#    
#    # Open the excel spreadsheet and copy it
#    rb = open_workbook('Y:\Projects\Chiarlo\Shared_Folder\DVT Test Results\AM7802\A4\Lot_100065\Template_Marketing\Copy of AM7802 EVB 11 parts Test Template.xls',formatting_info=True)
#    #rb = open_workbook('Y:\Projects\Chiarlo\Shared_Folder\DVT Test Results\AM7801\A4 BOM_E\SN001_008_009_010_samplesboards\Ant_Rx_VSWR\AM7801 EVB Test Template with limits.xls',formatting_info=True)
#    #rb = open_workbook('X:\\01-Projects\\05-Chiarlo\PCB\AM7802-01_EVB_EEB\Test Plan\AM7801 EVB Test Template.xls',formatting_info=True)
#    #rb = open_workbook('N:\sw\user\masker\pygram\ipfiles\AM7801 EVB Test Template with limits-09-1112.xls',formatting_info=True)
#    
#    rs = rb.sheet_by_index(0)
#    wb = copy(rb)
#    ws = wb.get_sheet(0)
#    
###################################################################
###################################################################

# start pygram
g = pygram()

g.get_savefile_directory_dialog()
#g.add_logfile( r'/projects/sw/user/masker/pygram/ipfiles/TXM_7801_Stability_HL_CA_SN006&1.log')


oplog_filename =  'spur_matrix.log'
oplog_fullpath = os.path.join(  g.savedir , oplog_filename )
oplog = open( oplog_fullpath , 'a' )

g.spurlog = oplog

print ' Saving spur matrix table to:', oplog_fullpath

# Load the logfile
g.add_all_logfiles_dialog()


print >> oplog, g.get_audit_str()







# Set the graph properties
xynames   = [ 'Frequency of Spur (MHz)', 'Amplitude of Spur, no harmonic {spur_filter_table}MHz (dBm)']
g.xlimits = [ 0 , 15000 ]
g.ylimits = [ -50 , +40 ]
g.spec_limits = [[ [[0,-36],[15000,-36]] , "", 4 , "red" ]]
g.xgrid   = 1000
g.ygrid   = 10
g.plot_marker = 'o'

g.line_on.set( False )


g.update_filter_conditions('TestName', ['Spurious (ETSI reduced)', 'Spurious (quick)'] )

vsl =  g.values_dict[ 'VSWR' ]
vsl.sort()
vswr_str = ''
for vswr in vsl:
   vswr_str = '%s       VSWR %0.1f:1         |' % (vswr_str, float(vswr) )



nm = 'Serial Number'
for part in g.values_dict[ nm ]:
      g.update_filter_conditions(nm, part)




      print >> oplog,  '''
------------
Part = %s
------------------------------------------------------------------------------------------------------------------------------------
Vbat    Pin   Freq   | %s
------------------------------------------------------------------------------------------------------------------------------------''' % ( part, vswr_str )





      vbatl = g.values_dict[ 'Vbat(Volt)' ]
      vbatl.sort()
      for vbat in vbatl:
#      for vbat in [3.5]:
          g.update_filter_conditions('Vbat(Volt)', vbat)

          pinl = g.values_dict[ 'Pwr In(dBm)' ]
          pinl.sort()
          for pin in pinl:
#          for pin in [0]:
              g.update_filter_conditions('Pwr In(dBm)', pin)
             
              freql = g.values_dict[ 'Freq(MHz)' ]
              freql.sort()
              for freq in freql:
#              for freq in [1610]:
                  g.update_filter_conditions('Freq(MHz)', freq)

                  print >> oplog, '%3.1f    %2.0f     %4.0f   | ' % ( float( vbat), float( pin ), float( freq ) ),
#                  print '%3.1f    %2.0f     %4.0f   | ' % ( float( vbat), float( pin ), float( freq ) ),

                  vswrl = g.values_dict[ 'VSWR' ]
                  vswrl.sort()
                  for vswr in vswrl:
#                 for vswr in [8]:
                        g.update_filter_conditions('VSWR', vswr)

                        xyd = g.plot_graph_data( xynames, None, 'no save', 'Spur (30MHz filt) Vbat=%0.1f Pin=%0.0f Freq=%0.0f VSWR=%0.0f:1 %s' % ( vbat, pin, freq, vswr, part ) )

                        g.part_list = {}
                        g.failed_part_list = {}

#                   xydata, measurement_type , at_value,  limit 
                        rt  = g.measure_value( xyd,      'ymax',          '',       -36 )

### rt =  [ value , [ val_min, val_avg, val_max ], [xv, yv, rn, sn, c, d,], [ fail_count , 1 ] ]
### rt =  [ value , [ val_min, val_avg, val_max ], [xv, yv, rn, sn, c, d,], [ -1 , -1 ] ]
### rt =  None


                        print "measure_value = ",  rt
                        print "failed_part_list length=", len(g.failed_part_list)

                        if  len(g.failed_part_list) > 0 :  fstr = "FAIL"
                        else                            :  fstr = ""

                        if rt != None and len(rt) == 4 : 
                               if len(rt) == 4 and rt[3][0] == 0 : pf = '       no spurs          |'
                               else:              pf = '%4s (%5.1fdBm @ %4.0fMHz)|' % ( fstr, rt[0], rt[2][0])
                        elif xyd != None:
                               pf = '         pass            |'
                        else:
                               pf =                    '         na              |'
                        print >> oplog, '%s' % pf,

                  print >> oplog, ''
              print >> oplog, '------------------------------------------------------------------------------------------------------------------------------------'







oplog.close()










g.loop()

