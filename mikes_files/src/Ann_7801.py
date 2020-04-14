#!/usr/bin/env python

# Load the libraries
import sys, time
sys.path.append('/home/masker/bin/python')
from pygram_dev import *

# The main program
g = pygram()

g.add_all_logfiles_dialog()
g.get_savefile_directory_dialog()

###################################################################################
def std_filter_cond(sweepname, xynames):
    ''' Setup the standard filter conditions for the main parameters except for the swept parameter
        it also defines the color and line style base on the swept parameter.'''
        
    if sweepname == 'Vramp Voltage' and 'Adj Pwr Out(dBm)' in xynames:
        return 0
    
    if len(g.values_dict[sweepname]) > 1 and sweepname not in xynames:
        g.update_filter_conditions('Vbat(Volt)',    vbat)
        g.update_filter_conditions('Pwr In(dBm)',   pin)
        g.update_filter_conditions('Temp(C)',       temp)
        g.update_filter_conditions('Process',       process)
        g.update_filter_conditions('Freq(MHz)',     freq)
        g.update_filter_conditions(sweepname,       None)
        
        # make sure we don't set a filter for either of the axes
        g.update_filter_conditions(xynames[0],      None)
        g.update_filter_conditions(xynames[1],      None)
        
        if sweepname == 'Vbat(Volt)' :
            g.update_filter_conditions(sweepname, vbat_sweep_list)
            
        if len(g.values_dict['Serial Number']) > 1 :
            g.color_series.set(sweepname)
            g.line_series.set('Serial Number')
        else :
            g.color_series.set(sweepname)
            g.line_series.set('')
            
        if len(g.values_dict['Serial Number']) * len(g.values_dict[sweepname]) > 16:
            g.small_legend.set(True)
        else :
            g.small_legend.set(False)
            
        return 1
    else :
        return 0
###################################################################################

xmin = 0
xmax = 10
ymin = 0
ymax = 10

lb_pae_max = 36
lb_pae_med = 24
hb_pae_max = 34
hb_pae_med = 28

lb_pout_max = 33.6
lb_pout_1 = 32.6
lb_pout_2 = 32.1
hb_pout_max = 31.9
hb_pout_1 = 30.9
hb_pout_2 = 30.4

lb_pout_hi = 32.6
lb_pout_lo = 29.1
hb_pout_hi = 29.9
hb_pout_lo = 28.4

lb_vramp = 1.35
hb_vramp = 1.2

lb_ptarget = 33.1
hb_ptarget = 31.4

# Set the standard conditions for this test
vbat = 3.5
pin = 3.0
temp = 25
process = 'TT'
freq = [880, 1710]

vbat_sweep_list = [2.7, 3.2, 3.5, 4.6]


# Plot format options
g.plot_linewidth = 1
g.legend_location = [0.8, 0.0]
g.small_legend.set(True)
g.sort_data_on.set(True)
g.save_plot_count = 0

#sweep_list = ['Freq(MHz)', 'Vbat(Volt)', 'Pwr In(dBm)', 'Temp(C)', 'Process', 'Vramp Voltage']
sweep_list = ['Freq(MHz)', 'Temp(C)', 'Process', 'Vramp Voltage']

if 0 :
    #############################################################
    ###  POUT VS VRAMP across Freq
    #############################################################
    xynames = ['Vramp Voltage', 'Adj Pwr Out(dBm)']
   
    for sweepname in sweep_list:
        if std_filter_cond(sweepname, xynames) == 0 :
            continue
        g.update_filter_conditions('TestName', 'Output Power & Efficiency')
        
        g.xgrid = 0.05
        g.update_filter_conditions('HB_LB', 'LB')
        #g.update_filter_conditions('Vbat(Volt)', 3.5)
        #g.update_filter_conditions('Pwr In(dBm)', 3.0)
        xmin = 0.8
        xmax = 1.7
        ymin = 26
        ymax = 35
        g.xlimits = [xmin, xmax]
        g.ylimits = [ymin, ymax]
        g.spec_limits = [[ [[xmin, lb_pout_max], [xmax, lb_pout_max]], 'Max Power=' + str(lb_pout_max) + 'dBm', 2, 'red']]
                         #[ [[xmin, lb_pout_1], [xmax, lb_pout_1]], 'Pout 1 = 32.6dBm', 2, 'red'],
                         #[ [[xmin, lb_pout_2], [xmax, lb_pout_2]], 'Pout 2 = 32.1dBm', 2, 'red']]
        #add plot title here
        g.plot_graph_data(xynames, None, 'LB ' + 'Pout vs Vramp across ' + sweepname)
        
        g.update_filter_conditions('HB_LB', 'HB')
        ymax = 33
        g.ylimits = [ymin, ymax]
        g.spec_limits = [[ [[xmin, hb_pout_max], [xmax, hb_pout_max]], 'Max Power=' + str(hb_pout_max) + 'dBm', 2, 'red']]
                         #[ [[xmin, hb_pout_1], [xmax, hb_pout_1]], 'Pout 1 = 30.9dBm', 2, 'red'],
                         #[ [[xmin, hb_pout_2], [xmax, hb_pout_2]], 'Pout 2 = 30.4dBm', 2, 'red']]
        g.plot_graph_data(xynames, None, 'HB ' + 'Pout vs Vramp across ' + sweepname)
        
        g.update_filter_conditions('TestName', None)
        

#sweep_list = ['Freq(MHz)', 'Vbat(Volt)', 'Temp(C)', 'Process', 'Vramp Voltage']
if 0 :
    sweep_list = ['Freq(MHz)', 'Vbat(Volt)', 'Temp(C)', 'Process', 'Vramp Voltage']
    #############################################################
    ###  POUT1 VS VRAMP across Vbat & Temp
    #############################################################
    xynames = ['Vramp Voltage', 'Adj Pwr Out(dBm)']
    for sweepname in sweep_list :
        if std_filter_cond(sweepname, xynames) == 0 :
            continue
        g.update_filter_conditions('TestName', 'Output Power & Efficiency')
       
        g.xgrid = 0.05
        g.update_filter_conditions('HB_LB', 'LB')
        xmin = 0.8
        xmax = 1.7
        ymin = 26
        ymax = 35
        g.xlimits = [xmin, xmax]
        g.ylimits = [ymin, ymax]
        g.sort_data_on.set(False)
        g.spec_limits = [[ [[xmin, lb_pout_1], [xmax, lb_pout_1]], 'Pout 1=' + str(lb_pout_1) + 'dBm', 2, 'red']]
        g.plot_graph_data(xynames, None, 'LB ' + 'Pout vs Vramp across ' + sweepname)
  
        g.update_filter_conditions('HB_LB', 'HB')
        ymax = 33
        g.ylimits = [ymin, ymax]
        g.spec_limits = [[ [[xmin, hb_pout_1], [xmax, hb_pout_1]], 'Pout 1=' + str(hb_pout_1) + 'dBm', 2, 'red']]
        g.plot_graph_data(xynames, None, 'HB ' + 'Pout vs Vramp across ' + sweepname)
       
if 0 :
    #############################################################
    ###  POUT2 VS VRAMP across Vbat & Temp
    #############################################################
    xynames = ['Vramp Voltage', 'Adj Pwr Out(dBm)']
    for sweepname in sweep_list :
        if std_filter_cond(sweepname, xynames) == 0 :
            continue
        g.update_filter_conditions('TestName', 'Output Power & Efficiency')
        
        g.xgrid = 0.05
        g.update_filter_conditions('HB_LB', 'LB')
        xmin = 0.8
        xmax = 1.7
        ymin = 26
        ymax = 35
        g.xlimits = [xmin, xmax]
        g.ylimits = [ymin, ymax]
        g.sort_data_on.set(False)
        g.spec_limits = [[ [[xmin, lb_pout_2], [xmax, lb_pout_2]], 'Pout 2=' + str(lb_pout_2) + 'dBm', 2, 'red']]
        g.plot_graph_data(xynames, None, 'LB ' + 'Pout vs Vramp across ' + sweepname)

        g.update_filter_conditions('HB_LB', 'HB')
        ymax = 33
        g.ylimits = [ymin, ymax]
        g.spec_limits = [[ [[xmin, hb_pout_2], [xmax, hb_pout_2]], 'Pout 2=' + str(hb_pout_2) + 'dBm', 2, 'red']]
        g.plot_graph_data(xynames, None, 'HB ' + 'Pout vs Vramp across ' + sweepname)
  

if 0 :
    sweep_list = ['Freq(MHz)', 'Temp(C)', 'Process', 'Vramp Voltage']
    #############################################################
    ######### POWER & PAE #######################################
    #############################################################
    xynames = ['Adj Pwr Out(dBm)', 'PAE(%)']
    for sweepname in sweep_list :
        if std_filter_cond(sweepname, xynames) == 0 :
            continue
        g.update_filter_conditions('TestName', 'Output Power & Efficiency')
        g.xgrid = 0.5

        g.update_filter_conditions('Pwr In(dBm)', 0)
        g.update_filter_conditions('HB_LB', 'LB')
        xmin = 25
        xmax = 35
        ymin = 15
        ymax = 47
        g.xlimits = [xmin, xmax]
        g.ylimits = [ymin, ymax]
        g.sort_data_on.set(False)
        g.spec_limits = [[ [[xmin, lb_pae_max], [xmax, lb_pae_max]], 'MAX PAE=' + str(lb_pae_max) + '%', 2, 'red'],
                         [ [[xmin, lb_pae_med], [xmax, lb_pae_med]], 'MED PAE=' + str(lb_pae_med) + '%', 2, 'red'],
                         [ [[lb_pout_hi, ymin], [lb_pout_hi, ymax]], 'Pout=' + str(lb_pout_hi) + 'dBm', 2, 'orange'],
                         [ [[lb_pout_lo, ymin], [lb_pout_lo, ymax]], 'Pout=' + str(lb_pout_lo) + 'dBm', 2, 'orange']]
        g.plot_graph_data(xynames, None, 'LB ' + 'PAE vs Pout across ' + sweepname)
        
        g.update_filter_conditions('HB_LB', 'HB')
        xmin = 25
        xmax = 33
        ymin = 20
        ymax = 38
        g.xlimits = [xmin, xmax]
        g.ylimits = [ymin, ymax]
        g.spec_limits = [[ [[xmin, hb_pae_max], [xmax, hb_pae_max]], 'MAX PAE=' + str(hb_pae_max) + '%', 2, 'red'],
                         [ [[xmin, hb_pae_med], [xmax, hb_pae_med]], 'MED PAE=' + str(hb_pae_med) + '%', 2, 'red'],
                         [ [[hb_pout_hi, ymin], [hb_pout_hi, ymax]], 'Pout=' + str(hb_pout_hi) + 'dBm', 2, 'orange'],
                         [ [[hb_pout_lo, ymin], [hb_pout_lo, ymax]], 'Pout=' + str(hb_pout_lo) + 'dBm', 2, 'orange']]
        g.plot_graph_data(xynames, None, 'HB ' + 'PAE vs Pout across ' + sweepname)


if 0 :
    #############################################################
    ######### IBAT vs POUT #######################################
    #############################################################
    sweep_list = ['Freq(MHz)', 'Temp(C)', 'Process', 'Vramp Voltage']
 
    xynames = ['Adj Pwr Out(dBm)', 'Vbat_I(Amp)']
    for sweepname in sweep_list :
        if std_filter_cond(sweepname, xynames) == 0 :
            continue
        
        g.update_filter_conditions('TestName', 'Output Power & Efficiency')
        g.xgrid = 0.5
        xmin = 25
        xmax = 35
        ymin = 0
        ymax = 2.0
        ivbat_max = 1.161
        g.update_filter_conditions('HB_LB', 'LB')
        g.xlimits = [xmin, xmax]
        g.ylimits = [ymin, ymax]
        g.sort_data_on.set(False)
        g.spec_limits = [[[[xmin, ivbat_max], [xmax, ivbat_max]], 'MAX Current=' + str(ivbat_max) + 'A', 4, 'red'],
                         [[[lb_ptarget, ymin], [lb_ptarget, ymax]], 'Ptarget=' + str(lb_ptarget) + 'dBm', 4, 'orange']]
        g.plot_graph_data(xynames, None, 'LB ' + 'IBAT Vs Pout across ' + sweepname)
        
        xmax = 33
        ivbat_max = 0.847
        g.update_filter_conditions('HB_LB', 'HB')
        g.xlimits = [xmin, xmax]
        g.ylimits = [ymin, ymax]
        g.spec_limits = [[[[xmin, ivbat_max], [xmax, ivbat_max]], 'MAX Current=' + str(ivbat_max) + 'A', 4, 'red'],
                         [[[hb_ptarget, ymin], [hb_ptarget, ymax]], 'Ptarget=' + str(hb_ptarget) + 'dBm', 4, 'orange']]
        g.plot_graph_data(xynames, None, 'HB ' + 'IBAT Vs Pout across ' + sweepname)

    g.update_filter_conditions('TestName', None)

if 0 :
    sweep_list = ['Freq(MHz)', 'Vbat(Volt)', 'Pwr In(dBm)', 'Temp(C)', 'Process', 'Vramp Voltage']
    #############################################################
    ######### HARMONICS #########################################
    #############################################################
    yi = 0
    hlimits = [-36, -36, -36, -36, -36, -36, -36, -36, -36]
    for yaxis in ('2nd Harmonics Amplitude(dBm)',
                  '3rd Harmonics Amplitude(dBm)',
                  '4th Harmonics Amplitude(dBm)',
                  '5th Harmonics Amplitude(dBm)',
                  '6th Harmonics Amplitude(dBm)',
                  '7th Harmonics Amplitude(dBm)',
                  '8th Harmonics Amplitude(dBm)',
                  '9th Harmonics Amplitude(dBm)',
                  '10th Harmonics Amplitude(dBm)') :
        limit = hlimits[yi]
        yi += 1
        
        xynames = ['Adj Pwr Out(dBm)', yaxis]
        for sweepname in sweep_list:
            if std_filter_cond(sweepname, xynames) == 0 :
                continue
            g.sort_data_on.set(True)
            
            ######### Harmonic vs POUT #############################
            g.xgrid = 1
            g.ygrid = 2
            
            g.update_filter_conditions('HB_LB', 'LB')
            xmin = 29
            xmax = 37
            ymin = -60
            ymax = -5
            g.xlimits = [xmin, xmax]
            g.ylimits = [ymin, ymax]
            g.spec_limits = [limit, 'Max Limit', 4, 'red']
            g.plot_graph_data(xynames, None, 'LB ' + yaxis + ' vs Pout across ' + sweepname)
            
            if yi < 7 :
                xmin = 26
                xmax = 35
                g.xlimits = [xmin, xmax]
                g.update_filter_conditions('HB_LB', 'HB')
                g.spec_limits = [limit, 'Max Limit', 4, 'red']
                g.plot_graph_data(xynames, None,'HB ' + yaxis + ' vs Pout across ' + sweepname)
                

if 0 :
    sweep_list = [ 'Freq(MHz)' , 'Vbat(Volt)', 'Pwr In(dBm)', 'Temp(C)', 'Process', 'Vramp Voltage' ]
    #############################################################
    ######### FORWARD ISOLATION #################################
    #############################################################
    xynames = ['Freq(MHz)', 'Fwd Isol1 (TxOff) Amplitude(dBm)']
    for sweepname in sweep_list :
        if std_filter_cond(sweepname, xynames) == 0 :
            continue
        
        g.xgrid = 10
        g.ygrid = 1
        
        # Fwd Iso 1
        ymin = -70
        ymax = -20
        g.xlimits = []
        g.ylimits = [ymin, ymax]
        
        g.update_filter_conditions('Vramp Voltage', 1.4)
        g.update_filter_conditions('HB_LB', 'LB')
        g.spec_limits = [-40, 'Max Limit', 4, 'red']
        g.plot_graph_data(xynames, None, 'LB Fwd Iso 1 (TXEN=0 VRAMP=1.4V) vs Freq across ' + sweepname)
        g.update_filter_conditions('HB_LB', 'HB')
        g.spec_limits = [-52, 'Max Limit', 4, 'red']
        g.plot_graph_data(xynames, None, 'HB Fwd ISo 1 (TXEN=0 VRAMP=1.4V) vs Freq across ' + sweepname)
        
   
    xynames = ['Freq(MHz)', 'Fwd Isol2 (TxOn) Amplitude(dBm)']
    for sweepname in sweep_list :
        if std_filter_cond(sweepname, xynames) == 0 :
            continue
        # Fwd Iso 2
        ymin = -70
        ymax = -20
        g.xlimits = []
        g.ylimits = [ymin, ymax]
        
        g.update_filter_conditions('Vramp Voltage', 0.15)
        g.update_filter_conditions('HB_LB', 'LB')
        g.spec_limits = [-40, 'Max Limit', 4, 'red']
        g.plot_graph_data(xynames, None, 'LB Fwd Iso 2 (TXEN=1 VRAMP=0.15) vs Freq across ' + sweepname)
        g.update_filter_conditions('HB_LB', 'HB')
        g.spec_limits = [-52, 'Max Limit', 4, 'red']
        g.plot_graph_data(xynames, None, 'HB Fwd ISo 2 (TXEN=1 VRAMP=0.15) vs Freq across ' + sweepname)
        

if 0 :
    #############################################################
    ######### ORFS 400KHz #######################################
    #############################################################
    xynames = ['Vramp Voltage', 'Sw Pwr 400KHz(dBm)']
    for sweepname in sweep_list :
        if std_filter_cond(sweepname, xynames) == 0 :
            continue
        
        g.xgrid = 0.1
        xmin = 0.5
        xmax = 1.6
        ymin = -40
        ymax = -10
        g.xlimits = [xmin, xmax]
        g.ylimits = [ymin, ymax]
        
        g.update_filter_conditions('HB_LB', 'LB')
        g.spec_limits = [[-27, 'Max Limit', 4, 'red']]
        g.plot_graph_data(xynames, None, 'LB Sw Pwr 400KHz (dBm) vs Pout across ' + sweepname)
        
        g.update_filter_conditions('HB_LB', 'HB')
        g.spec_limits = [[-30, 'Max Limit', 4, 'red']]
        g.plot_graph_data(xynames, None, 'HB Sw Pwr 400KHz (dBm) vs Pout across ' + sweepname)
 
if 0 :
    #############################################################
    ######### ORFS 600KHz #######################################
    #############################################################
    xynames = ['Vramp Voltage', 'Sw Pwr 600KHz(dBm)']
    for sweepname in sweep_list :
        if std_filter_cond(sweepname, xynames) == 0:
            continue
        
        g.xgrid = 0.1
        xmin = 0.5
        xmax = 1.6
        ymin = -40
        ymax = -10
        g.xlimits = [xmin, xmax]
        g.ylimits = [ymin, ymax]
   
        g.update_filter_conditions('HB_LB', 'LB')
        g.spec_limits = [[-29, 'Max Limit', 4, 'red']]
        g.plot_graph_data(xynames, None, 'LB Sw Pwr 600KHz (dBm) vs Pout across ' + sweepname)
        
        g.update_filter_conditions('HB_LB', 'HB')
        g.spec_limits = [[-32, 'Max Limit', 4, 'red']]
        g.plot_graph_data(xynames, None, 'HB Sw Pwr 600KHz (dBm) vs Pout across ' + sweepname)
    
if 1 :
    #############################################################
    ######### Power Variation vs Pout @ Ta= 25..60 ##############
    #############################################################
    xsweep_list = ['Freq(MHz)', 'Vbat(Volt)', 'Pwr In(dBm)', 'Temp(C)', 'Process', 'Vramp Voltage']
    xynames = ['Adj Pwr Out(dBm)', 'Pwr Variation(dB)']
    for sweepname in sweep_list :
        if std_filter_cond(sweepname, xynames) == 0 :
            continue
        
        g.xgrid = 5
        g.ygrid = 1
        xmin = -30
        xmax = 35
        ymin = -15
        ymax = 15
        g.xlimits = [xmin, xmax]
        g.ylimits = [ymin, ymax]
        
        g.update_filter_conditions('HB_LB', 'LB')
        g.update_filter_conditions('Temp(C)', [25,60])
        g.spec_limits = [[[[-20, -9], [-15, -9]], 'Max Limit 1', 4, 'red'],
                         [[[-20, 9], [-15, 9]], 'Max Limit 1', 4, 'red'],
                         [[[5.3, -4.5], [11.3, -4.5]], 'Max Limit 2', 4, 'red'],
                         [[[5.3, 4.5], [11.3, 4.5]], 'Max Limit 2', 4, 'red'],
                         [[[13.3, -2.5], [31.3, -2.5]], 'Max Limit 3', 4, 'red'],
                         [[[13.3, 2.5], [31.3, 2.5]], 'Max Limit 3', 4, 'red'],
                         [[[32.8, -1], [32.9, -1]], 'Max Limit 4', 4, 'red'],
                         [[[32.8, 1.5], [32.9, 1.5]], 'Max Limit 4', 4, 'red']]
        g.line_series.set('Temp(C)')
        g.plot_graph_data(xynames, None, 'LB Pwr Variation vs Pout @ Ta= 25..60 across ' + sweepname)
        
        g.update_filter_conditions('HB_LB', 'HB')
        g.spec_limits = [[[[-20, -9], [-15, -9]], 'Max Limit 1', 4, 'red'],
                         [[[-20, 9], [-15, 9]], 'Max Limit 1', 4, 'red'],
                         [[[0.4, -4.5], [2.4, -4.5]], 'Max Limit 2', 4, 'red'],
                         [[[0.4, 4.5], [2.4, 4.5]], 'Max Limit 2', 4, 'red'],
                         [[[4.4, -3.5], [12.4, -3.5]], 'Max Limit 3', 4, 'red'],
                         [[[4.4, 3.5], [12.4, 3.5]], 'Max Limit 3', 4, 'red'],
                         [[[14.4, -2.5], [28.4, -2.5]], 'Max Limit 4', 4, 'red'],
                         [[[14.4, 2.5], [28.4, 2.5]], 'Max Limit 4', 4, 'red'],
                         [[[30.9, 1], [31, 1]], 'Max Limit 5', 4, 'red'],
                         [[[30.9, -1.5], [31, -1.5]], 'Max Limit 5', 4, 'red']]
        g.plot_graph_data(xynames, None, 'HB Pwr Variation vs Pout @ Ta= 25..60 across ' + sweepname)
            
if 1 :
    #############################################################
    ######### Power Variation vs Pout @ Ta= -15..85 #############
    #############################################################
    xsweep_list = ['Freq(MHz)', 'Vbat(Volt)', 'Pwr In(dBm)', 'Temp(C)', 'Process', 'Vramp Voltage']
    xynames = ['Adj Pwr Out(dBm)', 'Pwr Variation(dB)']
    for sweepname in sweep_list :
        if std_filter_cond(sweepname, xynames) == 0 :
            continue
        
        g.xgrid = 5
        g.ygrid = 1
        xmin = -30
        xmax = 35
        ymin = -15
        ymax = 15
        g.xlimits = [xmin, xmax]
        g.ylimits = [ymin, ymax]
        
        g.update_filter_conditions('HB_LB', 'LB')
        g.update_filter_conditions('Temp(C)', [-15,85])
        g.spec_limits = [[[[-20, -10], [-15, -10]], 'Max Limit 1', 4, 'red'],
                         [[[-20, 10], [-15, 10]], 'Max Limit 1', 4, 'red'],
                         [[[5.3, -5.5], [11.3, -5.5]], 'Max Limit 2', 4, 'red'],
                         [[[5.3, 5.5], [11.3, 5.5]], 'Max Limit 2', 4, 'red'],
                         [[[13.3, -3.5], [31.3, -3.5]], 'Max Limit 3', 4, 'red'],
                         [[[13.3, 3.5], [31.3, 3.5]], 'Max Limit 3', 4, 'red'],
                         [[[32.8, -1.5], [32.9, -1.5]], 'Max Limit 4', 4, 'red'],
                         [[[32.8, 2], [32.9, 2]], 'Max Limit 4', 4, 'red']]
        g.line_series.set('Temp(C)')
        g.plot_graph_data(xynames, None, 'LB Pwr Variation vs Pout @ Ta= -15..85 across ' + sweepname)
        
        g.update_filter_conditions('HB_LB', 'HB')
        g.spec_limits = [[[[-20, -10], [-15, -10]], 'Max Limit 1', 4, 'red'],
                         [[[-20, 10], [-15, 10]], 'Max Limit 1', 4, 'red'],
                         [[[0.4, -5.5], [2.4, -5.5]], 'Max Limit 2', 4, 'red'],
                         [[[0.4, 5.5], [2.4, 5.5]], 'Max Limit 2', 4, 'red'],
                         [[[4.4, -4.5], [12.4, -4.5]], 'Max Limit 3', 4, 'red'],
                         [[[4.4, 4.5], [12.4, 4.5]], 'Max Limit 3', 4, 'red'],
                         [[[14.4, -3.5], [28.4, -3.5]], 'Max Limit 4', 4, 'red'],
                         [[[14.4, 3.5], [28.4, 3.5]], 'Max Limit 4', 4, 'red'],
                         [[[30.9, 2], [31, 2]], 'Max Limit 5', 4, 'red'],
                         [[[30.9, -2], [31, -2]], 'Max Limit 5', 4, 'red']]
        g.plot_graph_data(xynames, None, 'HB Pwr Variation vs Pout @ Ta= -15..85 across ' + sweepname)
       
    

##################################################################     
g.loop()    # loop forever, and wait for input from the user
