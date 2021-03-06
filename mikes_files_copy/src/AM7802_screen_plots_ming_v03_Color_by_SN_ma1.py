#!/usr/bin/python

# Load the libraries 
import sys
sys.path.append(r'/projects/sw/release')
sys.path.append(r'N:\sw\release')
from pygram_dev import *



# The main program

g = pygram()

g.add_all_logfiles_dialog()
g.get_savefile_directory_dialog()

###################################################################################

def std_filter_cond( sweepname , xynames ):

    ''' Sets up the standard filter condtions for the main parameters except for the swept paramter
        it also defines the color and line style based on the swept parameter. '''

#   print '(std_filter_cond) ', sweepname,  g.values_dict[ sweepname ] , xynames

    if sweepname == 'Vramp Voltage' and 'Adj Pwr Out(dBm)' in xynames: 
       return 0




    if len(g.values_dict[ sweepname ]) > 1 and sweepname not in xynames :

        g.update_filter_conditions( 'Vbat(Volt)',      vbat    )
        g.update_filter_conditions( 'Pwr In(dBm)',     pin     )
        g.update_filter_conditions( 'Temp(C)',         temp    )
        g.update_filter_conditions( 'Process' ,        process )
        g.update_filter_conditions( 'Test Freq(MHz)' , freq    )
        g.update_filter_conditions( sweepname,         None    )


        # make sure we don't set a filter for either of the axes
        g.update_filter_conditions( xynames[0],         None    )
        g.update_filter_conditions( xynames[1],         None    )


        if sweepname == 'Vbat(Volt)' :
            g.update_filter_conditions( sweepname,         vbat_sweep_list    )


        if len( g.values_dict[ 'Serial Number' ]) > 1 :
            g.color_series.set(  'Serial Number'  )
            g.line_series.set( sweepname  )
        else:
            g.color_series.set( sweepname  )
            g.line_series.set(  ''  )

        if len( g.values_dict[ 'Serial Number' ]) * len( g.values_dict[ sweepname ]) > 16 : g.small_legend.set( True   )
        else:                                                                               g.small_legend.set( False  )

        return 1

    else:
 
        return 0

###################################################################################

# Set Specline Limit Here

pael_max = 47    # typ pae at rated power lb
pael_33 = 46     # typ pae at rated power lb 33 dBm
pael_29 = 31     # typ pae at rated power lb 29 dBm

paeh_max = 37    # typ pae at rated power hb
paeh_30 = 35     # typ pae at rated power hb 30 dBm
paeh_28 = 27     # typ pae at rated power hb 28 dBm

pwrl = 33        # rated power for lb
pwrl_v3p0 = 30.5 # rated power for lb
pwrl_v2p7 = 29   # rated power for lb

pwrh = 30        # rated power for hb
pwrh_v3p0 = 28.5 # rated power for hb
pwrh_v2p7 = 28   # rated power for hb

fwd_iso1_l_max = -40  # max forward isolation 1 lb
fwd_iso1_l_typ = -55  # typ forward isolation 1 lb
fwd_iso2_l_max = -22  # max forward isolation 2 lb
fwd_iso2_l_typ = -25  # typ forward isolation 2 lb

fwd_iso1_h_max_pin6 = -48 # max forward isolation 1 hb
fwd_iso1_h_max_pin3 = -50 # max forward isolation 1 hb
fwd_iso1_h_typ = -60  # typ forward isolation 1 hb
fwd_iso2_h_max = -25  # max forward isolation 2 hb
fwd_iso2_h_typ = -30  # typ forward isolation 2 hb

orfs_400k_l_max = -24 # max limit ORFS 400KHz lb
orfs_400k_l_typ = -28 # max limit ORFS 400KHz lb

orfs_400k_h_max = -24 # max limit ORFS 400KHz hb
orfs_400k_h_typ = -28 # max limit ORFS 400KHz hb

vramph = 1.2      # vramp voltage for rated power for hb
vrampl = 1.35     # vramp voltage for rated power for lb

#   Set the standard conditions for this test
vbat = 3.5
pin  = 3.0
temp = 25
process  = 'TT'
freq = [880, 1785]  

vbat_sweep_list = [ 2.7, 3.0, 3.2, 3.5, 4.0, 4.5]

# Plot format options
g.plot_linewidth = 1
g.legend_location     = [ 0.70, 0.0   ] 
#g.small_legend.set( True )
g.sort_data_on.set(False)
g.save_plot_count = 0

# sweep_list = [ 'Test Freq(MHz)' , 'Vbat(Volt)', 'Pwr In(dBm)','Temp(C)', 'Process', 'Vramp Voltage' ]

#############################################################
###  1 LB - Maximum Output Power Nominal
#############################################################

sweep_list = [ 'Test Freq(MHz)', 'Pwr In(dBm)', 'Vramp Voltage' ]

g.update_filter_conditions( 'HB_LB', 'LB' )
g.update_filter_conditions( 'Vbat(Volt)', 3.5 )
g.update_filter_conditions( 'Temp(C)', 25 )
freq = [915] 

xynames = [ 'Vramp Voltage' , 'Adj Pwr Out(dBm)'  ]

for sweepname in sweep_list:
    
    if std_filter_cond( sweepname, xynames ) == 0 : continue
    g.update_filter_conditions( 'TestName', 'Output Power & Efficiency' )
    
    g.xgrid   = 0.05
    g.ygrid   = 0.5
    g.xlimits = [0.8, 1.7]   
    g.ylimits = [26 , 35] 
    g.spec_limits = [[ pwrl , "Min Pout, Nominal", 4, "red" ]]
    g.plot_graph_data( xynames, None, '#1 LB' + ' Pout vs VRAMP across ' + sweepname)

#############################################################
###  2 LB - Maximum Output Power Extreme (Vbat >= 3.0)
#############################################################

sweep_list = [ 'Vbat(Volt)', 'Temp(C)', 'Vramp Voltage' ]
vbat_sweep_list = [3.0, 3.2, 3.5, 4.0, 4.5]
freq = [915]
pin  = 3.0

xynames = [ 'Vramp Voltage' , 'Adj Pwr Out(dBm)'  ]

for sweepname in sweep_list:
    
    if std_filter_cond( sweepname, xynames ) == 0 : continue
    g.update_filter_conditions( 'TestName', 'Output Power & Efficiency' )
     
    g.spec_limits = [[ pwrl_v3p0 , "Min. Pout, Extreme", 4, "red"]]
    g.plot_graph_data( xynames, None, '#2 LB' + ' Pout (Vbat>=3.0V) vs VRAMP across ' + sweepname)

#############################################################
###  2 LB - Maximum Output Power Extreme (Vbat = 2.7)
#############################################################

sweep_list = [ 'Test Freq(MHz)', 'Temp(C)', 'Vramp Voltage' ]
vbat = 2.7
pin  = 3.0

xynames = [ 'Vramp Voltage' , 'Adj Pwr Out(dBm)'  ]

for sweepname in sweep_list:
    
    if std_filter_cond( sweepname, xynames ) == 0 : continue
    g.update_filter_conditions( 'TestName', 'Output Power & Efficiency' )
     
    g.spec_limits = [[ pwrl_v2p7 , "Min. Pout, Extreme", 4, "red"]]
    g.plot_graph_data( xynames, None, '#2 LB' + ' Pout (Vbat=2.7V) vs VRAMP across ' + sweepname)

#############################################################
### 5-7 LB - PAE
#############################################################
    
sweep_list = [ 'Test Freq(MHz)', 'Vramp Voltage' ]
g.update_filter_conditions( 'Vbat(Volt)', 3.5 )
vbat = 3.5
pin  = 3.0
xynames = [ 'Adj Pwr Out(dBm)' , 'PAE(%)' ]
for sweepname in sweep_list:
    if std_filter_cond( sweepname, xynames ) == 0 : continue

    g.xgrid   = 0.5
    g.ygrid   = 2
    g.xlimits = [26, 35]
    g.ylimits = [20, 50] 
    g.spec_limits = [[ [[pwrl,g.ylimits[0]],[pwrl,g.ylimits[1]]] , "", 4, "yellow" ],
                     [ [[pwrl_v2p7,g.ylimits[0]],[pwrl_v2p7,g.ylimits[1]]] , "", 4, "yellow" ],
                     [ [[33.5,pael_max],[34.5,pael_max]], "PAE @ max Pout", 4, "blue" ],
                     [ [[pwrl-0.5,pael_33],[pwrl+0.5,pael_33]], "PAE @ 33 dBm", 4, "blue" ],
                     [ [[pwrl_v2p7-0.5,pael_29],[pwrl_v2p7+0.5,pael_29]] , "PAE @ 29 dBm", 4, "blue" ]]
    g.plot_graph_data( xynames, None, '#5_7 LB' + ' PAE vs POUT across ' + sweepname)

g.update_filter_conditions( 'TestName', None )
g.update_filter_conditions( 'Test Freq(MHz)', None )

#############################################################
###  12 LB - Forward Isolation 1
#############################################################

g.update_filter_conditions( 'Vramp Voltage', 0.15 )
g.update_filter_conditions( 'Pwr In(dBm)'    , 6 )
vbat = 3.5
pin  = 6.0
vbat_sweep_list = [ 2.7, 3.5, 4.5]

xynames = [ 'Test Freq(MHz)', 'Fwd Isol1 (TxOff) Amplitude(dBm)' ]
sweep_list = [ 'Test Freq(MHz)']
g.color_series.set(  'Serial Number'  )

for sweepname in sweep_list:
    # if std_filter_cond( sweepname, xynames ) == 0 : continue
    
    g.xlimits = []
    g.ylimits = [-70, -10]
    g.xgrid   = 10
    g.ygrid   = 5

    g.spec_limits = [[ fwd_iso1_l_max , "Max Limit", 4, "red" ],
                     [ fwd_iso1_l_typ , "Typical Limit", 4, "blue" ]]
    g.plot_graph_data( xynames, None,  "#12 LB Fwd Iso1 (TX_EN=0, VRAMP=0.15v) vs Freq")

#############################################################
###  13 LB - Forward Isolation 2
#############################################################

g.update_filter_conditions( 'Vramp Voltage', 0.15 )
g.update_filter_conditions( 'Pwr In(dBm)'    , 6 )
vbat = 3.5
pin  = 6.0
vbat_sweep_list = [ 2.7, 3.5, 4.5]

xynames = [ 'Test Freq(MHz)', 'Fwd Isol2 (TxOn) Amplitude(dBm)' ]
sweep_list = [ 'Test Freq(MHz)']
g.color_series.set(  'Serial Number'  )

for sweepname in sweep_list:
    # if std_filter_cond( sweepname, xynames ) == 0 : continue
    
    g.xlimits = []
    g.ylimits = [-70, -10]
    g.xgrid   = 10
    g.ygrid   = 5

    g.spec_limits = [[ fwd_iso2_l_max , "Max Limit", 4, "red" ],
                     [ fwd_iso2_l_typ , "Typical Limit", 4, "blue" ]]
    g.plot_graph_data( xynames, None,  "#12 LB Fwd Iso2 (TX_EN=1, VRAMP=0.15v) vs Freq")   

g.update_filter_conditions( 'TestName', None )
g.update_filter_conditions( 'Test Freq(MHz)', None )
g.update_filter_conditions( 'Vramp Voltage', None )

#############################################################
###  14 LB - Harmonic Distortion
#############################################################

# sweep_list = [ 'Test Freq(MHz)' , 'Pwr In(dBm)','Temp(C)', 'Vramp Voltage' ]
sweep_list = [ 'Test Freq(MHz)','Temp(C)', 'Vramp Voltage' ]
g.update_filter_conditions( 'HB_LB', 'LB' )
vbat = 3.5
pin=3

yi = 0
hlimits = [ -33, -33, -33, -33, -33, -33, -33, -33, -33]
for yaxis in ( '2nd Harmonics Amplitude(dBm)', 
               '3rd Harmonics Amplitude(dBm)',
               '4th Harmonics Amplitude(dBm)',
               '5th Harmonics Amplitude(dBm)',
               '6th Harmonics Amplitude(dBm)',
               '7th Harmonics Amplitude(dBm)',
               '8th Harmonics Amplitude(dBm)',
               '9th Harmonics Amplitude(dBm)',
               '10th Harmonics Amplitude(dBm)',
             ):
    
    limit = hlimits[yi]
    yi = yi + 1

    xynames = [ 'Adj Pwr Out(dBm)' , yaxis ]

    for sweepname in sweep_list:

        if std_filter_cond( sweepname, xynames ) == 0 : continue
        g.sort_data_on.set(True)

        g.xgrid   = 0.25
        g.ygrid   = 5
        g.xlimits = [32,34]
        g.ylimits = [-60, 0]

        g.spec_limits = [[ limit , "Max Limit", 4, "red" ],
                         [ [[pwrl,g.ylimits[0]],[pwrl,g.ylimits[1]]] , "", 4, "yellow" ]]
        g.plot_graph_data( xynames, None, '#14 LB' + ' ' + yaxis + " vs POUT across " + sweepname)
  
g.update_filter_conditions( 'TestName', None )
#############################################################
###  24 LB - ORFS, Nominal Conditions (400KHz) - SWEEP POUT
#############################################################

sweep_list = [ 'Test Freq(MHz)', 'Pwr In(dBm)', 'Temp(C)', 'Vramp Voltage' ]
g.update_filter_conditions( 'Vbat(Volt)', 3.5 )
freq = [880]
vbat = 3.5
pin  = 3.0
xynames = [ 'Adj Pwr Out(dBm)' , 'Sw Pwr 400KHz(dBm)' ]

for sweepname in sweep_list:
    
    if std_filter_cond( sweepname, xynames ) == 0 : continue

    g.xlimits = [32, 34]   
    g.ylimits = [-40, -10]
    g.xgrid   = 0.25
    g.ygrid   = 5
    g.spec_limits = [[ orfs_400k_l_max , "Max. limit, Extreme conditions", 4, "red" ],
                      [ orfs_400k_l_typ , "Typ. limit, Nominal conditions", 4, "blue" ],
                     [ [[pwrl,g.ylimits[0]],[pwrl, g.ylimits[1] ]] , "", 4, "yellow" ]]
    g.plot_graph_data( xynames, None, '#24 LB' + ' 400kHz ORFS vs POUT across  ' + sweepname)

#############################################################
###  24 LB - ORFS, Nominal Conditions (400KHz) - SWEEP VBAT
#############################################################

sweep_list = [ 'Vbat(Volt)', 'Temp(C)', 'Vramp Voltage' ]
freq = [880]
pin  = 3.0
xynames = [ 'Vbat(Volt)' , 'Sw Pwr 400KHz(dBm)' ]

for sweepname in sweep_list:
    
    if std_filter_cond( sweepname, xynames ) == 0 : continue

    g.xlimits = [2.5, 3.9]   
    g.ylimits = [-40, -10]
    g.xgrid   = 0.1
    g.ygrid   = 5
    g.spec_limits = [[ orfs_400k_l_max , "Max. limit, Extreme conditions", 4, "red" ],
                      [ orfs_400k_l_typ , "Typ. limit, Nominal conditions", 4, "blue" ],
                     [ [[pwrl, g.ylimits[0]],[pwrl, g.ylimits[1] ]] , "", 4, "yellow" ]]
    g.plot_graph_data( xynames, None, '#24 LB' + ' 400kHz ORFS vs VBAT across  ' + sweepname)

#############################################################
###  1 HB - Maximum Output Power Nominal
#############################################################

sweep_list = [ 'Test Freq(MHz)', 'Pwr In(dBm)', 'Vramp Voltage' ]

g.update_filter_conditions( 'HB_LB', 'HB' )
g.update_filter_conditions( 'Vbat(Volt)', 3.5 )
g.update_filter_conditions( 'Temp(C)', 25 )
freq = [1910] 

xynames = [ 'Vramp Voltage' , 'Adj Pwr Out(dBm)'  ]

for sweepname in sweep_list:
    
    if std_filter_cond( sweepname, xynames ) == 0 : continue
    g.update_filter_conditions( 'TestName', 'Output Power & Efficiency' )
    
    g.xgrid   = 0.05
    g.ygrid   = 0.5
    g.xlimits = [0.8, 1.7]   
    g.ylimits = [24 , 33] 
    g.spec_limits = [[ pwrh , "Min Pout, Nominal", 4, "red" ]]
    g.plot_graph_data( xynames, None, '#1 HB' + ' Pout vs VRAMP across ' + sweepname)

#############################################################
###  2 HB - Maximum Output Power Extreme (Vbat >= 3.0)
#############################################################

sweep_list = [ 'Vbat(Volt)', 'Temp(C)', 'Vramp Voltage' ]
vbat_sweep_list = [3.0, 3.2, 3.5, 4.0, 4.5]
freq = [1910]
pin  = 3.0

xynames = [ 'Vramp Voltage' , 'Adj Pwr Out(dBm)'  ]

for sweepname in sweep_list:
    
    if std_filter_cond( sweepname, xynames ) == 0 : continue
    g.update_filter_conditions( 'TestName', 'Output Power & Efficiency' )
     
    g.spec_limits = [[ pwrh_v3p0 , "Min. Pout, Extreme", 4, "red"]]
    g.plot_graph_data( xynames, None, '#2 HB' + ' Pout (Vbat>=3.0V) vs VRAMP across ' + sweepname)

#############################################################
###  2 HB - Maximum Output Power Extreme (Vbat = 2.7)
#############################################################

sweep_list = [ 'Test Freq(MHz)', 'Temp(C)', 'Vramp Voltage' ]
vbat = 2.7
pin  = 3.0

xynames = [ 'Vramp Voltage' , 'Adj Pwr Out(dBm)'  ]

for sweepname in sweep_list:
    
    if std_filter_cond( sweepname, xynames ) == 0 : continue
    g.update_filter_conditions( 'TestName', 'Output Power & Efficiency' )
     
    g.spec_limits = [[ pwrh_v2p7 , "Min. Pout, Extreme", 4, "red"]]
    g.plot_graph_data( xynames, None, '#2 HB' + ' Pout (Vbat=2.7V) vs VRAMP across ' + sweepname)

#############################################################
### 5-7 HB - PAE
#############################################################
    
sweep_list = [ 'Test Freq(MHz)', 'Vramp Voltage' ]
g.update_filter_conditions( 'Vbat(Volt)', 3.5 )
vbat = 3.5
pin  = 3.0
xynames = [ 'Adj Pwr Out(dBm)' , 'PAE(%)' ]
for sweepname in sweep_list:
    if std_filter_cond( sweepname, xynames ) == 0 : continue

    g.xgrid   = 0.5
    g.ygrid   = 2
    g.xlimits = [24, 33]
    g.ylimits = [15, 45] 
    g.spec_limits = [[ [[pwrh,g.ylimits[0]],[pwrh,g.ylimits[1]]] , "", 4, "yellow" ],
                     [ [[pwrh_v2p7,g.ylimits[0]],[pwrh_v2p7,g.ylimits[1]]] , "", 4, "yellow" ],
                     [ [[30.5,paeh_max],[31.5,paeh_max]], "PAE @ max Pout", 4, "blue" ],
                     [ [[pwrh-0.5,paeh_30],[pwrh+0.5,paeh_30]], "PAE @ 30 dBm", 4, "blue" ],
                     [ [[pwrh_v2p7-0.5,paeh_28],[pwrh_v2p7+0.5,paeh_28]] , "PAE @ 28 dBm", 4, "blue" ]]
    g.plot_graph_data( xynames, None, '#5_7 HB' + ' PAE vs POUT across ' + sweepname)

g.update_filter_conditions( 'TestName', None )
g.update_filter_conditions( 'Test Freq(MHz)', None )

#############################################################
###  12 HB - Forward Isolation 1 (Pin=6 dBm)
#############################################################

g.update_filter_conditions( 'Vramp Voltage', 0.15 )
g.update_filter_conditions( 'Pwr In(dBm)'    , 6 )
vbat = 3.5
pin  = 6.0
vbat_sweep_list = [ 2.7, 3.5, 4.5]

xynames = [ 'Test Freq(MHz)', 'Fwd Isol1 (TxOff) Amplitude(dBm)' ]
sweep_list = [ 'Test Freq(MHz)']
g.color_series.set(  'Serial Number'  )

for sweepname in sweep_list:
    #if std_filter_cond( sweepname, xynames ) == 0 : continue
    
    g.xlimits = []
    g.ylimits = [-70, -10]
    g.xgrid   = 20
    g.ygrid   = 5

    g.spec_limits = [[ fwd_iso1_h_max_pin6 , "Max Limit", 4, "red" ],
                     [ fwd_iso1_h_typ , "Typical Limit", 4, "blue" ]]
    g.plot_graph_data( xynames, None,  "#12 HB Fwd Iso1 (TX_EN=0, VRAMP=0.15v, Pin=6dBm) vs Freq")

#############################################################
###  12 HB - Forward Isolation 1 (Pin=3 dBm)
#############################################################

g.update_filter_conditions( 'Vramp Voltage', 0.15 )
g.update_filter_conditions( 'Pwr In(dBm)'    , 3 )
vbat = 3.5
pin  = 3.0
vbat_sweep_list = [ 2.7, 3.5, 4.5]

xynames = [ 'Test Freq(MHz)', 'Fwd Isol1 (TxOff) Amplitude(dBm)' ]
sweep_list = [ 'Test Freq(MHz)']
g.color_series.set(  'Serial Number'  )

for sweepname in sweep_list:
    #if std_filter_cond( sweepname, xynames ) == 0 : continue
    
    g.xlimits = []
    g.ylimits = [-70, -10]
    g.xgrid   = 20
    g.ygrid   = 5

    g.spec_limits = [[ fwd_iso1_h_max_pin3 , "Max Limit", 4, "red" ],
                     [ fwd_iso1_h_typ , "Typical Limit", 4, "blue" ]]
    g.plot_graph_data( xynames, None,  "#12 HB Fwd Iso1 (TX_EN=0, VRAMP=0.15v, Pin=3dBm) vs Freq")

#############################################################
###  13 HB - Forward Isolation 2
#############################################################

g.update_filter_conditions( 'Vramp Voltage', 0.15 )
g.update_filter_conditions( 'Pwr In(dBm)'    , 6 )
vbat = 3.5
pin  = 6.0
vbat_sweep_list = [ 2.7, 3.5, 4.5]

xynames = [ 'Test Freq(MHz)', 'Fwd Isol2 (TxOn) Amplitude(dBm)' ]
sweep_list = [ 'Test Freq(MHz)']
g.color_series.set(  'Serial Number'  )

for sweepname in sweep_list:
    #if std_filter_cond( sweepname, xynames ) == 0 : continue
    
    g.xlimits = []
    g.ylimits = [-70, -10]
    g.xgrid   = 20
    g.ygrid   = 5

    g.spec_limits = [[ fwd_iso2_h_max , "Max Limit", 4, "red" ],
                     [ fwd_iso2_h_typ , "Typical Limit", 4, "blue" ]]
    g.plot_graph_data( xynames, None,  "#12 HB Fwd Iso2 (TX_EN=1, VRAMP=0.15v) vs Freq")   

g.update_filter_conditions( 'TestName', None )
g.update_filter_conditions( 'Test Freq(MHz)', None )
g.update_filter_conditions( 'Vramp Voltage', None )

#############################################################
###  14 HB - Harmonic Distortion
#############################################################

# sweep_list = [ 'Test Freq(MHz)' , 'Pwr In(dBm)','Temp(C)', 'Vramp Voltage' ]
sweep_list = [ 'Test Freq(MHz)','Temp(C)', 'Vramp Voltage' ]
g.update_filter_conditions( 'HB_LB', 'HB' )
vbat = 3.5
pin=3

yi = 0
hlimits = [ -33, -33, -33, -33, -33]
for yaxis in ( '2nd Harmonics Amplitude(dBm)', 
               '3rd Harmonics Amplitude(dBm)',
               '4th Harmonics Amplitude(dBm)',
               '5th Harmonics Amplitude(dBm)',
               '6th Harmonics Amplitude(dBm)',
             ):
    
    limit = hlimits[yi]
    yi = yi + 1

    xynames = [ 'Adj Pwr Out(dBm)' , yaxis ]

    for sweepname in sweep_list:

        if std_filter_cond( sweepname, xynames ) == 0 : continue
        g.sort_data_on.set(True)

        g.xgrid   = 0.25
        g.ygrid   = 5
        g.xlimits = [29,31]
        g.ylimits = [-60, 0]

        g.spec_limits = [[ limit , "Max Limit", 4, "red" ],
                         [ [[pwrh,g.ylimits[0]],[pwrh,g.ylimits[1]]] , "", 4, "yellow" ]]
        g.plot_graph_data( xynames, None, '#14 HB' + ' ' + yaxis + " vs POUT across " + sweepname)
  
g.update_filter_conditions( 'TestName', None )
#############################################################
###  24 HB - ORFS, Nominal Conditions (400KHz) - SWEEP POUT
#############################################################

sweep_list = [ 'Test Freq(MHz)', 'Pwr In(dBm)', 'Temp(C)', 'Vramp Voltage' ]
g.update_filter_conditions( 'Vbat(Volt)', 3.5 )
freq = [1785]
vbat = 3.5
pin  = 3.0
xynames = [ 'Adj Pwr Out(dBm)' , 'Sw Pwr 400KHz(dBm)' ]

for sweepname in sweep_list:
    
    if std_filter_cond( sweepname, xynames ) == 0 : continue

    g.xlimits = [29, 31]   
    g.ylimits = [-40, -10]
    g.xgrid   = 0.25
    g.ygrid   = 5
    g.spec_limits = [[ orfs_400k_h_max , "Max. limit, Extreme conditions", 4, "red" ],
                     [ orfs_400k_h_typ , "Typ. limit, Nominal conditions", 4, "blue" ],
                     [ [[pwrh,g.ylimits[0]],[pwrh, g.ylimits[1] ]] , "", 4, "yellow" ]]
    g.plot_graph_data( xynames, None, '#24 HB' + ' 400kHz ORFS vs POUT across  ' + sweepname)

#############################################################
###  24 HB - ORFS, Nominal Conditions (400KHz) - SWEEP VBAT
#############################################################

sweep_list = [ 'Vbat(Volt)', 'Temp(C)', 'Vramp Voltage' ]
freq = [1785]
pin  = 3.0
xynames = [ 'Vbat(Volt)' , 'Sw Pwr 400KHz(dBm)' ]

for sweepname in sweep_list:
    
    if std_filter_cond( sweepname, xynames ) == 0 : continue

    g.xlimits = [2.5, 3.9]   
    g.ylimits = [-40, -10]
    g.xgrid   = 0.1
    g.ygrid   = 5
    g.spec_limits = [[ orfs_400k_h_max , "Max. limit, Extreme conditions", 4, "red" ],
                     [ orfs_400k_h_typ , "Typ. limit, Nominal conditions", 4, "blue" ],
                     [ [[pwrh, g.ylimits[0]],[pwrh, g.ylimits[1] ]] , "", 4, "yellow" ]]
    g.plot_graph_data( xynames, None, '#24 HB' + ' 400kHz ORFS vs VBAT across  ' + sweepname)



g.loop()