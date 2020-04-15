#!/usr/local/bin/python

# Load the pygram libraries 

import sys
sys.path.append(r'/projects/sw/release')
sys.path.append(r'N:\sw\release')
from pygram_dev import *





mag = pygram()
mag.add_logfile(  r'N:\sw\user\masker\pygram\ipfiles\AM7802_TA4_B1B_SN001.log')
mag.add_logfile(  r'N:\sw\user\masker\pygram\ipfiles\AM7802_TA4_B1B_SN002.log')


xynames =   ['Freq(MHz)', 'S21 DeEmbed', 'VSWR']


mag.color_series.set( 'Port'  )

#mag.color_series.set( 'VSWR' )
mag.plot_graph_data( xynames )


mag.loop()


