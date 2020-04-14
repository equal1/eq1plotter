
######################################################################################################
def create_offset_target( target, minmax ):
    '''Create new target line, which is offset from the input
    #   [ [1500,-3],   [1650,-3], ]    <- input target
    #   [ [1500,-3.2], [1650,-3.2] ]   <- ouput offset target
    '''

    yoffset = (self.ylimits[1] - self.ylimits[0])/50.0

    if minmax == 'max':
        yoffset = -yoffset
        
    new_target = []
    for pt in target:
        new_target.append( [pt[0], pt[1]+yoffset] )

    return new_target


######################################################################################################
def run_plot( xynames, xlim, ylim, target, titletxt ):
    '''Function to plot the data, setup the axes, and measure the results'''  
    
    # First plot out the graph
    self.xlimits = xlim
    self.ylimits = ylim
    if target != None:
        self.spec_limits = []
        for tg in target:
            print 'target1=', tg
            minmax = tg.pop()
            print 'target2=', tg
            print 'minmax=', minmax
            
            tg_shaded = create_offset_target( tg, minmax )
            self.spec_limits.append(  [ tg_shaded  , "", 20, '#FFEEEE' ] )
            self.spec_limits.append(  [ tg  ,        "", 3, "red" ] )
    else:
        self.spec_limits = None
    xyd = self.plot_graph_data( xynames,  titletxt = titletxt, savefile=titletxt)

######################################################################################################


import numpy as np
import scipy
import matplotlib.pyplot as plt
import cProfile

print 'This is script princomp_ma7.py'
import __main__ as M
self = M.mag
self.status.set( 'running script' )

self.wclearfiles()

logfile = r'T:\Advanced_Development\Shared\Projects\AD4007\lab_testing\test_results\logfiles\AD4007AA_screen_ATRunknown_SN64_AAS1_E0.1_GSO_OF_Reflow(35)_Trial3_13may15_1337.log'
self.add_logfile( logfile )
self.win_load()


# self.spec_limits = [ 
#    [ [ [1500,-3.2], [1650,-3.2], ] ,  "", 20, '#FFEEEE',  ],
#    [ [ [1500,-3],   [1650,-3], ] ,  "", 3, 'red' ],
#    ]
# 
# self.xlimits = [1000, 2000]
# self.ylimits = [-10, 0]
# 
# 
# self.plot_graph_data(xynames)
# 

xynames = ['Freq(MHz)', 's21_RFI_RFO_dB']
target = [ [[1427,-1.6], [1606,-1.6], 'max'],
           [[699,-12],   [960,-12],   'min'],
           [[1710,-10],   [2700,-10],   'min'],
         ]
run_plot( xynames, [500, 3000], [-15, 0], target, "")


self.status.set( 'script finished' )