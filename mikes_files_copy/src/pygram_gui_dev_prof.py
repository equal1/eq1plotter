#!/usr/local/bin/python

# Load the pygram libraries 

import sys
sys.path.append(r'/projects/sw/release')
sys.path.append(r'N:\sw\release')
from pygram_dev import *

import cProfile


def prof():
    mag = pygram()
    mag.prof_slope_count  = 0
    mag.add_logfile(  r'C:\TEMP\AM7802_100059_SN001.log')
    print " mag.prof_slope_count = ",        mag.prof_slope_count
#    mag.loop()


cProfile.run( "prof()" )