import numpy as np
import scipy
import matplotlib.pyplot as plt


print 'This is script princomp_ma7.py'
import __main__ as M
self = M.mag
self.status.set( 'running script' )

self.wclearfiles()

get_real_data = 1

if get_real_data:


    self.add_logfile( r'C:\Log File\cr0_cr1_sweep_ma2_xxxx_atrMA1_18feb15_1409.log')
    self.win_load()
    self.update_filter_conditions( 'C14' , 0.5 )
    #self.color_series.set( 'Vbat(Volt)' )

    cols = 'CR0_requested CR1_requested'.split()     # These are the columns names containing all the dependent coefficient values
    self.xnames_ordered = cols
    self.ynames_ordered = ['Fpk(MHz)']
    self.select_columns( self.xaxis_col_list, self.xnames_ordered )
    self.select_columns( self.yaxis_col_list, self.ynames_ordered )
    self.plot_interactive_graph()
    # Update the GUI with the new data





self.status.set( 'script finished' )