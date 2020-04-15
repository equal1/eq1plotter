#!/usr/bin/python

###################################################################
###################################################################
#####   PYGRAM  SCRIPT  ###########################################
###################################################################
###################################################################

# Load the libraries 
import sys

# Tell python where to look for the matplotlib libraries as these are not part of the
#  standard python distribution
sys.path.append( '/home/masker/bin/python' )
from pygram_dev import *

# Initialize pygram
g = pygram()

# Read the logfiles
g.add_all_logfiles_dialog()
g.get_savefile_directory_dialog()

g.print_column_list()  
g.print_values_list()   
 
###################################################################
###################################################################
###################################################################
###################################################################

# change below here....






######################################################################
def runplots( band ):

  g.update_filter_conditions( 'HB_LB', band )
  g.update_filter_conditions('Vramp Voltage', None )


  # plot out the PSA

  g.update_filter_conditions('Vbat(Volt)', 3.6 )
  g.xlimit = [ 0, 1.6 ]
  g.ylimit = [ 0, 40  ]
  g.plot_limits = []
  g.color_series.set('')
  xynames = ['Vramp Voltage', 'PSA Pwr Out(dBm)'     ]
  g.plot_graph_data( xynames,  None, band + ' Pout vs VRAMP @ VBAT=3.6v'  )

  g.update_filter_conditions('Vbat(Volt)', None)


  g.update_filter_conditions('Vramp Voltage', [0.8,0.9,1.0,1.1,1.2,1.3,1.4] )
  g.ylimit = [ -50, -10 ]


  g.plot_limits  = [[ -24 , "Datasheet Limit", 4, "red" ],
                      [ -27 , "Margin Limit", 4, "y" ]]
  g.xlimit = [ 2.5, 4.5 ]
  g.color_series.set('Vramp Voltage')
  xynames = ['Vbat(Volt)', 'Sw Pwr 400KHz(dBm)'     ]
  g.plot_graph_data( xynames,  None, band + ' ORFS vs VBAT over VRAMP'  )


  g.plot_limits = [[ -24 , "Datasheet Limit", 4, "red" ],
                     [ -27 , "Margin Limit", 4, "y" ]]
  g.update_filter_conditions('Vramp Voltage', None )
  g.xlimit = [ 20, 38 ]
  g.color_series.set('Vbat(Volt)')
  xynames = ['PSA Pwr Out(dBm)', 'Sw Pwr 400KHz(dBm)'     ]
  g.plot_graph_data( xynames,  None, band + ' ORFS vs Pout over VBAT'  )


  g.plot_limits = [[ -24 , "Datasheet Limit", 4, "red" ],
                     [ -27 , "Margin Limit", 4, "y" ]]
  g.xlimit = [ 0.6, 1.6 ]
  g.color_series.set('Vbat(Volt)')
  xynames = ['Vramp Voltage', 'Sw Pwr 400KHz(dBm)'     ]
  g.plot_graph_data( xynames,  None, band + ' ORFS vs VRAMP over VBAT'  )

########################################################################


g.update_filter_conditions( 'Test Freq(MHz)', [869.0, 1850.0] )


runplots( 'LB' )
runplots( 'HB' )

g.loop()



