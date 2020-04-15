#!/usr/local/bin/python

# Load the pygram libraries 

import sys
sys.path.append(r'/projects/sw/release')
sys.path.append(r'N:\sw\release')
from pygram_dev import *





mag = pygram()
mag.add_logfile(  r'N:/sw/user/masker/pygram/ipfiles/am7801-100107-sn045a2r8.csv')
mag.add_logfile(  r'N:/sw/user/masker/pygram/ipfiles/am7801-100107-sn045a3r1.csv')
mag.add_logfile(  r'N:/sw/user/masker/pygram/ipfiles/am7801-100107-sn045a1r8.csv')

xynames =  ['[Time] VAM', '[Time] SCOPE EFF*']


mag.color_series.set( 'csvfilename'  )

#mag.color_series.set( 'VSWR' )
mag.plot_graph_data( xynames )


mag.loop()


