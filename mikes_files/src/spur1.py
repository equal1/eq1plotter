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

# Load the logfile
#g.add_all_logfiles_dialog()
g.add_logfile( r'N:\sw\user\masker\pygram\ipfiles\TXM_7801_Stability_HL_TA5_T_U_CF_SN009B_C11_13pF_Wire_mini_2.log')




# Set the graph properties
#xynames   = [ 'Frequency of Spur (MHz)', 'Amplitude of Spur, no harmonic 30MHz (dBm)']
xynames   = [ 'Frequency of Spur (MHz)', 'Amplitude of Spur (dBm)']
#g.xlimits = [ 0 , 15000 ]
#g.ylimits = [ -50 , +40 ]
#g.spec_limits = [[ [[0,-36],[15000,-36]] , "", 4 , "red" ]]
#g.xgrid   = 1000
#g.ygrid   = 10
g.plot_marker = 'o'

g.line_on.set(False)


g.update_filter_conditions('TestName', 'Spurious (ETSI reduced)' )


xyd = g.plot_graph_data( xynames, )



g.loop()

