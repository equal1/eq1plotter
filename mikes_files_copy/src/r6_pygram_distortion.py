#!/usr/bin/python


import sys, time
#sys.path.append(r'/projects/sw/user/masker/pygram/src')
sys.path.append(r'/projects/sw/release')
sys.path.append(r'N:\sw\release')
from pygram_dev import *


###################################################################
###################################################################
###################################################################
###################################################################


# initialize pygram
mag = pygram()

# This following line defines 4 line dash patterns.
# The first graph will use the [1,0] pattern
# the second will use [3,2] etc
# The first of the two numbers are the length of the solid line and
# the second number is the length of the gap. Therefore [3,2] means
# draw a line with three units of line followed by a gap of 2 units, and
# repeat this pattern.
# This definition needs to follow the mag = pygram() line and be before the any 
# mag.plot_graph_data() lines.
#mag.dash_list = [ [1,0], [3,2], [15,4], [5,8] ]
mag.dash_list = [ [1,0], [1,0], [15,4], [5,8] ]

# read the logfiles
#mag.add_all_logfiles_dialog()
#mag.get_savefile_directory_dialog()
mag.savedir     =  r'N:\sw\user\masker\pygram\opfiles\tmp10'
#mag.add_logfile('Y:/Projects/Chiarlo/Shared_Folder/DVT Test Results/AM8901/B0x/Tuning/AM8901_TB0C_T_U_CB_GSM_25deg_SN004_ATR2.log')
mag.add_logfile('N:\sw\user\masker\pygram\ipfiles\AM8901_TB0C_T_M_CB_GSM_LB_25degC_SN008.log')
mag.add_logfile('N:\sw\user\masker\pygram\ipfiles\AM8901_TB0C_T_M_CB_GSM_LB_n40degC_SN008.log', temperature=-40)
mag.add_logfile('N:\sw\user\masker\pygram\ipfiles\AM8901_TB0C_T_M_CB_GSM_LB_85degC_SN008.log')





# do the vam distortion calculations, note the last conditions will be the conditions chosen as the nominal reference 

# set the offset voltage
mag.vam_offset = 0.230

mag.add_vam_pout_columns(ref_temp=25,ref_freq=837,ref_hblb='LB',ref_seg='00', ref_vbat=3.5)
mag.add_vam_pout_columns(ref_temp=25,ref_freq=1748,ref_hblb='HB',ref_seg='00', ref_vbat=3.5)
mag.print_column_list()  
mag.print_values_list()    

#mag.loop()


###################################################################
def run_plots( band, segs, sweep_param, vals=None ) :


    mag.update_filter_conditions( 'Vbat(Volt)',  [ 3.5, 3.6 ] )
    mag.update_filter_conditions( 'Temp(C)',       25 )
    mag.update_filter_conditions( 'Pwr In(dBm)',    3 )
    #mag.update_filter_conditions( 'Process',     [ 'SS', 'TT', 'FF' ] )
    mag.update_filter_conditions( 'Process',     'TT' )
    mag.update_filter_conditions( 'Test Freq(MHz)', [837.0, 1748.0] )


    mag.update_filter_conditions( sweep_param, vals )

    mag.xlimits = [ -20, 38 ]


    mag.update_filter_conditions( 'HB_LB', band )
    mag.update_filter_conditions( 'Segments', segs )

    mag.color_series.set(sweep_param)

    if segs == '00' : segtxt = '2seg'
    if segs == '11' : segtxt = '1seg'

    txt = ' %s-%s vs Pout  over %s' % ( band, segtxt, sweep_param )

    mag.ylimits = [ 0 , 40 ]
    xynames = ['Adj Pwr Out(dBm)', 'Gain AM/(VAM-offset) (dB) <emp-limits>' ]
    mag.plot_graph_data( xynames,  None, 'AM-AM Dist: ' + txt  )


    mag.ylimits = [ -1, 1 ]
    xynames = ['Adj Pwr Out(dBm)', 'Gain AM/(VAM-offset) Slope - Ref (dB/dB) <emp-limits>' ]
    mag.plot_graph_data( xynames,  None, 'AM-AM Dist Variation: ' + txt  )



    mag.ylimits = [ -100, 50 ]
    xynames = ['Adj Pwr Out(dBm)', 'AM-PM(degree)'     ]
    mag.plot_graph_data( xynames,  None, 'AM-PM Distortion: ' + txt  )

    mag.ylimits = [ -10, 10 ]
    xynames = ['Adj Pwr Out(dBm)', 'AM-PM Slope - Ref (deg/dB) <emp-limits>'     ]
    mag.plot_graph_data( xynames,  None, 'AM-PM Dist Variation: ' + txt  )


    mag.xlimits = [ 0.2, 1.7 ]
    mag.xgrid = 0.1
    mag.ylimits = [ -28, 36 ]
    xynames = ['VAM(volt)', 'Adj Pwr Out(dBm)' ]
    mag.plot_graph_data( xynames,  None, 'Output Power vs VAM: ' + txt  )
    mag.xgrid = None



###################################################################


# define the different series conditions that are to be plotted
# and also the filter conditions



mag.color_list = [ 'b','g','r','c','m','y' ]



#run_plots( 'LB', '00', 'Vbat(Volt)' , [2.7, 3.0, 3.5, 3.6, 4.0, 4.5]    )
#run_plots( 'LB', '00', 'Test Freq(MHz)')
#run_plots( 'LB', '00', 'Pwr In(dBm)'    )
run_plots( 'LB', '00', 'Temp(C)'        )
#run_plots( 'LB', '00', 'Process'        )


#run_plots( 'HB', '00', 'Vbat(Volt)' , [2.7, 3.0, 3.5, 3.6, 4.0, 4.5]    )
#run_plots( 'HB', '00', 'Test Freq(MHz)')
#run_plots( 'HB', '00', 'Pwr In(dBm)'    )
#run_plots( 'HB', '00', 'Temp(C)'        )
#run_plots( 'HB', '00', 'Process'        )


mag.loop()
