#!/usr/bin/python

# Load the libraries 
import sys, time
#sys.path.append(r'/projects/sw/user/masker/pygram/src')
sys.path.append(r'/projects/sw/release')
sys.path.append(r'N:\sw\release')
from pygram_dev import *


# start pygram
g = pygram()
g.add_logfile( r'N:/sw/user/masker/pygram/ipfiles/AM7806_temp_A1_DE_SN002_orig.log')


g.update_filter_conditions( 'Freq(MHz)' , 898.0 )
g.update_filter_conditions( 'Pwr In(dBm)', 3.0 )
g.update_filter_conditions( 'Temp(C)', 25 )
g.update_filter_conditions( 'Sub-band', 'LB-EGSM900' )
g.update_filter_conditions( 'TestName', 'Output Power & Efficiency' )

g.update_filter_conditions( 'Ref Pout(dBm)' )
g.update_filter_conditions( 'Ref Pout(dBm) N27' )
g.update_filter_conditions( 'Ref Pout(dBm) N35' )
#g.update_filter_conditions( 'nominal conditions', ['N35_LB-EGSM900', 'N27_LB-EGSM900'] )

g.color_series.set( 'Vbat(Volt)' )

xynames = ['Ref Pout(dBm) N27', 'Pwr Variation(dB) N27']
g.plot_graph_data( xynames )

 
g.loop()

