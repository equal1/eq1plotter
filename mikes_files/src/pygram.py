#!/usr/bin/python

###################################################################
#
# Example PYTHON matplotlib Program to display the    xxx
# spectrum of a modulated waveform  (Mike Asker 11jul08)
#
###################################################################


# Load the libraries 
import sys

# Tell python where to look for the matplotlib libraries as these are not part of the
#  standard python distribution
sys.path.append( '/tools/gnu/Linux/lib/python' )
sys.path.append( '/tools/gnu/Linux/lib/python/matplotlib-0.91.2-py2.3-linux-i686.egg' )
#sys.path.append( '/home/masker/bin/python' )

# Load the matplotlib and pylab libraries
from   matplotlib.mlab    import load
import matplotlib
import matplotlib.numerix as nx
import numpy as nu
from   pylab import *

import Tkinter as Tk
from tkFileDialog   import askopenfilename, asksaveasfilename, askdirectory, askopenfilenames

from matplotlib.widgets import Button, RectangleSelector

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

# General libraries for doing useful stuff (they're not needed in this prog though)
import re , os, getopt, math, commands, csv, types, glob


import Tix

from pprint import pprint 






###################################################################
###################################################################
###################################################################
###################################################################


class pygram:



###################################################################
###################################################################

    def __init__( self ):

      self.pygram_version = 'v1.42'
      print 'PYGRAM: %s,  MATPLOTLIB: %s,  PYTHON: %s'%  ( self.pygram_version, matplotlib.__version__,  sys.version[:6])

      self.run_mode = 'script'

      nu.seterr(divide='ignore', invalid='ignore')
#     nu.seterr(divide='raise', invalid='raise')


#     self.freq_sub_band_list  = [ ['GSM850' , 824, 848] ,        \
#                                  ['EGSM'   , 880, 914] ,        \
#                                  ['DCS'    , 1710.2, 1784.8],   \
#                                  ['PCS'    , 1850.2, 1909.8],   \
#                                  ['LB'     , 820, 915],         \
#                                  ['HB'     , 1710, 1910],       \
#                                ]

      # Define the frequencies of each sub band but round them up, this makes sure we are collecting all of the test results
      # which may include frequencies just outside the extremes of the band
      self.freq_sub_band_list  = [ ['GSM850' , 820, 850] ,        \
                                   ['EGSM'   , 880, 915] ,        \
                                   ['DCS'    , 1710, 1785],       \
                                   ['PCS'    , 1850, 1910],       \
                                   ['LB'     , 800, 950],         \
                                   ['HB'     , 1700, 1950],       \
                                 ]

                                                          #  LB  HB
      self.rated_power_values = {  '@ Rated Power(dB)'  : [ 33, 30 ] , }



      self.value_dict_names_original_list = [ 'logfilename', 'SN', 'TestName', 'Temp(C)', 
                                               'HB_LB', 'Segments', 'Vbat(Volt)', 'Freq(MHz)', 'Pwr In(dBm)', 
                                               'VSWR', 'Phase(degree)', 'Source VSWR', 'Source Phase(degree)',
                                               'Vramp Voltage', 'Regmap', 'Process',   ]
#                                              'Regmap', 'Process', 'Ref Pout(dBm)'  ]
      self.value_dict_names_original_list.sort()
      self.xaxis_reduced_list  =  [ 'Freq(MHz)', 'Temp(C)', '[Time] Time',  '[Time] VAM', '[Time] VRAMP', 
                                    'VSWR', 'Phase(degree)', 'Source VSWR', 'Source Phase(degree)',
                                     'Pout(dBm)', 'VAM(volt)', 'Vbat(Volt)', 
                                    'Vramp Voltage', 'Frequency of Spur (MHz)', 'PSA Pwr Out(dBm)', 'Ref Pout(dBm)']

      self.yaxis_reduced_list  =  [ 'AM-PM Slope (deg/dB)' ,
                                    'AM-PM(degree)' ,
                                    'Pout(dBm)' ,
                                    'AM-PM Slope - Ref (deg/dB) <emp-limits>' ,
                                    'Gain AM/(VAM-offset) Slope - Ref (dB/dB) <emp-limits>' ,
                                    'Gain AM/(VAM-offset) (dB) <emp-limits>' ,
                                    'Amplitude of Spur (dBm)',
                                    'Amplitude of Spur, no harmonic 20MHz (dBm)',
                                    'Amplitude of Spur, no harmonic {spur_filter_table}MHz (dBm)',
                                    'PAE(%)',
                                    '2nd Harmonics Amplitude(dBm)',
                                    '3rd Harmonics Amplitude(dBm)',
                                    '4th Harmonics Amplitude(dBm)',
                                    '5th Harmonics Amplitude(dBm)',
                                    '6th Harmonics Amplitude(dBm)',
                                    'Crossband Isolation Amplitude(dBm)',
                                    'Fwd Isol1 Amplitude(dBm)',
                                    'Fwd Isol2 Amplitude(dBm)',
                                    'Sw Pwr 400KHz(dBm)',
                                    'Sw Pwr 600KHz(dBm)',
                                  ]
    
      # series_seperated_list is a list that causes data to be split into seperate series based on these column names. 
      self.series_seperated_list = [ 'Freq(MHz)' ,
                                     'Process',
                                     'Pwr In(dBm)',
                                     'Regmap',
                                     'Segments',
                                     'SN',
                                     'Temp(C)',
                                     'TestName',
                                     'Vbat(Volt)',
                                     'logfilename',
                                     'VSWR',
                                     'Source VSWR',
                                   ]


      if os.name == 'nt':
        var = 'TEMP'
        self.os = 'pc'
      else:
        var = 'HOME'
        self.os = 'linux'

      self.config_file =  os.path.join( os.environ[ var ]  , 'pygram.ini')

      cwd = os.getcwd()
      self.config = {}
      self.config[ 'loaddir' ]  = cwd  
      self.config[ 'savedir' ]  = cwd  


      self.characteristic_impedance = 50.0
      self.vam_offset = 0.24
      self.ambient_temperature   = 25
      self.harmonic_spur_min_amp = -44.0
      self.spur_freq_filter_table    = {}

      self.vmuxsel_register      = '22'  # classico
      self.vmuxsel_register      = '24'  # chiarlo



      self.value_dict_names = []
      self.values_dict_done = 0

      self.db_selfam     = None
      self.db_selfam_old = None
      self.db_doublebuttonpress = False
      self.db_seldb     = 'LAB'
      self.db_seldb_old = None
      self.db_serial_number = ''
      self.done_db_logfile_dict = False

      self.data = {}
      self.ref  = {}
      self.csv_data = []
      self.datacount = 0
      self.recordnum = 0
      self.atrsectioncount = 0
      self.csvsectioncount = 0
      self.logfilenames = []
      self.csvfilenames = []
      self.savefilename = ''
      self.savedir     = os.getcwd() + '/'
      self.logfiledir  = os.getcwd() + '/'
      self.logfilename  = ''
      self.logfilebasename  = ''
       
      self.ref_logfilename  = None

      self.done_list_columns = False
      self.values_dict            = {}
      self.filter_conditions = []
      self.series_conditions = []
      self.xynames = [ None, None ]

      self.spec_limits = None

      self.interactive = 0
      self.xlimits = []
      self.ylimits = []
      self.xaxis_limits = []
      self.yaxis_limits = []
      self.xgrid = None
      self.ygrid = None

 



      self.numgrids = 20
#                                 left  right  top    bottom
      self.plot_position       = [0.06, 0.75,  0.92,  0.07 ]
      self.conditions_location = [ 0.76 , 0.88 ]   # window coordinates
      self.legend_location     = [ 0.63, 0.0   ]   # graph data coordinates
      self.color_list = [ 'r','g','b','c','m','y', 'k', 'orange','violet', 'brown', 'purple' ]
      self.dash_list = [ [1,0], [3,2], [15,4], [5,8] ]
      self.plot_marker = '.'
      self.plot_linewidth = 2
      self.save_plot_count = -1

      self.xdata = {}
      self.ydata = {}
      self.rndata = {}
      self.data_color = {}
      self.pick_count = 0
      self.pick_count_total = 0
      self.pick_data = False
      self.series_picked = {}
      self.series_picked_ind = {}
      self.plot = False
      self.sel_object = None
      self.something_picked = False
      self.png_filename = ''
      self.key = 'None'
      self.keysym = 'NoKeyYet'
      self.keysym_dict = {}
      self.hblb        = ''
      self.s2p_type    = ''
      
      self.win_init()




      self.spec2meas = {   \

      '(.*) MHz Ant-Rx Insertion Loss (dB)' : [  'Rx Insertion Loss',  ], \
      '(.*) MHz (.*) VSWR'                  : [  'Rx VSWR',  ], \
      }












   

###################################################################
###################################################################

    def html_add_image_text( self, html_file='', txt='', img_file='' ):
        '''Writes txt into the html_file (if present) and writes the html_file as a link into the html_file (if present)'''
    

        if html_file == '': return

        fp = open( html_file, 'a' )
     

        if img_file != '':
            img_file  = re.sub( r'^/projects/' , 'http://netapp/' , img_file )
            img_base = re.sub( r'.*/', '', img_file )
            print >> fp , '<br>Plot <a href="%s">%s</a><img src="%s"><br>' % (img_file, img_base, img_file)

        if txt != '':
            txtlis = txt.split('\n')
            for t in txtlis:
              print >> fp , '%s<br>' % t
              print '%s' % t
           

        fp.close()
   
   
###################################################################

    def html_check_limit( self, val,  gtlt, lim ):
         ''' Checks to see if val is within the limit. gtlt is '<' or '>' character.
          val and lim are numbers that are compared depending on gtlt 
          The returned valu is an html string of the form   'val(lim)'
          If the val fails the gtlt test against the lim value then the val
          is colored red '''

         if  val != None:
           if( (gtlt == ">" and val > lim  or gtlt == "<" and val < lim) ): 
              txt = '%0.3f(%0.2f)' % (val, lim)
           else:    
              txt = '<font color=\"#FF0000\">%0.3f</font>(%0.2f)' % (val, lim)    # added !!!!! so that we can turn it into a regular space at the end of write_html_file
         else:
              txt = '<font color=\"#FF0000\">???</font>(%0.2f)'   % (lim)    # added !!!!! so that we can turn it into a regular space at the end of write_html_file
         return txt

###################################################################
###################################################################
# Table Driven Graph Functions

##################################################################################################
    def set_filter_conditions( self, fct, sweep_params_list, nom_vals ):
    
        band = self.get_filter_conditions( 'HB_LB' )
        if type( band ) != types.StringType:  band = ''
    
    
        # first set all sweep params to nominal
        for swp in sweep_params_list:
            self.update_filter_conditions(swp, nom_vals[swp] )
    
        self.color_series.set('')
        self.line_series.set('')
           
        for ix, p in enumerate(fct[1:]):
    
          if p[0] == 'measure' : continue
          
          if len(p) < 2 :
             print '*** error *** error in filter_conditions_table , line = %s' % (fct)
             print '       error in filter = %s' % p
    
          swp_name = p[0]
          swp_opt  = p[1]
    
          if len(p) > 2:   fixed_val = p[2]
          else:            fixed_val = None
    
          if len(p) > 2:  vals = p[2:]
          else:           vals = None
    
          if swp_opt == 'C':
               self.update_filter_conditions(swp_name)
               self.color_series.set(swp_name)
               # if the number of values in the values dict is only 1 then dont bother with this plot
               if 0 and len( self.values_dict[ swp_name ] ) <= 1:
                   print '*** WARNING *** for color sweep name %s there is only %d sweeps' % ( swp_name , len( self.values_dict[ swp_name ])) , self.values_dict[ swp_name ] 
       ## ?????????   we need to do a bit more checking here, we need to do as much checking to weed out any empty plots.
    #              write_excuse( fct )
                   return None
              
          if swp_opt == 'L':
               self.update_filter_conditions(swp_name)
               self.line_series.set(swp_name)
    
          if swp_opt == 'F':
            self.update_filter_conditions(swp_name, fixed_val )
    
          if vals != None:
               self.update_filter_conditions(swp_name, vals)
               
          if swp_opt == 'A':
               self.update_filter_conditions(swp_name)
    
        cond_str = ''
        for fltr in self.filter_conditions:
              if len ( fltr ) == 3 and fltr[0] in sweep_params_list:
                 cond_str = cond_str + '%s=%s; ' % ( fltr[0], fltr[2] )
     
        title = fct[0] % ( band, cond_str )
    
        return title
    
    ###################################################################################################
    
    
    
    ########################################################################################################
    def set_spec_limits( self, fct, limval ):
       ''' Set the spec limits to be plotted on the graph 
           It looks for an list item that matches:
    
             ['measure','ymin_at_xval','Pnmed','Nmed'] 
             [ measure', <measure_type>, <at_val>, <limit_value> ]
    
            Where :
               <measeure_type>     is one of  ymin, ymax, ymin_at_xval, ymax_at_xval, ?????? 
               <at_val>            is where on the x axis the measurement  measured, it is a limval name, or an actual value, or list of two values representing a range.
               <limit_value>       is the limit value that will be drawn on the graph
       '''
    
       band = self.get_filter_conditions( 'HB_LB' )
       if type( band ) != types.StringType:  band = ''
    
       self.spec_limits = []
       
#      print '(set_spec_limits)' , self.filter_conditions
#      print '(set_spec_limits)' , limval
       #   ....  ['measure','ymin_at_xval','vramp_max','Pout.n']],
       for p in fct:
         if p[0] == 'measure':
           mtype      = p[1]
           at_val     = p[2]
           limname    = p[3]
    
    
           if at_val == '' : at_val = None
    
    
           if type( limname ) == types.StringType:
               if type( limval[ limname ] ) == types.ListType:
                 if band == 'LB' : y = limval[ limname ][0]
                 else:             y = limval[ limname ][1]
               else:
                 y = limval[ limname ]
           else:
               y = limname
          
           if type( at_val ) == types.StringType:
               if at_val != None   and at_val  != '':
                   if type( limval[ at_val ] ) == types.ListType:
                     if band == 'LB' : x =  limval[ at_val ][0]
                     else:            x =  limval[ at_val ][1]
                   else:
                     x = limval[ at_val ]
           else:
     
              if type( at_val ) == types.ListType:
                x = at_val
              else:
                x =  at_val
     
           if limname != None  and limname != '' : 
               if at_val == None:     self.spec_limits.append( [ y , limname + ' = ' + str(y) , 2, 'red'] )
               else:            
                   if type( x ) == types.ListType:
                        self.spec_limits.append( [[[x[0], y],[x[1], y]]  , limname + ' = ' + str(y) , 2, 'red'] )
                   else:
                        self.spec_limits.append( [[[x*0.9, y],[x*1.1, y]]  , limname + ' = ' + str(y) , 2, 'red'] )
       
           if x != None  and type( x ) != types.ListType:
                print type( x ), x
                self.spec_limits.append( [[[ x, y*1.1],[x, y*0.9]] , '' , 2, 'y'] )
    
###################################################################












  
###################################################################
###################################################################
# Measurement functions

    def maxy2x( self, x, y, limits=None):
       ''' Finds the x value where y is a max 
           warning only works if y is an increasing quantity!!!'''
       maxval =  self.maxyval( x, y, limits)
       return self.measure_value( x, y, 'x_at_yval', maxval )

    def miny2x( self, x, y):
       ''' Finds the x value where y is a min
           warning only works if y is an increasing quantity!!!'''
       minval =  self.minyval( x, y, limits)
       return self.measure_value( x, y, 'x_at_yval', minval )

    def maxyval( self, x, y, limits=None):
       if limits == None: meas_type = 'ymax'
       else:              meas_type = 'ymax_limits'
       return self.measure_value( x, y, meas_type, limits ) - 1e-12

    def minyval( self, x, y, limits=None):
       if limits == None: meas_type = 'ymin'
       else:              meas_type = 'ymin_limits'
       return self.measure_value( x, y, meas_type, limits ) + 1e-12



    def y2x( self, x, y, yval):
       return self.measure_value( x, y, 'x_at_yval', yval )
      
    def x2y( self, x, y, t):
       return self.measure_value( x, y, 'y_at_xval', t )

###################################################################

    def measure_value( self, xyd, measure_type, at_value=None ):
       ''' Makes a measurement on the x and y data.
            measurement_type is one of   xmax,ymax,xmin,ymin, y_at_xval, x_at_yval
            at_value         is the value at which the meausrment is made '''
    
       val = NaN
       
       if at_value != None:
          if type(at_value) == types.ListType:
            at_value = [ float(at_value[0]), float(at_value[1])]
          else:
            at_value = float( at_value )
    
       if xyd == None: return val
       
       x   = xyd[0]
       y   = xyd[1]
       rnl = xyd[2]
       snl = xyd[3]
       cl  = xyd[4]
       dl  = xyd[5]
       
       
       # loop through all the lines, and measure_value on that line
       if len(x) > 1:
                      
          vl = []
          for  i in range(len(x)):
            xydi = [ [x[i]], [y[i]], [rnl[i]], [snl[i]], [cl[i]], [dl[i]] ]
            v = self.measure_value( xydi, measure_type, at_value )
            vl.append( v )
            

            
          if re.match( r'(x|y)max_', measure_type):
            vmix = 0
            for ix in range(len(vl)):
              v = vl[ix]
              if v[0] > vl[vmix][0]: vmix = ix
            v = vl[vmix]
            return  v[0], v[1], v[2], v[3]
            
          elif re.match( r'^(x|y)min_', measure_type):
            vmix = 0
            for ix in range(len(vl)):
              v = vl[ix]
              if v[0] < vl[vmix][0]: vmix = ix
            v = vl[vmix]
            return  v[0], v[1], v[2], v[3]

            return min(vl)
          else:
            # return the average value
            vsum = 0
            for ix in range(len(vl)):
              vsum += vl[ix][0]
            v = vl[0]
            return  vsum/len(vl), v[1], v[2], v[3]

       x = x[0]
       y = y[0]
       sn = snl[0]
       c  = cl[0]
       d  = dl[0]
       
       
       
       # check to see if we have multiple sets of data points (ie many lines)
       # if so the we will split them up into sub series and perform the measure on each seperately.
     
       if measure_type == 'ymax_at_xval' or measure_type == 'ymin_at_xval': measure_type = 'y_at_xval'
       if measure_type == 'xmax_at_yval' or measure_type == 'xmin_at_yval': measure_type = 'x_at_yval'
     
       if measure_type == 'y_at_xval':
          if not( max(x) < at_value or at_value < min(x)) :
#           [val] = interp([at_value], x, y)
            
            # loop through all the y values and look for the point where the y value crosses the at_value
            # then do proportional 
            for i in range( len(x) ):
              i2 = i+1
              if i2 >= len(x) : i2 = i
              x1 = x[i]
              x2 = x[i2]
              y1 = y[i]
              y2 = y[i2]


              if ( x2 > at_value and x1 <= at_value ) or \
                 ( x2 < at_value and x1 >= at_value ) :
                  val =  y1+ (  (y2-y1) * (at_value-x1) / (x2-x1) ) 
#                  print '       val=', val
                  break

            
    
       # warning this interp function assumes that the first dependent varaible is an increasing quantity!!!
       if measure_type == 'x_at_yval':
          if not( max(y) < at_value or at_value < min(y)) :
#           [val] = interp([at_value], y, x)

            # loop through all the y values and look for the point where the y value crosses the at_value
            # then do proportional 
            for i in range( len(x) ):
              i2 = i+1
              if i2 >= len(x) : i2 = i
              x1 = x[i]
              x2 = x[i2]
              y1 = y[i]
              y2 = y[i2]


              if ( y2 > at_value and y1 <= at_value ) or \
                 ( y2 < at_value and y1 >= at_value ) :
                  val =  x1+ (  (x2-x1) * (at_value-y1) / (y2-y1) ) 
#                  print '       val=', val
                  break
  

       elif measure_type == 'xmax':  val = max(x)
       elif measure_type == 'xmin':  val = min(x)
       elif measure_type == 'ymax':  val = max(y)
       elif measure_type == 'ymin':  val = min(y)
    
    
       elif measure_type == 'ymax_xlimits' or measure_type == 'ymin_xlimits' or measure_type =='ymaxabs_xlimits':
       # get the max y value for xvalues between at_value[0] and at_value[1]
    
          # first calculate the yvalues at the x at_value's
          y0 = self.measure_value( x, y, 'y_at_xval', at_value[0] )
    #     print 'at_value[ %s ] = %s' % ( at_value[0], y0 )
          y1 = self.measure_value( x, y, 'y_at_xval', at_value[1] )
    #     print 'at_value[ %s ] = %s' % ( at_value[1], y1 )
    
          #then clip the x and y lists so they contain only data points within the at_value limits
    
          xt = [ at_value[0] ]
          yt = [ y0 ]
          i = 0
          for xi in x:
             if xi > at_value[0] :
                if xi >= at_value[1]: break
                xt.append( xi )
                yt.append( y[i] )
             i += 1
          xt.append( at_value[1] )
          yt.append( y1 )
    
          if    measure_type == 'ymax_xlimits':
             val = max(yt)
          elif  measure_type == 'ymin_xlimits':
             val = min(yt)
          elif  measure_type == 'ymaxabs_xlimits':
             val = max( max(yt) , -min(yt) )
    
    
       return val, sn, c, d 
    
    
###################################################################
###################################################################

    def html_add_image( self, html_file, txt, img_file ):
       ''' adds txt and the img_file into an html file '''
    
       txt = re.sub( r'\n', '<br>', txt )
    
    
       img_file  = re.sub( r'^/projects/' , 'http://netapp/' , img_file )
       img_base = re.sub( r'.*/', '', img_file )
    
       fp = open( html_file, 'a' )
       print >> fp , '%s<br>Plot<a href="%s">%s</a><img src="%s">' % (txt, img_file, img_base, img_file)
       fp.close()




###################################################################
###################################################################

    def load_logfile( self, logfilename=None, csvlogfile=None, vmux_names_file=None, temperature=None ):

    
      self.wclearfiles()      
      self.add_logfile( logfilename, csvlogfile, vmux_names_file, temperature )



###################################################################


    def add_vmux_csvfile( self, vmux_results_filename, vmux_names_filename=None):
      '''Reads a VMUX style CSV format comma delimited log file and loads the data into an internal dictionary 'data' '''

      self.logfilename       =  vmux_results_filename 
#     self.logfilenames.append( vmux_results_filename )

      # first read the vmux mapping file that translates the register select number into the name of the selected vmux signal

      if vmux_names_filename != None:

          self.vmux_sel2name = {}

          filename = vmux_names_filename
          try:
            fip = open(filename, "rb")
            reader = csv.reader(fip, delimiter=',', skipinitialspace=True)
    
            print " ...reading vmux signal names file %s" % filename

            prefix = ''
            for c in reader:
                 if len(c) >= 5:
                   if c[1] != '' and c[4] != '':
                      if c[3] != '' : 
                          prefix = re.sub('\n',' ', c[3])
                      #name = 'vmux_sel[' + c[1] + ']  ' + prefix + ' ' + c[4]
                      name = prefix + ' ' + c[4] + ' vmux_sel[' + c[1] + ']'
                      self.vmux_sel2name[ c[1] ] = name
#                     print name

            fip.close()
      
          except Exception:
#           print "*** warning (add_vmux_csvfile) could not read vmux signal names file %s" % filename
            pass

      self.vmux_sel2name[ '-1' ] = 'SCOPE CHANNEL 1'
      self.vmux_sel2name[ '-2' ] = 'SCOPE CHANNEL 2'
      self.vmux_sel2name[ '-3' ] = 'SCOPE CHANNEL 3'
      self.vmux_sel2name[ '-4' ] = 'SCOPE CHANNEL 4'


      # then read the csv results log file to get the vmux value data 

      filename = vmux_results_filename
      
      try:
        fip = open(filename, "rb")
        reader = csv.reader(fip, delimiter=',', skipinitialspace=True)
      except Exception:
        print "*** ERROR (add_vmux_csvfile) could not read vmux results file %s" % filename
    
      print " ...reading vmux results file %s" % filename

      prefix = ''
      vmux_sig_list   = []
      vmux_time_list  = []
      vmux_value_list = []
      csvsectioncount    = self.csvsectioncount


      self.add_new_column( 'csvfilename' )

      

      # Go through all the existing record numbers and match the csv sections one at a time with each successive recordnumber. 
      # It is assumed that each section of csv data (data between 2 Test No. 1's) is associated with sucessive recordnumbers in the log filename.


      self.add_new_column( 'section'    )
      self.add_new_column( 'record_num' )
      self.add_new_column( 'Alert Reg' )



      recordnum = 0
      linecount = 0
      last_testnum = 0
      for c in reader:
         linecount += 1

         if len(c) > 3 and c[0] == 'Test No.' :
             vmux_time_list = c[5:]
             continue



         scope_vmux = False
         try:
             x = int( c[3] , 16 )
             if x > 0xFFFFFF0 : 
               x = x - 4294967296
               scope_vmux = True
         except:
             pass

#        if len(c) > 3 and ( ( c[1] == self.vmuxsel_register and c[3].strip() == '1' ) or scope_vmux ) :  # ie it is a register 22 read operation
         if len(c) > 3 and ( (  c[3].strip() == '1' ) or scope_vmux ) :  # ie it is a register 22 read operation

             regval = int(c[2], 16) 

#            print 'regval', c[2], regval, c[3]
             
             # check for the alert register
             if len(c) > 5:
                 self.data[ 'Alert Reg' ].append( c[4] )
                 

             # get the vmux name from the register 22 value
                           
             # the vmux select value is bits[9:3] of the register 22 value
             full_regval =  (0x03FF8 & regval)  >> 3
             if scope_vmux:  
                 full_regval = x


             # if we see a 1 in column 0 of the csv file we must be at the start of a section.
             # find the first column
             if c[0] == '1' and last_testnum != '1': 
               csvsectioncount += 1
               vmux_sig_list = []
             last_testnum = c[0]
    
     
             # possibly obsolete now! 
             if str(full_regval) in self.vmux_sel2name:
                 vmux_name = self.vmux_sel2name[ str(full_regval) ]
                 vmux_sig_list.append( full_regval )

             vmux_data_list = c[5:]


             self.datacount += 1
             self.data[ 'record_num'  ].append( self.datacount        )
             self.data[ 'csvfilename' ].append( vmux_results_filename )
             self.data[ 'section'     ].append( csvsectioncount       )

             self.write_vmux_data( csvsectioncount, full_regval, vmux_data_list, vmux_time_list  )


      self.csvsectioncount = csvsectioncount
      print '   .read %6d lines, record count %6d' % (linecount, self.datacount)

      fip.close()         
    
    ###################################################################

    def write_vmux_data( self, sectionnum, vmux_num, vmux_data_list, vmux_time_list  ):

        ''' Takes the vmux_data_list and add it to all the records in the data array for the given sectionnum
            It also does the same to the vmux_time_list, except it only does so if it is not already added. 
            In addition it will calculate an average value for the vmux_data_list by averaging the last 10% of
            samples, and writing this value into the data array '''

        # add vmux_data_list to every data array record which match sectionnum



        rn = self.datacount -1


        # go through the time list and find the end of the time data
        # strip off the last columns

        colnam  = {}
        collist = []
        n = 0
        for t in vmux_time_list:
           n +=1
           try:
              x = float( t )
           except Exception:
#             print 'non numeric column:', n, t
              collist.append( n )
              colnam[ n ] = t.strip()


        vmux_time_list = vmux_time_list[: collist[0]-1 ]


        # convert the vmux_data_list to floats, and remove every value that isn't a float
        new_vmux_data_list = []
        n = 0
        for fld in vmux_data_list:
             n +=1
             try:
                x = float( fld )
             except Exception:
                pass
             
             if n <  collist[0]:
                new_vmux_data_list.append( fld )
             else:
                # if this is a comment string then use it to get all our info
#               print 'v=', n, v
                if re.search('\s*//', fld):
#                   print 'found it'
                    
                    v = re.sub('\s', '', fld)
                    grps = re.search(r'{(.*?)(}|$)', fld)
                    if grps:
                       parstr = grps.groups()[0]
                       # overwrite the parameter string removing the vmux signals, we do this so that we can get a list of parameter conditions without the
                       # vmux selection
                       fld = re.sub( r'.*TERMINATE', 'TERMINATE', parstr)
                       pars   = parstr.split(';')
                       print pars
                       for nv in pars:
                          g = re.search( r'(.+)=(.+)' , nv)
                          if g and len(g.groups()) == 2:
#                            print nv
                             
                             nm =  g.groups()[0]
                             nm =  nm.strip()

                             v = g.groups()[1]
                             v =  v.strip()
                             c = '[csv] ' + nm
                             self.add_new_column( c )
                             self.data[ c ][rn] =  v 

                             if nm == 'VMUXNAME' : vmux_name = v
                if n in colnam:
                  cnam = '[csv] ' + colnam[ n ]
                  self.add_new_column( cnam )
                  self.data[ cnam ][rn] = fld


             
        vmux_data_list = new_vmux_data_list
         
        if str(vmux_num) in self.vmux_sel2name:   
            vmux_name = self.vmux_sel2name[ str(vmux_num) ]

        if vmux_num < 0:
           vmux_name = 'SCOPE CHANNEL %s' % -vmux_num



        vmux_data_name    = '[Time] ' + vmux_name                # the name of the field in the 
        vmux_time_name    = '[Time] ' + 'Time'

        self.add_new_column( vmux_data_name )
        self.add_new_column( vmux_time_name )

        self.data[ vmux_data_name ][rn] = vmux_data_list
        self.data[ vmux_time_name ][rn] = vmux_time_list

        # dont bother doing the 90% data values if we are running in csv only mode, (may have to revisit this
#       vmux_data_90_name = '[T90%] '  + vmux_name 
#       self.add_new_column( vmux_data_90_name )
#       vmux_90_data_value = self.get_90_vmux_data( vmux_data_list, 0.9, 1.0 )
#       self.data[ vmux_data_90_name ][ rn ] = vmux_90_data_value

        return



    ###################################################################

    def get_90_vmux_data( self, vmux_data_list, start, finish):

         len_vdl =  len(vmux_data_list) -1
         start_idx  = int( start  * len_vdl )
         finish_idx = int( finish * len_vdl )
         
         c = 0
         sum = 0
         for idx in range( start_idx, finish_idx): 
             c += 1
             sum += float( vmux_data_list[ idx ] )
          
         return sum / float( c )

    ###################################################################
    ###################################################################
    ###################################################################


    def add_logfile(self, logfilename=None, csvfilename=None, vmux_names_file=None, temperature=None):
      '''Reads the tab delimited log file and loads the data into an internal dictionary 'data' '''
    
   

      # first check to see what type of logfile this is, if its a csv file then assume it is a vmux logfile, and retspecify the file varaibles
      if logfilename != None and re.search(r'.csv', logfilename  ) and csvfilename==None and vmux_names_file==None:
         csvfilename = logfilename
         logfilename = None
         vmux_names_file = 'Riserva_vmux_signals.csv'


      self.status.set( '(add_logfile) LOADING LOGFILE RESULTS: %s %s ' % ( logfilename, csvfilename ) )
      self.root.update()

      rn_start = self.datacount
    
      if logfilename != None:

          self.logfilename      =  logfilename 
          self.logfiledir       = os.path.dirname( logfilename )
          self.logfilebasename  = os.path.basename( logfilename )
          ( dummy , self.logfile_extension ) = os.path.splitext(  logfilename )
          
          


          self.logfilenames.append( logfilename )

          linecount = 0
          
          try:
            fip = open(logfilename, "rb")
            reader = csv.reader(fip, delimiter='\t')
          except Exception:
            print "*** ERROR (load_logfile) could not read file " , logfilename
    
          print " ...reading logfile '%s'" % logfilename
    
          cnum = 1
          opcol2name = []
          section_data = {}
          in_section_header = False

    
          name = 'record_num'
          if name not in self.data :  
            self.data[ name ] = [None] * self.datacount
            opcol2name.append(name)
          name = 'logfilename'
          if name not in self.data :  
            self.data[ name ] = [None] * self.datacount
            opcol2name.append(name)
          name = 'linenumber'
          if name not in self.data :  
            self.data[ name ] = [None] * self.datacount
            opcol2name.append(name)
    

          logfile_type      = 'excel'
          done_column_header = False


          ### Enable the reading of s2p network analyzer files
          if self.logfile_extension == '.s2p':

               self.s2p_type = 'real_imag'
               logfile_type = 's2p'
               done_column_header = True
               current_test_colnum2colname = []
    
         
               # look at each column heading name and create a new data_column and fill it with nulls up to the
    
               
               for name in (    'Freq(s2p)',  \
                             's11_mag','s11_phi', \
                             's21_mag','s21_phi', \
                             's12_mag','s12_phi', \
                             's22_mag','s22_phi', \
                        ):
                  name = re.sub(r'\.', '', name)
                  current_test_colnum2colname.append( name )
    
                  if name not in self.data :  
            #        print "  ADDING  MISSING COLUMN ", name, self.datacount
                     self.add_new_column( name )
                     cnum = cnum + 1
                     opcol2name.append(name) 
    
    
          
    
          for row in reader:
    
            linecount += 1

            if logfile_type ==  's2p' : 
                 if re.search(r'^#\s+Hz\s+S\s+MA\s+R', row[0]): self.s2p_type = 'mag_phi'
                 row = row[0].split()
                 if  re.search(r'^\s*!.*', row[0]) or  re.search(r'^\s*#.*', row[0] ) :  continue



            if len( row ) < 1 : continue

            if re.search(r'^\s*//\*+', row[0]) :  continue

            # Look for a new section header line
            #
            #      //Serial Number: A0B BOM-C SS SN001

            grps = re.search(r'^//(.*?):(.*)$', row[0])
            if grps:
               name  = grps.groups()[0].strip()
               name = re.sub(r'\.', '', name)
               value = grps.groups()[1].strip()
               section_data[ name ] = value
               logfile_type = 'atr'

               if in_section_header == False:
                    in_section_header = True
                    self.atrsectioncount += 1
                    section_data[ 'section' ] = self.atrsectioncount

    
               if name == 'Register Map File' :
                 name = 'Regmap'
                 value = self.get_filename_from_fullpath( value )
                 section_data[ name ] = value
    






            # Look for a test header line in the log file of the form:
            #
            #     //T#    TestName        Sw Matrix       S21(dB) Tuner Loss(dB)  ...
            #
            # or if its a simulation results file : 
            #
            #     fin     vam     phase(outRl[::,1])[0, ::]

            
            if re.search(r'^\s*//T#\s*$', row[0]) : 
               atr_column_header = True
               logfile_type = 'atr'
            else:
               atr_column_header = False


            if atr_column_header == True                                   or \
               ( logfile_type == 'excel' and done_column_header == False) :

               logfile_type = 'atr'
               done_column_header = True
               current_test_colnum2colname = []
    
         
               # look at each column heading name and create a new data_column and fill it with nulls up to the
               
               for i in range( 0 , len(row)): 
                  name = row[i].strip()
                  name = re.sub(r'\.', '', name)
                  current_test_colnum2colname.append( name )
    
                  if name not in self.data :  
            #        print "  ADDING  MISSING COLUMN ", name, self.datacount
                     self.data[ name ] = [None] * self.datacount
                     cnum = cnum + 1
                     opcol2name.append(name) 
    
               for name in section_data: 
                  current_test_colnum2colname.append( name )
    
                  if name not in self.data :  
            #        print "  ADDING  MISSING COLUMN ", name, self.datacount
                     self.data[ name ] = [None] * self.datacount
                     cnum = cnum + 1
                     opcol2name.append(name) 
    











            #----------------------------------------------------------------------
            #
            # Add spurious data as a list to each test
            #
            #----------------------------------------------------------------------

          
            
            #//T#    TestName        Sw Matrix       S21(dB) Tuner Loss(dB)  S21In(dB)       Test Freq(MHz)  Vbat(Volt)      Pwr In(dBm)     Magnitude       Phase(degree)   VSWR    Ref Coef        Is Spur Harmonics (-99 = no)    Spur Number     Range Table of Spur     Frequency of Spur (MHz) Amplitude of Spur (dBm) Absolute Limit (dBm)    Pass/Fail(1|0)  Spur Pass Threshold (dBm)       Alert Reg       Temperature(degree C)   Vramp File      Date    Time    Comment 
            #2       Spurious (ETSI reduced) L3B     -25.846 -0.236  -4.065371       825     3.35    3       0.5     -180    3       0.5     0       0       0       0       0       0       0       0       1203                    l:\Lab & Testing\ATR_Classico\Ramp_files\ramps_classicoV6_9Jul08\LB_pwrsel11\classicoV6.1.40v_ramp.txt  11/7/2008       18:43:51        3
            #//Spurious Data                                                                                                         -99     1       7       796.2629        -42.692 -44     1       -36        
            #//Spurious Data                                                                                                         -99     2       8       875.9052        -43.666 -44     1       -36        
            #//Spurious Data                                                                                                         2       3       10      1649.331        -16.813 -44     1       -36        
            #//Spurious Data                                                                                                         3       4       10      2478.918        -23.649 -44     1       -36        
            #//Spurious Data                                                                                                         2       5       13      1644.11 -16.908 -44     1       -36        
            #//Spurious Data                                                                                                         3       6       13      2477.052        -23.837 -44     1       -36        





            if re.search(r'^\s*//Spurious Data\s*$', row[0]) :
               
                #print 'datacount linecount',  linecount, self.datacount

                # write the value of each column into the data[] dictionary by adding it to the end.
                for i in range( 1 , len(row)):
                  name  = current_test_colnum2colname[ i ]
                  value = row[i].strip()


                  #print 'value is <%s>' % value
                  #print 'length of %s is %s' % ( name , len(self.data[ name ]) )
    
                  # turn the spurioous column value into a list
                  if value != '':
                     if self.data[ name ][self.datacount-1] == 0 or self.data[ name ][self.datacount-1] == None:
                         self.data[ name ][self.datacount-1] = []
                     else:
                         self.data[ name ][self.datacount-1].append( value )


    
    
            # Look for a data result line
            #
            #      2       AM-AM AM-PM Distortion  L3B     -26.09  0.0     -5.31   825.0  ...
            # 
            # or if its a simulation results file : 
            #
            #      8.25000000000000000E8   2.39999999999999991E-1  -3.86778247745102188E1

            try: 
               x = float( row[0] )
               first_field_is_number = True
            except Exception:
               first_field_is_number = False
            

            #if re.search(r'^\s*\d+\s*$', row[0]):
            if ( logfile_type == 'atr'   and first_field_is_number      ) or \
               ( logfile_type == 'excel' and done_column_header == True ) or \
               ( logfile_type == 's2p'   and done_column_header == True ):


                self.datacount = self.datacount + 1 
                in_section_header = False
                c2num = {}
    
                # write the value of each column into the data[] dictionary by adding it to the end.
                for i in range( 0 , len(row)):
                  name  = current_test_colnum2colname[ i ]
                  value = row[i].strip()
                  c2num[ name ] = 'done'
    
    
                  #if name == 'Time' : value = re.sub(':','',value)
            
    
                  if name != 'Alert Reg' and re.search(r'^\s*(\+|\-)?\d+(\.)?(\d+)?([eE][+-]?\d+)?\s*$',value):
                      value = float(value)
    

                  if name == 'Temperature(degree C)' and temperature != None :
                     value = temperature

                  if name == 'AM-PM(degree)' and -360 <= float(value)  <= +360 :
                     value = ((value+270) % 360 ) - 270
                     
                  if name == '' and -360 <= float(value)  <= +360 :
                     value = ((value+270) % 360 ) - 270

                  if name == 'Frequency of Spur (MHz)' :
                       if value == 0.0 : dont_save_amplitude = True
                       else:             dont_save_amplitude = False

                  if name == 'Amplitude of Spur (dBm)' and dont_save_amplitude: 
                     value = None


                  ##############################################################################
                  # Save the ordinary data in the self.data array
                  #
                  # print '(load_logfile) name=<%s> value=<%s>' % ( name, value)
                  self.data[ name ].append( value )
                  #
                  ##############################################################################

    

                # save the record number as well
                self.data[ 'record_num' ].append( self.datacount )
                c2num[ 'record_num' ] = 'done'
    
                # save the record number as well
                self.data[ 'logfilename' ].append( logfilename )
                c2num[ 'logfilename' ] = 'done'

                # save the record number as well
                self.data[ 'linenumber' ].append( linecount )
                c2num[ 'linenumber' ] = 'done'


    
                for sd in section_data:
                  self.data[ sd ].append( section_data[ sd ] )
                  c2num[ sd ] = 'done'
    
    
                # fill the unused columns with None to pad them out.
                for name in self.data :
                  
                  if name not in c2num:
                    #print "filling in missing field for  column %s, on record %d" % ( name, self.datacount )
                    self.data[ name ].append( None )
    
    
    
          fip.close()



          print '   .read %6d lines, read in records %6d to %6d' % (linecount, rn_start, self.datacount)




      if csvfilename != None:

         self.add_vmux_csvfile( csvfilename, vmux_names_file )


      self.add_missing_columns( rn_start, self.datacount)




                

      self.win_load( logfilename, csvfilename, self.datacount-rn_start )


      files = ', '.join( self.logfilenames + self.csvfilenames )
      z = self.root.winfo_toplevel()
      z.wm_title('PYGRAM Graphing Tool  version:  ' + self.pygram_version + '     ' + files )







    ###################################################################
    ###################################################################

    def add_db_res(self, db_lg_key):
      '''Reads the results from the datapower database and loads the data into an internal dictionary 'data' '''
    

      temperature = None
      rescount = 0
      rn_start = self.datacount

    
      if db_lg_key != None:

          self.db_make_logfile_dict()
#         pprint( self.db_lgk2logfile )
        
          if db_lg_key in self.db_lgk2logfile:
             logfilename = self.db_lgk2logfile[ db_lg_key ]
             sn          = self.db_lgk2sn[ db_lg_key ]
             self.db_serial_number = sn

          else:
             print "*** ERROR *** (add_db_res) , cannot find logfile with key '%s' in the database" % db_lg_key
#            pprint( self.db_lgk2logfile )
#            return

          self.status.set( '(add_db_res) LOADING DATABASE RESULTS: (E%s) %s ' % ( db_lg_key, logfilename ) )
          self.root.update()


#         logfilename = 'E' + str( db_lg_key ) 
          self.logfilename =        logfilename 
          self.logfilenames.append( logfilename )

          linecount = 0
          
          #try:
          if 1==1:

              ###############################################
              #
              # Connect to the Datapower Oracle database
              #
              ###############################################

              cursor = self.connect_to_datapower_db()
              self.db_cursor = cursor


              print " ...reading results from Datapower for LG_KEY: E%s (logfile: '%s', Serial Number: '%s')" % ( db_lg_key, logfilename, sn )


              # With the Results key (db_lg_key LG_KEY) lookup the script file key (pg_key PG_KEY)

              pg_key = self.db_lookup('OP_LOG', 'PG_KEY', 'where LG_KEY = %s' % db_lg_key)



              ###############################################
              #
              # Retrieve all the column headers for this set of results
              #
              ###############################################

              cursor.execute( "select %s.DEF%s.*     from %s.DEF%s"  % (self.db_seldb, pg_key, self.db_seldb, pg_key) )
              db_headers      = cursor.fetchall()


              colname2num  = {}
              num2colname = {}
              for r in db_headers:
#                 print '%5s %s' % ( r[0], r[43] )
                  name = re.sub(r'\.', '', str(r[43]).strip() )
              
                  colname2num[ name ] = r[0]
                  num2colname[ str(r[0] ) ] = name

                  self.add_new_column( name )
#                 print r[43],
                  
#             print ''
              num2colname[ str(0) ] = 'LG_KEY'
              self.add_new_column( 'LG_KEY' )

              self.add_new_column( 'logfilename' )
              self.add_new_column( 'linenumber' )


              ###############################################
              #
              # Retreive all the results and add them to the data dictionary
              #
              ###############################################


              cursor.execute( "select %s.RES%s.*     from %s.RES%s where LG_KEY = %s"  % (self.db_seldb, pg_key, self.db_seldb, pg_key, db_lg_key) )
              db_test_results = cursor.fetchall()

              # sort the data into ascending linenumbers
              if 'linenum' in colname2num:
                 self.sort_column = colname2num[ 'linenum' ]
                 db_test_results.sort( self.compare_columns )

              for r in db_test_results:
                 self.datacount += 1
                 rescount += 1
                 for fi in range(len(r)):
                     f = r[fi]
                     colname = num2colname[ str(fi) ] 
                     if f == None: f = ''
                     try: 
                        f = float(f)
                     except Exception:
                        f = str(f).strip()

                     if colname == 'AM-PM(degree)' and f != '' and -360 <= float(f)  <= +360 :
                        f = ((f+270) % 360 ) - 270

                     self.data[ colname ].append( f )

                 self.data[ 'logfilename' ].append( logfilename )
                 self.data[ 'linenumber' ].append( str( rescount ) )

              print '   .read %6d db records, read in records %6d to %6d' % (rescount, rn_start, self.datacount)

#         except Exception:
#             print "*** ERROR (load_logfile) could not read file " , logfilename
    

    
              self.db_cursor.close()



      self.add_missing_columns( rn_start, self.datacount)




      self.win_load( logfilename, num_records= self.datacount-rn_start )


    ###################################################################
    def create_values_dict( self ):
    
             # look at the value and add them to the values dictionary if not already in the list
        if self.values_dict_done == 0:
             self.values_dict = {}
             self.values_dict_count = {}
             for name in self.value_dict_names:
               self.add_values_dict( name )
        self.values_dict_done = 1
             

    def add_values_dict( self, name ):

         if name not in self.data: 
            self.add_new_column( name )
            self.add_values_dict( name )
            return

         if type( name ) == types.StringType :
 
              if not name in self.values_dict:
               self.values_dict[ name ] = []
               self.values_dict_count[ name ] = []

               # if the number of different values exceeds 200 then abort the dictionary, 
               #  this must be a results data column, and we don't need to form the dictionary for results columns

               for rn in range(0,self.datacount):
                   val =  self.data[name][rn]
#                  if name == 'Serial Number': 
#                     val = re.sub(r'.*([sS][nN]\d+)[_ ]?.*', r'\1', val, re.I )
                     

                   try:
                     # we found a value which we've seen before, increamet the count
                     idx = self.values_dict[ name ].index( val ) 
                     self.values_dict_count[ name ][ idx ] += 1
                     
               
                   except Exception:
                       # we found a new value  , add it to the list, and set the count to 1
                       self.values_dict[ name ].append(  val ) 
                       self.values_dict_count[ name ].append( 1 )
                       if len( self.values_dict_count[ name ] ) > 200 : break
    
    ###################################################################
    def hex2bin( self, hexstr ):
    
      try:
        i = int( hexstr, 16 )
      except Exception:
        i = 0
        
      b = ''
      for count in range(0,16):
        j = i & 1
        b = str(j) + b
        i >>= 1
      return b
    
    ###################################################################
    
      
    def add_missing_columns(self, rn_start=None, rn_finish=None ):
      ''' Adds the vramp voltage column, and segment column and the, HB/LB column, also adds the part number etc'''
       

#     print '(add_missing_columns) rn_start=%s  rn_finish=%s' % ( rn_start, rn_finish)

      if rn_start==None or  rn_finish==None : return

      rn_sum = rn_finish - rn_start
    
      #add missing column data to the end of the existing data. 
    
      ### FILL IN THE ALERT REGISTER BITS  
      if 'Alert Reg' in self.data :

        self.add_new_column( 'Alert Reg (bit15) OCP1' )
        self.add_new_column( 'Alert Reg (bit14) OCP0' )
        self.add_new_column( 'Alert Reg (bit13) TEMP >125C' )
        self.add_new_column( 'Alert Reg (bit12) OVP' )
        self.add_new_column( 'Alert Reg (bit11) SHUTDN >150C' )
          
        for rn in range( rn_start, rn_finish ):
          alert_reg_binary = self.hex2bin( self.data['Alert Reg'][rn] )
          self.data['Alert Reg (bit15) OCP1'][rn]         = int( alert_reg_binary[15-15] )  
          self.data['Alert Reg (bit14) OCP0'][rn]         = int( alert_reg_binary[15-14] )  
          self.data['Alert Reg (bit13) TEMP >125C'][rn]   = int( alert_reg_binary[15-13] )  
          self.data['Alert Reg (bit12) OVP'][rn]          = int( alert_reg_binary[15-12] )  
          self.data['Alert Reg (bit11) SHUTDN >150C'][rn] = int( alert_reg_binary[15-11] )  



    
    
      ### GET INFO FROM THE VRAMP FILENAME AND PATH
      if 'Vramp File' in self.data :

        self.add_new_column( 'Vramp Filebase' )
        self.add_new_column( 'Segments' )
        self.add_new_column( 'Vramp Voltage' )
        self.add_new_column( 'Vramp Release' )
        self.add_new_column( 'PCL' )

        for rn in range( rn_start, rn_finish ):
          vramp_release, hb_lb, seg, voltage, full_filespec, pcl_level = self.get_vramp_filename_data( rn )
          self.data['Segments'][rn]        = seg
          self.data['Vramp Voltage'][rn]   = voltage
          self.data['Vramp Release'][rn]   = vramp_release
          self.data['Vramp Filebase'][rn]  = self.get_vramp_filebase( full_filespec )
          if pcl_level != '' : 
                self.add_new_column( 'PCL' )
                self.data['PCL'][rn]             = pcl_level
    
             
      if 'Serial Number' in self.data :
        old_fullname = ''
        shortname    = ''
        for rn in range( rn_start, rn_finish ):
           self.add_new_column( 'SN' )
           fullname = self.data['Serial Number'][rn]
           if fullname != old_fullname: 
                 shortname = re.sub(r'.*([sS][nN]\d+)[_ ]?.*', r'\1', fullname, re.I )
                 old_fullname = fullname
           self.data['SN'][rn] = shortname
           
#                  if name == 'Serial Number': 
        

      if 'Sw Matrix' in self.data :


        for rn in range( rn_start, rn_finish ):
           self.add_new_column( 'Sw Matrix' )
           f = self.data['Sw Matrix'][rn]
           if f == None and 'Sw.Matrix' in self.data: 
               f = self.data['Sw.Matrix'][rn]

           self.add_new_column( 'HB_LB' )
#          print 'f=', f, '  rn=', rn
           if f[0] == 'H' : self.data['HB_LB'][rn] = 'HB'
           else           : self.data['HB_LB'][rn] = 'LB'
      else: 
        try: 
            x = self.FIN
            self.add_new_column( 'HB_LB' )
            for rn in range( rn_start, rn_finish ):
                if float(x) > 1.2e9 :   self.data['HB_LB'][rn] = 'HB'
                else:                   self.data['HB_LB'][rn] = 'LB'
        except Exception:
            pass
     

      if 'Freq(s2p)' in self.data :
           self.add_new_column( 'Freq(MHz)' )
           self.add_new_column( 'Freq(GHz)' )
           for rn in range( rn_start, rn_finish ):
              self.data['Freq(MHz)'][rn] = self.data['Freq(s2p)'][rn] / 1e6
              self.data['Freq(GHz)'][rn] = self.data['Freq(s2p)'][rn] / 1e9
      
      if 'Test Freq(MHz)' in self.data :
           self.add_new_column( 'Freq(MHz)' )
           self.add_new_column( 'Freq(GHz)' )
           for rn in range( rn_start, rn_finish ):
              self.data['Freq(MHz)'][rn] = self.data['Test Freq(MHz)'][rn]
              self.data['Freq(GHz)'][rn] = self.data['Test Freq(MHz)'][rn] / 1e3
      

#####   To get S11 and S22 in VSWR, need to use (1+ mag (S11, or 22))/(1- mag (S11, or 22)),   email from H.Sun 12nov09

      # but first we need to convert the s2p data if it happens to be in real imaginary format into magnitude phase format
      if 's11_mag' in self.data and 's11_phi' in self.data and self.s2p_type == 'real_imag':
           for rn in range( rn_start, rn_finish ):
              self.data['s11_mag'][rn] = sqrt( self.data['s11_mag'][rn]**2 +  self.data['s11_phi'][rn]**2 )
              self.data['s11_phi'][rn] = 0.0
      if 's22_mag' in self.data and 's22_phi' in self.data and self.s2p_type == 'real_imag':
           for rn in range( rn_start, rn_finish ):
              self.data['s22_mag'][rn] = sqrt( self.data['s22_mag'][rn]**2 +  self.data['s22_phi'][rn]**2 )
              self.data['s22_phi'][rn] = 0.0
      if 's21_mag' in self.data and 's21_phi' in self.data and self.s2p_type == 'real_imag':
           for rn in range( rn_start, rn_finish ):
              self.data['s21_mag'][rn] = sqrt( self.data['s21_mag'][rn]**2 +  self.data['s21_phi'][rn]**2 )
              self.data['s21_phi'][rn] = 0.0
      if 's12_mag' in self.data and 's12_phi' in self.data and self.s2p_type == 'real_imag':
           for rn in range( rn_start, rn_finish ):
              self.data['s12_mag'][rn] = sqrt( self.data['s12_mag'][rn]**2 +  self.data['s12_phi'][rn]**2 )
              self.data['s12_phi'][rn] = 0.0


      if 's11_mag' in self.data :
           self.add_new_column( 's11_vswr' )
           for rn in range( rn_start, rn_finish ):
              self.data['s11_vswr'][rn] = (1 + self.data['s11_mag'][rn]) / (1 - self.data['s11_mag'][rn])

      if 's22_mag' in self.data :
           self.add_new_column( 's22_vswr' )
           for rn in range( rn_start, rn_finish ):
              self.data['s22_vswr'][rn] = (1 + self.data['s22_mag'][rn]) / (1 - self.data['s22_mag'][rn])


#####   To get S21 in dB and de-embed, need to do:  LB  20*log (mag(S21))  + 0.33,  HB  20*log (mag(S21))  + 0.59 ,   email from H.Sun 12nov09

      if 's21_mag' in self.data :
           self.add_new_column( 's21_dB' )
           for rn in range( rn_start, rn_finish ):
              if 'Freq(MHz)' in self.data and self.data['Freq(MHz)'][rn] < 1300 :
                  correction = 0.33
              else:
                  correction = 0.59
              self.data['s21_dB'][rn] =  20*log10(self.data['s21_mag'][rn])  + correction

#     if 's22_mag' in self.data :
      if 's12_mag' in self.data :
           self.add_new_column( 's12_dB' )
           self.add_new_column( 's12_Loss_dB' )
           for rn in range( rn_start, rn_finish ):
              if 'Freq(MHz)' in self.data and self.data['Freq(MHz)'][rn] < 1300 :
                  correction = 0.33
              else:
                  correction = 0.59
              self.data['s12_dB'][rn] =  20*log10(self.data['s12_mag'][rn])  + correction
              self.data['s12_Loss_dB'][rn] =  -self.data['s12_dB'][rn]















      if 'Reg Map' in self.data :
        for rn in range( rn_start, rn_finish ):
           self.add_new_column( 'Regmap' )
           self.data['Regmap'][rn] = self.data['Reg Map'][rn]


    

      if 'Temperature(degree C)' in self.data or 'Temp' in self.data:

          if  'Temperature(degree C)' in self.data:  self.add_new_column( 'Temperature(degree C)' )
          if  'Temp'                  in self.data:  self.add_new_column( 'Temp' )
          self.add_new_column( 'Temp(C)' )

          for rn in range( rn_start, rn_finish ):
             if 'Temperature(degree C)' in self.data :
                t =  self.data['Temperature(degree C)'][rn]
             else:
                t =  self.data['Temp'][rn]

             if t == None or t == '': 
                t = self.ambient_temperature
#            print 'Temperature(degree C)', t, 
             if -200 > t > 200 : 
               t = self.ambient_temperature
             self.data['Temp(C)'][rn] = self.nearest( t, 5, self.ambient_temperature )




      # look for the process in the serial number. If not found we will assume it is 'TT'

      self.add_new_column( 'Serial Number' )
      for rn in range( rn_start, rn_finish ):
            if self.data['Serial Number'][rn] == None:
               self.data['Serial Number'][rn] = self.db_serial_number


      self.add_new_column( 'Process' )
      for rn in range( rn_start, rn_finish ):
          x = re.search( r'(TT|FF|SS)', self.data['Serial Number'][rn].upper() )
          if x :
            n = x.groups()
            self.data['Process'][rn] = n[0]
          else:
            self.data['Process'][rn] = 'TT'




      self.add_new_column( 'Part Number (Chip ID)' )
      self.add_new_column( 'chipid' )
      for rn in range( rn_start, rn_finish ):
          if self.data['Part Number (Chip ID)'][rn] == None and self.data['chipid'][rn] != None :
                    self.data['Part Number (Chip ID)'][rn] = self.data['chipid'][rn].strip()


      # create a new orfs column with the worst of the +ve and -ve values, 
      # the +ve value is stored in the 'Sw Pwr 400KHz(dBm)' column, make this the column where the max value is stored

      if 'Sw Pwr -400KHz(dBm)' in self.data and 'Sw Pwr 400KHz(dBm)' in self.data:
         self.add_new_column( 'Sw Pwr +400KHz(dBm)' )
         self.add_new_column( 'Sw Pwr -400KHz(dBm)' )
         self.add_new_column( 'Sw Pwr 400KHz(dBm)' )

             
         self.add_new_column( 'PSA Pwr Out(dBm)' )
         
         for rn in range( rn_start, rn_finish ):
            maxval = max( self.data[ 'Sw Pwr -400KHz(dBm)' ][rn], self.data[ 'Sw Pwr 400KHz(dBm)' ][rn] )
            self.data[ 'Sw Pwr +400KHz(dBm)' ][rn] =  self.data[ 'Sw Pwr 400KHz(dBm)' ][rn] 
            self.data[ 'Sw Pwr 400KHz(dBm)'  ][rn] =  maxval
            if self.data[ 'Sw Pwr -400KHz(dBm)' ][rn] != None and self.data[ 'Sw Pwr -400KHz(db)' ][rn]:
                self.data[ 'PSA Pwr Out(dBm)'  ][rn] = self.data[ 'Sw Pwr -400KHz(dBm)' ][rn]   - self.data[ 'Sw Pwr -400KHz(db)' ][rn]
             

      # create a new orfs column with the worst of the +ve and -ve values, 
      # the +ve value is stored in the 'Sw Pwr 600KHz(dBm)' column, make this the column where the max value is stored

      if 'Sw Pwr -600KHz(dBm)' in self.data and 'Sw Pwr 600KHz(dBm)' in self.data:
         self.add_new_column( 'Sw Pwr +600KHz(dBm)' )
         self.add_new_column( 'Sw Pwr -600KHz(dBm)' )
         self.add_new_column( 'Sw Pwr 600KHz(dBm)' )
         
         for rn in range( rn_start, rn_finish ):
            maxval = max( self.data[ 'Sw Pwr -600KHz(dBm)' ][rn], self.data[ 'Sw Pwr 600KHz(dBm)' ][rn] )
            self.data[ 'Sw Pwr +600KHz(dBm)' ][rn] =  self.data[ 'Sw Pwr 600KHz(dBm)' ][rn] 
            self.data[ 'Sw Pwr 600KHz(dBm)'  ][rn] =  maxval
             


      
      if 'TestName' in self.data  and  'Spurious (ETSI reduced)' in  self.data['TestName']:
         self.add_spurious_data(  1 )
         self.add_spurious_data(  2 )
         self.add_spurious_data(  5 )
         self.add_spurious_data( 10 )
         self.add_spurious_data( 15 )
         self.add_spurious_data( 20 )
         self.add_spurious_data(    )
      

      self.add_vramp2pout_data( rn_start, rn_finish )



      # Convert the available power numbers into a generic column 'Pout' with units of dBm,W,V
      if 'Adj Pwr Out(dBm)' in self.data or 'PSA Pwr Out(dBm)' in self.data or 'Pout(dBm)' in self.data: 
         self.add_new_column( 'Pout(dBm)'  )
         self.add_new_column( 'Pout(W)'  )
         self.add_new_column( 'Pout(V)'  )
         self.add_new_column( 'Poutpk(V)'  )
         for rn in range( rn_start, rn_finish ):
             pdbm = None
             if      'Pout(dBm)' in self.data and self.data[ 'Pout(dBm)' ][rn] != None: 
                     pdbm = self.data[ 'Pout(dBm)' ][rn]
             elif    'Adj Pwr Out(dBm)' in self.data and self.data[ 'Adj Pwr Out(dBm)' ][rn] != None: 
                     pdbm = self.data[ 'Adj Pwr Out(dBm)' ][rn]
             elif    'PSA Pwr Out(dBm)' in self.data and self.data[ 'PSA Pwr Out(dBm)' ][rn] != None:                               
                     pdbm = self.data[ 'PSA Pwr Out(dBm)' ][rn]

             if pdbm != None:
                
                 pw = 10**( (pdbm-30.0)/10.0 )
                 pv = sqrt( self.characteristic_impedance * pw )
                 self.data[ 'Pout(dBm)' ][rn]  = pdbm
                 self.data[ 'Pout(W)'   ][rn]  = pw
                 self.data[ 'Pout(V)'   ][rn]  = pv
                 self.data[ 'Poutpk(V)'   ][rn]  = pv * 1.414213562



      # Get the AMAM data
      vam_name = 'VAM(volt)' 
      if vam_name not in self.data: 
          vam_name = 'Vramp Voltage'
      

      if vam_name in self.data and  'Pout(dBm)' in self.data :
         self.add_new_column( 'AMAM conversion abs (V/V)'   )
         self.add_new_column( 'AMAM conversion abs (V/V-voffset)'   )
         self.add_new_column( 'AMAM conversion Voutpk/VAM (dV/dV)' )
         for rn in range( rn_start, rn_finish ):

                 vam = float( self.data[ vam_name ][rn] )
                 pv  = self.data[ 'Poutpk(V)'   ][rn]
                 amam_abs   = None
                 amam_voff  = None
                 amam_delta = None
                 if vam != None and pv  != None :
                    amam_abs  =  pv / vam 
                    amam_voff =  pv / (vam - self.vam_offset )
                    try: 
                      delta_vam = vam - vam_old
                      delta_pv  = pv  - pv_old
                    except Exception:
                      delta_vam = 0
                      delta_pv  = 0
                   
                    if delta_vam < 1e-3: delta_vam = 1e-3
                      
                    amam_delta = delta_pv / delta_vam
                    pv_old = pv
                    vam_old = vam

                 self.data[ 'AMAM conversion abs (V/V)'            ][rn]  = amam_abs
                 self.data[ 'AMAM conversion abs (V/V-voffset)'    ][rn]  = amam_voff
                 self.data[ 'AMAM conversion Voutpk/VAM (dV/dV)'   ][rn]  = amam_delta
          




      # In simulation log files we can have VAM and Power out, in which case we can calculate the VAM to pout gain
      # We have VAM and Output Power data in the logfile then we can caluclate the AM-AM distortion
      if vam_name in self.data and  'Adj Pwr Out(dBm)' in self.data :

         got_data = False

         for rn in range( rn_start, rn_finish ):

            v = float( self.data[ vam_name   ][rn] )
            p = self.data[ 'Adj Pwr Out(dBm)' ][rn]
            if type(v) == types.NoneType or (type(v) == types.StringType  and  v.lower() == 'nan') or \
               type(p) == types.NoneType or (type(p) == types.StringType  and  p.lower() == 'nan'): 
               gain = None
            else:
               if not got_data:
                   got_data = True
                   self.add_new_column( 'Gain AM/(VAM-offset) (dB)'              )
                   self.add_new_column( 'Gain AM/(VAM-offset) (dB) <emp-limits>' )
                   self.add_new_column( 'Gain AM/(VAM-offset) Slope (dB/dB)'     ) 

               p = self.data[ 'Adj Pwr Out(dBm)' ][rn]
               if type(p) == types.NoneType or (type(p) == types.StringType  and  p.lower() == 'nan'): 
                  gain = None
               else:
              
                    vam_offset_diff = v - self.vam_offset
                    if vam_offset_diff < 0.001 : vam_offset_diff = 0.001
                    gain = self.data[ 'Adj Pwr Out(dBm)' ][rn] -   20*log10( vam_offset_diff )

            if got_data:
                self.data[ 'Gain AM/(VAM-offset) (dB)' ][rn]              = gain
                self.data[ 'Gain AM/(VAM-offset) (dB) <emp-limits>' ][rn] = gain

         if got_data:
             self.add_gain_slope( [ rn_start, rn_finish] )
             if 'AM-PM(degree)' in self.data:
                self.add_new_column( 'AM-PM Slope (deg/dB)' )
                self.add_phase_slope( [ rn_start, rn_finish] )


      # We have VAM and AM-PM Phase data in the logfile then we can calculate the phase distortion slope
#     if 'AM-PM(degree)' in self.data and  'Adj Pwr Out(dBm)' in self.data :
#        self.add_new_column( 'AM-PM Slope (deg/dB)' )
#        self.add_phase_slope( [ rn_start, rn_finish] )



      # make sure every data name in the data dictionary is the adjusted in length to the same value (self.datacount)
      for n in self.data:
        self.add_new_column( n )


      # add some special vmux columns
      pname = '[csv] Script File Name'
      if pname in self.data:

          name_a   = '[Time] AVDDRV3_TM'
          name_b   = '[Time] FB_TM'
          new_name = '[Time] AVDDRV3*'
 
          if name_a in self.data and name_b in self.data:
              self.add_new_column( new_name )
              for rna in range( rn_start, rn_finish ):
                   if self.data[ name_a ][ rna ] != None:
                      for rnb in range( rn_start, rn_finish ):
                          if self.data[ name_b ][ rnb ] != None:
#                            print self.data[ pname ][ rna ] , self.data[ pname ][ rnb ]
                             if self.data[ pname ][ rna ] == self.data[ pname ][ rnb ] :
#                               print 'found '
                                new_list = []
                                a_list = self.data[ name_a ][ rna ]
                                b_list = self.data[ name_b ][ rnb ]
#                               print len(a_list), len(b_list)
                                
                                for n in range(len( a_list )):
                                     a = float( a_list[ n ] )
                                     b = float( b_list[ n ] )
                                     y = a*9 - b*8
                                     new_list.append( y )
                                self.data[ new_name ][ rna ] = new_list


          name_a   = '[Time] VDD3_HALF'
          name_b   = '[Time] AVSS_VG3'
          new_name = '[Time] AVDDPA*'

          if name_a in self.data and name_b in self.data:
              self.add_new_column( new_name )
              for rna in range( rn_start, rn_finish ):
                   if self.data[ name_a ][ rna ] != None:

                      for rnb in range( rn_start, rn_finish ):
                          if self.data[ name_b ][ rnb ] != None:
#                            print self.data[ pname ][ rna ] , self.data[ pname ][ rnb ]
                             if 1==1 or self.data[ pname ][ rna ] == self.data[ pname ][ rnb ] :
#                               print 'found '
                                new_list = []
                                a_list = self.data[ name_a ][ rna ]
                                b_list = self.data[ name_b ][ rnb ]
#                               print len(a_list), len(b_list)
                                
                                for n in range(len( a_list )):
                                     a = float( a_list[ n ] )
                                     b = float( b_list[ n ] )
                                     y = 2*a - 2*b
                                     new_list.append( y )
                                self.data[ new_name ][ rna ] = new_list
                             break


          name_a   = '[Time] VBAT_THIRD'
          name_b   = '[Time] AVSS_VG3'
          new_name = '[Time] VBAT*'

          if name_a in self.data and name_b in self.data:
              self.add_new_column( new_name )
              for rna in range( rn_start, rn_finish ):
                   if self.data[ name_a ][ rna ] != None:

                      for rnb in range( rn_start, rn_finish ):
                          if self.data[ name_b ][ rnb ] != None:
#                            print self.data[ pname ][ rna ] , self.data[ pname ][ rnb ]
                             if 1==1 or self.data[ pname ][ rna ] == self.data[ pname ][ rnb ] :
#                               print 'found '
                                new_list = []
                                a_list = self.data[ name_a ][ rna ]
                                b_list = self.data[ name_b ][ rnb ]
#                               print len(a_list), len(b_list)
                                
                                for n in range(len( a_list )):
                                     a = float( a_list[ n ] )
                                     b = float( b_list[ n ] )
                                     y = 3*a - 4*b
                                     new_list.append( y )
                                self.data[ new_name ][ rna ] = new_list
                             break


#         self.scale_time_data( '[Time] VDD3_HALF',    '[Time] AVDDPA*'  , 2, rn_start, rn_finish )
          self.scale_time_data( '[Time] AVDDRV1_DIV2', '[Time] AVDDRV1*' , 2, rn_start, rn_finish )
          self.scale_time_data( '[Time] AVDDRV2_DIV2', '[Time] AVDDRV2*' , 2, rn_start, rn_finish )

          self.scale_time_data( '[Time] VG3_TM',       '[Time] VG3*'     , 3,  rn_start, rn_finish )
          self.scale_time_data( '[Time] VG2HB_TM',     '[Time] VG2HB*'   , 3,  rn_start, rn_finish )
          self.scale_time_data( '[Time] VG2LB_TM',     '[Time] VG2LB*'   , 3,  rn_start, rn_finish )
#         self.scale_time_data( '[Time] VBAT_THIRD',   '[Time] VBAT*'    , 3,  rn_start, rn_finish )
          self.scale_time_data( '[Time] VCP_BY4',      '[Time] VCP*'     , 4,  rn_start, rn_finish )

          name = '[Time] VAM'
          list = []
          if name in self.data:
             for rn in range( rn_start, rn_finish ):
                 if self.data[ name ][ rn ] != None:
                      list = self.data[ name ][ rn ]
       
             for rn in range( rn_start, rn_finish ):
                 self.data[ name ][ rn ] = list
        
          name = '[Time] VRAMP'
          list = []
          if name in self.data:
             for rn in range( rn_start, rn_finish ):
                 if self.data[ name ][ rn ] != None:
                      list = self.data[ name ][ rn ]
       
             for rn in range( rn_start, rn_finish ):
                 self.data[ name ][ rn ] = list
        
             
          if '[csv] Meas1 Value' in self.data and '[csv] Meas2 Value' in self.data and   \
             '[csv] Meas3 Value' in self.data and '[csv] Meas4 Value' in self.data:

             self.data[ '[csv] _mst event *' ]        = self.data[ '[csv] Meas1 Value' ]
             self.data[ '[csv] _current x 0.2ohm *' ] = self.data[ '[csv] Meas2 Value' ]
             self.data[ '[csv] _vbat *' ]             = self.data[ '[csv] Meas3 Value' ]
             self.data[ '[csv] _vout into 50ohm *' ] = self.data[ '[csv] Meas4 Value' ]

             new_name = '[csv] _efficiency *'
             self.add_new_column( new_name )

             for rn in range( rn_start, rn_finish ):
               vbat = self.data[ '[csv] _vbat *'             ][rn]
               curr = self.data[ '[csv] _current x 0.2ohm *' ][rn]
               vout = self.data[ '[csv] _vout into 50ohm *'  ][rn]
               try:
                  pwr = vout*vout / vbat*curr
               except Exception:
                  pwr = None         
               self.data[ new_name ][rn] = pwr
                          


      if self.value_dict_names == []:
          for vdn in self.value_dict_names_original_list:
            if vdn in self.data:
                self.value_dict_names.append( vdn )
#               self.values_dict[ vdn ] = []

      self.values_dict_done = 0
      self.create_values_dict()

      self.add_cal_pout_data( rn_start, rn_finish)

#     self.value_dict_names = []
#     if self.value_dict_names == []:
#         for vdn in self.value_dict_names_original_list:
#           if vdn in self.data:
#               self.value_dict_names.append( vdn )
#               self.values_dict[ vdn ] = []
                

    ###################################################################
    def scale_time_data( self, name, new_name, scale, rn_start, rn_finish ):
       ''' Creates a new column 'new_name' by scaling the 'name' column'''

       if name in self.data:
           self.add_new_column( new_name )
           for rn in range( rn_start, rn_finish ):
                if self.data[ name ][ rn ] != None:
                    new_list = []
                    list = self.data[ name ][ rn ]
                    
                    for n in range(len( list )):
                         a = float( list[ n ] )
                         y = a*scale
                         new_list.append( y )
                    self.data[ new_name ][ rn ] = new_list
                    



    ###################################################################
    def add_cal_pout_data( self, rn_start, rn_finish ):
      ''' The purpose of this function is to add a new calibration pout column
          The value of the 'Ref Pout(dBm)' column matches the Pout of the nominal
          conditions.
          Go through all the pout data for the nominal conditions and
          record the calibration pout values for each vramp voltage,
          then write out the calibration pout values for all the other
          non-nominal record. This way we can select data for rated power'''
          
        
        
        
  
      
      
        
      # These are the column names which we will check to see if the test is run nominal under nominal conditions 
      nom_colname_list  = [ 'VSWR', 'Phase(degree)', 'Temp(C)', 'Segments', 'Vbat(Volt)', 'Pwr In(dBm)', 'Regmap' ]
      
      # these are the nominal values which. Nominal data will be chosen with values closest to these
      nom_target_value_list = [   1   ,      0,             25     ,    'x',        3.5      ,     3        ,    'x'   ]
      nom_found_value_list  = []

      # 1
      # Find out which frequencies were present in the log file, and find the frequency which is closest to the center of the
      # band, (and make sure the count for this frequency is high enough)
      nom_freq_list = []
      done_lb = False
      done_hb = False
      for k in self.freq_sub_band_list:
           nom_freq = -1       
           # get the center of band frequency, this will be the nominal freq
           flw = k[1]
           fup = k[2]
           fmid = (flw+fup)/2.0

#          print '(add_cal) looking for values in values_dict that most closely match', fmid
           
           fmin_diff_i = 0
           fdiff = []
           inband_freq_count = 0
           for i,f in enumerate( self.values_dict[ 'Freq(MHz)' ] ):
                 fdiff.append(None)
                 fdiff[i] = abs(f - fmid)
                 if fdiff[i] < fdiff[ fmin_diff_i ]: fmin_diff_i = i
                 if  flw <= f <= fup  and self.values_dict_count[ 'Freq(MHz)' ][i] > 10:
                      inband_freq_count +=1
#                print '(add_cal)             ... trying', f, i, fmin_diff_i, ' inband_freq_count=', inband_freq_count, fdiff[i],  fdiff[ fmin_diff_i ]
                    
           # if the number of frequencies within the band is less than three then there is not enough to make a proper Ref Pout test
           
           #
           if inband_freq_count >=3:
                
               nom_freq = self.values_dict[ 'Freq(MHz)' ][ fmin_diff_i ]
               
               # if we have already found 3 frequnecies inside our sub band then do not calculate the Ref Pout for the entire band.
               if nom_freq < 1200 :
                  if k[0] == 'LB' and done_lb: nom_freq = -1
                  done_lb = True
               else:
                  if k[0] == 'HB' and done_hb: nom_freq = -1
                  done_hb = True

#          print '(add_cal)                         found ->>> ' , nom_freq
           nom_freq_list.append( nom_freq )         

      
#     print "(add_cal) self.freq_sub_band_list", self.freq_sub_band_list
#     print "(add_cal) self.values_dict[ 'Freq(MHz)' ] ", self.values_dict[ 'Freq(MHz)' ]
#     print '(add_cal) nom_freq_list =', nom_freq_list
      

      # 2.
      # For each column name in the nom_match_name_list, go through the values to find the
      # value which most closely matches the nominal value listed in the nom_match_value_list
      
      for i,n in enumerate( nom_colname_list ):
        if n in  self.values_dict:
          vlist = self.values_dict[ n ]
          vcount = self.values_dict_count[ n ]

          try:
             target_value = float( nom_target_value_list[i])
          except Exception:
             # add the first value from the value_dict
             nom_found_value_list.append( vlist[0] )
             continue

          closest_ix = 0
          vdiff      = abs( float( vlist[ closest_ix ]) - target_value )
          for ix, v in  enumerate( vlist ):
             # find the difference between this value and the target value
             # if its less than the current minimum then make this one the new min
             if abs( float( vlist[ ix ] ) - target_value) < vdiff and  vcount[ ix ] > 10:
                  closest_ix = ix
                  vdiff = abs( float( vlist[ ix ] ) - target_value)
                
          nom_found_value_list.append( vlist[ closest_ix ])

      

      print '(add_cal_pout_data) using nominal conditions:',
      for ix, n in enumerate( nom_colname_list):
        if n in  self.values_dict:
#       print '(add_cal_pout_data)     %10s  target=%10s found=%10s' % ( n, nom_target_value_list[ix], nom_found_value_list[ix] )    
           print '%s=%s ' % ( n, nom_found_value_list[ix] ),

      print ''





      # 3.
      # Go through all the records looking for the Power and Efficiency records that match the nominal conditions
      # and save away the vramp pout in a vramp2calpout dict.
      # (if there weren't any, look for PSA test results instead)
    
      self.add_new_column( 'Ref Pout(dBm)' ) 
      self.add_new_column( 'Pwr Variation(dB)' )
      for n in self.rated_power_values:
          self.add_new_column( n )
    
      multi_warn_done = False
      rpc = {}

      for fn, fbl in zip( nom_freq_list, self.freq_sub_band_list ):
         if fn < 0:   continue     # a negative freq signifies that there were no tests found at a freq within the subband
         flw = fbl[1]   # lower freq of the subband  
         fup = fbl[2]   # upper freq of the subband

#        print '(add_cal) doing freq' , fn
         
         vramp2calpout = {}
         for rn in range( rn_start, rn_finish ):
            if self.data['TestName'][rn] == 'Output Power & Efficiency' and self.data['Vramp Voltage'][rn] != None and self.data['Adj Pwr Out(dBm)'][rn] != None :
      
              rn_pout  = self.data['Adj Pwr Out(dBm)'][rn]
              rn_vramp = '%0.3f' % float(self.data['Vramp Voltage'][rn])
              match_found = True
              for ix,n in enumerate( nom_colname_list ) :      
                 rn_val  = self.data[ n ][rn]
                 fnd_val = nom_found_value_list[ix] 
                 if rn_val != fnd_val:
                    match_found = False
                    break
              
              # check that the freq is within limits    
#             if match_found and not (flw <= self.data['Freq(MHz)'][rn] <= fup) :
              if match_found and self.data['Freq(MHz)'][rn] != fn :
                  match_found = False
              
       
              if match_found :
                    if rn_vramp not in vramp2calpout:
                       vramp2calpout[ rn_vramp ] = rn_pout
                    else:
                       if not multi_warn_done:
                          print '*** warning *** multiple power and efficiency tests were run under the same nominal conditions, using the last set of data found'
                          multi_warn_done = 1
                       vramp2calpout[ rn_vramp ] = rn_pout
  

#        for v in vramp2calpout:
#          print '  %10s %15s  %10s %10s' % (fn, fbl, v, vramp2calpout[v])


         # 4. 
         # Go through all the vramp and calpout values looking to see which ones match the target power defined in the self.rated_power_values list
         # New columns will be created which will flag which of the results match the rated_power vramp conditions
         rpc = {}
         rpp = {}
         for n in self.rated_power_values:
            if fn < 1200:  ptarget = self.rated_power_values[ n ][0]
            else:          ptarget = self.rated_power_values[ n ][1]
            
            # find the closest vramp2calpout value to the rated_power value
            # and form a new dict 

            # go through all the vramps and see which one gives the nearest pout to the target power
            # the closest one above the target power wins
            vdiff = None
            for vrmp in vramp2calpout:
                
              calpout = vramp2calpout[ vrmp ]
              if calpout > ptarget : 

                 if vdiff == None or calpout - ptarget < vdiff: 
                   vdiff = calpout - ptarget
                   rpc[ n ] = vrmp
                   rpp[ n ] = calpout
            
            if vdiff == None: rpc[ n ] = None

#        for n, v in rpc.iteritems():
#            print '(add_cal)  freq=%10s  rpc[ %10s ] = %s   rpp[ %10s ] = %10s    ptarget=%10s' % ( fn, n, v, n, rpp[ n ], ptarget  ) 

      # 5.
      # Go through the records a second time filling in all the Ref Pout values
         for rn in range( rn_start, rn_finish ):
        
           # check that the record frequency is with the correct band
           if (flw <= self.data['Freq(MHz)'][rn] <= fup) :
              
              # if so then lookup the the calibrated power for the given vramp
              try:
                 vramp = '%0.3f' % float(self.data['Vramp Voltage'][rn])
                 self.data['Ref Pout(dBm)'    ][rn] = vramp2calpout[ vramp ]
                 self.data['Pwr Variation(dB)'][rn] = self.data['Adj Pwr Out(dBm)'][rn] - vramp2calpout[ vramp ]

                 # if the vramp voltage matches one of the target powers mark the record
                 for n in  rpc:
                     if vramp == rpc[n]:
#                         self.data[ n ][rn] = vramp2calpout[ vramp ]
                          self.data[ n ][rn] = 1
                     else:
                          self.data[ n ][rn] = 0

              except Exception: 
                 self.data['Ref Pout(dBm)'    ][rn] = ''
                 self.data['Pwr Variation(dB)'][rn] = ''
                 for n in  rpc:
                          self.data[ n ][rn] = 0


      self.add_values_dict( 'Ref Pout(dBm)' )
      self.add_values_dict( 'Pwr Variation(dB)' )
      for n in  rpc:
         self.add_values_dict( n )
         if n not in self.value_dict_names:
            self.value_dict_names.append( n )



    ###################################################################
    def add_vramp2pout_data( self, rn_start, rn_finish ):
      ''' Adds new pout column data to records which are not power and efficiency records '''

      # go through all the power and efficiency records andd build a lut to translate vramp voltage to pout 
      # then go through all the power and efficiency records and write the pout data from the lut


      if 'TestName' in self.data  and  'Vramp Voltage' in self.data and  'Output Power & Efficiency' in  self.data['TestName']:

        vramp2pout = {}
        self.add_new_column( 'Adj Pwr Out(dBm)' ) 
        for rn in range( rn_start, rn_finish ):
           if self.data['TestName'][rn] == 'Output Power & Efficiency' and self.data['Vramp Voltage'][rn] != None and self.data['Adj Pwr Out(dBm)'][rn] != None :

           
              ls = [ str(self.data['Vramp Voltage'  ][rn]) , 
                     str(self.data['Process'        ][rn]) , 
                     str(self.data['Vbat(Volt)'     ][rn]) , 
                     str(self.data['Temp(C)'        ][rn]) , 
                     str(self.data['HB_LB'          ][rn]) , 
                     str(self.data['Freq(MHz)'      ][rn]) , 
                     str(self.data['VSWR'           ][rn]) , 
                     str(self.data['Phase(degree)'  ][rn]) , 
                     str(self.data['Pwr In(dBm)'    ][rn]) , 
                     str(self.data['Segments'       ][rn]) , 
                     str(self.data['Regmap'         ][rn]) , ]

              cond = ' '.join( ls )
              
              vramp2pout[ cond ] = self.data['Adj Pwr Out(dBm)'][rn]


        for rn in range( rn_start, rn_finish ):
           if self.data['TestName'][rn] != 'Output Power & Efficiency' and self.data['Vramp Voltage'][rn] != None :
         
              ls = [ str(self.data['Vramp Voltage'  ][rn]) , 
                     str(self.data['Process'        ][rn]) , 
                     str(self.data['Vbat(Volt)'     ][rn]) , 
                     str(self.data['Temp(C)'        ][rn]) , 
                     str(self.data['HB_LB'          ][rn]) , 
                     str(self.data['Freq(MHz)'      ][rn]) , 
                     str(self.data['VSWR'           ][rn]) , 
                     str(self.data['Phase(degree)'  ][rn]) , 
                     str(self.data['Pwr In(dBm)'    ][rn]) , 
                     str(self.data['Segments'       ][rn]) , 
                     str(self.data['Regmap'         ][rn]) , ]

              cond = ' '.join( ls )
              
              if cond in vramp2pout:
                   pout = vramp2pout[ cond ] 
                   self.data['Adj Pwr Out(dBm)'][rn] = pout


    ###################################################################

    def add_spurious_data( self, freq_thres=None ):

        ''' Create new data columns flattenning the spurious data'''


        # hamonic amplitude
        # we want to null out any spurs that are really harmonics.
        # we do this by redefining the amplitude of the spur as a low value
        
        #self.harmonic_freq_thresh = 50.0   # (MHz)  # any frequency which is less than this value from a harmoinic is categorized as a harmonic and will be nulled

        if freq_thres != None:
            cname = 'Amplitude of Spur, no harmonic %sMHz (dBm)' % freq_thres
        else:
            cname = 'Amplitude of Spur, no harmonic {spur_filter_table}MHz (dBm)'

        self.add_new_column( cname )

        num_spurtests = 0
        num_spurs_det = 0
        for rn in range( self.datacount ):

           num_spurtests += 1

           if self.data['TestName'][rn] == 'Spurious (ETSI reduced)':
              freq = self.data['Freq(MHz)'][rn]

              self.data[ cname ][rn] = 0

              if  type( self.data['Frequency of Spur (MHz)'][rn] ) != types.ListType : continue

              self.data[ cname ][rn] = []



              for f,amp in zip( self.data['Frequency of Spur (MHz)'][rn], self.data['Amplitude of Spur (dBm)'][rn] ):
                  harmonic_float  = float(f)/float(freq)
                  harmonic_int    = int( harmonic_float + 0.5 )
                  harmonic_dist   = harmonic_float - harmonic_int
                  freq_dist       = freq * abs( harmonic_dist )

                  if freq_thres == None:
                     freq_thres = self.get_spur_freq_thres_from_table( freq, harmonic_int )

                  num_spurs_det +=1

                  if freq_dist < freq_thres:
                     amp = self.harmonic_spur_min_amp
                     amp = None

                # print 'freq = %10s   %10s  %10s  harm= %20s  dist = %20s' % ( freq, f , amp , harmonic_float, freq_dist )

                  self.data[ cname ][rn].append( amp )
                 
           
    ###################################################################

    def get_spur_freq_thres_from_table( self, freq, harmonic_int ):

        # load the spur filter table if not already done
        if self.spur_freq_filter_table == {}: 

            file2open = 'spur_freq_threshold_table.csv'
            
            try: 
                f = open(file2open, "rb")              # don't forget the 'b'!
            except  Exception:
                print "*** ERROR *** cannot read spur filter file: '%s'" % file2open
                return 0

            reader = csv.reader(f)
            column_headers = reader.next()

            # get rid of any leading and trailing spaces from the column headers
            ctn = []
            for c in column_headers:
               ctn.append( c.strip() )
            column_headers = ctn
          

            # go through each valid row, and go through ead field in the row
            # use the first field (column 0) as the row_header, and the column_header  name as the key for the dictionary.
            row_headers = []
            for row in reader:
               if len(row) >= len(column_headers):
                  row_header = row[0].strip()
                  row_headers.append( row_header )
                  for fldi in range( 1,  len(row) ):
                      fld = row[fldi].strip()
                      self.spur_freq_filter_table[  str( column_headers[ fldi ] ) + ' ' + str( row_header ) ]  = fld
               

            self.spur_freq_filter_table_flist = column_headers
            self.spur_freq_filter_table_hlist = row_headers

            print '\n---------------------------------------------------------------------------'
            print "Spurs frequency threshold table from file '%s'" % file2open
            
            #print 'Harmonics   :' , row_headers
            print '\nFreq :' , column_headers

            #pprint( self.spur_freq_filter_table )

            for r in row_headers:
               print '            %2s : ' % r ,
               for c in column_headers[1:]:
                  key  =   str(c) + ' ' + str(r)
                  print ' %5s' % self.spur_freq_filter_table[ key ],
               print ''
            print '---------------------------------------------------------------------------\n'


        # find out which is the closest spur_freq_filter_table frequency to the fundamental freq

        f_idx = self.get_nearest_value_from_list(  self.spur_freq_filter_table_flist, freq )
        h_idx = self.get_nearest_value_from_list(  self.spur_freq_filter_table_hlist, harmonic_int )

        
        key = str(  self.spur_freq_filter_table_flist[ f_idx ] ) + ' ' + str( self.spur_freq_filter_table_hlist[ h_idx ] )

        if key in self.spur_freq_filter_table:
            rv = float(  self.spur_freq_filter_table[ key ] )
            #print '(get_spur_freq_thres_from_table)  fund_freq=%s, harmonic=%s,  spur_filter=%s' % ( freq, harmonic_int, rv )
            return rv


        print '*** ERROR *** (get_spur_freq_thres_from_table) could not find matching value for freq=%s, harmonic=%s <%s>' % ( freq, harmonic_int , key )

            

            
           

              
    
    
    ###################################################################

    def get_nearest_value_from_list( self, ilst, value ):
        ''' Find the value in the list which is closest to the value, and return the index ''' 

        value = float( value )

        mindiff = 1e6
        minv    = 1e6

        mini = None
        for i in range( 0, len( ilst ) ):
           try: 
              v = float( ilst[i] )
           except Exception:
              continue


           #print  ' value=%s  i=%s  v=%s   mini=%s   minv=%s  abs(minv-value)=%s  <  mindiff=%s'  % (value, i , v , mini, minv, abs(minv-value), mindiff)

           if mini==None or  abs( v - value ) < mindiff :  
               #print  ' -->> NEW MIN'
               mini     = i
               minv     = v
               mindiff  = abs( v - value )


        #print ' finding the nearest value ', ilst, value, '-->>', ilst[ mini ], mini


        return mini






    ###################################################################

    def add_new_column( self, name ):

          # Create a new data name if it doesnt already exist
          if not name in self.data:
            self.data[name]      = []

          # Then extend the data to be the current datacount length
          # extend it with empty None values
          rn_sum = self.datacount - len( self.data[name] )
          self.data[name]   .extend( [None] * rn_sum )
        
    ###################################################################


    def nearest( self, num , roundnum, default ):
    
#       print '(nearest)', num, type(num), roundnum, default 

        if not num : return default

        try: 
           num = float(num)
        except Exception:
           return default

        if num > 0: m = 1
        else:        m = -1
        return int(( abs(num) / float(roundnum) ) + 0.5 ) * int(roundnum) * m
        
    ###################################################################
      
    
    def is_condition_match( self, cond, rercord_num ):
      return 1
    
    
    ###################################################################
#   def update_filter_conditions( self, name, values=None, oper='=' ):
    def update_filter_conditions( self, name, values=None, tolerance=None ):
    
    
      # if values is None then remove the filter name completely
      # else look for name in existing filter_conditions and change the entry for the filter
      # if the name does not exist add it to the end.
    


    
      if name not in self.data:
         print '*** ERROR *** (update_filter_conditions) name %s not a recognised column name in the logfile' % name
    


      if values == None:
        # loop through looking for any filter conditions which have the same name
        new_filter_conditions = []
        for c in self.filter_conditions:
           if c[0] != name:  new_filter_conditions.append( c )
        self.filter_conditions = new_filter_conditions[:]
        return
    
      if tolerance != None:  tolerance = float(tolerance)
    
      values = self.expand_filter_condition_values( name, values )

      # we need to replace or add a new condition
      new_c = [name, tolerance ]
      if type( values) == types.ListType  :
         for v in values:
            
            new_c.append( v )
      else:
         new_c.append( values )
    
    
      for i in range(len(self.filter_conditions)):
         c = self.filter_conditions[i]
         if c[0] == name:  
            self.filter_conditions[ i ] = new_c
            return
    
      self.filter_conditions.append( new_c )
      

    
      return
    
    
    ###################################################################
#   def update_filter_conditions( self, name, values=None, oper='=' ):
    def get_filter_conditions( self, name ):
    
    


    
      if name not in self.data:
         print '*** ERROR *** (get_filter_conditions) name %s not a recognised column name in the logfile' % name
    


      retval = None
      for c in self.filter_conditions:
         if c[0] == name:  retval = c[2]

      return  retval
    
    
    ###################################################################
    def expand_filter_condition_values( self, name, values ):
        ''' Take 'values' (which may be a single value or a list) and look for a '..' range string 
            between two numbers. If found it will take the range of the two numbers and look for all
            values in the vaules_dict that fall within the range '''

#       print '(expand_filter_condition_values) doing  ', name , values
        vl = None
        if type(values) == types.ListType:
           vl = []
           for v in values:
             if type(v) == types.StringType :
               grps = re.search( r'([0-9\+\-\.]+)\.\.([0-9\+\-\.]+)',v) 
               if grps:
                 r1 = float( grps.groups()[0] )
                 r2 = float( grps.groups()[1] )
#                print '(expand_filter_condition_values) found range list', values, r1, r2
                 
                 if name not in self.values_dict:  self.add_values_dict( name )

#                print '(expand_filter_condition_values)  values_dict[ %s ] = %s' % ( name, self.values_dict[ name ] )
                 for vd in self.values_dict[ name ]:
                    if r1 <= float(vd) <= r2:
                       vl.append( vd )
#                print '(expand_filter_condition_values)  returning', vl
                 
               else:
                 vl.append(v)
             else:
               vl.append( v )
                       
        else:
             if type(values) == types.StringType :
               grps = re.search( r'([0-9\+\-\.]+)\.\.([0-9\+\-\.]+)',values) 
               if grps:
#                print '(expand_filter_condition_values) found range ', values, r1, r2
                 r1 = float( grps.groups()[0] )
                 r2 = float( grps.groups()[1] )
                 if name not in self.values_dict:  self.add_values_dict( name )
                 
                 vl = []
                 for vd in self.values_dict[ name ]:
                    if r1 <= float(vd) <= r2:
                       vl.append( vd )
               else:
                 vl = values
             else:
               vl = values
                       
                   

        return vl
             

    ###################################################################
    def print_values_list( self ):
       # print out a list of different values for each of the series_conditions
    
    
       print "\nThe logfiles have the following parameters swept:"

       for sc in self.value_dict_names_original_list:
                 
          swept_val = {}
          swept_val_lst = []
          if sc in self.data: def_sc = 1; len_sc = len(self.data[sc])
          else         : def_sc = 0; len_sc = 0
         
          print "    %-15s:" % sc, 
          if sc in self.data:
            for rn in range(self.datacount):
                val = self.data[sc][rn]
                if val in swept_val:
                    swept_val[ val ] += 1
                else:
                    swept_val[ val ] = 1
                    swept_val_lst.append( val )
#         self.values_dict[ sc ] = []
          if len(swept_val_lst) >= 1:
            for n in swept_val_lst:
              print "%s(%d)" % (n, swept_val[n]), 
#             self.values_dict[ sc ].append( n )
          print ""
       print ""
    
#      self.values_dict = values_dict


       
    ###################################################################

    def add_filter_conditions( self, conditions=None ):

       #--------------------------------------------------------------------
       # Go through the conditions and split them into two lists, one for the seires and another for the filter
       # while we are at it check that the condition names are correct and are present in the logfile as column header names
       #--------------------------------------------------------------------

       if conditions != None:

           self.series_conditions = []
           self.filter_conditions = []
           name_error = 0
           testname = ''
           for c in conditions:
             if type(c) == types.StringType  :
               if not c in self.data:
                  print "*** ERROR (select_data) bad conditions list!, name <%s> is not a named column in the logfile" % c
                  name_error = 1
               self.series_conditions.append( c )
             if type(c) == types.ListType    :
               if len(c) < 3 :
                  print "*** ERROR (select_data) bad condition list!, filter list %s must have 3 values, e.g. ['Vbat(V)', '=', 4.5]" % c
               if c[0] not in self.data:
                  print "*** ERROR (select_data) bad conditions list!, filter name <%s> in <%s> is not a named column in the logfile" % (c[0], c)
                  name_error = 1
               if c[1] != '=':
                  print "*** ERROR (select_data) bad conditions list!, filter operator <%s> in <%s> must be '=', e.g.['Vbat(V)', '=', 4.5]" % (c[1], c)
                  for name in self.data:  print name
                  
               self.filter_conditions.append( c )
               
        
           if name_error: self.print_column_list()
    

    ###################################################################

    
    def select_data( self, conditions, xname ):
       '''Looks through data dictionary and returns a list of series which meet the filter conditions.
          Each series is a list of record numbers.
          There may be multiple sets of data which meet the same filter conditions, records that meet the
          filter_conditions but differ in the series_conditions are returned in separate series lists.
          The intent is that each series list is ploted on the same graph.
       '''
    


       self.add_filter_conditions( conditions )

       do_values_dict = False

       self.values_selected_dict = {}
       for vdn in self.value_dict_names:
         self.values_selected_dict[ vdn ] = []



       #--------------------------------------------------------------------------------
       # Create a new full series list. This takes the original series list and prepends it with 
       # the names of the gui color select name and the gui line select name
       #--------------------------------------------------------------------------------


       full_series_conditions = []
       series_conditions_done = {}


       # Break up the selected data into series using the color series name ands the line series name as filters.
       try: 
         n = self.color_series.get()
         if n != '' and n != 'None' :
           series_conditions_done[ n ] = 'done'
           full_series_conditions.append( n )

       except Exception:
         pass


       try: 
         n = self.line_series.get()
         if n != '' and n != 'None' :
           if not n in series_conditions_done:
                 series_conditions_done[ n ] = 'done'
           full_series_conditions.append( n )

       except Exception:
         pass


#      for sc in self.series_conditions:
#         print '(select_data) adding series_conditions onto  full_series_conditions', sc 
#         if sc not in series_conditions_done:
#                series_conditions_done[ sc ] = 'done'
#                full_series_conditions.append( sc )


       # Split the data based on the standart parameter sweep names, this will ensure that there will be separate lines for each condition
       # Except if we are doing Frequency of Spur plot then don't split it up!
       if xname != 'Frequency of Spur (MHz)':     

         for sc in self.value_dict_names:
            if sc != xname and sc in self.series_seperated_list and sc != 'Vramp Voltage':
               if sc not in series_conditions_done:
                   series_conditions_done[ sc ] = 'done'
                   full_series_conditions.append( sc )





       # full_series_conditions is a list of all the filter conditions plus the color and line series


       #--------------------------------------------------------------------
       # go through all the records in the data dictionary, and create new lists of record numbers
       # which match the filter_conditions and create separte lists for each series_condition
       #--------------------------------------------------------------------
    
    
       #print '  series data = ', self.series_conditions
       print '  filter conditions :'
    
       dcx = 0
       series_unique_name2num = {}
       series_count  = 0
       series_values = []
       series_data   = []
       for rn in range(self.datacount):
         record_good = True
    
         # Check to see if the filter conditions are all met
         for fc in self.filter_conditions:
           name = fc[0]
           oper = fc[1]
           tolerance = oper
           values = fc[2:]
    
           value_good = False
           if name in self.data:
             for value in values: 
    
#              if self.data[ name ][rn] == value :     # look out for this! - the filter 'value' might not be of the same type as the data dictionary value.
               if self.compare_values( self.data[ name ][rn] , value, tolerance ):     # look out for this! - the filter 'value' might not be of the same type as the data dictionary value.
                 value_good = True                # any value which matches in the filter list is enough - its an OR function

                 break

             if value_good == False:              # if the value doesnt match then this record is no good
               record_good = False
               break


         if do_values_dict:
             for vdn in self.value_dict_names:
                   try:
                     x = self.values_dict[ vdn ].index( self.data[vdn][rn] ) 
                   except Exception:
                     self.values_dict[ vdn ].append(  self.data[vdn][rn] ) 



         
         if record_good:
             for vdn in self.value_dict_names:
                   try:
                     x = self.values_selected_dict[ vdn ].index( self.data[vdn][rn] ) 
                   except Exception:
                     self.values_selected_dict[ vdn ].append(  self.data[vdn][rn] ) 
    
            



         if record_good == False: continue
    

         dcx += 1
         #print 'good record', dcx,  self.data[ 'VAM(volt)' ][rn] , self.data[ 'Adj Pwr Out(dBm)' ][rn], ';'


         

         #--------------------------------------------------------------------
         # Go through the series_conditions looking for unique set of values.
         # If unique then create a new series, if not then add to the existing series
         #--------------------------------------------------------------------

         
    
         series_name = ''
         for sc in full_series_conditions:
           name = sc
           value = self.data[ name ][rn]
           value_str = str( value )
           series_name = series_name + '@' + value_str
    
         if series_name not in series_unique_name2num:
             series_unique_name2num[ series_name ] = series_count
             series_values.append( series_name )
             series_data.append( [] )
             series_num = series_count
             series_count = series_count + 1
         else:
             series_num = series_unique_name2num[ series_name ]
    
             
         series_data[ series_num ].append( rn )


       self.create_values_dict()
    


       #--------------------------------------------------------------------
       # Go through all the series_values and create a new list of series values which have unique values
       #--------------------------------------------------------------------
    
       series_unique_name_value_str, series_unique_values, series_unique_names  = self.get_unique_series_names( full_series_conditions, series_values)



       for fc in self.filter_conditions:
              count = 'This column name is not in the logfile'
              name = fc[0]
              oper = fc[1]
              tolerance = oper
              values = fc[2:]
              count = 0
              if name in self.data:
                for rn in range(self.datacount):
                  for value in values: 
                    if self.compare_values(self.data[ name ][rn], value, tolerance) :    
                     count += 1            
              print '       name= %-15s values= %-30s match_count= %d' % (name, values, count)


    
       if len(series_data) == 0 :
            print "*** ERROR (select_data) no data was found in the logfile that matches the filter conditions"   
            return [],[],[],[],[]
       else:
            tot_record_count = 0
            for lst in series_data:
               tot_record_count += len(lst)
            print "  .(select_data) found %d series with %d individual measurement values that match all the filter conditions" % ( len(series_data), tot_record_count)


    
    
       return series_data, series_values, series_unique_name_value_str, series_unique_values, series_unique_names
    

    ########################################################################
    def compare_values( self, val1 , val2, tolerance=None ):     

         if val1 == val2: return 1

         try:
           v1 = float( val1 )
           v2 = float( val2 )
#          if 3.7 > v1 > 3.5 : print '(compare_values)', v1, v2 
           if tolerance == None:
               tolerance = 0.001

           if abs( v1 - v2 ) < tolerance : 
#               if 3.7 > v1 > 3.5 : print '( = ) ********************** Matched !!!!'
                return 1

                
         except Exception:
           pass

#        if type( val2 ) == types.BooleanType and val2 == True:
#            print '(compare_values) found true', val1
#            if not ( val1 == None or val1 == '' or val1 == NaN ):  
#            if val1 > 30:
#               print '(compare_values) found true and val1 =', val1 
#               return 1

         return 0

      
          
    ########################################################################
    def get_unique_series_names( self, series_cond, series_values):
       ''' go through all the series_values and create a new list of series values which have unique values'''
    
       series_unique_name_value_str  = []   # a list of unique names and values that will be prited on the graph legend
       series_unique_values          = []   # a list of lists with the values for each series
       series_unique_names           = []   # a list of unique parameter names
       ignore_lst = []


       for sci in range(len(series_cond)):
         count = 0
         valdict = {}
         for sv in series_values:
           vals = sv.split('@')
           val = vals[sci+1]
           if val in valdict:
             valdict[ val ] += 1
           else:
             count += 1
             valdict[ val ] = 1
    
         ignore_lst.append(count)
       
       
       for sci in range(len(series_cond)):
         if ignore_lst[sci] > 1:
           series_unique_names.append( series_cond[sci] )
    
    
       for sv in series_values:
         vals = sv.split('@')
         unique_name = ''
         unique_value_list = []
         for sci in range(len(series_cond)):
           if ignore_lst[sci] > 1 :
             val = vals[sci+1]
             name = self.truncate_name( series_cond[sci] )
#            unique_name = unique_name + name + '=' + self.truncate_value( val ) + ' '
             
             if name=='sn' :
               val = re.sub(r'.*([sS][nN]\d+)[_ ]?.*', r'\1', val, re.I )

             unique_name = unique_name  + self.truncate_value( val ) + ' '

             unique_value_list.append( val )
         series_unique_name_value_str.append( unique_name )
         series_unique_values.append( unique_value_list )
    
       return series_unique_name_value_str, series_unique_values, series_unique_names
            
    ########################################################################          
    def truncate_name( self,  name ):
    
      namel = name.lower()
      if    namel == 'Test Freq(MHz)'.lower() : name = 'Freq'
      elif  namel == 'Freq(MHz)'     .lower() : name = 'Freq'
      elif  namel == 'Segments'      .lower() : name = 'Seg'
      elif  namel == 'HB_LB'         .lower() : name = 'Band'
      elif  namel == 'logfilename'   .lower() : name = 'Logfile'
      elif  namel == 'Vramp Voltage' .lower() : name = 'vramp'
      elif  namel == 'TestName'      .lower() : name = 'test'
      elif  namel == 'Vramp Release' .lower() : name = 'vramp rel'
      elif  namel == 'Vramp Filebase' .lower() : name = 'vramp file'
      elif  namel == 'Part Number (Chip ID)' .lower() : name = 'chip'
      elif  namel == 'Serial Number' .lower() : name = 'sn'
      elif  namel == 'Temperature Soak Time (in secs)' .lower() : name = 'Temp'
    
      return name
    
    
      
    ########################################################################
    def truncate_value( self, value ):
    
      try:
        # remove the directory root if the text is too long
        if len(value) > 10:
           value = re.sub( r'.*/', '', value )
           value = re.sub( r'.*\\', '', value )
        value = re.sub( r'\.0+$', '', str(  '%0.2f' % value ) )
    
      except Exception:
        pass
    

      return value


    ########################################################################
    def simplify_keysym( self, value ):
        
         ''' Get a consistent name for the key that was pressed ie Control_L -> control , Alt_R -> alt , Shift_L -> shift '''

         if value == None : return None

         value = re.sub( r'_[LR]$', '', value )
         value = value.lower()
         return value
      
    ########################################################################
    def get_sub_series( self, xname, s ):
    
         # scan through all the xvalues, get the min and max values, and the range
         # find the main increase or decrease
    
    
         if xname not in self.data: return []
         
         # dont try to split up time series data
         if re.search('^\[Time\]', xname ) : return [s[:]]


         imin = imax = None
 
         islist = False
         do_split = True
         dold = None
         pos_inc = neg_inc = 0
    



         for i in s:
           d =  self.data[ xname ][i] 



           if type(d) == types.NoneType or type(d) == types.ListType or (type(d) == types.StringType  and  ( d.lower() == 'nan' or d == '')): 
                do_split = False
                continue

           try: 
              d = float( d )
           except Exception:
              print '*** ERROR *** (get_sub_series) data not a number data[%s][%i] = <%s><%s>, (Line %s)' % ( xname, i, d, type(d), self.data[ 'linenumber' ][i] )
              continue

           if dold == None : dold = d
           if imin == None   or   d < float( self.data[ xname ][imin])  : imin = i
           if imax == None   or   d > float( self.data[ xname ][imax])  : imax = i
    
           # look at the increment of the x value, count the number of positive increments and the number of negative increments
           if d != None and dold != None: 
             if d - dold > 0.0  : pos_inc +=1
             if d - dold < 0.0  : neg_inc +=1
    



           dold = d

           
         if pos_inc > neg_inc: inc =  1
         else:                 inc = -1
    
        #print '(get_sub_series) xname,imin,imax,inc = ', xname, imin, self.data[xname][imin], imax, self.data[xname][imax], inc
    
         if do_split :  rng = float(self.data[xname][imax])  -  float(self.data[xname][imin])
    
        #print '(get_sub_series) neg_in= %s, pos_inc= %s, inc= %s, rng= %s' % ( neg_inc, pos_inc, inc, rng )
    


         # now we know which direction the xaxis values are going, we can break the full list into
         # sub-lists where all the xvalues increment in the same direction. 
    
         vold = None
         snew = []
         snum = 0
         snew.append( [] )
         for i in s:
            v = self.data[xname][i] 
            if type(v) == types.NoneType or (type(v) == types.StringType  and  v.lower() == 'nan'): continue

            # if we have a list then plot don't try and split it just add it to the series

            
            if do_split == False :
                snew[snum].append(i)
                continue

            v = float( v )

            if vold == None : vold = v

            if (v - vold) * inc * -1  > 0.5 * rng :    # if the delta is greater than half the range then start a new series
               snum += 1
               snew.append( [] )
               
            snew[snum].append(i)
            vold = v
    
         return snew
        
    ########################################################################
    
       
    def get_data( self, xynames, conditions=[] ):
       '''Looks through the data dictionary looking for all records that have data in all the xnames, ynames fields,
          records also have to meet all the conditons. Where multiple sets of data are found
          it returns a list of series which have differing conditions 
    
          get_data = [ series1, series2, ... seriesN ]
    
          seriesN =  [ unique_conditions, selection_conditions, xvals, yvals ]
    
          unique_conditions = [ condition1, condition2, ... conditionN ] 
    
          selection_conditions = [ condition1, condition2, ... conditionN ] 
    
          conditionN = [ data_name , operator_str, data_value ]
    
          xvals = [ vals1 , vals2, ... valsN ]
    
          yvals = [ vals1 , vals2, ... valsN ]
    
          valsN = [ [name] , [ value1, value2, ... valueN ]
    
          name = column_name or name of the value
    
          valueN = value of measured quantity
       '''
    
    
       xy = []
       for i in range(0,len(xynames)) :
         xy.append( [] )
    
    
       # go through each record looking to see if the xnames and ynames fields exist and whether the records match the selection
       # criteria
    
       for rn in range( 0, self.datacount) :
    
         # check that the data is present 
    
         good_record = 1
         for  n in xynames :
           d = self.data[ n ]
           if d[ rn ] == None : good_record = 0
    
         if good_record == 1 :
           for  c in conditions :
             if self.record_match( c , r ): good_record = 0
      
         if good_record == 1 :
             
           # this is a good record we want to add it to the output data
    
           # for each xynames create a separate list 
           for i in range(0, len(xynames)) :
              d = self.data[ xynames[i] ]
              xy[ i ].append( d[rn] )
              
         
       return xy
    
    ###################################################################
    
    def get_minmax( self, lst ):
    
      min = lst[0] + 0.0
      max = lst[0] + 0.0
      for v in lst:
        if v > max: max = v
        if v < min: min = v
    
      return min,max
    
    ###################################################################
    def get_minmax_idx( self, lst ):
    
      min = lst[0]
      max = lst[0]
      idx_min = 0
      idx_max = 0
      i = 0
      for v in lst:
        if v > max:
            max = v
            idx_max = i
        if v < min:
            min = v
            idx_min = i
        i = i+1
      return idx_min,idx_max
    
    ###################################################################
    def annotate_polar_val( self, str, idx, txtx, txty ):
    
      #n = self.xydata[1][idx]
      n = round( self.xydata[3][idx], 2 )
      str = str + "\n(%d, %0.2f)" % (self.xydata[0][idx], n)
    
      annotate( str, xy=( self.xydata[0][idx]*2*pi/360.0 , self.xydata[1][idx] ),
                   xytext=(txtx, txty),  textcoords='figure fraction', 
                    arrowprops=dict(facecolor='black', shrink=0.02,width=0.1,headwidth=4, alpha=1),
                    horizontalalignment='left', verticalalignment='bottom',fontsize=10)
    
    ###################################################################
    def annotate_figure( self, str, txtx, txty ):
    
      if str == '': return
      annotate( str, xy=(txtx, txty),  textcoords='figure fraction', 
                    horizontalalignment='left', verticalalignment='bottom', fontsize=10)
    
    ###################################################################
    
    
    def deg2rad( self, lip ):
      lop = []
      for i in lip:   lop.append( i * 2*pi/360.0 )
      return lop
    ###################################################################
    def get_unique_vals( self, lip ):
    
      lop = []
      for i in lip:
        if type(i) == types.IntType or type(i) == types.FloatType:
          ir = round(i, 2)
        else:
          ir = i
        if ir not in lop: lop.append(ir)
    
      return lop
    ###################################################################
    def get_vramp_voltage( self, filename ):
    
      x = re.search( r'\.(\d\.\d+)v_ramp.txt', filename )
      if x :
           n = x.groups()
           return n[0]
      else :
           return ''
        
    ###################################################################          
    def get_vramp_filebase( self, filename ):
    
      x = re.search( r'.*\\(.*?_ramp.txt)', filename )
      if x :
           n = x.groups()
           return n[0]
      else :
           return ''
          
    ###################################################################
    def get_vramp_filename_data( self, rn ):


      # full_filespec = 'P:\\mike_askers_stuff\\ramps\\LBpwrsel11\\staircase-128us_ramp.txt'
      # full_filespec = 'L:\Testing\Chiarlo_EDGE\EDGE_sources\ATR_LB\EDGELB29_vam.wv'
      # full_filespec = 'G:\ATR_Classico\Ramp_files\ramps_classicoV6_9Jul08\LB_pwrsel00\classicoV6.1.50v_ramp.txt'
      #
      #      vramp_release, hb_lb, seg, voltage, full_filespec, pcl_level = self.get_vramp_filename_data( filename )

      full_filespec = ''
      pcl_level     = ''

      if 'Vramp Dir1' in self.data and self.data['Vramp Dir1'][rn] != '':
         full_filespec =     self.data['Vramp Dir1'][rn] +   self.data['Vramp Dir2'][rn] +  self.data['Vramp Dir3'][rn] + self.data['Vramp File'][rn] 

      elif  'Vramp File' in  self.data and  self.data['Vramp File'][rn] != '':
         full_filespec = self.data['Vramp File'][rn] 

      #print '(get_vramp_filename_data)' , full_filespec
    
      x = re.search( r'(ramps_[^\\]+)?\\(LB|HB)?_?pwrsel([01]+)?.*?(\d\.\d+)?v?_ramp.txt$', full_filespec, re.I )
      if x :
           n = x.groups()
           nl = list(n)
           nl.append( full_filespec )
           nl.append( '' )
           return nl
      else :

           # search for vw pcl level files 

           x = re.search( r'(.*)\\EDGE(LB|HB)(\d+)_vam.wv$', full_filespec, re.I )
           if x :
                n = x.groups()
                return n[0], n[1], '', '', full_filespec, n[2]

           # so we didn't get everything we wanted from the ramp full_filespec path, lets get what we can!

           # start with the HB/LB 
           x = re.search( r'(LB|HB)_?pwrsel([01]+)', full_filespec, re.I )

           
           #print '*** ERROR *** (get_vramp_filename_data) could not get info from vramp filename', filename

           if x :
              return '', x.groups()[0],  x.groups()[1], '', full_filespec, pcl_level

           else:

              x = re.search( r'\\(LB|HB)(\d)seg\\', full_filespec, re.I )

              if x :
                 return '', x.groups()[0],  x.groups()[1], '', full_filespec, pcl_level
              

      return '','','','', full_filespec, ''
    
    
    ###################################################################
    def get_filename_from_fullpath( self, filename ):
    
       return re.sub(r'.*(\\|/)','', str( filename ) )
    
    

    ###################################################################      

    def wadd_vam_pout_columns(self):


        vof = self.vam_offset_entry.get()

        if vof == '' :  
               self.vam_offset_entry.set( self.vam_offset )
        else:
               self.vam_offset = float( vof )


        if self.dist_logfilename.get() == None or self.dist_logfilename.get() == 'None' :

           print '... Adding Distortion Reference data based on CONDITIONS'
           self.add_vam_pout_columns( self.dist_temp.get() , \
                                      self.dist_freq.get() , \
                                      self.dist_vbat.get() , \
                                      self.dist_pin.get()  , \
                                      self.dist_seg.get() , \
                                      self.dist_hblb.get() , \
                                      self.dist_process.get() )
        else:
         
           print '... Adding Distortion Reference data based on Logfile ' , self.dist_logfilename.get()
           self.add_distortion_variation(self.dist_logfilename.get(),  \
                                       self.dist_temp.get() , \
                                       self.dist_freq.get() , \
                                       self.dist_vbat.get() , \
                                       self.dist_pin.get()  , \
                                       self.dist_seg.get() , \
                                       self.dist_hblb.get() , \
                                       self.dist_process.get() )
                                  
         
    ###################################################################      

    def add_distortion_variation(self, ref_logfilename=None, ref_temp=None, ref_freq=None, ref_vbat=None, ref_pin=None, ref_seg='*', ref_hblb=None , ref_process=None) :
       ''' Calculates the distortion variation data, by taking the reference data from the ref_logfilename, it must also match all the other conditions. 
           It will then calculate the variation by comparing the gain and phase slope data against the reference gain and phase slopes.'''


        
       err = False

       # check we have a valid reference logfile name
       if ref_logfilename == None:
           ref_logfilename = self.dist_logfilename.get()
           if ref_logfilename == None:
              print '*** ERROR *** (add_distortion_variation) No reference logfilename was entered, therefore distortion variation cannot be calculated'
              err = True

       print "\n...using the data in logfile '%s' as the reference data for calculating distortion variation" % ref_logfilename

       self.ref_logfilename = ref_logfilename

       # check that the right data is available to calculate variation
       for n in [ 'Gain AM/(VAM-offset) (dB)', 'Gain AM/(VAM-offset) Slope (dB/dB)',  'AM-PM Slope (deg/dB)' ]:
           if n not in self.data:
               print "*** warning *** (add_distortion_variation) missing data column '%s', This Column was not found and is required to calculate distortion variation" % n

       


       #  Look through all the data recored and find the start and finish  of the reference data 
       #   that is data records which match the ref_logfilename, and also match the conditions  (when provided)

       compare_reference_names  = [ 'Temp(C)', 'Freq(MHz)', 'Vbat(Volt)', 'Pwr In(dBm)', 'Segments', 'HB_LB', 'Process' ]
       compare_reference_values = [ ref_temp,   ref_freq,          ref_vbat,      ref_pin,      ref_seg,  ref_hblb, ref_process ]

       fnd_logfile = False
       rn_ref_st = None
       for rn in range( 0 ,  self.datacount ): 
           if self.data[ 'logfilename' ][rn] == ref_logfilename:
               fnd_logfile = True
               if self.compare_conditions( rn, compare_reference_names, compare_reference_values):
                  if rn_ref_st == None : rn_ref_st = rn
                  rn_ref_fn = rn
        
       # Error if we dont find the reference data
       if not fnd_logfile :
               print "*** ERROR *** (add_distortion_variation) No reference data was found that matches the reference logfile name '%s'" % ref_logfilename
               err = True
       else:
          if rn_ref_st == None:
               print "*** ERROR *** (add_distortion_variation) No reference data was found that matches the conditions", compare_reference_names, compare_reference_values
               err = True

       if err : return



       # Go through all the data and compare the gain and phase slopes with the refererence data gain and phase slopes.

       self.add_new_column( 'Gain AM/(VAM-offset) Slope - Ref (dB/dB)'                 )
       self.add_new_column( 'Gain AM/(VAM-offset) Slope - Ref (dB/dB) <emp-limits>'    )
       self.add_new_column( 'AM-PM Slope - Ref (deg/dB)'                               )
       self.add_new_column( 'AM-PM Slope - Ref (deg/dB) <emp-limits>'                  )

       for rn in range( 0 ,  self.datacount ): 
          if self.compare_conditions( rn, compare_reference_names, compare_reference_values):
             pwr = self.data[ 'Adj Pwr Out(dBm)' ][rn]                                                                                            #                   xi            x , y,  refst,reffn
             self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB)' ][rn] =  self.data[ 'Gain AM/(VAM-offset) Slope (dB/dB)' ][rn]  - self.interpolate_data(   pwr,  'Adj Pwr Out(dBm)', 'Gain AM/(VAM-offset) Slope (dB/dB)', rn_ref_st, rn_ref_fn)
             self.data[ 'AM-PM Slope - Ref (deg/dB)'      ][rn]          =  self.data[ 'AM-PM Slope (deg/dB)'      ][rn]           - self.interpolate_data(   pwr,  'Adj Pwr Out(dBm)', 'AM-PM Slope (deg/dB)'              , rn_ref_st, rn_ref_fn)
             self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB) <emp-limits>' ][rn]  =  self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB)' ][rn]
             self.data[ 'AM-PM Slope - Ref (deg/dB) <emp-limits>'      ][rn]   =   self.data[ 'AM-PM Slope - Ref (deg/dB)'      ][rn] 

  
    ###################################################################      
    def interpolate_data( self, xi, xname, yname, rn_st, rn_fin ):
       ''' Calculates a Yi value for a given Xi by interpolating the X and Y data provide by the xname and yname. 
           xname and yname data is searched searched between the rn_st and rn_fn values'''

       x = array( self.data[ xname ][rn_st:rn_fin] )
       y = array( self.data[ yname ][rn_st:rn_fin] )

       [yi] = stineman_interp([xi],x,y)

       return yi


    ###################################################################      
    def compare_conditions( self, rn, compare_reference_names, compare_reference_values):
       ''' Compares the record rn with the conditions provided by compare_reference_names and compare_reference_values.
           If the value is compare_reference_values is none then the match is true, ie it matches on missing data'''

       match = True

       for i in range( len(compare_reference_names) ):
          name      = compare_reference_names[ i ]
          ref_value = compare_reference_values[ i ]

          if name in self.data:
             v = self.data[ name ][rn]
#            print 'name=%15s   ref_val=%15s   rn=%3d   v=%15s' % (name, ref_value, rn, v ),
             if ref_value != None and ref_value != '*' and v != ref_value : 
                   match = False
#                  print '    *** match FALSE ***',
#            print ''
       return match










    ###################################################################      
    def add_vam_pout_columns(self, ref_temp=25, ref_freq=870.0, ref_vbat=3.6, ref_pin=3.0, ref_seg='*', ref_hblb = 'LB', ref_process = 'TT') :
    
       '''  add_vam_pout_columns : Does the all the processing of data for Edge Distortion Test plotting

       It creates a number of new data columns needed to plot distortion.

       1) Go through all the AM-AM distortion tests looking for the test that matches the reference conditions.
           When found save the AM-AM magnitude values and the VAM values for future calibration and reference calculations.

       2) Go through all the Power and Efficiency tests (PAE),
           It uses the measured power output for calibrating all subsequent AM-AM distortion data until the next PAE test.
           AM-AM magnitude value from the PSA does not give a direct power measurement in dBm. (We need to
           run a PAE test to get the power measured with a Power meter and use this as the calibration
           for subsequent AM-AM distortion tests.)
    
       3) For each group of distortion tests (which are all part of the same calibration group)
          Look for the distrtion test which matches the reference conditions. Calculate the calibration
          Scaling factors. 

       4) Go through all distortion tests in the calibration group and apply the calibration, and calculate the gain (Pout/VAM) etc
         
       5) Go through all the distortion tests and run
              add_gain_phase_slope
              add_gain_phase_ref_diff 
       '''
       
       self.status.set( '(add_vam_pout_columns) Calculating Distortion Values' )
       self.root.update()
    
       print '\n(add_vam_pout_columns) Calculating Distortion Values with reference conditions [%s %s %s %s %s %s %s]' % (ref_process, ref_temp, ref_hblb, ref_seg, ref_freq, ref_vbat, ref_pin)

       # save the reference conditions
       # these will be used to decide whether to plot limits later

       cond_txt = ref_hblb + ',' + ref_seg + ','  + ref_process + ','

       if not  cond_txt +  'Vbat(Volt)'      in self.ref:      self.ref[ cond_txt +  'Vbat(Volt)'     ] = ref_vbat 
       if not  cond_txt +  'Pwr In(dBm)'     in self.ref:      self.ref[ cond_txt +  'Pwr In(dBm)'    ] = ref_pin
       if not  cond_txt +  'Freq(MHz)'  in self.ref:      self.ref[ cond_txt +       'Freq(MHz)' ] = ref_freq 
       if not  cond_txt +  'Temp(C)'         in self.ref:      self.ref[ cond_txt +  'Temp(C)'        ] = ref_temp 
       #if not  cond_txt +  'Process'         in self.ref:      self.ref[ cond_txt +  'Process'        ] = ref_process 

                                                        
                                                        
       if not 'AM-AM' in self.data:
           print "...warning...(add_vam_pout_columns) There is no 'AM-AM' data in the logfile. Cannot plot Distortion results"
           return
    
       
    

       amam_ref   = {}
       vam_ref    = {}
    
       found_ref_am = 0
       ref_rns = [ None, None ]
       






       #-----------------------------------------------------------
       #
       #     1) Get the distortion data for the reference conditions.
       #
       #     look for the distortion data for the Reference conditions
       #     and save the AM-AM levels for each step.
       #
       #-----------------------------------------------------------
       
       for rn in range( self.datacount ) :
     
            if(self.data[ 'TestName' ][rn] == 'AM-AM AM-PM Distortion' and
               self.data[ 'HB_LB' ][rn] == ref_hblb                 and
               self.data[ 'Process' ][rn] == ref_process            and
               self.compare_values(self.data[ 'Vbat(Volt)'     ][rn] ,  ref_vbat  ) and
               self.compare_values(self.data[ 'Freq(MHz)' ][rn] ,  ref_freq  ) and
               self.compare_values(self.data[ 'Pwr In(dBm)'    ][rn] ,  ref_pin   ) and
               self.compare_values(self.data[ 'Temp(C)'        ][rn] ,  ref_temp  ) and
               (ref_seg == '*' or self.data[ 'Segments' ][rn] == ref_seg)) :
    
               
               # save the amam values for each step also, we will write these out as reference pout
               # values
               step = self.data[ 'Step' ][rn]

               # only add the reference power step on the first occurance (just for the sake of consistency)
               if not step in amam_ref:
                   amam_ref[ step ] = self.data[ 'AM-AM' ][rn]
                   vam_ref[ step ]  = self.data[ 'VAM(volt)' ][rn]
                   if step == 1 :  ref_rns[0] = rn
                   ref_rns[1] = rn
               if step == 1 : found_ref_am += 1
    
       if found_ref_am == 0:
            print '*** ERROR *** (add_vam_pout_columns) Could not find any AM-AM AM-PM Distortion test data that match the reference conditions [%s %s %s %s %s %s %s]' % (ref_process, ref_temp, ref_hblb, ref_seg, ref_freq, ref_vbat, ref_pin)
            return

       if found_ref_am > 1:
            print '...warning... (add_vam_pout_columns) Found %d sets of AM-AM AM-PM distortion test data that match the reference conditions [%s %s %s %s %s %s %s], will use the first one.' % (found_ref_am, ref_process, ref_temp, ref_hblb, ref_seg, ref_freq, ref_vbat, ref_pin)
    


       # Make up the new data columns


       if not 'Ref Pwr Out(dBm)' in self.data:
         self.data[ 'Ref Pwr Out(dBm)' ]     = [None] * self.datacount
         self.data[ 'Gain AM/VAM (V/V)']     = [None] * self.datacount
         self.data[ 'Gain AM/VAM (dB)']      = [None] * self.datacount
#        self.data[ 'Gain AM/VAM Norm (V/V)']         = [None] * self.datacount
         self.data[ 'Gain AM/(VAM-offset) (V/V)' ]    = [None] * self.datacount
         self.data[ 'Gain AM/(VAM-offset) (dB)']                = [None] * self.datacount
         self.data[ 'Gain AM/(VAM-offset) (dB) <emp-limits>' ]  = [None] * self.datacount
         self.data[ 'Gain AM/(VAM-offset) Slope (dB/dB)' ]      = [None] * self.datacount
         self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB)' ]  = [None] * self.datacount
         self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB) <emp-limits>' ]  = [None] * self.datacount

         self.data[ 'Adj-Ref Pwr Diff(dB)' ] = [None] * self.datacount
         self.data[ 'Ref VAM(volt)' ]        = [None] * self.datacount
         self.data[ 'VAM-Ref/Ref' ]          = [None] * self.datacount

         self.data[ 'AM-Ref/Ref' ]           = [None] * self.datacount
         self.data[ 'AM-PM Slope (deg/dB)' ] = [None] * self.datacount
         self.data[ 'AM-PM Slope - Ref (deg/dB)' ]       = [None] * self.datacount
         self.data[ 'AM-PM Slope - Ref (deg/dB) <emp-limits>' ]       = [None] * self.datacount



       self.vam_offset = float( self.vam_offset )
       
       print '...using a VAM offset of %s v' % self.vam_offset
       


       power_cal_count = 0




       #-----------------------------------------------------------
       #
       #     2) Find the location of all the PAE tests to be used for power calibration
       #
       #     and record the conditions for the PAE tests
       #
       #-----------------------------------------------------------

#      print 'self.datacount', self.datacount

       # build a list op pwr_eff_test pointers

       calib_pwr_pae_lst = []
       dist_test_lst = []

       start_dist_rn = None
       for rn in range( self.datacount ) :
          if self.data[ 'HB_LB' ][ rn ] == ref_hblb and  (ref_seg == '*' or self.data[ 'Segments' ][ rn ] == ref_seg) :

             if self.data[ 'TestName' ][ rn ] == 'Output Power & Efficiency' :
#                print ' (dist_test_lst) PAE   rn', rn
                 calib_pwr_pae_lst.append( rn )

#            print 'step=',  self.data[ 'Step' ][ rn ], self.data[ 'Step' ][ rn+1 ], '   rn=', rn
             if self.data[ 'Step' ][ rn ] == 1:
#                print '\n       (dist_test_lst) Step==1   rn', rn
                 start_dist_rn = rn
             if  rn+1 == self.datacount or self.data[ 'Step' ][ rn+1 ] == 1 or self.data[ 'Step' ][ rn+1 ] == None or self.data[ 'Step' ][ rn+1 ] == '':
#                print '       (dist_test_lst) Next rn Step==1   rn', rn
                 finish_dist_rn = rn+1
                 if start_dist_rn != None: 
                      dist_test_lst.append( [ start_dist_rn, finish_dist_rn ] )
#                     print '                  append dist_test_lst  rn', rn, start_dist_rn, finish_dist_rn
                 start_dist_rn = None 


       print '(wadd_vam_pout_columns) number of power calibration tests = ', len( calib_pwr_pae_lst )
             

       # loop through each of the pwr_eff_test records
       # record the conditions, and later search for the same conditions in the distortion data

    
       for rni in range( len(calib_pwr_pae_lst) ):

           rn = calib_pwr_pae_lst[ rni ]
    
           # save the current power cal values
           pwrcal_pout_dbm = self.data[ 'Adj Pwr Out(dBm)' ][ rn ]
           pwrcal_vramp    = self.data[ 'Vramp Voltage'    ][ rn ]
           pwrcal_freq     = self.data[ 'Freq(MHz)'   ][ rn ]
           pwrcal_vbat     = self.data[ 'Vbat(Volt)'       ][ rn ]
           pwrcal_pin      = self.data[ 'Pwr In(dBm)'      ][ rn ]
           pwrcal_hblb     = self.data[ 'HB_LB'            ][ rn ]
           pwrcal_seg      = self.data[ 'Segments'         ][ rn ]
    
    
    
    
           # find the span of the current pwr cal
           # (up to the next power cal)
           if rni == len( calib_pwr_pae_lst) -1 :
              next_rn = len( self.data[ 'TestName' ] )
           else:
              next_rn = calib_pwr_pae_lst[ rni+1 ]
    
    
           #print rn, next_rn, pwrcal_pout_dbm, pwrcal_vramp, pwrcal_freq, pwrcal_vbat, pwrcal_pin, pwrcal_hblb, pwrcal_seg
    
    




    
           #--------------------------------------------------------------------
           #
           # 3) Step through the distrtion tests of the current calibration group, if 
           # the conditions match the reference conditions calculate the calibration scaling factors
           #
           # loop through the following distortion test data (until the next power_eff_test)
           # look for the distortion test that has the same conditions as the preceding power_eff_test
           # when found look at the AM-AM value and calculate the power scaling factors
           #
           #--------------------------------------------------------------------
    
           
           found_matching_am_step = False
           for rnj in range( rn, next_rn ) :
              
              if(self.data[ 'TestName' ][rnj]    == 'AM-AM AM-PM Distortion' and
                 self.data[ 'HB_LB'    ][rnj]    == pwrcal_hblb              and
                 self.data[ 'Segments' ][rnj]    == pwrcal_seg               and
                 self.compare_values( self.data[ 'Vbat(Volt)'     ][rnj] , pwrcal_vbat) and
                 self.compare_values( self.data[ 'Pwr In(dBm)'    ][rnj] , pwrcal_pin ) and
                 self.compare_values( self.data[ 'Freq(MHz)' ][rnj] , pwrcal_freq)) :
                   
                 found_matching_am_step = True
    
                 amam_val = self.data[ 'AM-AM' ][rnj]
                 pwrcal_amam_sqr = amam_val ** 2
                 pwrcal_pout_w = (10**(pwrcal_pout_dbm/10.0))/1000
                 amam2w        = pwrcal_pout_w / pwrcal_amam_sqr


                 
         
           if found_matching_am_step == False and next_rn - rn > 2 :

             print '*** ERROR *** (add_vam_pout_columns) Could not find a matching AM-AM AM-PM Distortion test for power calculation [%d -> %d]' % (rn, next_rn)
             print self.data[ 'logfilename' ][rn] , self.data[ 'linenumber' ][rn] , self.data[ 'linenumber' ][next_rn]
             print pwrcal_vbat, pwrcal_pin, pwrcal_hblb, pwrcal_freq, pwrcal_seg, pwrcal_vramp, '[ %s -> %s ]' % (rn, next_rn)
             return
           else:
             #print pwrcal_vbat, pwrcal_pin, pwrcal_hblb, pwrcal_freq, pwrcal_seg, pwrcal_vramp, '[ %s -> %s ]' % (rn, next_rn)
             pass
     







           #--------------------------------------------------------------------
           #
           # 4) Step the distrtion tests again, this time applying the 
           # calibration to all the distortions tests, also calculate the gain
           #
           #--------------------------------------------------------------------

    
           for rnj in range( rn, next_rn ) :
              if self.data[ 'TestName' ][rnj] == 'AM-AM AM-PM Distortion' and self.data[ 'HB_LB' ][rnj] == ref_hblb  and  (ref_seg == '*' or self.data[ 'Segments' ][ rn ] == ref_seg) :
    
                 # calculate for the current am-am value
                 am_val  =   self.data[ 'AM-AM' ][rnj]
                 pwr_val_w = amam2w  *  am_val**2

                 self.data[ 'Adj Pwr Out(dBm)' ][rnj] =   10*log10(pwr_val_w*1000)
    
                 # calculate for the PSA AM/VAM value
                 if type(self.data[ 'VAM(volt)' ][rnj]) != types.StringType and  self.data[ 'VAM(volt)' ][rnj] != 'nan':
                    # if the VAM - offset is less than 1mv make this will cause the log10 to error, therefore fix minimum to 1mv
                    power_cal_count += 1
                    vam_offset_diff = self.data[ 'VAM(volt)'][rnj] - self.vam_offset
                    if vam_offset_diff < 0.001 : vam_offset_diff = 0.001
                    self.data[ 'Gain AM/VAM (V/V)' ][rnj]  = am_val / (self.data[ 'VAM(volt)'][rnj] )                # Skyworks Gain definition
                    self.data[ 'Gain AM/(VAM-offset) (V/V)' ][rnj]  = am_val / vam_offset_diff
                    self.data[ 'Gain AM/(VAM-offset) (dB)'  ][rnj]  = 20*log10(  am_val / vam_offset_diff  )  # EMP Gain definition
                    self.data[ 'Gain AM/(VAM-offset) (dB) <emp-limits>'  ][rnj]  = 20*log10(  am_val / vam_offset_diff  )
                 else:
                    self.data[ 'Gain AM/VAM (V/V)' ][rnj]  = 'NaN'
                    self.data[ 'Gain AM/(VAM-offset) (V/V)' ][rnj]  = 'Nan'
                    self.data[ 'Gain AM/(VAM-offset) (dB)'  ][rnj]  = 'Nan'
                    self.data[ 'Gain AM/(VAM-offset) (dB) <emp-limits>'  ][rnj]  = 'NaN'
                     #self.data[ 'VAM(volt)' ][rnj] = 0

   
                 # calculate for the reference am-am value also
                 if found_ref_am :
                   step = self.data[ 'Step' ][rnj]
                   am_val  =  amam_ref[ step ]
                   pwr_val_w = amam2w  *  am_val**2
                   self.data[ 'Ref Pwr Out(dBm)'     ][rnj] = 10*log10(pwr_val_w*1000)
                   self.data[ 'Adj-Ref Pwr Diff(dB)' ][rnj] = self.data[ 'Adj Pwr Out(dBm)' ][rnj] - self.data[ 'Ref Pwr Out(dBm)' ][rnj]
                   self.data[ 'Ref VAM(volt)'        ][rnj] = vam_ref[ step ]
              
                   try: self.data[ 'VAM-Ref/Ref'          ][rnj] = ( self.data['VAM(volt)'][rnj]-self.data['Ref VAM(volt)'][rnj])/self.data['Ref VAM(volt)'][rnj]
                   except Exception: self.data[ 'VAM-Ref/Ref'          ][rnj] = 'NaN'

                   try: self.data[ 'AM-Ref/Ref'          ][rnj] = ( self.data['AM-AM'][rnj]-am_val )/ am_val
                   except Exception: self.data[ 'AM-Ref/Ref'          ][rnj] = 'NaN'


#           self.add_normalized_gain( rn, next_rn, ref_hblb )



       print "...calibrated the power for %d 'AM-AM AM-PM Distortion' test results" % power_cal_count 


       #--------------------------------------------------------------
       #
       #  5) Calculate the Gain and Phase distortion variation data
       # 
       #--------------------------------------------------------------


       for test_rns in dist_test_lst:
         #self.add_normalized_gain( test_rns ) 
         self.add_gain_slope( test_rns ) 
         self.add_phase_slope( test_rns ) 

       for test_rns in dist_test_lst:
         self.add_gain_ref_diff( test_rns, ref_rns ) 
         self.add_phase_ref_diff( test_rns, ref_rns ) 

            
       self.gen_values_dict()
       self.status.set( 'waiting for user input' )
       self.root.update()



    ###################################################################

    def add_normalized_gain( self , trns ):

         # find the gain when the power out is 0dBm
 
         
         # normalize the gain to 0dBm       

         x = array( self.data[ 'Adj Pwr Out(dBm)'  ][trns[0]:trns[1]] )
         y = array( self.data[ 'Gain AM/(VAM-offset) (dB)' ][trns[0]:trns[1]] )
         
         xi = 0

         [yi] = stineman_interp([xi],x,y)

         for rnj in range( trns[0], trns[1] ): 
                  self.data[ 'Gain AM/VAM Norm (dB)' ][rnj]  =  self.data[ 'Gain AM/VAM (dB)' ][rnj] / yi

            
    ###################################################################

    def add_gain_phase_slope( self, trns ):

         x  = self.data[ 'Adj Pwr Out(dBm)'       ] [trns[0]:trns[1]] 
         yn = self.data[ 'Gain AM/(VAM-offset) (dB)' ][trns[0]:trns[1]] 
         yp = self.data[ 'AM-PM(degree)'          ] [trns[0]:trns[1]]


         old_xi = x[0]
         old_yni = yn[0]
         old_ypi = yp[0]
         rnj = trns[0]
         for xi,yni,ypi in zip(x,yn,yp):

            
            if xi == None or xi == '' : xi = old_xi
            dxi = xi - old_xi
            if dxi == 0 : dxi = 1e6   # dxi is 0 for first loop which would cause divZero error, this hack prevents this from happenning
            old_xi = xi

            if yni == None or yni == '' : yni = old_yni
            nslope = yni - old_yni
            
            self.data[ 'Gain AM/(VAM-offset) Slope (dB/dB)'              ][rnj]  =  nslope / dxi
            old_yni = yni

            if ypi == None or ypi == '' : ypi = old_ypi
            pslope = ypi - old_ypi
            self.data[ 'AM-PM Slope (deg/dB)'                   ][rnj]  =  pslope / dxi
            old_ypi = ypi

            rnj += 1

    
    ###################################################################
    def add_gain_slope( self, trns ):

         x  = self.data[ 'Adj Pwr Out(dBm)'       ] [trns[0]:trns[1]] 
         yn = self.data[ 'Gain AM/(VAM-offset) (dB)' ][trns[0]:trns[1]] 

         old_xi = x[0]
         old_yni = yn[0]
         rnj = trns[0]

         for xi,yni in zip(x,yn):
            

            if xi == None or xi == '' : xi = old_xi
            dxi = xi - old_xi
            if dxi == 0 : dxi = 1e6   # dxi is 0 for first loop which would cause divZero error, this hack prevents this from happenning
            old_xi = xi

            if yni == None or yni == '' : yni = old_yni
            nslope = yni - old_yni
            
            self.data[ 'Gain AM/(VAM-offset) Slope (dB/dB)'              ][rnj]  =  nslope / dxi
            old_yni = yni

            rnj += 1

    
    ###################################################################
    def add_phase_slope( self, trns ):

         x  = self.data[ 'Adj Pwr Out(dBm)'       ] [trns[0]:trns[1]] 
         yp = self.data[ 'AM-PM(degree)'          ] [trns[0]:trns[1]]


         old_xi = x[0]
         old_ypi = yp[0]
         rnj = trns[0]
         for xi,ypi in zip(x,yp):

            
            if xi == None or xi == '' : xi = old_xi
            dxi = xi - old_xi
            if dxi == 0 : dxi = 1e6   # dxi is 0 for first loop which would cause divZero error, this hack prevents this from happenning
            old_xi = xi

            if ypi == None or ypi == '' : ypi = old_ypi
            pslope = ypi - old_ypi
            self.data[ 'AM-PM Slope (deg/dB)'                   ][rnj]  =  pslope / dxi
            old_ypi = ypi

            rnj += 1

    
    ###################################################################

    def add_gain_phase_ref_diff( self, trns, ref_rns ) :

         '''For this distortion take the gain and phase slope and subract the gain and phase slope from the reference test'''

         ref_rn = ref_rns[0]

         if ref_rn == None :
            print '*** ERROR *** (add_gain_phase_ref_diff) No reference data found, cannot calculate gain phase reference difference'
            return
         
         for rn in range( trns[0], trns[1] ): 
            self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB)' ][rn]                =  self.data[ 'Gain AM/(VAM-offset) Slope (dB/dB)' ][rn]  - self.data[ 'Gain AM/(VAM-offset) Slope (dB/dB)' ][ref_rn]
            self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB) <emp-limits>' ][rn]   =  self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB)' ][rn]
            self.data[ 'AM-PM Slope - Ref (deg/dB)'      ][rn]   =  self.data[ 'AM-PM Slope (deg/dB)'      ][rn]  - self.data[ 'AM-PM Slope (deg/dB)'      ][ref_rn]
            self.data[ 'AM-PM Slope - Ref (deg/dB) <emp-limits>'      ][rn]   =   self.data[ 'AM-PM Slope - Ref (deg/dB)'      ][rn] 
            ref_rn += 1
       



    def add_gain_ref_diff( self, trns, ref_rns ) :

         '''For this distortion take the gain and phase slope and subract the gain and phase slope from the reference test'''

         ref_rn = ref_rns[0]

         if ref_rn == None :
            print '*** ERROR *** (add_gain_ref_diff) No reference data found, cannot calculate gain reference difference'
            return
         
         for rn in range( trns[0], trns[1] ): 
            self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB)' ][rn]                =  self.data[ 'Gain AM/(VAM-offset) Slope (dB/dB)' ][rn]  - self.data[ 'Gain AM/(VAM-offset) Slope (dB/dB)' ][ref_rn]
            self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB) <emp-limits>' ][rn]   =  self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB)' ][rn]
            ref_rn += 1
       



    def add_phase_ref_diff( self, trns, ref_rns ) :

         '''For this distortion take the gain and phase slope and subract the gain and phase slope from the reference test'''

         ref_rn = ref_rns[0]

         if ref_rn == None :
            print '*** ERROR *** (add_gain_phase_ref_diff) No reference data found, cannot calculate phase reference difference'
            return
         
         for rn in range( trns[0], trns[1] ): 
            self.data[ 'AM-PM Slope - Ref (deg/dB)'      ][rn]   =  self.data[ 'AM-PM Slope (deg/dB)'      ][rn]  - self.data[ 'AM-PM Slope (deg/dB)'      ][ref_rn]
            self.data[ 'AM-PM Slope - Ref (deg/dB) <emp-limits>'      ][rn]   =   self.data[ 'AM-PM Slope - Ref (deg/dB)'      ][rn] 
            ref_rn += 1
       





    ###################################################################
    
    def swap_hb_seg_data( self ):
    
       # a mistake in the ramp files files caused the segment value for HB staircase file to
       # be swapped.
    
    
    
    
    
       # For records with Testname=AM_DISTORTION HB_LB=HB SEG=11 to be change SEG field to 00
       # For records with Testname=AM_DISTORTION HB_LB=HB SEG=00 to be change SEG field to 11
    
    
       seg_swap1 = seg_swap2 = 0
       for rn in range(self.datacount):
          if (self.data['TestName'][rn] == 'AM-AM AM-PM Distortion' and
              self.data['HB_LB'][rn]    == 'HB'):
              
             if self.data['Segments'][rn] == '11' : self.data['Segments'][rn] = 'to_00'
             if self.data['Segments'][rn] == '00' : self.data['Segments'][rn] = 'to_11'
             seg_swap1 += 1
             
       for rn in range(self.datacount):
          if (self.data['TestName'][rn] == 'AM-AM AM-PM Distortion' and
              self.data['HB_LB'][rn]    == 'HB'):
    
             if self.data['Segments'][rn] == '11' or  self.data['Segments'][rn] == '00' :
               print '*** ERROR *** (swap_hb_seg_data) bad seg value data found' ,rn, self.data['Segments'][rn]
              
             if self.data['Segments'][rn] == 'to_11' : self.data['Segments'][rn] = '11'
             if self.data['Segments'][rn] == 'to_00' : self.data['Segments'][rn] = '00'
             seg_swap2 +=1
    
    
    
    
    
    
    
    
       # For records with Testname=POWEREFF HB_LB=HB SEG 00 swap complete record with 
       #  records with Testname=POWEREFF HB_LB=HB SEG 11
    
    
    
       pwr_eff_lst = []
       for rn in range(self.datacount):   
         if (self.data['TestName'][rn] == 'Output Power & Efficiency' and
              self.data['HB_LB'][rn]    == 'HB'):
            pwr_eff_lst.append( rn )
    #       print rn, data['Segments'][rn], data['Temp(C)'][rn], data['Vbat(Volt)'][rn], data['Test Freq(MHz)'][rn], data['Pwr In(dBm)'][rn], data['Segments'][rn]
                     
    
    #  print 'pwr_eff_lst=', pwr_eff_lst
    #  print ''
    
    
       pairs_done = {}
       pairs_list = []
    
       check_list = ['Temp(C)', 'Vbat(Volt)', 'TestName', 'Freq(MHz)', 'Pwr In(dBm)', 'HB_LB', 'Magnitude', 'Phase(degree)', 'logfilename']
    
    
       for rni in range(len(pwr_eff_lst)):   
            rn = pwr_eff_lst[rni]
    
            # if this is one of the pairs we have already identified then ignore it
            if rn in pairs_done: continue
    
            # find the oposite segment from this one
            seg = self.data['Segments'][rn]
            if seg == '11' : seg_to_find = '00'
            if seg == '00' : seg_to_find = '11'
          
    
            # look through the remainder of the records to see if we can locate a matching record where the
            # segment is inverted.
     
            for rnni in range( rni, len(pwr_eff_lst)):
              rnn = pwr_eff_lst[rnni]
              match = True
              for c in check_list:
                 if self.data[c][rn] != self.data[c][rnn] :
                    match = False
                    break
              if match == False or self.data['Segments'][rnn] != seg_to_find : continue
    
              # got a match!   then save this original record and the matching record
    
              if rnn not in pairs_done:
                 pairs_list.append( [rn, rnn] )
                 pairs_done[ rnn ] = 'done'
                 break 
    
            if match == False :
              print '*** ERROR *** (swap_hb_seg_data) couldnt find matching record for record', rn
    #       print pairs_list
    #       print pairs_done
    
       # swap the pairs
    
       for p in pairs_list:
          for n in self.data:
                 tmpval          = self.data[n][ p[0] ]
                 self.data[n][ p[0] ] = self.data[n][ p[1] ]
                 self.data[n][ p[1] ] = tmpval
                
      
    ###################################################################
    def plot_polar_data( self, xynames,  logfilename ):
    
    
      print '...plotting polar data for:' , xynames[2]
    
      self.xydata = self.get_data( xynames,  conditions=[] )  
    
      rootfilename = re.sub(r'\..*', '', logfilename)
    
    
      vswr_lst = self.get_unique_vals( self.xydata[3] )
    
      xrad = self.deg2rad(self.xydata[0])
    
    
    
    
    
      idx_min, idx_max = self.get_minmax_idx( self.xydata[2] )
    
      xmin, xmax = self.get_minmax( xrad )
      ymin, ymax = self.get_minmax( self.xydata[1] )
    
      # set the resolution of the color grid
      #n = 800
      n = 100
      xser = linspace(xmin,xmax, n)
      yser = linspace(ymin,ymax, n)
      X,Y = meshgrid( xser, yser )
    
      # generate interpolated Z values for the fine XY grid, (griddata requires matplotlib v0.98)
      Z = matplotlib.mlab.griddata(xrad, self.xydata[1], self.xydata[2],  X, Y)
    
      figure()
      ax1 = subplot(111, polar=True)
      
     # pcolormesh( X, Y, Z, alpha=0.2)   # pcolormesh runs a lot faster than pcolor for the polar plot!
    
      # Make the color coding sensible for binary alert register values
      if re.search(r'Alert Reg', xynames[2]) :
        vmx = 1.0; vmn = 0.0
      else:
        vmx = None ; vmn = None
        
      pcolormesh( X, Y, Z, alpha=0.2, vmin=vmn,vmax=vmx )   # pcolormesh runs a lot faster than pcolor for the polar plot!
    
      # make sure the Magnitude axis is set to 1.0 (which is VSWR of infinity) to match Smith Chart scaling
      axis([0,1,0,1])
      
      #grid()
      # make the magnitude labels invisible (it clutters the plot, and we are more interested in vswr)
      setp( ax1.get_yticklabels(), visible=False)
    
      colorbar()
      title( xynames[2] )
    
    
    
      if not re.search(r'Alert Reg', xynames[2]) :
    
        # draw contour lines
        ax3 = contour(X, Y, Z )
        clabel(ax3)
        
        # annotate the min and max values
        self.annotate_polar_val(   'max = %0.3fv' % self.xydata[2][idx_max]   , idx_max, 0.2, 0.9 )
        self.annotate_polar_val(   'min = %0.3fv' % self.xydata[2][idx_min]   , idx_min, 0.6, 0.9 ) 
    
      # draw dots where each loadpull sample was measured
      scatter(xrad, self.xydata[1],marker='^',s=1) 
      axis([0,1,0,1])
    
    
      y = 0.25
      for txt in [ 'Band = %s' % ( self.data['HB_LB'][-1] ) ,
                   'Seg  = %s' % ( self.data['Segments'][-1] ) ,
                   
                   'Freq = %dMHz' % ( self.data['Freq(MHz)'][-1] ) ,
                   'Vbat  = %sv' % ( self.data['Vbat(Volt)'][-1] ) , 
                   'VAM  = %sv' % ( self.data['Vramp Voltage'][-1] ) ,
                   'VSWR = %s' % vswr_lst , 
                   '',
                   'Date = %s %s' % ( self.data['Date'][-1],self.data['Time'][-1]) ,
                   'Vramp Rel = %s' % ( self.data['Vramp Release'][-1] ) , 
                   'Logfile = %s' % ( self.data['logfilename'][-1]) , ]:
         self.annotate_figure( txt, 0.02 , y )
         y = y - 0.025
    
         
    
      #legend(shadow=True,pad = 0.1,labelsep = 0.001, prop = matplotlib.font_manager.FontProperties(size='smaller') )
      name = rootfilename + ' ' + xynames[2]
      name = re.sub('[<>]', '_', name )
      print '...saving png file: ', name
      savefig( name )
    
    
    ###################################################################
    def print_column_list( self ):
    
      print '\n...the following data columns were found in the logfile:\n'
      cll = []
      for col in self.data:
        cll.append(col)
      cll.sort()
      for c in cll:
        print "'%s'," % c ,
      print '\n'
    
    
    
    
    ###################################################################
    def get_line_style_indexes( self, series_unique_values, series_unique_names, listcount, listlen, ycount, ylen ):
    
        ''' Tries to workout what color and line style to draw the graph
            it does this by looking at the series_unique_names and series_unique_values
         
            The series_unique_names is a list of all the parameter names that vary in the series,


            If the series_unique_names and series_unique_values are empty resort to using the number of graphs and number of ycount
'''




        
#       print '(get_line_style_indexes) series_unique_values=%s   series_unique_names=%s '% (series_unique_values,series_unique_names) , ycount , listcount
        sun = ''
        cidx = 0
#       if len( series_unique_names ) > 0: 
#         j = 0
#         sun = series_unique_names[j]

        sun = self.color_series.get()

        jfound = None
        for j,n in enumerate( series_unique_names ):
             if n == sun : 
                 jfound = j
                 break

        if sun != '' and sun != 'None' and sun != 'Yaxis' and jfound != None:

          # find the position of the color_series column name in the series_unique_names list
          # this is the value we will look for in the values_dict.

#         self.add_values_dict( sun )
          scd = self.values_selected_dict[ sun ]
          for ki in range(len(scd)):
            k = scd[ki]
#           print '(get_line_style_indexes) CIDX comparing series_unique_values[j]=<%s %s>   and scd[k]=<%s %s>' % (str(series_unique_values[j]), type(series_unique_values[j]), str(k), type(k))
            if str(series_unique_values[jfound]) == str(k):
#               print '     match'
                cidx = ki

        else:
             cidx = ycount + listcount 
             if listcount > 0 and ycount > 0:
                cidx = ycount 
                

#       print '      selecting color based on <%s> %s ' % (sun, cidx)
    
        sun = ''
        didx = 0
#       if len( series_unique_names ) > 1:
#         j = 1
#         sun = series_unique_names[j]

        sun = self.line_series.get()

        jfound = None
        for j,n in enumerate( series_unique_names ):
             if n == sun :
                jfound = j
                break

        if sun != '' and sun != 'None' and sun != 'Yaxis' and jfound != None :
#         self.add_values_dict( sun )
          scd = self.values_selected_dict[ sun ]
          for ki in range(len(scd)):
            k = scd[ki]
#           print '(get_line_style_indexes) CIDX comparing series_unique_values[j]=<%s %s>   and scd[k]=<%s %s>' % (str(series_unique_values[j]), type(series_unique_values[j]), str(k), type(k))
            if str(series_unique_values[jfound]) == str(k):
#               print '     match'
                didx = ki
        else:
             if listcount > 0 and ycount > 0:
                didx = listcount



#       print '      selecting line  based on <%s> %s ' % (sun, didx)
#       print series_unique_names



        c = self.color_list[ cidx %    len(self.color_list)    ]
        d = self.dash_list [ didx %    len(self.dash_list )    ]


        if self.line_on.get() == False : d = [0,100]

        return c, d, str(cidx), str(didx)


##################################################################################


    def get_selected_plot_data( self, selected_record_list, xynames, xysel ):
          ''' Weed out any bad data from the selected data. Bad data is any data that is not numeric 
              Bad data is converted to None'''
           

          xyname = xynames[ xysel ]


          time_data = False
          if re.search('^\[Time\]', xyname ):
             time_data = True 


          dlst = []
          rnlst = []

#         if not xyname in self.data:  return [None] * len( selected_record_list )
          if not xyname in self.data:  return [], []


          got_data = False

#         print 'selected_record_list'  , xyname, len( selected_record_list ), selected_record_list
          for rn in selected_record_list:

#                 print 'rn= %d  len( self.data[ %s ] ) = %s' % ( rn, xyname, len( self.data[ xyname ] ) )
                  xyv = self.data[ xyname ][rn]

                  #print '%5d xyv = <%s>' % ( rn, xyv)

                  if xyv == None:
                      dlst.append( None )
                      rnlst.append( None )


                  # We want to skip this plot if any of the data contains 'nan'

                  elif type(xyv) == types.StringType and xyv.lower() == 'nan':
                      print '...warning... found NaN data in %s data [%d], ... skipping this plot' % (xyname , rn )
                      dlst.append( None )
                      rnlst.append( None )


                  # if the data value is a list in its own right then return the value list

                  elif type(xyv) == types.ListType :
#                     print '(get_selected_plot_data)  xyv list= ',  xyv
                      got_data = True
                      txyv = []
                      rnl  = []
                      for tv in xyv:
                        try: 
                           tv = float( tv )
                        except Exception:
                           pass
                        txyv.append( tv )
                        rnl.append( rn )
                      dlst.extend( txyv )
                      rnlst.extend( rnl )
                  else:

                      # if its a regular number then add it to the plot data list 'dlst'

                      try: 
                        dlst.append( float( xyv ) )
                        got_data = True
                      except Exception:
                        dlst.append( None )
                      rnlst.append( rn )


          if not got_data : 
              return [], []

          return dlst, rnlst



    #####################################################################################
    def plot_graph_data( self, xynames,  conditions=None, savefile=None, titletxt=None ):
        xyd = self.plot_graph_data_core( 'xy_scatter_plot', xynames,  conditions, savefile, titletxt )
        return xyd
        
    ###################################################################
    def plot_polar_data( self, xynames,  conditions, savefile=None, titletxt=None ):
        xyd = self.plot_graph_data_core( 'polar_plot', xynames,  conditions, savefile, titletxt )
        return xyd
     
    ###################################################################
    def plot_interactive_graph( self ):
        self.interactive = True
        xyd  = self.plot_graph_data( self.xynames,  None,  )
        try:                self.status.set( 'waiting for user input' )
        except Exception:   pass
          
        self.root.update()
        print '  ...waiting for user input'
        return xyd

    ###################################################################
    def plot_graph( self ):
        self.interactive = False
        xyd = self.plot_graph_data( self.xynames,  None,  )
        return xyd
        



    
    ###################################################################
    def plot_graph_data_core( self, plottype, xynames,  conditions, savefile=None, titletxt=None ):

    
      self.status.set( '(plot_graph_data_core) PLOTTING GRAPH' )
      self.root.update()

      if not self.done_list_columns:
          self.print_column_list()
          self.print_values_list()
          self.done_list_columns = True


      done_a_plot   = False
      legend_list   = {}
      self.csv_data = []
 
      done_legend_color      = {}
      done_legend_linestyle  = {}
      done_legend_color_line = {}
      
      print '\n---(plot_graph_data_core)----------------------------------------\n'

#     print 'xynames=', xynames

      if len(xynames) < 2 or xynames[0]  == None or xynames[1]  == None  :   
            print '*** ERROR *** X or Y axis not defined'
            return 


      print "...plotting data for  x,y,z = %s\n" % ( xynames )
    
    
      # Check to see if we have any data to plot

      got_yaxis_data = False
      for i in range(len(xynames)):
         name = xynames[i]
         if not name in self.data:
            print "*** ERROR *** (plot_graph_data_core) There is no data for axis '%s'. It is not a named column in the logfile" % name
#           sys.stdout.write('\a')
            sys.stdout.flush()
            continue
         else:
            if i > 0 : got_yaxis_data = True



      # finish with this graph if we didn't get any data to plot on any of the yaxis's
      if got_yaxis_data == False: return 


 
      series_data, series_values, series_unique_name_value_str, series_unique_values, series_unique_names  = self.select_data( conditions, xynames[0] )



      self.xynames = xynames
      self.conditions = conditions


      # now update the control window with the selected axes etc. (this is mainly needed if we are running in script mode)


      self.win_select( xynames )

      # save the plot the file if selected       

      if savefile != None:
          rootfilename = re.sub(r'\..*',  '', savefile)
          rootfilename = re.sub(r'^.*\\', '', rootfilename)
          if re.search('auto', savefile, re.I ):  
               if titletxt != None:
                  savefilename = titletxt 
               else:
                  savefilename = xynames[1]
          else: 
                  savefilename = rootfilename 
      else:
               if titletxt != None:
                  savefilename = titletxt 
               else:
                  savefilename = xynames[1]
                    

    
    
      if titletxt == None :
         
             wtitle = self.graph_title.get() 
             if wtitle.strip() != '':
                 titletxt = wtitle.strip()
             if savefile != None:
                 titletxt = savefile
             
      if titletxt == None :
             titletxt = xynames[1]
    

    


      self.plot_position       = self.update_entry_box( self.plot_position, self.wplot_position )
      self.color_list          = self.update_entry_box( self.color_list,          self.wcolor_list )
      self.legend_location     = self.update_entry_box( self.legend_location,     self.wlegend_location )
      self.conditions_location = self.update_entry_box( self.conditions_location, self.wconditions_location )


            
      if plottype == 'xy_scatter_plot':

#          self.plot_interactive_graph( logfilename, xynames,  conditions )
        self.fig.clf()
        self.ax = self.fig.add_subplot(1,1,1)
        self.fig.subplots_adjust( left=self.plot_position[0], right=self.plot_position[1], top=self.plot_position[2], bottom=self.plot_position[3]  )


        self.xaxis_limits = self.get_axis_limits( self.xlimits, self.xscl_min.get(), self.xscl_max.get() )
        self.yaxis_limits = self.get_axis_limits( self.ylimits, self.yscl_min.get(), self.yscl_max.get() )

        if series_data != []:

          xname = xynames[0]
          yname = xynames[1]

 

          self.ax.set_title( titletxt )
          self.graph_title.set( titletxt ) 
           
          

          xlab = self.ax.set_xlabel( xynames[0] )
        
          txt = '\n'.join( xynames[1:] )

          ylab = self.ax.set_ylabel( txt )

 

        
          c = d = None

          self.lineref = {}
          self.xdata = {}
          self.ydata = {}
          self.rndata = {}
          self.data_color = {}
          xvals  = []
          yvals  = []
          rnvals = []
          snvals = []
          cvals  = []
          dvals  = []

          for ycount in range( 1, len(xynames)):

              #if ycount == 2 : 
              #  self.ax2 = twinx()
              #  self.ax2.yaxis.tick_right()
              #  ylabel(xynames[2])


              sn  = ''
              rn  = 0

              
              for sd,sn,sv in zip(series_data,series_unique_name_value_str, series_unique_values):
        



#               print '(plot...) sn = ', sn, sv, series_unique_names

                #--------------------------------------------------------
                # even though we have tried to split the data up into separate series, it is possible that
                # the data contains repeated tests with the same conditions. If this happens we should try to
                # further split the data into further series for plotting.
        
                # To detect whether the series needs to be split we need to look at the X values and see if they
                # progress in a more or less monotonic fashion.
                #--------------------------------------------------------



        
                sd_new = self.get_sub_series( xynames[0], sd )



                # if the data is time based data from the csv file we need to further break the list into 
                # individual values 

                if re.search(r'^\[Time\]' , xynames[ycount] ):
                   sdt_new = []
                   for sdt in sd_new:
                      if len(sdt) > 1 :
                         for sdtt in sdt:
                            sdt_new.append( [sdtt] )
                   sd_new = sdt_new
                     


                sd_new_len = 0
                for sl in sd_new:
                   if len( sl ) > 0 : sd_new_len += 1
                
                if sd_new_len != 1 : txt = 'x %d' % sd_new_len
                else:                 txt = ''
#               print "  .adding plot to graph for %s [%s] %s" % (xynames[ycount], sn, txt) 
        


                sdi = 0
                for sdai in range(len(sd_new)):
                  sda = sd_new[sdai]

                  if sda == [] : 
                       continue

                  trn = sda[0]
#                 print sdai, self.data['linenumber'][trn]  , self.data['//T#'][trn], self.data['TestName'][trn],  self.data['Test Freq(MHz)'][trn], sda
                  x,rnl = self.get_selected_plot_data( sda, xynames, 0 )
                  if x == []     : continue
                  y,rnl = self.get_selected_plot_data( sda, xynames, ycount )
                  if y == []: continue

                  if xynames[0] == 'Frequency of Spur (MHz)' or self.sort_data_on.get()  :
                      x, y, rnl = self.sort_selected_data( x, y, rnl ) 



                  xlen = len(x)
                  ylen = len(y)

                  if xlen < ylen:
                     y = y[:xlen]
                     rnl = rnl[:xlen]
                  if xlen > ylen:
                     x = x[:ylen]
                     rnl = rnl[:ylen]
              
                  if len(x) == 0 : continue

                  c, d, c_idx, d_idx = self.get_line_style_indexes( sv, series_unique_names, sdai, len(sd_new), ycount, len(xynames[1:]) )

                  sdi +=1
                
                  if sn == '' :     sn = xynames[ycount]   # make sure there is a label string
                  else:
                     sn_full = sn
                     
                     # truncate the sn name so that it only contains the color and line series values
                     sn = ''
                     nget = self.color_series.get()
                     for i,n in enumerate(series_unique_names):
                        if n == nget:
                           sn = sv[i]
                     nget = self.line_series.get()
                     for i,n in enumerate(series_unique_names):
                        if n == nget:
                           sn = sn + ' ' + sv[i]

                  if sdi > 1  :     sn = ''    # stop multiple repeated series names from cluttering up the legend
    

                  # if smaller legend is set then remove all but the first legend value from sn.
                  # and make sure it is unique


                  if self.small_legend.get() and sn != '':
                     sm_sn = re.sub(r'(\S+?)=(.+?)\s+(\S+?)=.*', r'\2', sn)
                     sm_sn = re.sub(r'(\S+?)=(.+?)\s*$', r'\2', sm_sn)
                     if sm_sn not in legend_list:
#                        legend_list[ sm_sn ] = 'done'
                        sn = sm_sn
                     else:
                        sn = ''
#                       sn_full = sm_sn + ' <' + str( line_count ) + '>'
#                       line_count += 1

                  else: 
                     pass
#                 print "  .adding plot to graph for yaxis '%s', series name '%s', num of points [%s]" % (xynames[ycount], sn, len(x), ) 
                     
                  # We need to limit the number of lines in the legend.
                  # Normally the legend will compriose of all combinations of color and line styles which can frequently end up being too long.    
                  # we will do two operations on the legend lines. Limit the number legend lines to only include one line of each color, and one line of each line style.
                  # remove the pareameter= from the parameter=value


                  if self.small_legend.get():

                      if c_idx in done_legend_color and d_idx in done_legend_linestyle :
                         sn = ''
#                        sn_full = sm_sn + ' <' + str( line_count ) + '>'
                      else:
#                        sn_full = sn
                         done_legend_color    [ c_idx ] = 'done' 
                         done_legend_linestyle[ d_idx ] = 'done' 
                  else:
                      ix = '%d %d' % ( int(c_idx), int(d_idx) )
                      if ix in done_legend_color_line:
                         sn = ''
                      else:
                         done_legend_color_line [ ix ] = 'done' 



                  try:
                     x,y,rnl = self.remove_bad_data( x,y,rnl, self.xaxis_limits, self.yaxis_limits )
                  except Exception:
                     pass

                  marker    = self.update_entry_box( self.plot_marker, self.wplot_marker )
                  linewidth = self.update_entry_box( self.plot_linewidth, self.wplot_linewidth )
                  ###############################################################################
                  #  And finally, here's what you've been waiting for ...  the plot command !!!

                  xx = self.ax.plot( x, y, color=c, dashes=d, label=sn, marker=marker, linewidth=linewidth, picker=5 )

#                 print dir(xx)


                  #
                  ###############################################################################
              
                  # save the data away so that it can be measured later if needed
                  xvals.append(x)
                  yvals.append(y)
                  rnvals.append(rnl)
                  snvals.append(sn)
                  cvals.append(c)
                  dvals.append(d)
                  
                  # save the data in dicts so that we can access it for gui data probing
                  self.lineref[  sn ] = xx
                  self.xdata[  sn ] = x
                  self.ydata[  sn ] = y
                  self.rndata[ sn ] = rnl
                  self.data_color[ sn ] = c


                  rn = sda[0]

                  if '[csv] Script File Name' in self.data:
                      tname =  self.data[ '[csv] Script File Name' ][ rn ]
                      if re.search( r'\[Time\]', xynames[ycount] ):
                         print '     .found time data to plot {%s}' % tname


                  if re.search( '<emp-limits>', xynames[ycount] ) and  self.check_nominal_condition( rn ): 
                     print "  .adding limits to plot"
                     self.add_all_limits( xynames[ycount], x, y, c, d, rn)

                  if re.search( r'\[Time\]', xynames[ycount] ): 
                      txt = tname
                  else: 
                      txt = sdai

                  if not done_a_plot : self.csv_data.append( [ xynames[0], '', x] )
                  self.csv_data.append( [ xynames[ycount], txt, y] )

                  done_a_plot = True



          if c != None and d != None and self.spec_limits != None:
              self.add_spec_limits( c, [100,0] )
               

          if self.legend_location and done_a_plot:
               self.legend = self.ax.legend(shadow=True,labelsep = 0.001,loc=self.legend_location, prop = matplotlib.font_manager.FontProperties(size='smaller'), pad=0.01 )
               self.legend.set_picker(self.my_legend_picker)
       


#         print 'self.xaxis_limits', self.xaxis_limits
#         print 'self.yaxis_limits', self.yaxis_limits
        

          # Set the axes limits, the limits were calculated earlier on

          if self.xaxis_limits != [] :
              self.ax.set_xlim( ( self.xaxis_limits[0] , self.xaxis_limits[1] ) )
 
          if self.yaxis_limits != [] :
              self.ax.set_ylim( ( self.yaxis_limits[0] , self.yaxis_limits[1] ) )






          # Set the number of grid lines

          self.ax.grid()

          g = self.xgrd_step.get()

          lim = self.ax.set_xlim()
          self.ax.set_xticks( self.get_grid_ticks( lim, self.xgrid, g ) )



          g = self.ygrd_step.get()

          lim = self.ax.set_ylim()
          self.ax.set_yticks( self.get_grid_ticks( lim, self.ygrid, g ) )



        
          #--------------------------------------------------------
          # Write out the conditions on the plot on the top RHS
          # note we dont print out variables which are swept,
          # (instead the swept vairaibles  will be written out in the graph legend)
          #--------------------------------------------------------

          if self.draw_conditions.get() and self.conditions_location :

              y = self.conditions_location[1]
              self.annotate_figure( 'CONDITIONS:' , self.conditions_location[0]  , y )
              y = y - 0.018
              for name in [ ''                     ,
                            'Part Number (Chip ID)',
                            'Serial Number'        ,            
                            ''                     ,
                            'HB_LB'                ,
                            'Segments'             ,
                            'Freq(MHz)'       ,
                            'Vramp Voltage'        ,
                            'Pwr In(dBm)'          ,
                            ''                     ,
                            'Vbat(Volt)'           , 
                            'Temp(C)'              ,
                            'Process'              , 
                            ''                     ,
                            'VSWR'                 ,
                            'Phase(degree)'        ,
                            ''                     ,
                            'Date'                 ,
                            'TestName'             ,
                            'Regmap'               ,
                            'Vramp Release'        , 
                            'logfilename'          ,
                            'csvfilename'            ]:
                
                 tname = self.truncate_name( name )
                 if  name in self.data and sn.find( tname ) < 0 and name not in xynames:
                     if name in  self.values_selected_dict:
                       txt = '%s = %s' % ( tname, self.list2str( self.values_selected_dict[ name ]) )
                     else:
                       self.add_values_dict( name )
                       txt = '%s = %s' % ( tname, self.list2str( self.values_dict[ name ]) )
                     #self.annotate_figure( txt, 0.755 , y )
                     ln = len(txt)
                     if ln > 200: ln = 200
                     for p in range(0, ln, 36):
                        t = txt[p:p+36]
                        if p > 0 : t = '   ' + t
                        self.annotate_figure( t, self.conditions_location[0]  , y )
                        y = y - 0.018
                 if name == '': y = y - 0.010
        

         
          if not done_a_plot:  self.fig.clf()

          if not done_a_plot:
              print "*** ERROR *** (get_selected_plot_data) There is no data for some of these axes '%s', please choose other axes, or select different filter values" % xynames

             

#         self.ax.annotate( 'hello6', xy=(0.5,20), 
#                   horizontalalignment='left', verticalalignment='bottom', fontsize=10)
                    
                    

          #--------------------------------------------------------
          # save the plot file
          #--------------------------------------------------------

          self.savefilename = savefilename
          self.png_filename = ''
        
          if savefile != None:        
             

              savefilename = self.clean_savefilename( savefilename )

              self.save_plot_count = int( self.save_plot_count)
              if int( self.save_plot_count) >= 0:
                self.save_plot_count = self.save_plot_count + 1
                savefilename = 'P%03d_%s' % ( self.save_plot_count, savefilename )


              savefile_fullpath = os.path.join(  self.savedir , savefilename )
 
              savefile_fullpath = savefile_fullpath + '.png'

              if done_a_plot:
                 print "....saving plot file: '%s'" % savefile_fullpath

                 self.root.update()
                 #self.root.update_idletasks()
              
                 try:
                   savefig( savefile_fullpath, dpi=100 )
                   self.png_filename = savefile_fullpath
                 except Exception:
                   print "*** ERROR *** could not save plot file '%s' (check permissions to write plot file in this directory)" % savefile_fullpath
              else:
                 print '   ... did not save a plot file'

#         self.ax.annotate( 'hello9', xy=(0.5,28), 
#                   horizontalalignment='left', verticalalignment='bottom', fontsize=10)
#         print '\ndir self.ax 1' , dir( self.ax )
          self.canvas.draw()
          self.root.update()
#         print '\ndir self.ax 2' , dir( self.ax )

          #--------------------------------------------------------
          #  If this is an interactive plot_graph then we want to enter the matplotlib loop
          #--------------------------------------------------------

          if self.interactive:
              self.canvas.show()

          self.sel_object = None
          
          return [xvals, yvals, rnvals, snvals, cvals, dvals]
        else:
          return 
      else:
        return 


###################################################################################################
    def get_grid_ticks(  self, minmax, step,  form_step) :


         if form_step != '' :
             if form_step >= 0:
                 step = form_step
             else:
                 step = None



         if type( step ) == types.StringType :
              if (step == '' or step.lower() == 'a') :
                  step = None

         if step == None :
              diff = abs( minmax[0] - minmax[1] )
              self.numgrids = self.update_entry_box( self.numgrids, self.wnumgrids)
              step = self.get_nearest_125num( diff/self.numgrids )


         try:
            step = float( step )
         except Exception: 
            return []

         if step > 0:
            x = arange( minmax[0], minmax[1]+step, step )
         else:
            x = []

         return x
###################################################################################################
    def update_entry_box( self, ipval , win ):
        ''' If in script mode this updates the entry box with the ipval, and returns the same ipval.
            if in gui mode it ignores the ipval and returns the value entered on the gui entry box window''' 

        val = ipval

        lenx = -1
        if self.run_mode == 'script' :
            if type( ipval ) == types.ListType:
               lst = []
               for i in ipval:
                 lst.append( str(i) )
               ipval = ' '.join( lst )
            win.set( ipval )

        if self.run_mode == 'gui' :
            val =  win.get()
            if val != '':
                x = val.split()
                lenx = len(x)
                if len(x) > 1:
                   lst = []
                   for i in x:
                     try: 
                       i = float(i)
                     except Exception:
                       pass   
                     lst.append( i )
                   val = lst
            else:
                val = ipval
          
       
        try: 
           val = float( val )
        except Exception:
           pass
           
#       print '(update_entry_box)  %s  ipval=<%s>, val=<%s> window=<%s> lenx=%s' % (self.run_mode, ipval, val, win, lenx)
        return val


###################################################################################################


    def get_axis_limits(  self, lims, lim_min_form, lim_max_form ) :


         if self.run_mode == 'script' :
              if lims == [] : 
                 return []
              else:
                 return [lims[0], lims[1], abs( lims[1]-lims[0] ) ]

         # if we have an 'A' character then we always have automatic scales
         if type( lim_max_form ) == types.StringType and lim_max_form.lower() == 'a' :
              return []

         # if the limits are set then use those limits
         if lim_max_form == '' and lims != [] :
              return [lims[0], lims[1], abs( lims[1]-lims[0] ) ]

         try: 
            lim_max_form = float( lim_max_form )
            lim_min_form = float( lim_min_form )
         except Exception:
            return []
             
         return [ lim_min_form, lim_max_form, abs( lim_max_form - lim_min_form ) ]



###################################################################################################
    def get_nearest_125num( self, num ):
         'Returns the nearest number to num that starts with a 1 2 or 5 digit'

         numabs = abs( num )

         # find the nearest exponent
         for e in range(-20, +20): 
             if 10**e > numabs: 
                  break
        
         m = 10**(e-1)

         
         n = 1
         if numabs > ( 1.5 * m ): 
                  n = 2
         if numabs > ( 3.5 * m ): 
                  n = 5
         if numabs > ( 7.5 * m ): 
                  n = 1
                  m = 10**e

         if num < 0 : n = -n

         return n * m
         


###################################################################################################
    def clean_savefilename( self, savefilename ):

         savefilename = re.sub(r'\..*$',              '',  savefilename )    # remove any extentions
         savefilename = re.sub(r'.*[\\\/]',           '',  savefilename )    # remove the directory pathnames
         savefilename = re.sub(' ',                   '_', savefilename )    # turn all spaces into underscores to help with linux filenames
         savefilename = re.sub('\[Time\]',            '',  savefilename )    # remove the special axis prefixes [Time]
         savefilename = re.sub('\[T90%\]',             '',  savefilename )    # remove the special axis prefixes [
         savefilename = re.sub('\[csv\]',             '',  savefilename )    # remove the special axis prefixes [
         savefilename = re.sub('[{}\[\]<>\(\)\.\,=://\n\*]', '', savefilename )    # remove any characters that arn't usually part of a filename e.g. , < > ( )

         return savefilename



###################################################################################################

    def save_plot( self ):

         savefilename = self.clean_savefilename( self.savefilename )

         last_used_directory = self.read_pygram_config( 'savedir' )

         savefilename = asksaveasfilename( defaultextension='.png', 
                                     title='Save Plot Filename', 
                                     initialdir=last_used_directory ,
                                     initialfile=savefilename+'.png' ,
                                     filetypes=[('PNG', '*.png'),] )

         if savefilename == '' or savefilename == (): return



         self.save_pygram_config( 'savedir', os.path.dirname(  os.path.abspath(savefilename) ) )
         self.savefilename =  os.path.basename(  os.path.abspath(savefilename) )
         self.savedir  =  os.path.dirname(   os.path.abspath(savefilename) )

         print "...saving plot file (save_plot): '%s'" % savefilename

         # add the name to the listbox
         try:
           savefig( savefilename )
         except Exception:
           print "*** ERROR *** could not save plot file '%s' (check permissions to write plot file in this directory)" % savefilename
              

###################################################################################################

    def save_excel( self ):

         savefilename = self.clean_savefilename( self.savefilename )

         savefilename = asksaveasfilename( defaultextension='.log', 
                                     title='Save Excel Filename', 
                                     initialfile=savefilename+'.csv',
                                     filetypes=[('comma seperated values', '*.csv'),] )

         if savefilename == '': return







         print "...saving excel file: '%s'" % savefilename


         fop = open( savefilename, 'w' )


         for col in self.csv_data:
              if col[1] > 0 : srs = '%s [%s]' % ( col[0], str( col[1] ) )
              else:           srs = col[0]
              print >> fop ,  srs , ',',
         print >> fop , ''              # newline 

         
         num_cols = len( self.csv_data )

         # find the maximum series length
         for coli in range( len(self.csv_data) ):
            col = self.csv_data[ coli ]
            
            if coli == 0 or len( col[2] ) > max_len :
               max_len = len( col[2] )
            

         for r in range( max_len ):
            for c in range(num_cols):
                if r < len( self.csv_data[c][2] ) : 
                     print >> fop,  self.csv_data[c][2][r] , ',' ,
                else:
                     print >> fop,                           ',' ,
            print >> fop, ''

         fop.close()

              

###################################################################################################


    def compare_columns(self, a, b):
        # sort on ascending self.sort_column
        
        return cmp(a[self.sort_column], b[self.sort_column])

###################################################################################################

    def sort_selected_data( self, x, y, rnl ):
        '''  Sort the x and y list data, reorder the lists so that the x data is increasing '''


        # make up a new index list from the x data

        if len(x) > len(y)  : ln = len(y)
        else                : ln = len(x)


        # make a new list compining the x and y data.
        # but we also weed out any empty 'None' values

        sd = []
        for tx, ty, trn in zip( x[:ln] , y[:ln], rnl[:ln] ) :
          if tx != None and ty != None:
             sd.append( [float(tx), float(ty), trn] )




        # compare function which sorts the list into ascending x values
        self.sort_column = 0

        sd.sort( self.compare_columns )


        # now unzip the x and y lists again

        xn = []
        yn = []
        rnln = []
        for tl in sd:
          #print '  %20s  %20s' % ( tl[0], tl[1] )
          xn.append( tl[0] )
          yn.append( tl[1] )
          rnln.append( tl[2] )
        
        return xn, yn, rnln


###################################################################################################


    def check_nominal_condition( self, rn ):

       # go through the current nominal conditions and check whether this record number matches.


       # if no reference has been defined then return a match
       if self.ref == {} : return 1

       cond_txt    = self.data[ 'HB_LB' ] [ rn ]  + ',' + self.data[ 'Segments' ] [ rn ] + ',' + self.data[ 'Process' ] [ rn ] + ','


       # look for an exact match with the segments matching
       if self.ref_logfilename != None and self.data[ 'logfilename' ][rn] == self.ref_logfilename:
            ret_val = 1
            return ret_val 



       ret_val = 1
       for c in [ 'Temp(C)' , 'Freq(MHz)', 'Vbat(Volt)', 'Pwr In(dBm)' ]:

           # if we cant even find the main columns in the data then give up
           if ( c not in self.data ) : return 0
          
           ctxt =  cond_txt + c
#          print '(check_nominal_condition) checking ', c , self.data[ c ][rn], self.ref[ ctxt ]
           if  (ctxt not in self.ref)  or not self.compare_values( self.data[ c ][rn], self.ref[ ctxt ]) :  
              ret_val = 0


       # ok we didn't make a match with the exact reference values,
       #  lets look to see if the segment reference value is a wildcard, and check for a match with that
       if ret_val == 0:
           cond_txt = self.data[ 'HB_LB' ] [ rn ]  + ',*,' +  self.data[ 'Process' ] [ rn ] + ','

           ret_val = 1
           for c in [ 'Temp(C)' , 'Freq(MHz)', 'Vbat(Volt)', 'Pwr In(dBm)' ]:

               # if we cant even find the main columns in the data then give up
               if ( c not in self.data ) : return 0
              
               
               ctxt =  cond_txt + c
               if  (ctxt not in self.ref) or not self.compare_values( self.data[ c ][rn] , self.ref[ ctxt ] ) :  
                      ret_val = 0


       return ret_val










###################################################################################################

    def add_all_limits( self, name, x, y , c, d, rn ) :

        x,y =  self.make_data_monatonic(  x , y )

        if name == 'Gain AM/(VAM-offset) (dB) <emp-limits>' :
            self.add_plot_emp_gain_limits( name, x, y , c, d, rn )

        elif name == 'Gain AM/(VAM-offset) Slope - Ref (dB/dB) <emp-limits>' :
            self.add_plot_emp_gain_slope_limits( name, x, y , c, d, rn )

        elif name == 'AM-PM Slope - Ref (deg/dB) <emp-limits>' :
            self.add_plot_emp_phase_slope_limits( name, x, y , c, d, rn )



###################################################################################################
    def add_spec_limits( self, color, dashes ) :
           

           # check that the plot limit value is in the right structure format

           if type( self.spec_limits ) != types.ListType: return

           # If the first element in the list is not a list then we must wrap another list round plot_limit
           if len( self.spec_limits ) > 1 :
               pl = self.spec_limits[0]
               if type( pl ) != types.ListType: 
                  self.spec_limits = [ self.spec_limits ] 

              
           for pl in self.spec_limits:

             # self.add_region_limit( None, None, c, d, lm, 2, 0, 0)
             
             #                         x      y               anotation text    line_thickness color 
             #  mag.spec_limits =  [ -19,  "3GPP min limit", line_thickness, blue ]
             #  mag.spec_limits =  [ [ [[0,-19], [20,-19]],  "3GPP min limit", line_thickness, blue ], ... ]


             lines = pl[0]
             if lines == None : continue

             if type( lines ) != types.ListType:
                xmin, xmax = xlim()
                pl[0] = [ [ xmin , lines ], [xmax , lines ] ]

             if pl[0][0][0]  == None or pl[0][1][0]  == None : continue
             if pl[0][0][1]  == None or pl[0][1][1]  == None : continue
                 
             lim = array( pl[0] )
             x = lim[ : , 0  ] 
             y = lim[ : , 1  ] 


             if len(pl) > 2 and pl[2] != None :  thickness = pl[2]
             else:                               thickness = 1
             if len(pl) > 3 and pl[3] != None :  color     = pl[3]
             if len(pl) > 4 and pl[4] != None :  dashes    = pl[4]

             self.ax.plot( x , y , color, dashes=dashes, linewidth=thickness)

             
             if len(pl) > 1 and pl[1] != None :  
                
                txtx = nu.mean(x)
                txty = nu.mean(y)
                text      = pl[1]
                annotate( text, xy=(txtx, txty),  color=color, textcoords='offset points', xytext=(0,3),
                    horizontalalignment='center', verticalalignment='bottom', fontsize=10)

#          self.spec_limits = None

             
###################################################################################################

    def add_plot_emp_gain_slope_limits( self, name, x, y , c, d, rn ) :

       if self.data[ 'HB_LB' ] [ rn ] == 'LB' or self.hblb == 'LB' :
#      if self.data[ 'HB_LB' ] [ rn ] == 'LB' :
           ref_pwr1 = 33.5
           ref_pwr2 = 25
    
           # Power region 1
           lim = array( [ [ 0   , +0.05],
                          [-25  , +0.05 ],
                          [  0  , -0.05 ],
                          [-25  , -0.05 ] ]    )
    
           ref_pwr = ref_pwr1
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    
    
           # Power region 2
           lim = array( [ [ 0   , +0.10 ],
                          [-23  , +0.10 ],
                          [  0  , -0.10 ],
                          [-23  , -0.10 ] ]    )
    
           ref_pwr = ref_pwr2
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    
    
           # Power region 3
           lim = array( [ [ 0   , +0.15 ],
                          [-23  , +0.15 ],
                          [  0  , -0.15 ],
                          [-23  , -0.15 ] ]    )
    
           ref_pwr = ref_pwr2-6.0
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    
    
           # Power region 4
           lim = array( [ [ 0   , +0.15 ],
                          [-21  , +0.15 ],
                          [  0  , -0.15 ],
                          [-21  , -0.15 ] ]    )
    
           ref_pwr = ref_pwr2-12.0
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    
    
    
           # Power region 5
           lim = array( [ [ 0   ,  +0.20 ],
                          [-20.5 , +0.20 ],
                          [  0  ,  -0.20 ],
                          [-20.5,  -0.20 ] ]    )
    
           ref_pwr = ref_pwr2-16.0
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    



       elif self.data[ 'HB_LB' ] [ rn ] == 'HB' or self.hblb == 'HB' :
#      elif self.data[ 'HB_LB' ] [ rn ] == 'HB'  :

           ref_pwr1 = 30.7
           ref_pwr2 = 22
    
           # Power region 1
           lim = array( [ [ 0   , +0.05 ],
                          [-25  , +0.05 ],
                          [  0  , -0.05 ],
                          [-25  , -0.05 ] ]    )
    
           ref_pwr = ref_pwr1
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    
    
           # Power region 2
           lim = array( [ [ 0   , +0.10 ],
                          [-23  , +0.10 ],
                          [  0  , -0.10 ],
                          [-23  , -0.10 ] ]    )
    
           ref_pwr = ref_pwr2
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    
    
           # Power region 3
           lim = array( [ [ 0   , +0.15 ],
                          [-23  , +0.15 ],
                          [  0  , -0.15 ],
                          [-23  , -0.15 ] ]    )
    
           ref_pwr = ref_pwr2-6.0
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    
    
           # Power region 4
           lim = array( [ [ 0   , +0.15 ],
                          [-21  , +0.15 ],
                          [  0  , -0.15 ],
                          [-23  , -0.15 ] ]    )
    
           ref_pwr = ref_pwr2-12.0
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    
    
    
           # Power region 5
           lim = array( [ [ 0   ,  +0.20 ],
                          [-20.5 , +0.20 ],
                          [  0  ,  -0.20 ],
                          [-20.5,  -0.20 ] ]    )
    
           ref_pwr = ref_pwr2-16.0

           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)





###################################################################################################

    def add_plot_emp_phase_slope_limits( self, name, x, y , c, d, rn ) :

       if self.data[ 'HB_LB' ] [ rn ] == 'LB'  or self.hblb == 'LB':
#      if self.data[ 'HB_LB' ] [ rn ] == 'LB'  :
           ref_pwr1 = 33.5
           ref_pwr2 = 25
    
           # Power region 1
           lim = array( [ [ 0   , +0.50],
                          [-25  , +0.50 ],
                          [  0  , -0.50 ],
                          [-25  , -0.50 ] ]    )
    
           ref_pwr = ref_pwr1
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    
    
           # Power region 2
           lim = array( [ [ 0   , +1.00 ],
                          [-23  , +1.00 ],
                          [  0  , -1.00 ],
                          [-23  , -1.00 ] ]    )
    
           ref_pwr = ref_pwr2
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    
    
           # Power region 3
           lim = array( [ [ 0   , +1.00 ],
                          [-23  , +1.00 ],
                          [  0  , -1.00 ],
                          [-23  , -1.00 ] ]    )
    
           ref_pwr = ref_pwr2-6.0
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    
    
           # Power region 4
           lim = array( [ [ 0   , +1.50 ],
                          [-21  , +1.50 ],
                          [  0  , -1.50 ],
                          [-21  , -1.50 ] ]    )
    
           ref_pwr = ref_pwr2-12.0
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    
    
    
           # Power region 5
           lim = array( [ [ 0   ,  +1.50 ],
                          [-20.5 , +1.50 ],
                          [  0  ,  -1.50 ],
                          [-20.5,  -1.50 ] ]    )
    
           ref_pwr = ref_pwr2-16.0
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    



       elif self.data[ 'HB_LB' ] [ rn ] == 'HB' or self.hblb == 'HB' :
#      elif self.data[ 'HB_LB' ] [ rn ] == 'HB' :

           ref_pwr1 = 30.7
           ref_pwr2 = 22
    
           # Power region 1
           lim = array( [ [ 0   , +0.50 ],
                          [-25  , +0.50 ],
                          [  0  , -0.50 ],
                          [-25  , -0.50 ] ]    )
    
           ref_pwr = ref_pwr1
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    
    
           # Power region 2
           lim = array( [ [ 0   , +1.00 ],
                          [-23  , +1.00 ],
                          [  0  , -1.00 ],
                          [-23  , -1.00 ] ]    )
    
           ref_pwr = ref_pwr2
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    
    
           # Power region 3
           lim = array( [ [ 0   , +1.00 ],
                          [-23  , +1.00 ],
                          [  0  , -1.00 ],
                          [-23  , -1.00 ] ]    )
    
           ref_pwr = ref_pwr2-6.0
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    
    
           # Power region 4
           lim = array( [ [ 0   , +1.50 ],
                          [-21  , +1.50 ],
                          [  0  , -1.50 ],
                          [-23  , -1.50 ] ]    )
    
           ref_pwr = ref_pwr2-12.0
           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)
    
    
    
           # Power region 5
           lim = array( [ [ 0   ,  +1.50 ],
                          [-20.5 , +1.50 ],
                          [  0  ,  -1.50 ],
                          [-20.5,  -1.50 ] ]    )
    
           ref_pwr = ref_pwr2-16.0

           self.add_region_limit( x, y, c, d, lim, 2, ref_pwr, 0)


###################################################################################################

    def make_data_monatonic( self, x , y ):

       #Check that all values in x are increasing and monoatonic 
       # if not then discard the rotton x and y values

       if len(x) == 0 or len(y) == 0: return x,y

       x_new = []
       y_new = []
 

       xi_old = x[0] - 1.0
       for xi,yi in zip(x,y):
         if xi > xi_old :
           x_new.append(xi)
           y_new.append(yi)
         xi_old = xi

       return x_new, y_new

###################################################################################################

    def remove_bad_data( self, x,y,rnl, xslim, yslim ):


       #Check that all values in x are valid numbers
       # if not then discard the rotton x and y values

       # also if the any of the values are greater than the axes limit value then
       # limit the value in the plot to 10x the axes limit , this stops matplotlib trying to render hopelessly large graphs (I think)


       x_new = []
       y_new = []
       rnl_new = []

       maxscale = 10
       if xslim != []:    
            diff = abs( xlimits[1] - xlimits[0] ) + maxscale
            xlimits = [ xslim[0] - diff ,  xslim[1] + diff  ]
       if yslim != []:    
            diff = abs( ylimits[1] - ylimits[0] ) + maxscale
            ylimits = [ yslim[0] - diff ,  yslim[1] + diff  ]

       for xi,yi,rni in zip(x,y,rnl):
         if not isnan(xi) and not isnan(yi):

           if xslim != []:

              if xi > xlimits[1] : xi = xlimits[1]
              if xi < xlimits[0] : xi = xlimits[0]

           x_new.append(xi)

           if yslim != []:
              if yi > ylimits[1] : yi = ylimits[1]
              if yi < ylimits[0] : yi = ylimits[0]

           y_new.append(yi)
           rnl_new.append(rni)
          
       return x_new, y_new, rnl_new

###################################################################################################

    def add_plot_emp_gain_limits( self, name, x, y , c, d, rn ) :

       # check to see if this plot is for the nominal condition



       if len(x) == 0 or len(y) == 0 : return

       if self.data[ 'HB_LB' ] [ rn ] == 'LB' or self.hblb == 'LB':
#      if self.data[ 'HB_LB' ] [ rn ] == 'LB':
           ref_pwr1 = 33.5
           ref_pwr2 = 25
    
           # Power region 1
           lim = array( [ [ 0   , +4.4 ],
                          [-3.5 , +6.0 ],
                          [-25  , +6.0 ],
                          [  0  , -2.5 ],
                          [-5.8 , -2.5 ],
                          [-5.8 , -7.3 ],
                          [-25  ,-18.3 ] ]    )
    
           ref_pwr = ref_pwr1
           [ref_gain] = stineman_interp([ref_pwr],x,y)
           self.add_region_limit( x, y, c, d, lim, 3, ref_pwr, ref_gain )
    
    
           # Power region 2
           lim = array( [ [ 0   , +4.4 ],
                          [-3.5 , +6.0 ],
                          [-23  , +6.0 ],
                          [  0  , -2.5 ],
                          [-3.9 , -2.5 ],
                          [-3.9 , -6.2 ],
                          [-23  ,-16.2 ] ]    )
    
           ref_pwr = ref_pwr2
           [ref_gain] = stineman_interp([ref_pwr],x,y)
           self.add_region_limit( x, y, c, d, lim, 3, ref_pwr, ref_gain )
    
    
           # Power region 3
           lim = array( [ [ 0   , +4.4 ],
                          [-3.5 , +6.0 ],
                          [-23  , +6.0 ],
                          [  0  , -2.5 ],
                          [-3.7 , -2.5 ],
                          [-3.7 , -6.1 ],
                          [-23  ,-16.1 ] ]    )
    
           ref_pwr = ref_pwr2-6.0
           [ref_gain] = stineman_interp([ref_pwr],x,y)
           self.add_region_limit( x, y, c, d, lim, 3, ref_pwr, ref_gain )
    
    
           # Power region 4
           lim = array( [ [ 0   , +4.4 ],
                          [-3.5 , +6.0 ],
                          [-21  , +6.0 ],
                          [  0  , -2.5 ],
                          [-1.2 , -2.5 ],
                          [-1.2 , -5.0 ],
                          [-21  ,-14.3 ] ]    )
    
           ref_pwr = ref_pwr2-12.0
           [ref_gain] = stineman_interp([ref_pwr],x,y)
           self.add_region_limit( x, y, c, d, lim, 3, ref_pwr, ref_gain )
    
    
    
           # Power region 5
           lim = array( [ [ 0   , +4.4 ],
                          [-3.5 , +6.0 ],
                          [-20.5 , +6.0 ],
                          [  0  , -2.5 ],
                          [-3.3 , -2.5 ],
                          [-3.3 , -5.8 ],
                          [-20.5,-14.5 ] ]    )
    
           ref_pwr = ref_pwr2-16.0
           [ref_gain] = stineman_interp([ref_pwr],x,y)
           self.add_region_limit( x, y, c, d, lim, 3, ref_pwr, ref_gain )
    



       elif self.data[ 'HB_LB' ] [ rn ] == 'HB' or self.hblb == 'HB' :
#      elif self.data[ 'HB_LB' ] [ rn ] == 'HB':

           ref_pwr1 = 30.7
           ref_pwr2 = 22
    
           # Power region 1
           lim = array( [ [ 0   , +4.4 ],
                          [-3.5 , +6.0 ],
                          [-25  , +6.0 ],
                          [  0  , -2.5 ],
                          [-5.9 , -2.5 ],
                          [-5.9 , -7.3 ],
                          [-25  ,-18.4 ] ]    )
    
           ref_pwr = ref_pwr1
           [ref_gain] = stineman_interp([ref_pwr],x,y)
           self.add_region_limit( x, y, c, d, lim, 3, ref_pwr, ref_gain )
    
    
           # Power region 2
           lim = array( [ [ 0   , +4.4 ],
                          [-3.5 , +6.0 ],
                          [-23  , +6.0 ],
                          [  0  , -2.5 ],
                          [-3.7 , -2.5 ],
                          [-3.7 , -6.1 ],
                          [-23  ,-16.1 ] ]    )
    
           ref_pwr = ref_pwr2
           [ref_gain] = stineman_interp([ref_pwr],x,y)
           self.add_region_limit( x, y, c, d, lim, 3, ref_pwr, ref_gain )
    
    
           # Power region 3
           lim = array( [ [ 0   , +4.4 ],
                          [-3.5 , +6.0 ],
                          [-23  , +6.0 ],
                          [  0  , -2.5 ],
                          [-3.5 , -2.5 ],
                          [-3.5 , -6.0 ],
                          [-23  ,-15.9 ] ]    )
    
           ref_pwr = ref_pwr2-6.0
           [ref_gain] = stineman_interp([ref_pwr],x,y)
           self.add_region_limit( x, y, c, d, lim, 3, ref_pwr, ref_gain )
    
    
           # Power region 4
           lim = array( [ [ 0   , +4.4 ],
                          [-3.5 , +6.0 ],
                          [-21  , +6.0 ],
                          [  0  , -2.5 ],
                          [-3.3 , -2.5 ],
                          [-3.3 , -5.8 ],
                          [-23  ,-15.9 ] ]    )
    
           ref_pwr = ref_pwr2-12.0
           [ref_gain] = stineman_interp([ref_pwr],x,y)
           self.add_region_limit( x, y, c, d, lim, 3, ref_pwr, ref_gain )
    
    
    
           # Power region 5
           lim = array( [ [ 0   , +4.4 ],
                          [-3.5 , +6.0 ],
                          [-20.5 , +6.0 ],
                          [  0  , -2.5 ],
                          [-3.3 , -2.5 ],
                          [-3.3 , -5.8 ],
                          [-20.5,-14.5 ] ]    )
    
           ref_pwr = ref_pwr2-16.0

           [ref_gain] = stineman_interp([ref_pwr],x,y)
           self.add_region_limit( x, y, c, d, lim, 3, ref_pwr, ref_gain )




###################################################################################################

    def add_region_limit( self, x, y, c, d, lim, seperate, offset_x, offset_y) :

       

       # draw the upper limit
       x = lim[ :seperate , 0  ] + offset_x
       y = lim[ :seperate , 1  ] + offset_y
       self.ax.plot( x , y , c, dashes=d)

       # draw the lower limit

       if seperate > 0 :
         x = lim[ seperate: , 0  ] + offset_x
         y = lim[ seperate: , 1  ] + offset_y
         self.ax.plot( x , y ,c, dashes=d)


###################################################################################################
###################################################################################################


    def line_select_callback(self, event1, event2):
        'event1 and event2 are the press and release events'
        x1, y1 = event1.xdata, event1.ydata
        x2, y2 = event2.xdata, event2.ydata
        print "(%3.2f, %3.2f) --> (%3.2f, %3.2f)"%(x1,y1,x2,y2)
        print " The button you used were: ",event1.button, event2.button
    
###################################################################################################
    
    def loop( self ):

        #-------------------------------------------------------------------------------
        # After all the non-interactive plots have been run, wait in this Tk mainloop for interactive gui actions to occur
        # This function needs to be added to the end of every script
        #-------------------------------------------------------------------------------\

        # update the filters 
        self.wupdate_filter_cond_list( None ) 
        self.vlist.delete_all()                

        self.gen_values_dict()
        self.root.update()

        self.run_mode = 'gui'
        print '  ...waiting for user input'
        self.status.set( 'waiting for user input' )

        Tk.mainloop()



###################################################################################################
    def get_cond_str_from_rn( self, rn ):

        ''' Make up a string with all the conditions found for a gine record number in the data array '''


        tstr = ''
        opstr = '' 
        col = 'linenumber'
        tstr = tstr + '%s=%s \n' % ( col, self.truncate_value( self.data[col][rn]) )
        for col in self.value_dict_names:
          
#         print  '(get_cond_str_from_rn)', col, len( self.values_dict_count[ col ] )

          if col not in [ 'TestName' , 'HB_LB' ]:
             if len( self.values_dict_count[col] ) > 1:
                if col[0] == '@' : continue
                tstr = tstr + '%s=%s ' % ( col, self.truncate_value( self.data[col][rn]) )
#               if len(tstr) > 40:
                if len(tstr) > 1:
                   opstr = opstr + '\n' + tstr
                   tstr = ''
                    

        if len(tstr) > 1:
                opstr = opstr + '\n' + tstr
         
        if len(opstr)> 1: opstr = opstr[1:]

        return opstr


###################################################################################################
#### FUNCTIONS FOR PICKING OBJECTS ON THE CANVAS
###################################################################################################

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 

    #pick up the legend patch
    def my_legend_picker(self, legend, event):
        return self.legend.legendPatch.contains(event)


# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 
#   def on_key_press( self, event  ):
#
#      if event.name == 'key_press_event':
#          self.key = event.key
#    
#      
#      print '(on_key_press)', event.name, self.key
#      pass
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 
#   def on_key_release( self, event  ):
#
#      if event.name == 'key_release_event':
#          self.key = 'None'
#      
#      print '(on_key_release)', event.name, self.key
#      pass
#
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 


    def on_button_release( self, event  ):

#       print '(on_button_release)', event.__dict__
#       self.key = event.key

        if self.gotLegend == 1:
            self.gotLegend = 0
            # write the legend location back to the format tab entry box
            txt = '%0.3f %0.3f' % ( self.legend_location[0], self.legend_location[1] )
            self.wlegend_location.set( txt )
        self.pick_count_total = 0   
        self.pick_data = False
	self.something_picked = False
        if self.sel_object != None and self.key != 'shift':
#          print '(on_button_release)', self.sel_object, self.key, event.__dict__
#          x = self.sel_object.findobj()
	   x = gca()
 #         print 'dir  gca ', dir( x.texts )
           del gca().texts[-1]


        if self.sel_object == None and self.key == 'control':
	   x = gca()
           del gca().texts[-1]



        self.canvas.draw()

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 


    def on_motion( self, event  ):


#       print '(on_motion)', self.pick_data, event.button

        if self.something_picked:
                mouse_diff_x = self.mouse_pick_x - event.x  #how much the mouse moved.
                mouse_diff_y = self.mouse_pick_y - event.y

                #move the legend from its previous location by that same amount
                loc_in_canvas = self.pick_min_x - mouse_diff_x, self.pick_min_y - mouse_diff_y
                if  matplotlib.__version__ == '0.91.2':
                    loc_in_norm_axes = self.legend.parent.transAxes.inverse_xy_tup(loc_in_canvas) 
                else:
                    loc_in_norm_axes = self.legend.parent.transAxes.inverted().transform_point(loc_in_canvas)

                self.selected_location     = loc_in_norm_axes

        if self.gotLegend == 1:
                self.legend._loc = tuple(loc_in_norm_axes)


	if self.pick_data:
	       
#              print '(on_motion) about to set_position to:', loc_in_norm_axes, tuple(loc_in_norm_axes)
#	       print '(on motion) dir gca:', dir( gca().texts[-1] ) 
#	       gca().texts[-1].set_position( loc_in_norm_axes )
#              setp( gca().texts[-1], position=tuple(loc_in_norm_axes) )
#              gca().texts[-1].set_position( tuple(loc_in_norm_axes) )
#              gca().texts[-1].set_x( tuple(loc_in_norm_axes)[0] )
#              gca().texts[-1].set_y( tuple(loc_in_norm_axes)[1] )
#              gca().texts[-1]._x = tuple(loc_in_norm_axes)[1]
#              gca().texts[-1]._y = tuple(loc_in_norm_axes)[1]
                
               gca().texts[-1].xytext = [ event.xdata, event.ydata ]


#              gca().texts[-1]._loc = tuple( [25,30] )
#              print 'gca().texts[-1].__dict__' , gca().texts[-1].__dict__
#              print 'dir( gca().texts[-1])' , dir(  gca().texts[-1] )
#              print 'gca().texts[-1].get_position()', gca().texts[-1].get_position()

#              print 'event.__dict__', event.__dict__
#              print 'gca().texts[-1].xy', gca().texts[-1].xy
#              print 'gca().texts[-1].xycoords', gca().texts[-1].xycoords
#              print 'gca().texts[-1].xytext', gca().texts[-1].xytext

        self.canvas.draw()
#           self.parent.Refresh() 

        if self.pick_data:
            mouse_diff_x = self.mouse_pick_x - event.x  #how much the mouse moved.
            mouse_diff_y = self.mouse_pick_y - event.y

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 


    def on_button_press( self, event  ):
          self.key = event.key
          if self.pick_data:
#             print '(on_button_press) :', self.pick_count, self.pick_count_total
                   
              thisline = self.series_picked[ self.pick_count ]
              grps =  re.search( r'Line2D\((.*)\)', str(thisline) )
              if grps and self.pick_count_total > 0:
                self.pick_count = (self.pick_count) % self.pick_count_total 
                self.pick_data = True
                sn = grps.groups()[0]
                xdata = thisline.get_xdata()
                ydata = thisline.get_ydata()
                ind = self.series_picked_ind[ self.pick_count ]
                
#               print '(on_button_press) onpick points:', sn ,ind
#               print '(on_button_press) onpick points:', thisline, ind, self.xdata[ sn ][ ind ], self.ydata[ sn ][ ind ]

                try:
                   rn = self.rndata[ sn ][ ind ]
                   cond_str = self.get_cond_str_from_rn( rn )
                   txt = 'X=%0.3f     Y=%0.3f\n%s\n%s' % (self.xdata[ sn ][ ind ], self.ydata[ sn ][ ind ], sn, cond_str)
   
   
                   v = self.ax.get_xlim()
                   xinc = abs( v[0]-v[1] ) * 0.1
                   v = self.ax.get_ylim()
                   yinc = abs( v[0]-v[1] ) * 0.1
                   xy_data = (self.xdata[ sn ][ ind ], self.ydata[ sn ][ ind ])
                   xy_text = (xy_data[0]-xinc , xy_data[1]+yinc)
   
                   if sn in self.data_color:
                      arrow_color = self.data_color[ sn ]
                   else:
                      arrow_color = 'black'
    
                   self.sel_object = self.ax.annotate( txt, xy=xy_data,  
                       horizontalalignment='left', verticalalignment='bottom', fontsize=9,
                       xytext=xy_text, textcoords='data',
    #                  xytext=(-50, 30), textcoords='offset points',
    #                   arrowprops=dict(arrowstyle="->"),
    #                   bbox=dict(boxstyle="round", fc="0.8"),
                       arrowprops=dict(facecolor=arrow_color, edgecolor=arrow_color, shrink=0.02,width=0.1,headwidth=4, alpha=1),
    
                   )
   #            		print 'get_position = ',  self.sel_object.get_position()
                   self.pick_min_x = self.sel_object.get_position()[0]
                   self.pick_min_y = self.sel_object.get_position()[1]
                   
   
                   self.canvas.draw()
   #               print '(on_button_press) self.sel_object', dir( self.sel_object )
                   self.pick_count = (self.pick_count + 1) % self.pick_count_total 
   
                except Exception:
                   self.pick_data = False
                   print "(on_button_press) Line not found in self.rndata dict,  clicked on line '%s', ind=%s\n  List of lines available:" % ( str(sn), str(ind) )
                   for s in self.rndata:
                      print '                     ', s




# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 

          
    def on_pick( self, event  ):
         legend = self.legend

         self.mouse_pick_x = event.mouseevent.x  #get mouse coordinates at time of pick in pixel units.
         self.mouse_pick_y = event.mouseevent.y
         self.mouse_pick_xdata = event.mouseevent.xdata  #get mouse coordinates at time of pick in data units
         self.mouse_pick_ydata = event.mouseevent.ydata

         # move the legend
         if event.artist == legend: 
             bbox = self.legend.get_window_extent()  #gets the box of the legend.
	     self.something_picked = True
             self.gotLegend  = 1

	 if self.gotLegend :
             if  matplotlib.__version__ == '0.91.2':
               self.pick_min_x = bbox.xmin()          #get legend coordinates at time of pick.
               self.pick_min_y = bbox.ymin() 
             else:
               self.pick_min_x = bbox.xmin            #get legend coordinates at time of pick.
               self.pick_min_y = bbox.ymin 
         

   
	     
         # Add a data label at the clicked point    
         
         # This function will be run multiple times for each button press, once for each thing picked under the mouse.
         # If its a line then it will return a list of data points indexes on the line which fall within the picker window
         # We will only select points for which the DATA point is close to the button click positions.
         # (it selects data points if the line is close button click) Therefore we must look at each data point and 
         # see if it falls within our mouse click range.

         # However, there may be more than one data point close to the position clicked
         # in which case we must 
         thisline = event.artist 
         grps =  re.search( r'Line2D\((.*)\)', str(thisline) )
         if grps:
                self.pick_data = True
	        self.something_picked = True
                sn = grps.groups()[0]
                xdata = thisline.get_xdata()
                ydata = thisline.get_ydata()
                ind = event.ind
                # ind may be a list of picked series, if it is get the mid series
                v = self.ax.get_xlim()
                xinc = abs( v[0]-v[1] ) * 0.01
                v = self.ax.get_ylim()
                yinc = abs( v[0]-v[1] ) * 0.01
                
                if type( ind ) != types.IntType:
                   for i  in ind:

#                    print '(on_pick)', self.mouse_pick_xdata, xinc, self.mouse_pick_ydata, yinc, xdata[i], ydata[i]
                     if (self.mouse_pick_xdata-xinc  < xdata[i] < self.mouse_pick_xdata+xinc ) and \
                        (self.mouse_pick_ydata-yinc  < ydata[i] < self.mouse_pick_ydata+yinc ) :

                        self.series_picked[ self.pick_count_total ] = thisline
                        self.series_picked_ind[ self.pick_count_total ] = i
                        self.pick_count_total += 1
#                       print'(on_pick)X: mouse_pos=[%s:%s]  series_picked=%s ind=%s data=[%s:%s]'% (self.mouse_pick_xdata, self.mouse_pick_ydata, thisline, i, xdata[i], ydata[i]) 
                     else:
#                       print'(on_pick) . mouse_pos=[%s:%s]  series_picked=%s ind=%s data=[%s:%s]'% (self.mouse_pick_xdata, self.mouse_pick_ydata, thisline, i, xdata[i], ydata[i]) 
                        pass
                else:
                     i = ind

                     if (self.mouse_pick_xdata-xinc  < xdata[i] < self.mouse_pick_xdata+xinc ) and \
                        (self.mouse_pick_ydata-yinc  < ydata[i] < self.mouse_pick_ydata+yinc ) :

                        self.series_picked[ self.pick_count_total ] = thisline
                        self.series_picked_ind[ self.pick_count_total ] = i
                        self.pick_count_total += 1
#                       print'(on_pick)X: mouse_pos=[%s:%s]  series_picked=%s ind=%s data=[%s:%s]'% (self.mouse_pick_xdata, self.mouse_pick_ydata, thisline, i, xdata[i], ydata[i]) 
                     else:
#                       print'(on_pick) . mouse_pos=[%s:%s]  series_picked=%s ind=%s data=[%s:%s]'% (self.mouse_pick_xdata, self.mouse_pick_ydata, thisline, i, xdata[i], ydata[i]) 
                        pass
                self.pick_min_x = event.mouseevent.x
                self.pick_min_y = event.mouseevent.y

                
         self.pick = str( event.artist )
         self.status.set( self.pick )
         
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 
         

###################################################################################################
###################################################################################################


    def win_init( self ):


          #----------------------------------------
          # Draw the main matplot graph plotting area
          #----------------------------------------

          #self.fig = figure(figsize=(11,5))
          self.fig = figure(figsize=(12,6))
#         print 'dir self.fig', dir( self.fig )
          self.mgr = get_current_fig_manager()
          self.mgr.set_window_title("Results Plotter    - " )
#         print 'dir self.mgr', dir( self.mgr )
          #ax = subplot(111)
          self.ax = self.fig.add_subplot(1,1,1)
#         print 'dir self.ax', dir( self.ax )
 #         RS = RectangleSelector( self.ax,  self.line_select_callback, drawtype='box',useblit=True)

          self.fig.subplots_adjust( left=self.plot_position[0], right=self.plot_position[1], top=self.plot_position[2], bottom=self.plot_position[3]  )



 
          #----------------------------------------
          # Create a Tk control window area 
          #----------------------------------------

          self.root = Tix.Tk()
          z = self.root.winfo_toplevel()
          z.wm_title('PYGRAM Graphing Tool  version:  ' + self.pygram_version )

          ctlfrm = Tix.Frame(self.root, name='ctlfrm')
          ctlfrm.pack(expand=0, fill=Tix.BOTH, padx=0, pady=0 ,side=Tix.LEFT)
          



          #----------------------------------------
          # Create a set of buttons at the bottom 
          #----------------------------------------

          butfrm = Tix.Frame(ctlfrm, name='butfrm')
          butfrm.pack( padx=0, pady=0 ,side=Tix.BOTTOM)
          
          plotgr  = Tix.Button(butfrm, name='plotgr',  text='Plot',          width=5, height=2, command=self.plot_interactive_graph  ) .grid( column=0, row=0, sticky=Tix.S)
          printgr = Tix.Button(butfrm, name='save',    text='Save\nPlot',    width=5, height=2, command=self.save_plot)                      .grid( column=1, row=0, sticky=Tix.S)
          export  = Tix.Button(butfrm, name='export',  text='Export\nExcel', width=5, height=2, command=self.save_excel)                .grid( column=2, row=0, sticky=Tix.SW)
          quit    = Tix.Button(butfrm, name='quit',    text='Quit',          width=5, height=2, command=sys.exit    )                  .grid( column=3, row=0, sticky=Tix.S)
          






          #----------------------------------------
          # Create a 'notebook' area with multiple tabs to allow the user to load log files and specify the x and y axes, and filter conditions
          #----------------------------------------

          self.nb = Tix.NoteBook(ctlfrm, name='nb', ipadx=0, ipady=0)
          self.nb['bg'] = 'gray'
          #nb.nbframe['backpagecolor'] = 'gray'
          
          tb = self.nb.add('load',   label="Load",   underline=0)     
          self.nb.add('xaxis',  label="Xaxis",  underline=0)
          self.nb.add('yaxis',  label="Yaxis",  underline=0)
          self.nb.add('filter', label="Filter", underline=0)
          self.nb.add('distortion',  label="Dist",  underline=0)
          self.nb.add('format',  label="Format",  underline=0)
          self.nb.pack(expand=1, fill=Tix.BOTH, padx=0, pady=0 ,side=Tix.TOP)
          






          #----------------------------------------
          # Create the Load File Tab Page
          #----------------------------------------
           
          tab=self.nb.load
          tabfrm = Tix.Frame(tab, name='frm')
          tabfrm.pack(side=Tix.TOP, padx=2)


          scrollbar = Tk.Scrollbar(tabfrm, orient=Tk.VERTICAL)
          listbox   = Tk.Listbox(tabfrm, name='lb', width=40, height=15, yscrollcommand=scrollbar.set)
          scrollbar.config(command=listbox.yview)

          listbox.grid  (columnspan=3, column=1, row=0, sticky='w' )
          scrollbar.grid(              column=4, row=0, sticky='wns' )

          loadfile     = Tix.Button(tabfrm, name='loadfile',  text='Load\nLogfile',   width=6, command=self.wloadfile  ) .grid( column=1, row=1 )
          loaddb       = Tix.Button(tabfrm, name='loaddb',  text='Load\nDataPower',   width=6, command=self.wloaddb  )   .grid( column=2, row=1 )
          clearfile    = Tix.Button(tabfrm, name='clearfile', text='Reset\nLogfiles', width=6, command=self.wclearfiles) .grid( column=3, row=1 )


          # insert the already loaded logfiles into the listbox

          self.logfiles = listbox
          #for f in  self.logfilenames :
          #  self.logfiles.insert( Tk.END, f )






          #----------------------------------------
          # Create the Distortion Tab Page
          #----------------------------------------
           
          tab=self.nb.distortion
          tabfrm = Tix.Frame(tab, name='dist')
          tabfrm.pack( side=Tix.TOP, padx=2)


          # distortion reference settings

          fsz = 10
          Tk.Label( tabfrm, text='\n\n\n---------------------------------------------------\nEdge Distortion Reference Conditions\n',  font=("Helvetica", fsz) )   .grid( column=0, row=2, columnspan=4, sticky='w')


          self.vam_offset_entry   =  Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='VAM Offset (v):',  font=("Helvetica", fsz) )   .grid( column=0, row=3, columnspan=2, sticky='w')
          Tk.Entry( tabfrm, width=22, textvariable=self.vam_offset_entry )        .grid( column=2, row=3, columnspan=2, sticky='w')

          # Set reference condition for process
          self.dist_process   =  Tk.StringVar(master=tabfrm)
          dist_process_w = Tix.ComboBox(tabfrm, label="Process:", dropdown=1, name='dist_process', editable=1,
              variable=self.dist_process,
              options='listbox.height 5  listbox.width 55 entry.width 30 label.width 10 label.anchor w entry.state normal')
          dist_process_w.grid( columnspan=4, column=0, row=5 )
          self.dist_process_w = dist_process_w

          # Set reference condition for temp
          self.dist_temp   =  Tk.StringVar(master=tabfrm)
          dist_temp_w = Tix.ComboBox(tabfrm, label="Temp:", dropdown=1, name='dist_temp', editable=1,
              variable=self.dist_temp,
              options='listbox.height 5  listbox.width 55 entry.width 30 label.width 10 label.anchor w entry.state normal')
          dist_temp_w.grid( columnspan=4, column=0, row=6 )
          self.dist_temp_w = dist_temp_w

          # Set reference condition for hblb
          self.dist_hblb   =  Tk.StringVar(master=tabfrm)
          dist_hblb_w = Tix.ComboBox(tabfrm, label="HB/LB:", dropdown=1, name='dist_hblb', editable=1,
              variable=self.dist_hblb,
              options='listbox.height 5  listbox.width 55 entry.width 30 label.width 10 label.anchor w entry.state normal')
          dist_hblb_w.grid( columnspan=4, column=0, row=7 )
          self.dist_hblb_w = dist_hblb_w

          # Set reference condition for seg
          self.dist_seg   =  Tk.StringVar(master=tabfrm)
          dist_seg_w = Tix.ComboBox(tabfrm, label="Seg:", dropdown=1, name='dist_seg', editable=1,
              variable=self.dist_seg,
              options='listbox.height 5  listbox.width 55 entry.width 30 label.width 10 label.anchor w entry.state normal')
          dist_seg_w.grid( columnspan=4, column=0, row=8 )
          self.dist_seg_w = dist_seg_w

          # Set reference condition for freq
          self.dist_freq   =  Tk.StringVar(master=tabfrm)
          dist_freq_w = Tix.ComboBox(tabfrm, label="Freq:", dropdown=1, name='dist_freq', editable=1,
              variable=self.dist_freq,
              options='listbox.height 10  listbox.width 55 entry.width 30 label.width 10 label.anchor w entry.state normal')
          dist_freq_w.grid( columnspan=4, column=0, row=9 )
          self.dist_freq_w = dist_freq_w

          # Set reference condition for vbat
          self.dist_vbat   =  Tk.StringVar(master=tabfrm)
          dist_vbat_w = Tix.ComboBox(tabfrm, label="Vbat:", dropdown=1, name='dist_vbat', editable=1,
              variable=self.dist_vbat,
              options='listbox.height 5  listbox.width 55 entry.width 30 label.width 10 label.anchor w entry.state normal')
          dist_vbat_w.grid( columnspan=4, column=0, row=10 )
          self.dist_vbat_w = dist_vbat_w

          # Set reference condition for pin
          self.dist_pin   =  Tk.StringVar(master=tabfrm)
          dist_pin_w = Tix.ComboBox(tabfrm, label="Pin:", dropdown=1, name='dist_pin', editable=1,
              variable=self.dist_pin,
              options='listbox.height 5  listbox.width 55 entry.width 30 label.width 10 label.anchor w entry.state normal')
          dist_pin_w.grid( columnspan=4, column=0, row=11 )
          self.dist_pin_w = dist_pin_w

          # Set reference logfilename
          self.dist_logfilename   =  Tk.StringVar(master=tabfrm)
          dist_logfilename_w = Tix.ComboBox(tabfrm, label="Logfilename:", dropdown=1, name='dist_logfilename', editable=1,
              variable=self.dist_logfilename,
              options='listbox.height 5  listbox.width 55 entry.width 30 label.width 10 label.anchor w entry.state normal')
          dist_logfilename_w.grid( columnspan=4, column=0, row=12 )
          self.dist_logfilename_w = dist_logfilename_w


          Tix.Button(tabfrm, name='add_dist_ref',  text='Add Distortion Reference',  command=self.wadd_vam_pout_columns  )   .grid( column=0,columnspan=4,  row=13 )








          #----------------------------------------
          # Create an alphabetically ordered list of column names, this is the list that the user will
          # choose for the X and Y axes
          #----------------------------------------

        # cll = []
        # for n in  self.data:
        #    if n != '' :
        #       cll.append(n)
        # cll.sort()




          #----------------------------------------
          # Create the Xaxis and Yaxis Tab pages
          #----------------------------------------




          for xy in ('X', 'Y' ):

              # Define variables for the selected axes values.
  
              # A common name 'base_*' is used for both axes which is then 
              # assigned to the actual axis. This allows the code to be reused to 
              # define both axes.
              if xy == 'X' : 
                self.xaxis_tabfrm = tabfrm
                tab=self.nb.xaxis
                base_name     =  self.xname     = Tk.StringVar(master=tabfrm)
                base_text     =  self.xtext     = Tk.StringVar(master=tabfrm)
                base_full_list = self.xfull     = Tk.IntVar(master=tabfrm)
                base_scl_auto =  self.xscl_auto = Tk.IntVar(master=tabfrm)
                base_scl_max  =  self.xscl_max  = Tk.StringVar(master=tabfrm)
                base_scl_min  =  self.xscl_min  = Tk.StringVar(master=tabfrm)
                base_grd_step  =  self.xgrd_step  = Tk.StringVar(master=tabfrm)
              if xy == 'Y' : 
                self.yaxis_tabfrm = tabfrm
                tab=self.nb.yaxis
                base_name     =  self.yname     = Tk.StringVar(master=tabfrm)
                base_text     =  self.ytext     = Tk.StringVar(master=tabfrm)
                base_full_list = self.yfull     = Tk.IntVar(master=tabfrm)
                base_scl_auto =  self.yscl_auto = Tk.IntVar(master=tabfrm)
                base_scl_max  =  self.yscl_max  = Tk.StringVar(master=tabfrm)
                base_scl_min  =  self.yscl_min  = Tk.StringVar(master=tabfrm)
                base_grd_step  =  self.ygrd_step  = Tk.StringVar(master=tabfrm)
  
  


              # create a frame to put every thing into
              tabfrm = Tix.Frame(tab, name='frm')
              tabfrm.pack(side=Tix.TOP, padx=2)


              Tk.Label( tabfrm, text='Select %saxis From List:' % xy, font=("Helvetica", fsz) ) .grid( columnspan=2, column=0, row=1, sticky='w')
              Tk.Label( tabfrm, text='Full List',  font=("Helvetica", fsz) )               .grid( column=2, row=1, sticky='w')
              Tk.Checkbutton( tabfrm, variable=base_full_list, command=self.wupdate_column_lists) .grid( column=3, row=1, sticky='w')
              base_full_list.set( False )

              # Create a scrolled listbox to show the available axes names
              axis_sb = Tk.Scrollbar(tabfrm, orient=Tk.VERTICAL)
              names   = Tk.Listbox(tabfrm, name='lb', width=40, height=33, yscrollcommand=axis_sb.set, exportselection=0, selectmode=Tk.EXTENDED)
              axis_sb.config(command=names.yview)
  
              names                                                                  .grid( columnspan=3, column=0, row=2)
              axis_sb                                                                .grid( columnspan=3, column=3, row=2, sticky='wns')
  

              if xy == 'X' : 
                self.xaxis_col_list  = names
              if xy == 'Y' : 
                self.yaxis_col_list  = names
  
  
   
              # label to show the selected axis name
              Tk.Label( tabfrm, font=("Helvetica", fsz), textvariable=base_name)     .grid( columnspan=3, column=0, row=4, sticky='w')
  
              # entry area to allow the user to change the printed name of the axis 
              Tk.Label( tabfrm, text='%saxis Label:' % xy, font=("Helvetica", fsz) ) .grid( columnspan=5, column=0, row=5, sticky='w')
              Tk.Entry( tabfrm, width=40, textvariable=base_text )                   .grid( columnspan=3, column=0, row=6, sticky='w')
  
              # entry area to allow the user to change the scale of the axis
              Tk.Label( tabfrm, text='Scale', font=("Helvetica", fsz) )              .grid( column=0, row=7, sticky='w')
              Tk.Label( tabfrm, text='a=auto', font=("Helvetica", fsz) )             .grid( column=1, row=7, sticky='w')
              Tk.Label( tabfrm, text='Max',  font=("Helvetica", fsz) )               .grid( column=0, row=8, sticky='w')
              Tk.Entry( tabfrm, width=10, textvariable=base_scl_max )                .grid( column=1, row=8, sticky='w')
              Tk.Label( tabfrm, text='Min',  font=("Helvetica", fsz) )               .grid( column=0, row=9,sticky='w')
              Tk.Entry( tabfrm, width=10, textvariable=base_scl_min )                .grid( column=1, row=9,sticky='w')
  
              Tk.Label( tabfrm, text='Grid', font=("Helvetica", fsz) )               .grid( column=2, row=7, sticky='w')
              Tk.Label( tabfrm, text='a=auto', font=("Helvetica", fsz) )             .grid( column=3, row=7, sticky='w')
              Tk.Label( tabfrm, text='Step',  font=("Helvetica", fsz) )              .grid( column=2, row=8, sticky='w')
              Tk.Entry( tabfrm, width=5, textvariable=base_grd_step )                .grid( column=3, row=8, sticky='w')
  
              base_scl_auto.set( True )
              base_grd_step.set( '' )
  
              # set the x and y axes according to the initial xynames values
              # and select them in the listbox areas
  

              if xy == 'X' : self.xnames = names
              if xy == 'Y' : self.ynames = names
              #



  
          #----------------------------------------
          # Filter Tab
          #----------------------------------------


          tab=self.nb.filter
          tabfrm = Tix.Frame(tab, name='fltr')
          tabfrm.pack( side=Tix.TOP, padx=2)

          self.filter_tabfrm = tabfrm


          # Create a scrolled listbox to show all available filter names
          axis_sb = Tk.Scrollbar(tabfrm, orient=Tk.VERTICAL)
          names   = Tk.Listbox(tabfrm, name='filter_column_list', width=40, height=10, yscrollcommand=axis_sb.set, exportselection=0)
          axis_sb.config(command=names.yview)


          self.ffull     = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Full List',  font=("Helvetica", fsz) )   .grid( column=2, row=1, sticky='w')
          Tk.Checkbutton( tabfrm, variable=self.ffull, command=self.wupdate_column_lists) .grid( column=3, row=1, sticky='w')
          self.ffull.set( False )
  
          Tk.Label( tabfrm, text='Filter Data', font=("Helvetica", fsz) )  .grid( columnspan=3, column=0, row=1, sticky='w')
          names                                                            .grid( columnspan=3, column=0, row=2)
          axis_sb                                                          .grid(               column=3, row=2, sticky='wns')

          
          self.filter_column_list = names

          Tk.Label( tabfrm, font=("Helvetica", fsz), text='Current Filters          ')            .grid( column=0, row=4)
          Tix.Button(tabfrm, name='add_filter', text='Add',    width=4, command=self.waddfilter) .grid( column=1, row=4)
          Tix.Button(tabfrm, name='del_filter', text='Delete', width=4, command=self.wdelfilter) .grid( column=2, row=4)

          shl = Tix.ScrolledHList(tabfrm, name='fltr_list', options='hlist.columns 3 hlist.header 1' )
          shl.grid  (columnspan=4, column=0, row=5, sticky='w' )
          flist=shl.hlist
          flist.column_width(2,0)
          flist.config(separator='.', width=40, height=10, drawbranch=0, indent=10)
          flist.column_width(0, chars=20)
          flist.column_width(1, chars=25)

          flist.header_create(0, itemtype=Tix.TEXT, text='Name')
          flist.header_create(1, itemtype=Tix.TEXT, text='Values')

          self.flist = flist

          #self.wupdate_filter_cond_list( None )

          

          self.filter_name   =  Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, font=("Helvetica", fsz), textvariable=self.filter_name)     .grid( columnspan=3, column=0, row=6, sticky='w')

          shl = Tix.ScrolledHList(tabfrm, name='value_list', options='hlist.columns 4 hlist.header 1' )
          shl.grid  (columnspan=4, column=0, row=7, sticky='w' )
          vlist=shl.hlist
          vlist.column_width(3,0)
          vlist.config(separator='.', width=40, height=10, drawbranch=0, indent=10)
          vlist.column_width(0, chars=25)
          vlist.column_width(1, chars=10)
          vlist.column_width(2, chars=10)

          vlist.header_create(0, itemtype=Tix.TEXT, text='Value')
          vlist.header_create(1, itemtype=Tix.TEXT, text='Count')
          vlist.header_create(2, itemtype=Tix.TEXT, text='Selected')

          self.vlist = vlist
        


          # color selection

          self.color_series   =  Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text=' ', font=("Helvetica", fsz) )      .grid( columnspan=3, column=0, row=8, sticky='w')
          clr = Tix.ComboBox(tabfrm, label="Color:", dropdown=1, name='color', editable=1,
              variable=self.color_series,
              options='listbox.height 30  listbox.width 60 entry.width 30 label.width 6 label.anchor w entry.state normal')
          clr.grid( columnspan=4, column=0, row=9 )

 
          self.clr = clr
         


          # line style selection

          self.line_series   =  Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text=' ', font=("Helvetica", fsz) )      .grid( columnspan=3, column=0, row=10, sticky='w')
          linst = Tix.ComboBox(tabfrm, label="Line: ", dropdown=1, name='line', editable=1,
              variable=self.line_series,
              options='listbox.height 30  listbox.width 60 entry.width 30 label.width 6 label.anchor w entry.state normal')
          linst.grid( columnspan=4, column=0, row=11 )
          linst.config( background='red')


          self.linst = linst




          self.line_on     = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Line On:',  font=("Helvetica", fsz) ) .grid( column=0, row=12, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.line_on )               .grid( column=1, row=12, sticky='w')
          self.line_on.set( True )


          self.sort_data_on     = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Sort:',  font=("Helvetica", fsz) )  .grid( column=2, row=12, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.sort_data_on )        .grid( column=3, row=12, sticky='w')
          self.sort_data_on.set( True )




          #----------------------------------------
          # format Tab
          #----------------------------------------

          tab=self.nb.format
          tabfrm = Tix.Frame(tab, name='format')
          tabfrm.pack(side=Tix.TOP, padx=2)

          self.graph_title      = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Graph Title:', font=("Helvetica", fsz) ) .grid( columnspan=5, column=0, row=1, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.graph_title, validate='all', validatecommand=self.update_graph_title )     .grid( columnspan=3, column=0, row=2, sticky='w')
          self.graph_title.set('') 





          
          
          self.wplot_position      = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Graph Location', font=("Helvetica", fsz) )    .grid( columnspan=5, column=0, row=3, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.wplot_position )        .grid( columnspan=3, column=0, row=4, sticky='w')
          self.plot_position = self.update_entry_box( self.plot_position, self.wplot_position )

          self.wconditions_location      = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Conditions Location:', font=("Helvetica", fsz) )  .grid( columnspan=1, column=0, row=5, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.wconditions_location )      .grid( columnspan=3, column=0, row=6, sticky='w')
          self.conditions_location = self.update_entry_box( self.conditions_location, self.wconditions_location )

          self.draw_conditions    = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Draw Conditions',  font=("Helvetica", fsz) )  .grid( column=1, row=5, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.draw_conditions )                 .grid( column=2, row=5, sticky='w')
          self.draw_conditions.set( True )
          


          self.wlegend_location      = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Legend Location:', font=("Helvetica", fsz) )  .grid( columnspan=5, column=0, row=7, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.wlegend_location )      .grid( columnspan=3, column=0, row=8, sticky='w')
          self.legend_location     = self.update_entry_box( self.legend_location,     self.wlegend_location )

          self.small_legend    = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Smaller Legend',  font=("Helvetica", fsz) )  .grid( column=1, row=7, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.small_legend )                 .grid( column=2, row=7, sticky='w')
          self.small_legend.set( True )
          
          self.wcolor_list      = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Color Order: r g b c m y k orange violet brown', font=("Helvetica", fsz) )       .grid( columnspan=5, column=0, row=11, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.wcolor_list )                                              .grid( columnspan=3, column=0, row=12, sticky='w')
          self.update_entry_box( self.color_list, self.wcolor_list )

          self.wdash_list      = Tk.StringVar(master=tabfrm)

          self.wplot_linewidth      = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Line Width:', font=("Helvetica", fsz) )      .grid( columnspan=5, column=0, row=15, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.wplot_linewidth )      .grid( columnspan=3, column=0, row=16, sticky='w')
          self.update_entry_box( self.plot_linewidth, self.wplot_linewidth )

          self.wplot_marker      = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Line Marker:  . , o v ^ < > 1-7 s p x h H D d + | _ ', font=("Helvetica", fsz) )  .grid( columnspan=5, column=0, row=17, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.wplot_marker )                                              .grid( columnspan=3, column=0, row=18, sticky='w')
          self.update_entry_box( self.plot_marker, self.wplot_marker )

          self.wnumgrids      = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Default Number of Grid Lines:', font=("Helvetica", fsz) ) .grid( columnspan=5, column=0, row=19, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.wnumgrids )                         .grid( columnspan=3, column=0, row=20, sticky='w')
          self.update_entry_box( self.numgrids, self.wnumgrids )





          #----------------------------------------
          # Define keyboard shortcuts and other button click actions
          #----------------------------------------

#         self.root.bind("<Button>",        self.do_event_buttonpress,       '+' )
          self.root.bind("<ButtonRelease>", self.do_event_buttonrelease,      )
          self.root.bind("<Control-ButtonRelease>", self.do_event_ctlbuttonrelease,      )
          self.root.bind("<Double-Button>", self.do_event_doublebuttonpress,   )
          self.root.bind("<KeyPress>",             self.do_event_key_press     )
          self.root.bind("<KeyRelease>",           self.do_event_key_release   )
  




          #----------------------------------------
          # Select the Tab we want to come up at the start
          #----------------------------------------

          self.nb.raise_page('load')
          self.nb.update()


                                                                                 


          #----------------------------------------
          # Merge the Tk widgets with the matplotlib figure
          #----------------------------------------

          self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)

          self.graphwin = self.canvas.get_tk_widget()

          self.graphwin.pack(side=Tk.RIGHT, fill=Tk.BOTH, expand=1)
          
          toolbar = NavigationToolbar2TkAgg( self.canvas, self.root )
          toolbar.update()

          # Create a status bar 
          self.status   =  Tk.StringVar(master=tabfrm)
          Tk.Label( toolbar, text='     Status:',  font=("Helvetica", fsz) )   .pack(side='left')
          Tk.Entry( toolbar, width=60, textvariable=self.status )         .pack(side='left')
          self.canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
          
#         self.canvas.mpl_connect('key_press_event',      self.on_key_press)
#         self.canvas.mpl_connect('key_release_event',    self.on_key_release)
          self.canvas.mpl_connect('motion_notify_event',  self.on_motion)
          self.canvas.mpl_connect('pick_event',           self.on_pick)
          self.canvas.mpl_connect('button_release_event', self.on_button_release)
          self.canvas.mpl_connect('button_press_event',   self.on_button_press)
          self.gotLegend = 0



#############################################################################################################          
    def update_graph_title( self ):

        title( self.graph_title.get() )



#############################################################################################################          
    def win_load( self, logfile=None, csvfilename=None, num_records=0 ):


          # this updates the list of columns in the gui, and is listed on each of the axes, and on the fileter page
          # which also includes the color and line style selection boxes.

          # This should be run every time the list of columns changes


          #----------------------------------------
          # Insert the already loaded logfiles into the listbox
          #----------------------------------------

          if logfile     != None :   self.logfiles.insert( Tk.END, self.get_filename_from_fullpath( logfile ) + ' (%s)' % num_records   )
          if csvfilename != None :   self.logfiles.insert( Tk.END, self.get_filename_from_fullpath( csvfilename ) + ' (%s)' % num_records)


          #--------------------------------------------------
          # Update the Distortion Reference selection values
          #--------------------------------------------------

          winname_ref_lst = [ self.dist_process_w , \
                              self.dist_temp_w    , \
                              self.dist_hblb_w    , \
                              self.dist_seg_w     , \
                              self.dist_freq_w    , \
                              self.dist_vbat_w    , \
                              self.dist_pin_w     , \
                              self.dist_logfilename_w   ]

          var_ref_lst =     [ self.dist_process , \
                              self.dist_temp    , \
                              self.dist_hblb    , \
                              self.dist_seg     , \
                              self.dist_freq    , \
                              self.dist_vbat    , \
                              self.dist_pin     , \
                              self.dist_logfilename    ]

          colname_ref_lst = [ 'Process'         , \
                              'Temp(C)'         , \
                              'HB_LB'           , \
                              'Segments'        , \
                              'Freq(MHz)'  , \
                              'Vbat(Volt)'      , \
                              'Pwr In(dBm)'     , \
                              'logfilename'             ]

          self.values_dict_done = 0
          self.create_values_dict()


          vof = self.vam_offset_entry.get()

          if vof == '' :  
               self.vam_offset_entry.set( self.vam_offset )
          else:
               self.vam_offset = float(vof)

          for win, cname, var in zip( winname_ref_lst, colname_ref_lst, var_ref_lst):

              # first collect get the currently selected value
              try:
                s = var.get()
              except Exception:
                pass


              # get a list of available values for the currently loaded results
              self.add_values_dict( cname )
              
              vl = self.values_dict[ cname ]
              values = [None]
              values.extend( vl ) 

             
              # remove any values form the selection box
              #win.delete_all()
              win.subwidget_list[ 'slistbox' ].subwidget_list[ 'listbox' ].delete(0, Tix.END )

              # add the new set of values into the selection box
              for v in values:
                win.insert(Tk.END, str(v))

              # select the previously selected value
              #self.select_listbox_name( s,  win.subwidget_list[ 'slistbox' ].subwidget_list[ 'listbox' ] )
              if s == None or s == '':
                if len(values) > 0:
                  s = values[0]
                else:
                  s = ''

              var.set( s )

              
               
              

          








          #----------------------------------------
          # Create an alphabetically ordered list of column names, this is the list that the user will
          # choose for the X and Y axes
          #----------------------------------------

          cll = []
          for n in  self.data:
             if n != '' :
                cll.append(n)
          cll.sort()
    
          #----------------------------------------
          # Load the Xaxis and Yaxis Tab pages
          #----------------------------------------

          self.xaxis_col_list.delete(0, Tk.END)
          full_list = self.xfull.get()
          for c in cll:
            if full_list or (c in self.xaxis_reduced_list):
               self.xaxis_col_list.insert( Tix.END, c )

          self.yaxis_col_list.delete(0, Tk.END)
          full_list = self.yfull.get()
          for c in cll:
            if full_list or (c in self.yaxis_reduced_list):
                self.yaxis_col_list.insert( Tix.END, c )

          self.filter_column_list.delete(0, Tk.END)                
          full_list = self.ffull.get()
          for c in cll:
            if full_list:
                self.filter_column_list.insert( Tix.END, c )
            else:
                if (c in self.value_dict_names) :
                     self.filter_column_list.insert( Tix.END, c )







          #----------------------------------------
          # Update the column lists for the colr and line selection boxes
          # unfortunately we have to redraw these ComboBox's from scratch 
          # each time as I don't know how to clear their entries!
          #----------------------------------------

          tabfrm = self.filter_tabfrm


          # first do the color selection combobox
          clr = Tix.ComboBox(tabfrm, label="Color:", dropdown=1, name='color', editable=1,
              variable=self.color_series,
              options='listbox.height 30  listbox.width 60 entry.width 30 label.width 6 label.anchor w entry.state normal')
          clr.grid( columnspan=4, column=0, row=9 )

          # add the list of data columns into the listbox
          clr.insert( Tix.END, '' )
          for c in cll:
            clr.insert( Tix.END, c )

          self.clr = clr
         


          # then do the line selection combobox
          linst = Tix.ComboBox(tabfrm, label="Line: ", dropdown=1, name='line', editable=1,
              variable=self.line_series,
              options='listbox.height 30  listbox.width 60 entry.width 30 label.width 6 label.anchor w entry.state normal')
          linst.grid( columnspan=4, column=0, row=11 )
          linst.config( background='red')

          # add the list of data columns into the listbox
          linst.insert( Tix.END, '' )
          for c in cll:
            linst.insert( Tix.END, c )

          self.linst = linst







#         self.nb.raise_page('xaxis')
          self.nb.update()
#         self.nb.raise_page('yaxis')
#         self.nb.update()


#############################################################################################################          
    def win_select( self, xynames ):






          #----------------------------------------
          # Load the Xaxis and Yaxis Tab pages
          #----------------------------------------

          for xy in ('X', 'Y' ):


              # get the axes

              # if it is not set then set it from the supplied values


              # Define variables for the selected axes values.
  
              # A common name 'base_*' is used for both axes which is then 
              # assigned to the actual axis. This allows the code to be reused to 
              # define both axes.
              if xy == 'X' : 
                base_name     =  self.xname     
                base_text     =  self.xtext     
                base_names    =  self.xaxis_col_list
                xyname        =  xynames[0] 
                lim           =  self.xlimits
                base_scl_auto =  self.xscl_auto
                base_scl_max  =  self.xscl_max 
                base_scl_min  =  self.xscl_min 
                base_full     =  self.xfull
               
              if xy == 'Y' : 
                base_name     =  self.yname     
                base_text     =  self.ytext     
                base_names    =  self.yaxis_col_list
                xyname        =  xynames[1] 
                lim           =  self.ylimits
                base_scl_auto =  self.yscl_auto
                base_scl_max  =  self.yscl_max 
                base_scl_min  =  self.yscl_min 
                base_full     =  self.yfull
                
  
  
              n = base_names.get( Tk.ACTIVE )
              base_name.set( n )         
              base_text.set( n )
              


              # if there is no current axis selection , make it visible
              xysel_lst =  base_names.curselection()     
              if len(xysel_lst) == 0: 

                  if xy == 'X':
                         done = self.select_listbox_name( xyname, base_names )
                         # we didn't find the value in the reduce list , expand the list and look for it again!
                         if done == False:
                            base_full.set(True)
                            self.win_load()
                            done = self.select_listbox_name( xyname, base_names )


                  if xy == 'Y':
                      for xyname in xynames[1:] :
                         done = self.select_listbox_name( xyname, base_names )
                         # we didn't find the value in the reduce list , expand the list and look for it again!
                         if done == False:
                            base_full.set(True)
                            self.win_load()
                            done = self.select_listbox_name( xyname, base_names )


              # if the axis limit was set then update the window, and reset the 'script' limit
              #if base_scl_auto.get() == 0 and lim != []:
              if base_scl_auto.get() == False and lim != []:
                base_scl_auto.set( False )
                base_scl_max.set( lim[ 1 ] )
                base_scl_min.set( lim[ 0 ] )
#               lim = []
                
              if xy == 'X' : 
                self.xlimits  = lim
              if xy == 'Y' : 
                self.ylimits  = lim
              
              

          files = ', '.join( self.logfilenames + self.csvfilenames )
          z = self.root.winfo_toplevel()
          z.wm_title('PYGRAM Graphing Tool  version:  ' + self.pygram_version + '     ' + files )


          




#####################################################################################


    def select_listbox_name( self, name, listbox ):

                     done = False
                     for i in range( listbox.size() ):
                         if name ==  listbox.get( i ) :
                             listbox.activate( i )         
                             listbox.selection_set( i )         
                             listbox.see( i )
                             done = True

                     return done




#####################################################################################

    def list2str( self, lst ):

         txt = ''
         for i in lst:
            if i == None : continue
            txt = txt + ' ' + str(  self.truncate_value( self.get_filename_from_fullpath( i ) ) )

         return txt.strip()


###############################################################33


    def db_make_dict( self, topkey, key, value, cond='' ):
    

      root = self.db_seldb + '.' + topkey
      query_str = "select  %s.%s , %s.%s from %s %s" % (root,key,   root,value, root, cond )
    
      self.db_cursor.execute( query_str )
      rows = self.db_cursor.fetchall()

#     print  '(db_make_dict)' , query_str
      rows_new = []
      for r in rows:
        r0 = str( r[0] ).strip()
        r1 = str( r[1] ).strip()
        rows_new.append( [ r0, r1 ] )
        
#       print '%15s   %15s' % ( r0, r1 )

      k2n = dict( rows_new )

    
      return k2n




#####################################################################################

    def wloaddb( self ):



      ##########################################################
      #
      # Create a new window for entering the database results
      #
      ##########################################################

      self.dbwin = Tix.Toplevel( master=self.root, name = 'dbwin' )
      self.dbwin.title("Load test results from DataPower")
      
      dbfrm = Tix.Frame(self.dbwin, name='dbfrm')
      dbfrm.grid()





      ##########################################################
      #
      # Add a list box to select the available databases
      #
      ##########################################################

      dbnames = ['LAB', 'TEST', 'PRODUCTION', 'QUAL_CHAR']
      self.db_seldb = 'LAB'

      w =     Tk.Label(dbfrm, text="Select Database:") .grid( column=0, row=1)


      shl = Tix.ScrolledHList(dbfrm, name='topdb_list', options='hlist.columns 3 hlist.header 1' )
      shl.grid  (columnspan=2, column=0, row=2)
      topdblist=shl.hlist
      topdblist.column_width(2,0)
      topdblist.config(separator='.', width=21, height=5, drawbranch=0, indent=10)
      topdblist.column_width(0, chars=15)
      topdblist.column_width(1, chars=15)

      topdblist.header_create(0, itemtype=Tix.TEXT, text='Database')
      topdblist.header_create(1, itemtype=Tix.TEXT, text='# Records' )

      self.topdblist = topdblist

      for name in dbnames:
          e = name
          topdblist.add(e, itemtype=Tix.TEXT, text=name)
          topdblist.item_create(e, 1, itemtype=Tix.TEXT, text='?')

      self.topdblist.selection_set( self.db_seldb )


      ##########################################################
      #
      # Add a list box to select the available product families
      #
      ##########################################################

      w =     Tk.Label(dbfrm, text="Select Product Family:") .grid( column=3, row=1)


      shl = Tix.ScrolledHList(dbfrm, name='fam_list', options='hlist.columns 3 hlist.header 1' )
      shl.grid  (columnspan=4, column=3, row=2)
      famlist=shl.hlist
      famlist.column_width(2,0)
      famlist.config(separator='.', width=21, height=5, drawbranch=0, indent=10)
      famlist.column_width(0, chars=15)
      famlist.column_width(1, chars=15)

      famlist.header_create(0, itemtype=Tix.TEXT, text='Product Family')
      famlist.header_create(1, itemtype=Tix.TEXT, text='# Results' )

      self.famlist = famlist





      ##########################################################
      #
      # Add a list box to select the the script file aka PG_KEY
      #
      ##########################################################





      w =     Tk.Label(dbfrm, text="Select Test Type Script:") .grid( row=3, column=0 )

      #shl = Tix.tixTList(dbfrm, name='script_list', options='hlist.columns 5 hlist.header 1 ' )
      #shl = Tix.TList(dbfrm, name='script_list' )
      shl = Tix.ScrolledHList(dbfrm, name='script_list', options='hlist.columns 6 hlist.header 1 ' )
      shl.grid  (columnspan=4, column=0, row=4 )
      scriptlist=shl.hlist
      scriptlist.column_width(2,0)
      scriptlist.config(separator='.', width=150, height=20, drawbranch=0, indent=10,   selectmode=Tk.EXTENDED )
#          names   = Tk.Listbox(tabfrm, name='lb', width=40, height=40, yscrollcommand=axis_sb.set, exportselection=0, selectmode=Tk.EXTENDED)

      scriptlist.column_width(0, chars=55)
      scriptlist.column_width(1, chars=8)
      scriptlist.column_width(2, chars=30)
      scriptlist.column_width(3, chars=30)
      scriptlist.column_width(4, chars=10)
      scriptlist.column_width(5, chars=35)

      scriptlist.header_create(0, itemtype=Tix.TEXT, text='Scriptfile')
      scriptlist.header_create(1, itemtype=Tix.TEXT, text='# Logs')
      scriptlist.header_create(2, itemtype=Tix.TEXT, text='Logfiles')
      scriptlist.header_create(3, itemtype=Tix.TEXT, text='Serial Numbers')
      scriptlist.header_create(4, itemtype=Tix.TEXT, text='# Tests')
      scriptlist.header_create(5, itemtype=Tix.TEXT, text='Test Date')

      self.scriptlist = scriptlist



      #####################################################################
      #
      # Add a list box to select between the different test results LG_KEY
      #
      #####################################################################





      w =     Tk.Label(dbfrm, text="Select Test Results:") .grid( row=5, column=0 )

      #shl = Tix.tixTList(dbfrm, name='res_list', options='hlist.columns 5 hlist.header 1 ' )
      #shl = Tix.TList(dbfrm, name='res_list' )
      shl = Tix.ScrolledHList(dbfrm, name='res_list', options='hlist.columns 6 hlist.header 1 ' )
      shl.grid  (columnspan=4, column=0, row=6 )
      reslist=shl.hlist
      reslist.column_width(2,0)
      reslist.config(separator='.', width=150, height=20, drawbranch=0, indent=10,   selectmode=Tk.EXTENDED )
#          names   = Tk.Listbox(tabfrm, name='lb', width=40, height=40, yscrollcommand=axis_sb.set, exportselection=0, selectmode=Tk.EXTENDED)

      reslist.column_width(0, chars=55)
      reslist.column_width(1, chars=30)
      reslist.column_width(2, chars=10)
      reslist.column_width(3, chars=35)
      reslist.column_width(4, chars=5)
      reslist.column_width(5, chars=5)

      reslist.header_create(0, itemtype=Tix.TEXT, text='Logfile')
      reslist.header_create(1, itemtype=Tix.TEXT, text='Serial Number')
      reslist.header_create(2, itemtype=Tix.TEXT, text='# Tests')
      reslist.header_create(3, itemtype=Tix.TEXT, text='Test Date')
      reslist.header_create(4, itemtype=Tix.TEXT, text='PG_KEY')
      reslist.header_create(5, itemtype=Tix.TEXT, text='LG_KEY')

      self.reslist = reslist






      self.wupdate_dbwin_fam_list()



      Tk.Button(dbfrm, text="Load\nResults",  command=self.load_all_db_res) .grid(row=7, column=0)
      Tk.Button(dbfrm, text="Reset\nResults", command=self.wclearfiles    ) .grid(row=7, column=1)
      Tk.Button(dbfrm, text="Cancel",         command=self.dbwin.destroy  ) .grid(row=7, column=2)




      self.dbwin.bind("<ButtonRelease>", self.do_dbwin_event_buttonrelease,      )
      #self.dbwin.bind("<Control-ButtonRelease>", self.do_event_ctlbuttonrelease,      )
      self.dbwin.bind("<Double-Button>", self.do_dbwin_event_doublebuttonpress,  )
      #self.dbwin.bind("<Key>",           self.do_event_key,                )




#####################################################################################
    def connect_to_datapower_db(self):

      import cx_Oracle

      db =  cx_Oracle.connect('mydpuser','hard2guess','ssvrr02/dpower')
      cursor = db.cursor()
      return cursor

#####################################################################################


    def db_get_key_data( self, topkey, key, cond='' ):

      root = self.db_seldb + '.' + topkey
      query_str = "select  %s.%s from %s %s" % (root, key, root, cond )
#     print '(db_get_key_data)', query_str
      self.db_cursor.execute( query_str )
      rows = self.db_cursor.fetchall()

#     print '(db_get_key_data)' , topkey, key, cond, ' ->', rows
      return rows

#####################################################################################



    def wupdate_dbwin_fam_list( self ):    
      

      n = self.topdblist.info_selection()
      if len(n) > 0 : 
          self.db_seldb = n[0]
      else:  return

      if self.db_seldb == None or self.db_seldb == self.db_seldb_old  : return

      self.db_seldb_old = self.db_seldb



      ###############################################
      #
      # Connect to the Datapower Oracle database
      #
      ###############################################

      cursor = self.connect_to_datapower_db()
      self.db_cursor = cursor


      ###############################################
      #
      # First get all the product families and create a 
      # lookup table dictionary
      #
      ###############################################
      
      # The db_make_dict will run an SQL query on the db
      # returning all the records and makes a dictionary
      # between the two fields
      
      family_k2n     =  self.db_make_dict(  'FAMILY',  'FM_KEY',  'FM_NAME'  )


      ###############################################
      #
      # Write a list of the product families into the window
      #
      ###############################################

      self.db_selfam = self.db_selfam_old = None
      self.famlist.delete_all()                
      self.scriptlist.delete_all()                


      for key, name in family_k2n.iteritems() :

          # Run another SQL query to count the number of 
          # records that present for each product familiy
          query_str = 'select count( %s.PROG2FAM.FM_KEY ) from %s.PROG2FAM where FM_KEY = %s' % ( self.db_seldb, self.db_seldb, key )
          cursor.execute( query_str )
          count =  cursor.fetchall()


          ###############################################
          #
          # Add the families to the listbox
          #
          ###############################################
          
          e = name
          self.famlist.add(e, itemtype=Tix.TEXT, text=name)
          self.famlist.item_create(e, 1, itemtype=Tix.TEXT, text=count[0][0])


      self.db_cursor.close()

      self.wupdate_dbwin_script_list()



#####################################################################################

    def db_make_logfile_dict( self ):

      if self.done_db_logfile_dict == False:

          cursor = self.connect_to_datapower_db()
          self.db_cursor = cursor

          lot_id2k            =  self.db_make_dict(    'LOT',       'LOT_ID',  'LOT_KEY' )
          lot_k2id            =  self.db_make_dict(    'LOT',       'LOT_KEY', 'LOT_ID' )
          oplog_src2pgk       =  self.db_make_dict(    'OP_LOG',    'SRC_LOT', 'PG_KEY'  )
          oplog_src2lgk       =  self.db_make_dict(    'OP_LOG',    'SRC_LOT', 'LG_KEY'  )
          oplog_lgk2src       =  self.db_make_dict(    'OP_LOG',    'LG_KEY',  'SRC_LOT' )
          oplog_lgk2snk       =  self.db_make_dict(    'OP_LOG',    'LG_KEY',  'LOT_KEY' )
#         pprint( lot_k2id         )
#         pprint( lot_id2k         )
#         pprint( oplog_src2pgk  )
#         pprint( oplog_src2lgk  )
#         pprint( oplog_lgk2src  )
#         pprint( oplog_lgk2snk )

          self.db_logfile2pgk = {}
          self.db_logfile2lgk = {}
          self.db_lgk2logfile = {}
          self.db_lgk2sn      = {}


          # Create the Logfile name (SRC_LOT)  to PG_KEY dict
          # if the key is in the logfile dict oplog_src2pgk, then the k is a logfile key
          # and then use it to look up the PG_KEY
          for src, pgk in oplog_src2pgk.iteritems():
             if src in lot_k2id:
                 logfile = lot_k2id[ src ]
                 self.db_logfile2pgk[ logfile ] =  str( pgk )


             # Create the logfile to lgk (Logfile  to LG_KEY) dict
             # Create the lgk to logfile (LG_KEY  to Logfile) dict
          for lgk, src in oplog_lgk2src.iteritems():
             if src in lot_k2id:
                 logfile = lot_k2id[ src ]
                 self.db_logfile2lgk[ logfile ] =  str( lgk )
                 self.db_lgk2logfile[ str( lgk ) ]      =  logfile

          for lgk, snk in oplog_lgk2snk.iteritems():
             if snk in lot_k2id:
                 sn = lot_k2id[ snk ]
                 logfile = self.db_lgk2logfile[ lgk ]
                 self.db_lgk2sn [ str(lgk) ] =  str( sn )


          self.done_db_logfile_dict = True

          self.db_cursor.close()


       


      
#####################################################################################

    def add_db_logfile( self, logfile ):



      self.db_make_logfile_dict()

      logfile = re.sub( r'.*/', '', logfile )
      

      found_logfile = False
      for lgk , logf in self.db_lgk2logfile.iteritems():
#        if logfile.strip() == logf and str(lgk) == '304': 
         if logfile.strip() == logf : 
             self.add_db_res( lgk )
             found_logfile = True


      if not found_logfile:
         print "*** ERROR *** (add_db_logfile) , cannot find logfile '%s' in the database" % logfile


      files = ', '.join( self.logfilenames + self.csvfilenames )
      z = self.root.winfo_toplevel()
      z.wm_title('PYGRAM Graphing Tool  version:  ' + self.pygram_version + '     ' + files )



#####################################################################################










    def wupdate_dbwin_script_list( self ):



      n = self.famlist.info_selection()
      if len(n) > 0 : 
          self.db_selfam = n[0]
      else:  return

      if self.db_selfam == None or self.db_selfam == self.db_selfam_old  : return

      self.db_selfam_old = self.db_selfam



      ###############################################
      #
      # Connect to the Datapower Oracle database
      #
      ###############################################

      cursor = self.connect_to_datapower_db()
      self.db_cursor = cursor



      ###############################################
      #
      # First create lookup table dictionaries
      #
      ###############################################


      family_n2k      =  self.db_make_dict(  'FAMILY',  'FM_NAME', 'FM_KEY'   ) 
                                             
      scriptfam_k2fk  =  self.db_make_dict(  'PROG2FAM','PG_KEY',  'FM_KEY'   )
#     logfile_sn_k2n  =  self.db_make_dict(  'LOT',     'LOT_KEY', 'LOT_ID'   )   # LOT_KEY now gives Serial Number and Logfile
      oplog_k2et      =  self.db_make_dict(  'OP_LOG',  'PG_KEY',  'END_TIME' )
#     oplog_k2snk     =  self.db_make_dict(  'OP_LOG',  'PG_KEY',  'LOT_KEY'  )   # In the OP_LOG the LOT_KEY is the Serial num 
#     oplog_k2lk      =  self.db_make_dict(  'OP_LOG',  'PG_KEY',  'SRC_LOT'  )
      scriptfile_k2n  =  self.db_make_dict(  'PROGRAM', 'PG_KEY',  'PPID'     )









      ###############################################
      #
      # The Datapower Schema for the test results is:
      #
      #
      # TEST.FAMILY   -> FM_KEY  FM_NAME                (FAMILY = Riserva Classico etc)
      #                     |
      #                     V
      # TEST.PROG2FAM -> FM_KEY  PG_KEY                 (PROGRAM = Scriptfile)
      #                            |
      #                            V
      # TEST.PROGRAM  ->         PG_KEY  PPID                          ... 
      # TEST.PROG2LOT ->         PG_KEY  LOT_KEY
      # TEST.OP_LOG   ->         PG_KEY  LOT_KEY  SRC_LOT LG_KEY   START_TIME END_TIME  ...  (SRC_LOT = Logfile)
      #                                     |
      #                                     V
      # TEST.LOT                         LOT_KEY  LOT_ID ...   (LOT_ID = Serial Number name)
      # 
      # 
      # TEST.DEF{PG_KEY}         TEST_INDEX  COND0  ...        (TEST_INDEX columnnum  COND0(43) columnname) 
      # TEST.RES{PG_KEY}         LG_KEY I0 I1 I2 ... I19 T0 T1 T2 ...  ( LG_KEY is the 
      #
      ###############################################



      #####################################################################
      #
      # Fill the script_list listbox with all the results files for this family
      #
      #####################################################################


      self.reslist.delete_all()                
      self.scriptlist.delete_all()                


      ec = 0
      for  scriptkey, sf  in scriptfile_k2n.iteritems():
         if scriptfam_k2fk[ scriptkey ] == family_n2k[ self.db_selfam ] :
      
           et = oplog_k2et       [ scriptkey ]
      
           #print '****************************************\n'
           # count and list the logfiles 
           rows = self.db_get_key_data( 'OP_LOG', 'LG_KEY', 'where PG_KEY = %s' % scriptkey )
           lgc = len( rows )

           # get count and list of different logfiles
           lftxt = ''
           sntxt = ''
           sn_n = ''
           lf_n = ''
           for r in rows:
              # get the logfile key
              lg_k = r[0]      
              lf_k = self.db_lookup(  'OP_LOG', 'SRC_LOT', 'where LG_KEY = %s' % lg_k)
              if lf_k != None:
                  lf_n = self.db_lookup(  'LOT',    'LOT_ID',  'where LOT_KEY = %s' % lf_k)
                  # get the serial number key
              sn_k = self.db_lookup(  'OP_LOG', 'LOT_KEY', 'where LG_KEY = %s' % lg_k)
              if sn_k != None:
                  sn_n = self.db_lookup(  'LOT',    'LOT_ID',  'where LOT_KEY = %s' % sn_k)

              if len(lftxt) == 0: 
                  lftxt = ' ' + lf_n
                  sntxt = ' ' + sn_n
              else:               
                  lftxt = lftxt + ',' + lf_n
                  sntxt = sntxt + ',' + sn_n

              

           # count the number of tests that were done on all logfiles run wit this scriptfile
           query_str = 'select count( %s.RES%s.LG_KEY ) from %s.RES%s'  % ( self.db_seldb, scriptkey, self.db_seldb, scriptkey )
           cursor.execute( query_str )
           count =  cursor.fetchall()
           test_count = ' ' + str( count[0][0] )

      
           e = 'E' + str(scriptkey)

           self.scriptlist.add(e, itemtype=Tix.TEXT, text=sf)
           self.scriptlist.item_create(e, 1, itemtype=Tix.TEXT, text=lgc)
           self.scriptlist.item_create(e, 2, itemtype=Tix.TEXT, text=lftxt)
           self.scriptlist.item_create(e, 3, itemtype=Tix.TEXT, text=sntxt)
           self.scriptlist.item_create(e, 4, itemtype=Tix.TEXT, text=test_count)
           self.scriptlist.item_create(e, 5, itemtype=Tix.TEXT, text=et)
           
           ec += 1

      self.db_cursor.close()


#####################################################################################

    def wupdate_dbwin_res_list( self ):

      sellist = self.scriptlist.info_selection()
      if len(sellist) > 0 : 
          self.db_selscript = sellist[0]
      else:  return

      if self.db_selscript == None : return




      ###############################################
      #
      # Connect to the Datapower Oracle database
      #
      ###############################################

      cursor = self.connect_to_datapower_db()
      self.db_cursor = cursor




      ###############################################
      #
      # The Datapower Schema for the test results is:
      #
      #
      # TEST.FAMILY   -> FM_KEY  FM_NAME                (FAMILY = Riserva Classico etc)
      #                     |
      #                     V
      # TEST.PROG2FAM -> FM_KEY  PG_KEY                 (PROGRAM = Scriptfile)
      #                            |
      #                            V
      # TEST.PROGRAM  ->         PG_KEY  PPID                          ... 
      # TEST.PROG2LOT ->         PG_KEY  LOT_KEY
      # TEST.OP_LOG   ->         PG_KEY  LOT_KEY  SRC_LOT LG_KEY   START_TIME END_TIME  ...  (SRC_LOT = Logfile)
      #                                     |
      #                                     V
      # TEST.LOT                         LOT_KEY  LOT_ID ...   (LOT_ID = Serial Number name)
      # 
      # 
      # TEST.DEF{PG_KEY}         TEST_INDEX  COND0  ...        (TEST_INDEX columnnum  COND0(43) columnname) 
      # TEST.RES{PG_KEY}         LG_KEY I0 I1 I2 ... I19 T0 T1 T2 ...  ( LG_KEY is the 
      #
      ###############################################



      #####################################################################
      #
      # Fill the res_list listbox with details of the reesults
      #
      #####################################################################

      self.reslist.delete_all()                


      oplog_k2et      =  self.db_make_dict(  'OP_LOG',  'LG_KEY',  'END_TIME' )

      
      # go round each of the scriptfiles selected
      for pg in sellist:
#        print pg
         pg_k = pg[1:]
         


         rows = self.db_get_key_data( 'OP_LOG', 'LG_KEY', 'where PG_KEY = %s' % pg_k )
#        print rows 


         for r in rows:
            	
              lg_k = r[0]      
              lf_k = self.db_lookup(  'OP_LOG', 'SRC_LOT', 'where LG_KEY = %s' % lg_k)
              if lf_k != None:
                  lf_n = self.db_lookup(  'LOT',    'LOT_ID',  'where LOT_KEY = %s' % lf_k)
                  # get the serial number key
              sn_k = self.db_lookup(  'OP_LOG', 'LOT_KEY', 'where LG_KEY = %s' % lg_k)
              if sn_k != None:
                  sn_n = self.db_lookup(  'LOT',    'LOT_ID',  'where LOT_KEY = %s' % sn_k)


              # count the number of tests that were done on all logfiles run wit this scriptfile
              query_str = 'select count( %s.RES%s.LG_KEY ) from %s.RES%s where LG_KEY = %s'  % ( self.db_seldb, pg_k, self.db_seldb, pg_k, lg_k )
              cursor.execute( query_str )
              count =  cursor.fetchall()
              test_count = ' ' + str( count[0][0] )

              et = oplog_k2et       [ str( lg_k ) ]


              e = 'E' + str(lg_k)

              self.reslist.add(e, itemtype=Tix.TEXT, text=lf_n)
              self.reslist.item_create(e, 1, itemtype=Tix.TEXT, text=sn_n)
              self.reslist.item_create(e, 2, itemtype=Tix.TEXT, text=test_count)
              self.reslist.item_create(e, 3, itemtype=Tix.TEXT, text=et)
              self.reslist.item_create(e, 4, itemtype=Tix.TEXT, text=str(pg_k))
              self.reslist.item_create(e, 5, itemtype=Tix.TEXT, text=e)

              self.reslist.selection_set( e )



         # leave all the results selected by default

      self.db_cursor.close()


#####################################################################################
    def db_lookup( self, topkey, key, cond=None ):

         query_str = 'select %s.%s.%s from %s.%s %s'  % ( self.db_seldb, topkey, key,     self.db_seldb,topkey,  cond )
#        print '(db_lookup)',  query_str,
         self.db_cursor.execute( query_str )
         rows = self.db_cursor.fetchall()
#        print rows
         
         retval = rows[0][0]
         if  rows[0][0] != None : retval = str(  rows[0][0] ).strip()

         return retval





#####################################################################################
    def read_pygram_config( self, param ):


         try: 
            fip = open( self.config_file )
            
            print "...reading pygram configuration file '%s'" % self.config_file

            for line in fip:
                x = re.search( r'^\s*(\S+)\s+(.+)', line )
                x = x.groups()
                if len(x) == 2:
                   key = x[0].strip()
                   val = x[1].strip()
                   self.config[ key ] = val

            fip.close()


                
         except Exception:      
            print "*** warning *** unable to read pygram configuration file '%s'" % self.config_file
            pass
       
         if param in self.config:
            return self.config[ param ]
         else:
            return ''


#####################################################################################
    def save_pygram_config( self, param, value ):
          
         self.config[ param ] = value

         fop = open( self.config_file, 'w' )
         
         for key, val in self.config.iteritems():
 
             print >> fop, '%10s %20s' % ( key, val )
             
         
         fop.close()
         


#####################################################################################
    def add_all_logfiles_dialog(self):
       ''' Adds all the log files specified on the command line, or if none given
         it will ask for a log file or a directory containing logfiles'''
    

       if len(sys.argv[1:]) > 0 :
          filenames = sys.argv[1:]
       else:


           last_used_directory = self.read_pygram_config( 'loaddir' )

           filenames = askopenfilename( defaultextension='.log',
                                   initialdir=last_used_directory,
                                   multiple=True,
                                   title='Select Directory Containing Log files',
                                   filetypes=[('logfile', '*.log'), ('csvfile', '*.csv'), ('text', '*.txt'), ('s2p', '*.s2p'), ('all', '*.*')] )


           if filenames == () or filenames[0] == '' :
              print "*** ERROR *** No Log files were specified"
              return

           dirname = os.path.dirname(  os.path.abspath(filenames[0]) )
           self.save_pygram_config( 'loaddir', dirname )

       for p in filenames:
           self.add_logfile(  p  )


#####################################################################################
    def get_savefile_directory_dialog(self):
       '''get the name of the directory where the plot files will be saved'''


       last_used_directory = self.read_pygram_config( 'savedir' )
                        

       dirname = askdirectory( title='Select Directory to Save Plot Files',
                                    initialdir=last_used_directory , )

       if not os.path.isdir( dirname ) :
          print "(get_savefile_directory) save directory '%s' does not exist, therefore it will be created"  % dirname
          os.makedirs( dirname )

       if dirname == '' or dirname == () or not os.path.isdir( dirname ) : 
          print "*** ERROR ***  No valid Save Directory was specified" 
          return
       
       self.save_pygram_config( 'savedir',  os.path.abspath(dirname)  ) 

       self.savedir  = dirname
       

#####################################################################################
    def wloadfile( self ):


         last_used_directory = self.read_pygram_config( 'loaddir' )


         filenames = askopenfilename( defaultextension='.log', 
                                     initialdir=last_used_directory,
                                     title='Select Log Files to Load', 
                                     multiple=True,
                                     filetypes=[('logfile', '*.log'), ('csvfile', '*.csv'), ('text', '*.txt'), ('s2p', '*.s2p'), ('all', '*.*')] )

#### >>>> #### temporary fix to work with python 2.6.2 #### askopenfilename doesn't return a list
#        filenames = [ filenames ]

         
         if filenames == () or filenames[0] == '': return

        


         self.save_pygram_config( 'loaddir', os.path.dirname(  os.path.abspath(filenames[0]) ) )
    

         for f in filenames:
             self.add_logfile( f )

         self.print_column_list()                    # prints out all the available column names (useful when defining the conditions)
         self.print_values_list()
         self.done_list_columns = True

         self.gen_values_dict()

         print '  ...waiting for user input'
         self.status.set( 'waiting for user input' )
         self.root.update()
        

         # load the file

#####################################################################################
    def gen_values_dict(self):

         pass

         cll = []
         for n in  self.data:
            if n != '' :
               cll.append(n)
         cll.sort()
    
         for c in cll:
               self.add_values_dict( c )



#####################################################################################

    def find_clicked_object( self, event , click_type ):

        '''Try to determine where the cursor is in relation to everything
           on the window'''

#       print '(find_clicked_object)', event.widget , click_type
        
        if event.x < 0 or re.search('ctlfrm' , str(event.widget) ):
            #print '(find_clicked_object) click on control window'
            ctl_item = str( event.widget )
            return '', ctl_item

        else: 
            #print '(find_clicked_object) click on graph at x=%s y=%s'% (float(event.x)/float(event.widget['width']), float(event.y)/float(event.widget['height']))
            try: 
              w = float(str(event.widget['width']))
            except Exception:
              w = 0

            try:
              h = float(str(event.widget['height']))
            except Exception:
              h = 0

            # sometimes at startup the size of the windows hasn't been defined, therefore force a dummy legal value
            if w == 0 or h == 0 :
                w = 500
                h = 500
               

            x = float(event.x)/w
            y = float(event.y)/h

            graph_item = 'yaxis' 
            if y < 0.1  : graph_item = 'format'
            if x < 0.07 : graph_item = 'yaxis'
            if y > 0.9  : graph_item = 'xaxis'
            if x > 0.75 and y < 0.5 : graph_item = 'filter'
            if x > 0.75 and y > 0.5 : graph_item = 'filter'

#           print '(find_clicked_object) pointed at ' , graph_item
#           self.nb.raise_page( graph_item )

            return graph_item, ''


        return ''


#####################################################################################

    def do_event_key_press              ( self,  event ):
#       print '(on_event_key_press)', event.__dict__
        self.keysym = event.keysym
        self.key    = self.simplify_keysym( event.keysym )
        self.do_event             (        event, 'key' )

    def do_event_key_release              ( self,  event ):
#       print '(on_event_key_release)', event.__dict__
        self.keysym = event.keysym
        self.key    = None


    def do_event_buttonpress      ( self,  event ):
        self.do_event             (        event, 'buttonpress' )

    def do_event_doublebuttonpress( self,  event ):
        self.do_event             (        event, 'doublebuttonpress' )

    def do_event_buttonrelease    ( self,  event ):
        self.do_event             (        event, 'buttonrelease' )

    def do_event_ctlbuttonrelease ( self,  event ):
        self.do_event             (        event, 'ctlbuttonrelease' )


    def do_dbwin_event_ctlbuttonrelease ( self,  event ):
        self.do_dbwin_event             (        event, 'ctlbuttonrelease' )

    def do_dbwin_event_buttonrelease    ( self,  event ):
        self.do_dbwin_event             (        event, 'buttonrelease' )

    def do_dbwin_event_doublebuttonpress( self,  event ):
        self.do_dbwin_event             (        event, 'doublebuttonpress' )

#####################################################################################
    def do_dbwin_event( self, event, click_type ):
#      print '(do_dbwin_event)', event.widget, click_type

       if re.search('dbfrm.topdb_list.f1.hlist$', str(event.widget)) : 
           self.wupdate_dbwin_fam_list()

       if re.search('dbfrm.fam_list.f1.hlist$', str(event.widget)) : 
           self.wupdate_dbwin_script_list()

       if re.search('dbfrm.script_list.f1.hlist$', str(event.widget)) : 
           self.wupdate_dbwin_res_list()

       if re.search('dbfrm.res_list.f1.hlist$', str(event.widget)) : 
           if click_type == 'doublebuttonpress' : self.db_doublebuttonpress = True
           if click_type == 'buttonrelease' :
              if self.db_doublebuttonpress == True:
                 self.load_all_db_res()
              self.db_doublebuttonpress = False

#####################################################################################

    def load_all_db_res(self):

        # look at the list of selected results and load all of them them one by one

        n = self.reslist.info_selection()
        
        if len(n) > 0 : 
            for r in n:
                self.add_db_res( r[1:] )

        self.print_column_list()                    # prints out all the available column names (useful when defining the conditions)
        self.print_values_list()
        self.done_list_columns = True

        self.gen_values_dict()
        print '  ...waiting for user input'
        self.status.set( 'waiting for user input' )
        self.root.update()
               

#####################################################################################


    


    def do_event( self, event, click_type ):


#      print '(do_event)', event.widget, click_type

       self.keysym = event.keysym
       self.keysym_dict = event.__dict__

       page = str(  self.nb.raised() )

       #print '(do_event): click_type=%10s tab=%s  widget=(%30s) but=%s key=%4s xy=(%4s,%4s) xy_root=(%4s,%4s)'% ( 
       #           click_type, page, str(event.widget), event.num,  event.keysym , 
       #           event.x ,event.y, event.x_root, event.y_root)



       # determine what we just clicked 
       graph_action, ctl_action = self.find_clicked_object( event , click_type )
     

       if ctl_action: 

           if  click_type == 'doublebuttonpress' and re.search('axis', page) and event.num == 1 :
               self.plot_interactive_graph()

           if re.search('axis', page):

               if re.search('xaxis', page):
                  base_names =  self.xnames
                  base_name  =  self.xname
                  base_text  =  self.xtext
        
               if re.search('yaxis', page):
                  base_names =  self.ynames
                  base_name  =  self.yname
                  base_text  =  self.ytext



               if click_type == 'buttonrelease' or click_type == 'key':

                   inc = 0
                   if str(event.keysym) == 'Up'  : inc = -1
                   if str(event.keysym) == 'Down': inc = +1
        
                   if inc != 0 :
                       # get the first selected value in the list
                       i = int( base_names.curselection()[0] )

                       # clear the selection (unselect it)
                       base_names.selection_clear( 0, Tk.END )         

                       # move the index to the next value in the list
                       i = i + inc

                       # dont move the selection outside the list limits
                       if (i < 0 ) : i = 0
                       if (i >= base_names.size() ) : i = base_names.size()-1


                       # select the indexed value
                       base_names.activate( i )         
                       base_names.selection_set( i )         
                       
                       # make sure it updates in the widget.
                       base_names.see( i )



                   n = base_names.get( Tk.ACTIVE )
                   base_name.set( n )         
                   base_text.set( n )
      
                   if re.search('xaxis', page): self.xynames[0] = n
                   if re.search('yaxis', page): 

                       # go through all the selected items and add them to the xynames
                       xysel_lst =  base_names.curselection()     
                       self.xynames = [ self.xynames[0] ]
                       for i in xysel_lst:
                          n = base_names.get( int(i) )
                          self.xynames.append( n )
                       self.graph_title.set('') 



               if re.search('yaxis', page) and click_type == 'ctlbuttonrelease':

                  # go through all the selected items and add them to the xynames
                  xysel_lst =  base_names.curselection()     
                  self.xynames = [ self.xynames[0] ]
                  for i in xysel_lst:
                     n = base_names.get( int(i) )
                     self.xynames.append( n )
                  self.graph_title.set('') 







                 
           if re.search('filter', page) and click_type == 'buttonrelease':

             # for some reason I  cannot get the element name to work if it contains number characters
             # therefore I am mapping the value index into a letter

             # if we click in the flist area, fill out the vlist window with a list of the values and the selected status
             if re.search( 'fltr_list' , ctl_action ):
                n = self.flist.info_selection()
                name = n[0]
                self.filter_name.set( name )
                self.add_values_dict( name )
#               print 'filter clicked = ', name, self.values_dict[name], n

                self.wupdate_filter_value_list( name ) 

                self.filter_column_list.selection_clear(0, Tk.END)
                self.select_listbox_name( name, self.filter_column_list )


             if re.search( 'value_list' , ctl_action ):
                n = self.flist.info_selection()
                name = n[0]
               
                self.add_values_dict( name )
                values = self.values_dict[ name ]

                n = self.vlist.info_selection()
                val_letter = n[0]
                #print 'value clicked    = ', val_letter
                seq= 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
                #print 'value index      = ', seq.index( val_letter ) , 
                #print 'value translated = ', values[ seq.index( val_letter ) ]
                selected_v = values[ seq.index( val_letter ) ]
    
                # toggle the select value
                
                # first get the current filter values  

                for c in self.filter_conditions:
                   n = c[0]
                   if n == name:
                      filter_values = ( c[2:] )

                # make up a new filter_values list with the value changed
                new_c = [] 
                got_it = False
                for fv in filter_values:
                    if fv != selected_v:   # if the existing filter_value its not the selected v
                          new_c.append( fv )  
                    else:
                       got_it = True      
                if got_it == False : 
                          new_c.append( selected_v )  


                self.update_filter_conditions( name, new_c )

                # update the flist and vlist with the changed filter conditions
                self.wupdate_filter_cond_list( name ) 
                self.wupdate_filter_value_list( name ) 


           # double clicking the filter adds or removes it from the filter list
           if re.search('filter', page) and click_type == 'doublebuttonpress' and re.search( 'filter_column_list' , ctl_action ):

                self.create_values_dict()

                name = self.filter_column_list.get( Tk.ACTIVE )
#               print '(do_event) filter double' , name
                
                # add or remove the filter
                exists_already = 0
                for c in self.filter_conditions:
                   n = c[0]
                   if n == name:
                      exists_already = 1

                if exists_already :  self.wdelfilter( )
                else              :  self.waddfilter( )
                
  

#####################################################################################
    def wallon( self ):

        pass


#####################################################################################
    def walloff( self ):
      
       pass

#####################################################################################

    def waddfilter( self ):

                name = self.filter_column_list.get( Tk.ACTIVE )
                
                # determine if this is already an existing filter name. If it is then ignore the request
                exists_already = 0
                for c in self.filter_conditions:
                   n = c[0]
                   if n == name:
                      exists_already = 1

                if not exists_already:
                  self.filter_conditions.append( ( name, '=' ) )
                  self.wupdate_filter_cond_list( name ) 
                  self.add_values_dict( name )
                  self.wupdate_filter_value_list( name ) 
                  if name not in self.value_dict_names:
                     self.value_dict_names.append( n )

#####################################################################################


    def wdelfilter( self ):

                name = self.filter_column_list.get( Tk.ACTIVE )

                if name == '':
                  n = self.flist.info_selection()
                  name = n[0]
#                 print '(wdelfilter) 1', name
                  self.wupdate_filter_cond_list(name) 

                self.update_filter_conditions( name, None )
                self.wupdate_filter_cond_list( None ) 
                self.vlist.delete_all()                

#####################################################################################

    def wupdate_column_lists( self ):

          #print '(wupdate_column_lists)'
          self.win_load( )


#####################################################################################


    def wmorefilter( self ):
          self.filter_column_list.delete(0,Tk.END)                
          cll = []
          for col in self.data:
            if col != '':
               cll.append(col)
          cll.sort()
          for c in cll:
             self.filter_column_list.insert( Tix.END, c )
#####################################################################################

    def wlessfilter( self ):
          self.filter_column_list.delete(0,Tk.END)                
          for c in self.value_dict_names:
             self.filter_column_list.insert( Tix.END, c )
               
#####################################################################################



    def wupdate_filter_cond_list( self, name = None ):
          self.flist.delete_all()                
          for c in self.filter_conditions:
             e = c[0]
             self.flist.add(e, itemtype=Tix.TEXT, text=c[0])
             txt = self.list2str( c[2:] )
             self.flist.item_create(e, 1, itemtype=Tix.TEXT, text=txt)

          if name != None:
             self.flist.selection_set( name )
          
#####################################################################################


    def wupdate_filter_value_list( self, name ):

                seq= 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
                filter_values = None
                for c in self.filter_conditions:
                   n = c[0]
                   if n == name:
                      filter_values = ( c[2:] )

                self.vlist.delete_all()                
                j = 0
                self.add_values_dict( name )
                for v in self.values_dict[ name ]:
                  e = seq[j]
                  txt = self.truncate_value(v)
                  self.vlist.add(e, itemtype=Tix.TEXT, text=txt)

                  
                  if filter_values: 
                      seltxt = '-'
                      for fv in filter_values:
                          if fv == v :
                              seltxt = 'YES'
                  else:
                      seltxt = '-'
                      

                  self.vlist.item_create(e, 1, itemtype=Tix.TEXT, text=str(self.values_dict_count[ name ][j]))
                  self.vlist.item_create(e, 2, itemtype=Tix.TEXT, text=seltxt)
                  
               
                  j = j + 1
                  if j >= len(seq) : break


           
#####################################################################################
         


    def do_command( self, event ):

       print 'do_command' , event 
       print self.pr(event)

#####################################################################################

    def pr( self, v ):

      
      for kv in dir(v):
        print "  %10s  :  %10s" % ( kv, eval('v.' + kv) )


#####################################################################################

    def wclearfiles( self ):

      print '... removing all logfile data'
    
      self.logfilenames = []
      self.csvfilenames = []
      self.savefilename = ''
      self.logfiles.delete(0,Tk.END)
      self.data = {}
      self.csv_data = []
      self.datacount = 0
      self.recordnum = 0
      self.done_db_logfile_dict = False
      self.db_serial_number = ''

      self.values_dict            = {}
      self.values_dict_count      = {}
      self.values_dict_done       = 0
    
 
#####################################################################################


    def doDestroy(self):
         self.root.destroy()
#####################################################################################
     
    def createCommonButtons(self, master):
         ok     = Tix.Button(master, name='ok',     text='OK',     width=6, command=self.doDestroy) .grid( column=0, row=9,  sticky=Tix.SW)
         apply  = Tix.Button(master, name='apply',  text='Apply',  width=6, command=self.doDestroy) .grid( column=1, row=9,  sticky=Tix.S)
         cancel = Tix.Button(master, name='cancel', text='Cancel', width=6, command=self.doDestroy) .grid( column=2, row=9,  sticky=Tix.S)
         quit   = Tix.Button(master, name='quit',   text='Quit',   width=6, command=sys.exit      ) .grid( column=3, row=9,  sticky=Tix.S)

#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
     
