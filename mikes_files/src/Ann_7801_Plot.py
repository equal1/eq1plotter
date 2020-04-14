#!/usr/bin/python

# Load the libraries
import sys, time
sys.path.append('/home/masker/bin/python')
from pygram_dev import *

# The main program
g = pygram()







limval = {}
                               # LB    HB
limval[ 'Pout.n'    ]       =  [33.6, 31.9]
limval[ 'Pout.1'    ]       =  [32.6, 30.9] 
limval[ 'Pout.2'    ]       =  [32.1, 30.4] 

limval[ 'Ptarget_Vh_Tnom' ] =  [33.1, 31.4]
limval[ 'Ptarget_Vl_Tnom' ] =  [32.3, 30.6]
limval[ 'Ptarget_Textrm'  ] =  [31.8, 30.1]

g.rated_power_values[ '@ Ptarget_Vh_Tnom' ] = limval[ 'Ptarget_Vh_Tnom' ]
g.rated_power_values[ '@ Ptarget_Vl_Tnom' ] = limval[ 'Ptarget_Vl_Tnom' ]
g.rated_power_values[ '@ Ptarget_Textrm'  ] = limval[ 'Ptarget_Textrm'  ]




g.add_all_logfiles_dialog()
g.get_savefile_directory_dialog()

#g.add_logfile( '/projects/sw/user/masker/pygram/ipfiles/AM7804_TA1_T_U_A0C_Dband_SN031p.log' )
#g.add_logfile( '/projects/sw/user/masker/pygram/ipfiles/AM7804_TA0C_AC_Pout_Harm_ORFS_Temp_SN028.log' )


#g.savedir  = '/projects/sw/user/masker/pygram/opfiles'





########################################################################################################




# Plot format options
g.plot_linewidth = 1
g.legend_location = [0.8, 0.0]
g.small_legend.set(True)
g.sort_data_on.set(True)
g.save_plot_count = 0


limval = {}
limval[ 'vramp_max' ] = 1.7

#                        LB    HB

# sweep_params_list is a list of the parameters that may be swept in the graphs. 
# Each of these parameters will normally be set to the nominal value.
sweep_params_list = [  'Vbat(Volt)', 'Pwr In(dBm)',  'Temp(C)' ,  'Freq(MHz)' ,  'Process' ]

# The nom_val dictionary is used to define the nominal values for each parameter.
# This value may be a two element list, where the first is the nominal value for LB and the second for HB.
nom_vals = {}
nom_vals[ 'Vbat(Volt)' ] = 3.5
nom_vals[ 'Pwr In(dBm)'] = 3
nom_vals[ 'Temp(C)'    ] = 25
nom_vals[ 'Freq(MHz)'  ] = [898, 1748]
nom_vals[ 'Process'    ] = 'TT'




# Table Driven Graphs
# Graphs are defined by using a graph_table list,  each row in the list defines a graph to be plotted. 

        #  The <graph_table> is a list containing one or more  <row_list>, where each <row_list> is a spearate graph to be plotted.
        #   <graph_table> = [ <row_list>... ]
        #
        # Each row is also a list, with a variable number of elements.
        #     <row_list>  =   [ <title_string> , <cond_filter>... , <measure_spec>... ]
        #   
        # The first element of the row is always the <title_string>. the table starts with the title. 
        #      The title string must have two %s format specifiers. 
        #      The first will have the band HB/LB inserted, the second will have the conditions string inserted.
        # 
        # The next fields in the row are the conditions filters <cond_filter>, each <cond_filter> defines whether a 
        #      parameter is to be swept or filtered or used to set the line colors. The <cond_filter> is a list containing 2 or 3 elements.
        #
        #    <cond_filter> = [ <column_name> , <option>, <value_def> ]
        #         <column_name> = Name of the parameter that will be filtered, swept, etc.
        #         <option>      = Defines what type of filtering or sweep operation is to be done.
        #               'C' (different lines will be drawn with different Colors)
        #               'L' (different lines will be drawn with different Linestyles)
        #               'A' (different lines will be drawn with the same linestyle and color)
        #               'N' will be filtered with the Nominal value
        #         <value_def> = The value of the parameter (Optional)
        #                If <value_def> is present it may be a single value or a list or a range.
        #               <value_def> =    <value>  |  [<value>...]  |  <value>..<value>
        # By default all conditions parameters are set to nominal, (as defined in the nom_val[] dict. 
        #
        # The next elements in the row list are the measurement spec limit definitions <measure_spec>. These are used to set the spec_limit lines on the graps
        # and to also report the measure data and whether the data passes or fails the spec limits  
        #    <measure_spec> = [ 'measure' ,  <meas_type>, <xval>, <ylimit> ]
        #  
        #    <meas_type>  =  'ymax_at_xval'    Measures the maximum y value at a given x 
        #                 =  'ymin_at_xval'    Measures the minimum y value at a given x
        #                 =  'ymax'            Measures the maximum y value anywhere on the x axis
        #                 =  'ymin'            Measures the minimum y value anywhere on the x axis
        #    <xval>       =   <spec_def>       Used to set the xaxis value at which the measurement will be made and the x value where the spec limit will be drawn on the graph.                   
        #                                         It may be a list of containing 2 x value points.
        #    <ylimit>     =  <spec_def>        Used to define the y value limit to determine if the data passes or fails and also defines the y value where the spec limit will be drawn on the graph.
        #    
        #    <spec_def>   =  <value>  |  [<value>...] | <dict_key_name>
        #    <value>      =  NUMBER | 'string'
        #    
        #    <dict_key_name>  =   This is used to reference an array or dictionary containing all the limit specifications.
        #
        #      limval[ <dict_key_name> ]  =   value   |    [value,value]    |    [ [value,value],[value,value] ]                
        #          value                            = single value, which is applied to all graphs
        #          [value,value]                    = two value list, where the first elemetn applies to LB and the secon for HB   [ LB,HB ]
        #          [ [value,value],[value,value] ]  = two element list of lists, where the first element specifies a range for LB and the second specifies a list for HB
        #             
        #    Examples:
        #         limval[ 'PNu1' ] =  9    
        #
        #                             LB    HB
        #         limval[ 'Pnhi' ] = [32.6, 29.9] 
        #                               
        #                                LB Range       HB Range
        #         limval[ 'PR1'  ] = [ [-20,  -15],   [-20, -15] ] 






if 0 :
    #############################################################
    ###  POUT VS VRAMP 
    #############################################################
    g.update_filter_conditions('TestName', 'Output Power & Efficiency')
   

    xynames = ['Vramp Voltage', 'Adj Pwr Out(dBm)']


    # Nokia spec
    graph_table = [
               # HB/LB                   vbat=3.5 pin=3 etc                                                                                                                  Type of measure              Limit
     ['#23,#68 %s Pout vs Vramp across Temp \n(@ %s)',                  ['Temp(C)','C','-15..60'],                     ['Pwr In(dBm)','F',-3 ], ['Freq(MHz)','L'], ['measure','ymin_at_xval','vramp_max','Pout.n']],
     ['#24,#69 %s Pout vs Vramp across Temp and Vbat \n(@ %s)',         ['Temp(C)','C','-15..60'], ['Vbat(Volt)','L'], ['Pwr In(dBm)','F',-3 ], ['Freq(MHz)','A'], ['measure','ymin_at_xval','vramp_max','Pout.1']],
     ['#25,#70 %s Pout vs Vramp across Temp Extreme and Vbat \n(@ %s)', ['Temp(C)','C', '60..85'], ['Vbat(Volt)','L'], ['Pwr In(dBm)','F',-3 ], ['Freq(MHz)','A'], ['measure','ymin_at_xval','vramp_max','Pout.2']], ]

    for fct in graph_table:

        for band in ['LB','HB' ]:

           g.update_filter_conditions('HB_LB', band)

           title = g.set_filter_conditions( fct, sweep_params_list, nom_vals )

           if title != None: 
              g.set_spec_limits( fct, limval )
              xyd= g.plot_graph_data(xynames, None, title)
#             measure_data( xyd, fct )



if 0 :
    #############################################################
    ######### POWER & PAE #######################################
    #############################################################
    g.update_filter_conditions('TestName', 'Output Power & Efficiency')

    xynames = ['Pout(dBm)', 'PAE(%)']

    limval[ 'Pnhi'      ] = [32.6, 29.9] 
    limval[ 'Pnmed'     ] = [29.1, 28.4] 
    limval[ 'Nhi'       ] = [36, 34] 
    limval[ 'Nmed'      ] = [24, 28] 


    graph_table = \
    [ ['#26,#71 %s PAE vs Pout across Temp \n(@ %s)',     ['Temp(C)','C','-15..60'],  ['Pwr In(dBm)','F',0 ], ['Freq(MHz)','L'], ['measure','ymin_at_xval','Pnhi', 'Nhi' ], ['measure','ymin_at_xval','Pnmed','Nmed']], ] 


    for fct in graph_table:
        for band in ['LB','HB' ]:
           g.update_filter_conditions('HB_LB', band)
           title = g.set_filter_conditions( fct, sweep_params_list, nom_vals )
           if title != None: 
              g.set_spec_limits( fct, limval )
              xyd= g.plot_graph_data(xynames, None, title)
#             measure_data( xyd, fct )




if 0 :
    #############################################################
    ######### IBAT vs POUT #######################################
    #############################################################
    g.update_filter_conditions('TestName', 'Output Power & Efficiency')
 
    xynames = ['Phase(degree)', 'Vbat_I(Amp)']

    limval[ 'Imax'] = [ 5.0, 5.0 ]
        
    graph_table = \
    [ ['#29,#74 %s Max Current vs VSWR & Phase\n(@ %s)',   ['@ Ptarget_Textrm','F',True], ['Vbat(Volt)','A'], ['Temp(C)','C','-30..85'],  ['Pwr In(dBm)','F',3 ], ['Freq(MHz)','L'], ['VSWR','A'], ['measure','ymax','','Imax']], ] 


    for fct in graph_table:
        for band in ['LB','HB' ]:
           g.update_filter_conditions('HB_LB', band)
           title = g.set_filter_conditions( fct, sweep_params_list, nom_vals )

           if title != None: 
              g.set_spec_limits( fct, limval )
              xyd= g.plot_graph_data(xynames, None, title)
#             measure_data( xyd, fct )



if 0 :
    #############################################################
    ######### Power Variation vs POUT ###########################
    #############################################################
    g.update_filter_conditions('TestName', 'Output Power & Efficiency')
    g.xlimits = [ -30, +35 ]
    g.ylimits = [ -15, +15 ]

  # Pwr Var Lim   Tnom   HB   LB         Pwr Var Lim Textr    HB   LB            # Pwr  range limits LB min..max    HB min..max       
    limval[ 'PNu1' ] =  9            ;   limval[ 'PEu1' ] =  10            ;     limval[ 'PR1' ] = [ [-20,  -15],   [-20, -15] ]   ;  
    limval[ 'PNd1' ] = -9            ;   limval[ 'PEd1' ] = -10            ;                                                          
    limval[ 'PNu2' ] = 4.5           ;   limval[ 'PEu2' ] = 5.5            ;     limval[ 'PR2' ] = [ [5.3, 11.3],   [0.4, 2.4] ]   ;  
    limval[ 'PNd2' ] = -4.5          ;   limval[ 'PEd2' ] = -5.5           ;                                                          
    limval[ 'PNu3' ] = [2.5 ,  3.5]  ;   limval[ 'PEu3' ] = [3.5 ,  4.5]   ;     limval[ 'PR3' ] = [ [13.3, 31.3],  [4.4, 12.4] ]  ;  
    limval[ 'PNd3' ] = [-2.5, -3.5]  ;   limval[ 'PEd3' ] = [-4.5, -4.5]   ;                                                          
    limval[ 'PNu4' ] = [1.5 ,  2.5]  ;   limval[ 'PEu4' ] = [2.0 ,  3.5]   ;     limval[ 'PR4' ] = [ [32.7, 32.9],  [14.4,28.4] ]  ;  
    limval[ 'PNd4' ] = [-1.0, -2.5]  ;   limval[ 'PEd4' ] = [-1.5, -3.5]   ;                                                          
    limval[ 'PNu5' ] = [None,  1.5]  ;   limval[ 'PEu5' ] = [None,  2.0]   ;     limval[ 'PR5' ] = [ [None,None ],  [30.8,31.0] ]  ;  
    limval[ 'PNd5' ] = [None, -1.0]  ;   limval[ 'PEd5' ] = [None, -1.5]   ;                                                          

    xynames = ['Ref Pout(dBm)', 'Pwr Variation(dB)' ]

    graph_table =  [ 
      ['#50,#91 %s Power Variation vs Pout across Tnom 25C..60C\n(@ %s)', 
               ['Temp(C)','C','25..60'],  ['Pwr In(dBm)','L'], ['Freq(MHz)','A'],  
                           ['measure','ymax_at_xval', 'PR1' ,'PNu1'], 
                           ['measure','ymin_at_xval', 'PR1' ,'PNd1'], 
                           ['measure','ymax_at_xval', 'PR2' ,'PNu2'], 
                           ['measure','ymin_at_xval', 'PR2' ,'PNd2'], 
                           ['measure','ymax_at_xval', 'PR3' ,'PNu3'], 
                           ['measure','ymin_at_xval', 'PR3' ,'PNd3'], 
                           ['measure','ymax_at_xval', 'PR4' ,'PNu4'], 
                           ['measure','ymin_at_xval', 'PR4' ,'PNd4'], 
                           ['measure','ymax_at_xval', 'PR5' ,'PNu5'], 
                           ['measure','ymin_at_xval', 'PR5' ,'PNd5'], ],

      ['#50,#91 %s Power Variation vs Pout across Textreme -15C..85C\n(@ %s)', 
               ['Temp(C)','C','-15..85'],  ['Pwr In(dBm)','L'], ['Freq(MHz)','A'], 
                           ['measure','ymax_at_xval', 'PR1' ,'PEu1'], 
                           ['measure','ymin_at_xval', 'PR1' ,'PEd1'], 
                           ['measure','ymax_at_xval', 'PR2' ,'PEu2'], 
                           ['measure','ymin_at_xval', 'PR2' ,'PEd2'], 
                           ['measure','ymax_at_xval', 'PR3' ,'PEu3'], 
                           ['measure','ymin_at_xval', 'PR3' ,'PEd3'], 
                           ['measure','ymax_at_xval', 'PR4' ,'PEu4'], 
                           ['measure','ymin_at_xval', 'PR4' ,'PEd4'], 
                           ['measure','ymax_at_xval', 'PR5' ,'PEu5'], 
                           ['measure','ymin_at_xval', 'PR5' ,'PEd5'], ],
                               ] 



    for fct in graph_table:
        for band in ['LB','HB' ]:
#       for band in ['LB', ]:
           g.update_filter_conditions('HB_LB', band)
           title = g.set_filter_conditions( fct, sweep_params_list, nom_vals )

           if title != None: 
              g.set_spec_limits( fct, limval )
              xyd= g.plot_graph_data(xynames, None, title)
#             measure_data( xyd, fct )





if 0 :
    #############################################################
    ######### AM-AM vs POUT #######################################
    #############################################################
    g.update_filter_conditions('TestName', 'Output Power & Efficiency')
 
    xynames = ['Phase(degree)', 'Vbat_I(Amp)']

    limval[ 'Imax'] = [ 5.0, 5.0 ]
        
    graph_table = \
    [ ['#29,#74 %s Max Current vs VSWR & Phase\n(@ %s)',   ['@ Ptarget_Textrm','F',True], ['Vbat(Volt)','A'], ['Temp(C)','C','-30..85'],  ['Pwr In(dBm)','F',3 ], ['Freq(MHz)','L'], ['VSWR','A'], ['measure','ymax','','Imax']], ] 


    for fct in graph_table:
        for band in ['LB','HB' ]:
           g.update_filter_conditions('HB_LB', band)
           title = g.set_filter_conditions( fct, sweep_params_list, nom_vals )

           if title != None: 
              g.set_spec_limits( fct, limval )
              xyd= g.plot_graph_data(xynames, None, title)
#             measure_data( xyd, fct )

if 0 :
    ##############################################################
    ########## 2ND HARMONICS VS. FREQUENCY   #############
    ##############################################################

    g.update_filter_conditions('TestName', 'Harmonics (2nd VSA)')

    xynames = ['Freq(MHz)', '2nd Harmonics Amplitude(dBm)']
    
    #Harmonics limits    [ LB, HB]
    limval[ 'HarmonicsLimit' ]=[-33,-33,]
    
    # set grid spacing
    g.xgrid = 5
    g.ygrid = 1

    # set x and y scales
    g.xlimits = []
    g.ylimits = [-60, -30]

    # set legend location
    g.legend_location = [1.0, .05]

    # graph_table [ title, condition set, limits]
    graph_table = [
     ['%s 2nd Harmonics (dBm) vs Frequency (MHz)\n(@ %s)',
       ['@ Ptarget_Vl_Tnom', 'F',True], ['Vbat(Volt)', 'N'], ['Temp(C)','N'], ['Pwr In(dBm)', 'F', '-3..3'], ['Freq(MHz)', 'A'],
        ['measure', 'ymax','','HarmonicsLimit']]
                  ]

    for fct in graph_table:
        for band in ['LB', 'HB']:
           g.update_filter_conditions('HB_LB', band)
           title = g.set_filter_conditions(fct, sweep_params_list, nom_vals )

           if title != None:
              g.set_spec_limits(fct, limval)
              xdy = g.plot_graph_data(xynames, None, title)
#             measure_data(xyd, fct)

if 0 :
    ##############################################################
    ########## 3RD HARMONICS VS. FREQUENCY   #############
    ##############################################################

    g.update_filter_conditions('TestName', 'Harmonics (3rd VSA)')

    xynames = ['Freq(MHz)', '3rd Harmonics Amplitude(dBm)']
    
    #Harmonics limits    [ LB, HB]
    limval[ 'HarmonicsLimit' ]=[-33,-33,]
    
    # set grid spacing
    g.xgrid = 5
    g.ygrid = 1

    # set x and y scales
    g.xlimits = []
    g.ylimits = [-60, -30]

    # set legend location
    g.legend_location = [1.0, .05]

    # graph_table [ title, condition set, limits]
    graph_table = [
     ['%s 3rd Harmonics (dBm) vs Frequency (MHz)\n(@ %s)',
       ['@ Ptarget_Vl_Tnom', 'F',True], ['Vbat(Volt)', 'N'], ['Temp(C)','N'], ['Pwr In(dBm)', 'F', '-3..3'], ['Freq(MHz)', 'A'],
        ['measure', 'ymax','','HarmonicsLimit']]
                  ]

    for fct in graph_table:
        for band in ['LB', 'HB']:
           g.update_filter_conditions('HB_LB', band)
           title = g.set_filter_conditions(fct, sweep_params_list, nom_vals )

           if title != None:
              g.set_spec_limits(fct, limval)
              xdy = g.plot_graph_data(xynames, None, title)
#             measure_data(xyd, fct)

if 1 :
    ##############################################################
    ########## 2ND TO 13TH HARMONICS VS. FREQUENCY   #############
    ##############################################################

    g.update_filter_conditions('TestName', ['Harmonics (2nd VSA)','Harmonics (3rd VSA)', 'Harmonics (4th VSA)', 'Harmonics (5th VSA)', 'Harmonics (6th VSA)'])

    xynames = ['Freq(MHz)', '2nd Harmonics Amplitude(dBm)','3rd Harmonics Amplitude(dBm)', '4th Harmonics Amplitude(dBm)',
               '5th Harmonics Amplitude(dBm)','6th Harmonics Amplitude(dBm)' ]
    
    #Harmonics limits    [ LB, HB]
    limval[ 'HarmonicsLimit' ]=[-33,-33,]
    
    # set grid spacing
    g.xgrid = 5
    g.ygrid = 1

    # set x and y scales
    g.xlimits = []
    g.ylimits = [-65, -30]

    # set legend location
    g.legend_location = [1.0, .05]

    # graph_table [ title, condition set, limits]
    graph_table = [
     ['%s 3rd Harmonics (dBm) vs Frequency (MHz)\n(@ %s)',
       ['@ Ptarget_Vl_Tnom', 'F',True], ['Vbat(Volt)', 'N'], ['Temp(C)','A'], ['Pwr In(dBm)', 'F', '-3..3'], ['Freq(MHz)', 'A'],
        ['measure', 'ymax','','HarmonicsLimit']]
                  ]

    for fct in graph_table:
        for band in ['LB', 'HB']:
           g.update_filter_conditions('HB_LB', band)
           title = g.set_filter_conditions(fct, sweep_params_list, nom_vals )

           if title != None:
              g.set_spec_limits(fct, limval)
              xdy = g.plot_graph_data(xynames, None, title)
#             measure_data(xyd, fct)


##################################################################     
g.loop()    # loop forever, and wait for input from the user
