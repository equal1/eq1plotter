

######################################################################################
######################################################################################
# Read the PRD excel spreadsheet and put the data into prd_list



g = self


print '(ARGPRD_chiarlo_all.py) g.arg_runmode = ', g.arg_runmode


rb = open_workbook(  g.prdfile,  formatting_info=True)



# Go through the PRD excel spreadsheet and get all the test names, 
# conditions, and limits, and put this info into a standard list prd_list
prd_list = g.get_prd_data( rb )
# look through the prd_list to see which rated power values will need to be filtered
g.rated_power_values = g.get_prd_rated_power_conditions( prd_list )


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



#    
###################################################################
###################################################################
# TEST DESCRIPTION LIST
# Define test info for each test parameter name in the PRD.  This will tell 
# us which axes, which Testname, which measurement to use for each PRD test.

        # PRD test name       , logfile types  ,  Testname                        ,  xynames                     ,  conditions, measures

g.legend_location = [1.0, 0]
tdesc_desc_list = [
 
  {
   'parameter'  :  'Max. Output Power'                     ,
   'logfiletype':  ['room','temp']                         ,
   'testname'   :  'Output Power & Efficiency'             ,
   'xynames'    :  ['Vramp Voltage','Pout(dBm)']           ,
   'xylimits'   :  [ [0, 2.0], [ -20, +40 ] ]                 ,
   'filters'    :  [['Freq(MHz)', 'C'],['SN','L']]         ,
   'measures'   :  [['min', 'min_ymax_at_xrange'], ['typical','avg_ymax_at_xrange']] ,
  },

 
  {
   'parameter'  : 'Power @ VSWR'                           ,
   'logfiletype':  ['room','temp','loadpull']              ,
   'testname'   : 'Output Power & Efficiency'              ,
   'xynames'    : ['Phase(degree)','Pout(dBm)']            ,
   'xylimits'   :  [ [-180, 180], [ 25, 38 ]]                 ,
   'filters'    : [['Freq(MHz)','L'],['SN','C']] ,
   'measures'   :  [[ 'min', 'min_ymin'], [ 'max', 'max_ymax']] ,
  },
  {# This EDGE Power @ VSWR is for AM8901 only
   'parameter'  : 'EDGE Power @ VSWR'                           ,
   'logfiletype':  ['room','temp','loadpull']              ,
   'testname'   : 'Output Power & Efficiency'              ,
   'xynames'    : ['Phase(degree)','Pout(dBm)']            ,
   'xylimits'   :  [ [-180, 180], [ 24, 38 ] ]                 ,
   'filters'    : [['Freq(MHz)','L'],['SN','C']] ,
   'measures'   :  [[ 'min', 'min_ymin'], [ 'max', 'max_ymax']] ,
  },
  {
   'parameter'  : 'Maximum current  @ VSWR'                ,
   'logfiletype':  ['room','temp','loadpull']              ,
   'testname'   : 'Output Power & Efficiency'              ,
   'xynames'    : ['Phase(degree)','Vbat_I(Amp)']          ,
   'xylimits'   :  [ [-180, 180], [ 0, 2 ] ]               ,
   'filters'    : [['Freq(MHz)','L'],['SN','C']]           ,
   'measures'   :  [ [ 'max', 'max_ymax']]                 ,
  },

  {
   'parameter'	: 'PAE Max'				,
   'logfiletype': ['room']				,
   'testname'	: 'Output Power & Efficiency'	,
   'xynames'	: ['Pout(dBm)', 'PAE(%)']		,
   'xylimits'	: [[-20, +40], [-2, 60]]		,
   'filters'	: [['Freq(MHz)', 'C'], ['SN', 'L']]	,
   'measures'	: [['typical', 'avg_ymax']]		,
  },
  
  {
   'parameter'	: 'PAE @'				,
   'logfiletype': ['room']				,
   'testname'	: 'Output Power & Efficiency'	,
   'xynames'	: ['Pout(dBm)', 'PAE(%)']		,
   'xylimits'	: [[-20, +40], [-2, 60]]		,
   'filters'	: [['Freq(MHz)', 'C'], ['SN', 'L']]	,
   'measures'	: [['typical', 'avg_at_xval']]	,
  },
  
  {# This maximum control slope is for AM7801/7802 only
   'parameter'  : 'Maximum Control slope'                ,
   'logfiletype':  ['room','temp']                       ,
   'testname'   : 'Output Power & Efficiency'            ,
   'xynames'    : ['Pout(dBm)', 'Power Control Slope (dB/V)']  ,
   'xylimits'   :  [ [0, 40], [ -20, 500 ] ]             ,
   'filters'    : [['Freq(MHz)','L'],['SN','C']]         ,
   'measures'   :  [ [ 'min', 'ymin_at_xrange'],[ 'max', 'ymax_at_xrange']] ,
  },
  {# This maximum control slope is for AM8901 only
   'parameter'  : 'Max Control slope'                ,
   'logfiletype':  ['room','temp']                       ,
   'testname'   : 'Output Power & Efficiency'            ,
   'xynames'    : ['Ref Pout(dBm)', 'Power Control Slope (dB/V)']  ,
   'xylimits'   :  [ [0, 40], [ -20, 500 ] ]             ,
   'filters'    : [['Freq(MHz)','L'],['SN','C']]         ,
   'measures'   :  [ [ 'min', 'ymin_at_xrange'],[ 'max', 'ymax_at_xrange']] ,
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
   'parameter'  : 'Cross band Isolation'                                ,
   'logfiletype':  ['room','temp']                                      ,
   'testname'   :  'Crossband Isolation'                              ,
   'xynames'    :  ['Freq(MHz)','Crossband Isolation Amplitude(dBm)' ]  ,
   'xylimits'   :  [[], [ -70, 0 ]]                                     ,
   'filters'    :  [['SN','C']]                       ,
   'measures'   :  [[ 'max', 'max_ymax']]                               ,
  },
  {
   'parameter'  : 'AM-AM Conversion'                                    ,
   'logfiletype':  ['room','temp']                                      ,
   'testname'   :  'AM-AM AM-PM Distortion'                       ,
   'xynames'    :  ['Pout(dBm)','AMAM conversion Voutpk/VAM (dV/dV)' ]  ,
   'xylimits'   :  [[-20, 35], [ 0, 25 ]] ,
   'filters'    :  [['SN','C']]                       ,
   'measures'   :  [['min', 'min_ymin_at_xrange'],['max', 'max_ymax_at_xrange'],['typical', 'yavg_at_xrange']]    ,
  },
  {
   'parameter'  : 'AM-PM Conversion'                                    ,
   'logfiletype':  ['room','temp']                                      ,
   'testname'   :  'AM-AM AM-PM Distortion'                        ,
   'xynames'    :  ['Pout(dBm)','AM-PM Slope (deg/dB)' ]                ,
   'xylimits'   :  [[-20, 35], [ -10, 25 ]]                             ,
   'filters'    :  [['SN','C']]                       ,
   'measures'   :  [['min', 'min_ymax_at_xrange'],['max', 'max_ymax_at_xrange']]    ,
  }, 
  {
   'parameter'  : 'All Other Non-Harmonic Spurious 100 kHz to 1GHz'    ,
   'logfiletype':  ['room','temp']                                     ,
   'testname'   : 'Spurious (ETSI reduced)'                            ,
   'xynames'    : ['Frequency of Spur (MHz)', 'Amplitude of Spur, no harmonic 15MHz (dBm)'] ,
   'xylimits'   :  [ [0, 1000], [ -50, 40] ]                           ,
   'lineon'     : False                                                ,
   'filters'    : [['Frequency of Spur (MHz)','F', '0.1..1000'],['SN','C']]          ,
   'measures'   :  [[ 'max', 'ymax_at_xrange']]                                  ,
  },
  
  {
   'parameter'  : 'All Other Non-Harmonic Spurious 1GHz to 12.75GHz'   ,
   'logfiletype':  ['room','temp']                                     ,
   'testname'   : 'Spurious (ETSI reduced)'                            ,
   'xynames'    : ['Frequency of Spur (MHz)', 'Amplitude of Spur, no harmonic 15MHz (dBm)'] ,
   'xylimits'   :  [ [1000, 13000], [ -50, 40] ]                       ,
   'lineon'     : False                                                ,
   'filters'    : [['Frequency of Spur (MHz)','F', '1000..13000'],['SN','C']]        ,
   'measures'   :  [[ 'max', 'ymax_at_xrange'], [ 'typical', 'yavg_at_xrange']]        ,
  },
  
   # definition for stability with max limit value
  {
   'parameter'  : 'Output Load VSWR Stability'                         ,
   'logfiletype':  ['room','temp']                                     ,
   'testname'   : 'Spurious (ETSI reduced)'                            ,
   'xynames'    : ['Frequency of Spur (MHz)', 'Amplitude of Spur, no harmonic 15MHz (dBm)']            ,
   'xylimits'   :  [ [0, 12000], [ -50, 40] ]                          ,
   'lineon'     : False                                                ,
   'filters'    : [['SN','C'],['Freq(MHz)','L'], ['Phase(degree)','A'],['VSWR','F', '1.5..10'] ]                     ,
   'measures'   :  [[ 'min', 'max_ymax','',-36]]                              ,
  },

   # second definition for stability with typical limit value ( note different VSRW condition)
  {
   'parameter'  : 'Output Load VSWR Stability'                         ,
   'logfiletype':  ['room','temp']                                     ,
   'testname'   : 'Spurious (ETSI reduced)'                            ,
   'xynames'    : ['Frequency of Spur (MHz)', 'Amplitude of Spur, no harmonic 15MHz (dBm)']            ,
   'xylimits'   :  [ [0, 12000], [ -50, 40] ]                          ,
   'lineon'     : False                                                ,
   'filters'    : [['SN','C'],['Freq(MHz)','L'], ['Phase(degree)','A'],['VSWR','F', '1.5..12'] ]                     ,
   'measures'   :  [[ 'typical', 'max_ymax','',-36]]                              ,
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
   'parameter'	: 'Transient Spectrum Extreme Conditions'	      ,
   'logfiletype': ['temp']					                      ,
   'testname'	: 'GSM ORFS Switching'		                      ,
   'xynames'	: ['Freq(MHz)', 'Sw Pwr 400KHz(dBm)']	          ,
   'xylimits'	: [[820, 855], [-40, -10], [875, 920], [-40, -10], [1705, 1790], [-40, -10], [1845, 1915], [-40, -10]],
   'filters'	: [['SN', 'C']]	                                  ,
   'measures'	: [['max', 'ymax']]                               ,
  },

  {
   'parameter'  : 'Transmit Power Control Accuracy'                  ,
   'logfiletype':  ['room','temp']                                   ,     
   'testname'   : 'Output Power & Efficiency'                        ,
   'xynames'    : ['Ref Pout(dBm)', 'Pwr Variation(dB)']             ,
   'xylimits'   :  [ [-5, 35], [ -10, 10 ]]                          ,
   'filters'    : [['Temp(C)','C'],['SN','L'],]                      ,
   'measures'   :  [ [ 'min', 'ymin_at_xrange'],[ 'max', 'ymax_at_xrange']] ,

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
nom_vals['VSWR']     = 1
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

            # Measure the data on the plots, and update the excel PRD with the results
            g.measure_plot_data(xyd, fct, limval, oplog, prdl, wb, savefile)





wb.save( opxl )

g.xl_tmpfile.close()
oplog.close()

g.loop()







