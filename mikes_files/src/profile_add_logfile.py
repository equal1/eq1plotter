#!/usr/bin/python

import sys
sys.path.append(r'/projects/sw/release')
sys.path.append(r'N:\sw\release')
from pygram_dev import *



import profile

# The main program

g = pygram()

file = 'Y:\Projects\NightTrainExpress\Shared_Area\DVT Test Results\AM7811\Molded\Lot_999_CC1\PRS_Test\EVB_nofilter_wC3\Contour\AM7811_100999_nofilter_wC3_SN038_Contour_Pypat.log'

profile.run('g.add_logfile(file)')

