#!/usr/local/bin/python

# Load the pygram libraries 

import sys
sys.path.append(r'/projects/sw/release')
sys.path.append(r'N:\sw\release')
from pygram_dev import *





mag = pygram()

mag.add_logfile(  r'N:\sw\user\masker\pygram\ipfiles\AM7801_TA5_T_U_CD_SN011.log')
mag.add_logfile(  r'N:\sw\user\masker\pygram\ipfiles\AM7801_TA5_T_U_CC_SN012.log')

mag.argscript   =  r'N:/sw/user/masker/arg/src/ARGPRD_chiarlo_all.py'
mag.prdfile     =  r'X:/01-Projects/05-Chiarlo/Marketing/PRD/PRD-05-0012-AM7801 Product Specification Document.xls'
mag.savedir     =  r'N:\sw\user\masker\pygram\opfiles\tmp10'
mag.arg_runmode =  'all'
mag.arg_testnum =  ''
mag.copy_atrlogfiles = False

self = mag

execfile( mag.argscript, globals(), locals() )


mag.loop()


