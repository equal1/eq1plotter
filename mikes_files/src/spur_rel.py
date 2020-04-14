#!/usr/bin/python

# Load the libraries 
import sys, time
sys.path.append( '/home/masker/bin/python' )
from pygram import *

###################################################################
###################################################################

# start pygram
aa = pygram()

# Load the logfile
aa.load_logfile( 'L:\Lab & Testing\ATR_Chiarlo\Log_files\Load_pull\TXM_7802_Stability_HL_TA4_100059_003.log')


#               XAXIS, YAXIS, 2nd YAXIS 
aa_xynames = [ 'Frequency of Spur (MHz)', \
            'Amplitude of Spur (dBm)', \
            'Amplitude of Spur, no harmonic 20MHz (dBm)' \
          ]


aa.plot_graph_data( aa_xynames )

aa.loop()   # loop forever, and wait for input form the gui
