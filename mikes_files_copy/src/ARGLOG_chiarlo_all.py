

######################################################################################
######################################################################################
# Read the PRD excel spreadsheet and put the data into prd_list



g = self




rb = open_workbook(  g.prdfile,  formatting_info=True)

g.xl_type = 'perf_log'  # tells get_prd_data to look for different column names in the excel file

# Go through the PRD excel spreadsheet and get all the test names, 
# conditions, and limits, and put this info into a standard list prd_list
prd_list = g.get_prd_data( rb )



# look through the prd_list to see which rated power values will need to be filtered
#g.rated_power_values = g.get_prd_rated_power_conditions( prd_list )


g.rated_power_values = {}
g.rated_power_values['@ Prated'] = [34.2, 32.0]



# Make a copy of the excel PRD spreadsheet, this is the one we will update with
# measurement data
wb = copy(rb)

#g.savedir = g.get_directory_dialog( 'Select ARG Report Save Directory', 'savedir' )
#g.savedir = 'N:/sw/user/masker/pygram/opfiles'

name = re.sub('[\\/]$', '', g.savedir)   # remove any trailing slash
g.resultsdir_basename = os.path.basename( name )


# start a second pygram session log file in the results directory
pygram_logfile =  os.path.join( g.savedir  , g.script_basename + '_pygram.log')
sys.stdout.start_log2( pygram_logfile )



opxl = g.resultsdir_basename + '.xls'

opxl = os.path.join(  g.savedir , opxl )
print ".saving to output excel file '%s'" % opxl
g.oplogfilenames.append( opxl )
g.xl_tmpfile = g.init_xl_tmpfile( opxl, wb )






##############################################################################
# define the styles used to write data out into the output excel results file
# one for good passing data, and another for failing data etc

# standard style for everything we write to the PRD
stxt = 'font: colour %s, name Times New Roman, height 160; alignment: vertical center, horizontal center, wrap True; pattern: pattern solid, fore_colour %s; '
thk = 'thin'   # the border thickness
stxt = '%s borders: left %s, right %s, top %s, bottom %s;' % ( stxt,thk,thk,thk,thk )
#                                               text   fill
g.excel_style = {}
g.excel_style[ 'fail' ]    = easyxf( stxt % ( 'red','white') )
g.excel_style[ 'pass' ]    = easyxf( stxt % ( 'green','white') )
g.excel_style[ 'nomeas' ]  = easyxf( stxt % ( 'black','white') )
g.excel_style[ 'typical' ] = easyxf( stxt % ( 'black','white') )
g.excel_style[ 'blank' ]   = easyxf( stxt % ( 'black','white'      ) )
g.excel_style[ 'typical_fail' ]   = easyxf( stxt % ( 'black','white'      ) )






######################################################################################
######################################################################################
# Load the ATR logfiles

#g.add_logfile( 'N:/sw/user/masker/pygram/ipfiles/AM7804_TA1_T_U_A0C_Dband_SN031p.log')
#g.add_logfile( 'N:/sw/user/masker/pygram/ipfiles/TXM_7801_Stability_HL_CB_SN006.log')
#g.product = 'AM7801'

#g.add_all_logfiles_dialog()


for f in g.atr_logfiles:
     g.add_logfile( f )


if g.copy_atrlogfiles:
   g.copy_all_logfiles( os.path.join( g.savedir, 'atr_logfiles' ))


# Set the output logfile for the measurements

oplog_filename = g.resultsdir_basename + '.log'
oplog_fullpath = os.path.join(  g.savedir , oplog_filename )
oplog = open( oplog_fullpath , 'a' )
g.oplogfilenames.append( oplog_fullpath )


g.get_audit_str()
print >> oplog, g.get_audit_str()


g.print_values_list()


# Write out the part number info at the top of the sheet
#              Name            sheetnum, row  col  style
data_dict = { 'Chip Model'       : [ 1,   0,   4, 'blank' ] ,
              'Serial Number'    : [ 1,   1,   4, 'blank' ] ,
              'Test Date & Time' : [ 1,   2,   4, 'blank' ]
            }
g.write_xl_part_info(wb, data_dict)

#    
###################################################################
###################################################################
# TEST DESCRIPTION LIST
# Define test info for each test parameter name in the PRD.  This will tell 
# us which axes, which Testname, which measurement to use for each PRD test.

        # PRD test name       , logfile types  ,  Testname                        ,  xynames                     ,  conditions, measures

g.legend_location = [1.0, 0]
tdesc_desc_list = [
 
  {   # 1
   'parameter'  :  '$Freq MHz Max Pout (dBm)'              ,
   'logfiletype':  ['room']                                ,
   'testname'   :  'Output Power & Efficiency'             ,
   'xynames'    :  ['Vramp voltage','Pout(dBm)']           ,
   'xylimits'   :  [ [0, 2.0], [ -20, +40 ] ]              ,
   'filters'    :  [['Freq(MHz)', 'F' '$Freq']]            ,
   'measures'   :  [['Limit', 'min']]                      ,
  },

  {  # 2
   'parameter'	: '$Freq MHz PAE at Rated Power (%)'				,
   'logfiletype': ['room']				,
   'testname'	: 'Output Power & Efficiency'	,
   'xynames'	: ['Pout(dBm)', 'PAE(%)']		,
   'xylimits'	: [[-20, +40], [-2, 60]]		,
   'filters'	: [['Freq(MHz)', 'F', '$Freq'], ['@ Prated', 'F', True]]	,
   'measures'	: [['Limit', 'min']]	,
  },
  

  {
   'parameter'	: 'Forward Isolation 1'                        ,
   'logfiletype': ['room']                                     ,
   'testname'	: 'Fwd Isol1 (TxOff)'                          ,
   'xynames'	: ['Freq(MHz)', 'Fwd Isol1 (TxOff) Amplitude(dBm)'] ,
   'xylimits'	: [[820, 855], [-70, -10], [875, 920], [-70, -10], [1705, 1790], [-70, -10], [1845, 1915], [-70, -10]],
   'filters'	: [['SN', 'C']]                                ,
   'measures'	: [['typical', 'avg_ymax'], ['max', 'ymax']]   ,
  },  
  
  {
   'parameter'	: 'Forward Isolation 2'				,
   'logfiletype': ['room']					,
   'testname'	: 'Fwd Isol2 (TxOn)'	         		,
   'xynames'	: ['Freq(MHz)', 'Fwd Isol2 (TxOn) Amplitude(dBm)']				,
   'xylimits'	: [[820, 855], [-70, -10], [875, 920], [-70, -10], [1705, 1790], [-70, -10], [1845, 1915], [-70, -10]],
   'filters'	: [['SN', 'C']]	,
   'measures'	: [['typical', 'avg_ymax'], ['max', 'ymax']]  	,
  },



  {
   'parameter'  : '2nd Harmonic Distortion'                             ,
   'logfiletype':  ['room','temp']                                      ,
   'testname'   :  'Harmonics (2nd VSA)'                             ,
   'xynames'    :  ['Freq(MHz)','2nd Harmonics Amplitude(dBm)' ]        ,
   'xylimits'   :  [[820, 855], [ -60, 0 ], [875, 920], [-60, 0], [1705, 1790], [-60, 0], [1845, 1915], [-60, 0]] ,
   'filters'    :  [['SN','C'],['TestName', 'L']]                       ,
   'measures'   :  [ [ 'typical', 'avg_ymax'],[ 'max', 'max_ymax']]     ,
  },
  {
   'parameter'  : '3rd Harmonic Distortion'                             ,
   'logfiletype':  ['room','temp']                                      ,
   'testname'   :  'Harmonics (3rd VSA)'                              ,
   'xynames'    :  ['Freq(MHz)','3rd Harmonics Amplitude(dBm)' ]        ,
   'xylimits'   :  [[820, 855], [ -60, 0 ], [875, 920], [-60, 0], [1705, 1790], [-60, 0], [1845, 1915], [-60, 0]] ,
   'filters'    :  [['SN','C'],['TestName', 'L']]                       ,
   'measures'   :  [ [ 'typical', 'avg_ymax'],[ 'max', 'max_ymax']]     ,
  },

  {
   'parameter'  : '4th thru 7th Harmonic Distortion'      ,
   'logfiletype':  ['room','temp']                         ,
   'testname'   :  ['Harmonics (4th VSA)',
                    'Harmonics (5th VSA)',
                    'Harmonics (6th VSA)',
                    'Harmonics (7th VSA)',],
   'xynames'    : ['Freq(MHz)','4th Harmonics Amplitude(dBm)',
                               '5th Harmonics Amplitude(dBm)',
                               '6th Harmonics Amplitude(dBm)',
                               '7th Harmonics Amplitude(dBm)']       ,
   'xylimits'   :  [[820, 855], [ -60, -20 ], [875, 920], [-60, -20], [1705, 1790], [-60, -20], [1845, 1915], [-60, -20]] ,
   'filters'    : [['SN','L'],['TestName', 'C']]                       ,
   'measures'   :  [ [ 'typical', 'avg_ymax'],[ 'max', 'max_ymax']]    ,
  },
  {
   'parameter'  : '4th thru 13th Harmonic Distortion'      ,
   'logfiletype':  ['room','temp']                         ,
   'testname'   :  ['Harmonics (4th VSA)',
                    'Harmonics (5th VSA)',
                    'Harmonics (6th VSA)',
                    'Harmonics (7th VSA)',
                    'Harmonics (8th VSA)',
                    'Harmonics (9th VSA)',
                    'Harmonics (10th VSA)'],
   'xynames'    : ['Freq(MHz)','4th Harmonics Amplitude(dBm)',
                               '5th Harmonics Amplitude(dBm)',
                               '6th Harmonics Amplitude(dBm)',
                               '7th Harmonics Amplitude(dBm)',
                               '8th Harmonics Amplitude(dBm)',
                               '9th Harmonics Amplitude(dBm)',
                               '10th Harmonics Amplitude(dBm)' ]       ,
   'xylimits'   :  [[820, 855], [ -60, -20 ], [875, 920], [-60, -20], [1705, 1790], [-60, -20], [1845, 1915], [-60, -20]] ,
   'filters'    : [['SN','L'],['TestName', 'C']]                       ,
   'measures'   :  [ [ 'typical', 'avg_ymax'],[ 'max', 'max_ymax']]    ,
  },



  {
   'parameter'	: 'Transient Spectrum 3GPP Transient PSD spec +/- 400kHz' ,
   'logfiletype': ['room']					                          ,
   'testname'	: 'GSM ORFS Switching'	                              ,
   'xynames'	: ['Freq(MHz)', 'Sw Pwr 400KHz(dBm)']                 ,
   'xylimits'	: [[820, 855], [-40, -10], [875, 920], [-40, -10], [1705, 1790], [-40, -10], [1845, 1915], [-40, -10]],
   'filters'	: [['SN', 'C']]	                                      ,
   'measures'	: [['typical', 'avg_ymax']]			                  ,
  },  
  


  {
   'parameter'  : 'Insertion Loss LB'                             ,
   'logfiletype':  ['s2p',]                                      ,
   'testname'   :  None                                           ,
   'xynames'    :  [ 'Freq(MHz)',  's12_Loss_dB',  ]              ,
   'xylimits'   :  [ [820,990], [0,3]]                            ,
   'filters'    :  [['logfilename','C'], ['Freq(MHz)','F', '820..990']]   ,
   'measures'   :  [ [ 'typical', 'avg_at_xval'],[ 'max', 'ymax_at_xval']]      ,
  },
 
  {
   'parameter'  : 'Insertion Loss HB'                             ,
   'logfiletype':  ['s2p',]                                      ,
   'testname'   :  None                                           ,
   'xynames'    :  [ 'Freq(MHz)',  's12_Loss_dB',  ]              ,
   'xylimits'   :  [ [1800,2000], [0,3]]                            ,
   'filters'    :  [['logfilename','C'], ['Freq(MHz)','F', '1800..2000']]   ,
   'measures'   :  [ [ 'typical', 'avg_at_xval'],[ 'max', 'ymax_at_xval']]      ,
  },
 
  {
   'parameter'  : 'VSWR at Rx and ANT Ports LB'                   ,
   'logfiletype':  ['s2p',]                                      ,
   'testname'   :  None                                           ,
   'xynames'    :  [ 'Freq(MHz)',  's11_vswr', 's22_vswr', ]      ,
   'xylimits'   :  [ [820,990], [0,3]]                            ,
   'filters'    :  [['logfilename','C'], ['Freq(MHz)','F', '820..990']]   ,
   'measures'   :  [ [ 'typical', 'avg_at_xval'],[ 'max', 'ymax_at_xval']]      ,
  },
 
  {
   'parameter'  : 'VSWR at Rx and ANT Ports HB'                   ,
   'logfiletype':  ['s2p',]                                      ,
   'testname'   :  None                                           ,
   'xynames'    :  [ 'Freq(MHz)',  's11_vswr', 's22_vswr', ]      ,
   'xylimits'   :  [ [1800,2000], [0,3]]                            ,
   'filters'    :  [['logfilename','C'], ['Freq(MHz)','F', '1800..2000']]   ,
   'measures'   :  [ [ 'typical', 'avg_at_xval'],[ 'max', 'ymax_at_xval']]      ,
  },  
  
]
 


tdesc_desc_list = [

  {   # 1
   'parameter'  :  'MHz Max Pout (dBm)'                    ,
   'logfiletype':  ['room']                                ,
   'testname'   :  'Output Power & Efficiency'             ,
   'xynames'    :  ['Vramp Voltage','Pout(dBm)']           ,
   'xylimits'   :  [ [0, 2.0], [ -20, +40 ] ]              ,
   'filters'    :  []                                      ,
   'measures'   :  [['Limit', 'min_ymax']]                      ,
  },


  {  # 2
   'parameter'	: 'MHz PAE at Rated Power (%)'              ,
   'logfiletype': ['room']				                    ,
   'testname'	: 'Output Power & Efficiency'	            ,
   'xynames'	: ['Pout(dBm)', 'PAE(%)']		            ,
   'xylimits'	: [[-20, +40], [-2, 60]]		            ,
   'filters'	: [['@ Prated', 'F', True]]	                ,
   'measures'	: [['Limit', 'ymax']]	                    ,
  },

  {  # 3
   'parameter'	: 'MHz Icc at Rated Power (mA)'             ,
   'logfiletype': ['room']				                    ,
   'testname'	: 'Output Power & Efficiency'	            ,
   'xynames'	: ['Pout(dBm)', 'Vbat_I(mA)']		        ,
   'xylimits'	: [[-20, +40], [-2, 2000]]		            ,
   'filters'	: [['@ Prated', 'F', True]]	                ,
   'measures'	: [['Limit', 'ymax']]	                    ,
  },

  {	 # 4
   'parameter'	: 'MHz Forward Isolation 1 (dBm)'			,
   'logfiletype': ['room']									,
   'testname'	: 'Fwd Isol1 (TxOff)'						,
   'xynames'	: ['Freq(MHz)', 'Fwd Isol1 (TxOff) Amplitude(dBm)'],
   'xylimits'	: [[820, 855], [-70, -10]]					,
   'filters'	: [['VRamp Voltage', 'F', '0.15']]			,
   'measures'	: [['Limit', 'ymax']]						,
  },
  {	 # 5
   'parameter'	: 'MHz 2nd harmonic (dBm)'	                ,
   'logfiletype': ['room']									,
   'testname'	: 'Harmonics (2nd VSA)'						,
   'xynames'	: ['Freq(MHz)', '2nd Harmonics Amplitude(dBm)'],
   'xylimits'	: []		     			                ,
#   'filters'	: [['@ Prated', 'F', True]]	                ,
   'filters'	: [['Vramp Voltage', 'C' ]]	                ,
   'measures'	: [['Limit', 'ymax_at_xval']]               ,
  },


]

######################################################################################
######################################################################################


#sweep_params_list = ['Vbat(Volt)', 'Pwr In(dBm)', 'Temp(C)', 'Freq(MHz)', 'VSWR', 'Phase(degree)' ]
sweep_params_list  = ['Vbat(Volt)', 'Pwr In(dBm)', 'Temp(C)',              'VSWR', 'Phase(degree)' ]

# The nom_val dictionary is used to define the nominal values for each parameter.
# This value may be a two element list, where the first is the nominal value for LB and the second for HB.
nom_vals = {}
nom_vals['Vbat(Volt)']  = 3.5
nom_vals['Pwr In(dBm)'] = 3
nom_vals['Temp(C)']     = 25
nom_vals['Freq(MHz)']   = [837, 898, 1748, 1880]
nom_vals['Process']     = 'TT'
nom_vals['VSWR']        = 1
nom_vals['Phase(degree)']     = 0




g.sort_data_on.set(False)






######################################################################################
######################################################################################
#  Go through the prd_list tests one by one plotting and measuring the data.
#  When each measurement is done add it back to the PRD (a copy of).


for prdl in prd_list:

    g.parameter_plot_count = 0
    g.selected_filter_conditions_str = ''

    for tdl in tdesc_desc_list:

        tdesc = g.get_test_desc(tdl, prdl, g.arg_testnum, g.arg_runmode )

        if tdesc:

            # Using the test description and the prd info create a graph table row (fct)
            # which has everything needed to plot and measure the data
            fct = g.gen_graph_table_row( tdesc, prdl)
            
            g.reset_filter_conditions(fct)
            # Setup some filters and define the x,y axes
            band = prdl[ 'sub-band' ]
            g.update_filter_conditions('TestName', tdesc['testname'])
            g.update_filter_conditions('Sub-band', band)
            xynames = tdesc['xynames']
            g.set_xyaxes_limits( tdesc )


            limval  = {}

            # Setup the plotting filters based on the PRD Conditions,
            # setup the plot limits, and do the plot
            savefile, title = g.set_filter_conditions(fct, sweep_params_list, nom_vals, tdesc)
            g.set_spec_limits(fct, limval)
            xyd = g.plot_graph_data(xynames, None, savefile, title)

            print '(ARGLOG) xyd = ', xyd

            # Measure the data on the plots, and update the excel PRD with the results
            g.measure_plot_data(xyd, fct, limval, oplog, prdl, wb, savefile)





wb.save( opxl )

g.xl_tmpfile.close()
oplog.close()

g.loop()







