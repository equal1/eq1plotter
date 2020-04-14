#!/usr/bin/python

# Load the libraries 
import sys, time
sys.path.append( '/home/masker/bin/python' )
from pygram_dev import *


# The main program

g = pygram()

g.add_all_logfiles_dialog()
g.get_savefile_directory_dialog()

#g.add_logfile( '05222009_BOM_G_SN011.log' )
#g.add_logfile( '05222009_BOM_G_SN012.log' )
#g.add_logfile( '05222009_BOM_G_SN002.log' )
#g.add_logfile( 'AOB_BOM_G_SN016.log' )
#g.add_logfile( 'AOB_BOM_G_SN015_ORFS.log' )


##################################################################
##################################################################
##################################################################
##################################################################


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
            g.color_series.set(  sweepname  )
            g.line_series.set( 'Serial Number'  )
        else:
            g.color_series.set( sweepname  )
            g.line_series.set(  ''  )



        if len( g.values_dict[ 'Serial Number' ]) * len( g.values_dict[ sweepname ]) > 16 : g.small_legend.set( True   )
        else:                                                                               g.small_legend.set( False  )


        return 1

    else:
 
        return 0

###################################################################################












pael = 54        # min pae at rated power lb
paeh = 44        # min pae at rated power hb

pwrl = 34.2      # rated power for lb
pwrh = 32        # rated power for hb

vramph = 1.3     # vramp voltage for rated power for hb
vrampl = 1.3     # vramp voltage for rated power for lb




#   Set the standard conditions for this test
vbat = 3.5
pin  = 3.0
temp = 25
process  = 'TT'
freq = [ 880 , 1850 ]  

vbat_sweep_list = [ 2.7, 3.0 , 3.5, 4.0, 4.5 ]



# Plot format options
g.plot_linewidth = 1
g.legend_location     = [ 0.80, 0.0   ] 
#g.small_legend.set( True )
g.sort_data_on.set(True)
g.save_plot_count = 0


sweep_list = [ 'Test Freq(MHz)' , 'Vbat(Volt)', 'Pwr In(dBm)', 'Temp(C)', 'Process', 'Vramp Voltage' ]




if 1:
    #############################################################
    ###  POUT VS VRAMP
    #############################################################

    xynames = [ 'Vramp Voltage' , 'Adj Pwr Out(dBm)'  ]

    for sweepname in sweep_list:
        if std_filter_cond( sweepname, xynames ) == 0 : continue
        
        g.update_filter_conditions( 'TestName', 'Output Power & Efficiency' )
        
        g.xgrid   = 0.05
        g.xlimits = [0.9, 1.7] 
        
        g.update_filter_conditions( 'HB_LB'    , 'LB' )
        
        g.ylimits = [30 , 36  ] 
        g.spec_limits = [[ 34.2 , "Rated Power", 4, "red" ]]
        g.plot_graph_data( xynames, None, 'LB' + ' Pout vs VRAMP across ' + sweepname)
        
        g.update_filter_conditions( 'HB_LB'    , 'HB' )
        
        g.ylimits = [27 , 34  ] 
        g.spec_limits = [[ 32 , "Rated Power", 4, "red" ]]
        g.plot_graph_data( xynames, None, 'HB' + ' Pout vs VRAMP across ' + sweepname)
            
        g.update_filter_conditions( 'TestName', None )
    
    
    
    
if 1:
    #############################################################
    ######### POWER & PAE #######################################
    #############################################################
    
    xynames = [ 'Adj Pwr Out(dBm)' , 'PAE(%)' ]
    for sweepname in sweep_list:
        if std_filter_cond( sweepname, xynames ) == 0 : continue
    
        g.xgrid   = 0.5
        
        g.update_filter_conditions( 'HB_LB'    , 'LB' )
        
        
        g.xlimits = [30 , 36]
        g.ylimits = [35 , 60] 
        g.spec_limits = [[  pael , "Min PAE Spec", 4, "red" ],
                         [ [[pwrl,pael+5],[pwrl,pael-5  ]] , "", 4, "yellow" ]]
        g.plot_graph_data( xynames, None, 'LB' + ' PAE vs POUT across ' + sweepname)
        
        g.update_filter_conditions( 'HB_LB'    , 'HB' )
        
        g.xlimits = [27 , 34]
        g.ylimits = [25 , 50] 
        g.spec_limits = [[ paeh, "Min PAE Spec", 4, "red" ],
                         [ [[pwrh,paeh+5],[pwrh, paeh-5 ]] , "", 4, "yellow" ]]
        g.plot_graph_data( xynames, None, 'HB' + ' PAE vs POUT across ' + sweepname)
        
        
        # Close look at two freq
        
#       g.update_filter_conditions( 'HB_LB'             , None )
#       g.update_filter_conditions( 'Test Freq(MHz)'    , freq )
#       g.line_series.set(  'Test Freq(MHz)'  )
#       g.xlimits = [27 , 36]
#       g.ylimits = [25 , 60] 
#       g.spec_limits = [[ [[pwrh,  paeh],[pwrh+2,paeh]] , "HB Min PAE Spec", 4, "red" ],
#                        [ [[pwrh,paeh+5],[pwrh, paeh-5 ]] , "", 4, "red" ],
#                        [ [[pwrl,  pael],[pwrl+2,pael]] , "LB Min PAE Spec", 4, "red" ],
#                        [ [[pwrl,pael+5],[pwrl,pael-5  ]] , "", 4, "red" ]]
#       g.plot_graph_data( xynames, None, 'PAE vs POUT @ Freq=%s'%freq + ' across ' + sweepname)
#       g.update_filter_conditions( 'Test Freq(MHz)'    , None )
            
            
    
if 1:
    #############################################################
    ######### IBAT vs POUT #######################################
    #############################################################
    
    xynames = [ 'Adj Pwr Out(dBm)' , 'Vbat_I(Amp)' ]
    for sweepname in sweep_list:
        if std_filter_cond( sweepname, xynames ) == 0 : continue
    
        g.xgrid   = 2
        
        g.update_filter_conditions( 'HB_LB'    , 'LB' )
        
        
        g.xlimits = [-10 , 36]
        g.ylimits = [-0.1 , 2 ] 
        g.spec_limits = [ [ [[5,0]     ,[ 5,  0.5 ]] ,         "", 4, "red" ],
                          [ [[pwrl,0.5],[pwrl,2.0 ]] , "", 4, "red" ] ]
        g.plot_graph_data( xynames, None, 'LB' + ' IBAT vs POUT across ' + sweepname)
        
        g.update_filter_conditions( 'HB_LB'    , 'HB' )
        
        g.xlimits = [-10 , 34]
        g.ylimits = [-0.1 , 2 ] 

        g.spec_limits = [ [ [[0,0],[0,0.5 ]] ,         "", 4, "red" ],
                          [ [[pwrh,0.5],[pwrh,2.0 ]] , "", 4, "red" ] ]
        g.plot_graph_data( xynames, None, 'HB' + ' IBAT vs POUT across ' + sweepname)
        
        
        # Close look at two freq
        
#       g.update_filter_conditions( 'HB_LB'             , None )
#       g.update_filter_conditions( 'Test Freq(MHz)'    , freq )
#       g.line_series.set(  'Test Freq(MHz)'  )
#       g.xlimits = [27 , 36]
#       g.ylimits = [25 , 60] 
#       g.spec_limits = [[ [[pwrh,  paeh],[pwrh+2,paeh]] , "HB Min PAE Spec", 4, "red" ],
#                        [ [[pwrh,paeh+5],[pwrh, paeh-5 ]] , "", 4, "red" ],
#                        [ [[pwrl,  pael],[pwrl+2,pael]] , "LB Min PAE Spec", 4, "red" ],
#                        [ [[pwrl,pael+5],[pwrl,pael-5  ]] , "", 4, "red" ]]
#       g.plot_graph_data( xynames, None, 'PAE vs POUT @ Freq=%s'%freq + ' across ' + sweepname)
#       g.update_filter_conditions( 'Test Freq(MHz)'    , None )
            
            
    
    
if 1:
    #############################################################
    ######### POUT vs Freq ######################################
    #############################################################
    
    xynames = [ 'Test Freq(MHz)', 'Adj Pwr Out(dBm)' ]

    for sweepname in sweep_list:
        if sweepname == 'Vramp Voltage' : continue
        if std_filter_cond( sweepname, xynames ) == 0 : continue

    
        g.xgrid   = 50
        g.ygrid   = 1
        
        g.update_filter_conditions( 'HB_LB'    , 'LB' )
        
        
        g.update_filter_conditions( 'Vramp Voltage'    , str(vrampl) )
        g.xlimits = []
        g.ylimits = [32, 36]
        g.spec_limits = [ pwrl , 'Rated Power', 4, 'yellow' ]
        g.plot_graph_data( xynames, None, 'LB' + ' Pout vs Freq @ Vramp=' + str(vrampl) + 'v across ' + sweepname)
        
    
        g.update_filter_conditions( 'HB_LB'    , 'HB' )
        
        
        g.update_filter_conditions( 'Vramp Voltage'    , str(vramph) )
        g.xlimits = []
        g.ylimits = [30, 34]
        g.spec_limits = [ pwrh , 'Rated Power', 4, 'yellow' ]
        g.plot_graph_data( xynames, None, 'HB' + ' Pout vs Freq @ Vramp=' + str(vramph) + 'v across ' + sweepname)
        
    

if 1:
    #############################################################
    ######### PAE vs Freq #######################################
    #############################################################
    
    xynames = [ 'Test Freq(MHz)', 'PAE(%)' ]

    for sweepname in sweep_list:
        if sweepname == 'Vramp Voltage' : continue
        if std_filter_cond( sweepname, xynames ) == 0 : continue
    
        g.xgrid   = 50
        g.ygrid   = 1
        
        g.update_filter_conditions( 'HB_LB'    , 'LB' )
        
        
        g.update_filter_conditions( 'Vramp Voltage'    , str(vrampl) )
        g.xlimits = []
        g.ylimits = [40, 60]
        g.spec_limits = [ pael , 'Min PAE', 4, 'yellow' ]
        g.plot_graph_data( xynames, None, 'LB' + ' PAE vs Freq @ Vramp=' + str(vrampl) + 'v across ' + sweepname)
        

        g.update_filter_conditions( 'HB_LB'    , 'HB' )
        
        
        g.update_filter_conditions( 'Vramp Voltage'    , vramph )
        g.xlimits = []
        g.ylimits = [30, 50]
        g.spec_limits = [ paeh , 'Min PAE', 4, 'yellow' ]
        g.plot_graph_data( xynames, None, 'HB' + ' PAE vs Freq @ Vramp=' + str(vramph) + 'v across ' + sweepname)
        g.update_filter_conditions( 'Vramp Voltage'    , None )
        
        g.update_filter_conditions( 'TestName', None )
    
    
    
if 1:    
    #############################################################
    ######### HARMONICS #########################################
    #############################################################
    
    yi = 0
    hlimits = [ -10, -15, -15, -20, -20 ]


    for yaxis in ( '2nd Harmonics Amplitude(dBm)', 
                   '3rd Harmonics Amplitude(dBm)',
                   '4th Harmonics Amplitude(dBm)',
#                  '5th Harmonics Amplitude(dBm)',
#                  '6th Harmonics Amplitude(dBm)',
                 ): 


        limit = hlimits[yi]
        yi = yi + 1

        xynames = [ 'Adj Pwr Out(dBm)' , yaxis ]

        for sweepname in sweep_list:
            if std_filter_cond( sweepname, xynames ) == 0 : continue

            
            g.sort_data_on.set(True)

            ######### Harmonic vs POUT #############################


            g.xgrid   = 1
            g.ygrid   = 2


            g.update_filter_conditions( 'HB_LB'    , 'LB' )

            g.spec_limits = [[ limit , "Max Limit", 4, "red" ],
                             [ [[pwrl,limit-15],[pwrl,limit+15]] , "", 4, "yellow" ]]

            g.xlimits = [29, 37]
            g.ylimits = [-40, 0]
            g.plot_graph_data( xynames, None, 'LB' + ' ' + yaxis + " vs POUT across " + sweepname)
    

            g.update_filter_conditions( 'HB_LB'    , 'HB' )

            g.spec_limits = [[ limit , "Max Limit", 4, "red" ],
                             [ [[pwrh,limit-15],[pwrh,limit+15]] , "", 4, "yellow" ]]

            g.xlimits = [26, 35]
            g.ylimits = [-40, 0]
            g.plot_graph_data( xynames, None, 'HB' + ' ' + yaxis + " vs POUT across " + sweepname)
    

sweep_list = [ 'Test Freq(MHz)' , 'Vbat(Volt)', 'Pwr In(dBm)', 'Temp(C)', 'Process', 'Vramp Voltage' ]

if 1:
    #############################################################
    ######### FORWARD ISOLATION #################################
    #############################################################
    
    xynames = [ 'Test Freq(MHz)', 'Fwd Isol1 Amplitude(dBm)' ]

    for sweepname in sweep_list:
        if sweepname == 'Vramp Voltage' : continue
        if std_filter_cond( sweepname, xynames ) == 0 : continue

        g.xgrid   = 20
        g.ygrid   = 1
        
        # Fwd Iso 1
        g.update_filter_conditions( 'Vramp Voltage'    , 1.4 )
        g.xlimits = []
        g.ylimits = [-50, -10]

        g.update_filter_conditions( 'HB_LB'    , 'LB' )
        g.spec_limits = [ -30 , "Max Limit", 4, "red" ]
        g.plot_graph_data( xynames, None,  "LB Fwd Iso 1 (TXEN=0 VRAMP=1.4v) vs Freq across " + sweepname)
        g.update_filter_conditions( 'HB_LB'    , 'HB' )
        g.spec_limits = [ -30 , "Max Limit", 4, "red" ]
        g.plot_graph_data( xynames, None,  "HB Fwd Iso 1 (TXEN=0 VRAMP=1.4v) vs Freq across " + sweepname)


        # Fwd Iso 2
        g.update_filter_conditions( 'Vramp Voltage'    , 0.1 )

        g.update_filter_conditions( 'HB_LB'    , 'LB' )
        g.spec_limits = [ -30 , "Max Limit", 4, "red" ]
        g.plot_graph_data( xynames, None,  "LB Fwd Iso 2 (TXEN=1 VRAMP=0.1v) vs Freq across " + sweepname)
        g.update_filter_conditions( 'HB_LB'    , 'HB' )
        g.spec_limits = [ -30 , "Max Limit", 4, "red" ]
        g.plot_graph_data( xynames, None,  "HB Fwd Iso 2 (TXEN=1 VRAMP=0.1v) vs Freq across " + sweepname)

        g.update_filter_conditions( 'Vramp Voltage'    , None )


freq =  824 

if 1:
    #############################################################
    ######### CROSSBAND ISOLATION ###############################
    #############################################################

    xynames = [ 'Adj Pwr Out(dBm)' , 'Crossband Isolation Amplitude(dBm)' ]

    for sweepname in sweep_list:
        if sweepname == 'Vramp Voltage' : continue
        if std_filter_cond( sweepname, xynames ) == 0 : continue

        g.xgrid   = 1
        g.ygrid   = 1

        limit = -20

        g.update_filter_conditions( 'HB_LB'    , 'LB' )

        g.ylimits = [-50, -10]

        g.spec_limits = [[ limit , "Max Limit", 4, "red" ],
                         [ [[pwrl,limit],[pwrl, limit-20 ]] , "", 4, "yellow" ]]

        g.plot_graph_data( xynames, None, "Crossband Isolation vs POUT across " + sweepname)
        



freq = [ 880 , 1850 ]  

if 1:
    #############################################################
    ######### ORFS ##############################################
    #############################################################
    
    # 400kHz ORFS

    xynames = [ 'Vramp Voltage' , 'Sw Pwr 400KHz(dBm)' ]

    for sweepname in sweep_list:
        if std_filter_cond( sweepname, xynames ) == 0 : continue

        g.xlimits = [ 0.5, 1.6 ]
        g.ylimits = [ -40, -10 ]
        g.xgrid = 0.1


        g.update_filter_conditions( 'HB_LB'    , 'LB' )
        g.spec_limits =  [[ -24 , "Maximum Datasheet Limit", 4, "red" ],
                          [[[pwrl,-10],[pwrl,-40]] , "", 4, "yellow" ],
                          [ -27 , "Margin Limit",    4, "blue" ],
                          [ -19 , "3GPP Limit",    4, "brown" ]]
        g.plot_graph_data( xynames, None, 'LB 400kHz ORFS vs Vramp across ' + sweepname)


        g.update_filter_conditions( 'HB_LB'    , 'HB' )
        g.spec_limits =  [[ -24 , "Maximum Datasheet Limit", 4, "red" ],
                          [ -27 , "Margin Limit",    4, "blue" ],
                          [ -20 , "3GPP Limit",    4, "brown" ]]
        g.plot_graph_data( xynames, None, 'HB 400kHz ORFS vs Vramp across ' + sweepname)


#   xynames = [ 'PSA Pwr Out(dBm)' , 'Sw Pwr 400KHz(dBm)' ]
    xynames = [ 'Adj Pwr Out(dBm)' , 'Sw Pwr 400KHz(dBm)' ]
    g.xlimits = [ 20, 38 ]
    g.xgrid = 1

    for sweepname in sweep_list:
        if sweepname == 'Vramp Voltage' : continue
        if std_filter_cond( sweepname, xynames ) == 0 : continue

        g.update_filter_conditions( 'HB_LB'    , 'LB' )
        g.spec_limits =  [[ -24 , "Maximum Datasheet Limit", 4, "red" ],
                          [[[pwrl,-10],[pwrl,-40]] , "", 4, "yellow" ],
                          [ -27 , "Margin Limit",    4, "blue" ],
                       [[[ 31,-19], [40,-19]] , "",           3, "brown" ],
                       [[[ 31,-19], [31,-21]] , "",           3, "brown" ],    # vert
                       [[[ 29,-21], [31,-21]] , "3GPP Limit", 3, "brown" ],
                       [[[ 29,-23], [29,-21]] , "",           3, "brown" ],    # vert
                       [[[-20,-23], [29,-23]] , "",           3, "brown" ] ]

        g.plot_graph_data( xynames, None, 'LB 400kHz ORFS vs POUT across ' + sweepname)


        g.update_filter_conditions( 'HB_LB'    , 'HB' )
        g.spec_limits =  [[ -24 , "Maximum Datasheet Limit", 4, "red" ],
                          [[[pwrh,-10],[pwrh,-40]] , "", 4, "yellow" ],
                          [ -27 , "Margin Limit",    4, "blue" ],
                       [[[ 30,-20], [40,-20]] , "",           3, "brown" ],
                       [[[ 30,-20], [30,-22]] , "",           3, "brown" ],    # vert
                       [[[ 28,-22], [30,-22]] , "3GPP Limit", 3, "brown" ],
                       [[[ 28,-23], [28,-22]] , "",           3, "brown" ],    # vert
                       [[[-20,-23], [28,-23]] , "",           3, "brown" ] ]

        g.plot_graph_data( xynames, None, 'HB 400kHz ORFS vs POUT across ' + sweepname)


    # ORFS vs VBAT
    xynames = [ 'Vbat(Volt)' , 'Sw Pwr 400KHz(dBm)' ]
    g.xlimits = [ 2, 4.5 ]
    g.xgrid = 0.5

    for sweepname in sweep_list:
        if sweepname == 'Vramp Voltage' : continue
        if std_filter_cond( sweepname, xynames ) == 0 : continue

        g.update_filter_conditions( 'Vbat(Volt)'    , None )
        g.update_filter_conditions( 'Vramp Voltage' , vrampl )
        

        g.update_filter_conditions( 'HB_LB'    , 'LB' )
        g.spec_limits =  [[ -24 , "Maximum Datasheet Limit", 4, "red" ],
                          [ -27 , "Margin Limit",    4, "blue" ],
                          [ -19 , "3GPP Limit",    4, "brown" ]]
        g.plot_graph_data( xynames, None, 'LB 400kHz ORFS vs Vbat across ' + sweepname)


        g.update_filter_conditions( 'HB_LB'    , 'HB' )
        g.update_filter_conditions( 'Vramp Voltage' , vramph )
        g.spec_limits =  [[ -24 , "Maximum Datasheet Limit", 4, "red" ],
                          [ -27 , "Margin Limit",    4, "blue" ],
                          [ -20 , "3GPP Limit",    4, "brown" ]]
        g.plot_graph_data( xynames, None, 'HB 400kHz ORFS vs Vbat across ' + sweepname)

        g.update_filter_conditions( 'Vbat(Volt)'    , vbat )
        g.update_filter_conditions( 'Vramp Voltage' , None )




    # 600kHz ORFS

#   xynames = [ 'PSA Pwr Out(dBm)' , 'Sw Pwr 600KHz(dBm)' ]
    xynames = [ 'Adj Pwr Out(dBm)' , 'Sw Pwr 600KHz(dBm)' ]
    g.xlimits = [ 20, 38 ]
    g.xgrid = 1

    for sweepname in sweep_list:
        if sweepname == 'Vramp Voltage' : continue
        if std_filter_cond( sweepname, xynames ) == 0 : continue

        g.update_filter_conditions( 'HB_LB'    , 'LB' )
        g.spec_limits = [[[[ 31,-21], [40,-21]] , "",           3, "brown" ],
                          [[[pwrl,-10],[pwrl,-40]] , "", 4, "yellow" ],
                         [[[ 31,-21], [31,-23]] , "",           3, "brown" ],    # vert
                         [[[ 29,-23], [31,-23]] , "3GPP Limit", 3, "brown" ],
                         [[[ 29,-25], [29,-23]] , "",           3, "brown" ],    # vert
                         [[[ 27,-25], [29,-25]] , "",           3, "brown" ],
                         [[[ 27,-25], [27,-26]] , "",           3, "brown" ],    # vert
                         [[[-20,-26], [27,-26]] , "",           3, "brown" ] ]

        g.plot_graph_data( xynames, None, 'LB 600kHz ORFS vs POUT across ' + sweepname)

        g.update_filter_conditions( 'HB_LB'    , 'HB' )
        g.spec_limits = [ [[[ 30,-22], [40,-22]] , "",           3, "brown" ],
                          [[[pwrh,-10],[pwrh,-40]] , "", 4, "yellow" ],
                       [[[ 30,-22], [30,-24]] , "",           3, "brown" ],    # vert
                       [[[ 28,-24], [30,-24]] , "3GPP Limit", 3, "brown" ],
                       [[[ 28,-25], [28,-24]] , "",           3, "brown" ],    # vert
                       [[[ 26,-25], [28,-25]] , "",           3, "brown" ],
                       [[[ 26,-25], [26,-26]] , "",           3, "brown" ],    # vert
                       [[[-20,-26], [26,-26]] , "",           3, "brown" ] ]
        g.plot_graph_data( xynames, None, 'HB 600kHz ORFS vs POUT across ' + sweepname)




##################################################################
##################################################################
##################################################################


g.loop()   # loop forever, and wait for input from the user
