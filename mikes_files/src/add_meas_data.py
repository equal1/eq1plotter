#!/usr/bin/python

# Load the libraries 
import sys, time
sys.path.append( '/home/masker/bin/python' )
from pygram_dev import *

###################################################################
###################################################################
## New imports for all the excel reading and writing functions
from xlrd import open_workbook
from xlwt import *
from xlutils.copy import *

# Open the excel spreadsheet and copy it
rb = open_workbook('N:\sw\user\masker\pygram\ipfiles\AM7801 EVB Test Template.xls',formatting_info=True)
#rb = open_workbook('Y:\Projects\Chiarlo\Shared_Folder\DVT Test Results\AM7801\A4 BOM_E\SN001_008_009_010_samplesboards\Ant_Rx_VSWR\AM7801 EVB Test Template with limits.xls',formatting_info=True)
#rb = open_workbook('X:\\01-Projects\\05-Chiarlo\PCB\AM7802-01_EVB_EEB\Test Plan\AM7801 EVB Test Template.xls',formatting_info=True)
#rb = open_workbook('N:\sw\user\masker\pygram\ipfiles\AM7801 EVB Test Template with limits-09-1112.xls',formatting_info=True)

rs = rb.sheet_by_index(0)
wb = copy(rb)
ws = wb.get_sheet(0)

###################################################################
###################################################################

# start pygram
aa = pygram()

# Load the logfile
#aa.add_logfile( r'N:\sw\user\masker\pygram\ipfiles\001-RX1.s2p')
#aa.add_logfile( r'N:\sw\user\masker\pygram\ipfiles\001-RX2.s2p')
#aa.add_logfile( r'N:\sw\user\masker\pygram\ipfiles\001-RX3.s2p')
#aa.add_logfile( r'N:\sw\user\masker\pygram\ipfiles\001-RX4.s2p')

aa.add_all_logfiles_dialog()

re.sub(r'-.*', '', aa.logfilebasename)
grps = re.search(r'SN(\d+)(_.*)?\.s2p', aa.logfilebasename)
partnumber = grps.groups()[0]

#opxl = aa.logfiledir + '/rx_updated_sn' + re.sub(r'-.*', '', aa.logfilebasename) + '.xls'
opxl = 'rx_updated_sn' + partnumber + '.xls'

print ' Will write output excel file ', opxl
# first blank out all the other data in this spreadsheet
for i,cell in enumerate(rs.col(0)):
    ws.row(i).set_cell_blank(1)
    ws.row(i).set_cell_blank(3)




flist =    [869,881,894,925,942,960,1790,1827,1865,1930,1960,1990]

spl = [[  1.5 , "Max VSWR Limit", 4, "red" ],]
for f in flist:
    vline = [ [[f,1.0],[f,2.0]], "", 1, "brown"]
    spl.append( vline )


aa_xynames   = [ 'Freq(MHz)',  's22_vswr',  ]
aa.spec_limits = spl
aa.color_series.set( 'logfilename'  )
xyd = aa.plot_graph_data( aa_xynames )




spec_test_name = 'MHz Ant VSWR'    # the core spec test name


def update_spec_test():

  for i,cell in enumerate(rs.col(0)):
    
    # Look at the Spec Test Name in column 0, if it matches the pattern
    # will extract the frequency, the limit value,
    # and then we will insert the measured value, and the PASS/FAIL status 
    try:
#      print '           ', spec_test_name, cell.value
       freq = re.search(r'(\d+)\s*'+spec_test_name, cell.value, re.I).groups()[0]
    except Exception:    continue
    
    print ' cell=', freq, cell.value
    val = aa.measure_value( xyd, 'ymax_at_xval' , freq )[0]
    print ' at freq=%6sMHz Measured s22 VSWR = %s' % (freq, aa.measure_value( xyd, 'ymax_at_xval' , freq )[0])

    ws.write(i, 1, val)
    lim = float(rs.cell(i,2).value)
    if  val <= lim:
          ws.write(i, 3, 'PASS')
    else:
          ws.write(i, 3, 'FAIL',Style.easyxf('font: colour red;'))


update_spec_test()


fnl= aa.values_dict[ 'logfilename' ]



for rxf in fnl:
    print 'DOING ', rxf
    try:
        rx = re.search(r'(RX\d)_.*\.s2p', rxf, re.I).groups()[0]
    except Exception: continue
    
    rx  = rx.upper()

    spec_test_name = 'MHz %s VSWR' % rx   # the core spec test name

    print '  ... ', rxf, rx, spec_test_name



    aa.update_filter_conditions( 'logfilename' ,  rxf )
    aa_xynames   = [ 'Freq(MHz)',  's11_vswr',  ]
    aa.spec_limits = spl
    aa.color_series.set( 'logfilename'  )
    xyd = aa.plot_graph_data( aa_xynames )
    update_spec_test()






# now do the insertion loss 
aa.update_filter_conditions( 'logfilename' ,  None )




spl = [[  [[800,1.3],[1000,1.3]] , "Max LB Insertion Loss", 4, "red" ],
       [  [[1600,1.6],[2100,1.6]] , "Max HB Insertion Loss", 4, "red" ]]

for f in flist:
    vline = [ [[f,1.0],[f,2.0]], "", 1, "brown"]
    spl.append( vline )
    

for rxf in fnl:
    print 'DOING ', rxf
    try:
        rx = re.search(r'(Rx\d)_.*\.s2p', rxf, re.I).groups()[0]
    except Exception: continue
    
    rx  = rx.upper()

    spec_test_name = 'MHz Ant-%s Insertion Loss \(dB\)' % rx    # the core spec test name

    aa.update_filter_conditions( 'logfilename' ,  rxf )
    aa_xynames   = [ 'Freq(MHz)',  's12_Loss_dB',  ]   # insertion loss defined as s12 according to Xuesong 13nov09!
    aa.spec_limits = spl
    aa.color_series.set( 'logfilename'  )
    xyd = aa.plot_graph_data( aa_xynames )
    update_spec_test()
    
wb.save( opxl )



aa.loop()   # loop forever, and wait for input form the gui
