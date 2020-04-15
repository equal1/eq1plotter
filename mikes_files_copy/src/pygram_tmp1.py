#!/usr/local/bin/python

# Load the pygram libraries 

import sys
sys.path.append(r'/projects/sw/release')
sys.path.append(r'N:\sw\release')
from pygram_dev import *





mag = pygram()
mag.add_logfile(  r'N:\sw\user\masker\pygram\ipfiles\TXM_Pout_Contour_xxx.log')

#xynames = [ 'Phase(degree)', 'VSWR', 'Pout(dBm)','PAE(%)' ]
xynames = [ 'Phase(degree)', 'VSWR', 'PAE(%)' ]

mag.update_filter_conditions( 'Freq(MHz)',   825  )

#mag.color_series.set( 'VSWR' )
mag.plot_graph_data( xynames )



mag.loop()


