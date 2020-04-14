import numpy as np
import scipy
import matplotlib.pyplot as plt
import cProfile

print 'This is script princomp_ma7.py'
import __main__ as M
self = M.mag
self.status.set( 'running script' )

logfile = r'L:\Lab & Testing\Hideya\afar_switch_3\IL\afar_sw_IL_GSO_06may15_1230_5228_P1_L2P1_D7_S1_B29_SN1.log'
self.wclearfiles()

command_string = 'self.add_logfile( logfile )'
cProfile.runctx( command_string , globals(), locals() )
self.win_load()

self.status.set( 'script finished' )