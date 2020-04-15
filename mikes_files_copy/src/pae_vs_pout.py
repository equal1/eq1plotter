#!/usr/local/bin/python

# Load the pygram libraries
import sys
sys.path.append(r'/projects/sw/release')
sys.path.append(r'N:\sw\release')
from pygram_dev import *


# Initialize pygram
g = pygram()


# load a logfile
g.add_logfile(  r'N:/sw/release/AM8901_TB0C_T_U_CB_GSM_SN002_ATR2.log')

#### Or prompt the user for the logfile and where to save the plots
#g.add_all_logfiles_dialog()
#g.get_savefile_directory_dialog()


# print out info about the logfile contents
g.print_column_list()  
g.print_values_list()   
 

# plot out the PAE vs POUT

g.update_filter_conditions('HB_LB', 'HB' )
g.update_filter_conditions('Vbat(Volt)', 3.5 )

# set the axes limits
g.xlimits = [ 24, 35 ]
g.ylimits = [ 20, 50 ]

# set the color of the
g.color_series.set('Freq(MHz)')

# set the axes plot for  PAE vs Pout
#             X           Y
xynames = ['Pout(dBm)', 'PAE(%)'    ]

#                 x y axes,  None,   Title and name of plot file
g.plot_graph_data( xynames,  None,   'PAE vs Pout @ VBAT=3.5v'  )


g.loop()   # pygram idle loop, (it would exit straight away without this)



