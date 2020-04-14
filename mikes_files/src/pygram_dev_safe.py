#!/usr/local/bin/python


import sys
sys.path.append( '/tools/gnu/Linux/lib/python' )
sys.path.append( '/tools/gnu/Linux/lib/python/matplotlib-0.91.2-py2.3-linux-i686.egg' )

###################################################################
#
# PYGRAM  MODULE   (Mike Asker : 11jul08)
#
# Python functions to graphically plot data
#
# Provides a pygram() class and a collection of high level functions to plot
# and measure data. It makes use of matplotlib and Tkinter/Tix to provide a GUI.
# It is able to read and process data for Amalfi ATR tester format log files.
# In addition it can read s2p format files, and general purpose csv format data files.
# In addition to ploting data it can read and update excel format spreadsheets and
# populate it with measurement data.
#
###################################################################




# Load the matplotlib and pylab libraries
from   matplotlib.mlab    import load
import matplotlib
#import matplotlib.numerix as nx
import numpy as nu
from   pylab import *

import Tkinter as Tk
from   tkFileDialog   import askopenfilename, asksaveasfilename, askdirectory, askopenfilenames
from   tkSimpleDialog import askstring
from   tkMessageBox   import askyesno , showinfo, showwarning, showerror, askquestion

from   matplotlib.widgets import Button, RectangleSelector
from   matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

# General libraries for doing useful stuff
import re , os, getopt, math, commands, csv, types, glob, time, shutil, getpass, subprocess

import Tix
from   pprint import pprint


## import the excel stuff if we can, we may be on linux and we may not be able to run the excel spreadsheet functions
try:
      from xlrd import open_workbook
      from xlwt import Workbook,easyxf,Formula
      from xlutils.copy import *
      got_xl_import = True

except Exception:
      print '...warning no Excel library modules found, cannot import xlrd,xlwt,xlutils'
      got_xl_import = False



###################################################################
###################################################################
class Logger(object):
    '''Class to send the sys out to a logfile by redefining the write function'''
    def __init__(self):
    
        self.terminal = sys.stdout

        if os.name == 'nt':
          var = 'TEMP'
        else:
          var = 'HOME'

        logfile = os.path.join( os.environ[ var ]  , 'pygram.log')
        self.log = open(logfile, "w")

        self.log2 = None


    def start_log2( self, log2file ):
        self.log2 = open(log2file, "w")

    def write(self, message):
        self.terminal.write( message.encode('UTF-8'))
        self.log.write( message.encode('UTF-8'))
        if self.log2 != None:
            self.log2.write( message.encode('UTF-8'))

    def flush(self):
        self.terminal.flush()
        self.log.flush()
        if self.log2 != None:
               self.log2.flush()


sys.stdout = Logger()



# # start a second pygram session log file in the results directory
# sys.stdout.start_log2( g.savedir  , sys.argv[0] + '.log' ))



###################################################################
###################################################################

class pygram:
    '''A set of methods for plotting Amalfi test data'''

###################################################################
##### INITIALIZE PYGRAM
###################################################################

    def __init__( self ):
      '''Initializes the pygram instance. It defines a long list of pygram variables.
      It also creates the top level pygram window by calling (win_init)

      pygram variables:  self.data = {}   Dictionary of data records. Each column
                                         name from the ATR file is converted into a key name in the self.data dict
                                        Many other keynames are created also. The data is writen into the self.data
                                        as a list of values, one value per record. All self.data[] lists are of the
                                        same self.datacount length.
      Paramters: None
      Returns  : None

      Updates  : Creates and Initializes virtually all the pygram attributes. '''


      # Make the pygram  version number by using the sos revision number and manipulating the string
      txt = '$Revision: 1.164 $'                   # sos revision number, auto assigned by sos when doing a checkin
      txt = re.sub( '.*Revision\S*\s+','dev',txt)  # change R_e_v_i_s_i_o_n  to  d_e_v, this will be changed to X and V when released
      txt = re.sub( r'\$','',txt)
      self.pygram_version = txt

      print '\nPYGRAM: %s,  MATPLOTLIB: %s,  PYTHON: %s\n'%  ( self.pygram_version, matplotlib.__version__,  sys.version[:6])

      self.run_mode = 'script'

      self.pygram_start_time_str = time.strftime("%d%b%y_%H%M", time.localtime()).lower()

      self.script_filename                             = sys.argv[0]
      self.script_dir                                  = os.path.dirname( self.script_filename )
      self.script_basename                             = os.path.basename( self.script_filename )
      ( self.script_rootbasename , self.script_extension ) = os.path.splitext(  self.script_basename )
      ( self.script_rootname , dummy ) = os.path.splitext(  self.script_filename )



      nu.seterr(divide='ignore', invalid='ignore')
#     nu.seterr(divide='raise', invalid='raise')
      matplotlib.rcParams['contour.negative_linestyle'] = 'solid'

      if os.name == 'nt':
        var = 'TEMP'
        self.os = 'PC'
      else:
        var = 'HOME'
        self.os = 'LINUX'



      cwd = os.getcwd()

      self.pyconfig_file =  os.path.join( os.environ[ var ]  , 'pygram.ini')
      self.pyconfig = {}
      self.pyconfig[ 'loaddir' ]  = cwd
      self.pyconfig[ 'savedir' ]  = cwd




      # Define the frequencies of each sub band but round them up, this makes sure we are collecting all of the test results
      # which may include frequencies just outside the extremes of the band
      self.freq_sub_band_list  = [ ['LB-GSM850'    , 820, 850,    836],       \
                                   ['LB-EGSM900'   , 880, 915,    898],       \
                                   ['HB-DCS1800'   , 1710, 1785, 1748],       \
                                   ['HB-PCS1900'   , 1850, 1910, 1880],       \
                                   ['LB'           , 800, 950,    880],       \
                                   ['HB'           , 1700, 1950, 1780],       \
                                 ]

      self.sub_band_list = []
      for b in self.freq_sub_band_list:
        self.sub_band_list.append(  b[0] )

      self.nom_freq_list = []
                                                   #  LB  HB
      self.rated_power_values = {  '@ _33_30'   : [ 33  , 30   ]  ,
                                   '@ _34,2_32' : [ 34.2, 32.0 ]  ,
                                   '@ _5_5'     : [ 5   ,  5   ]  ,
                                   '@ _29_28'   : [ 29  , 28   ]  ,
                                   '@ _31_28,5' : [ 31  , 28.5 ]  ,  }

      self.rated_power_tolerance = 0.5


#       # These are the column names which we will check to see if the test is run nominal under nominal conditions
# #      self.nom_colname_list      = [ 'VSWR', 'Phase(degree)', 'Temp(C)', 'Segments', 'Vbat(Volt)', 'Pwr In(dBm)', 'Regmap' ]
#       self.nom_colname_list      = [ 'VSWR', 'Phase(degree)', 'Temp(C)', 'Vbat(Volt)', 'Pwr In(dBm)', 'Regmap' ]
#       
#       
# 
#       # these are the nominal values which. Nominal data will be chosen with values closest to these
#       self.nom_target_value_list = [   1   ,      0,             25     ,    3.5      ,     3        ,    'x'   ]
# 
# 
#       self.nom_value_list = \
#       [[[ 836, 898, 1748, 1880, -1, -1], [1.0, 0.0, 25, 3.5, 3.0, None], 'N3.5' , [ None, None, None, 3.5, None, None]],
#        [[ 836, 898, 1748, 1880, -1, -1], [1.0, 0.0, 25, 2.7, 3.0, None], 'N2.7' , [ None, None, None, 2.7, None, None]],
#       ]
# 
      # Nominal Conditions variables. List of column names and default values that will be used for determining 
      # whether the test is run under nominal conditions
      self.nom_colname_list      = [ 'VSWR', 'Phase(degree)', 'Temp(C)', 'Vbat(Volt)', 'Pwr In(dBm)',  ]
      self.nom_target_value_list = [   1   ,      0,             25     ,    3.5      ,     3       ,  ]
      # Default nominal conditions list, this is the list of different nominal conditions that will be used
      # [  center-of-band frequencies ], [  Nominal Cond values ], Name   , [ values which have a difference between conditions]
      self.nom_value_list = \
      [[[ 836, 898, 1748, 1880, -1, -1], [1.0, 0.0, 25, 3.5, 3.0], 'N3.5' , [ None, None, None, 3.5, None]],
       [[ 836, 898, 1748, 1880, -1, -1], [1.0, 0.0, 25, 2.7, 3.0], 'N2.7' , [ None, None, None, 2.7, None]],
      ]


      self.value_dict_names_original_list = [ 'logfilename', 'SN', 'TestName', 'Temp(C)', 'Test Freq(MHz)', 'Serial Number',
                                               'HB_LB', 'Sub-band', 'Segments', 'Vbat(Volt)', 'Freq(MHz)', 'Pwr In(dBm)',
                                               'VSWR', 'Phase(degree)', 'Source VSWR', 'Source Phase(degree)',
                                               'Vramp Voltage', 'Regmap', 'Process', 'csvfilename'  ,
                                               'ibcom', 'gpib_addr',  'duration(sec)',  'scpi_wr', 'scpi_rd',
                                            ]
#                                              'Regmap', 'Process', 'Ref Pout(dBm)'  ]
      self.value_dict_names_original_list.sort()
      self.xaxis_reduced_list  =  [ 'Freq(MHz)', 'Temp(C)', '[Time] Time',  '[Time] VAM', '[Time] VRAMP', '[Time] SCOPE CHANNEL 4',
                                    'VSWR', 'Phase(degree)', 'Source VSWR', 'Source Phase(degree)',
                                     'Pout(dBm)', 'VAM(volt)', 'Vbat(Volt)',
                                    'Vramp Voltage', 'Frequency of Spur (MHz)', 'PSA Pwr Out(dBm)', 'Ref Pout(dBm)', 'Step' ]

      self.yaxis_reduced_list  =  [ 'AM-PM Slope (deg/dB)' ,
                                    'AM-PM(degree)' ,
                                    'Pout(dBm)' ,
                                    'AM-PM Slope - Ref (deg/dB) <emp-limits>' ,
                                    'Gain AM/(VAM-offset) Slope - Ref (dB/dB) <emp-limits>' ,
                                    'Gain AM/(VAM-offset) (dB) <emp-limits>' ,
                                    'Amplitude of Spur, no harmonic 15MHz (dBm)',
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
                                    'Vbat_I(Amp)',
                                    'Magnitude',
                                  ]

      # series_seperated_list is a list that causes data to be split into seperate series based on these column names.
      self.series_seperated_list = [ 'Freq(MHz)' ,
                                     'Process',
                                     'Pwr In(dBm)',
                                     'Regmap',
                                     'Segments',
                                     'SN',
                                     'Serial Number',
                                     'Temp(C)',
                                     'TestName',
                                     'Vbat(Volt)',
                                     'logfilename',
                                     'VSWR',
                                     'Source VSWR',
                                   ]




      # Define some test condition parameters
      self.characteristic_impedance = 50.0
      self.vam_offset               = 0.24
      self.ambient_temperature      = 25
      self.harmonic_spur_min_amp    = -49.0
      self.spur_freq_filter_table   = {}

      self.vmuxsel_register      = '22'  # classico
      self.vmuxsel_register      = '24'  # chiarlo



      self.value_dict_names = []
      self.values_dict_done = 0


      # Datapower variables
      self.db_selfam     = None
      self.db_selfam_old = None
      self.db_doublebuttonpress = False
      self.db_seldb     = 'LAB'
      self.db_seldb_old = None
      self.db_serial_number = ''
      self.done_db_logfile_dict = False


      self.data = {}
      self.ref  = {}
      self.datacount = 0
      self.recordnum = 0
      self.atrsectioncount = 0
      self.csvsectioncount = 0

      # Filename variables
      self.atr_logfiles = []
      self.logfilenames = []
      self.csvfilenames = []
      self.oplogfilenames = []
      self.savefilename = ''
      self.savedir     = os.getcwd() + '/'
      self.logfiledir  = os.getcwd() + '/'
      self.logfilename  = ''
      self.logfilebasename  = ''
      self.ref_logfilename  = None
      self.prdfile          = None

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

      self.part_list = {}
      self.failed_part_list = {}





      self.numgrids    = 15
      self.numcontours = 8
#                                 left  right  top    bottom
      self.plot_position       = [0.06, 0.75,  0.92,  0.07 ]
      self.conditions_location = [ 0.76 , 0.88 ]   # window coordinates
      self.legend_location     = [ 0.95, 0.0   ]   # graph data coordinates
      self.color_list = [ 'r','g','b','c','m','y', 'k', 'orange','violet', 'brown', 'purple' ]
      self.dash_list = [ [1,0], [3,2], [10,4], [5,8], [8, 10] ]
      self.plot_marker = '.'
      self.plot_linewidth = 2
      self.save_plot_count = -1
      self.parameter_plot_count = -1


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
      self.png_filename    = ''
      self.png_relfilename = ''
      self.png_dir         = ''
      self.png_reldir      = ''
      self.selected_filter_conditions_str  = ''
      self.print_values_list_str = ''
      self.xl_cell_done = {}
      self.xl_type      = 'prd'

      self.key = 'None'
      self.keysym = 'NoKeyYet'
      self.keysym_dict = {}
      self.hblb        = ''
      self.s2p_type    = ''
      self.product = None

      # Create the main window
      self.win_init()

      self.plot_data = None

      self.vramp_search_testname_bad = 'VRamp Search_NO_MATCH'  ## Intentionally miss-defined so that VRamp Search tests are not detected
      self.vramp_search_testname_good = 'VRamp Search'  

      self.vramp_search_testname = self.vramp_search_testname_bad
      self.run_refpout_from_vrampsearch = 0


      # If we have access to the excel modlues then we can defines some excel styles for writing
      # values into cells.
      try:
        ######################################################################################
        ######################################################################################
        # define the styles used to write data out into the output excel results file
        # one for good passing data, and another for failing data etc

        # standard style for everything we write to the PRD
        stxt = 'font: colour %s; alignment: vertical center, horizontal center, wrap True; pattern: pattern solid, fore_colour %s; '

        thk = 'medium'   # the border thickness
        stxt = '%s borders: left %s, right %s, top %s, bottom %s;' % ( stxt,thk,thk,thk,thk )

        #                                               text   fill
        self.excel_style = {}
        self.excel_style[ 'fail' ]    = easyxf( stxt % ( 'black','coral') )
        self.excel_style[ 'pass' ]    = easyxf( stxt % ( 'black','light_green') )
        self.excel_style[ 'nomeas' ]  = easyxf( stxt % ( 'black','light_green') )
        self.excel_style[ 'typical' ] = easyxf( stxt % ( 'black','light_green') )
        self.excel_style[ 'blank' ]   = easyxf( stxt % ( 'black','white'      ) )
        self.excel_style[ 'typical_fail' ]   = easyxf( stxt % ( 'black','ivory'      ) )
      except Exception: pass



###################################################################
###################################################################

    def get_audit_str(self, prefix = ''):
     ''' Creates a string containing information about the user, input files, output files, versions etc
        Parameter:
           prefix = ''    Prefix string added to the start of each line in the audit string
        Returns:          String multiline sting containing the audit info'''

     txt = ''
     txt = '%s%s*******************************************************************************\n' % ( txt, prefix,                                   )
     txt = '%s%s Script        : %s\n'                                                 % ( txt, prefix, self.script_basename              )
     txt = '%s%s Run on        : %s\n'                                                 % ( txt, prefix, self.pygram_start_time_str        )

     txt = '%s%s Run by        : %s\n'                                                 % ( txt, prefix, getpass.getuser() )
     txt = '%s%s Version Info  : PYGRAM: %s, MATPLOTLIB: %s, PYTHON: %s, OS: %s %s\n' % ( txt, prefix, self.pygram_version, matplotlib.__version__,  sys.version[:6], os.name, self.os)
     txt = '%s%s PyConfig file : %s\n'                                                % ( txt, prefix, os.path.abspath(self.pyconfig_file) )
     txt = '%s%s ATR Logfiles  : %s\n'                                                 % ( txt, prefix, self.logfilenames                 )

     if self.prdfile != None:
        txt = '%s%s PRD .xls file : %s\n'                                              % ( txt, prefix, self.prdfile                      )


     if  len(self.oplogfilenames) > 0:
        txt= '%s%s OP files      : %s\n' % ( txt, prefix, self.oplogfilenames  )

     txt = '%s%s Save Directory: %s\n'                                                % ( txt, prefix, self.savedir                     )


     if 'Serial Number' in self.values_dict:  ttxt = '%s' % self.values_dict['Serial Number']
     else:                                    ttxt = 'UNKNOWN'
     txt = '%s%s Serial Numbers: %s\n'                                                 % ( txt, prefix, ttxt )
     txt = '%s%s*******************************************************************************\n' % ( txt, prefix,                                   )

     return txt









###################################################################
####  HTML Functions
###################################################################

    def html_add_image_text( self, html_file='', txt='', img_file='' ):
        '''Writes txt into the html_file (if present) and writes the html_file as a link into the html_file (if present)
        This function is intended to be used as part of the simcheck utility
        
        Parameters:
           html_file:   HTML filename to write (optional)
           txt:         Text to write into HTML file
           img_file:    Image file to insert into HTML file (optional)
        Returns:        None'''


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
          The returned value is an html string of the form   'val(lim)'
          If the val fails the gtlt test against the lim value then the val
          is colored red 
          
         Parameters:
            val:   value to be checked
            gtlt:  operator '<' or '>' 
            lim:   limit that the val will be compared with
         Returns:
            txt:   Comparison result text'''

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

    def html_add_image_obsolete( self, html_file, txt, img_file ):
       ''' adds txt and the img_file into an html file '''

       txt = re.sub( r'\n', '<br>', txt )


       img_file  = re.sub( r'^/projects/' , 'http://netapp/' , img_file )
       img_base = re.sub( r'.*/', '', img_file )

       fp = open( html_file, 'a' )
       print >> fp , '%s<br>Plot<a href="%s">%s</a><img src="%s">' % (txt, img_file, img_base, img_file)
       fp.close()





###################################################################
###################################################################
#####  ARG Filter Functions

##################################################################################################
    def set_filter_conditions( self, fct, sweep_params_list, nom_vals, tdesc=None ):
        ''' Sets filters based on the graph table row (fct) definition, and in the sweep_params_list.
          It will run self.update_filter_condition on each filter listed in the fct and each filter in
          sweep_parameter_list. The fct list takes precidence.   It also applies the color and line style filters.

            Parameters:
                fct               :  List defining title, xy axes, filters, and measurements (see graph table defintion ???)'
                sweep_params_list :  List of variables that are all set to nominal values (as defined in the nom_vals dict)
                nom_vals          :  Dict of nominal values. One entry for each in the sweep_params_list
                tdesc    = None   :  Optional tdesc, used to define a subdirectory, for saving results.

            Returns:   savefile , title
                savefile :  List of [ filename, subdir1, subdir2 ], where
                                  filename : filename used to save the plot (without extention),
                                  subdir1  : subdirectory of self.savedir where the plot will be saved
                                  subdir2  : subdirectory of self.savedir where the plot will be linked
                title    : Name used as the title of the graph'''



        band = self.get_filter_conditions( 'Sub-band' )
        if type( band ) != types.StringType:  band = ''

        if tdesc!=None:
           subdir = tdesc[ 'parameter' ]
           subdir = self.clean_savefilename( subdir )
        else:
           subdir = None

        # first set all sweep params to nominal
        for swp in sweep_params_list:
            # for s2p logfiles only reset the vbat and temp conditions
            if 's2p' not in tdesc['logfiletype'] or   swp in [ 'Vbat(Volt)','Temp(C)']:
                print '(set_filter_conditions) ', tdesc['logfiletype'], swp
                self.update_filter_conditions(swp, nom_vals[swp] )

        # if the xaxis is part of the sweep_param_list we need to remove it from the filters


        if tdesc!=None:
           xname = tdesc[ 'xynames' ][0]
           if xname in sweep_params_list:
               self.update_filter_conditions(xname, None)


        self.color_series.set('')
        self.line_series.set('')

        for ix, p in enumerate(fct[2:]):


          if p[1] == 'measure' or (len(p) > 2 and p[2] == 'measure') : continue



          if len(p) < 2 :
             print '*** error *** error in filter_conditions_table , line = %s' % (fct)
             print '       error in filter = %s' % p

          swp_name = p[0]
          swp_opt  = p[1]


          if len(p) == 3:  fixed_val = p[2]
          else:            fixed_val = None

          # check for a list
          if len(p) > 3:  vals = p[2:]
          else:           vals = None

          if swp_opt == 'C':

#               self.update_filter_conditions(swp_name)
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



        # finally make up a title based on the name of the test and use the
        # graph id number as a prefix




        cond_str = ''
        for fltr in self.filter_conditions:
              if len ( fltr ) == 3 and fltr[0] in sweep_params_list:
                 cond_str = cond_str + '%s=%s; ' % ( fltr[0], fltr[2] )

        try:
          gn = '%d' % int(float(fct[0]))
        except Exception:
          gn = fct[0]

        if self.product != None:
            product = self.product
        else:
            product = ''


        if self.parameter_plot_count >= 1:
            cstr = ' (%d)' % self.parameter_plot_count
        else:
            cstr = ''

        title = '%s %s %s%s %s\n(%s)' %  ( gn, product, band, cstr, fct[1], cond_str)

        title_filename = '%s %s %s%s %s' %  ( gn, product, band, cstr, subdir)

        title_filename = self.clean_savefilename( title_filename )

        savefile = [ title_filename , 'all_plots', subdir ]

#        print '(set_filter_conditions) title =', title

        return savefile , title

    ###################################################################################################

    def reset_filter_conditions( self, fct ):
        '''Resets all the filter conditions set in the graph table row
        It also clears the color, line_style,  x,ylimits, x,ygrids

        Parameters:  fct   :  graph table row definition.

        Returns:     None
        Updates:     self.filter_conditions[]'''


        self.color_series.set('')
        self.line_series.set('')

#        for p in fct[2:]:
#
#          if p[1] == 'measure' or (len(p) > 2 and p[2] == 'measure') : continue
#          swp_name = p[0]
#          self.update_filter_conditions(swp_name)


        self.filter_conditions = []

        self.xlimits = []
        self.ylimits = []

        self.xgrid = ''
        self.ygrid = ''


    ########################################################################################################
    def set_spec_limits( self, fct, limval ):
       ''' Set the spec limits to be plotted on the graph.
           It looks in the graph table row (fct) to determine which spec limits to add to the graph an.

             ['measure','2','ymin_at_xval','Pnmed','Nmed']
             [ measure',<id#>,<measure_type>, <at_val>, <limit_value> ]

            Where :
               <measeure_type>     is one of  ymin, ymax, ymin_at_xval, ymax_at_xval, ??????
               <at_val>            is where on the x axis the measurement  measured, it is a limval name, or an actual value, or list of two values representing a range.
               <limit_value>       is the limit value that will be drawn on the graph

       Parameters:
           fct    :      graph table row defimnition
           limval :      dict containing the limit values.

       Returns:   None'''

       band = self.get_filter_conditions( 'Sub-band' )
       if type( band ) != types.StringType:  band = ''

       self.spec_limits = []

#      print '(set_spec_limits)' , self.filter_conditions
#      print '(set_spec_limits)' , limval
       #   ....  ['measure','ymin_at_xval','vramp_max','Pout.n']],
       for p in fct:
#         print '(set_spec_limits)', p

         if type( p ) == types.ListType :

           if p[1] == 'measure':

              midnum = str( p[0] )
              mtype      = p[2]
              at_val     = p[3]
              limname    = p[4]

           elif len(p) > 2 and p[2] == 'measure':

              midnum = str( p[0] )
              mtype      = p[3]
              at_val     = p[4]
              limname    = p[5]

           else:  continue

           if at_val == '' : at_val = None



           if isinstance( limname , types.StringTypes):
               if type( limval[ limname ] ) == types.ListType:
                 if band[:2] == 'LB' : y = limval[ limname ][0]
                 else:                 y = limval[ limname ][1]
               else:
                 y = limval[ limname ]
           else:
               y = limname
               limname = mtype


           if isinstance( at_val , types.StringTypes):
               if at_val != None   and at_val  != '':
                   if at_val in limval:
                       if type( limval[ at_val ] ) == types.ListType:
                         if band[:2] == 'LB' : x =  limval[ at_val ][0]
                         else:                 x =  limval[ at_val ][1]
                       else:
                         x = limval[ at_val ]
                   else:
                      r1,r2 = self.get_filter_value_range( at_val )
                      x = [ r1, r2 ]
           else:

              if type( at_val ) == types.ListType:
                x = at_val
              else:
                x = at_val

#           print '(set_spec_limits) <%s>  <%s> %s' % (limname, y, type(y))

           if limname != None  and limname != '' :
               if at_val == None:     self.spec_limits.append( [ y , limname + ' = ' + str(y) , 2, 'k'] )
               else:
                   if type( x ) != types.ListType:
                           self.spec_limits.append( [[[x*0.97, y],[x*1.03, y]]  , limname + ' = ' + str(y) , 2, 'k'] )
                   else:
                      if x[0] != None and x[1] != None:
                         self.spec_limits.append( [[[float(x[0])*0.97, y],[float(x[-1])*1.03, y]]  , '%s = %s @ %s' % ( limname, str(y), x) , 2, 'k'] )
                      elif x[0] != None:
                         self.spec_limits.append( [[[float(x[0])*0.97, y],[float(x[0])*1.03, y]]  , '%s = %s @ %s' % ( limname, str(y), x) , 2, 'k'] )
                      elif x[-1] != None:
                         self.spec_limits.append( [[[float(x[-1])*0.97, y],[float(x[-1])*1.03, y]]  , '%s = %s @ %s' % ( limname, str(y), x) , 2, 'k'] )

           if x != None:
              if type( x ) != types.ListType:
                     self.spec_limits.append( [[[ x, y*1.1],[x, y*0.9]] , '' , 2, 'y'] )

              else:
                 for xt in x:
                     self.spec_limits.append( [[[ xt, y*1.1],[xt, y*0.9]] , '' , 2, 'y'] )


###################################################################
    def set_xyaxes_limits( self, tdesc ):
        ''' Function to set the xy graph axes limits, based on the tdesc dictionary value for key 'xyaxes_limits'
            The tdesc['xyaxes_limits'] can be take on one of the following forms:
            tdesc['xyaxes_limits'] : None   or  []  or ''
                                             All bands
            tdesc['xyaxes_limits'] : [ [ 0.0, 2.0],[-20,40 ] ],
                                             LB                          HB
            tdesc['xyaxes_limits'] : [ [ 0.0, 2.0],[-20,40 ] ,  [ 0.0, 2.0],[-20,40 ] ],
                                          gsm850           egsm900          dcs1800           pcs1900
            tdesc['xyaxes_limits'] : [ [0,2],[-20,40]  ,[0,2],[-20,40],  [0,2],[-20,40],  [0,2],[-20,40]]

         Parameters:
              tdesc    :  Dict containing a 'xyaxes_limits' key

         Returns:      None  '''

#        print "(set_xyaxes_limits) tdesc[ 'xylimits' ] = ", tdesc[ 'xylimits' ]

        self.xlimits = []
        self.ylimits = []


        if 'xylimits' in tdesc:

               # first expand the xyaxes_limits to cover all 4 sub-bands
               tlm = tdesc[ 'xylimits' ]

               if isinstance( tlm, types.ListType) and tlm != []:


                   ntlm = []
                   if len(tlm) == 2:
                      ntlm = [ tlm[0],tlm[1],  tlm[0],tlm[1],  tlm[0],tlm[1],  tlm[0],tlm[1],  tlm[0],tlm[1],  tlm[0],tlm[1], ]
                   elif len(tlm) == 4:
                      ntlm = [ tlm[0],tlm[1],  tlm[0],tlm[1],  tlm[2],tlm[3],  tlm[2],tlm[3],   tlm[0],tlm[1],   tlm[2],tlm[3]  ]
                   elif len(tlm) == 8:
                      ntlm = [ tlm[0],tlm[1],  tlm[2],tlm[3],  tlm[4],tlm[5],  tlm[6],tlm[7],   tlm[0],tlm[1],   tlm[4],tlm[5]  ]
                   elif len(tlm) == 12:
                      ntlm = tlm
                   else:
                       print '*** ERROR *** (set_xyaxes_limits)  tdesc[ \'xylimits\' ] incorrectly specified, it must be a 2,4,8,12 element list'
                       print '  tdesc[ \'xylimits\' ] = ', tlm

                   if ntlm != []:

                       band = self.get_filter_conditions( 'Sub-band' )
                       if type( band ) != types.StringType:  band = ''

                       try:
                          idx = self.sub_band_list[:5].index( band )

                          xl = ntlm[  idx*2   ]
                          yl = ntlm[  idx*2 +1]

                       except Exception:
                          # didnt find the band therefore coose the first definitions 0 and 1

                          xl = ntlm[ 0 ]
                          yl = ntlm[ 1 ]

                       if  isinstance( xl, types.ListType) and       \
                              isinstance( yl, types.ListType) :

                             self.xlimits = xl
                             self.ylimits = yl

#                             print '(set_xyaxes_limits) setting limits to', xl, yl

                       else:
                              print '*** ERROR *** (set_xyaxes_limits)  tdesc[ \'xyaxes_limits\' ] incorrectly specified, each limit must be list of 0 or 2 numbers'
                              print '  tdesc[ \'xylimits\' ] = ', tlm





        self.xgrid = ''
        self.ygrid = ''
        if 'xygrids' in tdesc:
             glst = tdesc['xygrids']
             if isinstance( glst, types.ListType) and len(glst) == 2 :
                self.xgrid = glst[0]
                self.ygrid = glst[1]

#        print "(set_xyaxes_limits) 1 tdesc['lineon'] = "

        # Noramlly set the graph lines to be on.
        bval = True
        if 'lineon' in tdesc:
             bval = tdesc['lineon']
#             print "(set_xyaxes_limits) 2 tdesc['lineon'] = ",tdesc['lineon']
        self.line_on.set( bval )

        return

###################################################################




#####  Excel Functions 
###################################################################
    def add_excel_results( self, wb, sheetn, row, col, txt, style_key='', hyperlink='' ):
           ''' Write out the result to the excel spreadsheet.
           But look to see if it we have results from a previous run, if so
           add this result at the begining of the string.

           Check to see if we have written to this cell before in this run. If
           we have then don't write it again. i.e. only write to each cell once.

           Also write out the result to a temp file so that we can use it
           for subsequent runs. If previous results are present these are
           rewritten out again also.

           Parameters:
                wb     : excel workbook handle
                sheetn : the spreadsheet worksheet number
                col    : column number in the spreadsheet
                row    : row number in the spreadsheet
                txt    : The raw text to appear in the cell (no formula stuff)
                style  : key index into self.excel_style{} dict to point to a excel style to use for the cell
                           (default 'blank' will cause a white background cell)
                hyperlink : hyperlink filename path, (default '' no hyperlink will be written)

           Returns:  None
           Reads  :  self.xl_previous_values[ idx ]
           Updates:  self.xl_done_cell[ idx ]'''


#           print '(add_excel_results) ', wb, sheetn, row, col, [ txt, style_key, hyperlink]


           # look in the previous results to see if there were previous results for this cell
           # if so look to see if they are different the latest results, if they are different then
           # add the previous results after the current results.
#           idx = '%s %s %s' % ( sheetn, row, col )
#           if idx in self.xl_previous_values:
#               previous_value = self.xl_previous_values[ idx ]
#               if previous_value.strip() !=  txt.strip():       # if the two results were different
#                       txt = '%s ; %s' % (txt, previous_value)

           # Write the text into the excel spreadsheet cell,
           # If we are writing a hypertext link then make up the hyperlink formula htxt

           ws = wb.get_sheet(sheetn)

           # there is a limit of 255 chars in the hypertext formula,
           # therefore truncate the text to 250 chars (only in the formula cells)
           ttxt = txt
           if len( txt) > 250:  ttxt = txt[:250]


           if style_key != None and style_key != '':
               style = self.excel_style[ style_key ]
               if hyperlink == '':
                  htxt = txt
                  ws.write(row, col, txt , style)
               else:
                  htxt = 'HYPERLINK("%s";"%s")' % ( hyperlink, ttxt)
                  ws.write(row, col, Formula( htxt ) , style)
           else:
              if hyperlink == '':
                  htxt = txt
                  ws.write(row, col, txt )
              else:
                  htxt = 'HYPERLINK("%s";"%s")' % ( hyperlink, ttxt)
                  ws.write(row, col, Formula( htxt ) )


              

           # write the results and previous results back out to the excel tmpfile
           self.write_xl_tmpfile( sheetn, row, col, htxt , style_key, txt )

###################################################################
    def write_xl_part_info( self, wb, data_dict ):
        '''Write out general info into the excel output file.
        It uses the data_dict to specify the value to be written out and
        the location and style to use.  The data_dict key is the name of the
        self.data column to use, The values of this column are concatenated
        together to make the final value.

        e.g.
          #                 Name            sheetnum, row   col  style
             data_dict = { 'Chip Model'       : [ 0,   0,   4,  'blank' ] ,
                           'Serial Number'    : [ 0,   1,   4,  'pass'  ] ,
                           'Test Date & Time' : [ 0,   2,   4,  'blanlk' ]
                         }

        Parameters:
             wb        :   Pointer into an already created output Excel Workbook
             data_dict :   Dictionary of column names to use for the value and the location and style
        '''



        for name in data_dict:
            if name not in self.values_dict:
                 self.add_values_dict(name)
#            print '(write_xl_part_info) ' , self.values_dict[name]

            tstr = ' '.join( self.values_dict[name])
            ws    = wb.get_sheet(  data_dict[name][0] )
            row   = data_dict[name][1]
            col   = data_dict[name][2]
            style = data_dict[name][3]

            ws.write(row , col , tstr, self.excel_style[ style ])
            if name == 'Serial Number':
                ws.name = tstr
           


###################################################################
    def init_xl_tmpfile( self, opxl, wb ):
        '''Reads an existing tempfile. The data in this file is a list of the measurments
        made on a previous run. The measurements are written to the output excel workbook.
        Subsequent runs will add more measurement data to this file.
        (note the excel xlrd module is unable to read Formulae and Hyperlink data from a spreadsheet,
         so it is necessary for us to save the hyperlink data into a hidden temporary file where we can
         use it to populate the spreadsheet with past measurements ) This function will populate
         the excel spreadsheet with all the previous measurments form past runs.

        Parameters:
             opxl  : Name of temporay file used for saving measurment data
             wb    : excel workbook where the previous measurements will be written

        Returns:
             file  : File handle to the tmpfile  '''

        tmpfile = opxl + '.tmp'

        fop = None

        self.xl_previous_values = {}

        if not os.access(tmpfile, os.R_OK):
            fop = open(  tmpfile, 'w' )
        else:

            print '    (init_xl_tmpfile) reading excel tmpfile' , tmpfile
            fip = open(  tmpfile, 'r' )

            # Now go through the existing tmpfile and read everything
            # and load this into the new output spreadsheet
            for line in fip:

#                    print '(init_xl_tmpfile)    read line' , line.strip()
                     flds = line.split('|')
                     ff = []
                     for f in flds:
                         f = f.strip()
                         try:
                           f = int(f)
                         except Exception: pass
                         ff.append(f)


                     if len(ff) == 6:

                       ws = wb.get_sheet(ff[0])

                       ff[3] = re.sub( r'&nl&' ,'\n', ff[3] )

                       if ff[4] != '':
                           if re.search(r'HYPERLINK', ff[3])  :
                              ws.write(ff[1], ff[2], Formula( ff[3] ) , self.excel_style[ ff[4] ])
                           else:
                              ws.write(ff[1], ff[2], ff[3] , self.excel_style[ ff[4] ])
                       else:
                           if re.search(r'HYPERLINK', ff[3])  :
                              ws.write(ff[1], ff[2], Formula( ff[3] ))
                           else:
                              ws.write(ff[1], ff[2], ff[3] )




                       # setup a dictionary of saved values
                       idx = '%s %s %s' % ( ff[0], ff[1], ff[2] )
                       ff[5] = re.sub( r'&nl&' ,'\n', ff[5] )
                       self.xl_previous_values[ idx ] = str( ff[5] )


                     else:
                       print "(init_xl_tmpfile) *** ERROR *** excel tmpfile '%s' line does not have 6 fields, cannot update excel output\n   %s" % (tmpfile,  line.strip())
            fip.close()
            fop = open(  tmpfile, 'a' )
        print '    (init_xl_tmpfile) writing excel tmpfile' , tmpfile
        return fop

###################################################################
    def write_xl_tmpfile( self, sheetnum, row, col, val, style, txt ):
        ''' Writes out the value val to a temporary file, so that we can run the ARGPRD
        scripts incrementally.
         (note the excel xlrd module is unable to read Formulae and Hyperlink data from a spreadsheet,
         so it is necessary for us to save the hyperlink data into a hidden temporary file where we can
         use it to populate the spreadsheet with past measurements ) This function will
         write the value and the location in the spreadsheet so that it can be read in
         future runs.

        Parameters:
            sheetnum:    Excel Sheet number
            row     :    Excel Row number
            col     :    Excel Column number
            val     :    value to be written
            style   :    Excel style
            txt     :    String to be written

        Returns:    None '''


        # only write this to this cell once

        idx = '%s %s %s' % ( sheetnum, row, col )

        if idx not in self.xl_cell_done:
                self.xl_cell_done[ idx ] = 'done'

                # make sure the text we write doesn't have any cariage return characters '\n'
                # if so replace them with special chars

                txt = re.sub( r'\n', '&nl&' , txt )
                val = re.sub( r'\n', '&nl&' , val )

                print >> self.xl_tmpfile , '%s | %s | %s | %s | %s | %s' % ( sheetnum , row, col, val, style, txt )


###################################################################
##### PRD  Functions
###################################################################


    def get_prd_data( self, rb ):
        '''   Reads through the sheets of an excel PRD spreadsheet, and create a
        list of dictionaries containing parameter data in the prd.
        It looks at each sheet for column headings listed in
        self.prd_headers_lst, if found it will create a dictionary for each
        for the values. This is repeated for every row in the spreadsheet.


        Parameters:
              rb       :  Pointer to the excel spreadsheet to be read

        Returns:
              prd_list :
        '''


        prd_list = []


        # Loop round the PRD sheets, looking for ones which have the correct column headings
        for snum,s in enumerate( rb.sheets() ):


           # Find out which sub-band this sheet is for
           # from the sheet name we get the sub-band
           sheet_band = None

           grps = re.search( r'(\d+)', s.name )
           if grps:
               sn_num = grps.groups()[0]
               for sb in self.sub_band_list:
                  grps = re.search( r'(\d+)', sb )
                  if grps:
                       sbl_num = grps.groups()[0]
                       if sbl_num == sn_num:
                          sheet_band = sb
                          break

#           print ' = = = = = = = = = = = = = = = = = '

           # Go through the columns of first 2 rows and get the column header names (or 5 for performance logs)
           # and build a couple of lookup dictionaries to get us from column number to
           # heading name (and visa-versa)
           n2c = {}
           c2n = {}


           # There are currently two types of excel file that pygram can read
           #   - a PRD xls file
           #   - a Performance Log Template xls file
           # We will look for the column headings to determine whether the sheet
           # which can be processed. The column headers will be different for each xls file type
           #
           # self.prd_header_list is list of column header names expected in the spreadsheet
           # (note: they are all set to lower case, we convert to lowercase before comparing
           if self.xl_type == 'prd'     :
              row_hdr = 2
              self.prd_header_lst = [ '#', 'parameters', 'min', 'typical', 'max', 'unit', 'conditions', 'comments', 'min_2', 'typical_2', 'max_2']

           if self.xl_type == 'perf_log':
              row_hdr = 5
              self.prd_header_lst = [ '#', 'parameters', 'data', 'limit', 'pass/fail', 'comments']

           if self.xl_type == 'mktg_plots':
              row_hdr = 5
              self.prd_header_lst = [ '#', 'parameters', 'vs (x-axis)' ]

           # Go through the first few rows of the sheet collecting the names of the
           # column headers found, create a n2c and c2n dictionary so we can do an easy lookup
           for row in range(s.nrows):
              if row >= row_hdr:  break
              for col_num in range(s.ncols):
                 name = s.cell(row,col_num).value
                 name = str( name )
                 name = name.lower()
                 if name != '':
                    if name not in n2c:
                       n2c[ name ] = col_num
                       c2n[ col_num ] = name
                    else:
                       name = name + '_2'  # the second (or last name) will have _2 suffix, normally used for the results columns
                       n2c[ name ] = col_num
                       c2n[ col_num ] = name





           # Look through the column name dictionaries and
           # make sure we have all the required columns in this sheet
           # If not then this sheet cannot be used for plotting.
           missing_header_name = ''
           good_sheet = True
           for hn in self.prd_header_lst:
              if hn not in n2c:
                 good_sheet = False
                 missing_header_name = hn
                 break




           # If we have a good sheet then, we will proceed to collect all the
           # text in the prd_header_lst columns
           if good_sheet:
               print "  .(get_prd_data) found xls sheet: '%s' which matches sub-band %s"  % (s.name, sheet_band )

               if self.xl_type == 'prd':
                   # identifiy the columns which will be used to write the measurement results
                   result_col_min   = n2c[ 'min_2']
                   result_col_max   = n2c[ 'max_2']
                   result_col_typ   = n2c[ 'typical_2']
                   unit_col         = n2c[ 'unit']
                   comments_col     = n2c[ 'comments' ]
               if self.xl_type == 'perf_log':
                   result_col_data  = n2c[ 'data' ]
                   result_col_passfail  = n2c[ 'pass/fail' ]
                   comments_col     = n2c[ 'comments' ]
               if self.xl_type == 'mktg_plots':
                   result_col_plots  = n2c[ 'vs (x-axis)' ]
                   result_col_passfail  = n2c[ 'pass/fail' ]
                   comments_col     = n2c[ 'Notes' ]



               old_parameters = ''

               # Go through the remainder of the rows in this sheet
               # and create a pdata dictionary of all the values found
               # and add it to the prd_list
               for row in range(row_hdr,s.nrows):

                    # Add general info to the pdata dict
                    if self.xl_type == 'prd':
                                  # sheet_number, sheet_name, band, row_numer, measurement_result_column
                        pdata = { 'sheet_num' : snum,
                                  'sheet_name': s.name,
                                  'sub-band'  : sheet_band,
                                  'row'       : row,
                                  'result_col_min' : result_col_min,
                                  'result_col_typ' : result_col_typ,
                                  'result_col_max' : result_col_max,
                                  'unit_col'       : unit_col,
                                  'comments_col'   : comments_col,
                                }
                    elif self.xl_type == 'perf_log':
                        pdata = { 'sheet_num' : snum,
                                  'sheet_name': s.name,
                                  'sub-band'  : sheet_band,
                                  'row'       : row,
                                  'result_col_data'     : result_col_data,
                                  'result_col_passfail' : result_col_passfail,
                                  'comments_col'        : comments_col,
                                }
                    elif self.xl_type == 'mktg_plots':
                        pdata = { 'sheet_num' : snum,
                                  'sheet_name': s.name,
                                  'sub-band'  : sheet_band,
                                  'row'       : row,
                                }


                    # For each of the columns in the prd_header_list
                    # add the value to pdata dict
                    for hn in self.prd_header_lst:
                        try:
                           val = str(s.cell( row, n2c[ hn ] ).value )
                        except Exception:
                           val = s.cell( row, n2c[ hn ]).value

                        if hn == '#':
        #                    print '%%%%% id#   ',  val, type(val)
                            try:
                               val = str( int(float(val)))
                            except Exception:
                               pass
#                        print '(get_prd_data)  %20s        col=%2s  row=%2s      <%s>  <%s>' %   (hn, n2c[hn] , row, val, s.cell( row, n2c[ hn ] ) )

                        val = re.sub( '\s\s+', ' ', val).strip()



                        if hn.lower() == 'parameters' and pdata[ '#' ] != '' :
                           if  val == '' :
                              val = old_parameters



                        pdata[ hn ] =  val

                        if hn.lower() == 'parameters' and val != '' :
                            old_parameters = val




                    for c in [ 'min', 'typical', 'max' ]:
                          try:
                              v = pdata[ c ]
                              v = re.sub( r':.*', '', v )  # clean up the limit values, remove any :1 from 3:1 type limit
                              pdata[ c ] = v
                          except: pass

#                   print  '\n(get_prd_data) pdata =', pdata

               # check to see if the min or max values contain '+/-'
               # if they do then populate both the min and max columns with the respective values

                    if self.xl_type == 'prd':
                        for c in [ 'min', 'max' ]:
                           v = pdata[ c ]
                           if v != '':
    #                          print '(get_prd_data) converting +/- limits', c, str(v)
                              grps =  re.search( '(\+\/\-)\s*(\S+)', str(v))
                              if grps:
                                  v = grps.groups()[1]
                                  pdata[ 'min' ] = - float(v)
                                  pdata[ 'max' ] =   float(v)


                    prd_list.append(  pdata  )

           else:
               print "      (get_prd_data) ..warning, cannot process sheet '%s' as it does not have all the correct column heading names (column '%s' is missing)" % (s.name, missing_header_name )

        return prd_list

###################################################################
    def get_test_desc( self, tdesc, prdl, idnum=None, arg_testmode = 'list' ):

        ''' Gets the test desc data (tdesc) associated with a PRD test (prd1)
        If the prd1['parameters'] matches the tdesc['parameter'] name then it
        returns tdesc, if not it returns None.
        If the idnum is specified it will also check that it matches the prdl['#']

        Parameters:
             tdesc  :   dict containing info on how to plot this parameter
             prdl   :   dict containing info the PRD test
             idnum = None : An idnumber, or a list of idnumbers, or a string containing a list
                 of idnums, If arg_testmode = 'list' and if the number or one of the numbers
                 matches the prdl['#'] then the test will be run.
             arg_testmode = 'list' : If ='all' all tests are run.
                                     If ='list' then only tests which match idnum will be run
                                     All other values will be against the test prdl[ logfiletypes ]
                                     values, if it matches then the test will be run

        Returns:  tdesc only if tdesc[ 'parameter'] matches prdl['parameters']
                    The match is done ignoring case and ignoring spaces.
                    It also only matches upto the the length of tdesc['parameter']
                  Returns None if no match is made'''

        self.selected_filter_conditions_str  = ''

        pname = prdl[ 'parameters'].lower()
        pname = re.sub( '\s+','',  pname)



        if self.xl_type == 'perf_log':
            # Ignore the frequency at the beginning of the Test name
            pname = re.sub( '^\d+','',  pname)

        if self.xl_type == 'mktg_plots':
            # Ignore the band at the beginning of the Test name
            pname = re.sub( '^\S+','',  pname)



        ret_val = None

        if 1:

           tname =  re.sub( '\s+','', tdesc[ 'parameter' ] ).lower()

           tln = len(tname)

           if len(pname) < tln : return ret_val

           if tname[ :tln ] == pname[ :tln ] :
               if arg_testmode == 'all' :
                   return tdesc

               elif arg_testmode == 'list':

                  # if the idnum is a string, split it up into a list
                  if not isinstance( idnum, types.ListType ):
                      idnum = str(idnum)
                      idnum = idnum.split()

                  # check to see if the idnum of this prd test is in the idnum list
                  for idn in idnum:
                    idn = str(idn).strip()

                    if prdl[ '#' ].upper() == idn.upper():
                         return tdesc

               else:
                   # for other atr_test modes look to see if it matches to any of the 'logfiletype' values for this test

                   if  arg_testmode  in  tdesc[ 'logfiletype' ]:
                         return tdesc

        return ret_val


###################################################################

    def get_prd_rated_power_conditions( self, prd_list ):
        '''Look at the prd_list for all the 'Conditions', if we see a
        'Set Vramp to XX dBm' condition then this indicates that a rated power
         filter is required

         All the rated power condtions are listed and a miimum set of '@ Prated' filters
         is created

         prd_test[ 'conditions'] is updated with the new rated power condition and the
         the rate_power_values list returned

         Parameters:
             prd_list:   List of PRD dicts, one per idnum

         Returns:    rated_power_values  list of rated power values.
         Updates:    prd_list[]['conditions']   It adds '@ Prated_x_x_x_x = 1' to the conditions
         '''

        rated_power_values   = {}
        rated_power_values_x = {}
        rated_power_values_idnum_list = {}

        for prd_test in prd_list:

           if 'conditions' in prd_test:
               cl = prd_test[ 'conditions'].split(';')
               prd_test[ 'rated power value'] = []
               
#               if prd_test[ '#'] == '146': sys.exit()

               for cond in cl:
                  
                  pwrs = []
                  grps = re.search( r'Ref\s*Pout\s*=\s*(\d.*)', cond, re.I)
                  if grps:
                      pwr_str = grps.groups()[0]
                      pwr_str = re.sub(' ',',', pwr_str)
                      pwrs = pwr_str.split(',')
                  else:
                  
                      grps = re.search( r'Set Vramp to ([\d\.]+)', cond, re.I)
                      if grps:
                         rpwr = grps.groups()[0]
                         pwrs = [ rpwr ]
                         
#                   print '(get_rated_power_conditions) %10s %2s %30s %30s %5s' \
#                 % ( prd_test[ 'sub-band' ], \
#                      prd_test[ '#'], \
#                      prd_test['parameters'], \
#                      cond ,
#                      pwrs )

                  for rpwr_raw in pwrs:
                             rpwr = rpwr_raw.strip()     
                             try:
                               x = float( rpwr )
                             except:
                               continue
                             
#                             print '(get_rated_power_conditions) XXXX doing rpwr=', rpwr
                               
                             par = prd_test[ 'parameters' ]
                             par = re.sub( r'\s\s+', ' ', par).lower()     # remove multiple spaces
        
        #                     # create a lookup table between the rated_power_value name and the test id num
        #                     if par not in rated_power_values_idnum_list:
        #                        rated_power_values_idnum_list[ par ] = []
        #                     rated_power_values_idnum_list[ par ].append( prd_test['#'])
        
        
        
                             if par not in rated_power_values:
                                rated_power_values[ par ] = [ [], [], [], [] ]
        
                             # save the rpwr value for this specific test in the rated_power_values dict
                             # (this is a 4 element list, one power level is added for each ref power found in each subband)
                             sb = prd_test[ 'sub-band' ]
        
                             for i in [0,1,2,3]:
                                 if self.sub_band_list[i] == sb :
                                      if 0 and  rated_power_values[ par ][i] != None and abs( float( rpwr ) - rated_power_values[ par ][i]) > 0.01 :
                                            print '*** ERROR *** (get_rated_power_conditions) In the PRD different "Set Vramp at XX dBm" conditions were defined for two tests with the same parameter name (and also in the same sub-band)'
                                            print '        PRD Test Num #  = ',  prd_test[ '#']
                                            print '        PRD Sheetname   = ',  prd_test['sheet_name' ]
                                            print '        Sub-band        = ',  prd_test['sub-band' ]
                                            print '        Parameter       = ',  prd_test['parameters']
                                            print '        1st Rated Power = ',  rated_power_values[ par ][i]
                                            print '        2nd Rated Power = ',  float( rpwr )
                                            print "  Either change the the parameter name in the PRD (and script) for one of the two tests, or change the 'Set Vramp at XX dBm' condition"
        
                                      rated_power_values[ par ][i].append( float( rpwr ) )
        
                             # if we have a straight HB or LB definition in the PRD then add it to tthe 
                             if sb == self.sub_band_list[4] :
                                 if rated_power_values[ par ][0] != None : rated_power_values[ par ][0].append(float( rpwr ))
                                 if rated_power_values[ par ][1] != None : rated_power_values[ par ][1].append(float( rpwr ))
                             if sb == self.sub_band_list[5] :
                                 if rated_power_values[ par ][2] != None : rated_power_values[ par ][2].append(float( rpwr ))
                                 if rated_power_values[ par ][3] != None : rated_power_values[ par ][3].append(float( rpwr ))
        
                             # save away the actual rated power, we will use this later when making up the graph title
                             prd_test[ 'rated power value'].append(rpwr)
        
                             rpwr_str = '@Pr %0.1f' % float(rpwr)
                             rated_power_values_x[ rpwr_str ] = float(rpwr) 

#                print "(get_rated_power_conditions) prd_test[ 'rated power value']", prd_test[ 'rated power value']
#                print "(get_rated_power_conditions) rated_power_values", rated_power_values


 # Set the rated power based on the sub-band
 #       self.freq_sub_band_list  = [ ['LB-GSM850'    , 820, 850] ,      \
 #                                  ['LB-EGSM900'   , 880, 915] ,        \
 #                                  ['HB-DCS1800'   , 1710, 1785],       \
 #                                  ['HB-PCS1900'   , 1850, 1910],       \
 #                                  ['LB'           , 800, 950],         \
 #                                  ['HB'           , 1700, 1950],       \
 #                                ]

 #       for p in rated_power_values:
 #          print '(get_rated_power_conditions)  rated_power_values[%s]   =  %s' % ( p, rated_power_values[ p ] )




        # Reduce the number of rated_power_value entries.
        # Many of the tests use the same rated power values

        # go through each of the rated_power_values entries, and remove any entries
        # which have the same entries. We Also need to create a lookup table which
        # tells us which rated_power_values entry to use for each test.


        prefix = '@ Prated'
        idx_max = 0
        new_rated_power_values = {}

        p2n = {}

        for p in rated_power_values:
           r = rated_power_values[ p ]
           new_name = '%s_%s_%s_%s_%s' % (prefix, r[0],r[1],r[2],r[3])
           new_name = re.sub( '\.0\d*', '', new_name)        # clean up the new_name for tkinter listbox
           new_name = re.sub( '\.', ',', new_name)             #   it must not contain any '.' characters
#           print '(get_rated_power_conditions) p2n_loop <%s> <%s>'%  (p , new_name)
           p2n[ p ] = new_name
           if new_name not in new_rated_power_values:

               new_rated_power_values[ new_name ] = r
               p2n[ p ] = new_name
#               print '(get_rated_power_conditions)      adding p2n', new_name,   r, p
#           print '(get_rated_power_conditions)2     adding p2n', [ p, rated_power_values[ p ],  p2n[ p ],   new_rated_power_values[ new_name ] ]



        # go through all the prd tests and if the parameter matches a name in the  p2n dict
        # we will add the condtion using the new_rated_power_values new_name
        # with the p2n lookup table we can rename the new


        for prd_test in prd_list:

           if 'conditions' in prd_test:
               cl = prd_test[ 'conditions'].split(';')
               cl_new = ''
               for cond in cl:
                  cond_new = cond
                  cl_new = cl_new + cond_new + ';'
                  grps = re.search( r'Set Vramp to ([\d\.]+)', cond, re.I)
                  if grps:
                     rpwr = grps.groups()[0]
 #                    print '(get_rated_power_conditions)2 %10s %2s %30s %30s %5s' \
 #                       % ( prd_test[ 'sub-band' ], \
 #                           prd_test[ '#'], \
 #                           prd_test['parameters'], \
 #                           cond ,
 #                           rpwr )


                     par = prd_test[ 'parameters' ]
#                     par = re.sub( r'@', 'AT', par)     # change the @ to something else (@ rated power) name might cause confusion
                     par = re.sub( r'\s\s+', ' ', par).lower()
#                     par = '@ Prated {' + par + '}'

                     if par in p2n:
                         new_name = p2n[ par ]
                     else:
                         new_name = '???'
                         print '*** ERROR *** (get_rated_power_conditions) could not find p2n[%s]' % par

                     cond_new = '%s = 1' % ( new_name )
                     cl_new = cl_new + cond_new + ';'

               prd_test[ 'conditions' ] = cl_new

        rated_power_values = new_rated_power_values
        rated_power_values = rated_power_values_x


        print '(get_rated_power_values)', rated_power_values


        return rated_power_values


###################################################################

    def check_test_desc_ok( self, test_desc ):
        '''Looks through the test descrition (tdesc) to check whether it is properly defined.
        checking for the correct numbers of items in the list, and whether it has the right keys

        Parameters:
            test_desc:   test description detailing the how to plot and measure the parameter

        Returns:   None'''


        if len(test_desc) < 4:
           print "*** ERROR *** test_desc_lst is too short '%s'" % ( test_desc )
           sys.exit()


        pname = test_desc[ 'parameter' ]
        # test wether the axes list is a list (error if not)

        if 'xynames' not in test_desc or not isinstance( test_desc['xynames'] , types.ListType ):  # a single value gets replicated 4 times
           print "*** ERROR *** (check_test_desc_ok) test_desc the 4th value axes '%s' should be a list, e.g. ['Freq(MHz)','Pout(dBm)']\n%s" % (test_desc[3], test_desc )
           sys.exit()



        # check whether the x and y axes are available


        for ax in test_desc[ 'xynames' ]:
           if ax not in self.data:
               print "...warning... (check_test_desc_ok) the logfiles do not contain any data for '%s' axis" % ( ax )
               print '               found in test_desc' , pname




        # test whether the test name is a string (error if not)

#        if not isinstance( test_desc[2] , types.StringTypes ):  # a single value gets replicated 4 times
#           print "*** ERROR *** test_desc_lst 3rd value should be the TestName '%s' and it should be a string, e.g. 'PAE(%%)'\n%s" % (test_desc[2], test_desc )
#           sys.exit()


        # check whether the test name is available
        if 'TestName' in self.data:
              tnl = self.values_dict[ 'TestName']
              if test_desc['testname'] not in tnl:
               print "...warning... (check_test_desc_ok) the log files do not contain any test with TestName = '%s'" % ( test_desc['testname'] )
               print '     found in test_desc_list' , pname
               print '     These are the tests which were found in the logfiles' , tnl





        # check whther we have the correct log file types available



        pass

###################################################################

    def check_prd_test_ok( self, prd_test ):
       '''Looks through the PRD info (prd_test) to check whether it is properly defined.
        checking for the correct numbers of items in the list, and whether it has the right keys
        CURRENTLY DOES NOTHING

        Parameters:
            prd_test:   PRD description detailing parameter, limits, and conditions

        Returns:   None'''

       pass

###################################################################


    def gen_graph_table_row( self, test_desc, prd_test):
        ''' Takes the test_desc and the prd_test info and creates a graph_table
            row (fct) so that a graph and measurement can be done

            It is assumed the the test_desc and the prd_test have been successfully matched
            (using self.get_test_desc).

                ['1', 'AM7801 Max Output Power vs Vramp across Parts',
                        ['Freq(MHz)', 'C'], ['SN', 'L'],
                        ['1', 'measure', 'ymin_at_xval', 'Vramp_max', 'Prated']]

        Parameters:
             test_desc:    test description dict containg info on how to plot the graph, and how to make the measurements
             prd_test :    PRD parameter dict containing inof on the test limits and condtions

        Returns:    g_row     Graph Table Row (same as fct) '''

#        print test_desc
#        print prd_test


        print '\n******************************************************************************'
        print '******************************************************************************'
        tstr = '(gen_graph_table_row) %s:    DOING PRD # %s [%s]' % ( prd_test['sheet_name'], prd_test[ '#'],  prd_test[ 'parameters' ] )
        print tstr
        print '******************************************************************************'
        print '******************************************************************************'

        self.selected_filter_conditions_str  = '%s\n%s' % ( self.selected_filter_conditions_str, tstr)




        self.check_test_desc_ok( test_desc )
        self.check_prd_test_ok( prd_test )

#        print '(gen_graph_table_row)  cl =',  prd_test[ 'conditions'].split(';')


        g_row = []

        at_val = ''

        g_row.append( '%s' % prd_test[ '#'] )

        title = prd_test[ 'parameters']

        if 'rated power value' in prd_test:
           title = '%s @ Prated=%sdBm' % (title, prd_test[ 'rated power value' ] )
#           print '(gen_graph_table_row)    rated power value @ = ', title
        g_row.append( title )

#        print ''
#        print g_row
#        print ''
#        for c in prd_test[ 'conditions']:
#        print '    ' , prd_test[ 'conditions']
#        print 'test_desc' , test_desc


#       print '\n(gen_graph_table_row) Test id# %s  conditions=' % prd_test[ '#']

        td_cond = test_desc[ 'filters' ]


        # Add the filters, from the test_desc
        for tc in td_cond:
            if not (len(tc) > 2 and tc[2] == 'measure'):


              # if the xaxis name is the same as the condition name, don't add it,
              # instead we will make it an at_val value for the measure command
              if test_desc['xynames'][0] == tc[0] :
#               print '(gen_graph_table_row) xaxis == cond name', prd_test[ '#'], test_desc['xynames'][0], cgtc
                try:
                   num = float( tc[2] )
                   at_val = num
                except Exception:
                   at_val = tc[2]

              else:
                 g_row.append( tc )

        # Add conditions from the PRD Conditions
        # also add any conditions from the PRD Parameters (ie if there is an @ ... )


        if 'conditions' in prd_test:
           cl = prd_test[ 'conditions'].split(';')
        else:
           cl = []

#        print '(gen_graph_table_row)  cl =', cl


# Removed the detection of conditions in the parameter column  (ma/ar 29jul10)
#
#        # Add conditions from any @ conditions in the Parameters
#        #    e.g.    PAE @ Pout = 33dBm
#        grps = re.search( r'@(.*)', prd_test[ 'parameters' ] )
#        if grps:
#            p  = grps.groups()[0].strip()
#            pl = p.split(';')
#            cl.extend( pl )
# 


        # Add a Freq(MHz) conditions if the parameter starts with '/d+ MHz'
        #    e.g.   880 MHz Max Pout (dBm)
        grps = re.search( r'^\s*(\d+)\s*MHz', prd_test[ 'parameters' ] )
        if grps:
            p  = grps.groups()[0].strip()
            cl.append( 'Freq=%s' % p )


        if self.xl_type == 'mktg_plots':
            grps = re.search( r'^\s*(\S+)\s*', prd_test[ 'parameters' ] )
            if grps:
                p  = grps.groups()[0].strip()
                for b in self.freq_sub_band_list:
                   if re.search('-',b[0]):
                       bnp = re.sub('^.*-','',b[0])
                       if bnp.index(p) == 0:                        
                          cl.append( 'sub-band=%s' % p )
                          break


        for c in cl:
           # set all the params as defined in the conditions
           #  (but only if theyt are not defined by the test_desc)


           if c == '': continue
           add_condition = True
           cgtc = self.gen_graph_table_condition( c, prd_test[ '#'] )  # the test number is only needed for debug

#           print '(gen_graph_table_row)            c=<%s>  %s ' % (c, cgtc)

           if cgtc == None:
               self.graph_table_row_debug( test_desc,prd_test,[] )
               print "*** ERROR *** (gen_graph_table_row) cannot make a condition (filter) from '%s'" % c
               sys.exit()

#           print '(gen_graph_table_row) \n   test_desc=%s\n   cgtc=%s' %  (test_desc, cgtc)

           # go through the full list of filters, and remove those that are not filters
#           add_condition = True
#           for tc in td_cond:
#              if tc[1] == 'measure' or len(tc) > 2 and tc[2] == 'measure': continue
#              if tc[0] == cgtc[0]:
#                  add_condition = False
#                  break

           # if the xaxis name is the same as the condition name, don't add it,
           # instead we will make it an at_val value for the measure command
           if test_desc['xynames'][0] == cgtc[0] :
              add_condition = False
#              print '(gen_graph_table_row) xaxis == cond name', prd_test[ '#'], test_desc['xynames'][0], cgtc
              try:
                 num = float( cgtc[2] )
                 at_val = num
              except Exception:
                 at_val = cgtc[2]

           if add_condition:
               g_row.append( cgtc )

#           print '                         %30s   %s' % (c.strip(), cgtc)



        self.graph_table_row_debug( test_desc,prd_test,g_row )




        # Add the measurements from the test_desc
        mnum = 1
        for tc in test_desc['measures']:
            
            if not isinstance( tc, types.ListType):
                print '(gen_graph_table_row) *** ERROR *** test_desc measure definition must be a list of lists', test_desc['measures']
                sys.exit()
                
            
            if len(tc) >= 2 :
               # look at the measure command.
               # if it is min or max limit exists in the prd add this
               # to the measure statement, but make sure the coresponding
               # measure statement has the same min or max command


               # First determine if the measurement needs to be done with at_val
               # If the





#                 td: [1,   'typical', 'measure', 'avg_at_xval']   - old list format
#                 td: ['typical','avg_at_xval']                    - new dict format
#                fct: [1,   'typical', 'measure', 'avg_at_xval', 33.0, 46.0]

#              ntc = [ tc[0], tc[1], tc[2], tc[3], at_val ]


               limval = None

               if len(tc) >= 3 and tc[2] != '':
                    at_val = tc[2]
               if len(tc) >= 4 and tc[3] != '':
                    limval = tc[3]

               ntc = [ mnum, tc[0], 'measure', tc[1],  at_val ]
            

               if re.search( r'(at_xval|at_xrange)', tc[1]) and ( at_val == '' or at_val == None ):
                   self.graph_table_row_debug( test_desc,prd_test,[] )
                   print "*** ERROR *** (gen_graph_table_row) for # %s '%s'."  % ( prd_test[ '#'], test_desc['parameter'] )
                   print "             Measurement %s requires an X axis value or range to measure."  % ( ntc )
                   print "             Expecting a PRD Condition (or filter) for '%s'"  % ( test_desc[ 'xynames' ][0] )
                   sys.exit()

               # if there is no limval in the test_desc then use the limit value from the prd
               # determine which min/typ/max test to do from the test_desc
               if limval == None:
                   if    re.search( r'min', tc[0], re.I) and prd_test['min']     != '':
                        limval = prd_test['min']
                   elif  re.search( r'max', tc[0], re.I) and prd_test['max']     != '':
                        limval = prd_test['max']
                   elif  re.search( r'typ', tc[0], re.I) and prd_test['typical'] != '':
                        limval = prd_test['typical']
                   elif  re.search( r'limit', tc[0], re.I) and prd_test['limit'] != '':
                        limval = prd_test['limit']


#               print '(gen_graph_table_row) adding MEASURE' , [ ntc, limval ]

               if limval != None and limval != '':

                  ntc.append( float(limval) )
                  g_row.append(ntc)


               mnum += 1


        # debug print statements

        self.graph_table_row_debug( test_desc,prd_test,g_row )


        return g_row

###################################################################
    def  graph_table_row_debug( self,test_desc,prd_test,g_row ):
            '''Prints the test_desc, prdtest, and graph_table_row (fct)

            Parameters:
                test_desc:    test description dict containg info on how to plot the graph, and how to make the measurements
                prd_test :    PRD parameter dict containing inof on the test limits and condtions
                g_row    :    Graph Table Row (same as fct)
            Returns:       None '''



            for key, val  in test_desc.iteritems():
                print '  td: %15s  %20s' % ( key,val )
            print ''
            for key, val in prd_test.iteritems():
                print ' prd: %15s  %20s' % ( key,val )
            print ''
            for fcti in g_row:
                print ' fct:' , fcti

            print '******************************************************************************'



###################################################################
    def  gen_graph_table_condition( self, prd_txt, test_id):
        '''  Takes the condition from the prd spec, and tries to convert it into
             a format suitable for the <cond_filter> of a graph_table_row
             This routine needs to be very flexible in identifying the different
             ways a condition can be set.   Special thing this function will do

             1) The prd_txt is only one condition from the conditions. It is
                 assumed that the conditions are seperated by a ';' character'
             2) The name of the parameter is translated into the normal name
                 used for the parameter in the ATR log files. This may be test
                 dependent (e.g. 'Vramp Voltage' or 'VAM') So 'fin' in the spec
                 would be translated into the name 'Freq(MHz)'
             3) The value is everything after the name. The condition may or
                 not contain '='. The value may be a single value or a range,
                 or a series of values.
                     'to' is used to denote a range
                     '-' is used to denote a range'
                     'up to' is used to denote a range with no 1st limit
                    ',' or ' ' is used to separate values into a list
                 The value units may or may not be specified after the value.
                 The value units are currently removed and ignored.

            Parameters:
               prd_txt :   The text string containing the condition, (this the condion after it has
                             been split into it's separate sub-condirions)
               test_id :   PRD test ID#, this is only used if an error was found in the condition.
                             To tell the user where in the PRD the error condition occurred.

            Returns:
               [ Name, 'F' Value ]  i.e. Graph Table Row format filter. Where:

               Name  :    Name of the condition as translated into its normal ATR column name (if recognized)
               Value :    A single value, a list of values, or a string containing 'num..num, '..num', or 'num..' '''

#        print '(gen_graph_table_condition)', prd_txt

        name = None
        val  = None

        if re.search( '=.*=', prd_txt ):
               print '***ERROR*** (gen_graph_table_condition) Syntax error in PRD conditions, two or more equal chars found (possible missing semicolon)'
               print '   PRD #', test_id, [ prd_txt ]
               sys.exit()

        prd_txt = prd_txt.strip()
        prd_txt = re.sub( '\s\s+', ' ', prd_txt)  # remove multiple space chars




        # look for any conditions which have two < or two > characters (or unicode <= / >= chars)
        if re.search( u'(<|>|\u2264|\u2265)', prd_txt):

            print '(gen_graph_table_condition) found gt lt chars', prd_txt
            #                  '  5db     <         Pout    <        30db '
            grps = re.search( u'(\S+) ?', prd_txt, re.I)
            grps = re.search( u'(\S+) ?(<|\u2264) ?(.*) ?(<|\u2264) ?(\S+)', prd_txt, re.I)

            if not grps:
                grps = re.search( u'(\S+) ?(>|\u2265) ?(\S+) ?(>|\u2265) ?(\S+)', prd_txt, re.I)


            if grps:
               name  = grps.groups()[2].strip()
               p1    = grps.groups()[0].strip()
               p2    = grps.groups()[4].strip()
               gtlt  = grps.groups()[1].strip()

               if re.search(u'(<|\u2264)', gtlt):

                  val1 = p1
                  val2 = p2
               else:
                  val1 = p2
                  val2 = p1

               val1   = re.sub( '[ a-zA-Z\.\,]+$', '', val1)  # remove any trailing units
               val2   = re.sub( '[ a-zA-Z\.\,]+$', '', val2)  # remove any trailing units
               val    = '%s..%s' % ( val1, val2 )

            if not grps:
                  grps = re.search( u'(\S+) ?(>|\u2265) ?(\S+)', prd_txt, re.I)
                  if grps:
                      name  = grps.groups()[0].strip()
                      val   = grps.groups()[1].strip()
                      val   = re.sub( '[ a-zA-Z\.\,]+$', '', val)  # remove any trailing units
                      val   = '%s..' % val

            if not grps:
                  grps = re.search( u'(\S+) ?(<|\u2264) ?(\S+)', prd_txt, re.I)
                  if grps:
                      name  = grps.groups()[0].strip()
                      val   = grps.groups()[1].strip()
                      val   = re.sub( '[ a-zA-Z\.\,]+$', '', val)  # remove any trailing units
                      val   = '..%s' % val


 #              print '(gen_graph_table_condition) found gtlt condition,  %s = %s' % ( name, val )




        # look for an '=' char to separate the name and the value
        if re.search('=',prd_txt):
            pl = prd_txt.split('=')
            name = pl[0].strip()
            val  = pl[1].strip()


        if name == None or val == None:

            # or else look for a space to separate the name and the value
            grps = re.search(r'(\S+)\s+(.+)', prd_txt)
            if grps and len(grps.groups())==2:
               name  = grps.groups()[0].strip()
               val   = grps.groups()[1].strip()

        if name == None or val == None:
               print '***ERROR*** (gen_graph_table_condition) Syntax error in PRD conditions. Either the condition name or value are incorrectly defined'
               print '   PRD #', test_id, [ prd_txt ]
               return None





        # change the param name to the name used in our log files
        # (warning this may be dependent on the test run)
        if    re.search( r'^(Freq|fin)',name,re.I):      name = 'Freq(MHz)'
        elif  re.search( r'^vbat',name,re.I):            name = 'Vbat(Volt)'
        elif  re.search( r'^(H|L)B_?IN',name,re.I):      name = 'Pwr In(dBm)'
        elif  re.search( r'^pin',name,re.I):             name = 'Pwr In(dBm)'
        elif  re.search( r'temp',name,re.I):             name = 'Temp(C)'
        elif  re.search( r'temp',name,re.I):             name = 'Temp(C)'
        elif  re.search( r'vramp',name,re.I):            name = 'Vramp Voltage'
        elif  re.search( r'^pout$',name,re.I):           name = 'Pout(dBm)'
        elif  re.search( r'^p$',name,re.I):              name = 'Pout(dBm)'
        elif  re.search( r'ref\s*pout',name,re.I):       name = 'Ref Pout(dBm)'
        elif  re.search( r'ref2\s*pout',name,re.I):       name = 'Ref2 Pout(dBm)'

        # Now we have a value which may be any one of the following formats
        #    vbat = 3v
        #    vbat = 2.7v to 4.5v
        #    vbat = 2.7v  - 4.5v
        #    vbat = 2.7v , 3.5v , 4.5v
        #    vbat = 2.7v min.
        #    vbat = 4.5v max.
        #    vbat = up to 4.5v
        #    vbat = down to 2.7v


        # Now look at the val and translate it to the correct graph_table row format

        # look for a '-', or 'to' used to define a range

#        print '(gen_graph_table_condition)  ', name, val


        if re.search(r',', val) : commas = True
        else:                     commas = False

        grps = None










        # look for 'min' or 'max''
        if not grps and commas == False:
            grps = re.search( '(\S+)\s*(min|max)\.?', val, re.I)

            if grps:
              val   = grps.groups()[0].strip()
              val  = re.sub( '[ a-zA-Z\.\,]+$', '', val)  # remove any trailing units

              minmax = grps.groups()[1].strip().lower()
              if minmax == 'min':
                val   = '%s..' % val
              if minmax == 'max':
                val   = '..%s' % val

        if not grps and commas == False:
           grps = re.search( '(\S+)-(\S+)', val)
        if not grps:
           grps = re.search( '(\S+) to (\S+)', val, re.I)


        if grps and len(grps.groups())==2 and commas == False:
            val1   = grps.groups()[0].strip()
            val2   = grps.groups()[1].strip()

            val1   = re.sub( '[ a-zA-Z\.\,]+$', '', val1)  # remove any trailing units
            val2   = re.sub( '[ a-zA-Z\.\,]+$', '', val2)  # remove any trailing units
            val    = '%s..%s' % ( val1, val2 )





        # look for 'up to'
        if not grps and commas == False:
            grps = re.search( '(up) ?to (\S+)', val, re.I)
            if not grps:
                grps = re.search( u'(<|\u2264) ?(\S+)', val, re.I)

            if grps:
              val   = grps.groups()[1].strip()
              val  = re.sub( '[ a-zA-Z\.\,]+$', '', val)  # remove any trailing units
              val   = '..%s' % val

        # look for 'down to'
        if not grps and commas == False:
            grps = re.search( '(down) ?to (\S+)', val, re.I)
            if not grps:
                grps = re.search( u'(>|\u2265) ?(\S+)', val, re.I)

            if grps:
              val   = grps.groups()[1].strip()
              val  = re.sub( '[ a-zA-Z\.\,]+$', '', val)  # remove any trailing units
              val   = '%s..' % val



        # if we get to this point and grps is None then we have a simple value
        if not grps:
              val  = re.sub( '[ a-zA-Z\.\,]+$', '', val)  # remove any trailing units

              if name == 'VSWR':
                  val  = re.sub( ':.*', '', val)  # remove any trailing N:1


        # look for ',' or multiple values in val used to define a list

        val_l = val.split(',')
        if len(val_l) <= 1:  val_l = val.split()

        if len(val_l) >= 2:
#          print '(gen_graph_table_condition) found comma split values'
           val = []
           for v in val_l:


              vs = re.sub( r'[ a-zA-Z\.\,]+$', '', v  ).strip()

              # look for any embedded spaces.
              if re.search( r'\S\s+\S', vs):

                   print '*** ERROR *** (gen_graph_table_condition) illegal space in the middle of a PRD Condition value', [val]
                   print '   PRD #', test_id, [ prd_txt ]
                   return None



              if vs != '':
                try:
                  vs = float( vs )
                except Exception: pass

                val.append( vs )



        try:
          val = float( val )
        except Exception : pass

 #       print '(gen_graph_table_condition) got ', [ name,  'F', val ]


        return [ name,  'F', val ]

###################################################################




###################################################################
###################################################################
###### Measurement functions
###################################################################



    def maxy2x( self, x, y, limits=None):
       ''' Finds the x value where y is a max
           warning only works if y is an increasing quantity!!!'''
       maxval =  self.maxyval( x, y, limits)
       return self.measure_value( xyd, 'x_at_yval', maxval )

    def miny2x( self, x, y):
       ''' Finds the x value where y is a min
           warning only works if y is an increasing quantity!!!'''
       minval =  self.minyval( x, y, limits)
       return self.measure_value( xyd, 'x_at_yval', minval )

    def maxyval( self, x, y, limits=None):
       if limits == None: meas_type = 'ymax'
       else:              meas_type = 'ymax_limits'
       return self.measure_value( xy, meas_type, limits ) - 1e-12

    def minyval( self, x, y, limits=None):
       if limits == None: meas_type = 'ymin'
       else:              meas_type = 'ymin_limits'
       return self.measure_value( xyd, meas_type, limits ) + 1e-12



    def y2x( self, x, y, yval):
       return self.measure_value( xyd, 'x_at_yval', yval )

    def x2y( self, x, y, t):
       return self.measure_value( xyd, 'y_at_xval', t )


###################################################################
    def meas_minmax_ix( self, lst1, minmax):
       '''Finds the index which has the min or max value in the list

       Parameters:
           lst1   :  list of values
           minmax :  'max' or 'min', if 'max' will find the index pointing to the maximum value, else it will
                      find the index pointing to the minimum value
       Returns:
           ixm    :  index pointing to the min or max value if found. If not found returns None'''


       ix  = 0
       ixm = None
       l1m = None
       for l1 in lst1:

           if l1 != None :

               if ixm == None:
                  ixm = ix
                  l1m = l1


               if minmax == 'max':
                  if l1 >= l1m:
                      l1m = l1
                      ixm = ix
               else :
                  if l1 <= l1m:
                      l1m = l1
                      ixm = ix
#          print '(meas_minmax_ix)  minmax=%s   ix=%s  l1=%s   l1m=%s   ixm=%s' % (minmax, ix, l1, l1m, ixm )
           ix += 1

       return  ixm





###################################################################

    def measure_value( self, xyd, measure_type, at_value=None, limit=None ):
       ''' Makes a measurement on the x and y data previously plotted on the graph (using self.plot_graph_data)

       The xyd data is a list of lists of the form  [  [ x-lists ], [ y-lists ],  [rn_lists], .. ]
       Multiple lists of x and y data will occur if there are multiple lines on the graph.

       The multiple lists will be split into separate line lists and this function will be called
       separately for each line.

       Parameters:
          xyd             :          x and y data, List of x values, y values and d values (from self.plot_graph_data)
          measure_type    : type of measurement to make (see list directly below for all accepted values)
          at_value = None : For measurment_type *_at_xval at_value is a single x value where the measurment will be made,
                         if measurement_type is *_at_xrange at_value must be a 2 element list of
                         x values between which the measurement will be made.
                         For all other measurement_types the at_value should = None
          limit = None    : Measurment Limit, this limit is used when counting the failed part count

       Returns:   [ val [min, avg, max], [ x, y, sn, c, d ], [ #fails, #parts] ]'''


       if measure_type not in [ 'xmin',     'ymin',     'xmax',      'ymax',
                                'x_at_yval',            'y_at_xval' ,
                                'xmin_at_yval',         'ymin_at_xval',       'xmax_at_yval', 'ymax_at_xval',
                                'ymin_at_xrange',       'ymax_at_xrange',
                                'min_ymin_at_xrange' ,  'max_ymax_at_xrange', 'yavg_at_xrange',
                                'max_ymin_at_xrange' ,  'min_ymax_at_xrange', 'avg_ymax_at_xrange',
                                'min_ymin', 'max_ymax',
                                'min_ymax', 'max_ymin', 'yaverage', 'avg_ymax', 'avg_ymin', 'avg_at_xval' ]:

          print "*** ERROR *** (measure_value) incorrect measure_type: '%s'"% measure_type

#       print '(measure_value) ENTRY ', [ measure_type,  at_value, limit ]


       val = None



       if xyd == None or len( xyd[0] ) == 0 :
#          print '(measure_value) xyd==none or len(xyd[0])==0   returning val ', val
          return val


       x   = xyd[0]
       y   = xyd[1]
       rnl = xyd[2]
       snl = xyd[3]
       cl  = xyd[4]
       dl  = xyd[5]

       fail_count = 0



       # # # # # # # # # # # # # # # # # # # # # # # # #
       # Expannd series
       # If there is multiple series of data, seperate the data into separate lines.
       # loop through all the lines, and measure_value on each line
       # also if there are multiple at_value's we need to loop through these as well.
       #
       if len(x) > 1    or    (type(at_value) == types.ListType and len( at_value ) > 1 and re.search( r'at_xval', measure_type )):

          # if its an at_xval measurement then the at_xval may be a list or a single value,
          # if its single value pop it into list so that we can process it with a list loop
          # also loop through all the at_value's if its a list.


          # if the measurement_type is _xrange we want to put the the two xrange values into another list
          at_val = at_value
          if type( at_value ) == types.ListType:
              if re.search( r'xrange', measure_type ):
                 at_val = [at_value]
              elif not re.search( r'at_xval', measure_type ):
                 at_val = [ '' ]
          else:
              at_val = [at_value]

          self.part_list = {}
          self.failed_part_list = {}


          vl = []
          for av in at_val:

                  try:
                     av = float( av )
                  except Exception:
                     pass


                  for  i in range(len(x)):


#                    print '(measure_value) series '
#                    for  xtt in x[i]:
#                        print '%06.3f' % xtt,
#                    print ''
#                    for  ytt in y[i]:
#                        print '%06.3f' % ytt,
#                    print ''


                    if len(x) > 1:
                       xydi = [ [x[i]], [y[i]], [rnl[i]], [snl[i]], [cl[i]], [dl[i]] ]
                    else:
                       xydi = [ x, y, rnl, snl, cl, dl ]
        #            print '(measure_value) SERIES    params', i,  measure_type, at_value, limit
                    v = self.measure_value( xydi, measure_type, av, limit )
        #            print '(measure_value) SERIES    val=', i, v, '\n'
                    vl.append( v )



          # # # # # # # # # # # # # # # # # # # # # # # #
          #  find the maximum of all the measurements
          vmix = None

          for ix in range(len(vl)):
              v = vl[ix]
              if vmix == None and v != None and v[0] != None: vmix = ix
              if v == NaN or v == None or vmix == None: continue
              if v[0] > vl[vmix][0]: vmix = ix

          vmax_ix = vmix
          if vmix != None and vl[vmix] != None:
              vmax = vl[vmix][0]
          else:                vmax    = None


          # # # # # # # # # # # # # # # # # # # # # # # #
          #  find the minimum of all the measurements
          vmix = None
          for ix in range(len(vl)):
              v = vl[ix]
              if vmix == None and v != None and v[0] != None: vmix = ix
              if v == NaN or v == None or vmix == None : continue

              if v[0] < vl[vmix][0]: vmix = ix

          vmin_ix = vmix
          if vmix != None and vl[vmix] != None:
              vmin = vl[vmix][0]
          else:                vmin    = None



          # # # # # # # # # # # # # # # # # # # # # # # #
          #  find the average of all the measurements
          vsum = 0
          vavg = None
          ix = 0
          for v in vl:

              if v == NaN or v == None or v[0] == None : continue
              vsum += v[0]
              ix += 1
#              print '(mesure_value)  ix=%s      v[0]=%s     vsum=%s' % (ix, v[0], vsum )

          if ix != 0:
             vavg = vsum/ix






          if re.match( r'^(x|y)?max', measure_type):
            if  vmax_ix == None or vl[vmax_ix] == None :
               print '(measure_value) series vl[vmax_ix] == None   returning none '
               return None
            val = vl[vmax_ix][0]
            vix = vmax_ix
          elif re.match( r'^(x|y)?min', measure_type):
            if  vmin_ix == None or  vl[vmin_ix] == None :
               print '(measure_value) series vl[vmin_ix] == None   returning none '
               return None
            val = vl[vmin_ix][0]
            vix = vmin_ix
          else:
            val = vavg
            vix = None

          if vix != None:
              vll = vl[vix][2]
          else:
              vll = []

          return  [ val, [vmin,vavg,vmax], vll, [-1,1] ]

       # end of series expansion block
       ###############################################################################################



       x = x[0]
       y = y[0]
       sn = snl[0]
       rnl = rnl[0]
       c  = cl[0]
       d  = dl[0]
       rn = None


       yv = None
       xv = None

       val_min = None
       val_avg = None
       val_max = None

       # check to see if we have multiple sets of data points (ie many lines)
       # if so the we will split them up into sub series and perform the measure on each seperately.

       measure_type_orig = measure_type

       if measure_type == 'ymax_at_xval' or \
          measure_type == 'ymin_at_xval' or \
          measure_type == 'avg_at_xval'  or \
          measure_type == 'yavg_at_xval'                                  : measure_type = 'y_at_xval'

       if measure_type == 'xmax_at_yval' or measure_type == 'xmin_at_yval': measure_type = 'x_at_yval'
       if measure_type == 'min_ymax'                                      : measure_type = 'ymax'
       if measure_type == 'max_ymin'                                      : measure_type = 'ymin'
       if measure_type == 'avg_ymax'                                      : measure_type = 'ymax'
       if measure_type == 'avg_ymin'                                      : measure_type = 'ymin'
       if measure_type == 'max_ymax'                                      : measure_type = 'ymax'
       if measure_type == 'min_ymin'                                      : measure_type = 'ymin'

       if re.search( '_(ymax|ymin|yavg)_at_xrange', measure_type)   : measure_type = re.sub( r'^(min|max|avg)_', '', measure_type)


       # define the quantities we are going to return

       idx = None  #    index for the measurement value
       val = None  #    measurement value
       yv  = None  #    y value for the measurement  (usually = val if its a y measurement)
       xv  = None  #    y value for the measurement  (usually = val if its a y measurement)
       idxmax = None #  maximum y value
       idxmin = None #  minimum y value
       yv_avg = None #  avg y value





# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
       if measure_type == 'y_at_xval':
#          print '(measure_value) single max(x) at_value  min(x)' , [max(x) , at_value, min(x)]

          val = None
          idx = None

          if at_value == None or at_value == '':
#             print '*** ERROR *** (measure_value) at_value is None, this needs to be a value or list for measure_type=', measure_type
             pass
          else:

              # need two or more data points in the data list to do an interpolation -- changing to one point as we
              # we want to bable to do a single point measurement
              if len(x) >=1 and len(y) >=1 :
                  at_value = float( at_value )
                  if min(x) <= at_value <= max(x) :
    #               [val] = interp([at_value], x, y)

#                    print '(measure_value) single doing loop', len(x), len(y)
                    # loop through all the y values and look for the point where the y value crosses the at_value
                    # then do proportional
                    val = None
                    yv  = None
                    xv  = None
                    idx = None


                    for i in range( len(x) ):
                      i2 = i+1
                      if i2 >= len(x) : i2 = i
                      x1 = x[i]
                      x2 = x[i2]
                      y1 = y[i]
                      y2 = y[i2]

#                      print '(measure_value)      x1= %10s  x2= %10s  y1= %10s  y2= %10s' % ( x1,x2,y1,y2)

                      if x1 == None or x2 == None or y1 == None or y2 == None: continue  # can't do anything if any of the 4 values are none

                      # if the at_value is between the two x1/x2 points or on the last point the at_value == the x1 point
                      if ( (x1 <= at_value < x2)  or  (x1 == at_value and i2==i) ) or \
                         ( (x1 >= at_value > x2)  or  (x1 == at_value and i2==i) ) :


                          # interpolate the value
                          if x2 != x1:
                            val =   (at_value-x1) * (y2-y1)/(x2-x1)  + y1
                          else:
                            val = (y1+y2)/2.0

                          # get the closes index
                          if abs( x1 - at_value ) < abs( x2 - at_value ):
                            idx = i
                          else:
                            idx = i2


                          break

# These elif's catch the case when the xval is outside the min and max values of the x data
# We will try to extroploate this and get a value. <<<<<<  Decided not to do this and return a None value
                  elif 0 and at_value < min(x) :
                        if 0:
                            x1 = x[0]
                            x2 = x[1]
                            y1 = y[0]
                            y2 = y[2]
                            val =   (at_value-x1) * (y2-y1)/(x2-x1)  + y1
                            idx = 0

                  elif 0 and at_value > max(x):
                        if 0:
                            x1 = x[-2]
                            x2 = x[-1]
                            y1 = y[-2]
                            y2 = y[-1]
                            val =   (at_value-x1) * (y2-y1)/(x2-x1)  + y1
                            idx = -1


          # # # # # # # # # # # # # # # # #
          #  get the min max avg values

          if idx != None:
            yv =   y[ idx ]
            xv =   x[ idx ]
            rn = rnl[ idx ]

          val_max = val
          val_min = val
          val_avg = val

#          print '(measure_value) at_xval , idx=%s, y[idx]=%s, x[idx]=%s' % ( idx, yv, xv )

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
       ## TODO update as above  'y_at_xval'
       if measure_type == 'x_at_yval':
          val = None
          idx = None
          at_value = float(at_value)
          if min(y) <= at_value and at_value <= max(y) :
            # warning this interp function assumes that the first dependent varaible is an increasing quantity!!!
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
                  if y2 != y1:
                    val =  x1+ (  (x2-x1) * (at_value-y1) / (y2-y1) )
                  else:
                    val = (x1+x2)/2.0

                  idx = i
                  break

            # # # # # # # # # # # # # # # # #
            #  get the min max avg values

            if idx != None:
               yv =   y[ idx ]
               xv =   x[ idx ]
               rn = rnl[ idx ]
            val_max = val
            val_min = val
            val_avg = val



# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
       elif measure_type in ['ymax', 'ymin'] :
          idxmax = self.meas_minmax_ix(y,'max')
          idxmin = self.meas_minmax_ix(y,'min')
          if measure_type == 'ymax' : idx = idxmax
          else:                       idx = idxmin


          # # # # # # # # # # # # # # # # #
          #  get the min max avg values
          yv =   y[ idx ]
          xv =   x[ idx ]
          rn = rnl[ idx ]
          val_max = y[ idxmax ]
          val_min = y[ idxmin ]

          val_avg = (val_max + val_min) / 2.0

          val = yv


# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
       elif measure_type in ['xmax', 'xmin'] :
          idxmax = self.meas_minmax_ix(x,'max')
          idxmin = self.meas_minmax_ix(x,'min')
          if measure_type == 'xmax' : idx = idxmax
          else:                       idx = idxmin


          # # # # # # # # # # # # # # # # #
          #  get the min max avg values
          yv =   y[ idx ]
          xv =   x[ idx ]
          rn = rnl[ idx ]
          val_max = y[ idxmax ]
          val_min = y[ idxmin ]
          val_avg = (val_max + val_min) / 2.0

          val = xv



# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
       elif measure_type == 'ymax_at_xrange' or measure_type == 'ymin_at_xrange' or measure_type == 'yavg_at_xrange':
       # get the max y value for xvalues between at_value[0] and at_value[1]

          if isinstance( at_value, types.StringTypes ) and re.search(r'\.\.', at_value):
               r1,r2 = self.get_filter_value_range( at_value )
               at_value = [r1,r2]

          if at_value == None or at_value == '':
             print '*** ERROR *** (measure_value) at_value is None, this needs to be a range for measure_type=', measure_type


          # first calculate the yvalues at the x at_value's
          vv = self.measure_value( xyd, 'y_at_xval', at_value[0], limit )
          if vv == None or vv == NaN :
              y0 = None
          else:
              y0 = vv[0]

          vv = self.measure_value( xyd, 'y_at_xval', at_value[1], limit )
          if vv == None or vv == NaN :
              y1 = None
          else:
              y1 = vv[0]

#          print '    (measure_value) [y0,y1] =', [y0,y1]
          if y0 == None and y1 == None :
               return None

          #then clip the x and y lists so they contain only data points within the at_value limits
          idx = None
          xt = [ at_value[0] ]
          yt = [ y0 ]
          rt = [ None ]

          for i, xi in enumerate(x):

             if xi < at_value[0] : continue
             if xi >= at_value[1]: continue
             xt.append( xi )
             yt.append( y[i] )
             if rt[ 0 ] == None :  rt[ 0 ] = rnl[i]
             rt.append( rnl[i] )

          xt.append( at_value[1] )
          yt.append( y1 )
          rt.append(  rnl[i-1] )



          # # # # # # # # # # # # # # # # #
          #  get the min max avg values

          idxt = None
          idxmax = self.meas_minmax_ix(yt,'max')
          if idxmax != None:
              val_max = yt[ idxmax ]
          idxmin = self.meas_minmax_ix(yt,'min')
          if idxmin != None:
              val_min = yt[ idxmin ]
          if idxmin != None and idxmax != None:
             val_avg = (val_max + val_min) / 2.0

          if    measure_type == 'ymax_at_xrange':
              idxt = idxmax

          elif  measure_type == 'ymin_at_xrange':
              idxt = idxmin



          if idxmin != None and idxmax != None and idxt != None:
              yv  = yt[ idxt ]
              xv  = xt[ idxt ]
              rn  = rt[ idxt ]
              val = yv

          if  measure_type == 'yavg_at_xrange':
              yv  = val_avg
              val = yv

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
       elif measure_type == 'yaverage' :

          sum = 0
          for yt in y:
             sum += yt

          if len(y) > 0:
            yv = sum/len(y)
            val = yv


# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
       elif measure_type == 'xaverage' :

          sum = 0
          for xt in x:
             sum += xt

          if len(x) > 0:
            xv = sum/len(x)
            val = xv


# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .




       fail_count = 0
       if measure_type_orig[1:4] == 'max' and val > limit : fail_count = 1
       if measure_type_orig[1:4] == 'min' and val < limit : fail_count = 1




       if val == None :
#          print '(measure_value) single series val==None   returning none '
          return val


       if rn != None:
           serial_num = self.data[ 'Serial Number' ][ rn ]
           if serial_num != '':
              if serial_num not in self.part_list:
                   self.part_list[ serial_num ] = 1
              else:
                   self.part_list[ serial_num ] += 1

              if fail_count > 0 :

                if serial_num not in self.failed_part_list:
                   self.failed_part_list[ serial_num ] = 1
                else:
                   self.failed_part_list[ serial_num ] += 1



#       print '(measure_value) single series return values',  measure_type, [ val, [  val_min, val_avg, val_max  ], [xv, yv, rn, sn, c, d,]], measure_type, measure_type[1:4], limit, fail_count

#              [ val [min avg max], [ x, y, sn, c, d ], [ #fails, #parts] ]

       return [ val, [ val_min, val_avg, val_max ], [xv, yv, rn, sn, c, d,], [ fail_count , 1 ] ]


########################################################################################################
    def measure_plot_data( self, xyd, fct, limval, oplog=None, prd_test=None, wb=None, subdir=None ):
       ''' Measures data plotted on the graph. It uses the data in the xyd list (which is created by plot_graph_data)
           to look make a measurement. The measurements made are listed in the graph table row definition (fct)
           It looks for an list item that matches:

             ['measure','2','ymin_at_xval','Pnmed','Nmed']
             [ measure',<id#>,<measure_type>, <at_val>, <limit_value> ]

           Each separate measurment will be made for each 'measure' found in the fct.
           The measurment is made by the self.measure_value function.
           The result of the measurement is written to oplog file (if present)
           and to the excel output workbook wb (if present). It will  also write a link to 'subdir' in the excel file.

            Where :
               <measeure_type>     is one of  ymin, ymax, ymin_at_xval, ymax_at_xval, ??????
               <at_val>            is where on the x axis the measurement  measured, it is a limval name, or an actual value, or list of two values representing a range.
               <limit_value>       is the limit value that will be drawn on the graph

            Parameters:
                 xyd:    x and y data, List of x values, y values and d values  (x,y,d)
                 fct:    graph table row with containing the measurement commands
                 limval: limit value dictionary, dictionary of limit values.
                 oplog    = None : File handle for writing the measurement results
                 prd_test = None : prd dictionary, dictionary of prd cell data for reading the data from the prd
                 wb:      = None : prd output workbook handle, for writing prd measurement results
                 subdir   = None : Writes the subdir into the 'Unit' column of the excel output

            Returns:   Measurement value string.  Of the format "Value ( min , typ, max )  pass/FAIL (1/6)"

       '''

       self.part_list = {}
       self.failed_part_list = {}


       ret_val = None

       band = self.get_filter_conditions( 'Sub-band' )
       if type( band ) != types.StringType:  band = ''


#       self.spec_limits = []

       #          id# col   keyword  measurement_type   xval(at_val)   ylimit(limname)
       #   ....  [2,       'measure', 'ymin_at_xval',   'vramp_max',     'Pout.n']],

       #  or     [3, 'typ', 'measure', 'ymin_at_xval',  'vramp_max', 'Pout.n'']
       for p in fct:

         if type( p ) == types.ListType:

           idnum = ''
           if p[1] == 'measure':

              idnum     = str( p[0] )
              mtype      = p[2]
              if len(p) > 3:          at_val     = p[3]
              else:                   at_val     = None
              if len(p) > 4:          limname    = p[4]
              else:                   limname    = None
              td_prd_col_name                    = None


           elif len(p) > 2 and p[2] == 'measure':


              idnum     = str( p[0] )
              mtype      = p[3]
              if len(p) > 4:          at_val     = p[4]
              else:                   at_val     = None
              if len(p) > 5:          limname    = p[5]
              else:                   limname    = None
              td_prd_col_name                    = p[1]


           if idnum != '':

              if at_val == '' : at_val = None


              if isinstance(limname,types.StringTypes):
                  if type( limval[ limname ] ) == types.ListType:
                    if band[:2] == 'LB' : y = limval[ limname ][0]
                    else:                 y = limval[ limname ][1]
                  else:
                     y = limval[ limname ]
              else:
                  y = limname

              if isinstance(at_val,types.StringTypes):
                  if at_val != None   and at_val  != '':
                      if at_val in limval:
                          if type( limval[ at_val ] ) == types.ListType:
                            if band[:2] == 'LB' : x =  limval[ at_val ][0]
                            else:                 x =  limval[ at_val ][1]
                          else:
                            x = limval[ at_val ]
                      else:
                            x = at_val
              else:

                 if type( at_val ) == types.ListType:
                   x = at_val
                 else:
                   x = at_val


              tstr = '\n   Measure = %s;   At X = %s;    Limit = %s' % ( mtype, x , y )
              self.selected_filter_conditions_str  = '%s\n%s' % ( self.selected_filter_conditions_str, tstr)

              # Do the actual measuring here using the x y data from the graph plot
              val = self.measure_value( xyd, mtype , x , y)

              tstr = '   Result =       %s\n' % (val)
              self.selected_filter_conditions_str  = '%s\n%s' % ( self.selected_filter_conditions_str, tstr)



              style = 'nomeas'

              if (type(val) == types.ListType or type(val) == types.TupleType) and val[0] != None :


                  # only compare against a limit if we have a valid limit
                  if y != None:
                      pf    = 'pass'
                      style = 'pass'
                      if ((mtype[:4] == 'ymax' or mtype[:3] == 'max')   and val[0]>y ) or  \
                         ((mtype[:4] == 'ymin' or mtype[:3] == 'min' )  and val[0]<y ) :
                           pf = 'FAIL'
                           style = 'fail'

#                      print '(measure_plot_data) 1 td_prd_col_name=%s mtype=%s typical_fail=%s pf=%s' % (td_prd_col_name, mtype, typical_fail,pf)

                      if prd_test != None and wb != None and  re.search('typical', td_prd_col_name) and prd_test['typical'] :
                            pf = ''
                            # for typical tests we just look to see if the magnitude of the number is less than the limit.
                            # in all cases I've seen this is good enough to determin pass/fail!
                            if abs( val[0] ) > abs( y ):    # OK I know this is lame, but its the best I can do!
                                style = 'typical'
                            else:
                                style = 'typical_fail'





                      # indicate whether the result includes measurements made over the full range of filter conditions.
                      full_condition_selected_str = xyd[6]
                      pf = pf + full_condition_selected_str

                      margin = abs( val[0]-y )

                      if pf != '':
                         fail_stat =  '%s/%s'  % ( len( self.failed_part_list ) , len( self.part_list ) )
                      else:
                         fail_stat =  '%s'     % (                                len( self.part_list ) )

                      pf = '%s mgn:%0.3f (%s)'  % ( pf, margin, fail_stat )

                  else:
                      pf = '(%s)'  % ( len( self.part_list ) )

                  if  val[1][0] == None or  val[1][1] == None or   val[1][2] == None :
                     minmax_str = ''
                  else:
                     minmax_str = '%0.3f,%0.3f,%0.3f' % ( val[1][0], val[1][1], val[1][2] )

### FINISH THIS !!!!!!!!!!!!!!!!!!!!!!!!!!!!!

#              # if we are measuring a spur test and we don't get any value then that's a good result!
#             elif measure_test == spur and ( val[0] == None or  val[3][0] == 0) :
#                  pf = 'NO SPUR'

              else:

                  x = val
                  val =[]
                  val.append(x)
                  pf = 'NO_DATA'
                  minmax_str = ''
                  style = 'nomeas'






#             print  "(measure_plot_data) ", p, mtype, x, y

              # write out the results, to the console, to the log file, (and to the PRD
              # file if present)
              tstr = '%3s.%-2s %-10s %-18s %12s Limit %8s = %-6s  Meas = %-12s (%20s)  %s' % ( fct[0], idnum, band, "'%s'" % fct[1], mtype, "'%s'" % limname , y, val[0], minmax_str, pf)

              print  "\n(measure_plot_data) ", tstr
              if oplog : print >> oplog ,   tstr



              if isinstance( val[0], types.FloatType):
                 ret_val = "%0.3f (%s) %s" % ( val[0], minmax_str, pf)
              else:
                 ret_val = "%s (%s) %s" %    ( val[0], minmax_str, pf)


              # Update the excel PRD
              if prd_test != None and wb != None:

                 graph_link = self.png_relfilename
#                 print [self.savedir ,self.png_filename]
#                 graph_link = re.sub( self.savedir , '', self.png_filename)  # remove the savedir from the plotfile fullpathname to make it a relative path!




                 # Get the column where we will place the results
                 # min/typical/max results column
                 col = None
                 if   re.search('max' ,    td_prd_col_name, re.I) and prd_test['max'] != '':
                      col = prd_test['result_col_max']
                 elif re.search('min',     td_prd_col_name, re.I) and prd_test['min'] != '':
                      col = prd_test['result_col_min']
                 elif re.search('typical', td_prd_col_name, re.I) and prd_test['typical'] != '':
                      col = prd_test['result_col_typ']
                 elif re.search('limit', td_prd_col_name, re.I) and prd_test['limit'] != '':
                      col = prd_test['result_col_data']
                 else:
                      print "***ERROR*** (measure_plot_data) #id=%s 'measure' statement prd_column_name does not match the column name in prd" % prd_test[ '#']
                      print '   test_desc= ', p
                      for pi in prd_test:
                        print  '   prd_test %10s = %s' % ( pi, prd_test[ pi ] )

                 if col != None:    write_to_excel = True
                 else:              write_to_excel = False


                 # Write the reulst out to the spreadsheet
                 #
                 # But before we start writing to the spreadsheet check to see if there is a value already from a previous ARGPRD run
                 # If there is we need to decide whether to clobber the previous value
                 # We will clobber it if the previous value is a 'NO_DATA' value or is empty

                 idx = '%s %s %s' % (prd_test['sheet_num'], prd_test['row'], col  )
                 if idx in self.xl_previous_values:
                    previous_value = self.xl_previous_values[ idx ]
                    if not re.search(r'NO_DATA', previous_value) and not re.search(r'NO_DATA', ret_val):
                       # there was data in the previous_value, if the current value has data concat the two and write a warning (if they are different)
                           if  previous_value.strip() !=  ret_val.strip():  # if the two results were different
                             print '(measure_plot_data) Warning. There was valid data from a previous ARGPRD run, results will concatenated\n   previous  %s\n   current  %s' % (previous_value, ret_val)
                             if len( ret_val) + len(previous_value) < 250:  # dont let this string get too long else it can't be printed by xlwt
                                ret_val = '%s ; %s' % (ret_val, previous_value)


                    # If the measurement is empty 'NO_DATA'  but the previous run there was valid data then
                    # we should not overwrite the previous data, therefore do not write and leave the previous data in tact.
                    if not re.search(r'NO_DATA', previous_value) and re.search(r'NO_DATA', ret_val):
                          write_to_excel = False


                 if write_to_excel:
                     # Write out the measurement result using and excel formula which also contains
                     # a hyperlink to the plt graph file

                     tstr = ret_val
                     tstyle = style
                     if 'pass/fail' in prd_test:
                         tstr = ret_val.split()[0]
                         tstyle = 'blank'

                     self.add_excel_results( wb, prd_test['sheet_num'], prd_test['row'], col , tstr, tstyle, graph_link )

                     # Also write out an excel formula which contains a hyperlink to the subdir in the UNIT column
                     if 'unit_col' in prd_test:
                         graph_link =  subdir[2]
                         col = prd_test['unit_col']
                         self.add_excel_results( wb, prd_test['sheet_num'], prd_test['row'], col , prd_test['unit'] , 'blank', graph_link )

                     # Also write out the pass/fail status for the perf_log xls files
                     if 'pass/fail' in prd_test:
                         graph_link =  subdir[2]
                         col = prd_test['result_col_passfail']
                         self.add_excel_results( wb, prd_test['sheet_num'], prd_test['row'], col , pf.split()[0] , style, '' )


       # Write out helpful info in the Comments column
       if prd_test != None and wb != None:
           col = prd_test[ 'comments_col' ]

           # write out the filter conditions (an explantation of the asterisks)
           tstr = self.selected_filter_conditions_str
           self.add_excel_results( wb, prd_test['sheet_num'], prd_test['row'], col , tstr , '', '' )

           # write out the logfile columns, and other status info
           tstr = self.print_values_list_str
           self.add_excel_results( wb, prd_test['sheet_num'], 0, col , tstr , '', '' )

       return ret_val




###################################################################
##### Load data functions
###################################################################

    def load_logfile( self, logfilename=None, csvlogfile=None, vmux_names_file=None, temperature=None ):
      '''Loads a Log file into pygram.  All data read from the file is loaded into internal dict self.data[]
      Clears all previously loaded Logfile data, and runs self.add_logfile

      Parameters:
         logfilename = None    :  Name of filename containing ATR style log data
         cvslogfile  = None    :  Name of filename containing csv style data (including vmux analog files)
         vmux_name_file = None :  (obsolete) Name of lookup table for vmux signal names and vmux address mux.
         temperature = None    :  If data does not contain any temperature data, set the temperature data to this value (normally 25C)

      Returns   :   None'''

      self.wclearfiles()
      self.add_logfile( logfilename, csvlogfile, vmux_names_file, temperature )



###################################################################


    def add_vmux_csvfile( self, vmux_results_filename, vmux_names_filename=None):
      '''Reads a VMUX style CSV format comma delimited log file and loads the data into an internal dictionary self.data[]

      Parameters:
         vmux_results_filename       :  Name of filename containing csv style data (including vmux analog files)
         vmux_names_filename  = None :  (obsolete) Name of lookup table for vmux signal names and vmux address mux.

      Returns :  None'''


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
      self.add_new_column( 'linenumber' )



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
             x = None
             pass


#        if len(c) > 3 and ( ( c[1] == self.vmuxsel_register and c[3].strip() == '1' ) or scope_vmux ) :  # ie it is a register 22 read operation
#         if len(c) > 3 and ( (  c[3].strip() == '1' ) or scope_vmux ) :  # ie it is a register 22 read operation
          
         if len(c) > 3:     # look for a line thats long enough
           try:
              tn = int( c[0] )
           except:
              tn = -1
           if tn >=0 or scope_vmux:       # look for a line that starts with a +ve integer

 

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
             self.data[ 'linenumber'  ].append( linecount             )

 
             self.write_vmux_data( csvsectioncount, full_regval, vmux_data_list, vmux_time_list  )


      self.csvsectioncount = csvsectioncount
      print '   .read %6d lines, record count %6d' % (linecount, self.datacount)

      fip.close()

    ###################################################################

    def write_vmux_data( self, sectionnum, vmux_num, vmux_data_list, vmux_time_list  ):

        ''' Takes the vmux_data_list and add it to all the records in the data array for the given sectionnum
            It also does the same to the vmux_time_list, except it only does so if it is not already added.
            In addition it will calculate an average value for the vmux_data_list by averaging the last 10% of
            samples, and writing this value into the data array

         Parameters:
             sectionnum     :  section number of the main ATR logfile (if present)
             vmux_num       :  vmux address number
             vmux_data_list :  List of data values for a given vmux_num
             vmux_time_list :  List of time values

         Returns:   None'''

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
        
        vmux_name = ''

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
                if re.search('\s*//', fld):
#                   print 'found it'

                    v = re.sub('\s', '', fld)
#                    print 'v=', n, v

                    grps = re.search(r'{(.*?)(}|$)', fld)
                    if grps:
                       parstr = grps.groups()[0]
                       # overwrite the parameter string removing the vmux signals, we do this so that we can get a list of parameter conditions without the
                       # vmux selection
                       fld = re.sub( r'.*TERMINATE', 'TERMINATE', parstr)
                       pars   = parstr.split(';')
#                      print pars
                       for nv in pars:
                          g = re.search( r'(.+)=(.+)' , nv)
                          if g and len(g.groups()) == 2:
#                            print nv

                             nm =  g.groups()[0]
                             nm =  nm.strip()
                             nm =  nm.upper()


                             v = g.groups()[1]
                             v =  v.strip()
                             try:
                                v = float(v)
                             except: pass
                             c = '[csv] ' + nm
                             self.add_new_column( c )
                             self.data[ c ][rn] =  v

                    
                             if nm == 'VMUXNAME' : vmux_name = v
 
                if n in colnam:
                  cnam = '[csv] ' + colnam[ n ]
                  self.add_new_column( cnam )
                  self.data[ cnam ][rn] = fld

##        try:     print '(vmux)     vmux_name =',      vmux_name, vmux_num
##        except:  pass


        vmux_data_list = new_vmux_data_list

        if str(vmux_num) in self.vmux_sel2name:
            vmux_name = self.vmux_sel2name[ str(vmux_num) ]

        if vmux_num < 0:
           vmux_name = 'SCOPE CHANNEL %s' % -vmux_num

        
        if vmux_name != '':
  
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
         '''Takes a list of vmux data and averages the values between the start and finish indexes

         Parameters:
            vmux_data_list : List of vmux data
            start          : starting index fraction  (usually 0.9)
            finish         : finish index fraction (usually 1.0)

         Returns:
            average        : average value between start and finish indexes
         '''


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
      '''Loads a Log file into pygram.  All data read from the file is loaded into internal dict self.data[]

      Parameters:
         logfilename = None    :  Name of filename containing ATR style log data
         cvslogfile  = None    :  Name of filename containing csv style data (including vmux analog files)
         vmux_name_file = None :  (obsolete) Name of lookup table for vmux signal names and vmux address mux.
         temperature = None    :  If data does not contain any temperature data, set the temperature data to this value (normally 25C)

      Returns   :   None'''



      # first check to see what type of logfile this is, if its a csv file then assume it is a vmux logfile, and retspecify the file varaibles
      if logfilename != None and re.search(r'.csv', logfilename  ) and csvfilename==None and vmux_names_file==None:
         csvfilename = logfilename
         logfilename = None
         vmux_names_file = 'Riserva_vmux_signals.csv'



      self.status.set( '(add_logfile) LOADING LOGFILE RESULTS: %s %s ' % ( logfilename, csvfilename ) )
      self.root.update()

      self.logfile_type      = 'excel'
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



          done_column_header     = False
          done_column_header_pre = False
          atr_column_header  = False


          ### Enable the reading of s2p network analyzer files
          if self.logfile_extension == '.s2p':

               self.s2p_type = 'real_imag'
               self.logfile_type = 's2p'
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


          linecount = 0
          amp_array = {}
          camp2num  = {}
          previous_row = []




          for row in reader:


            linecount += 1

            if self.logfile_type ==  's2p' :
                 if re.search(r'^#\s+Hz\s+S\s+MA\s+R', row[0]): self.s2p_type = 'mag_phi'
                 row = row[0].split()
                 if  re.search(r'^\s*!.*', row[0]) or  re.search(r'^\s*#.*', row[0] ) :  continue



            if len( row ) < 1 : continue

            if re.search(r'^\s*//\*+', row[0]) :  continue

            # Look for a new section header line
            #
            #      //Serial Number: A0B BOM-C SS SN001

#            print '(add_logfile)  row[0]=', linecount, row[0]

            grps = re.search(r'^//(.*?):(.*)$', row[0])
            if grps:
               name  = grps.groups()[0].strip()
               name = re.sub(r'\.', '', name)
            
               if name == 'Comment' : name = 'Comment_Section'
            
               value = grps.groups()[1].strip()
               try:
                  value = float(value)
               except: pass
               section_data[ name ] = value
               self.logfile_type = 'atr'



               if in_section_header == False:
                    in_section_header = True
                    self.atrsectioncount += 1
                    


               if name == 'Register Map File' :
                 name = 'Regmap'
                 value = self.get_filename_from_fullpath( value )
                 section_data[ name ] = value

               section_data[ 'section' ] = self.atrsectioncount

               if 'section' in self.data:
                  ln = len(self.data[ 'section' ])
                  lnll = []
                  nnll = []
                  for tsd in section_data:
                      if tsd in self.data:
                          lnl = len(self.data[tsd])
                      else:
                          lnl = None
                      lnll.append(lnl)
                      nnll.append(tsd)

               else:
                  ln =  -1
                  lnll = []
                  nnll = []

#               print '@@@@(add_logfile) ', linecount, self.datacount, section_data[ 'section' ], ln, lnf, lnll, nnll


            # Look for a test header line in the log file of the form:
            #
            #     //T#    TestName        Sw Matrix       S21(dB) Tuner Loss(dB)  ...
            #
            # or if its a simulation results file :
            #
            #     fin     vam     phase(outRl[::,1])[0, ::]


            if re.search(r'^\s*//T#\s*$', row[0]) :
               atr_column_header = True
               self.logfile_type = 'atr'
               in_section_header = False


            else:
               atr_column_header = False


            if atr_column_header == True                                   or \
               ( self.logfile_type == 'excel' and done_column_header == False and not re.match( r'^[\-\+0-9]', row[0] )) :    # look for excel column name row


               atr_column_header = True
               if self.logfile_type != 'excel':
                  atr_logfile = 'atr'
                  done_column_header = True
               else:
                  done_column_header_pre = True


               current_test_colnum2colname = []


               # look at each column heading name and create a new data_column and fill it with nulls up to the
               for i in range( 0 , len(row)):
                  name = row[i].strip()
                  name = re.sub(r'\.', '', name)
                  current_test_colnum2colname.append( name )

                  # If this is the first time we've seen this column name then create a new column in self.data and fill it will None.
                  if name not in self.data :
            #        print "  ADDING  MISSING COLUMN ", name, self.datacount
                     self.data[ name ] = [None] * self.datacount
                     cnum = cnum + 1
                     opcol2name.append(name)


               # look at each of the names in the header section and add it to the list of columns
               for name in section_data:
#                  current_test_colnum2colname.append( name )

                  # If this is the first time we've seen this section name then create a new column in self.data and fill it will None.
                  if name not in self.data :
            #        print "  ADDING  MISSING COLUMN ", name, self.datacount
                     self.data[ name ] = [None] * self.datacount
                     cnum = cnum + 1
                     opcol2name.append(name)









#           print '(add_logfile) looking for  &&', linecount, row[0]
            row0 = row[0].strip()

            #  Add the Parameter data
            #  Look for Special  && lines

            if len(row0) > 1 and row0[0] == '&':
               flds = row0.split(';')

               for fld in flds:
                 if len(fld) > 2:

                     if fld[0] == '&':
                         grps = re.search(r'&&\s*(\S+)', fld)
                         if grps:


                            amp_type = grps.groups()[0]
                            amp_type = amp_type.lower()
                            amp_prefix = '[&&%s] ' % amp_type
                            amp_array[ amp_prefix ] = []


                     else:
                         grps = re.search(r'(.*)=(.*)', fld)
                         if grps:
                            n = grps.groups()[0].strip()
                            v  = grps.groups()[1].strip()

                            try:
                               v = int( v )
                            except Exception:
                               pass
                            colname = '%s %s' % ( amp_prefix,  n )
                            self.add_new_column( colname )
                            camp2num[ colname ] = 'done'

                            amp_array[ amp_prefix ].append( [colname, v ] )


            #  Add the Parameter data
            #  Look for Special  && lines

            if len(row0) > 1 and row0.find('$$Parametric') == 0:
               flds = row0.split('}')

               get_regs = False
            
               for fld in flds:
                 fld = fld.strip()
                 if len(fld) > 2:


                     if fld.find('Accumulated Reg Settings') > 0:  #searching for:   'Accumulated Reg Settings = 38{13:9;8};'
                        get_regs = True
                        amp_prefix = '[$$Parametric] ' 
                        amp_array[ amp_prefix ] = []

 
                       
                     if get_regs:
                        grps = re.search( r'(\d+)\s*{\s*(\d+)\s*[:;]\s*(\d+)\s*[:;]\s*(\d+)', fld)           #searching for:   '38{13:9;8};'
 
                        if grps and len(grps.groups())==4 :
                            reg_num       = grps.groups()[0]
                            reg_stop_bit  = grps.groups()[1]
                            reg_start_bit = grps.groups()[2]
                            reg_value     = grps.groups()[3]

                            n = 'Reg%s[%s:%s]' % ( reg_num, reg_stop_bit, reg_start_bit ) 
                            colname = '%s %s' % ( amp_prefix,  n )
                            self.add_new_column( colname )
                            camp2num[ colname ] = 'done'

                            v = float( reg_value )
                            amp_array[ amp_prefix ].append( [colname, v ] )







            # If we have a spurious test line then lets preprocess the line so it looks like an ordinary test result line

            if re.search(r'^\s*//Spurious Data\s*$', row[0]) :

                # First copy the previous line
                # then copy the current line, but only those fields that are not empty

                new_row = previous_row

                for i, fld in enumerate( row ):
                   if fld.strip() != '' and fld != None and i != 0:
                       new_row[i] = row[i]
                row = new_row
 
            previous_row = row










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








            # Look for a valid data line. Line which contains measurement results.
            # if re.search(r'^\s*\d+\s*$', row[0]):     i.e.  look for a number in the first column




#            print logfile_type

            if ( self.logfile_type == 'atr'   and first_field_is_number  and done_column_header == True ) or \
               ( self.logfile_type == 'excel' and done_column_header == True ) or \
               ( self.logfile_type == 's2p'   and done_column_header == True ):


                self.datacount = self.datacount + 1
                in_section_header = False
                c2num = {}

                # write the value of each column into the data[] dictionary by adding it to the end.
                for i in range( 0 , len(row)):

                  if i >= len(current_test_colnum2colname):
#                    print '*** ERROR **** (add_logfile)', linecount, [ len(row), row[i]], i, len(current_test_colnum2colname), row
                     continue
                  name  = current_test_colnum2colname[ i ]
                  value = row[i].strip()
                  


                  #if name == 'Time' : value = re.sub(':','',value)


                  if name != 'Alert Reg' and re.search(r'^\s*(\+|\-)?\d+(\.)?(\d+)?([eE][+-]?\d+)?\s*$',value):
                      value = float(value)


                  if name == 'Temperature(degree C)' and temperature != None :
                     value = temperature

                  if name == 'AM-PM(degree)' and -360 <= float(value)  <= +360 :
                     value = ((value+270) % 360 ) - 270


                  if name == 'VAM(volt)':
                     value = float(value)  
                     value = abs(value)


#                  if name == 'Frequency of Spur (MHz)' :
#                       if value == 0.0 :
#                            dont_save_amplitude = True
#                            value = None
#                      else:
#                           dont_save_amplitude = False
#                 if name == 'Amplitude of Spur (dBm)' and dont_save_amplitude:
#                    value = None
#                    value = -49.0
#                    print 'amp of spur', value, dont_save_amplitude


                  if name == 'Date' or name == 'Test Date & Time':
                     try:
                       value = re.sub( r'/', '-', value)
                     except:
                       pass

                  ##############################################################################
                  # Save the ordinary data in the self.data array
                  #
                  # print '(load_logfile) name=<%s> value=<%s>' % ( name, value)
                  self.data[ name ].append( value )
                  c2num[ name ] = 'done'
                  #
                  ##############################################################################



                # save the record number as well
                self.data[ 'record_num' ].append( self.datacount )
                c2num[ 'record_num' ] = 'done'

                # save the record number as well
                self.data[ 'logfilename' ].append( self.logfilebasename )
                c2num[ 'logfilename' ] = 'done'

                # save the record number as well
                self.data[ 'linenumber' ].append( linecount )
                c2num[ 'linenumber' ] = 'done'



                # Add the parameter data for each record
                for amp_prefix in amp_array:
                    for amp_name_val in amp_array[ amp_prefix ]:
                         n = amp_name_val[0]
                         v = amp_name_val[1]
                         self.data[ n ].append( v )


#                print '(add_logfile) section_data names=',

                # Add the section header data in for each record.
                for sd in section_data:

                  # first check to see if this section_data sd name is also a main data column name in current_test_colnum2colname
#                  print sd,

                  if sd != 'Comment' and sd in current_test_colnum2colname:
                       print '*** ERROR *** (add_logfile) Line=%d  section name=%s is in the main data results at column=%d' % ( linecount, sd, current_test_colnum2colname.index(sd) )
                  self.data[ sd ].append( section_data[ sd ] )
                  c2num[ sd ] = 'done'
#                print ''


                # fill the unused columns with None to pad them out.
                for name in self.data :

                  if name not in c2num and name not in camp2num:
                    #print "filling inmissing field for  column %s, on record %d" % ( name, self.datacount )
                    self.data[ name ].append( None )



            if self.logfile_type == 'excel' and done_column_header_pre == True:
                  done_column_header     = True
                  done_column_header_pre == False



          fip.close()

          print '   .read %s %6d lines, read in records %6d to %6d' % (self.logfile_type, linecount, rn_start, self.datacount)


      if csvfilename != None:
         self.add_vmux_csvfile( csvfilename, vmux_names_file )



      # Add all the missing data, (ie. data columns we generate from the logfile columns)
      
      # first break it up into seperate sections, by making a list record numbers where the
      # section number changes
      
      if 'section' in self.data:
          rn_sf_list = []
          section_prev = None
          for rn in range(rn_start, self.datacount):
            section = self.data['section'][rn]
            if section != section_prev:
                rn_sf_list.append(rn)
            section_prev = section
     
          # process each section      
          for i in range( len(rn_sf_list) ):
            rns = rn_sf_list[i]
            
            # the last record is the next section break
            # unless we are at the end when we will use the last record 
            if i != len(rn_sf_list)-1:
                rnf = rn_sf_list[i+1]
            else:
                rnf = self.datacount
                
            self.add_missing_columns( rns, rnf )
      else:
            self.add_missing_columns( rn_start, self.datacount )
        

      self.win_load( logfilename, csvfilename, self.datacount-rn_start )


      files = ', '.join( self.logfilenames + self.csvfilenames )
      z = self.root.winfo_toplevel()
      z.wm_title('PYGRAM Graphing Tool  version:  ' + self.pygram_version + '     ' + files )






    ###################################################################
    ###################################################################

    def add_db_res(self, db_lg_key):
      '''Reads the results from the datapower database and loads the data into an internal dictionary 'data'

      Parameters:
           db_lg_key :  key into the datapower records

      Returns:   None'''


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

                 self.data[ 'logfilename' ].append( self.logfilebasename )
                 self.data[ 'linenumber' ].append( str( rescount ) )

              print '   .read %6d db records, read in records %6d to %6d' % (rescount, rn_start, self.datacount)

#         except Exception:
#             print "*** ERROR (load_logfile) could not read file " , logfilename



              self.db_cursor.close()



      self.add_missing_columns( rn_start, self.datacount)




      self.win_load( logfilename, num_records= self.datacount-rn_start )


    ###################################################################
    def create_values_dict( self ):
        '''Generates a dictionary of values for the standard column names (those in self.value_dict_names)
        For each column name it goes through the self.data[name] values making a list self.values_dict[name]
        listing all the unique values, and self.values_dict_count listing the counts for each value.
        (uses self.add_values_dict( name ))

        It only does this if self.values_dict_done == 0, when done it sets self.values_dict_done = 1

        Parameters:   None

        Returns   :   None'''



             # look at the value and add them to the values dictionary if not already in the list
        if self.values_dict_done == 0:
             self.values_dict = {}
             self.values_dict_count = {}
             for name in self.value_dict_names:
               self.add_values_dict( name )
        self.values_dict_done = 1

    ###################################################################
    def add_values_dict( self, name, rn_start=0, rn_finish=None ):
         '''Adds an entry to the self.value_dict[ name ] and self.values_dict_count[ name ]
        It goes through the self.data[name] values, making a list of
        unique values, and self.values_dict_count listing the counts for each value.

        Optional rn_start and rn_finish parameters are used to restrict the scope of
        the dict to just the self.data[] values for a given data range.

        This function is intended to be used on swept variables.
        If a column name contains more than 200 different values then a warning is pronted
        and the function is terminated and self.values[] contains only the first 200 values.

        Parameters:
             name             :  Column name used to build values_dict from self.data[]
             rn_start  = None :  Starting record number, if None record number 0 is used
             rn_finish = None :  Finish record number, if None record number self.datacount is used (i.e. the last record)

        Returns   :   None

        Updates   :  self.values_dict[ name ]
                     self.values_dict_count[ name ]'''

         if rn_finish == None:
            rn_finish = self.datacount

         if name not in self.data:
            self.add_new_column( name )
            self.add_values_dict( name, rn_start, rn_finish )
            return

         if type( name ) == types.StringType :

              if not name in self.values_dict:
               self.values_dict[ name ] = []
               self.values_dict_count[ name ] = []

               # if the number of different values exceeds 200 then abort the dictionary,
               #  this must be a results data column, and we don't need to form the dictionary for results columns

               for rn in range(rn_start,rn_finish):
                   val =  self.data[name][rn]
#                  if val == None or val == '': continue   # dont count null data
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
                       if len( self.values_dict_count[ name ] ) > 200 :
                           print "...warning (add_values_dict) attempt to create values_dict for column '%s' which has too many different values" % ( name )
#                          raise Exception
                           break

    ###################################################################
    def hex2bin( self, hexstr ):
      '''Converts a string from hex into a 16 bit binary string
      
      Parameters:
          hexstr:  Input hex string, must be less <= FFFF
      Returns:     
          b:       16 character string containing the converted binary value''' 

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
      '''After reading in a logfile (add_logfile) this function will add new self.data[] columns
      for the missing or generated data. Such as vramp voltage column, and segment column
      and the, HB/LB column, also adds the part number etc

      Parameters :
         rn_start  :  First record number to start work on
         rn_finish :  Last record number to work on
         logfile_type : Specifies the type of logfile 'atr' 'excel', 's2p'
      Returns :  None
      Reads  :  self.data[]
      Updates : self.data[]
      '''


#      print '(add_missing_columns) rn_start=%s  rn_finish=%s' % ( rn_start, rn_finish)

      if rn_start==None or  rn_finish==None : return

      rn_sum = rn_finish - rn_start

      #add missing column data to the end of the existing data.

      if self.logfile_type == 'atr':
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
#                  print '(add_logfile) vramp data ', [ vramp_release, hb_lb, seg, voltage, full_filespec, pcl_level ]

                  try:
                     voltage = float(voltage)
                  except Exception:
                     pass

                  self.data['Segments'][rn]        = seg
                  self.data['Vramp Voltage'][rn]   = voltage
                  self.data['Vramp Release'][rn]   = vramp_release
                  self.data['Vramp Filebase'][rn]  = self.get_vramp_filebase( full_filespec )
                  if pcl_level != '' :
                        self.add_new_column( 'PCL' )
                        self.data['PCL'][rn]             = pcl_level


        #                  if name == 'Serial Number':


              if 'Sw Matrix' in self.data :


                for rn in range( rn_start, rn_finish ):
                   self.add_new_column( 'Sw Matrix' )
                   f = self.data['Sw Matrix'][rn]

                   if f == None and 'Sw.Matrix' in self.data:
                       f = self.data['Sw.Matrix'][rn]

                   if f == None : break

                   self.add_new_column( 'HB_LB' )
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
              if self.data['Test Freq(MHz)'][rn] != None :   self.data['Freq(GHz)'][rn] = self.data['Test Freq(MHz)'][rn] / 1e3


      if 'Freq(MHz)' in self.data and rn_finish <= len(self.data['Freq(MHz)']):

           print '(add_missing_column)', len( self.data['Freq(MHz)'] ), rn_start, rn_finish

           self.add_new_column( 'Sub-band' )

           bndlst = []
           bndlst[:] = self.freq_sub_band_list
           bndlst.reverse()
           for rn in range( rn_start, rn_finish ):
              f = self.data['Freq(MHz)'][rn]
              if f != None:
                  for b in bndlst:
                      f_up  = b[2]
                      f_low = b[1]
                      if f_low <= f <= f_up:   self.data['Sub-band' ][rn] = b[0]




##  To get S11 and S22 in VSWR, need to use (1+ mag (S11, or 22))/(1- mag (S11, or 22)),   email from H.Sun 12nov09

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




########
########

##   To get S21 in dB and de-embed, need to do:  LB  20*log (mag(S21))  + 0.33,  HB  20*log (mag(S21))  + 0.59 ,   email from H.Sun 12nov09


      # Tony's new compensation data (3/2/10)

      if 's21_mag' in self.data :
           self.add_new_column( 's21_dB' )
           for rn in range( rn_start, rn_finish ):
                  if 'Freq(MHz)' in self.data and self.data['Freq(MHz)'][rn] < 1383:
                        if 'Freq(MHz)' in self.data and self.data['Freq(MHz)'][rn] < 910:
                              correction = 0.32
                        else:
                              correction = 0.35
                  else:
                        if 'Freq(MHz)' in self.data and self.data['Freq(MHz)'][rn] < 1905:
                              correction = 0.74
                        else:
                              correction = 0.81
                  self.data['s21_dB'][rn] =  20*log10(self.data['s21_mag'][rn])  + correction

      if 's12_mag' in self.data :
            self.add_new_column( 's12_dB' )
            self.add_new_column( 's12_Loss_dB' )
            for rn in range( rn_start, rn_finish ):
                  if 'Freq(MHz)' in self.data and self.data['Freq(MHz)'][rn] < 1383:
                        if 'Freq(MHz)' in self.data and self.data['Freq(MHz)'][rn] < 910:
                              correction = 0.32
                        else:
                              correction = 0.35
                  else:
                        if 'Freq(MHz)' in self.data and self.data['Freq(MHz)'][rn] < 1910:
                              correction = 0.74
                        else:
                              correction = 0.81

                  self.data['s12_dB'][rn] = 20*log10(self.data['s12_mag'][rn]) + correction
                  self.data['s12_Loss_dB'][rn] = -self.data['s12_dB'][rn]
########
########



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




      # seperate the fields in the serial number in case we want to match
      if 'Serial Number' in self.data and rn_finish > 0:
        fullname = self.data['Serial Number'][rn_start]
        flds = fullname.split('-')
        fl   = len(flds)
        for rn in range( rn_start, rn_finish ):
           fullname = self.data['Serial Number'][rn]
           flds = fullname.split('-')
           if len(flds) == 1 and flds[0] == '': continue
           for i,n in enumerate( flds ):
              inm = 'SN_fld' + str(i)
              if inm not in self.data: self.add_new_column( inm )
              self.data[ inm ][rn] = flds[i]






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




      # At this point we should have all the standard sweep variables setup
      # and we should be ok to generate the values_dict (a list of all values in self.data[]  for a given column name)

      if self.value_dict_names == []:
          for vdn in self.value_dict_names_original_list:
            if vdn in self.data:
                self.value_dict_names.append( vdn )
#               self.values_dict[ vdn ] = []

      self.values_dict_done = 0
      self.create_values_dict()



      self.scale_data( 'Vbat_I(Amp)', 'Vbat_I(mA)' , 1000,  rn_start, rn_finish )




      # create a new orfs column with the worst of the +ve and -ve values,
      # the +ve value is stored in the 'Sw Pwr 400KHz(dBm)' column, make this the column where the max value is stored

      if 'Sw Pwr -400KHz(dBm)' in self.data and 'Sw Pwr 400KHz(dBm)' in self.data:
         self.add_new_column( 'Sw Pwr +400KHz(dBm)' )
         self.add_new_column( 'Sw Pwr -400KHz(dBm)' )
         self.add_new_column( 'Sw Pwr 400KHz(dBm)' )


         if 'Sw Pwr -400KHz(db)' in self.data : self.add_new_column( 'PSA Pwr Out(dBm)' )

         for rn in range( rn_start, rn_finish ):
            maxval = max( self.data[ 'Sw Pwr -400KHz(dBm)' ][rn], self.data[ 'Sw Pwr 400KHz(dBm)' ][rn] )
            self.data[ 'Sw Pwr +400KHz(dBm)' ][rn] =  self.data[ 'Sw Pwr 400KHz(dBm)' ][rn]
            self.data[ 'Sw Pwr 400KHz(dBm)'  ][rn] =  maxval
            if  'Sw Pwr -400KHz(db)' in self.data and self.data[ 'Sw Pwr -400KHz(dBm)' ][rn] != None and self.data[ 'Sw Pwr -400KHz(db)' ][rn]:
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

#### QQQQ ORFS



      if ('TestName' in self.data)  and  ('Spurious (ETSI reduced)' in  self.data['TestName'] or \
                                          'Spurious (ETSI full)'    in  self.data['TestName'] or \
                                          'Spurious (quick)'        in  self.data['TestName'] ):

         self.add_spurious_data(  1, rn_start, rn_finish )
         self.add_spurious_data(  2, rn_start, rn_finish )
         self.add_spurious_data(  5, rn_start, rn_finish )
         self.add_spurious_data( 10, rn_start, rn_finish )
         self.add_spurious_data( 15, rn_start, rn_finish )
         self.add_spurious_data( 20, rn_start, rn_finish )
         self.add_spurious_data( 30, rn_start, rn_finish )
         self.add_spurious_data( None, rn_start=rn_start, rn_finish=rn_finish  )



### QQQQ RELOCATE THIS UP 
      # if the product number is not set then look at the list of serial numbers in fld 0
      # if there is only one value then assume that this is the product number
      #
      if self.product == None:
          if 'SN_fld0' in self.data:
             self.add_values_dict( 'SN_fld0')

             if len( self.values_dict['SN_fld0' ] ) == 1 :
                self.product = self.values_dict['SN_fld0' ][0]



      self.add_vmux_columns( rn_start, rn_finish )

      self.add_aclr_data(  rn_start, rn_finish )

      self.add_all_power_values( rn_start, rn_finish )



      # make sure every data name in the data dictionary is the adjusted in length to the same value (self.datacount)
      for n in self.data:
        self.add_new_column( n )



      if 'TestName' in self.values_dict:
          del self.values_dict[ 'TestName' ]
      self.add_values_dict( 'TestName')    # reset the TestName values_dict

      if 'Freq(MHz)' in self.values_dict:
          del  self.values_dict[ 'Freq(MHz)']
      self.add_values_dict('Freq(MHz)' )





    ######################################################################################
    def add_all_power_values( self, rn_start, rn_finish ):
      '''Adds all the Pout data. This includes the following operations
      
         - For 'Vramp Search' tests - copy 'Closest Power' to 'Adj Pwr Out'
         - Copy Adj Pwr Out(dBm) values from Pwr&Eff tests to Non Pwr&Eff tests which have exactly the same conditions
         - Add Pout(dBm) values to the 'AMAM distortion' tests by Calibrating using the preceding Pwr&Eff test.
         - From the 'Adj Pwr Out(dBm)' (or 'PSA Pwr Out') value calculate: Pout(dBm), Pout(W) Pout(V), Poutpk(V)
         - Calculate 'AMAM conversion (V/V)' and 'AMAM conversion (V/V-offset)'
         - Calculate the 'AMAM conversion Voutpk/VAM (dV/dV)' Slope and the 'Power Control' slope
         - Calculate the 'Gain*' and AMAM slope and AMPM slope for <emp> type measurements
         - Get the Nominal Conditions  (get_nom_conditions)
         - Add the 'Ref Pout(dBm)' and 'Pwr Variation(dB)'  (add_ref_pout_data)
         - Add the @ reference power data, (add_rated_power_values)      
      ''' 




      # Propagate the Vramp Search values
      if 'TestName' in self.data  and 'Closest Target Power(dBm)' in self.data  :
          self.add_new_column( 'Adj Pwr Out(dBm)'  )
          for rn in range( rn_start, rn_finish ):
              if self.data['TestName'][rn] == self.vramp_search_testname :
                  self.data[ 'Adj Pwr Out(dBm)' ][rn] = self.data[ 'Closest Target Power(dBm)' ][rn]




      # Add pout data to non power and efficiency tests
      self.add_vramp2pout_data( rn_start, rn_finish )




      # Calculate Pout data from the AMAM DIstortion test data (and Calibrate using Power & Eff test)
      # Also adds the Ref Pout and Rated Pout data
      self.calc_amam_pout( rn_start, rn_finish )
          



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

             if pdbm != None :

                 try:                
                     pw = 10**( (pdbm-30.0)/10.0 )
                     pv = sqrt( self.characteristic_impedance * pw )
                     self.data[ 'Pout(dBm)' ][rn]  = pdbm
                     self.data[ 'Pout(W)'   ][rn]  = pw
                     self.data[ 'Pout(V)'   ][rn]  = pv
                     self.data[ 'Poutpk(V)'   ][rn]  = pv * 1.414213562
                 except:
                     pass





      # Calculate the AMAM Conversion
      for vam_name in [ 'VAM(volt)', 'Vramp Voltage']:

       if 1==1 and vam_name in self.data and  'Pout(dBm)' in self.data :
         self.add_new_column( 'AMAM conversion abs (V/V)'   )
         self.add_new_column( 'AMAM conversion abs (V/V-voffset)'   )
         delta_vam = 0
         delta_pv  = 0
         for rn in range( rn_start, rn_finish ):
                 try:
                    vam = float( self.data[ vam_name ][rn] )
                 except Exception:
                    vam_old = None
                    pv_old  = None
                    continue
                 pv  = self.data[ 'Poutpk(V)'   ][rn]
                 pdb = self.data[ 'Pout(dBm)'   ][rn]
                 amam_abs   = None
                 amam_voff  = None
                 amam_delta = None
                 try:
                    amam_abs  =  pv / vam
                    amam_voff =  pv / (vam - self.vam_offset )
                    self.data[ 'AMAM conversion abs (V/V)'            ][rn]  = amam_abs
                    self.data[ 'AMAM conversion abs (V/V-voffset)'    ][rn]  = amam_voff

                 except Exception:
                    pass




         # Add Pout slope data (vs Vramp)
         self.add_slope( vam_name, 'Poutpk(V)', 'AMAM conversion Voutpk/VAM (dV/dV)', rn_start, rn_finish)
         self.add_slope( vam_name, 'Pout(dBm)', 'Power Control Slope (dB/V)', rn_start, rn_finish)

 
 
     
      # Calculate the AMAM Gain
      if 1==1 and vam_name in self.data and  'Pout(dBm)' in self.data :

         got_data = False

         for rn in range( rn_start, rn_finish ):

            try:
               v = float( self.data[ vam_name    ][rn] )
               p = float( self.data[ 'Pout(dBm)' ][rn] )
            except Exception:
               continue

            if type(v) == types.NoneType or (type(v) == types.StringType  and  v.lower() == 'nan') or \
               type(p) == types.NoneType or (type(p) == types.StringType  and  p.lower() == 'nan'):
               gain = None
            else:
               if not got_data:
                   got_data = True
                   self.add_new_column( 'Gain AM/(VAM-offset) (dB)'              )
                   self.add_new_column( 'Gain AM/(VAM-offset) (dB) <emp-limits>' )
                   self.add_new_column( 'Gain AM/(VAM-offset) Slope (dB/dB)'     )


               if type(p) == types.NoneType or (type(p) == types.StringType  and  p.lower() == 'nan'):
                  gain = None
               else:

                    vam_offset_diff = v - self.vam_offset
                    if vam_offset_diff < 0.001 : vam_offset_diff = 0.001
                    gain = p -   20*log10( vam_offset_diff )

            if got_data:
                self.data[ 'Gain AM/(VAM-offset) (dB)' ][rn]              = gain
                self.data[ 'Gain AM/(VAM-offset) (dB) <emp-limits>' ][rn] = gain




         # Add Gain and Phase slope data (vs Pout)
                        #    x col            y col                          new slope y col
         self.add_slope( 'Pout(dBm)', 'Gain AM/(VAM-offset) (dB)', 'Gain AM/(VAM-offset) Slope (dB/dB)', rn_start, rn_finish)
         self.add_slope( 'Pout(dBm)', 'AM-PM(degree)',             'AM-PM Slope (deg/dB)',               rn_start, rn_finish )





      if 'Pout(dBm)' in self.data and '[csv] Script File Name' not in self.data and self.logfile_type == 'atr':

         try:
            del self.values_dict[ 'TestName' ]
         except:  pass

         self.add_values_dict( 'TestName', rn_start, rn_finish)
         if 1:
#         if 1==1 or self.vramp_search_testname in self.values_dict[ 'TestName' ]:
             rnl_list = self.get_nom_conditions( rn_start, rn_finish)

             # for each of the nominal cond list go through the

             if rnl_list != None and len( rnl_list ) > 0 :
                 for rnl in rnl_list:
                     print '(add_missing_columns)  rnl=', rnl
                     self.update_nom_conditions( rnl )
                     self.add_ref_pout_data( rnl, rn_start, rn_finish, testname='Output Power & Efficiency', matchname='Vramp Voltage')
                     self.add_ref_pout_data( rnl, rn_start, rn_finish, testname='AM-AM AM-PM Distortion'   , matchname='Step')

                 self.add_rated_power_values( rn_start, rn_finish )





    ######################################################################################
    def add_vmux_columns( self, rn_start, rn_finish ):

#      return

      # Add some special vmux columns
      pname = '[csv] Script File Name'
      if pname in self.data:

          name_a   = '[Time] AVDDRV3_TM'
          name_b   = '[Time] FB_TM'
          new_name = '[Time] AVDDRV3*'

          print '(add_vmux_columns)' , rn_start, rn_finish, len( self.data[name_a]) ,len( self.data[name_b])


          # Go through all the records for this logfile.
          # For each record with non-None list in column 'name_a' look
          # look for a non-None list for 'name_b' column in the same record range.
          # if found then take the 'name_a' list and the 'name_b' list and generate a 
          # new column list and call it 'new_name'
          if name_a in self.data and name_b in self.data:
              self.add_new_column( new_name )
              for rna in range( rn_start, rn_finish ):
                   if self.data[ name_a ][ rna ] != None:
                      for rnb in range( rn_start, rn_finish ):
                          if self.data[ name_b ][ rnb ] != None:
#                            print self.data[ pname ][ rna ] , self.data[ pname ][ rnb ]
                             # Check that the csv logfile names are the same
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


          name_a   = '[Time] SCOPE CHANNEL 2'
          name_b   = '[Time] SCOPE CHANNEL 4'
          new_name = '[Time] SCOPE EFF*'

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
                                     y = b/max(a, 0.01)
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


          # If any records have a non null VAM list, then copy every record with
          #  the list.
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

          name = '[Time] SCOPE CHANNEL 4'
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



    ###################################################################
    def add_aclr_data( self,  rn_start, rn_finish ):
      '''Function for creating new ACLR columns for linear amp performance measurements
          Creates the following column names:
           'Linear Pwr Gain'    :  output power - input power (dB/dB)
           'ACLR-5,-10,5,10     :  difference between power at center freq and power at offset freq

         Parameters:
             rn_start  :  starting record number
             rn_finish :  finish record number. Only records between rn_start and rn_finish will be calculated.

         Returns:   None
         Updates:    self.data[ ]
      '''

      # add WCDMA data
      if 'Pwr at Center Freq (dBc)' in self.data:
          if 'Pwr at -5 MHz Offset (dBc)'   in self.data and \
             'Pwr at -10 MHz Offset (dBc)' in self.data and \
             'Pwr at 5 MHz Offset(dBc)'   in self.data and \
             'Pwr at 10 MHz Offset(dBc)'  in self.data    :
              self.add_new_column( 'ACLR-5' )
              self.add_new_column( 'ACLR-10')
              self.add_new_column( 'ACLR5'  )
              self.add_new_column( 'ACLR10' )
              self.add_new_column( 'Linear Pwr Gain' )


# Gain = Pwr at Center Freq (dBc)  -  Pwr In (dBm)
#  ACLR-5 = -Pwr at Center Freq (dBc)  +  Pwr at -5MHz Offset (dBc)
#  ACLR5  = -Pwr at Center Freq (dBc)  +  Pwr at 5MHz Offset (dBc)
#  ACLR5  = -Pwr at Center Freq (dBc)  +  Pwr at -10MHz Offset (dBc)
#  ACLR10 = -Pwr at Center Freq (dBc)  +  Pwr at 10MHz Offset (dBc)



              for rn in range( rn_start, rn_finish ):
                if self.data['Pwr at Center Freq (dBc)'][rn] != None:
                  self.data['ACLR-5'][rn]  = self.data['Pwr at -5 MHz Offset (dBc)'][rn]  - self.data['Pwr at Center Freq (dBc)'][rn]
                  self.data['ACLR-10'][rn] = self.data['Pwr at -10 MHz Offset (dBc)'][rn] - self.data['Pwr at Center Freq (dBc)'][rn]
                  self.data['ACLR5'][rn]   = self.data['Pwr at 5 MHz Offset(dBc)'][rn]   - self.data['Pwr at Center Freq (dBc)'][rn]
                  self.data['ACLR10'][rn]  = self.data['Pwr at 10 MHz Offset(dBc)'][rn]  - self.data['Pwr at Center Freq (dBc)'][rn]
                  self.data['Linear Pwr Gain'][rn] = self.data['Pwr at Center Freq (dBc)'][rn] - self.data['Pwr In(dBm)'][rn]
#  ACLR-5 = -Pwr at Center Freq (dBc)  +  Pwr at -5MHz Offset (dBc)



    ###################################################################
    def scale_time_data( self, name, new_name, scale, rn_start, rn_finish ):
       ''' Creates a new column 'new_name' by scaling the 'name' column
          it works on vmux type data which is in the form of a list

         Updates:  self.data[ new_name ]

         Parameters:

             name      :   Name of existing column to be scaled
             new_name  :   Name of new column which will be have the scaled data
             scale     :   Number that is used to scale the data 'name' * scale  = 'new_name'
             rn_start  :  starting record number
             rn_finish :  finish record number. Only records between rn_start and rn_finish will be calculated.

         Returns:  None'''

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
    def scale_data( self, name, new_name, scale, rn_start, rn_finish ):
       ''' Creates a new column 'new_name' by scaling the 'name' column
          it works on the self.data values

         Updates:  self.data[ new_name ]

         Parameters:

             name      :   Name of existing column to be scaled
             new_name  :   Name of new column which will be have the scaled data
             scale     :   Number that is used to scale the data 'name' * scale  = 'new_name'
             rn_start  :  starting record number
             rn_finish :  finish record number. Only records between rn_start and rn_finish will be calculated.

         Returns:  None'''

       if name in self.data:
           self.add_new_column( new_name )
           for rn in range( rn_start, rn_finish ):
                if self.data[ name ][ rn ] != None:
                     self.data[ new_name ][ rn ] = self.data[ name ][ rn ] * scale

    ###################################################################

    def update_nom_conditions( self, nom_list ):
       '''Takes the list of nominal frequencies and values as generated by function
       get_nom_conditions and sets the self.nom_freq_list and self.nom_found_value_list
       This is required by the add_cal_pout_data function.

       Paramaters:
          nom_list  :  Two element list [ nom_freq_list, nom_found_value_list ]

       Returns:   None
       Sets:  self.nom_freq_list  and  self.nom_found_value_list'''

       self.nom_freq_list        = nom_list[0]
       self.nom_found_value_list = nom_list[1]



    ###################################################################
#    def get_nom_conditions( self, rn_start, rn_finish ):
    def get_nom_conditions( self, rn_start, rn_finish ):
      ''' Gets a list of the nominal conditions
      Returns :
          vramp_search_sections :
             A list of 3 element lists. One per VRAMP SEARCH section
             [ [ [ nom_freq_list] [ nom_value_list ] ], rn_start, rn_finish ] ... ]
            (if no VRAMP SEARCH found then the list contains a single 3 element list ) '''

      return self.nom_value_list


#       if 'Freq(MHz)' not in self.data: return
# 
# 
#       
# 
#       # Get a list of vramp search sections.
#       # record the start and finish record number for each section
#       vramp_search_sections = []
#       rns = rn_start
#       rnf = rn_start
#       vrmp_search = False
# 
#       if 'section' in self.data:
#              sectionnum = self.data['section'][rns]
# 
#       for rn in range(rn_start, rn_finish ):
#           if self.data['TestName'][rn] == self.vramp_search_testname:
#              vramp_search_sections.append( [ None, rns, rnf+1, vrmp_search, [ self.data['linenumber'][rns], self.data['linenumber'][rnf]] ] )
#              rns = rn
#              vrmp_search = True
# #             print '(get_nom_conditions) found vramp search at rn=', rn
# 
# 
#           # if we find a new section header in the log file then start a new vrmap_search_section
#           if 'section' in self.data:
#              sn = self.data['section'][rn]
#              if sn != '' and sn != sectionnum :
#                 vramp_search_sections.append( [ None, rns, rnf+1, vrmp_search, [ self.data['linenumber'][rns], self.data['linenumber'][rnf]] ])
#                 rns = rn
#                 vrmp_search = False
#                 sectionnum = sn
# 
#           rnf = rn
#       vramp_search_sections.append( [ None, rns, rnf+1, vrmp_search, [ self.data['linenumber'][rns], self.data['linenumber'][rnf]] ])
# 
# 
# 
# 
#       for vss_idx,vss  in enumerate( vramp_search_sections ):
# 
# #              print '(get_nom_conditions) looping round the vramp_search_sections'
# 
#               
#               rns = vss[1]
#               rnf = vss[2]
#               vrs = vss[3]
# 
#               nom_freq_list = []
#               nom_found_value_list  = []
# 
# 
# 
#               # make up a fresh list of frequencies that are in the this section of the self.data[]
#               del  self.values_dict[ 'Freq(MHz)']
#               self.add_values_dict('Freq(MHz)', rns,rnf )
# 
#               new_nom_colname_list = []
#               for i,n in enumerate( self.nom_colname_list ):
#                   if n in self.values_dict:
#                      del  self.values_dict[ n ]
#                   self.add_values_dict(n, rns,rnf )
# #                  print  '(get_nominal_conditions)  values_dict: ', n , len(self.values_dict[n]), self.values_dict[n] 
#                   if len(self.values_dict[n]) >= 1:  val0 = self.values_dict[n][0]
#                   else:                              val0 = None
#                   if val0 != None:
#                       new_nom_colname_list.append( n )
# 
#               self.nom_colname_list = new_nom_colname_list
# 
#               # 1
#               # Find out which frequencies were present in the log file, and find the frequency which is closest to the center of the
#               # band, (and make sure the count for this frequency is high enough)
#               done_lb = False
#               done_hb = False
#               for kidx,k in enumerate( self.freq_sub_band_list) :
#                    nom_freq = -1
#                    # get the center of band frequency, this will be the nominal freq
#                    flw = k[1]
#                    fup = k[2]
#                    fmid = (flw+fup)/2.0
#                    subbandname = k[0]
# 
# 
#                    if vrs:
#                           # if doing a vramp search then we dont need to look through the data for the most common freq
#                           # instead we will use the frequency that was used for the vramp search (record number = rns )
# 
#                           # if this freq lies within the current band then we'll use it else set nom_freq to -1
# 
#                           freq = self.data['Freq(MHz)'][rns]
#                           if kidx == self.get_subband_idx_from_freq( freq ):
#                                nom_freq = freq
#                           else:
#                                nom_freq = -1
# 
#                    else:
# 
# 
# 
#                 #          print '(add_cal) looking for values in values_dict that most closely match', fmid
# 
#                            fmin_diff_i = 0
#                            fdiff = []
#                            inband_freq_count = 0
#                            for i,f in enumerate( self.values_dict[ 'Freq(MHz)' ] ):
#                                  if f == None : continue
#                                  fdiff.append(None)
#                                  fdiff[i] = abs(f - fmid)
#                                  if fdiff[i] < fdiff[ fmin_diff_i ]:
#                                     fmin_diff_i = i
#                                  if  flw <= f <= fup  and self.values_dict_count[ 'Freq(MHz)' ][i] > 5:
#                                       inband_freq_count +=1
# 
#                 #                print '(add_cal)             ... trying', f, i, fmin_diff_i, ' inband_freq_count=', inband_freq_count, fdiff[i],  fdiff[ fmin_diff_i ]
#                            # fmin_diff_i = index for freq that is closest to midband
# 
#                            # if the number of frequencies within the band is less than three then there is not enough to make a proper Ref Pout test
# 
#                            #
#                            if inband_freq_count >=1:
#                                nom_freq = self.values_dict[ 'Freq(MHz)' ][ fmin_diff_i ]
# 
#                                # if we have already found 3 frequnecies inside our sub band then do not calculate the Ref Pout for the entire band.
#                                if nom_freq < 1200 :
#                                   if k[0] == 'LB' and done_lb: nom_freq = -1
#                                   done_lb = True
#                                else:
#                                   if k[0] == 'HB' and done_hb: nom_freq = -1
#                                   done_hb = True
#                            else:
#                                nom_freq = -1
# 
#                    nom_freq_list.append( nom_freq )
# 
# 
# 
#               # 2.
#               # For each column name in the nom_match_name_list, go through the values to find the
#               # value which most closely matches the nominal value listed in the nom_match_value_list
# 
#               for i,n in enumerate( self.nom_colname_list ):
# 
#                 if vrs:
# 
#                         # if doing vramp search then use the nominal value from the vramp search record.
#                         nom_found_value_list.append( self.data[ n ][rns] )
# 
#                 else:
#              
#                         if n in  self.values_dict:
#                           vlist = self.values_dict[ n ]
#                           vcount = self.values_dict_count[ n ]
# 
# 
#                           try:
#                              target_value = float( self.nom_target_value_list[i])
#                           except Exception:
#                              # add the first value from the value_dict
#                 #             nom_found_value_list.append( vlist[0] )
# 
#                              nom_found_value_list.append( None )
# 
#                              continue
# 
#                           closest_ix = 0
# 
# #                          print '(get_nom_conditions) n=%s, closest_ix=%s' % ( n , closest_ix )
# #                          print '(get_nom_conditions)             target_value=', target_value
# #                          print '(get_nom_conditions)             vlist[closest_ix]=',  vlist[ closest_ix ] 
#  
#                           try:
#                               vdiff      = abs( float( vlist[ closest_ix ]) - target_value )
#                               for ix, v in  enumerate( vlist ):
#                                  # find the difference between this value and the target value
#                                  # if its less than the current minimum then make this one the new min
#                                  if abs( float( vlist[ ix ] ) - target_value) < vdiff and  vcount[ ix ] > 10:
#                                       closest_ix = ix
#                                       vdiff = abs( float( vlist[ ix ] ) - target_value)
#                           except: 
#                                  pass
# 
#                           nom_found_value_list.append( vlist[ closest_ix ])
#                         else:
#                           nom_found_value_list.append( None )
# 
# 
# 
# 
# #              self.nom_found_value_list = nom_found_value_list[:]
# 
# 
# 
# 
# 
# #             print '\n    (get_nom_conditions) using nominal conditions:\n        ',
# #              for ix, n in enumerate( self.nom_colname_list):
# #                if n in  self.values_dict:
# #                    print '(add_cal_pout_data)     %10s  target=%10s found=%10s' % ( n, self.nom_target_value_list[ix], nom_found_value_list[ix] )
# #                    try:
# #                        print '%s=%s ' % ( n, nom_found_value_list[ix] ),
# #                        pass
# #                    except Exception:
# #                       pass
# #              print ''
# 
# 
# #              print '    (get_nom_conditions)  nom_freq_list ', nom_freq_list, rns, rnf
# 
#               vramp_search_sections[ vss_idx ][0] = [ nom_freq_list[:] , nom_found_value_list[:] ]
# 
#       print '\n  (get_nom_conditions) List of different nominal condition sections. New Vramp Search and new section in logfile will cause a new conditions section'
#       print '     "[[[ freq ... ] ,  [ vswr, phase, temp, vbat, pin, reg ]], rns, rnf, Vramp_search, [ line_stt, line_fin ]]"'
#       for i  in vramp_search_sections:
#          print '     ', i
#       print ''
# 
#       return vramp_search_sections


    ###################################################################
#    def get_nom_conditions( self, rn_start, rn_finish ):
    def get_nom_conditions_obsolete( self, rn_start, rn_finish ):
      ''' Gets the nominal conditions from a set of records.
      First it breaks the records into separate VRAMP SEARCH sections.
      If there are one or more records with a TestName of VRAMP SEARCH, it will split the
      the records into separate sections each starting with a new VRAMP SEARCH record.
      The intent is that the nominal conditions in the first VRAMP SEARCH record are
      applied to all the subsequent records up to the next VRAMP SEARCH record and are
      grouped together with the same Nominal Conditions.   The function will
      find the Nominal frequency, the nominal conditions and the start and finish records
      for each VRAMP SEARCH section. If there is no VRAMP SEARCH tests in the records
      (rn_start to rn_finish) it will find the Nominal frequency and Nominal
      Values which are closest to the Nominal global values.

      The following add_cal_pout function will calculate the Ref Pout and @ rated_power
      data based on these nominal conditions.

      Parameters:
         rn_start  : first record index number of the self.data dictionary to search
         rn_finish : last record index number of the self.data dictionary to search

      Returns :
          vramp_search_sections :
             A list of 3 element lists. One per VRAMP SEARCH section
             [ [ [ nom_freq_list] [ nom_value_list ] ], rn_start, rn_finish ] ... ]
            (if no VRAMP SEARCH found then the list contains a single 3 element list ) '''


      if 'Freq(MHz)' not in self.data: return


      # Get a list of vramp search sections.
      # record the start and finish record number for each section
      vramp_search_sections = []
      rns = rn_start
      rnf = rn_start
      vrmp_search = False

      if 'section' in self.data:
             sectionnum = self.data['section'][rns]

      for rn in range(rn_start, rn_finish ):
          if self.data['TestName'][rn] == self.vramp_search_testname:
             vramp_search_sections.append( [ None, rns, rnf+1, vrmp_search, [ self.data['linenumber'][rns], self.data['linenumber'][rnf]] ] )
             rns = rn
             vrmp_search = True
#             print '(get_nom_conditions) found vramp search at rn=', rn


          # if we find a new section header in the log file then start a new vrmap_search_section
          if 'section' in self.data:
             sn = self.data['section'][rn]
             if sn != '' and sn != sectionnum :
                vramp_search_sections.append( [ None, rns, rnf+1, vrmp_search, [ self.data['linenumber'][rns], self.data['linenumber'][rnf]] ])
                rns = rn
                vrmp_search = False
                sectionnum = sn

          rnf = rn
      vramp_search_sections.append( [ None, rns, rnf+1, vrmp_search, [ self.data['linenumber'][rns], self.data['linenumber'][rnf]] ])




      for vss_idx,vss  in enumerate( vramp_search_sections ):

#              print '(get_nom_conditions) looping round the vramp_search_sections'

              
              rns = vss[1]
              rnf = vss[2]
              vrs = vss[3]

              nom_freq_list = []
              nom_found_value_list  = []



              # make up a fresh list of frequencies that are in the this section of the self.data[]
              del  self.values_dict[ 'Freq(MHz)']
              self.add_values_dict('Freq(MHz)', rns,rnf )

              new_nom_colname_list = []
              for i,n in enumerate( self.nom_colname_list ):
                  if n in self.values_dict:
                     del  self.values_dict[ n ]
                  self.add_values_dict(n, rns,rnf )
#                  print  '(get_nominal_conditions)  values_dict: ', n , len(self.values_dict[n]), self.values_dict[n] 
                  if len(self.values_dict[n]) >= 1:  val0 = self.values_dict[n][0]
                  else:                              val0 = None
                  if val0 != None:
                      new_nom_colname_list.append( n )

              self.nom_colname_list = new_nom_colname_list

              # 1
              # Find out which frequencies were present in the log file, and find the frequency which is closest to the center of the
              # band, (and make sure the count for this frequency is high enough)
              done_lb = False
              done_hb = False
              for kidx,k in enumerate( self.freq_sub_band_list) :
                   nom_freq = -1
                   # get the center of band frequency, this will be the nominal freq
                   flw = k[1]
                   fup = k[2]
                   fmid = (flw+fup)/2.0
                   subbandname = k[0]


                   if vrs:
                          # if doing a vramp search then we dont need to look through the data for the most common freq
                          # instead we will use the frequency that was used for the vramp search (record number = rns )

                          # if this freq lies within the current band then we'll use it else set nom_freq to -1

                          freq = self.data['Freq(MHz)'][rns]
                          if kidx == self.get_subband_idx_from_freq( freq ):
                               nom_freq = freq
                          else:
                               nom_freq = -1

                   else:



                #          print '(add_cal) looking for values in values_dict that most closely match', fmid

                           fmin_diff_i = 0
                           fdiff = []
                           inband_freq_count = 0
                           for i,f in enumerate( self.values_dict[ 'Freq(MHz)' ] ):
                                 if f == None : continue
                                 fdiff.append(None)
                                 fdiff[i] = abs(f - fmid)
                                 if fdiff[i] < fdiff[ fmin_diff_i ]:
                                    fmin_diff_i = i
                                 if  flw <= f <= fup  and self.values_dict_count[ 'Freq(MHz)' ][i] > 5:
                                      inband_freq_count +=1

                #                print '(add_cal)             ... trying', f, i, fmin_diff_i, ' inband_freq_count=', inband_freq_count, fdiff[i],  fdiff[ fmin_diff_i ]
                           # fmin_diff_i = index for freq that is closest to midband

                           # if the number of frequencies within the band is less than three then there is not enough to make a proper Ref Pout test

                           #
                           if inband_freq_count >=1:
                               nom_freq = self.values_dict[ 'Freq(MHz)' ][ fmin_diff_i ]

                               # if we have already found 3 frequnecies inside our sub band then do not calculate the Ref Pout for the entire band.
                               if nom_freq < 1200 :
                                  if k[0] == 'LB' and done_lb: nom_freq = -1
                                  done_lb = True
                               else:
                                  if k[0] == 'HB' and done_hb: nom_freq = -1
                                  done_hb = True
                           else:
                               nom_freq = -1

                   nom_freq_list.append( nom_freq )



              # 2.
              # For each column name in the nom_match_name_list, go through the values to find the
              # value which most closely matches the nominal value listed in the nom_match_value_list

              for i,n in enumerate( self.nom_colname_list ):

                if vrs:

                        # if doing vramp search then use the nominal value from the vramp search record.
                        nom_found_value_list.append( self.data[ n ][rns] )

                else:
             
                        if n in  self.values_dict:
                          vlist = self.values_dict[ n ]
                          vcount = self.values_dict_count[ n ]


                          try:
                             target_value = float( self.nom_target_value_list[i])
                          except Exception:
                             # add the first value from the value_dict
                #             nom_found_value_list.append( vlist[0] )

                             nom_found_value_list.append( None )

                             continue

                          closest_ix = 0

#                          print '(get_nom_conditions) n=%s, closest_ix=%s' % ( n , closest_ix )
#                          print '(get_nom_conditions)             target_value=', target_value
#                          print '(get_nom_conditions)             vlist[closest_ix]=',  vlist[ closest_ix ] 
 
                          try:
                              vdiff      = abs( float( vlist[ closest_ix ]) - target_value )
                              for ix, v in  enumerate( vlist ):
                                 # find the difference between this value and the target value
                                 # if its less than the current minimum then make this one the new min
                                 if abs( float( vlist[ ix ] ) - target_value) < vdiff and  vcount[ ix ] > 10:
                                      closest_ix = ix
                                      vdiff = abs( float( vlist[ ix ] ) - target_value)
                          except: 
                                 pass

                          nom_found_value_list.append( vlist[ closest_ix ])
                        else:
                          nom_found_value_list.append( None )




#              self.nom_found_value_list = nom_found_value_list[:]





#             print '\n    (get_nom_conditions) using nominal conditions:\n        ',
#              for ix, n in enumerate( self.nom_colname_list):
#                if n in  self.values_dict:
#                    print '(add_cal_pout_data)     %10s  target=%10s found=%10s' % ( n, self.nom_target_value_list[ix], nom_found_value_list[ix] )
#                    try:
#                        print '%s=%s ' % ( n, nom_found_value_list[ix] ),
#                        pass
#                    except Exception:
#                       pass
#              print ''


#              print '    (get_nom_conditions)  nom_freq_list ', nom_freq_list, rns, rnf

              vramp_search_sections[ vss_idx ][0] = [ nom_freq_list[:] , nom_found_value_list[:] ]

      print '\n  (get_nom_conditions) List of different nominal condition sections. New Vramp Search and new section in logfile will cause a new conditions section'
      print '     "[[[ freq ... ] ,  [ vswr, phase, temp, vbat, pin, reg ]], rns, rnf, Vramp_search, [ line_stt, line_fin ]]"'
      for i  in vramp_search_sections:
         print '     ', i
      print ''

      return vramp_search_sections




    ###################################################################
    def get_subband_idx_from_freq( self, freq ):
       ''' Finds the sub-band index associated with a given frequency
       It inputs the freq and searches the self.freq_sub_band_list to find
       which sub-band the freq is in. It returns an index into the self.freq_sub_band_list
       (between 0 and 3)

       Paramaters :
          freq :   Frequency in MHz

       Returns : index into self.freq_sub_band_list (0 to 3) indicating
                 the band that the frequency is most close to'''

#     self.freq_sub_band_list  = [ ['GSM850' , 824, 848] ,        \
#                                  ['EGSM'   , 880, 914] ,        \
#                                  ['DCS'    , 1710.2, 1784.8],   \
#                                  ['PCS'    , 1850.2, 1909.8],   \
#                                  ['LB'     , 820, 915],         \
#                                  ['HB'     , 1710, 1910],       \
#                                ]

       for i, sb in enumerate( self.freq_sub_band_list ):
           if i == 3:                  # if we get to the 4th sub-band then return i
               return i
           sb_mid_freq = (self.freq_sub_band_list[i][2] + self.freq_sub_band_list[i+1][1])/2.0
           if freq < sb_mid_freq:      # this works for the first three sub-bands
               return i





    ###################################################################
    def add_ref_pout_data( self, rnl, rn_start, rn_finish, testname='Output Power & Efficiency', matchname='Vramp Voltage' ):
      ''' The purpose of this function is to add a 'Ref Pout(dBm)' and 'Pwr Variation' column data

          It calculates this for the current section only (i.e. for records between rn_start
          and rn_finish) and also only calculates for the current nominal condtions defined in parameter rnl.
          The processing is defined for each subband by the rnl parameter (using the self.nom_freq_list. (-1 means don't do)

          The processing is done using the center-of-band frequency as the reference condition, and also
          for calculates separately using the 'at-frequency' values (denoted with '2' in the name.

          It does the following:

          1) Mark records which match the nominal conditions EXACTLY with
                    self.data['nominal condition'][rn]   = 'N2.7_LB-EGSM900'  etc for center-of-band
                    self.data['nominal2 condition'][rn]  = 'N2.7_880'         etc for 'at-frequency'
                    
          2) For the records above which match EXACTLY, if they have a 'Pout(dBm)' value then save 
             the Pout value in a dict as the reference power (will become the 'Ref Pout' and 'Ref2 Pout' values):
                    vramp2pout[ nominal_condition_name ][1.315]  = 33.10245
                    vramp2pout[ nominal2_condition_name ][1.315] = 33.10245
             (sometimes the measurment record does not have a Pout value in which case done store vramp2pout dict)
             
          3) Go throug each record again and determine which nominal condition name applies to the measurement
            (at the end all record should have been assigned to one of the nominal conditon names. Should not be many None values)
                    self.data['nominal condition ref']  = 'N2.7_LB-EGSM900'
                    self.data['nominal2 condition ref'] = 'N2.7_880'

          4) Go through all the records again looking at its 'nominal condition ref' and 'nominal2 condition ref'
             and vramp voltage for the given measurement record. Lookup the the reference power in the
             vramp2pout dict:
                    self.data['Ref Pout(dBm)'][rn]  = vramp2pout[nominal_condition_name][vramp] 
                    self.data['Ref2 Pout(dBm)'][rn] = vramp2pout[nominal2_condition_name][vramp]
        
             If there was 'Ref Pout' but no 'Ref2 Pout' then copy 'Ref Pout' to 'Ref2 Pout'
             
             
          5) At the same time as doing 4) create 'Pwr Variation' data 
                    self.data['Pwr Variation(dB)'][rn]  =  self.data['Pout(dBm)'][rn] - self.data['Ref Pout(dBm)'][rn]
                    self.data['Pwr2 Variation(dB)'][rn] =  self.data['Pout(dBm)'][rn] - self.data['Ref2 Pout(dBm)'][rn]

          This function gets run twice once for Power and Effeicincy tests and once for AMAM Distortion tests as
          defined by the 'matchname' parameter. This is required as the vramp2pout dict needs to be defined differently
          using 'Step' (1-40) for AMAM Distotion Tests, and using Vramp voltage (0.000-1.795) for reugular Power and 
          Efficiency tests 

          Paramaters:
              rn_start  : first record index number of the self.data dictionary to search
              rn_finish : last record index number of the self.data dictionary to search
              testname  : Type of test that will be used to extract Pout data, (usually Pwr&Eff or AMAM)
              matchname : Type of Xaxis used for calculating the pwr vs vam/vramp (usualy Vramp or Step)

          Returns:  None

          Updates:  adds new ref pwr data into  self.data[ 'Ref Pout(dBm)' ]
                    '''




      if 'TestName' not in self.values_dict             :  return
      if testname not in self.values_dict[ 'TestName' ] :  return


      print '\n(add_cal_pout_data) DOING matchname ', matchname, rn_start, rn_finish
      print ' rnl=', rnl

      if matchname == 'Step':
         matchname_str = 'AMAM Staircase'
      else:
         matchname_str = 'Vramp'

     # 3.
      # Go through all the records looking for the Power and Efficiency records that match the nominal conditions
      # and save away the vramp pout in a vramp2calpout dict.
      # (if there weren't any, look for PSA test results instead)



      # Nominal Center of Band Condition and Reference Power for Center Frequency of Band tests
      self.add_new_column( 'nominal conditions' )
      self.add_new_column( 'nominal conditions ref' )
      self.add_new_column( 'nominal conditions rn' )    # This is a column to indicate which nominal test record number (rn) is associated with this test.

      self.add_new_column( 'Ref Pout(dBm)' )
      self.add_new_column( 'Pwr Variation(dB)' )

      # Nominal Conditions and Reference Power for exact frequency tests
      self.add_new_column( 'nominal2 conditions' )
      self.add_new_column( 'nominal2 conditions ref' )
      self.add_new_column( 'nominal2 conditions rn' )    # This is a column to indicate which nominal test record number (rn) is associated with this test.

      self.add_new_column( 'Ref2 Pout(dBm)' )
      self.add_new_column( 'Pwr2 Variation(dB)' )
      
      
      current_nominal_condition_root_name = rnl[2]
      
      # get rid of any '.' characters as these interfer with the id name used in the Tk list boxes!!!! 
      current_nominal_condition_root_name = re.sub('\.',',',current_nominal_condition_root_name)
      



      multi_warn_done = False
      rpc = {}
      test_count = 0
      rated_power_count = 0
      ref_pout_count    = 0

#       print '(add_cal) self.nom_freq_list', self.nom_freq_list
#       print '(add_cal) self.freq_sub_band_list', self.freq_sub_band_list 

      vramp2pout = {}
      vramp2rn   = {}


      debugline = 10013

      for fn, fbl in zip( self.nom_freq_list, self.freq_sub_band_list ):
         if fn < 0:   continue     # a negative freq signifies that there were no tests found at a freq within the subband
         flw = fbl[1]   # lower freq of the subband
         fup = fbl[2]   # upper freq of the subband
         subbandname = fbl[0]

         nominal_condition_name = current_nominal_condition_root_name + '_' + subbandname


         subband_rn_count = 0

         debug1 = 0
         debug2 = 0
         debug3 = 0
         debug4 = 0

         lcount = 0


         # First go through all records checking to see that the record matches the current nominal conditions (from rnl)
         # If it matches to the center of band frequency then add the condition name to the 'nominal conditions' column
         #    and save the vramp voltage (or amam step) in the vramp2pout[ nominal_condition_name ] dict
         # If it matches to the spot frequency then add the condition name to the 'nominal2 conditions' column
         #    and save the vramp voltage (or amam step) in the vramp2pout[ nominal2_condition_name ] dict

         for rn in range( rn_start, rn_finish ):

            if  self.data['Sub-band'][rn] != subbandname or self.data['nominal2 conditions'][rn] != None: continue            

            if  self.data[matchname][rn] != None :
            
              if self.data['Pout(dBm)'][rn] != None :
                  rn_pout  = self.data['Pout(dBm)'][rn]
              else:
                  rn_pout = None        
                  continue
                  
              subband_rn_count += 1

              # get the vramp voltage if we can (skip this record if we dont find a valid vramp)
              try:
                 rn_vramp = '%0.3f' % float(self.data[ matchname ][rn])
              except Exception:
                 continue





              # Check to see that the conditions of this record are the same as the rnl nominal conditions
              match_found = True
              missing_nom = False
              for ix,n in enumerate( self.nom_colname_list ) :
                 rn_val  = self.data[ n ][rn]
                 nom_val = self.nom_found_value_list[ix]



                 # check to see we have all the nom conditions
                 # if not then we will fill in the missing nom values
                 # when we get a match on all the others,
                 if nom_val == None:
                    missing_nom = True
                    continue

                 if rn_val != nom_val:

                    match_found = False
                    break


              # check that the freq is within limits
              if match_found and not (flw <= self.data['Freq(MHz)'][rn] <= fup) :
                  match_found = False



              if match_found :                    

                    # Save the name of the nominal conditions in the self.data[]
                                        
                    # If we have the frequency of this record matches exactly with thw nominal freq
                    # save the nominal cond name 
                    rnfreq = self.data['Freq(MHz)'][rn]
                    if int(rnfreq) == int(fn) :
                        self.data['nominal conditions'][rn] = nominal_condition_name
                        
                        if rn_pout != None :
                            if  nominal_condition_name not in vramp2pout:
                                vramp2pout[nominal_condition_name ] = {}
                                vramp2rn[nominal_condition_name]    = {}                          
                            # warn the user if this nominal vramp value has been defined before
                            if not multi_warn_done and rn_vramp in vramp2pout[nominal_condition_name ]:
                                print '*** warning *** (add_ref_pout_data) multiple power and efficiency tests were run under the same nominal conditions, using the last set of data found'
                                multi_warn_done = 1
                            vramp2pout[nominal_condition_name ][ rn_vramp ] = rn_pout
                            vramp2rn[nominal_condition_name][ rn_vramp ] = rn

                    # When the frequency does not match then save away the name as nomina2 condition name
                    nominal2_condition_name = '%s_%d' % ( current_nominal_condition_root_name, int(rnfreq) )
                    self.data['nominal2 conditions'][rn] = nominal2_condition_name
                    
                    if rn_pout != None:
                        if nominal2_condition_name not in vramp2pout:
                            vramp2pout[nominal2_condition_name ] = {}
                            vramp2rn[nominal2_condition_name]    = {}
                        # warn the user if this nominal vramp value has been defined before
                        if rn_pout != None and not multi_warn_done and rn_vramp in vramp2pout[nominal2_condition_name ]:
                          print '*** warning *** (add_ref_pout_data) multiple power and efficiency tests were run under the same nominal conditions, using the last set of data found'
                          multi_warn_done = 1
                        if rn_pout != None:
                            vramp2pout[nominal2_condition_name ][ rn_vramp ] = rn_pout
                            vramp2rn[nominal2_condition_name][ rn_vramp ] = rn
                   
                    
                    

                    
                    # mark this test record as a test run at nominal conditions

                    # this is a record that matches nominal conditions, but 1 or more
                    # nominal conditions are missing, therefore use the values from this record
                    # to set the nominal conditions
                    if missing_nom:
                        for ix,n in enumerate( self.nom_colname_list ) :
                           rn_val  = self.data[ n ][rn]
                           nom_val = self.nom_found_value_list[ix]
                           if nom_val == None:
                               self.nom_found_value_list[ix] = rn_val
                        missing_nom = False
             
                        
              ln = self.data['linenumber'][rn]
#               if self.data['linenumber'][rn] == debugline:
#                   print '@1 %(ln)s  %(nominal_condition_name)s %(nominal2_condition_name)s ( %(rn_pout)s %(rn_vramp)s )' % locals() 
#         print '(add_cal_pout_data) DOING freq=' , matchname_str, fn, vramp2rn

         # Dont bother going any further with this subband if there are no measurements made within this band
         if subband_rn_count == 0:
            continue
                      
#          for cn in   vramp2pout:
#                 print '@- vramp2pout dict key ', cn 
  



#          if nominal_condition_name in vramp2pout:
#              for v in vramp2pout[ nominal_condition_name ]:
#                 print '  freq=%10s    subband=%15s  vramp=%10s vramp2calpout%10s' % (fn, fbl, v, vramp2pout[nominal_condition_name][v])





         # Go round all the records again marking each record with one of the nominal conditions
         # make a determination as to which nominal condition applies to each and every record

         subband_rn_count = 0
        
         for nom_cond_type in ['nominal conditions ref', 'nominal2 conditions ref']:
#             print 'QQQQ (add_ref) nom_cond_type=', nom_cond_type
             for rn in range( rn_start, rn_finish ):

                if  self.data['Sub-band'][rn] != subbandname or self.data[nom_cond_type][rn] != None: continue                
                if  self.data[matchname][rn] :
                   subband_rn_count += 1    

                   rnfreq = self.data['Freq(MHz)'][rn]
                   
                   # find the appropriate condition name
                   if nom_cond_type == 'nominal conditions ref':
                       nominal_condition = nominal_condition_name
                   else:
                       nominal_condition = '%s_%d' % ( current_nominal_condition_root_name, int(rnfreq) )
                        
                   # Go through all the prime_condition_variables 
                   # (those variables which differ in their nominal conditions) 

                   match = True
                   for i,cvn in  enumerate( self.nom_colname_list ):
                        cvv = rnl[3][i]
                        if cvv != None:
                            
                            rnv = self.data[cvn][rn]

                            # We've found a condition variable which is different
                            
                            if cvn == 'Vbat(Volt)':                    
                               if cvv < 3.0 and rnv < 3.0:
                                   match = True
                               elif cvv >= 3.0 and rnv >= 3.0:
                                   match = True
                               else:
                                   match = False
                                   break  
                            ## elif ....   TBD  ADD MORE CONDITIONS HERE
                            
                        if not match: break                                     
                   if match :
                        self.data[ nom_cond_type ][rn] = nominal_condition
        
        
                ln = self.data['linenumber'][rn]
#                 if self.data['linenumber'][rn] == debugline:
#                   print '@2 %(ln)s  nominal_condition=%(nominal_condition)s nom_cond_type=%(nom_cond_type)s match=%(match)s' % locals() 

        
        
         if vramp2pout == {} :
             print '\n*** WARNING *** (add_ref_pout_data) [%s,%s] (%s) No data was found that matched the nominal conditions at the freq=%s,\n    therefore there will not be any \'Ref Pout\' data or any \'@ Prated\' for this sub-band freq' % ( rn_start, rn_finish, matchname_str, fn)
             print '    Make sure there is data in the logfile that meets the following condtions:'
             print '             %20s = %s' % ( 'Linenumber range' , [ self.data['linenumber'][rn_start], self.data['linenumber'][rn_finish-1]] )
             print '             %20s = %s' % ( 'Freq(MHz)' , fn )
             print '             %20s = %s' % ( 'TestName' , testname )
             for ix,n in enumerate( self.nom_colname_list ) :
                 nom_val = self.nom_found_value_list[ix]
                 print '             %20s = %s' % ( n , nom_val )
             print '    It may help to split the logfile into separate high band and low band logfiles.'

             # We could not find any records that matched the nominal conditions therefore continue onto the next subband
             continue
             
         else:
             print "\n  (add_ref_pout_data) ) [ %s,%s] '%s' data which met the nominal conditions for freq=%s was found. Therefore 'Ref Pout' data will be calculated"  % ( rn_start, rn_finish, matchname_str,  fn)      
             pass
        
        
        
                   
         # Go through all the records looking at the 'nominal conditions ref' and 'nominal2 conditions ref' and
         # write the ref pout into 'Ref Pout(dBm)' and 'Ref2 Pout(dBm)' values by looking up the powr values in
         # vramp2pout dict
         for rn in range( rn_start, rn_finish ):
           if  self.data[matchname][rn]:

             pp_ref = -999
             pp2_ref = -999
                          # get the vramp voltage if we can (skip this record if we dont find a valid vramp)
             try:
                 rn_vramp = '%0.3f' % float(self.data[ matchname ][rn])
             except Exception:
                 continue

            
             rnfreq = self.data['Freq(MHz)'][rn]
             
             nominal_condition_name  = self.data['nominal conditions ref'][rn]
             nominal2_condition_name = self.data['nominal2 conditions ref'][rn]

             rn_pout  = self.data['Pout(dBm)'][rn]
            
#              ln = self.data['linenumber'][rn]
#              if self.data['linenumber'][rn] == debugline:
#                  print 'Current nominal_condition_name=%s  nominal2_condition_name=%s'% (nominal_condition_name,nominal2_condition_name)
#                  tf = nominal_condition_name in vramp2pout
#                  tf2 = nominal2_condition_name in vramp2pout
#                  print  tf , tf2, rn_vramp
#                  for cn in vramp2pout:
#                     print '========================='
#                     print     cn
#                     print '-------------------------'
#                     for v in vramp2pout[ cn ]:
#                          print ' %s freq=%10s    subband=%15s  vramp=%10s vramp2calpout%10s' % (cn, fn, fbl, v, vramp2pout[cn][v])
# 

             # first write the 'Ref Pout' and 'Pwr Variation' by using the 'center of band' condition                
             if nominal_condition_name in vramp2pout and \
                  rn_vramp in vramp2pout[nominal_condition_name ] :

                refpwr  =  vramp2pout[ nominal_condition_name ][ rn_vramp ]
                self.data['Ref Pout(dBm)'][rn]  =  refpwr
                self.data['nominal conditions rn'][rn] = vramp2rn[nominal_condition_name][ rn_vramp ]
                if rn_pout != None:
                    self.data['Pwr Variation(dB)'][rn] = rn_pout - refpwr


             # second write the 'Ref2 Pout' and 'Pwr2 Variation' by using the 'at frequency' condition
             if nominal2_condition_name in vramp2pout and \
                  rn_vramp in vramp2pout[nominal2_condition_name ] :

                refpwr  =  vramp2pout[ nominal2_condition_name ][ rn_vramp ]
                self.data['Ref2 Pout(dBm)'][rn]  =  refpwr
                self.data['nominal2 conditions rn'][rn] = vramp2rn[nominal2_condition_name][ rn_vramp ]
                if rn_pout != None:
                    self.data['Pwr2 Variation(dB)'][rn] = rn_pout - refpwr
                    
                    # if for this record the 'Ref2 Pout' exists but the 'Ref Pout' does not exist
                    # then this must be a measurement made with a spot frequency vramp search
                    # in this case provide a fall back 'Ref Pout' value by copying it from the 'Ref2 Pout'
                    if self.data['Ref Pout(dBm)'][rn] == None:
                        self.data['Ref Pout(dBm)'][rn]  =  refpwr
                        self.data['Pwr Variation(dB)'][rn] = rn_pout - refpwr
            


      for n in  rpc:
         self.add_values_dict( n )
         if n not in self.value_dict_names:
            self.value_dict_names.append( n )





    ###################################################################
    def add_rated_power_values( self, rn_start, rn_finish ):
        '''Look through all the vramp searches, look at the ones that match the nominal condition specified by rnl
        
        Go through all the vramp searches
            - Create new @ rated power columns named @34.2_N2.7_880, and @34.2_N2.7_LB-DCS850 from (nom cond ref and nom2 cod ref)
            - Save the vramp voltage associated with each of these. (create a dictionary rated_power_cond) 
        Go through all records, and for each rated_power_cond that matches the nominal_condition_ref and nominal2_condition_ref
            - write a 1 if the vramp matches, or a 0 if it doesnt
        Go through all the rated power values from the prd and copy across the rated powers from above to the legacy rated power columns
        so as not to break all the ARG scripts
        ''' 
        
        
        if 'nominal conditions ref'  not in self.data or \
           'nominal2 conditions ref' not in self.data: 
            return
            
        self.add_new_column( '@Prated' )
                
        rated_power_cond = {}
        
        
        for rn in range( rn_start, rn_finish ):
            if self.data['TestName'][rn] == 'VRamp Search' :
                tpwr = '%0.1f' % self.data['TRP Target Power(dBm)'][rn]
                if tpwr[-1] == '0': tpwr = tpwr[:-2]
                tvramp =  '%0.3f' % float( self.data[ 'Vramp Voltage' ][rn])
                subband = self.data['Sub-band'][rn]
                for cn in  ['nominal conditions ref', 'nominal2 conditions ref']:
                
                   # For the 'nominal conditions ref' make sure that the frequency for this vramp search is
                   # at the center of band, ie ignore this vramp search if it is not run at the center of band frequency 
                   # (However for 'nominal2 conditions ref' is an at frequecny condition so don't skip it, we want 
                   # it added to the rated_power_cond regardless)
                   if cn == 'nominal conditions ref':
                      idx = self.sub_band_list[:4].index( subband )
                      cob_freq = self.freq_sub_band_list[idx][3]
                      rnfreq = self.data['Freq(MHz)'][rn]
                      freq_diff = abs( rnfreq - cob_freq )
#                      print '&&&  ( %(subband)s %(idx)s : %(cob_freq)s )  rnfreq=%(rnfreq)s freq_diff=%(freq_diff)s' % locals() 
                      if freq_diff > 5 :
                          continue
                      
                   ncr = self.data[cn][rn]
                   rpncr  = '@%(tpwr)s_%(ncr)s' % locals()
                   vlst =  [ rpncr, tpwr, [tvramp], subband ]
                   
                   
                   if not ncr in rated_power_cond:
                      rated_power_cond[ ncr ] = {}
                      
                   if rpncr not in rated_power_cond[ ncr ]:
                       vlst =  [ rpncr, tpwr, [tvramp], subband ]

                   else:
                      # OK we've seen this prncr before so add the vramp to the list
                      # not this only happens when two or more vramp searches are done
                      # under exactly the same conditions and target power level 
                      
                      vlst = rated_power_cond[ ncr ][ rpncr]
                      try:
                        vidx = vlst[2].index( tvramp )
                      except:
                        vlst[2].append( tvramp )
                   
                   rated_power_cond[ ncr ][ rpncr] = vlst 
    
    
        for key in rated_power_cond:
            vdict = rated_power_cond[ key ]
            for vkey in vdict:
                self.add_new_column( vkey )
                
#            print '@@@@@@  [ %(key)-10s ]  =  (  %(vdict)s )' % locals()


        # Go through all the records looking and through all the rated_power_cond keys looking for measurements
        # that have the same nominal conditions and have the same vramp voltage. These are the rated power measurements
        # and they will be marked with 1, measurements that dont match with vramp will be marked with a 0
        i = 0
        for rn in range( rn_start, rn_finish ):
            try:
               rn_vramp =  '%0.3f' % float( self.data[ 'Vramp Voltage' ][rn])
            except:
               continue
        
          
            for ncr in rated_power_cond:
                for vlst in rated_power_cond[ncr]:
                    npc_vramp = rated_power_cond[ncr][vlst][2]
                    rpncr     = rated_power_cond[ncr][vlst][0]
                    tpwr      = rated_power_cond[ncr][vlst][1]
                    for cn in  ['nominal conditions ref', 'nominal2 conditions ref']:
                        rn_ncr = self.data[cn][rn]
                        if ncr == rn_ncr :
                            vr_match = 0
                            for vr in npc_vramp:
                                if rn_vramp == vr :
                                    vr_match = 1
                                    break

                            self.data[rpncr][rn] = vr_match
                            if vr_match == 1:
                                self.data['@Prated'][rn] = tpwr
                            i += 1
                                
                                



        # Make sure the rated_power_values entries are all 4 element list (one power value per sub-band))
        # If not then make them so
        for n in self.rated_power_values:
             rpwr_lst = self.rated_power_values[ n ]
    
    #         print '(add_cal_pout_data)  self.rated_power_values[%s] = <%s>' % (n , rpwr_lst)
             if not isinstance( rpwr_lst , types.ListType ):  # a single value gets replicated 4 times
                rpwr_lst = [ rpwr_lst,rpwr_lst,rpwr_lst,rpwr_lst ]
             elif len(rpwr_lst) == 1:
                rpwr_lst = [ rpwr_lst[0],rpwr_lst[0],rpwr_lst[0],rpwr_lst[0] ]
             elif len(rpwr_lst) == 2:
                rpwr_lst = [ rpwr_lst[0],rpwr_lst[0],rpwr_lst[1],rpwr_lst[1] ]
             elif len(rpwr_lst) == 4:
                pass
             else:
                print '*** ERROR *** (add_cal_pout_data) rated_power_value[ %s ] = %s, is not defined correctly, it should be a 1,2 or 4 item list or a single value' % ( n, self.rated_power_values[ n ] )
             self.rated_power_values[ n ] = rpwr_lst
    




        for n in self.rated_power_values:  
            self.add_new_column( n )




#         print '----------------------------------------'
#         print self.rated_power_values
#         print '----------------------------------------'
        # Build a mapping table for copying the rated_power_cond (from the log file)
        # to the rated_power_values column names (from the PRD)
        
        rated_power_map = {}
        for rp_prd in self.rated_power_values:             #  gets   rp_prd = '@ _29_28'  -> [29, 29, 28, 28]

            pwrs_prd = self.rated_power_values[ rp_prd ]
#            rated_power_map[ rp_prd ] = [ [],[],[],[] ]    #  defines rated_power_map[ '@ _29_28' ] = [ [],[],[],[] ]
         
            for rpk in rated_power_cond:                   # gets a key like '@29_N3,5_LB-EGSM900': -> ['@29_N3,5_LB-EGSM900', '29', '0.510', 'LB-EGSM900']
               
               for rpkk in rated_power_cond[rpk]:          # gets a key like '@29_N3,5_LB-EGSM900': 
                   vals = rated_power_cond[rpk][rpkk]      # gets vals = ['@29_N2,7_915', '29', '0.500', 'LB-EGSM900']
                   
                   try:
                      # test whether this rated_power_cond[rp_prd] is in the sub_band_list
                      sbidx = self.sub_band_list.index( vals[3] )
                   except: 
                      sbidx = -1

                   if sbidx >= 0:
                        pwr_prd = pwrs_prd[sbidx]
                        
                        # if the prd rated power is None for this subband then skip the mapping
                        if pwr_prd == None:  continue
                          
                        pwr_prd = '%0.1f' % pwr_prd
                        if  pwr_prd[-1] == '0': pwr_prd = pwr_prd[:-2]
                        if pwr_prd == vals[1]:
                            if vals[3] in  rpkk:
                                if rp_prd not in rated_power_map:
                                    rated_power_map[ rp_prd ] = [ [],[],[],[] ]    #  defines rated_power_map[ '@ _29_28' ] = [ [],[],[],[] ]
    
                                rated_power_map[ rp_prd ][ sbidx ].append(  rpkk )
                 
#             if rp_prd in rated_power_map:
#                 print '    rated_power_map[', rp_prd, '] ', rated_power_map[ rp_prd ]
        

        # go through all the records looking for the rated_power_values 
        # (defined in the prd) and the rated_power_cond (defined above)
        for rn in range( rn_start, rn_finish ):

            subband = self.data['Sub-band'][rn]

            if subband == None:  
                continue
            
            sbidx = self.sub_band_list.index( subband )

            for rpm in rated_power_map:            
                rpml =  rated_power_map[ rpm ][sbidx]
                
                for ncr in rpml:
                   val = self.data[ncr][rn]
                   if val == 1:
                       self.data[ rpm ][rn] = val




        

    ###################################################################
    def add_cal_pout_data_obsolete( self, rn_start, rn_finish, testname='Output Power & Efficiency', matchname='Vramp Voltage' ):
      ''' The purpose of this function is to add a 'Ref Pout(dBm)' column data
          and '@ rated pwr' column data marking tests which were done at the rated power.

          It calculates this for the current section only (i.e. for records between rn_start
          and rn_finish). It assumes that the nominal conditions have been previoulsy calculated
          (get_nom_conditions) and they have been defined in self.nom_found_value_list,
          self.nom_name_list and self.nom_freq_list.

          It does the following:

          a) Make the rated powers extend over all 4 subbands (self.rated_power_values[]).
          b) Make a lookup table (vramp2calpout) between vramp voltages (or VAM) and the power
               out under nominal conditions (vramp2calpout). This is used for the 'Ref Pout(dBm)' column.
          c) For each of the rated powers find the nearest vramp value (rpc) and the nearest power (rpp).
          d) Go through all the records in the range and add the 'Ref Pout' column data. This is done by
               looking up the vramp (or VAM) voltage in the vramp2calpout dict. Also for each rated power value
               add a @ rated power column and make it =1 when the vramp file (and thus ref pout) is the same
               the value in the rpc dict.

          It does the above for each frequency defined in the self.nom_freq_list. (-1 means don't do)
          If a 'Vramp Search' command is used in the section it will use the rated power and nominal conditions.

          Paramaters:
              rn_start  : first record index number of the self.data dictionary to search
              rn_finish : last record index number of the self.data dictionary to search
              testname  : Type of test that will be used to extract Pout data, (usually Pwr&Eff or AMAM)
              matchname : Type of Xaxis used for calculating the pwr vs vam/vramp (usualy Vramp or Step)

          Returns:  None

          Updates:   adds new ref pwr data into  self.data[ 'Ref Pout(dBm)' ]
                     adds new rated power self.data[ '@rated_power_*' ]'''




      if 'TestName' not in self.values_dict             :  return
      if testname not in self.values_dict[ 'TestName' ] :  return


#     print '\n(add_cal_pout_data) DOING matchname ', matchname, rn_start, rn_finish

      if matchname == 'Step':
         matchname_str = 'AMAM Staircase'
      else:
         matchname_str = 'Vramp'

#      print '(add_cal_pout_data)  rn_start=%d  rn_finish=%d' % (rn_start, rn_finish)
#      print "(add_cal_pout_data)  len( self.data['linenumber'] )" , len( self.data['linenumber'] )
#      print "(add_cal_pout_data)  self.data['linenumber'][rn_start]  " , self.data['linenumber'][ rn_start ]
#      print "(add_cal_pout_data)  self.data['linenumber'][rn_finish] " , self.data['linenumber'][ rn_finish-1 ]


      # Make sure the rated_power_values entries are all 4 element list (one power value per sub-band))
      # If not then make them so
      for n in self.rated_power_values:
         rpwr_lst = self.rated_power_values[ n ]

#         print '(add_cal_pout_data)  self.rated_power_values[%s] = <%s>' % (n , rpwr_lst)
         if not isinstance( rpwr_lst , types.ListType ):  # a single value gets replicated 4 times
            rpwr_lst = [ rpwr_lst,rpwr_lst,rpwr_lst,rpwr_lst ]
         elif len(rpwr_lst) == 1:
            rpwr_lst = [ rpwr_lst[0],rpwr_lst[0],rpwr_lst[0],rpwr_lst[0] ]
         elif len(rpwr_lst) == 2:
            rpwr_lst = [ rpwr_lst[0],rpwr_lst[0],rpwr_lst[1],rpwr_lst[1] ]
         elif len(rpwr_lst) == 4:
            pass
         else:
            print '*** ERROR *** (add_cal_pout_data) rated_power_value[ %s ] = %s, is not defined correctly, it should be a 1,2 or 4 item list or a single value' % ( n, self.rated_power_values[ n ] )
         self.rated_power_values[ n ] = rpwr_lst




      # 3.
      # Go through all the records looking for the Power and Efficiency records that match the nominal conditions
      # and save away the vramp pout in a vramp2calpout dict.
      # (if there weren't any, look for PSA test results instead)

      self.add_new_column( 'Ref Pout(dBm)' )
      self.add_new_column( 'Pwr Variation(dB)' )
      for n in self.rated_power_values:
          self.add_new_column( n )
      self.add_new_column( 'nominal conditions rn' )    # This is a column to indicate which nominal test record number (rn) is associated with this test.

      multi_warn_done = False
      rpc = {}
      test_count = 0
      rated_power_count = 0
      ref_pout_count    = 0


      for fn, fbl in zip( self.nom_freq_list, self.freq_sub_band_list ):
         if fn < 0:   continue     # a negative freq signifies that there were no tests found at a freq within the subband
         flw = fbl[1]   # lower freq of the subband
         fup = fbl[2]   # upper freq of the subband
         subbandname = fbl[0]

#        print '(add_cal) freq',  fn

#        print '(add_cal) doing freq' , fn, matchname
#        print '(add_cal) ', self.nom_colname_list
#        print '(add_cal) subbandname=', subbandname
#        print '(add_cal) ', self.nom_found_value_list
#        print '(add_cal) self.nom_freq_list', fn, self.nom_freq_list
#        print '(add_cal) self.freq_sub_band_list', fbl, self.freq_sub_band_list
#        print '(add_cal) ', self.nom_found_value_list


         vramp2calpout = {}
         vramp2rn      = {}

         debug1 = 0
         debug2 = 0
         debug3 = 0
         debug4 = 0

         lcount = 0


         # If we have a VRAMP SEARCH we can imediately add the vramp voltage to the vramp2calpout table
         if self.data['TestName'][rn_start] == self.vramp_search_testname :
              vramp =  self.data['Vramp Voltage'][rn_start]
              pout  =  self.data['Closest Target Power(dBm)'][rn_start]
              vramp2calpout[ vramp ] = pout



         for rn in range( rn_start, rn_finish ):
            if  self.data[matchname][rn] != None and self.data['Pout(dBm)'][rn] != None :
#            if self.data['TestName'][rn] == testname and self.data[matchname][rn] != None and self.data['Pout(dBm)'][rn] != None :


              rn_pout  = self.data['Pout(dBm)'][rn]

              # get the vramp voltage if we can (skip this record if we dont find a valid vramp)
              try:
                 rn_vramp = '%0.3f' % float(self.data[ matchname ][rn])
              except Exception:
                 continue



              # check to see that the conditions are the same
              match_found = True
              missing_nom = False
              for ix,n in enumerate( self.nom_colname_list ) :
                 rn_val  = self.data[ n ][rn]
                 nom_val = self.nom_found_value_list[ix]



                 # check to see we have all the nom conditions
                 # if not then we will fill in the missing nom values
                 # when we get a match on all the others,
                 if nom_val == None:
                    missing_nom = True
                    continue

                 if rn_val != nom_val:

                    match_found = False
                    break


              # check that the freq is within limits
#             if match_found and not (flw <= self.data['Freq(MHz)'][rn] <= fup) :
              if match_found and self.data['Freq(MHz)'][rn] != fn :
                  match_found = False


              if match_found :
#                   print '(add_cal_pout_data) match found for fn=%s' % fn
                    if rn_vramp not in vramp2calpout:
                       pass
                    else:
                       if not multi_warn_done:
                          print '*** warning *** multiple power and efficiency tests were run under the same nominal conditions, using the last set of data found'
                          multi_warn_done = 1
                    vramp2calpout[ rn_vramp ] = rn_pout
                    vramp2rn[ rn_vramp ] = rn
                    # mark this test record as a test run at nominal conditions

                    # this is a record that matches nominal conditions, but 1 or more
                    # nominal conditions are missing, therefore use the values from this record
                    # to set the nominal conditions
                    if missing_nom:
                        for ix,n in enumerate( self.nom_colname_list ) :
                           rn_val  = self.data[ n ][rn]
                           nom_val = self.nom_found_value_list[ix]
                           if nom_val == None:
                               self.nom_found_value_list[ix] = rn_val
                        missing_nom = False

#         print '(add_cal_pout_data) DOING freq=' , matchname_str, fn, vramp2rn

         if vramp2calpout == {} :
             print '\n*** ERROR *** (add_cal_pout_data) [%s,%s] No %s data matched the freq=%s nominal conditions,\n    therefore there will not be any \'Ref Pout\' data or any \'@ rated power\' for this sub-band freq' % ( rn_start, rn_finish, matchname_str, fn)
             print '    Make sure there is data in the logfile that meets the following condtions:'
             print '             %20s = %s' % ( 'Linenumber range' , [ self.data['linenumber'][rn_start], self.data['linenumber'][rn_finish-1]] )
             print '             %20s = %s' % ( 'Freq(MHz)' , fn )
             print '             %20s = %s' % ( 'TestName' , testname )
             for ix,n in enumerate( self.nom_colname_list ) :
                 nom_val = self.nom_found_value_list[ix]
                 print '             %20s = %s' % ( n , nom_val )
             print '    It may help to split the logfile into separate high band and low band logfiles.'


         else:
             print "\n  (add_cal_pout_data) [ %s,%s] '%s' data which met the nominal conditions for freq=%s was found. Therefore 'Ref Pout' and '@ rated power' data will be calculated"  % ( rn_start, rn_finish, matchname_str,  fn)
#             print vramp2calpout


             
             pass


#         for v in vramp2calpout:
#           print '  freq=%10s    subband=%15s  vramp=%10s vramp2calpout%10s' % (fn, fbl, v, vramp2calpout[v])


         # 4.
         # Go through all the vramp and calpout values looking to see which ones match the target power defined in the self.rated_power_values list
         # New columns will be created which will flag which of the results match the rated_power vramp conditions
         rpc = {}
         rpp = {}
         rprn = {}

         for n in self.rated_power_values:

            rpc[ n ]  = None
            rpp [ n ] = None
            rprn[ n ] = None

            idx = self.get_subband_idx_from_freq( fn )
            ptarget = self.rated_power_values[ n ][idx]

#            print '(add_cal_pout_data) rated power', n
            if ptarget == None: continue


            if self.data['TestName'][rn_start] == self.vramp_search_testname :

                # For a VRAMP SEARCH section we will use the Target Search Power as the Rated Power value

                # if the rated power target is within 0.2dB of the VRAMP SEARCH TRP Target Power then we will use this vramp file for rated power
#                if  abs( ptarget - self.data['Closest Target Power(dBm)'][rn_start]) < 0.2:
                if  abs( ptarget - self.data['TRP Target Power(dBm)'][rn_start]) < 0.1:

                   rpc [ n ] =  '%0.3f' % float( self.data[ 'Vramp Voltage' ][rn_start])
                   rpp [ n ] =  self.data['Closest Target Power(dBm)'][rn_start]
                   rprn[ n ] =  rn_start

#                   print "   (add_cal_pout_data) for %s data, %7s(MHz) Rated Power '%s' is %0.1f(dBm)\n      The power for 'Vramp Search' on line %d is %0.3f(dBm) which is at a vramp of %sv" % (matchname_str, fn, n, ptarget, self.data['linenumber'][rn_start],rpp[n], rpc[n])
                   print "   (add_cal_pout_data) 'Vramp Search' %-14s found on line %d, %7s(MHz) Rated Power '%s' is %0.1f(dBm), Actual power found is %0.3f(dBm) which is at a vramp of %sv" % (matchname_str, self.data['linenumber'][rn_start], fn, n, ptarget, rpp[n], rpc[n])

            else:

                # If not a VRAMP SEARCH section we will find the rated power vramp/vam voltage based on the power vs vramp sweep data
                # don under nominal conditions

                # find the closest vramp2calpout value to the rated_power value
                # and form a new dict

                # go through all the vramps and see which one gives the nearest pout to the target power
                # the closest one above the target power wins
                vdiff = None
                for vrmp in vramp2calpout:

                  calpout = vramp2calpout[ vrmp ]
                  rn_nom  = vramp2rn[ vrmp ]


                  if self.data['TestName'][rn_start] != self.vramp_search_testname :
                     if 1==1 or calpout > ptarget :       # make it search for the nearest pout to the target power

                         if vdiff == None or abs( calpout - ptarget ) < vdiff:
                           vdiff = abs( calpout - ptarget )
                           rpc [ n ] = vrmp
                           rpp [ n ] = calpout
                           rprn[ n ] = rn_nom


                # Check whether the closest power found to the rated power is close enough,
                # if not we will not accept it and we will null out this rated power value
                if vdiff == None or abs( rpp[n] - ptarget ) > self.rated_power_tolerance :
                   print "*** ERROR *** (add_cal_pout_data) at %7s(MHz) NO rated power data was found for '%s' = %0.1f(dBm). The nearest power found is %s(dBm) which is at a vramp of %s (v)" % (fn, n, ptarget, rpp[n], rpc[n])
                   rpc[ n ]  = None
                   rpp [ n ] = None
                   rprn[ n ] = None

                else:
                   print "   (add_cal_pout_data) for %s data, %7s(MHz) Rated Power '%s' is %0.1f(dBm) nearest nominal power found is %0.3f(dBm) which is at a vramp of %sv" % (matchname_str, fn, n, ptarget, rpp[n], rpc[n])
                   pass


         # 5.
         # Go through the records a second time filling in all the Ref Pout values
         # and adding all the @ rated power columns, (1 when the Ref Pout is at the rated power,
         # a 0 if it doesn't match rated power)
         test_count = 0
         rated_power_count = 0
         ref_pout_count    = 0

         for rn in range( rn_start, rn_finish ):


           # check that the record frequency is with the correct band
           if (flw <= self.data['Freq(MHz)'][rn] <= fup) :
              test_count +=1
              vramp = None
              # if so then lookup the the calibrated power for the given vramp



              try:
                 vramp = '%0.3f' % float(self.data[ matchname ][rn])
                 self.data['Ref Pout(dBm)'    ][rn] = vramp2calpout[ vramp ]
                 ref_pout_count += 1
                 self.data['Pwr Variation(dB)'][rn] = self.data['Pout(dBm)'][rn] - vramp2calpout[ vramp ]

                 self.data['nominal conditions rn'    ][rn] = vramp2rn[ vramp ]
              except:
                 pass

#              print '(add_cal_pout_data) no look up -', self.data['Freq(MHz)'][rn],[rn,self.data[ 'linenumber' ][rn], self.data[ matchname ][rn], vramp ],vramp2calpout,self.data['Ref Pout(dBm)'    ][rn]

                 # if the vramp voltage matches one of the target powers mark the record

              if vramp != None and matchname=='Vramp Voltage':
                     for n in  rpc:

                         if vramp == rpc[n]:
    #                         self.data[ n ][rn] = vramp2calpout[ vramp ]
                              self.data[ n ][rn] = 1
                              rated_power_count += 1
                         else:
                              self.data[ n ][rn] = 0

#      print '     (add_cal_pout_data)  added     %d/%d  refpouts    and  %d/(%d*%s) @rated_power\'s' % (ref_pout_count, test_count, rated_power_count, test_count,len(rpc))



#      self.add_values_dict( 'Ref Pout(dBm)' )
#      self.add_values_dict( 'Pwr Variation(dB)' )
      for n in  rpc:
         self.add_values_dict( n )
         if n not in self.value_dict_names:
            self.value_dict_names.append( n )





    ###################################################################
    def add_vramp2pout_data( self, rn_start, rn_finish ):
      ''' Adds 'Adj Pwr Out(dBm)' data for all records that are not 'Pwr&Eff' tests
      It does this by recording all the pouts values for every Pwr&Eff test and then
      matching the conditions with non Pwr&Eff tests.
      
      Parameters:
           rn_start:    starting record to scan
           rn_finish:   last record to scan
      Updates:          self.data[ 'Adj Pwr Out(dBm)']'''

      # go through all the power and efficiency records andd build a lut to translate vramp voltage to pout
      # then go through all the power and efficiency records and write the pout data from the lut


      if 'TestName' in self.data  and  'Vramp Voltage' in self.data and  'Output Power & Efficiency' in  self.data['TestName']:
        pae_count = 0
        pae_cond_count = 0
        vramp2pout = {}
        self.add_new_column( 'Adj Pwr Out(dBm)' )
        for rn in range( rn_start, rn_finish ):
           if self.data['TestName'][rn] == 'Output Power & Efficiency' and self.data['Vramp Voltage'][rn] != None and self.data['Adj Pwr Out(dBm)'][rn] != None :
              pae_count += 1
              try:
                ls=[ str(self.data['Vramp Voltage'  ][rn]) ,
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
                pae_cond_count +=1
              except Exception:
                pass

#        print '(add_vramp2pout_data)   pae_count = %d    pae_cond_count = %d' % (pae_count, pae_cond_count)

        vramp_count = 0
        vramp_cond_count = 0

        for rn in range( rn_start, rn_finish ):
           if self.data['TestName'][rn] != 'Output Power & Efficiency' and self.data['Vramp Voltage'][rn] != None :
              vramp_count += 1
              try:
                ls=[ str(self.data['Vramp Voltage'  ][rn]) ,
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
                   vramp_cond_count += 1
 #                  print '   ', cond
              except Exception:
                pass

#        print '(add_vramp2pout_data)   vramp_count = %d    vramp_cond_count = %d' % (vramp_count, vramp_cond_count)





    ###################################################################

    def add_spurious_data( self, freq_thres=None, rn_start=None, rn_finish=None ):

        ''' Create new Spurious data columns containing the orginal spur data with data points
        closer than some frequency threshold removed
        
        Parameters:
            freq_thres:   Spurs which are Spur-Freq < freq_thres are removed
            rn_start:     Starting record number to scan
            rn_finish:    Last record number to scan
        Returns:          None
        Updates:          self.data[ 'Amplitude of Spur, no harmonic xxxMHz (dBm)'] '''


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


        for rn in range( rn_start, rn_finish ):

           num_spurtests += 1

           if self.data['TestName'][rn] == 'Spurious (ETSI full)'    or \
              self.data['TestName'][rn] == 'Spurious (ETSI reduced)' or \
              self.data['TestName'][rn] == 'Spurious (quick)'            :
              freq = self.data['Freq(MHz)'][rn]


              f = self.data['Frequency of Spur (MHz)'][rn]
              amp = self.data['Amplitude of Spur (dBm)'][rn]

              if amp != None and f != None:
                  harmonic_float  = float(f)/float(freq)
                  harmonic_int    = int( harmonic_float + 0.5 )
                  harmonic_dist   = harmonic_float - harmonic_int
                  freq_dist       = freq * abs( harmonic_dist )

                  if freq_thres == None:
                     freq_thres_tmp = self.get_spur_freq_thres_from_table( freq, harmonic_int )
                  else:
                     freq_thres_tmp = freq_thres


                  num_spurs_det +=1

                  if freq_dist < freq_thres_tmp :
                     amp = None

                  # force the 0 harmonic (DC) value to be a real value otherwise some filtered
                  # plots contain no non-None data and no plot is generated even though the test was done
                  if f < 1:
                     amp = self.harmonic_spur_min_amp
                     self.data['Amplitude of Spur (dBm)'][rn] = self.harmonic_spur_min_amp

              self.data[ cname ][rn] = amp



    ###################################################################

    def get_spur_freq_thres_from_table( self, freq, harmonic_int ):
        '''Used by (add_spurious_data) function to look up freq_thres from a lookup table
        Parameters:
            freq:           Fundamental frequency (MHz))
            harmonic_int:   Harmonic
        Returns:        
            rv:             freq_thres, frequency to be used for filtering the spur results'''

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

            txt = ""
            txt = txt + '\n---------------------------------------------------------------------------\n'
            txt = txt +  "Spurs frequency threshold table from file '%s'\n" % os.path.abspath(file2open)

            #print 'Harmonics   :' , row_headers
            txt = txt + '\nFreq :' + repr( column_headers )  + '\n'

            #pprint( self.spur_freq_filter_table )

            for r in row_headers:
               txt = txt + '            %2s : ' % r
               for c in column_headers[1:]:
                  key  =   str(c) + ' ' + str(r)
                  txt = txt +  ' %5s' % self.spur_freq_filter_table[ key ]
               txt = txt +  '\n'
            txt = txt +  '---------------------------------------------------------------------------\n'

            print txt

            try:     print >> self.spurlog, txt
            except:  pass

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
        ''' Find the value in the list which is closest to the value, and return the index
        
        Parameters:
            ilst:        List of values to choose from
            value:       Value to find closest in list
        Returns:
            mini:        Number from the list which is closest to 'value' '''

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
          '''Creates a new empty data column name if it doesnt already exist
          A new name is added to self.data[ name ] with an empty list with a length
          equal to the number of records (self.datacount)
          If the name already exists in self.data[ name ] then the length of the
          list is padded with None values to the length equal to the number of records
          (self.datacount)

          Parameter :
             name   : The name of the new column (key) to create in self.data[]
          Returns   : None
          Updates   : self.data[ name ]
          '''
          if not name in self.data:
            self.data[name]      = []

          # Then extend the data to be the current datacount length
          # extend it with empty None values
          try:
             rn_sum = self.datacount - len( self.data[name] )
          except:
             print '(add_new_column) *** ERROR *** self.datacount = %d self.data[%s]=%s ' % (self.datacount, name, self.data[name])


          self.data[name]   .extend( [None] * rn_sum )

    ###################################################################


    def nearest( self, num , roundnum, default ):
        '''Function to get the nearest quantized number.
           e.g.  self.nearest( 12.2,  5,  100 ) ->  10
                 self.nearest( None,  5,  100 ) ->  100

        Parameters:
           num      :  Number to convert
           roundnum :  Rounds to this nearest number
           default  :  If the num value is invalid (e.g. it was None, or could
                       not be converted with float() then return this number instead
        Returns
           The nearest quantized integer to the value num'''

#       print '(nearest)', num, type(num), roundnum, default

        if not num : return default

        try:
           num = float(num)
        except Exception:
           return default

        if num > 0: m = 1
        else:        m = -1
        return int(( abs(num) / float(roundnum) ) + 0.5 ) * int(roundnum) * m


    def get_vramp_voltage( self, filename ):
      '''Extract the vramp voltage from a vramp filename
      
      Parameters: 
          filename:    Filename to extract the voltage value
      Returns:
          voltage (float)
      '''

      x = re.search( r'\.(\d\.\d+)v_ramp.txt', filename )
      if x :
           n = x.groups()
           return float(n[0])
      else :
           return ''

    ###################################################################
    def get_vramp_filebase( self, filename ):
      '''Extract the vramp  filename
      
      Parameters: 
          filename:    vramp Filename
      Returns:
          basename of vrampfile
      '''


      if filename == None :  return ''
      x = re.search( r'.*\\(.*?_ramp.txt)', filename )
      if x :
           n = x.groups()
           return n[0]
      else :
           return ''

    ###################################################################
    def get_vramp_filename_data( self, rn ):
      '''Extract the vramp filename info

      # full_filespec = 'P:\\mike_askers_stuff\\ramps\\LBpwrsel11\\staircase-128us_ramp.txt'
      # full_filespec = 'L:\Testing\Chiarlo_EDGE\EDGE_sources\ATR_LB\EDGELB29_vam.wv'
      # full_filespec = 'G:\ATR_Classico\Ramp_files\ramps_classicoV6_9Jul08\LB_pwrsel00\classicoV6.1.50v_ramp.txt'
      #
      #      vramp_release, hb_lb, seg, voltage, full_filespec, pcl_level = self.get_vramp_filename_data( filename )
      
      Parameters: 
          rn:    Record number to use
      Returns:
          vramp_release:
          hb_lb:
          seg: 
          voltage:
          full_filespec:
          pcl_level:
      '''

      full_filespec = ''
      pcl_level     = ''

      if 'Vramp Dir1' in self.data and self.data['Vramp Dir1'][rn] != '':
         full_filespec =     self.data['Vramp Dir1'][rn] +   self.data['Vramp Dir2'][rn] +  self.data['Vramp Dir3'][rn] + self.data['Vramp File'][rn]

      elif  'Vramp File' in  self.data and  self.data['Vramp File'][rn] != '':
         full_filespec = self.data['Vramp File'][rn]

      if full_filespec == None:
#           print '(get_vramp_filename_data) found None', rn
           return '','','','', full_filespec, ''

      x = re.search( r'(ramps_[^\\]+)?\\(LB|HB)?_?pwrsel([01]+)?.*?(\d\.\d+)?v?_ramp.txt$', full_filespec, re.I )
      if x :
           n = x.groups()
           nl = list(n)
           nl.append( full_filespec )
           nl.append( '' )
           return nl
      else :
        
           x = re.search( r'(ramps_[^\\]+)\\([^\\]+)\\.*(\d\.\d+)v_ramp.txt$', full_filespec, re.I )
           if x:
                n = x.groups()
                return n[0], '', n[1], n[2], full_filespec, ''


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
       '''Removes the directory from a filepath
       
       Parameters:
           fullpath_filename
       Returns:
           filename
       '''

       return re.sub(r'.*(\\|/)','', str( filename ) )




    ###################################################################
    #### Filter Functions
    ###################################################################
    def update_filter_conditions( self, name, values=None, tolerance=None ):
      ''' Add/Modify/Delete a filter. A filter is used to select or restrict the
          data to be plotted to values which match the values parameter.
          values may be:
             None  :  The filter is removed. (Effectively making every value match)
             val   :  Single value, only data which equals this val will be selected (+/- tolerance) [=]
             'val' :  Single value, only data which equals this val will be selected (+/- tolerance) [=] (string)
             [val] :  Same as above [=]
             [val1,val2,...] : Only data which equals any of the val1,val2,... will be selected [=]
             'val1..val2'  : Only data which matches val1 <= data <= val2 will be selected [<>] (string)
             '..val'       : Only data which matches data <= val will be selected [<] (string)
             'val..'       : Only data which matches val  <= will be selected [>] (string)
             
       Parameters:
          name:        Name of filter to change
          values:      Value to change filter (optional)
          tolerance:   currently ignored (optional)
       Reads:
       Updates:        self.filter_conditions  , self.values_dict[name] self.values_dict_count[name]
       Returns:        None'''




      # if values is None then remove the filter name completely
      # else look for name in existing filter_conditions and change the entry for the filter
      # if the name does not exist add it to the end.



      # Error if the name of this filter is not in self.data
      if name not in self.data:
         print '... warning (update_filter_conditions) name <%s> not a recognised column name in the logfile' % name
         return




      # Delete the filter if values==None
      if values == None:
        # loop through looking for any filter conditions which have the same name
        new_filter_conditions = []
        for c in self.filter_conditions:
           if c[0] != name:  new_filter_conditions.append( c )
        self.filter_conditions = new_filter_conditions[:]
        return




      if tolerance != None:  tolerance = float(tolerance)

#      values, oper = self.expand_filter_condition_values( name, values )


      # Determine what type of operation is to be performed (=,<,>,<>)
      # if its a string, and it has '..' then we will then its one of <,>,<>

      oper = '='  # default operation type

      if isinstance( values, types.StringTypes) and re.search(r'\.\.', values):
         val1 = re.sub(r'\.\.\S+','',values)
         val2 = re.sub(r'\S+\.\.','',values)

#         print '(update_filter_conditions) double dot found (..)   name=%s, values=%s, val1=<%s> val2=<%s>' % ( name, values, val1, val2 )
         if val1 != '' and val2 != '':
            oper = '<<'
            val1 = float( val1 )
            val2 = float( val2 )
            if val2 > val1:
               values = [ val1, val2 ]
            else:
               values = [ val2, val1 ]
         if val1 != '' and val2 == '':
            oper = '>'
            val1 = re.sub(r'\.\.','',val1)
            val1 = float( val1 )
            values = val1
         if val1 == '' and val2 != '':
            oper = '<'
            val2 = re.sub(r'\.\.','',val2)
            val2 = float( val2 )
            values = val2



      # unlist  values if its not a list
      # and turn the values into floats if possible
      if isinstance( values, types.ListType):  # values is a list
         new_values = []
         for v in values:
            try:
              vx = float( v )
            except Exception:
              vx = v
            new_values.append( vx )
         values = new_values



      else:                                     # values is not a list
         pass
#         try:
#            values = float(values)
#         except Exception:
#            pass




      # If the filter name happens to be in the values_dict
      # look to see if all or none of the filter values are in the values_dict
      # if they are all in the values_dict then every compare with this filter will match (oper = 1)
      # if none of the filter values are in the values dict we know every compare with this filiter will not match (oper = 0)

      comp0 = 0
      comp1 = 0

      if name in self.values_dict:


         if not isinstance(values,types.ListType):
            vals = [ values ]
         else:
            vals = values



         for val in vals:
           for vd in self.values_dict[ name ]:
             if self.compare_values(val, vd, None) :
                 comp1 += 1
             else:
                 comp0 += 1

             if comp1 and comp0:
                break


         if not comp0 and comp1:     # only values that match present in the filter
           oper = '1'
         if comp0 and not comp0:     # only values that dont match present in the filter
           oper = '0'




      # Make up a new filter list item with the new filter in it
      new_c = [name, oper ]
      if type( values ) == types.ListType  :
         for v in values:
            new_c.append( v )
      else:
         new_c.append( values )

 #     print '(update_filter_conditions)  adding the filter ' , new_c


      # Go through all the exiting filters looking for this filter name
      # if found then replace the existing filter with the new one (new_c) we just made
      for i in range(len(self.filter_conditions)):
         c = self.filter_conditions[i]
         if c[0] == name:
            self.filter_conditions[ i ] = new_c

            return



      # If the filter was not found, add the new filter onto the end of the filter list
      self.filter_conditions.append( new_c )

      if name not in self.value_dict_names:
          self.add_values_dict( name )
          self.value_dict_names.append( name )


      return



    ###################################################################
#   def update_filter_conditions( self, name, values=None, oper='=' ):
    def get_filter_conditions( self, name ):
      '''Return the filter conditions
      
      Parameters:
         name:     Name of filter
      Returns:
         retval:   Value of filter 
      '''





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
            values in the vaules_dict that fall within the range
        
        Parameters: 
            name:      Name of filter
            values:    Values to expand
        '''

#        print '(expand_filter_condition_values) @@@@@@@@ doing  ', name , values
        vl = None
        if type(values) == types.ListType:
           vl = []
           for v in values:
             if isinstance(v, types.StringTypes) :
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

             if isinstance(values, types.StringTypes) :

               r1, r2 = self.get_filter_value_range( values )



               if grps:
                 if name not in self.values_dict:  self.add_values_dict( name )

                 vl = []
                 for vd in self.values_dict[ name ]:
                    if (r1 == None or r1 <= float(vd)) and  \
                       (r2 == None or float(vd) <= r2):

                       try:
                         vdf = float( vd )
                       except Exception:
                         vdf = vd
                       vl.append( vdf )



               if not grps:
                 vl = values

             else:
               vl = values

#        print '(expand_filter_condition_values)  name values=', name, vl

        try:
          vlf = float( vl )
        except Exception:
          vlf = vl

        return vlf




    ###################################################################
    def get_filter_value_range( self, values ):
               '''If the a filter condition contains a range string of the 
               form 'r1..r2' then return r1 and r2.
               
               Parameters:
                   values:    Value string which may of may not contain 'r1..r2'
               Returns:
                   r1:        r1 value, or None if not fount     
                   r2:        r2 value, or None if not found
               '''

               r1=None
               r2=None

               # look for "num..num"
               grps = re.search( r'([0-9\+\-\.]+)\.\.([0-9\+\-\.]+)',values)
               if grps:
                 r1 = float( grps.groups()[0] )
                 r2 = float( grps.groups()[1] )


               # look for   "..num"
               if not grps:
                   grps = re.search( r'\.\.([0-9\+\-\.]+)',values)
                   if grps:
                     r1 = None
                     r2 = float( grps.groups()[0] )




               # look for "num.."
               if not grps:
                   grps = re.search( r'([0-9\+\-\.]+)\.\.',values)
                   if grps:
                     r2 = None
                     r1 = float( grps.groups()[0] )

               return r1 , r2


    ###################################################################
    def print_values_list( self ):
       '''Print out a list of different values for each of the series_conditions
         
       Parameters:   None
       Reads:        self.value_dict_names_original_list,  self.data[]
       Returns:      None
       '''



       self.print_values_list_str = self.get_audit_str()

       tstr = "\nThe logfiles have the following parameters swept:"
       print tstr

       self.print_values_list_str = '%s%s' % (self.print_values_list_str, tstr)

       for sc in self.value_dict_names_original_list:

          swept_val = {}
          swept_val_lst = []
          if sc in self.data: def_sc = 1; len_sc = len(self.data[sc])
          else         : def_sc = 0; len_sc = 0

          tstr = "    %-15s:" % sc
          print tstr,
          self.print_values_list_str = '%s%s' % (self.print_values_list_str, tstr)

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
            for i,n in enumerate(swept_val_lst):
              tstr =  "%s(%d)" % (n, swept_val[n])
              print tstr,
              self.print_values_list_str = '%s%s' % (self.print_values_list_str, tstr)
              if i > 100: break
#             self.values_dict[ sc ].append( n )
          print ""
          self.print_values_list_str = '%s\n' % self.print_values_list_str
       print ""
       self.print_values_list_str = '%s\n' % self.print_values_list_str

#      self.values_dict = values_dict



    ###################################################################

    def add_filter_conditions( self, conditions=None ):

       '''Go through the conditions and split them into two lists, one for the seires
       and another for the filter while we are at it check that the condition names are
       correct and are present in the logfile as column header names
       
       Parameters:     
            conditions:      
       Updates:            
            self.filter_conditions
            self.series_conditions
       Returns:
       '''

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

    def select_data( self, conditions, xynames ):
       ''' NEW     Looks through data dictionary and returns a list of series which meet the filter conditions.
          Each series is a list of record numbers.
          There may be multiple sets of data which meet the same filter conditions, records that meet the
          filter_conditions but differ in the series_conditions are returned in separate series lists.
          The intent is that each series list is ploted on the same graph.
          
       Parameter:
            conditions:    List of conditions (not sure if this is still used)
            xname:         Name of the xaxis
       Reads:              self.filter_conditions
       Returns:
            series_data:
            series_values:
            series_unique_name_value_str:
            series_unique_values:
            series_unique_names:
            full_condition_selected_str 
       '''


       xname = xynames[0]

       self.add_filter_conditions( conditions )

       do_values_dict = False



       #--------------------------------------------------------------------------------
       # Create a new full series list. This takes the original series list and prepends it with
       # the names of the gui color select name and the gui line select name
       #--------------------------------------------------------------------------------


       full_series_conditions = []
       series_conditions_done = {}


       # Break up the selected data into series using the color series name ands the line series name as filters.
       # add the color-style  column to the value_dict_names, and to the full_series_conditions

       try:
         n = self.color_series.get()
         if n != '' and n != 'None' :
           series_conditions_done[ n ] = 'done'
           full_series_conditions.append( n )
           if n not in self.value_dict_names:
             self.add_values_dict( n )
             self.value_dict_names.append( n )

       except Exception:
         pass


       # add the line-style  column to the value_dict_names, and to the full_series_conditions
       try:
         n = self.line_series.get()
         if n != '' and n != 'None' :
           if not n in series_conditions_done:
                 series_conditions_done[ n ] = 'done'
           full_series_conditions.append( n )
           if n not in self.value_dict_names:
             self.add_values_dict( n )
             self.value_dict_names.append( n )

       except Exception:
         pass


#      for sc in self.series_conditions:
#         print '(select_data) adding series_conditions onto  full_series_conditions', sc
#         if sc not in series_conditions_done:
#                series_conditions_done[ sc ] = 'done'
#                full_series_conditions.append( sc )


       # Split the data based on the standart parameter sweep names, this will ensure that there will be separate lines for each condition
       # Except if we are doing Frequency of Spur plot then don't split it up!
       if xname != 'Frequency of Spur (MHz)' and xname[:5] != '[Time]' :

         for sc in self.value_dict_names:
            if sc != xname and sc in self.series_seperated_list and sc != 'Vramp Voltage':
               if sc not in series_conditions_done:
                   series_conditions_done[ sc ] = 'done'
                   full_series_conditions.append( sc )



       self.values_filtered_dict = {}
#      for vdn in self.value_dict_names:
#        print '(select_data) adding new values_selected_dict name', vdn
#        self.values_selected_dict[ vdn ] = []




       # full_series_conditions is a list of all the filter conditions plus the color and line series


       #--------------------------------------------------------------------
       # go through all the records in the data dictionary, and create new lists of record numbers
       # which match the filter_conditions and create separte lists for each series_condition
       #--------------------------------------------------------------------


       #print '  series data = ', self.series_conditions






       dcx = 0
       series_unique_name2num = {}
       series_count  = 0
       series_values = []
       series_data   = []
       selected_count  = {}
       selected_values = {}

       filter_conditions_match_count = {}

       # To start with mark all records as not matching (=0)
       rn_good_list = [ 0 ] * self.datacount









       # first filter out any records that don't have valid X axis or Y axis data
       # if there are multiple Y axes check that there is at least one good Y data value

       good_value_rn_count = 0

       for rn in range(self.datacount):

              val_rn  = self.data[ xynames[0] ][rn]
              if val_rn == None :     continue

              for axis_name in xynames[1:]:
                 val_rn  = self.data[ axis_name ][rn]
                 if val_rn != None :
                     # At this point we have a record with a good X value and
                     # at least one good Y value, therefore mark the record as good
                     rn_good_list[ rn ] = 1
                     good_value_rn_count += 1
                     break


       for fc in self.filter_conditions:
         name = fc[0]
         filter_conditions_match_count[ name ] = 0
         self.values_filtered_dict[ name ] = []
#        selected_count[ name ] = 0
#        selected_values[ name ] = []


       for fc in self.filter_conditions:

         name = fc[0]
         oper = fc[1]
         tolerance = None
         filter_values = fc[2:]

         # if we are filtering on a Pout value, these are likely to be imprecise, so widen the limits by 0.1 dB to make sure we accept close values.
         if re.search( r'Pout', name , re.I) or re.search( r'VSWR', name , re.I):
             tolerance = 0.2
         else:
             tolerance = None    # a tolerance of None means that the compare_value default tolerance is used (probably set to 0.001)



         if oper == '1':
                  if name in self.value_dict_names:
                     vd = self.data[ name ][0]
                  else:
                     vd = 'too many'
                  if vd not in self.values_filtered_dict[ name ]:
                     self.values_filtered_dict[ name ].append( vd )
                  filter_conditions_match_count[ name ] = good_value_rn_count
                  continue   # go to the next filter (no need to look at any of data.

         if oper == '0':
                  rn_good_list = [ 0 ] * self.datacount
                  break





         good_value_rn_count = 0

         for rn in range(self.datacount):






             if rn_good_list[ rn ]:
                 val_rn = self.data[ name ][rn]
                 value_good = False

                 for i, val_filter in enumerate(filter_values):

                        # if we have a << filter range then only do this loop once
                        if oper == '<<' and i == 0:
                           val_filter2 = filter_values[1]
                        else:
                           val_filter2 = None

                        # ok - for Pout filters which are less than 10dB set the tolerance to 2dB so that we don't filter out data that is close enough
                        if re.search( r'Pout', name , re.I) and val_filter < 10:
                            toler = 2
                        else:
                            toler = tolerance    # a tolerance of None means that the compare_value default tolerance is used (probably set to 0.001)


                        if self.compare_values( val_rn , val_filter, toler, oper, val_filter2 ):     # look out for this! - the filter 'value' might not be of the same type as the data dictionary value.
                             value_good = True                # any value which matches in the filter list is enough - its an OR function

                             if name in self.value_dict_names:
                                vd = val_rn
                             else:
                                vd = 'too many'
                             if vd not in self.values_filtered_dict[ name ]:
                                self.values_filtered_dict[ name ].append( vd )


                        # for the range oper = '<<', we must only do the loop once, even though there are two elements in the values list
                        if oper == '<<' : break




                 if value_good:
                      good_value_rn_count += 1
                 else:
                      rn_good_list[ rn ] = 0      # if the value doesnt match then mark this record is no good




         filter_conditions_match_count[ name ] = good_value_rn_count




       # From the filtered data get a list of different values for each filter
       # and save it in values_selected_dict
       #
       self.values_selected_dict = {}
       for fc in self.filter_conditions:
                 vdn = fc[0]
                 self.values_selected_dict[ vdn ] = []
                 for rn in range( self.datacount ):
                     if rn_good_list[ rn ]:
                         valrn = self.data[vdn][rn]
                         if valrn not in self.values_selected_dict[ vdn ]:
                              self.values_selected_dict[ vdn ].append( valrn )

       # Supplement the values_selected_dict with all the values from the values_dict_names list
       for vdn in self.value_dict_names:
            if vdn not in self.values_selected_dict:
                 self.values_selected_dict[ vdn ] = []
                 for rn in range( self.datacount ):
                     if rn_good_list[ rn ]:
                         valrn = self.data[vdn][rn]
                         if valrn not in self.values_selected_dict[ vdn ]:
                              self.values_selected_dict[ vdn ].append( valrn )




       #--------------------------------------------------------------------
       # Go through the series_conditions looking for unique set of values.
       # If unique then create a new series, if not then add to the existing series
       #--------------------------------------------------------------------

       full_series_conditions_no_xynames = []
       for sc in full_series_conditions:
           if sc not in xynames:
              full_series_conditions_no_xynames.append( sc )

       full_series_conditions =   full_series_conditions_no_xynames


       for rn in range( self.datacount ):
             if rn_good_list[ rn ]:
                 series_name = ''

                 # create a string (series_name) which is a concat of of all the values found for this record
                 for sc in full_series_conditions:
                   name = sc
                   value = self.data[ name ][rn]
                   value_str = str( value )
                   series_name = series_name + '@' + value_str

                 # for each new unique series_name
                 #   get a  series_name count (index)
                 #   build a list of series_names

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

#       print 'full_series_conditions', full_series_conditions
#       print 'series_values', series_values
#       print 'series_unique_name_value_str', series_unique_name_value_str
#       print 'series_unique_values',    series_unique_values
#       print 'series_unique_names', series_unique_names


       tstr = 'Parts: %s' % self.values_selected_dict[ 'SN' ]
       self.selected_filter_conditions_str  = '%s\n%s' % ( self.selected_filter_conditions_str, tstr)


       tstr = '  filter conditions :'
       print tstr
       self.selected_filter_conditions_str  = '%s\n%s' % ( self.selected_filter_conditions_str, tstr)



       full_condition_selected_str = ''

       for fc in self.filter_conditions:
              count = 'This column name is not in the logfile'
              name = fc[0]
              oper = fc[1]
              tolerance = None
              values = fc[2:]
              count = 0

              # if we are filtering on a Pout or VSWR value, these are likely to be imprecise, so widen the limits by 0.1 dB to make sure we accept close values.
              if re.search( r'Pout', name , re.I) or re.search( r'VSWR', name , re.I):
                 tolerance = 0.2
              else:
                 tolerance = None



#              print '(select_data) fc = ', fc

              if 0 and name in self.data:
                  if oper == '0':   # no values in vaules_dict match filter, count = 0
                     values = ''
                     count  = 0
                  elif oper == '1':  # all values in values_dict match filter, count = datacount
                     values  = self.values_dict[name]
                     count  = self.datacount
                  elif name in self.data:
                     for rn in range(self.datacount):
                        for value in values:

                           if re.search( r'Pout', name , re.I) and value < 10:
                              toler = 2
                           else:
                              toler = tolerance    # a tolerance of None means that the compare_value default tolerance is used (probably set to 0.001)

                           if self.compare_values(self.data[ name ][rn], value, toler) :
                               count += 1


              # Check to see if the selected data covers the full range of conditions
              # first get the extreme filter values, and set a fairly loose 10% tolerance
              if len( values ) > 1 and not isinstance( values[0], types.StringTypes ) :
                  if oper == '=':
                    vl  = values
                    tol = tolerance
                  else:
                    vl = [ values[0] , values[-1] ]
                    tol = abs( values[0] - values[-1] ) * 0.1
              else:
                  vl = [ values[0] ]
                  tol = tolerance

              # go through the each filters extreme values, looking to see if this value exists in the  values_selected_dict
              # and add an '*' character to mark each filter which is not fully included

              sel_lst =  self.values_selected_dict[ name ]
              sel_lst.sort()

              fcs_str = ''

              for v in vl:


                  # ok - for Pout filters which are less than 10dB set the tolerance to 2dB so that we don't filter out data that is close enough
                 if re.search( r'Pout', name , re.I) and v < 10:
                      toler = 2
                 else:
                      toler = tol    # a tolerance of None means that the compare_value default tolerance is used (probably set to 0.001)



                 full_condition_selected = False
                 for vs in sel_lst:
                    if self.compare_values(vs, v, toler) :
                       full_condition_selected = True
                       break
                 if full_condition_selected == False:
                       fcs_str = fcs_str + '*'
                       full_condition_selected_str = full_condition_selected_str + '*'
                       break

#              print '(select_data)   self.values_filtered_dict[ %s ] = %s' % ( name,  self.values_filtered_dict[ name ] )
#              print '(select_data)   self.values_selected_dict[ %s ] = %s' % ( name,  self.values_selected_dict[ name ] )




              if len( sel_lst ) < 12:
                sel_values = sel_lst
              else:
#                sel_values = 'LIST TOO LONG'
                sel_values = '['
                for sv in sel_lst[:5]:
                    sel_values = '%s %0.3f,' % (sel_values , float(sv) )
                sel_values = sel_values + ' ... '
                for sv in sel_lst[-5:]:
                    sel_values = '%s %0.3f,' % (sel_values , float(sv) )
                sel_values = sel_values + ']'

              tstr = '     %-15s %2s %-30s #matches= %-5d  sel= %-s %s' % (name, oper, values, filter_conditions_match_count[ name ], sel_values, fcs_str )
              print tstr
              self.selected_filter_conditions_str  = '%s\n%s' % ( self.selected_filter_conditions_str, tstr)



       if len(series_data) == 0 :
            tstr =  "*** ERROR (select_data) no data was found in the logfile that matches all the filter conditions"
            print tstr
            self.selected_filter_conditions_str  = '%s\n%s' % ( self.selected_filter_conditions_str, tstr)


            return [],[],[],[],[],''
       else:
            tot_record_count = 0
            for lst in series_data:
               tot_record_count += len(lst)
            tstr = "  .(select_data) found %d series with %d individual measurement values that match all the filter conditions" % ( len(series_data), tot_record_count)
            print tstr
            self.selected_filter_conditions_str  = '%s\n%s' % ( self.selected_filter_conditions_str, tstr)


#       print '\n(select_data_new) series_values    '           , series_values
#       print '\n(select_data_new) series_unique_name_value_str', series_unique_name_value_str
#       print '\n(select_data_new) series_unique_values'        , series_unique_values
#       print '\n(select_data_new) series_unique_names         ', series_unique_names



       return series_data, series_values, series_unique_name_value_str, series_unique_values, series_unique_names, full_condition_selected_str



    ########################################################################
    def compare_values( self, val_data , val_filter, tolerance=None, oper='=', val_filter2=None ):
         '''Compares a value against a limit.
         
         Parameter:
             val_data:     Data value to compare
             val_filter:   Filter Value to compare with val_data
             tolerance:    Comparison is made with +/- tolerance.  If None tolerance = 0.001
             oper:         Comparison operator '=', '<', '>','<<', 
             val2_filter:  If operator '<<' then comparison used 
         Returns:
             1:   comparison true
             0:   comparison false
         '''


         # simple equate, with all oper values, if val1 == val2 then it is a match
         if val_data == val_filter: return 1

         if tolerance == None:      tolerance = 0.001


         # if the val aint the same then try a little harder
         try:

           if oper == '=' and abs( val_data - val_filter ) <= tolerance :
              return 1

           if oper == '<' and val_data <= (val_filter + tolerance) :
              return 1

           if oper == '>' and val_data >= (val_filter - tolerance) :
              return 1

           if oper == '<<' and (val_filter - tolerance) <= val_data <= (val_filter2 + tolerance) :
              return 1

         except Exception:
           pass


         return 0



    ########################################################################
    def get_unique_series_names( self, series_cond, series_values):
       '''Go through all the series_values and create a new list of series values which have unique values
       
       Parameters:
            series_cond:
            series_values:
       Returns:
            series_unique_name_value_str:
            series_unique_values, series_unique_names
       '''

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

#            if name=='sn' :
#              val = re.sub(r'.*([sS][nN]\d+)[_ ]?.*', r'\1', val, re.I )

             unique_name = unique_name  + self.truncate_value( val ) + ' '

             unique_value_list.append( val )
         series_unique_name_value_str.append( unique_name )
         series_unique_values.append( unique_value_list )

       return series_unique_name_value_str, series_unique_values, series_unique_names

    ########################################################################
    def truncate_name( self,  name ):
      '''Truncates the name to provide a shortenned name suitable for printing a version of the name
      
      Parameters:
          name:   Name to shorten
      Returns:
          name:   Shortenned name
      '''

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
      '''Truncates the value to provide a shortenned name suitable for printing

      Parameters:
          value:   Value to shorten
      Returns:
          value:   Shortenned value
      '''


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
         ''' Get a consistent name for the key that was pressed ie Control_L -> control , Alt_R -> alt , Shift_L -> shift 
         
         Parameters:
             value:
         Returns:
             value:         
         '''

         if value == None : return None

         value = re.sub( r'_[LR]$', '', value )
         value = value.lower()
         return value

    ########################################################################
    def get_sub_series( self, xname, s ):
         '''Scan through all the xvalues, get the min and max values, and the range
         find the main increase or decrease
         
         Parameters:
             xname:    Name of axis
             s:        Series containing a list of record numbers
         Returns:
             snew:     The orginal list seperated into individual list (monatonic in x value)
         '''


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


            try:
                v = float( v )
        
                if vold == None : vold = v

                if (v - vold) * inc * -1  > 0.5 * rng :    # if the delta is greater than half the range then start a new series
                   snum += 1
                   snew.append( [] )
            except: pass

            snew[snum].append(i)
            vold = v

         return snew

    ########################################################################


    def get_data( self, xynames, conditions=[] ):
       '''Seems to be only used by the polar plot routine which is obsolete!!
       
          Looks through the data dictionary looking for all records that have data in all the xnames, ynames fields,
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
      '''Finds the minimum and maximum values from a list
      
      Parameters:
          lst:   list of values to search
      Returns:
          min:
          max:
      '''
      
      min = None
      max = None
      for v in lst:
        if max == None or v > max: max = v
        if min == None or v < min: min = v

      return min,max

    ###################################################################
    def get_minmax_idx( self, lst ):
      '''Finds the minimum and maximum value indexs from a list
      
      Parameters:
          lst:   list of values to search
      Returns:
          idx_min:
          idx_max:
      '''
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
      '''Places text on a polar plot
      
      Parameters:   
            str:        Text to plot
            idx:        index of data into the self.xydata array
            txtx:       x location of text
            txty:       y location of text
      Returns:      
            None
      '''

      #n = self.xydata[1][idx]
#      n = round( self.xydata[3][idx], 2 )
      m =  self.plot_x2pol[idx]
      a =  self.plot_xpol[idx]

      vswr = (1+m)/(1-m)

      R = ( 0 +0j )
      R = complex( m*cos(a), m*sin(a) )
      Z = (1+R)/(1-R)
      Zr = Z * self.characteristic_impedance

      str = r'$\mathrm{ %s\/\/\theta=%3.0f^o\/\/VSWR=%0.2f\/\/Z=(%0.1f\/%+0.1fj)\Omega}$' % (str, self.plot_xpol[idx]*360/(2*nu.pi), vswr, Zr.real, Zr.imag)

      annotate( str, xy=( self.plot_xpol[idx] , self.plot_x2pol[idx] ),
                   xytext=(txtx, txty),  textcoords='figure fraction',
#                    arrowprops=dict(facecolor='black', shrink=0.01,width=0.1,headwidth=4, alpha=1),
                    horizontalalignment='left', verticalalignment='bottom',fontsize=12)

    ###################################################################
    def annotate_figure( self, str, txtx, txty ):
      '''Annotates a graph plot
      
      Parameters:
           str:     Text to display
           txtx:    X coordinate as a fraction of the graph
           txty:    Y coordinate as a fraction of the graph
      Returns:      None
      '''

      if str == '': return
      self.ax.annotate( str, xy=(txtx, txty),  textcoords='figure fraction', xycoords='figure fraction', 
                     horizontalalignment='left', verticalalignment='bottom', fontsize=10)


    ###################################################################


    def deg2rad( self, lip ):
      '''Converts a list of values in degrees to a list of values in radians
      
      Parameters:
          lip  : List of degree values
      Returns:  
          lop  : List of radian values
      '''
      
      
      lop = []
      for i in lip:   lop.append( i * 2*pi/360.0 )
      return lop


    ###################################################################
    def get_unique_vals( self, lip ):
      '''Takes a list and removes any repeated values
      
      Parameters:
          lip:      List of values to scan
      Returns: 
          lop:      List containing unique values (same order as lip)
      '''

      lop = []
      for i in lip:
        if type(i) == types.IntType or type(i) == types.FloatType:
          ir = round(i, 2)
        else:
          ir = i
        if ir not in lop: lop.append(ir)

      return lop
    ###################################################################

#####################################################################################
#### Distortion Functions
#####################################################################################
    ###################################################################

    def wadd_vam_pout_columns(self):
        '''gui wrapper for add_vam_pout_columns function
        
        Parameters: None
        Returns:    None
        Reads:      'Dist' Gui control tab, self.dist_* selelection values
        Updates:    Runs  add_vam_pout_columns
        '''


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
       ''' Calculates the distortion variation data, by taking the reference data from the ref_logfilename, 
       it must also match all the other conditions. It will then calculate the variation by comparing the 
       gain and phase slope data against the reference gain and phase slopes.
       
       Parameters:
       Returns:
       Reads:
       Updates:'''



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
       ''' Calculates a Yi value for a given Xi by interpolating the X and Y data provide by the xname and yname.
           xname and yname data is searched searched between the rn_st and rn_fn values
           
       Parameters:
           xi:      x value to interpolate
           xname:   x axis column name
           yname:   y axis column name
           rn_st:   start record number 
           rn_fin:  last record number
       Returns: 
           yi:      interpolated y value
       '''

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
    def calc_amam_pout(self, rn_start, rn_finish):
      ''' calc_amam_pout :  Calculates the absolute power from a PSA AMAM test
          It looks through the results for the Power and Efficiency tests. The last Power & Efficiency test before the AMAM tests is used as
          a calibration for the following AMAM tests. It chooses the first AMAM test after a Power & Efficiency test to calculate
          a calibration power scaling factor 'psf'. The 'psf' is factor that will be used to scale all AMAM values to a coresponding Pout value.

          It is important that the VAM voltage of the last step in the AMAM test has exactly the same Vramp voltage of the preceding
          Power and Efficiency test, (should have the same DAC values in the _ramp.txt files)
          
          Parameters:
              rn_start:   starting record number
              rn_finish:  last record number
          Returns:        None'''



      if 'TestName' in self.data  and  'Vramp Voltage' in self.data and  'Output Power & Efficiency' in  self.data['TestName']:

        vramp2pout = {}
        self.add_new_column( 'Adj Pwr Out(dBm)' )


        if not 'AM-AM' in self.data: return

        self.add_new_column( 'Pout(dBm)'  )

        for rn in range( rn_start, rn_finish ):

           # find the power and efficiency tests
           if self.data['TestName'][rn] == 'Output Power & Efficiency' and self.data['Vramp Voltage'][rn] != None and self.data['Adj Pwr Out(dBm)'][rn] != None :


              ls = [ str(self.data['Process'        ][rn]) ,
                     str(self.data['Vbat(Volt)'     ][rn]) ,
                     str(self.data['Temp(C)'        ][rn]) ,
                     str(self.data['HB_LB'          ][rn]) ,
                     str(self.data['Freq(MHz)'      ][rn]) ,
                     str(self.data['VSWR'           ][rn]) ,
                     str(self.data['Phase(degree)'  ][rn]) ,
                     str(self.data['Pwr In(dBm)'    ][rn]) ,
#                     str(self.data['Segments'       ][rn]) ,
                     str(self.data['Regmap'         ][rn]) , ]

              cond = ' '.join( ls )

              hblb           = self.data['HB_LB'          ][rn]
              pout_at_cond   = self.data['Adj Pwr Out(dBm)'][rn]
              vramp_at_cond  = self.data['Vramp Voltage'][rn]


#              print '(calc_amam_pout) ', self.datacount, rn, self.data[ 'linenumber' ][rn],self.data['TestName'][rn], len(self.data['TestName'])
              # see if the next test is an AMAM test
              if rn < rn_finish+1 and rn+1 < len(self.data['TestName']) and self.data['TestName'][rn+1] == 'AM-AM AM-PM Distortion' :

                 rn_first_amam =  rn+1

                 # find the extent of the subsequent AMAM tests.
                 for rni in range( rn_first_amam, rn_finish ):
                     if self.data['TestName'][rni] != 'AM-AM AM-PM Distortion' :  break

                 rn_last_amam = rni

#                 print '   (calc_amam_pout) Calibrating PSA Power - found AM-AM AM-PM Distortion test at rn =', rn, rn_first_amam, rn_last_amam

                 vam = None
                 found_matching_conditions = False
                 first_amam_cond = None
                 for rnii in range( rn_first_amam, rn_last_amam ):
                 # Get the amam test conditions and look for the test conditions that matches the previous power and efficiency conditions
                    if self.data['TestName'][rnii] == 'AM-AM AM-PM Distortion' :

                        ls = [ str(self.data['Process'        ][rnii]) ,
                               str(self.data['Vbat(Volt)'     ][rnii]) ,
                               str(self.data['Temp(C)'        ][rnii]) ,
                               str(self.data['HB_LB'          ][rnii]) ,
                               str(self.data['Freq(MHz)'      ][rnii]) ,
                               str(self.data['VSWR'           ][rnii]) ,
                               str(self.data['Phase(degree)'  ][rnii]) ,
                               str(self.data['Pwr In(dBm)'    ][rnii]) ,
#                               str(self.data['Segments'       ][rnii]) ,
                               str(self.data['Regmap'         ][rnii]) , ]

                        condii = ' '.join( ls )

                        if first_amam_cond == None: first_amam_cond = condii

                    # if the conditions match the power and efficiency test condition, go through all the steps
                    if condii == cond :
                        vam = self.data[ 'AM-AM' ][rnii]
#                        print '(calc_amam_pout)          matching conditions found rn=%s  line=%s   vam=%s' % (rnii,self.data[ 'linenumber' ][rnii] , vam)
                        found_matching_conditions = True
                        vam = self.data[ 'AM-AM' ][rnii]
                        rn_vam = rnii

                 amam_val = vam

                 if amam_val == None :
                     print '*** ERROR *** could not find any matching AMAM tests for Power and Efficiency test with conditions \n  pwr_eff_cond =', cond
                     print '  1st_amam_cond=', first_amam_cond

                     break

                 rn_amam_val = rn_vam

#                 print '   (calc_amam_pout)   found matching amam test with vam =', amam_val, rn_amam_val
                 # caculate the power scaling factor
                 pwrcal_amam_sqr = amam_val ** 2
                 pwrcal_pout_w = (10**(pout_at_cond/10.0))/1000
                 amam2w        = pwrcal_pout_w / pwrcal_amam_sqr




                 # go through all the AMAM tests in this section and add the pout values
                 for rnii in range( rn_first_amam, rn_last_amam ):
                    if self.data['TestName'][rnii] == 'AM-AM AM-PM Distortion' and self.data['HB_LB'][rnii] == hblb :
                        # calculate for the current am-am value
                        am_val  =   self.data[ 'AM-AM' ][rnii]
                        pwr_val_w = amam2w  *  am_val**2
                        self.data[ 'Pout(dBm)' ][rnii] =   10*log10(pwr_val_w*1000)







    ###################################################################
    def add_vam_pout_columns(self, ref_temp=25, ref_freq=870.0, ref_vbat=3.6, ref_pin=3.0, ref_seg='*', ref_hblb = 'LB', ref_process = 'TT') :
       '''Does the all the processing of data for Edge Distortion Test plotting

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

       Parameters:
           ref_temp   :
           ref_freq   :
           ref_vbat   :
           ref_pin    :
           ref_seg    :
           ref_hblb   :
           ref_process:
       Returns   :   None
       Updates   :  self.data[]
                         'Gain AM/VAM (V/V)'
                         'Gain AM/(VAM-offset) (V/V)'
                         'Gain AM/(VAM-offset) (dB)'
                         'Gain AM/(VAM-offset) (dB) <emp-limits>'
                         'Gain AM/(VAM-offset) Slope (dB/dB)'
                         'AM-PM Slope (deg/dB)'
                         'Gain AM/(VAM-offset) Slope - Ref (dB/dB)'
                         'Gain AM/(VAM-offset) Slope - Ref (dB/dB) <emp-limits>'
                         'AM-PM Slope - Ref (deg/dB)'
                         'AM-PM Slope - Ref (deg/dB) <emp-limits>'
       '''

       self.status.set( '(add_vam_pout_columns) Calculating Distortion Values' )
       self.root.update()

       print '\n(add_vam_pout_columns) Calculating Distortion Values with reference conditions [%s %s %s %s %s %s %s]' % (ref_process, ref_temp, ref_hblb, ref_seg, ref_freq, ref_vbat, ref_pin)

       # save the reference conditions
       # these will be used to decide whether to plot limits later

       cond_txt = ref_hblb + ',' + ref_seg + ','  + ref_process + ','

       if not  cond_txt +  'Vbat(Volt)'      in self.ref:      self.ref[ cond_txt +  'Vbat(Volt)'     ] = ref_vbat
       if not  cond_txt +  'Pwr In(dBm)'     in self.ref:      self.ref[ cond_txt +  'Pwr In(dBm)'    ] = ref_pin
       if not  cond_txt +  'Freq(MHz)'       in self.ref:      self.ref[ cond_txt +  'Freq(MHz)' ] = ref_freq
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
               self.data[ 'HB_LB' ][rn]    == ref_hblb                 and
               self.data[ 'Process' ][rn]  == ref_process              and
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
            

#       print '(add_vam_pout_columns) found_ref_am=', found_ref_am, ref_rns, [ self.data['linenumber'][ref_rns[0]],self.data['linenumber'][ref_rns[1]] ]

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


             # Save the 'Output Power & Efficiency' record numbers in calib_pwr_pae_lst
             if self.data[ 'TestName' ][ rn ] == 'Output Power & Efficiency' :
#                print ' (dist_test_lst) PAE   rn', rn
                 calib_pwr_pae_lst.append( rn )

             # Save the first and last step in the AMAM distortion tests in dist_test_lst
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


       print '(add_vam_pout_columns) number of power calibration tests = ', len( calib_pwr_pae_lst )


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
                 self.compare_values( self.data[ 'Freq(MHz)'      ][rnj] , pwrcal_freq)) :

                 found_matching_am_step = True

                 amam_val = self.data[ 'AM-AM' ][rnj]
                 pwrcal_amam_sqr = amam_val ** 2
                 pwrcal_pout_w = (10**(pwrcal_pout_dbm/10.0))/1000
                 amam2w        = pwrcal_pout_w / pwrcal_amam_sqr




           if found_matching_am_step == False and next_rn - rn > 2 :

             print '*** ERROR *** (add_vam_pout_columns) Could not find a matching AM-AM AM-PM Distortion test for power calculation [%d -> %d]' % (rn, next_rn)
             print self.data[ 'logfilename' ][rn] , self.data[ 'linenumber' ][rn] , self.data[ 'linenumber' ][next_rn-1]
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


           self.add_normalized_ampm( rn, next_rn, 20 )


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
    def add_normalized_ampm( self, rn_start, rn_finish, pwr_norm=20, cnam='AM-PM norm(deg)'):
           '''Adds a new column with normalized phase.
           Creates new column 'AM-PM norm(deg)' which has the 
           phase normalized to 0 deg at power = pwr_norm
 
           Parameters:
              rn_start  :
              rn_finish : 
           Returns:  None
           Reads  :  self.data[] 'Adj Pwr Out(dBm)', 'AM-PM(degree)'
           Updates:  self.data[] 'AM-PM norm(deg)'
           '''

           ##################################
           # Add a normalized AM_PM column
           ##################################

           # find the 20dBm phase
           pm_val_old  = None
           pwr_val_old = None           
           pm_offset   = None
           for rnj in range( rn_start, rn_finish ) :
           
              if pm_offset != None: break
              
              if self.data[ 'TestName' ][rnj] == 'AM-AM AM-PM Distortion':

                 # interpolate to find the phase at pwr_norm
                 pm_val  =   self.data[ 'AM-PM(degree)' ][rnj]
                 pwr_val =   self.data[ 'Adj Pwr Out(dBm)' ][rnj] 

                 if pwr_val >= pwr_norm:
                     pm_offset = pm_val_old + (pm_val-pm_val_old)*(pwr_norm-pwr_val_old)/(pwr_val-pwr_val_old)

                 pm_val_old  = pm_val
                 pwr_val_old = pwr_val
                 
                 
                 
           self.add_new_column(cnam)
           for rnj in range( rn_start, rn_finish ) :
                if self.data['AM-PM(degree)' ][rnj] != None:
                    self.data[cnam][rnj] =  self.data['AM-PM(degree)' ][rnj] - pm_offset  
           
                     

    ###################################################################
    def add_normalized_gain( self , trns ):
         '''Adds new column with normalized gain.
         Find the gain when the power out is 0dBm
         With x='Gain AM/(VAM-offset) (dB)' and y='Adj Pwr Out(dBm)'
         Find the gain y where the output power x is 0dBm, then
         add new column with normalized gain

         Parameters:
            trns : [rn_start, rn_finish ]
         Returns   : None
         Reads :   self.data[] 'Adj Pwr Out(dBm)', 'Gain AM/(VAM-offset) (dB)', 'Gain AM/VAM (dB)'
         Updates:  self.data[] 'Gain AM/VAM Norm (dB)'
         '''


         # normalize the gain to 0dBm

         x = array( self.data[ 'Adj Pwr Out(dBm)'  ][trns[0]:trns[1]] )
         y = array( self.data[ 'Gain AM/(VAM-offset) (dB)' ][trns[0]:trns[1]] )

         xi = 0

         [yi] = stineman_interp([xi],x,y)

         for rnj in range( trns[0], trns[1] ):
                  self.data[ 'Gain AM/VAM Norm (dB)' ][rnj]  =  self.data[ 'Gain AM/VAM (dB)' ][rnj] / yi


    ###################################################################

    def add_gain_phase_slope( self, trns ):
         '''Add Gain and Phase  slope columns

         Parameters:
           trns :  [ rn_start , rn_finish ]
         Returns:  None
         Updates:  self.data[] 'Adj Pwr Out(dBm)', 'Gain AM/(VAM-offset) (dB)', 'AM-PM(degree)' '''


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
    def add_slope( self, x_col_name, y_col_name, op_col_name, rn_start=0, rn_finish=None  ):
         '''Creates a new column name 'op_col_name' by calculating the slope of 'y_col_name' wrt ''x_col_name'
         
         Parameters:
              x_col_name:      x column name from the self.data array
              y_col_name:      y column name from the self.data array
              op_col_name:     New Column name to create for the slope
              rn_start:        Starting record number  (default 0)
              rn_finish:       Last record number (default self.datacount)
         Returns:              None
         Reads:                 
              self.data[ x_column_name ]
              self.data[ y_column_name ]
         Updates:
              self.data[ op_col_name ]
         '''

         if x_col_name not in self.data  or \
            y_col_name not in self.data       : return

         self.add_new_column( op_col_name )



         if rn_finish == None: rn_finish = self.datacount


         # We can only calculate the slope between data which has the same conditions
         # Therefore we must loop through the data, each time calculating the
         # slope of data which has the same conditions

         # We will be looking for unique conditions to seperate the data into lists
         # the condition value is built by taking all the values in the value_dict_names
         # but we must not take the x_col_name value to build the condition value
         if x_col_name in [ 'Pout(dBm)', 'Adj Pwr Out(dBm)', 'PSA Pwr Out(dBm)' ] :
            ignore_col_lst = [ 'Step', 'Vramp Voltage', x_col_name ]
         else:
            ignore_col_lst = [ x_col_name ]



         # list for every value_dict_names value
         cond_list = [ None ] * rn_finish
         # a list marking whether the record has been done already
         done_list = [ None ] * rn_finish

         for rn in range(rn_start,rn_finish ):
            # don't do this record if either the x or y value is missing
            if self.data[ x_col_name ][rn] == None or \
               self.data[ y_col_name ][rn] == None :
                 done_list[ rn ] = True
                 continue

            cond_list[ rn ] = self.get_cond_val_from_rn( rn , ignore_col_lst )



#        for i in range(20):
#              print '(add_slope)', cond_list[ i ]


         for rns in range(rn_start,rn_finish ):

            # don't do the record if has been previously marked as done
            if done_list[ rns ] != None : continue


            x_m1 = x_m2 = y_m1 = y_m2 = None

            rni_m1 = rns

            condi = cond_list[ rns ]

            for rni in range( rns , rn_finish ):

               if done_list[ rni ] != None or cond_list[ rni ] != condi : continue

               # found a record which has the same condion as the outer loop condition
               #  mark it as done so we can quickly ignore the next time round the loop

               done_list[ rni ] = True

               x = self.data[ x_col_name ][rni]
               y = self.data[ y_col_name ][rni]

#               print '               m4',   [ x , y ]


               if x == None or y == None:
                    done_list[ rni ] = True
                    continue

               slope = None

               try:
                 dy =  y - y_m2
                 dx =  x - x_m2
                 slope = dy/dx
                 if rni > rns:    # dont write the first one as it would be less than rn_start
                    self.data[ op_col_name ][rni_m1]  = slope
                 self.prof_slope_count +=1
               except Exception:
                 slope = None


               rni_m1 = rni
               x_m2 = x_m1
               y_m2 = y_m1
               x_m1 = x
               y_m1 = y



    ###################################################################
    def add_gain_slope( self, trns ):
         '''Calculates and adds Gain Slope column data
         Parameters:  None
         Returns   :  None
         Reads     :  self.data[] 'Pout(dBm)', 'Gain AM/(VAM-offset) (dB)'
         Updates   :  self.data[] 'Gain AM/(VAM-offset) Slope (dB/dB)'
         '''

         x_m1 = x_m2 = y_m1 = y_m2 = None

         for rnj in range(trns[0],trns[1] ):

            x = self.data[ 'Pout(dBm)' ][rnj]
            y = self.data[ 'Gain AM/(VAM-offset) (dB)' ][rnj]

            try:
              dy =  y - y_m2
              dx =  x - x_m2
              slope = dy/dx
            except Exception:
              slope = None

            if rnj > trns[0]:    # dont write the first first one as it would be less than rn_start
               self.data[ 'Gain AM/(VAM-offset) Slope (dB/dB)'][rnj-1]  = slope

            x_m2 = x_m1
            y_m2 = y_m1
            x_m1 = x
            y_m1 = y


    ###################################################################
    def add_phase_slope( self, trns ):
         '''Calculates and adds Phase Slope column data
         Parameters:  None
         Returns   :  None
         Reads     :  self.data[] 'Pout(dBm)', 'AM-PM(degree)'
         Updates   :  self.data[] 'AM-PM Slope (deg/dB)'
         '''

         x  = self.data[ 'Pout(dBm)'              ] [trns[0]:trns[1]]
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
         '''For this distortion take the gain and phase slope and subract the gain and phase
         slope from the reference test

         Parameters:
            trns  :
            ref_trns:
         Returns : None
         Reads :  self.data[] 'Gain AM/(VAM-offset) Slope (dB/dB)',
                              'AM-PM Slope (deg/dB)'
         Updates: self.data[] 'Gain AM/(VAM-offset) Slope - Ref (dB/dB)',
                              'Gain AM/(VAM-offset) Slope - Ref (dB/dB) <emp-limits>',
                              'AM-PM Slope - Ref (deg/dB)',
                              'AM-PM Slope - Ref (deg/dB) <emp-limits>' '''

         ref_rn = ref_rns[0]

         if ref_rn == None :
            print '*** ERROR *** (add_gain_phase_ref_diff) No reference data found, cannot calculate gain phase reference difference'
            return

         for rn in range( trns[0], trns[1] ):
            try:
                self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB)' ][rn]                =  self.data[ 'Gain AM/(VAM-offset) Slope (dB/dB)' ][rn]  - self.data[ 'Gain AM/(VAM-offset) Slope (dB/dB)' ][ref_rn]
                self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB) <emp-limits>' ][rn]   =  self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB)' ][rn]
                self.data[ 'AM-PM Slope - Ref (deg/dB)'      ][rn]   =  self.data[ 'AM-PM Slope (deg/dB)'      ][rn]  - self.data[ 'AM-PM Slope (deg/dB)'      ][ref_rn]
                self.data[ 'AM-PM Slope - Ref (deg/dB) <emp-limits>'      ][rn]   =   self.data[ 'AM-PM Slope - Ref (deg/dB)'      ][rn]
            except:
                pass

            ref_rn += 1


    ###################################################################

    def add_gain_ref_diff( self, trns, ref_rns ) :
         '''For this distortion take the gain and phase slope and subract the gain and
         phase slope from the reference test

         Parameters:
              trns   :   [rn_start, rn_finish]
              ref_rns:   Record number of the reference Slope
         Returns: None
         Updates: self.data[] Gain AM/(VAM-offset) Slope - Ref (dB/dB)', 'Gain AM/(VAM-offset) Slope - Ref (dB/dB) <emp-limits>' '''

         ref_rn = ref_rns[0]

         if ref_rn == None :
            print '*** ERROR *** (add_gain_ref_diff) No reference data found, cannot calculate gain reference difference'
            return


         for rn in range( trns[0], trns[1] ):
            try:
               self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB)' ][rn]                =  self.data[ 'Gain AM/(VAM-offset) Slope (dB/dB)' ][rn]  - self.data[ 'Gain AM/(VAM-offset) Slope (dB/dB)' ][ref_rn]
               self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB) <emp-limits>' ][rn]   =  self.data[ 'Gain AM/(VAM-offset) Slope - Ref (dB/dB)' ][rn]
            except:
               pass

            ref_rn += 1


    ###################################################################

    def add_phase_ref_diff( self, trns, ref_rns ) :
         '''For this distortion take the gain and phase slope and subract the gain and
         phase slope from the reference test

         Parameters:
              trns   :   [rn_start, rn_finish]
              ref_rns:   Record number of the reference Slope
         Returns: None
         Updates: self.data[] 'AM-PM Slope - Ref (deg/dB)', 'AM-PM Slope - Ref (deg/dB) <emp-limits>' '''

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
       '''a mistake in the ramp files files caused the segment value for HB staircase file to
        be swapped.

       Parameters: None
       Returns   : None
       Updates:  self.data['Segments']'''





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

#####################################################################################
####  Plot Functions
#####################################################################################

    def plot_polar_data( self, xynames,  logfilename ):
      '''Polar Graph Plotting function  - obsolete
      '''


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
      '''Prints out all the column names in the self.data array
      
      Parameters:  None
      Returns:     None
      Reads:       self.data[ * ]
      '''


      print '\n...the following data columns were found in the logfile:\n'
      cll = []
      for col in self.data:
        cll.append(col)
      cll.sort()
      for c in cll:
        print "%s," % repr(c) ,
      print '\n'




    ###################################################################
    def get_line_style_indexes( self, series_unique_values, series_unique_names, listcount, listlen, ycount, ylen ):

        ''' Tries to workout what color and line style to draw the graph
            it does this by looking at the series_unique_names and series_unique_values

            The series_unique_names is a list of all the parameter names that vary in the series,


            If the series_unique_names and series_unique_values are empty resort to using the number of graphs and number of ycount
            Parameters:
               series_unique_values:     List of values in the same order as the column names
               series_unique_names:      List of column names
               listcount:                Graph line count, used to index the color if self.color_series in is not set
               listlen:                  Unused
               ycount:                   Count of the Y axis, used to index the color if no color or line is selected
               ylen:
            Returns:
               c:                        color
               d:                        line style pattern
               cidx:                     string of the colr index
               didx:                     string of the line style index
            Reads:
               self.color_series:        Gui control panel color setting Column Name selection
               self.line_series:         Gui control tab line setting Column Name selection
'''





#        print '\n(get_line_style_indexes) series_unique_values=%s   series_unique_names=%s '% (series_unique_values,series_unique_names) , ycount , listcount, ycount, ylen


        sun = ''
        cidx = 0


        sun = self.color_series.get()
#       print '\n(get_line_style_indexes)  self.color_series.get() = ', sun

        jfound = None
        for j,n in enumerate( series_unique_names ):
             if n == sun :
                 jfound = j
                 break

        if sun != '' and sun != 'None' and sun != 'Yaxis' and jfound != None:

          # find the position of the color_series column name in the series_unique_names list
          # this is the value we will look for in the values_dict.


          scd = self.values_selected_dict[ sun ]



          for ki in range(len(scd)):
            k = scd[ki]
#           print '         (get_line_style_indexes) CIDX comparing series_unique_values[j]=<%s %s>   and scd[k]=<%s %s>' % (str(series_unique_values[j]), type(series_unique_values[j]), str(k), type(k))
            if str(series_unique_values[jfound]) == str(k):
#               print '     match'
                cidx = ki

        else:

              cidx = ycount
#             cidx = ycount + listcount
#             if listcount > 0 and ycount > 0:
#                cidx = ycount - 1


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
             didx = 0


#       print '      selecting line  based on <%s> %s ' % (sun, didx)
#       print series_unique_names



        c = self.color_list[ cidx %    len(self.color_list)    ]
        d = self.dash_list [ didx %    len(self.dash_list )    ]


        if self.line_on.get()== False : d = [0,10000]


#        print '(get_line_style_indexes)  c=%s  d=%s   cidx=%s   didx=%s' % (c, d, str(cidx), str(didx) )


        return c, d, str(cidx), str(didx)

    ###################################################################
    def get_line_style_indexes_obsolete( self, series_unique_values, series_unique_names, listcount, listlen, ycount, ylen ):

        ''' Tries to workout what color and line style to draw the graph
            it does this by looking at the series_unique_names and series_unique_values

            The series_unique_names is a list of all the parameter names that vary in the series,


            If the series_unique_names and series_unique_values are empty resort to using the number of graphs and number of ycount
            Parameters:
               series_unique_values:     List of values in the same order as the column names
               series_unique_names:      List of column names
               listcount:                Graph line count, used to index the color if self.color_series in is not set
               listlen:                  Unused
               ycount:                   Count of the Y axis, used to index the color if no color or line is selected
               ylen:
            Returns:
               c:                        color
               d:                        line style pattern
               cidx:                     string of the colr index
               didx:                     string of the line style index
            Reads:
               self.color_series:        Gui control panel color setting Column Name selection
               self.line_series:         Gui control tab line setting Column Name selection
'''





#        print '\n(get_line_style_indexes) series_unique_values=%s   series_unique_names=%s '% (series_unique_values,series_unique_names) , ycount , listcount, ycount, ylen


        sun = ''
        cidx = 0


        sun = self.color_series.get()
#       print '\n(get_line_style_indexes)  self.color_series.get() = ', sun

        jfound = None
        for j,n in enumerate( series_unique_names ):
             if n == sun :
                 jfound = j
                 break

        if sun != '' and sun != 'None' and sun != 'Yaxis' and jfound != None:

          # find the position of the color_series column name in the series_unique_names list
          # this is the value we will look for in the values_dict.


          scd = self.values_selected_dict[ sun ]



          for ki in range(len(scd)):
            k = scd[ki]
#           print '         (get_line_style_indexes) CIDX comparing series_unique_values[j]=<%s %s>   and scd[k]=<%s %s>' % (str(series_unique_values[j]), type(series_unique_values[j]), str(k), type(k))
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


        if self.line_on.get()== False : d = [0,10000]


        print '(get_line_style_indexes)  c=%s  d=%s   cidx=%s   didx=%s' % (c, d, str(cidx), str(didx) )


        return c, d, str(cidx), str(didx)


##################################################################################


    def get_selected_plot_data( self, selected_record_list, xynames, xysel ):
          '''Weed out any bad data from the selected data. Bad data is any data that is not numeric
              Bad data is converted to None
              
          Parameter:
              selected_record_list:    List of record to select from
              xynames:                 List of x and y column names
              xysel:                   Index to select which axis to use from xynames 
          Returns:
              dlst:                    List of data values, with non numeric data removed (or set to None)
              rnlst:                   List of records, with non numeric data removed (or set to None)     
          '''


          xyname = xynames[ xysel ]


          time_data = False
          if re.search('^\[Time\]', xyname ):
             time_data = True


          dlst = []
          rnlst = []

#         if not xyname in self.data:  return [None] * len( selected_record_list )
          if not xyname in self.data:  return [], []


          got_data = False


          for rn in selected_record_list:

#                 print 'rn= %d  len( self.data[ %s ] ) = %s' % ( rn, xyname, len( self.data[ xyname ] ) )
                  xyv = self.data[ xyname ][rn]


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
        '''Plot graph data core function. Searches through the self.data[] array for 
      the xynames axis column name data and for data from the self.data[] which 
      match the conditions defined in self.filter_conditions (using function select_data())
      
      It returns a list of data points which can be used by measure_plot_data to 
      make measurements from the graph. 
      
      Prints the graph, and saves the plot to a file.
      
      Parameters:
           xynames:       List of self.data[] column names to define the x axis and one or more y axes
           conditions:    Obsolete
           savefile:      Defines the files and directory to save the plot in png format. (optional, defaults to None)
                          If None no files are saved
                          It can be one of the following forms:
                                savefile                       saves to directory self.savedir 
                                [ savefile, subdir ]           saves to {self.savedir}/subdir
                                [ savefile , subdir, linkdir ] also makes a link of plot file in linkdir
                          savefile is the filename without the .png extention
           titletxt:      Defines the title of the graph. (optional, defaults to None)
                          If None title is defined by the savefile name or if savefile is None the Yaxis name is used
      Returns:
         xyd:         A list of plot data
              [xvals:     List of Lists  of x data point values for the plotted series of graph lines
               yvals:     List of Lists  of y data point values for the plotted series of graph lines
               rnvals:    List of Lists  of record numbers data for the plotted series of graph lines
               snvals:    List of series numbers one for each series line graph
               cvals:     List of color values used for each of the graph line series
               dvals:     List of line style values used for each of the graph line series
               full_condition_selected_str:  String containing all the values of the selected filtered values
               xynames:]  List of x y axis names

      Reads:
        self.savedir
      Updates:
        self.plot_data = ret_val 
        self.plot_lineref
        self.plot_xdata
        self.plot_ydata
        self.plot_rndata
        self.plot_data_color
        self.plot_sn_full
 
        self.savefilename
        self.save_plot_count
        self.png_filename  
        self.png_filename
        self.png_relfilename
        self.png_dir
        self.png_reldir
        '''

        xyd = self.plot_graph_data_core( 'xy_scatter_plot', xynames,  conditions, savefile, titletxt )
        return xyd

    ###################################################################
    def plot_polar_data( self, xynames,  conditions, savefile=None, titletxt=None ):
        xyd = self.plot_graph_data_core( 'polar_plot', xynames,  conditions, savefile, titletxt )
        return xyd

    ###################################################################
    def plot_interactive_graph( self ):
        self.interactive = True

        # get the x and y axes from the selections in the X and Y axis tabs
        self.xynames = []
        xysel_lst =  self.xnames.curselection()
        for i in xysel_lst:
           n = self.xnames.get( int(i) )
           self.xynames.append( n )

        xysel_lst =  self.ynames.curselection()
        for i in xysel_lst:
           n = self.ynames.get( int(i) )
           self.xynames.append( n )
        self.graph_title.set('')



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
      '''Plot graph data core function. Searches through the self.data[] array for 
      the xynames axis column name data and for data from the self.data[] which 
      match the conditions defined in self.filter_conditions (using function select_data())
      
      It returns a list of data points which can be used by measure_plot_data to 
      make measurements from the graph. 
      
      Prints the graph, and saves the plot to a file.
      
      Parameters:
           plottype:      'xy_scatter_plot' the only currently supported graph type  
           xynames:       List of self.data[] column names to define the x axis and one or more y axes
           conditions:    Obsolete
           savefile:      Defines the files and directory to save the plot in png format. (optional, defaults to None)
                          If None no files are saved
                          It can be one of the following forms:
                                savefile                       saves to directory self.savedir 
                                [ savefile, subdir ]           saves to {self.savedir}/subdir
                                [ savefile , subdir, linkdir ] also makes a link of plot file in linkdir
                          savefile is the filename without the .png extention
           titletxt:      Defines the title of the graph. (optional, defaults to None)
                          If None title is defined by the savefile name or if savefile is None the Yaxis name is used
      Returns:
         ret_val:         A list of plot data
              [xvals:     List of Lists  of x data point values for the plotted series of graph lines
               yvals:     List of Lists  of y data point values for the plotted series of graph lines
               rnvals:    List of Lists  of record numbers data for the plotted series of graph lines
               snvals:    List of series numbers one for each series line graph
               cvals:     List of color values used for each of the graph line series
               dvals:     List of line style values used for each of the graph line series
               full_condition_selected_str:  String containing all the values of the selected filtered values
               xynames:]  List of x y axis names

      Reads:
        self.savedir
      Updates:
        self.plot_data = ret_val 
        self.plot_lineref
        self.plot_xdata
        self.plot_ydata
        self.plot_rndata
        self.plot_data_color
        self.plot_sn_full
 
        self.savefilename
        self.save_plot_count
        self.png_filename  
        self.png_filename
        self.png_relfilename
        self.png_dir
        self.png_reldir
      '''

      if 'Phase(degree)' in xynames[:2] and ('Magnitude' in xynames[:2] or 'VSWR' in xynames[:2] ):
          plottype = 'polar_plot'

          # Polar plots need to be plotted with 'Magnitude' as the Radius, and 'Phase(degree)' as the Theta
          # if the user specified 'VSWR' force it to plot 'Magnitude' instead.
          if  'VSWR' in xynames[:2] :
               v_idx = xynames.index(  'VSWR' )
               xynames[ v_idx ] =  'Magnitude'

          r_idx         = xynames.index(  'Magnitude' )
          theta_idx     = xynames.index(  'Phase(degree)' )

    #      print 'theta_idx=',   theta_idx
    #      print 'r_idx    =',   r_idx



      self.status.set( '(plot_graph_data_core) PLOTTING GRAPH %s'% plottype)
      self.root.update()


      self.png_filename    = ''
      self.png_relfilename = ''
      self.png_dir         = ''
      self.png_reldir      = ''


      if not self.done_list_columns:
          # add the rated_power_values to the list of printed out
          for key,val in self.rated_power_values.iteritems():
             self.value_dict_names_original_list.append(key)
#         print self.value_dict_names_original_list
          self.print_column_list()
          self.print_values_list()
          self.done_list_columns = True

      self.plot_data = None
      done_a_plot   = False
      legend_list   = {}

      done_legend_color      = {}
      done_legend_linestyle  = {}
      done_legend_color_line = {}

      print '\n---(plot_graph_data_core)----------------------------------------\n'

#     print 'xynames=', xynames

      if len(xynames) < 2 or xynames[0]  == None or xynames[1]  == None  :
            print '*** ERROR *** X or Y axis not defined'
            return


      tstr =  "...plotting data for  x,y,z = %s\n" % ( xynames )
      print tstr
      self.selected_filter_conditions_str  = '%s\n%s' % ( self.selected_filter_conditions_str, tstr)


      # Check to see if we have any data to plot

      got_yaxis_data = False
      for i in range(len(xynames)):
         name = xynames[i]
         if not name in self.data:
            print "*** ERROR *** (plot_graph_data_core) There is no data for axis '%s'. It is not a named column in the logfile" % name
#           sys.stdout.write('\a')
            sys.stdout.flush()
            return
         else:
            if i > 0 : got_yaxis_data = True



      # finish with this graph if we didn't get any data to plot on any of the yaxis's
      if got_yaxis_data == False: return

      print '(plot_graph) self.filter_conditions=', self.filter_conditions

      series_data, series_values, series_unique_name_value_str, series_unique_values, series_unique_names, full_condition_selected_str  = self.select_data( conditions, xynames )




      self.xynames = xynames
      self.conditions = conditions


      # now update the control window with the selected axes etc. (this is mainly needed if we are running in script mode)


      self.win_select( xynames )

      # Save the plot the file if selected

      if plottype == 'polar_plot' :  ynames_str =  ' '.join( xynames[2:] )
      else                        :  ynames_str =  ' '.join( xynames[1:] )


      subdir = ''
      if savefile != None:

          if type(savefile) == types.TupleType or type(savefile) == types.ListType :

                if type(savefile[0]) == types.ListType:
                   subdir   = savefile[0][1:]
                   savefile = savefile[1]
                else:
                   subdir   = savefile[1:]
                   savefile = savefile[0]




          rootfilename = savefile
          if re.search('auto', savefile, re.I ):
               if titletxt != None:
                  savefilename = titletxt
               else:
                  savefilename = ynames_str
          else:
                  savefilename = rootfilename
          if re.search('no\s*save', savefile, re.I ):
                  savefilename = None
                  savefile     = None
      else:
               if titletxt != None:
                  savefilename = titletxt
               else:
                  savefilename = ynames_str


      if titletxt == None :

             wtitle = self.graph_title.get()
             if wtitle.strip() != '':
                 titletxt = wtitle.strip()
             if savefile != None:
                 titletxt = savefile

      if titletxt == None :
             titletxt = ynames_str















      self.plot_position       = self.update_entry_box( self.plot_position, self.wplot_position )
      self.color_list          = self.update_entry_box( self.color_list,          self.wcolor_list )
      self.legend_location     = self.update_entry_box( self.legend_location,     self.wlegend_location )
      self.conditions_location = self.update_entry_box( self.conditions_location, self.wconditions_location )



      if plottype == 'xy_scatter_plot':

#          self.plot_interactive_graph( logfilename, xynames,  conditions )
        self.fig.clf()
        self.ax = self.fig.add_subplot(1,1,1)
        self.fig.subplots_adjust( left=self.plot_position[0], right=self.plot_position[1], top=self.plot_position[2], bottom=self.plot_position[3]  )


      elif plottype ==  'polar_plot':
        self.fig.clf()
        self.numcontours = self.update_entry_box( self.numcontours, self.wnumcontours)

        if 0:  # don't display Smith Chart image
            self.ax = self.fig.add_subplot(1,1,1, alpha=0.5, polar=False)
            self.fig.subplots_adjust( left=self.plot_position[0], right=self.plot_position[1], top=self.plot_position[2], bottom=self.plot_position[3]  )
            axis('off')
            img = imread( 'Fig1_SmithChart.png' )
            img = img * 1.0
            self.ax.imshow( img  )
            pos = [  self.plot_position[0],self.plot_position[1],self.plot_position[2],self.plot_position[3]]
            #       xoff  yoff
            pos = [ -0.047, 0.223,   0.9 , 0.56 ]
            axes( pos, alpha=1, polar=True)
            axis('off')
            grid(True)
            self.ax = gca()
        else:
            self.ax = self.fig.add_subplot(1,1,1, alpha=0.5, polar=True)
            self.fig.subplots_adjust( left=self.plot_position[0], right=self.plot_position[1], top=self.plot_position[2], bottom=self.plot_position[3]  )




      if 1:
        self.xaxis_limits = self.get_axis_limits( self.xlimits, self.xscl_min.get(), self.xscl_max.get() )
        self.yaxis_limits = self.get_axis_limits( self.ylimits, self.yscl_min.get(), self.yscl_max.get() )

        if series_data != []:

          xname = xynames[0]
          yname = xynames[1]



          self.ax.set_title( titletxt )
          self.graph_title.set( titletxt )


          if plottype != 'polar_plot' :
              xlab = self.ax.set_xlabel( xynames[0] )
              ylab = self.ax.set_ylabel( ynames_str )




          c = d = None

          self.plot_lineref = {}
          self.plot_xdata = {}
          self.plot_x2data = {}
          self.plot_ydata = {}
          self.plot_rndata = {}
          self.plot_data_color = {}
          self.plot_sn_full = {}
          self.plot_xpol = {}
          self.plot_x2pol = {}
          self.plot_ypol = {}
          xvals  = []
          x2vals  = []
          yvals  = []
          rnvals = []
          snvals = []
          cvals  = []
          dvals  = []
          lblvals  = []

          if plottype == 'polar_plot': ycount_start = 2
          else:                        ycount_start = 1

          yidx = 0


          for ycount in range( ycount_start, len(xynames)):

              #if ycount == 2 :
              #  self.ax2 = twinx()
              #  self.ax2.yaxis.tick_right()
              #  ylabel(xynames[2])


              sn  = ''
              sn_full = ''
              rn  = 0

              xpol   = []
              x2pol  = []
              ypol   = []
              rnpol  = []



              for sd,sn,sv in zip(series_data,series_unique_name_value_str, series_unique_values):




#                print '(plot...) sd,sn,sv = ', sd, sn, sv, series_unique_names

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
                      if len(sdt) >= 1 :
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

                  x2 = None
                  if plottype == 'polar_plot' :
                     x,rnl = self.get_selected_plot_data( sda, xynames, theta_idx )
                     x     = self.deg2rad(x)
                     x2,rnl = self.get_selected_plot_data( sda, xynames, r_idx )
                  else:
                     x,rnl = self.get_selected_plot_data( sda, xynames, 0 )

                  if x == []     : continue

                  y,rnl = self.get_selected_plot_data( sda, xynames, ycount )
                  if y == []: continue

#                  print '(plot_graph_data_core) rnl 1', rnl, y

                  if xynames[0] == 'Frequency of Spur (MHz)' or self.sort_data_on.get()  :
                      x, y, rnl = self.sort_selected_data( x, y, rnl )





                  xlen = len(x)
                  ylen = len(y)

                  if xlen < ylen:
                     y = y[:xlen]
                     rnl = rnl[:xlen]
                  if xlen > ylen:
                     x = x[:ylen]
                     if plottype == 'polar_plot' :  x2 = x2[:ylen]
                     rnl = rnl[:ylen]

                  if len(x) == 0 : continue

                  c, d, c_idx, d_idx = self.get_line_style_indexes( sv, series_unique_names, sdai, len(sd_new), yidx, len(xynames[1:]) )

                  sdi +=1

                  if sn == '' :
                     sn = xynames[ycount]   # make sure there is a label string
                     sn_full = sn
                  else:

                     # truncate the sn name so that it only contains the color and line series values
                     sn = ''
                     nget = self.color_series.get()
                     if nget != '':
                             for i,n in enumerate(series_unique_names):
                                if n == nget:
                                   sn = sv[i]
                             nget = self.line_series.get()
                             for i,n in enumerate(series_unique_names):
                                if n == nget:
                                   sn = sn + ' ' + sv[i]
                     else:
                          sn = xynames[ycount]
                     sn_full = sn

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



                  # This is code failing for some reason but I don't know why (ValueError Too many values to unpack !!!! FIXME FIXME FIXME !!!! )
                  try:
#                  if 1:
                     x,y,rnl = self.remove_bad_data( x, y, x2,rnl, self.xaxis_limits, self.yaxis_limits )
                  except Exception:  pass



                  # make sure there is at least one line series with an non empty sn name, (we get a legend.set_picker error if all sn's are empty)
                  if not done_a_plot and sn == '':  sn = ' '



                  marker    = self.update_entry_box( self.plot_marker, self.wplot_marker )
                  linewidth = self.update_entry_box( self.plot_linewidth, self.wplot_linewidth )
                  ###############################################################################
                  #  And finally, here's what you've been waiting for ...  the plot command !!!

                  if plottype == 'xy_scatter_plot' :
                      line, = self.ax.plot( x, y, color=c, dashes=d, label=sn, marker=marker, linewidth=linewidth, picker=5 )
                      lbl =  line._label
                      done_a_plot = True
                  else:
                      line = None
                      lbl = 'PoLaR'

                      # concatantate all the x, x2, and y data to form a single list
                      xpol.extend( x )
                      x2pol.extend( x2 )
                      ypol.extend( y )
                      rnpol.extend( rnl )

                  #
                  ###############################################################################


#                 print '(plot_graph_data_core)  _label =', xx._label



                  # save the data away so that it can be measured later if needed
                  xvals.append(x)
                  x2vals.append(x2)
                  yvals.append(y)
                  rnvals.append(rnl)
                  snvals.append(sn_full)
                  cvals.append(c)
                  dvals.append(d)
                  lblvals.append( lbl )

                  # save the data in dicts so that we can access it for gui data probing
                  self.plot_lineref[    lbl ] = line
                  self.plot_xdata[      lbl ] = x
                  self.plot_x2data[     lbl ] = x2
                  self.plot_ydata[      lbl ] = y
                  self.plot_rndata[     lbl ] = rnl
                  self.plot_data_color[ lbl ] = c
                  self.plot_sn_full[ lbl ] = sn_full


                  rn = sda[0]

                  if '[csv] Script File Name' in self.data:
                      tname =  self.data[ '[csv] Script File Name' ][ rn ]
                      if re.search( r'\[Time\]', xynames[ycount] ):
#                         print '     .found time data to plot {%s}' % tname
                          pass

                  if re.search( '<emp-limits>', xynames[ycount] ) and  self.check_nominal_condition( rn ):
                     print "  .adding limits to plot"
                     self.add_all_limits( xynames[ycount], x, y, c, d, rn)

                  if re.search( r'\[Time\]', xynames[ycount] ):
                      txt = tname
                  else:
                      txt = sdai





              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
              ## End of ycount loop

              yidx += 1



              ########################################################################
              ## Plot the polar plot
              ####
              if 1 and plottype == 'polar_plot':


                  # Due to bugs in matplotlib we first need to do a couple of cleaning up things with the data

                  # In order for the polar contour plot to work
                  # the phase data needs to sweep from 0 to 2*pi
                  # but the data usually is from -pi to +pi. Therefore
                  # we need to add 2*pi to the negative xpol angle data
                  # to make the negative angles all positive
                  for xi in range(len(xpol)):
                       theta = xpol[xi]
                       if theta < 0 :
                           xpol[xi] = theta + 2*nu.pi

                  # To show the contours joining up between 350 and 0 degrees
                  # we need to duplicate the 0 degree data at 360 degree
                  # (or 359.9 to be more precise)
                  xpl = []
                  x2pl = []
                  ypl = []
                  for xp, x2p, yp in zip(xpol,x2pol,ypol):
                       if  -0.01 <= xp < 0.01:
                            xpl.append( 2*nu.pi*(359.9/360.) )
                            x2pl.append( x2p )
                            ypl.append( yp )
                  xpol.extend( xpl )
                  x2pol.extend( x2pl )
                  ypol.extend( ypl )

                  # Save the polar data for future use
                  self.plot_xpol  = xpol
                  self.plot_x2pol = x2pol
                  self.plot_ypol  = ypol

                  # Get the min and max values for the data
                  idx_min, idx_max = self.get_minmax_idx( ypol )
                  xmin,  xmax   = self.get_minmax( xpol  )    # theta
                  x2min, x2max  = self.get_minmax( x2pol )    # r

                  # Create a Mesh grid to provide a continuous surface on which
                  # the contours can be calcuulated on.
                  # Set the resolution of the grid
                  n = 50
                  xser  = linspace(xmin,xmax, n)
                  x2ser = linspace(x2min,x2max, n)
                  X,X2  = meshgrid(xser,x2ser)
                  #                             theta  R     Y    theta, R
                  Z = matplotlib.mlab.griddata(xpol, x2pol, ypol,   X,   X2 )

                  # Set the axis to 0 to 1 for both R and theta.
                  # theta is fixed for theta
                  # and R is magnitude which has a range of 0 to 1
                  self.ax.axis( [0,1,0,1] )

                  # Do the contour polor plot
                  if self.contourfill.get():
                      CS = self.ax.contourf( X, X2, Z, int(self.numcontours)  )
                      colorbar( CS, ax=None, aspect=20, shrink=0.5, pad=0.02, fraction=0.02, orientation='horizontal' )
                  else:
                      CS = self.ax.contour( X, X2, Z , int(self.numcontours), alpha=1.0, colors=c, linestyles='solid', linewidths=linewidth  )
                      self.ax.clabel(CS, fontsize=9, inline=1)

                  #  CS = self.ax.pcolormesh( X, Y, Z, alpha=0.8 )   # pcolormesh runs a lot faster than pcolor for the polar plot!

                  # Draw the maximum value on the graph
                  yname = re.sub( r'%', '\%' , xynames[ycount] )
                  yname = re.sub( r'_', '' , yname )
                  if self.contourmaxval.get():
                      self.annotate_polar_val(   '%s _{max} = %0.3f' % ( yname, ypol[idx_max])   , idx_max, 0.43, yidx*0.03 - 0.005 )
                  if self.contourminval.get():
                      self.annotate_polar_val(   '%s _{min} = %0.3f' % ( yname, ypol[idx_min])   , idx_min, 0.43, yidx*0.03 - 0.025 )

                  # Draw dots where each loadpull sample was measured
                  if marker == '.':        mkr = '^'
                  else:                    mkr = marker
                  #
                  self.ax.scatter(xpol, x2pol,marker=mkr,s=1, alpha=0.2)

                  # Set the grid properties
                  setp( self.ax.get_yticklabels(), visible=False)
                  self.ax.set_rmax(1.0)
                  grid(False)

                  ## Write out an ERROR if multiple conditions were selected for the plot.
                  ## Polar Contour plots must only have one set of conditions.
                  ## Let the user know if multiple conditions were set.
                  vdict = {}
                  for name in self.series_seperated_list:
                      if name == 'VSWR' : continue
                      if name in self.data:
                          for rn in  rnpol:
                             val = self.data[name][rn]
                             if name not in vdict:
                                  vdict[name] = []
                             if val not in vdict[name]:
                                  vdict[name].append(val)
                  errstr = ''
                  for name in vdict:
                      if len( vdict[name] ) > 1:
                          errstr = '%s %s(%d),' % ( errstr, name, len(vdict[name]) )
                  if errstr != '':
                     errstr = '*** ERROR *** Multiple Conditions used for Polar Plot.\nPlease use the filter to select one set of conditions only.\n%s' % errstr
                     annotate( errstr, xy=( 0.05, 0.85 ) , textcoords='figure fraction')
                     print errstr

                  done_a_plot = True



          # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

          if c != None and d != None and self.spec_limits != None:
              self.add_spec_limits( c, [100,0] )


          if self.legend_location and done_a_plot and plottype != 'polar_plot':
                try:
                    self.legend = self.ax.legend(shadow = True,
                                            labelspacing = 0.001,
#                                            labelsep     = 0.001,
                                            loc  = self.legend_location,
                                            prop = matplotlib.font_manager.FontProperties(size='smaller'),
#                                            pad  = 0.01 )
                                            borderpad  = 0.01 )
                except:
                    self.legend = self.ax.legend(shadow = True,
#                                            labelspacing = 0.001,
                                            labelsep     = 0.001,
                                            loc  = self.legend_location,
                                            prop = matplotlib.font_manager.FontProperties(size='smaller'),
                                            pad  = 0.01 )
#                                            borderpad  = 0.01 )
                    

                self.legend.set_picker(self.my_legend_picker)





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
                            'Sub-Band'             ,
                            'Freq(MHz)'            ,
                            'Vramp Voltage'        ,
                            'Pwr In(dBm)'          ,
                            ''                     ,
                            'Segments'             ,
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
                 
                     values_list = []
                     vc = 0
                     
                     for rnl in rnvals:
                       for rn in rnl :
                            if rn != None and rn != '':
                              v = self.data[ name ][ rn ]
                      
                              if v != None and v != '' and v not in values_list:
                                  values_list.append( v ) 
                                  vc += 1
                     txt = '%s = %s' % ( tname, self.list2str( values_list ))
                 
#                     if name in  self.values_selected_dict:
#                       txt = '%s = %s' % ( tname, self.list2str( self.values_selected_dict[ name ]) )
#                     else:
#                       self.add_values_dict( name )
#                       txt = '%s = %s' % ( tname, self.list2str( self.values_dict[ name ]) )
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
              print "*** ERROR *** (plot_graph_data_core) There is no data for some of these axes '%s', please choose other axes, or select different filter values" % xynames




          ## ADD CODE TO LOOP ROUND MULTIPLE LIMITS SO THAT WE GET ZOOMED IN VERSIONS OF THE PLOTS IN ADDITION




#         print 'self.xaxis_limits', self.xaxis_limits
#         print 'self.yaxis_limits', self.yaxis_limits



          # Set the axes limits, the limits were calculated earlier on


          if plottype != 'polar_plot':
              if self.xaxis_limits != [] :
                  self.ax.set_xlim( ( self.xaxis_limits[0] , self.xaxis_limits[1] ) )

              if self.yaxis_limits != [] :
                  self.ax.set_ylim( ( self.yaxis_limits[0] , self.yaxis_limits[1] ) )

              self.ax.grid()

              # Set the number of grid lines

              g = self.xgrd_step.get()

              lim = self.ax.set_xlim()
              try:  self.ax.set_xticks( self.get_grid_ticks( lim, self.xgrid, g ) )
              except: pass


              g = self.ygrd_step.get()

              lim = self.ax.set_ylim()
              self.ax.set_yticks( self.get_grid_ticks( lim, self.ygrid, g ) )











          #--------------------------------------------------------
          # save the plot file
          #--------------------------------------------------------

#          print '(plot_graph_data_core) savefile=%s  savefilename=%s subdir=%s' % ( savefile, savefilename, subdir )

          self.savefilename = savefilename


          if savefile != None:


              savefilename = self.clean_savefilename( savefilename )

              self.save_plot_count = int( self.save_plot_count)
              if int( self.save_plot_count) >= 0:
                self.save_plot_count = self.save_plot_count + 1
                savefilename = 'P%03d_%s' % ( self.save_plot_count, savefilename )


              reldirname = ''
              ### if we have a non-null subdir then get the ARG save directory
              if subdir == '':
                 savefile_fullpath = os.path.join(  self.savedir , savefilename )
                 savefile_relpath  = savefilename
              else:

                 if subdir != '' and subdir != None and isinstance( subdir , types.ListType ) and len( subdir ) >=2:
                     # If we have an id number then we are doing an ARG run
                     # We will put all the plots into the a single all_plots directory
                     # We will also put the plots into a test based directory.

                     if self.parameter_plot_count >= 0:
                          self.parameter_plot_count  += 1


                     dir = os.path.join(  self.savedir, subdir[0] )
                     reldirname = subdir[0]

                     lst  = glob.glob(  dir  )
    #                print '(plot_graph_data_core) lst  = glob.glob(  %s  ) = %s' % ( dir, lst )
                     if len(lst) > 0:
                         dir = lst[0]
                     else:
                         os.mkdir( dir )

                     dirname = dir
                     savefile_fullpath = os.path.join(  dirname, savefile )
                     savefile_relpath  = os.path.join(  reldirname, savefile )



                 else:
                   print '*** ERROR *** (plot_graph_data_core) Incorrect savefile format , it should be a 2 or 3 element list [ file, subdir1, subdir2 ]', savefile

              savefile_fullpath = savefile_fullpath + '.png'
              savefile_relpath  = savefile_relpath + '.png'





              if done_a_plot:
                 print "....saving plot file: '%s'" % savefile_fullpath

                 self.root.update()
                 #self.root.update_idletasks()

                 try:
                   savefig( savefile_fullpath, dpi=100 )
                   self.png_filename    = savefile_fullpath
                   self.png_relfilename = savefile_relpath
                   self.png_dir         = dirname
                   self.png_reldir      = reldirname
                 except Exception:
                   print "*** ERROR *** could not save plot file '%s' (check permissions to write plot file in this directory)" % savefile_fullpath

                 if self.parameter_plot_count >= 0:
                      self.parameter_plot_count  += 1



              else:
                 print '   ... did not save a plot file due to a previous problem (look for any errors or warnings)'


              # make a link to the real plotfile
              if subdir != '' and subdir != None and isinstance( subdir , types.ListType ) and len( subdir ) >=2 and subdir[1] != None:

                 dir = os.path.join(  self.savedir, subdir[1] )

                 # create the subdir directory if needed
                 lst  = glob.glob(  dir  )
                 if len(lst) > 0:
                     dir = lst[0]
                 else:
                     os.mkdir( dir )


                 # Make a link from the subdir directory to the real plot file

                 tstr =  savefilename + '.png'

                 spath = os.path.join(  dir, tstr ) + '.lnk'
                 opath = self.png_filename


                 if self.os == 'PC':


#                                               xxmklink   spath  opath [ arg [ wdir [ desc [ mode [ icon[:n] ]]]]] [switches...]
#                    tstr = 'N:\\sw\\release\\XXMKLINK.EXE  "%s"  "%s"    ""     ""     ""     7  /q ' % (spath, opath)
                     tstr = 'N:\\sw\\release\\XXMKLINK.EXE  "%s"  "%s" ' % (spath, opath)
#                     op = commands.getoutput( tstr )

                     # Run the dos command but we don't want it to pop up a dos window each time it runs
                     # I found this code snippet that creates a subprocess with no dos window
                     # (Note commands.getouput() doesnt work on Windows - therefore use the subprocess module instead)
                     startupinfo = subprocess.STARTUPINFO()
                     startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                     op = subprocess.Popen(tstr, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
#                    print '(plot_graph_data_core) xxmklink command output: <%s>' % op
                     try:
                       op.close()
                     except Exception:
                       pass


                 if self.os == 'LINUX':
                     os.symlink( opath, spath )









          self.canvas.draw()
          self.root.update()


          #--------------------------------------------------------
          #  If this is an interactive plot_graph then we want to enter the matplotlib loop
          #--------------------------------------------------------

          if self.interactive:
              self.canvas.show()

          self.sel_object = None

          ret_val = [xvals, yvals, rnvals, snvals, cvals, dvals, full_condition_selected_str, xynames, ]

          self.plot_data = ret_val

          return ret_val
        else:
          return
      else:
        return


###################################################################################################
    def get_grid_ticks(  self, minmax, step,  form_step) :
         '''Gets a list of grid tick values used to for the grid lines of a graph
         If step is None it will automatically produce a set of gridlines between
         the minmax values, so that self.numgrids gridlines are displayed.
         
         Parameters:
             minmax:       List [min,max] used to define the start and finish grid line values
             step:         The value between each grid line, if None it will autocalculate the step to produce
             form_step:    This is the step value from the GUI, it overrides the 'step' value
         
         Returns:
             x:            List of values from min to max with a seperation of step (or form_step)
         '''


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
        ''' If in script mode this updates the entry box with the ipval, and 
            returns the same ipval, if in gui mode it ignores the ipval and 
            returns the value entered on the gui entry box window
            
        Parameters:
            ipval:  Value used in script mode to update the 'win' entery box
            win:    Entry Box id
        Returns:
            val:    In Gui mode value read from Entry Box, in Script mode it is ipval
            '''


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
            val =  val.strip()
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
#           else:
#               val = ipval


        try:
           val = float( val )
        except Exception:
           pass

#       print '(update_entry_box)  %s  ipval=<%s>, val=<%s> window=<%s> lenx=%s' % (self.run_mode, ipval, val, win, lenx)
        return val


###################################################################################################


    def get_axis_limits(  self, lims, lim_min_form, lim_max_form ) :
         '''In 'script' mode returns the lims axis limits. In Gui mode
         it returns axis defined using lim_min_form and lim_max_form
         (unless they are '' in which case lims is returned)
         Parameters:
              lims:            Used in script mode to define 
              lim_min_form:    The value of the axis minimum from the gui form
              lim_max_form:    The value of the axis maximum from the gui form
         Returns:
            List of 
            [ lim_min_form:    
              lim_max_form:     
              diff:]           The difference between lim_max_form and lim_min_form  
         '''


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
         '''Returns the nearest number to num that starts with a 1 2 or 5 digit
         
         Parameters:
             num:      Any number value
         Returns:
             val:      Number starting with 1,2,5 that is nearest to num
         '''

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
         '''Takes a string to be used as a filename and removes or replaces any characters
         that might cause problems when used in a filename (windows and linux)
         
         Parameters:
            savefilename:    Input filename
         Returns:
            savefilename:    Output filename (modified to change illegal characters)
         '''


         if savefilename != None:


#            savefilename = re.sub(r'\..*$',              '',  savefilename )    # remove any extentions
            if not re.search(r'\+\/\-',savefilename):
                savefilename = re.sub(r'.*[\\\/]',           '',  savefilename )    # remove the directory pathnames
            savefilename = re.sub(' ',                   '_', savefilename )    # turn all spaces into underscores to help with linux filenames
            savefilename = re.sub('\[Time\]',            '',  savefilename )    # remove the special axis prefixes [Time]
            savefilename = re.sub('\[T90%\]',             '',  savefilename )    # remove the special axis prefixes [
            savefilename = re.sub('\[csv\]',             '',  savefilename )    # remove the special axis prefixes [
            savefilename = re.sub('[{}\[\]<>\(\)\.\,=:/\\\n\*]', '', savefilename )    # remove any characters that arn't usually part of a filename e.g. , < > ( )

         return savefilename[:200]



###################################################################################################

    def save_plot( self ):
         '''Saves the plot file. Prompts the user for the filename to save the plot.
         
         Parameters:  None
         Returns:     None
         Updates:  
              self.read_pygram_config( 'savedir' )
              self.savefilename
              self.savedir    
         '''

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

    def save_csv( self ):
         '''Saves the current data in a csv file (obsolete)
         '''


         savefilename = self.clean_savefilename( self.savefilename )

         savefilename = asksaveasfilename( defaultextension='.csv',
                                     title='Save Excel csv Filename',
                                     initialfile=savefilename+'.csv',
                                     filetypes=[('comma seperated values', '*.csv'),] )

         if savefilename == '': return




#        self.plot_data = [xvals, yvals, rnvals, snvals, cvals, dvals, full_condition_selected_str, xynames]

         print "...saving excel csv file: '%s'" % savefilename

         if len(self.plot_data) != 8:
            print '*** ERROR *** (save_csv) cannot save csv data because there is no graph data, replot and try again'
            print len( self.plot_data )
            return

         xynames = self.plot_data[ 7 ]
         col_list = []
         col_list[:] = xynames



         meas_col_list = ['2nd Harmonics Amplitude(dBm)', '3rd Harmonics Amplitude(dBm)',
            'PAE(%)',  'Pout(dBm)', 'Pwr Variation(dB)', 'Sw Pwr 400KHz(dBm)',
            'Ref Pout(dBm)', 'SN', 'SN_fld0', 'Serial Number',
            'Test Date & Time', 'TestName',  'Vbat(Volt)', 'Vbat_I(Amp)',
            'Vbat_V(Volt)', 'Vramp Voltage', 'chipid']

         for c in self.value_dict_names:
            if c not in col_list and c in self.data:
                col_list.append( c )


         for c in meas_col_list:
            if c not in col_list and c in self.data:
                col_list.append( c )


         fop = open( savefilename, 'w' )


         for col in  col_list:
             print >> fop ,  "%s," % col,
         print >> fop, ''

         rnvals = self.plot_data[ 2 ]

         rncount = 1
         for rnl in rnvals:
             for rn in rnl:

                 for col in  col_list:
                        val = self.data[ col ][rn]
                        try:
                            val = float( val )
                        except Exception:
                            if val != None and val != '':
                               val = "%s" % val
                            else:
                               val = ''

                        print >> fop ,  '%s,' % val,
                 print >> fop, ''
                 rncount += 1


         print '(save_csv) done!  wrote %d lines' % rncount
         fop.close()


###################################################################################################


    def compare_columns(self, a, b):
        '''Sort compare function on ascending self.sort_column
        '''

        return cmp(a[self.sort_column], b[self.sort_column])

###################################################################################################

    def sort_selected_data( self, x, y, rnl ):
        '''  Sort the x and y list data, reorder the lists so that the x data is
        increasing 
        
        Parameters:
            x:       X series data list
            y:       Y series data list
            rnl:     Record Number series data list
        Returns:
            xn:      New X series data list where all data is ascending
            yn:      Coresponding Y series data list
            rnln:    Coresponding Record Number list
            '''


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
       '''Go through the current nominal conditions and check whether this record 
       number matches.
       
       Parameters:
               rn:    Record number to compare
       Returns:    
               1 if matches, 
               0 if no match
       Reads:          
               self.ref[]    
               self.data [ 'Temp(C)' , 'Freq(MHz)', 'Vbat(Volt)', 'Pwr In(dBm)' ]
       '''


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
        '''Adds EMP specific limits to the graph

        Parameters:
            name :
            x    :    list of x data to be plotted
            y    :    list of y data to be plotted
            c    :    color
            d    :    line style
            rn   :    list of record numbers to be plotted

        Returns :   None'''

        x,y =  self.make_data_monatonic(  x , y )

        if name == 'Gain AM/(VAM-offset) (dB) <emp-limits>' :
            self.add_plot_emp_gain_limits( name, x, y , c, d, rn )

        elif name == 'Gain AM/(VAM-offset) Slope - Ref (dB/dB) <emp-limits>' :
            self.add_plot_emp_gain_slope_limits( name, x, y , c, d, rn )

        elif name == 'AM-PM Slope - Ref (deg/dB) <emp-limits>' :
            self.add_plot_emp_phase_slope_limits( name, x, y , c, d, rn )



###################################################################################################
    def add_spec_limits( self, color, dashes ) :
           '''Plots a spec line or multiple spec lines to the graph.
             The spec line is defimed using the self.spec_limit variable. e.g.

                                 Yval     Label        line_thickness  line_color
           mag.spec_limits =  [ -19,  "3GPP min limit",    2 ,           'blue' ]

                                     x1y1     x2y2
           mag.spec_limits =  [ [ [[0,-19], [20,-19]],  "3GPP min limit", line_thickness, blue ], ... ]

           Reads:   self.spec_limit

           Paramaters:
               color :  Default color of the spec line, used only if it is not specified in the self.spec_limit definition
               dashes:  Default line style of the spec line, used only if it is not specified in the self.spec_limit definition

           Returns   :  None
           '''



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

             # if we have no list get the current xaxis
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

             xn = []
             for xt in x:
                xn.append( float(xt) )
             x = xn

             yn = []
             for yt in y:
                yn.append( float(yt) )
             y = yn


             if len(pl) > 1 and pl[1] != None :

                txtx = nu.mean(x)
                txty = nu.mean(y)
                text      = pl[1]
                annotate( text, xy=(txtx, txty),  color=color, textcoords='offset points', xytext=(0,3),
                    horizontalalignment='center', verticalalignment='bottom', fontsize=10)

#          self.spec_limits = None


###################################################################################################

    def add_plot_emp_gain_slope_limits( self, name, x, y , c, d, rn ) :
       '''Adds gain slope limits onto the graphs for EMP spec
       
       Parameters:
            name:    Not used!
            x:
            y: 
            c: 
            d:
            rn:
       Returns:
            None
       '''


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
       '''Adds phase slope limits onto the graphs for EMP spec
       
       Parameters:
            name:    Not used!
            x:
            y: 
            c: 
            d:
            rn:
       Returns:
            None
       '''



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
       '''Check that all values in x are increasing and monoatonic
        if not then discard the rotton x and y values

       Parameters:
           x  :  List of x data points
           y  :  List of y data points
       Returns   :
           x_new : List of x data points with, smallest first, all x values
                   which are 'out of sequence' are removed
           y_new : List of y data points coresponing to the x data points.
'''



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

    def remove_bad_data( self, x,y, x2, rnl, xslim, yslim ):
       '''Check that all values in x and y are valid numbers
       if not then discard the rotton x and y values from the X and y lists.
       Also if the any of the values are greater than the axes limit value then
       limit the value in the plot to 10x the axes limit , this stops matplotlib
       trying to render hopelessly large graphs (I think)

       Parameters :
           x :     List of x data points
           x2:     List of x2 datapoints (for polar plots) = None for non polar plots
           y :     List of y data points
           rnl :   List of coresponding record numbers to the x, y data points
           xslim : X axis limit list = [ xmin,xmax ]
           yslim : Y axis limit list = [ ymin,ymax ]
       Returns:
           x_new : New list of X data points with bad data removed
           x2_new: New list of X2 data points with bad data removed (=None if x2 is None)
           y_new : New list of Y data points with bad data removed
           rnl_new : New list of record numbers with bad data removed
       '''

       x_new = []
       x2_new = []

       y_new = []
       rnl_new = []

       if x2 == None :  x2t = x
       else          :  x2t = x2


#       print '(remove_bad_data) 1 rnl,x,y=', rnl,x,y,x2t,xslim, yslim

       maxscale = 10
       if xslim != []:
            diff = abs( xlimits[1] - xlimits[0] ) + maxscale
            xlimits = [ xslim[0] - diff ,  xslim[1] + diff  ]
       if yslim != []:
            diff = abs( ylimits[1] - ylimits[0] ) + maxscale
            ylimits = [ yslim[0] - diff ,  yslim[1] + diff  ]

#       print '(remove_bad_data) 1a len rnl,x,y=', len(rnl),len(x),len(y),len(x2t)

       for xi,x2i,yi,rni in zip(x,x2t,y,rnl):
         if not isnan(xi) and not isnan(x2i) and not isnan(yi) :

           if xslim != []:

              if xi > xlimits[1] : xi = xlimits[1]
              if xi < xlimits[0] : xi = xlimits[0]

           x_new.append(xi)
           x2_new.append(x2i)

           if yslim != []:
              if yi > ylimits[1] : yi = ylimits[1]
              if yi < ylimits[0] : yi = ylimits[0]

           y_new.append(yi)
           rnl_new.append(rni)

       if x2 == None: x2_new = None

#       print '(remove_bad_data) 2 rnl,x,y=', rnl_new,x_new,y_new
#       print ''

       return x_new, x2_new, y_new, rnl_new

###################################################################################################

    def add_plot_emp_gain_limits( self, name, x, y , c, d, rn ) :
       '''Adds gain limits onto the graphs for EMP spec
       
       Parameters:
            name:    Not used!
            x:
            y: 
            c: 
            d:
            rn:
       Returns:
            None
       '''



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
       '''Adds limits for EMP region onto the graph
       Parameters:
            x:
            y: 
            c: 
            d:
            lim:
            seperate:
            offset_x: 
            offset_y:
       Returns:
            None
       '''



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
        '''Debug function to show the x y mouse coordinates
        event1 and event2 are the press and release events
        
        Parameters:
            event1:    Button press event
            event2:    Button release event
        '''

        x1, y1 = event1.xdata, event1.ydata
        x2, y2 = event2.xdata, event2.ydata
        print "(%3.2f, %3.2f) --> (%3.2f, %3.2f)"%(x1,y1,x2,y2)
        print " The button you used were: ",event1.button, event2.button

###################################################################################################

    def loop( self ):
        '''Idle Loop Function. After all the non-interactive plots have been 
        run, wait in this Tk mainloop for interactive gui actions to occur
        This function needs to be added to the end of every script
        
        When entering the loop it will printout the audit string, and recalculate
        the self.values_dict array, and update the status at the bottom of the window
        
        Parameters:    None
        Returns:       None
        '''                          

        #-------------------------------------------------------------------------------
        # After all the non-interactive plots have been run, wait in this Tk mainloop for interactive gui actions to occur
        # This function needs to be added to the end of every script
        #-------------------------------------------------------------------------------\

        # update the filters
        self.wupdate_filter_cond_list( None )
        self.vlist.delete_all()

        self.gen_values_dict()
        self.root.update()

        print ''
        print self.get_audit_str()

        self.run_mode = 'gui'
        print '  ...waiting for user input'
        self.status.set( 'waiting for user input' )

        Tk.mainloop()

###################################################################################################
    def get_cond_val_from_rn( self, rn, ignore_lst ):
        '''Make up a string with all the conditions values found for a record number 
        in the self.data array. The conditions used are those defined by self.values_dict_names
        (minus any which start with'@' and any that are in the 'ignore_lst' parameter
        
        Parameters:
            rn:               Record Number to use for making the condition string
            ignore_list:      List of column names not to include when making the condition string
        Rerturns:
            tstr:             String containing a comma seperated condition values
            '''

        tstr = ''


#       print '(get_cond_val_from_rn)   list of conds'
        for col in self.value_dict_names:
#            print col, len(self.values_dict_count[col]), '=', self.data[col][rn], ';',

            if col[0] == '@' or col in ignore_lst or len( self.values_dict_count[col]) <= 1 : continue
#            if len( self.values_dict_count[col]) <= 1 or col in ignore_lst or col[0] == '@': continue

            tstr = tstr + '%s,' % self.data[col][rn]

#       print '\n retval=',  tstr

        return tstr


###################################################################################################
    def get_cond_str_from_rn( self, rn ):
        '''Make up a string with all the conditions found for a record number 
        in the self.data array. The conditions used are those defined by self.values_dict_names
        (minus any which start with'@' 
        
        Parameters:
            rn:               Record Number to use for making the condition string
        Rerturns:
            tstr:             String containing a new line seperated condition names and values
            '''



        tstr = ''
        opstr = ''
        col = 'linenumber'
        tstr = tstr + '%s=%s \n' % ( col, self.truncate_value( self.data[col][rn]) )
        for col in self.value_dict_names:


#          print  '(get_cond_str_from_rn)', col, len( self.values_dict_count[ col ] )

          if col not in [ 'HB_LB' ]:
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
        '''Function to pick up the legend patch. (found on google somewhere)
        '''
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
        '''Function to perform when releasing the button over the canvas.
        If an annotation is displayed it will delete the annotation on button release
        unless the shift key is pressed.

        Parameters:    
            event:     Mouse event
        Returns:       None
         '''

#       print '(on_button_release)', event.__dict__
#       self.key = event.key

        # if we've got the legend then update the legend location in the gui control entry box
        if self.gotLegend == 1:
            self.gotLegend = 0
            # write the legend location back to the format tab entry box
            txt = '%0.3f %0.3f' % ( self.legend_location[0], self.legend_location[1] )
            self.wlegend_location.set( txt )
        self.pick_count_total = 0
        self.pick_data = False
        self.something_picked = False
        
        # If we have an object selected and the no shift key is pressed then delete the last text
        if self.sel_object != None and self.key != 'shift':
#          print '(on_button_release)', self.sel_object, self.key, event.__dict__
#          x = self.sel_object.findobj()
            x = gca()
#         print 'dir  gca ', dir( x.texts )
            del gca().texts[-1]

        # if no object is selected and we have a control key pressed then delete the last text
        if self.sel_object == None and self.key == 'control':
            x = gca()
            del gca().texts[-1]



        self.canvas.draw()

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .


    def on_motion( self, event  ):
        '''When moving the mouse over the canvas, move the object that is selected
        and calculate the current mouse position and the starting mouse position when
        the object was first picked.
        
        Parameters:    
            event:     Mouse event
        Returns:       None
        '''


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
          '''When the mouse button is pressed over the canvas, it selects the
          data point on the graph that is closest to the mouse position and 
          displays an annotation showing the values and conditions of the data 
          point
        
          Parameters:    
              event:     Mouse event
          Returns:       None
          '''
    
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
                   rn = self.plot_rndata[ sn ][ ind ]
                   sn_full = self.plot_sn_full[ sn ]
                   cond_str = self.get_cond_str_from_rn( rn )
                   txt = 'X=%s    Y=%s\n%s\n%s' % (self.plot_xdata[ sn ][ ind ], self.plot_ydata[ sn ][ ind ], sn_full, cond_str)


                   v = self.ax.get_xlim()
                   xinc = abs( v[0]-v[1] ) * 0.1
                   v = self.ax.get_ylim()
                   yinc = abs( v[0]-v[1] ) * 0.1
                   xy_data = (self.plot_xdata[ sn ][ ind ], self.plot_ydata[ sn ][ ind ])
                   xy_text = (xy_data[0]-xinc , xy_data[1]+yinc)

                   if sn in self.plot_data_color:
                      arrow_color = self.plot_data_color[ sn ]
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
                   print "(on_button_press) Line not found in self.plot_rndata dict,  clicked on line '%s', ind=%s\n  List of lines available:" % ( str(sn), str(ind) )
                   for s in self.plot_rndata:
                      print "                    '%s'"% s




# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .


    def on_pick( self, event  ):
         '''Picks an object on the canvas 
        
         Parameters:    
              event:     Mouse event
         Returns:       None
         '''

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

         if self.gotLegend:
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
####  GUI Initialization
###################################################################################################


    def win_init( self ):
          '''Draw the main matplot graph plotting area
          Parametrers: None
          Returns:     None
          '''



          #----------------------------------------
          # Draw the main matplot graph plotting area
          #----------------------------------------

          #self.fig = figure(figsize=(11,5))
          self.fig = figure(figsize=(12,5))
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
          printgr = Tix.Button(butfrm, name='save',    text='Save\nPlot',    width=5, height=2, command=self.save_plot)                .grid( column=1, row=0, sticky=Tix.S)
          export  = Tix.Button(butfrm, name='export',  text='Export\nExcel', width=5, height=2, command=self.save_csv)                 .grid( column=2, row=0, sticky=Tix.SW)
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

          loadfile     = Tix.Button(tabfrm, name='loadfile',  text='Load\nLogfile',   width=8, command=self.wloadfile  ) .grid( column=1, row=1 )
          loaddb       = Tix.Button(tabfrm, name='loaddb',    text='Load\nDataPower', width=10, command=self.wloaddb )    .grid( column=2, row=1 )
          clearfile    = Tix.Button(tabfrm, name='clearfile', text='Reset\nLogfiles', width=8, command=self.wclearfiles) .grid( column=3, row=1 )
          Tk.Label(  tabfrm, text='')                   .grid( row=2, column=2 )
          loadgip      = Tix.Button(tabfrm, name='loadgip',   text='Load and Run\nARG Script',     width=14, command=self.get_arg_user_inputs_dialog  )   .grid( column=2, row=3 )

          
          self.vramp_search_enable     = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Use Vramp Search\nto calc\nRef Pout(dBm):' )                     .grid( column=3, row=4,sticky=Tk.S)
          Tk.Checkbutton( tabfrm, name='vramp_search_entry' , variable=self.vramp_search_enable )  .grid( column=3, row=3,sticky=Tk.N)
          self.vramp_search_enable.set( True )
          


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
              names   = Tk.Listbox(tabfrm, name='lb', width=40, height=30, yscrollcommand=axis_sb.set, exportselection=0, selectmode=Tk.EXTENDED)
              axis_sb.config(command=names.yview)

              names                                                                  .grid( columnspan=3, column=0, row=2)
              axis_sb                                                                .grid( columnspan=3, column=3, row=2, sticky='wns')


              if xy == 'X' :
                self.xaxis_col_list  = names
              if xy == 'Y' :
                self.yaxis_col_list  = names



              # label to show the selected axis name
              Tk.Label( tabfrm, font=("Helvetica", fsz), textvariable=base_name, width=30)     .grid( columnspan=3, column=0, row=4, sticky='w')

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
          flist.config(separator='.', width=40, height=8, drawbranch=0, indent=10)
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
          vlist.config(separator='.', width=40, height=8, drawbranch=0, indent=10)
          vlist.column_width(0, chars=30)
          vlist.column_width(1, chars=6)
          vlist.column_width(2, chars=7)

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

          self.wnumcontours     = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Default Number of Contour Lines (for polar plots):', font=("Helvetica", fsz) ) .grid( columnspan=5, column=0, row=21, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.wnumcontours )                      .grid( columnspan=3, column=0, row=22, sticky='w')
          self.update_entry_box( self.numcontours, self.wnumcontours )

          self.contourfill    = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Filled Contour Plot',  font=("Helvetica", fsz) )  .grid( column=1, row=23, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.contourfill )                 .grid( column=2, row=23, sticky='w')
          self.contourfill.set( False )

          self.contourmaxval    = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Display Max Contour Value',  font=("Helvetica", fsz) )  .grid( column=1, row=24, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.contourmaxval )                     .grid( column=2, row=24, sticky='w')
          self.contourmaxval.set( True )

          self.contourminval    = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Display Min Contour Value',  font=("Helvetica", fsz) )  .grid( column=1, row=25, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.contourminval )                     .grid( column=2, row=25, sticky='w')
          self.contourminval.set( True )



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
        '''Updates the graph title from gui control entry box
        Parameters: None
        Returns:    none
        Reads:      self.graph_tile   gui entry box
        '''

        title( self.graph_title.get() )



#############################################################################################################
    def win_load( self, logfile=None, csvfilename=None, num_records=0 ):
          '''Updates the list of columns in the gui, and is listed on each of the axes, and on the fileter page
          which also includes the color and line style selection boxes.
          This should be run every time the list of columns changes

          Parameters:
             logfile:    (optional default: None) File to display in the Logfile file list window
             csvfilename:    (optional default: None) File to display in the Logfile file list window
              
             num_records: (optional default: 0)
          Returns:
          '''


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


              if cname not in self.data: continue

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

          # before we clear everything from the Axis column lists
          # record the selection so that we can reapply it afterwards

          xnames_sel_lst = []
          xysel_lst =  self.xaxis_col_list.curselection()
          for i in xysel_lst:
             xnames_sel_lst.append(  self.xaxis_col_list.get( int(i) ) )

          ynames_sel_lst = []
          xysel_lst =  self.yaxis_col_list.curselection()
          for i in xysel_lst:
             ynames_sel_lst.append(  self.yaxis_col_list.get( int(i) ) )

          fnames_sel_lst = []
          xysel_lst =  self.filter_column_list.curselection()
          for i in xysel_lst:
             fnames_sel_lst.append(  self.filter_column_list.get( int(i) ) )


          # clear the listboxes

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


          # Reselect all the names that were originally selected (if we can)

          for i in range(  self.xaxis_col_list.size() ):
              if    self.xaxis_col_list.get(i) in   xnames_sel_lst:
                    self.xaxis_col_list.activate(i)
                    self.xaxis_col_list.selection_set(i)
                    self.xaxis_col_list.see(i)

          for i in range(  self.yaxis_col_list.size() ):
              if    self.yaxis_col_list.get(i) in   ynames_sel_lst:
                    self.yaxis_col_list.activate(i)
                    self.yaxis_col_list.selection_set(i)
                    self.yaxis_col_list.see(i)

          for i in range(  self.filter_column_list.size() ):
              if    self.filter_column_list.get(i) in   fnames_sel_lst:
                    self.filter_column_list.activate(i)
                    self.filter_column_list.selection_set(i)
                    self.filter_column_list.see(i)






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
          '''Load the Xaxis and Yaxis Tab pages



          
          Parameters:
              xynames:  List of x and y axis names
          Returns:      None
          '''






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
                     '''Selects the 'name' in the listbox
                     
                     Paramters:
                          name:      name to select
                          listbox:   Window Id for the listbox
                     Returns:        True if found, False if 'name' was not found
                     '''

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
         '''Converts a list of values into space seperated string
         Each of the values are truncated (truncate_value)
         
         Parameters:
             lst:      List of values
         Returns:
             txt:      String containing all truncated values seperated by ' ' char
         '''

         txt = ''
         for i in lst:
            if i == None : continue
            txt = txt + ' ' + str(  self.truncate_value( self.get_filename_from_fullpath( i ) ) )

         return txt.strip()


###############################################################
##### DataPower Functions
###############################################################


    def db_make_dict( self, topkey, key, value, cond='' ):
      '''Makes a db dictionary using key, value, and cond
      
      Parameters:
           topkey:
           key:
           value:
           cond:
      Returns:
           k2n:       dictionary 
      '''


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
      '''Create a new window for entering the database results
      Parameters:   None
      Returns:      None
      '''



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
      '''Opens a connection to the Oracle datapower database
      
      Parameters:
           None
      Returns:
           cursor:      DB Id handle
      '''

      import cx_Oracle

      db =  cx_Oracle.connect('mydpuser','hard2guess','ssvrr02/dpower')
      cursor = db.cursor()
      return cursor

#####################################################################################


    def db_get_key_data( self, topkey, key, cond='' ):
      '''Gets data from the database
      
      Parameters:
            topkey:
            key:
            cond:
      Returns:
            rows:
      '''

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
#### Configuration Functions
#####################################################################################
    def read_pygram_config( self, param=None ):
         '''Reads PYGRAM configuration data from the config file
         
         Parameter:
              param:   Key name 
         Returns:
              Value of param
         Reads:
              File self.pyconfig_file
         '''



         try:
            fip = open( self.pyconfig_file )

            for line in fip:
                x = re.search( r'^\s*(\S+)\s+(.+)', line )
                x = x.groups()
                if len(x) == 2:
                   key = x[0].strip()
                   val = x[1].strip()

                   # if val has <nl> then split into separate lines
                   val = re.sub( '<nl>', '\n', val )

                   if key == param or param == None:
                     self.pyconfig[ key ] = val

            fip.close()



         except Exception:
            print "*** warning *** (read_pygram_config) unable to read pygram configuration file '%s'" % self.pyconfig_file


         if param != None and param in self.pyconfig:
#            print "      .(read_pygram_config) reading config param ( %s = %s ) in file '%s'" % (param,self.pyconfig[ param ],self.pyconfig_file)
            return self.pyconfig[ param ]
         else:

            return ''


#####################################################################################
    def save_pygram_config( self, param, value ):
         '''Updates PYGRAM configuration data in the config file
         
         Parameter:
              param:   Key name 
              value:   Value of param
         Returns:
              None
         Updates:
              File self.pyconfig_file
         '''


         value = str(value)

         self.read_pygram_config()

         self.pyconfig[ param ] = value

         fop = open( self.pyconfig_file, 'w' )

         for key, val in self.pyconfig.iteritems():
             if val != '':
                 val = re.sub( '\n', '<nl>', val )
                 print >> fop, '%10s %20s' % ( key, val )
         fop.close()


#####################################################################################
########  ARGPRD  Entry Form  #######################################################
#####################################################################################
    def get_arg_user_inputs_dialog(self):
      '''Pops up a window form for the user to specify the input files and parameters
       for an ARGPRD script run
       There are 5 sections to the form:
           PRD select :  An area to specify the PRD file to use
           ATR Log sel:  An area to specify the ATR logfiles to read
           Result dir :  An area to specify the directory where the results will be stored
           Test select:  An area to define which types of tests are to be run
           Other Params: An area to provide extra info needed for the run

       All data entered into the form will be saved away into the config file.
       when the form is first opened it will populate the form with values saved from
       the previous run, read from the pygram config file.

       this function also checks the input data for any obvious errors.
       If an error is found it will

       Parameters:  None
       Returns:     None

       Updates:
            pygram.config file
            self.logfiles ...
      '''




      # Define the entry names used in the form
      self.gip_names_list = [ 'argscript',
                              'prdfile',
                              'resdir',
                              'testnum',
                              'runmode',
                              'copy_atrlogfiles_on',
                              'run_refpout_from_vrampsearch',
                            ]

      self.gip = {}      # this dict is going to be used for all the gui entry box variables





      ##########################################################
      #
      # Create a new window
      #
      ##########################################################

      self.gipwin = Tk.Toplevel( master=self.root, name = 'gipwin' )
      self.gipwin.title('Load & Run ARG Script')
      gipfrm  = Tix.Frame(self.gipwin, name='gipfrm')

      self.gipfrm = gipfrm

      i = 0

      Tk.Label(  gipfrm, text='')                   .grid( row=i, column=0 )
      i += 1

      # Add the ARG script file entry

      name = 'argscript'
      self.gip[ name ]  = Tk.StringVar(master=gipfrm)
      Tk.Label(  gipfrm, text="ARG script file")                                                                 .grid( row=i, column=0 )
      Tk.Entry(  gipfrm, name='%s_entry'%name , width=150, textvariable=self.gip[ name ] )                          .grid( row=i, column=1, sticky=Tk.W+Tk.E)
      Tk.Button( gipfrm, name='%s_button'%name, text="Browse",  width=7) .grid( row=i, column=2 )
      i += 1
      Tk.Label(  gipfrm, text='')                   .grid( row=i, column=0 )
      i += 1



      # Add the PRD file entry
      name = 'prdfile'
      self.gip[ name ]  = Tk.StringVar(master=gipfrm)
      Tk.Label(  gipfrm, text="PRD .xls file")                                                                      .grid( row=i, column=0 )
      Tk.Entry(  gipfrm, name='%s_entry'%name , width=150, textvariable=self.gip[ name ] )                          .grid( row=i, column=1, sticky=Tk.W+Tk.E)
      Tk.Button( gipfrm, name='%s_button'%name, text="Browse",  width=7 ) .grid( row=i, column=2 )
      i += 1
      Tk.Label(  gipfrm, text='')                   .grid( row=i, column=0 )
      i += 1



      # Add the ATR Log file entry

      name = 'atrfile'
      self.gip[ name ]  = Tk.StringVar(master=gipfrm)
      Tk.Label(  gipfrm, text="Load Logfiles:")                                              .grid( row=i, column=0 )
      Tk.Entry(  gipfrm, name='%s_entry'%name , width=150, textvariable=self.gip[ name ] )   .grid( row=i, column=1, sticky=Tk.W+Tk.E)
      Tk.Button( gipfrm, name='%s_button'%name, text="Browse",  width=7 )                       .grid( row=i, column=2 )

      Tk.Button( gipfrm, name='atr_remove_selected_button', text="Remove\nSelected",   width=7  ) .grid( row=i+1, column=2,sticky=Tk.N )
      Tk.Button( gipfrm, name='atr_remove_all_button',      text="Remove\nAll",   width=7  )      .grid( row=i+2, column=2,sticky=Tk.N )

      name =  'copy_atrlogfiles_on'
      self.gip[ name ]   = Tk.IntVar(master=gipfrm)
      Tk.Label( gipfrm, text='Copy\nLogfiles:' )                                                     .grid( column=2, row=i+3,sticky=Tk.S)
      Tk.Checkbutton( gipfrm, name='%s_entry' % name , variable=self.gip[ name ] )                   .grid( column=2, row=i+4,sticky=Tk.N)


      gipatrfrm = Tk.Frame(gipfrm, name='gipatrfrm')
      scrollbar = Tk.Scrollbar(gipatrfrm, orient=Tk.VERTICAL)
      self.atrlogfiles_listbox   = Tk.Listbox(gipatrfrm, name='lb', width=148, height=15, yscrollcommand=scrollbar.set,selectmode=Tk.EXTENDED)
      scrollbar.config(command=self.atrlogfiles_listbox.yview)
      self.atrlogfiles_listbox.grid  (column=1, row=0, sticky='w' )
      scrollbar.grid(column=2, row=0, sticky='wns' )

      gipatrfrm.grid( row=i+1, rowspan=4, column = 1 )

      i += 5
      Tk.Label(  gipfrm, text='')                   .grid( row=i, column=0 )
      i += 1




      # Add the Results Dir file entry
      name = 'resdir'
      self.gip[ name ]  = Tk.StringVar(master=gipfrm)
      Tk.Label(  gipfrm, text="Results Directory")                                                                  .grid( row=i, column=0 )
      Tk.Entry(  gipfrm, name='%s_entry'%name , width=150, textvariable=self.gip[ name ] )                          .grid( row=i, column=1, sticky=Tk.W+Tk.E)
      Tk.Button( gipfrm, name='%s_button'%name, text="Browse",  width=7 ) .grid( row=i, column=2 )
      i += 1
      Tk.Label(  gipfrm, text='')                   .grid( row=i, column=0 )
      i += 1




      # Add the Logfile Type and id number entry

      name = 'runmode'
      self.gip[ name ]  = Tk.StringVar(master=gipfrm)


      Tk.Radiobutton(gipfrm, text="Run all tests in script",   variable=self.gip[ name ], value='all')     .grid(column=1, row=i+0, sticky=Tk.W)
      Tk.Radiobutton(gipfrm, text="Run 'room' tests only",     variable=self.gip[ name ], value='room')    .grid(column=1, row=i+1, sticky=Tk.W)
      Tk.Radiobutton(gipfrm, text="Run 'temp' tests only",     variable=self.gip[ name ], value='temp')    .grid(column=1, row=i+2, sticky=Tk.W)
      Tk.Radiobutton(gipfrm, text="Run 'loadpull' tests only", variable=self.gip[ name ], value='loadpull').grid(column=1, row=i+3, sticky=Tk.W)
      Tk.Radiobutton(gipfrm, text="Run 's2p' tests only",      variable=self.gip[ name ], value='s2p')     .grid(column=1, row=i+4, sticky=Tk.W)
      Tk.Radiobutton(gipfrm, text="Run tests listed below",    variable=self.gip[ name ], value='list')    .grid(column=1, row=i+5, sticky=Tk.W)

      name =  'run_refpout_from_vrampsearch'
      self.gip[ name ]   = Tk.IntVar(master=gipfrm)
      Tk.Label( gipfrm, text='Use Vramp Search\nto calc\nRef Pout(dBm):' )                                 .grid( column=2, row=i+1,sticky=Tk.S)
      Tk.Checkbutton( gipfrm, name='%s_entry' % name , variable=self.gip[ name ] )                         .grid( column=2, row=i+2,sticky=Tk.N)



      i += 6


      name = 'testnum'
      self.gip[ name ]  = Tk.StringVar(master=gipfrm)
      Tk.Label(  gipfrm, text="Test Numbers")                                                                       .grid( row=i, column=0 )
      Tk.Entry(  gipfrm, name='%s_entry'%name , width=150, textvariable=self.gip[ name ] )                          .grid( row=i, column=1, sticky=Tk.W+Tk.E)
      i += 1
      Tk.Label(  gipfrm, text='')                   .grid( row=i, column=0 )
      i += 1


      # Finally the Run and Cancel buttons

      gipbtnfrm  = Tix.Frame(gipfrm, name='gipbtnfrm')
      Tk.Button( gipbtnfrm, text="Run",  width=7,   command=self.get_arg_user_inputs_dialog_run   ) .grid( row=0, column=0 )
      Tk.Button( gipbtnfrm, text="Cancel", width=7, command=self.get_arg_user_inputs_dialog_cancel) .grid( row=0, column=1 )
      gipbtnfrm.grid( row=i, column=1 )

      gipfrm.grid()

      # Fill the form with the values from the previous run (values stored in the pygram config file)
      self.read_arg_user_inputs_config()

      self.gipwin.update()



      # We will process the inputs to the form when a return is entered, or when when the left mouse button-1 is clicked over a button
      # Most of the form buttons do not have commands associated with them, and we rely on the button-1 event
      # to trigger the  'get_arg_user_inputs_do_entry'  function. Doing it this way makes it easier to have a single generic
      # 'get_arg_user_inputs_do_entry' function that can perform all the form input.
      self.gipwin.bind("<Return>",    self.get_arg_user_inputs_do_entry    )
      self.gipwin.bind("<Button-1>",  self.get_arg_user_inputs_do_entry    )


      return

######################################################################################
####  ARG Dialog Functions
#####################################################################################

    def get_arg_user_inputs_dialog_run(self):
       '''Function is run when the Run button is pressed. With all the values entered into the form
       It sets the main valiables required by the ARGPRD script, and saves the values in the config file.
       It uses the argscript file and run the argscript using execfile().
       '''

       # Start the run with a completely clean slate, (clear everything that moves)
       self.wclearfiles()

       self.argscript   =  self.get_arg_user_inputs_do_entry( event= 'argscript' ).strip()
       self.prdfile     =  self.get_arg_user_inputs_do_entry( event= 'prdfile'   ).strip()
       self.savedir     =  self.get_arg_user_inputs_do_entry( event= 'resdir'    ).strip()
       self.arg_runmode =  self.gip['runmode'].get()
       self.arg_testnum =  self.get_arg_user_inputs_do_entry( event= 'testnum'   ).strip()
       self.copy_atrlogfiles = self.gip['copy_atrlogfiles_on'].get()
       self.run_refpout_from_vrampsearch = self.gip['run_refpout_from_vrampsearch'].get()

       if self.run_refpout_from_vrampsearch:
          self.vramp_search_testname = self.vramp_search_testname_good
       else:
          self.vramp_search_testname = self.vramp_search_testname_bad
   
       


       # Read the list of atr logfiles
       lball = self.atrlogfiles_listbox.get(0, Tk.END )

       # join all the files together into a multiline string (concatenate the files with \n)
       self.atr_logfiles = []
       for n in lball:
            self.atr_logfiles.append(n)




       # Do some more checking and preparation stuff

       num_warnings = 0
#       if len( self.atr_logfiles ) == 0:
#            num_warnings += 1
#            showwarning('', 'No ATR logfiles were entered. Please enter one or more readable ATR logfiles)')

       if len( self.prdfile ) == 0:
            num_warnings += 1
            showwarning('', 'No PRD .xls file was entered. Please enter a readable PRD .xls file')

       if len( self.savedir ) == 0:
            num_warnings += 1
            showwarning('', 'No Result Directory was entered. Please enter the name of the directory where the results will be saved')

       if not os.access(self.savedir, os.R_OK):
            os.mkdir( self.savedir )
            if not os.access(self.savedir, os.R_OK):
                num_warnings += 1
                showwarning('', "Could not create the Results Directory '%s'\nPlease specify a valid root directory (and that you have permissions to create it)" % self.savedir )
            else:
                showinfo('', "Created new Results Directory '%s'" % self.savedir)


       if self.arg_runmode == 'list':
                tstr = re.sub( ',', ' ', self.arg_testnum.strip() )  # change any ',' delimiter to a space delimiter
                tstr = tstr.upper()
                self.arg_testnum_list =  tstr.split()                # split using the ' ' space character delimiter

                # Print warning if we don't have any valid test ID numbers specified
                if len( self.arg_testnum.strip() ) == 0 or len( self.arg_testnum_list ) == 0:
                    num_warnings += 1
                    showwarning('', "'Run List of Tests' was specified but no Test ID Numbers have been entered.\nPlease enter one or more valid Test ID Numbers (which must match the Test ID Number used in the PRD" )



       self.save_arg_user_inputs_config()

#       print '(get_arg_user_inputs_dialog_run) self.argscript   = ', self.argscript
#       print '(get_arg_user_inputs_dialog_run) self.prdfile     = ', self.prdfile
#       print '(get_arg_user_inputs_dialog_run) self.savedir     = ', self.savedir
#       print '(get_arg_user_inputs_dialog_run) self.arg_runmode = ', self.arg_runmode
#       print '(get_arg_user_inputs_dialog_run) self.arg_testnum = ', self.arg_testnum
#       print '(get_arg_user_inputs_dialog_run) self.copy_atrlogfiles = ', self.copy_atrlogfiles
#       print '(get_arg_user_inputs_dialog_run) self.logfilenames = ', self.logfilenames


       if num_warnings > 0 :
           return

       self.gipwin.destroy()

       # Run the Script File

       execfile( self.argscript, globals(), locals() )


       return


######################################################################################
    def get_arg_user_inputs_dialog_cancel(self):
       '''If the user clicks cancel it removes the form.
       but it does save the values in the config file
       '''

       # even though we are quitting, still save the settings as these
       # may be better than the previous ones
       self.save_arg_user_inputs_config()
       self.gipwin.destroy()



######################################################################################
    def get_arg_user_inputs_do_entry(self, event=None ):
       '''Does the updating of the form entry boxes and checks that the values are correct
       This is run when ever we enter a new value into the form. This is done under  the value entered is correct and updates the gui with the
       value.

       This function is run in several different ways when the user:
              - enters a value into the text entry box and hits return
              - Clicks on the Add or Browse button
              - When the user clcks on Run button and all inputs are re-checked.

       When a value is entered it is also saved in the config file
       '''

       # check that the entry is legal if not then popup a warning window

       # First determine what type of event caused this function to run
       #   either a button press, or text entry return


       if isinstance( event , types.StringTypes):       # Text entry
          entry_name = event
          entry_type = 'function_call'
       else:                                            # An Event such as Return key, or a Button Press


          widget_name = re.sub( r'.*\.' , '', str(event.widget) )


          #if it's not a button click or a return on the box entry then just return without doing anything
          if not re.search( '(_button|_entry)$', widget_name ):
              return

          if re.search( '_button$', widget_name ):
              entry_type = 'button_click'
          else:
              entry_type = 'return_key'

          entry_name = re.sub( '(_button|_entry)$', '', widget_name )




       if  entry_type == 'button_click':

           if   entry_name == 'argscript':
               val = self.get_readfiles_dialog( 'Select ARG python script to run', 'argdir' , ('Python', '*.py') )
           elif entry_name == 'prdfile':
               val = self.get_readfiles_dialog( 'Select PRD excel .xls file'     , 'prddir', ('Excel', '*.xls')  )
           elif entry_name == 'atrfile':
               val = self.get_readfiles_dialog( 'Select ATR Logfiles to load'    , 'loaddir', ('ATR Log', '*.log')  )
           elif entry_name == 'resdir':
               val = self.get_directory_dialog( 'Select ARG Report Save Directory', 'savedir' )

           elif entry_name == 'atr_remove_selected':

                sel = self.atrlogfiles_listbox.curselection()
                selc = []
                for s in sel:
                   n =  self.atrlogfiles_listbox.get( s )
                   selc.append( n )

                for n1 in selc:
                      lball = self.atrlogfiles_listbox.get(0, Tk.END )   # get the current of files
                      # then go through the current list and remove one file only at a time
                      for i, n2 in enumerate( lball ):
                         if n1 == n2:
                             self.atrlogfiles_listbox.delete( i )
                return

           elif entry_name == 'atr_remove_all':
                self.atrlogfiles_listbox.delete( 0, Tk.END )
                return

           val0 = val
           if isinstance( val , types.ListType ):

              if entry_name == 'atrfile':
                  for f in val:

                     # don't add the file if its there already
                     lball = self.atrlogfiles_listbox.get(0, Tk.END )
                     fnd_file = False
                     for n in lball:
                         if n == f:  fnd_file = True

                     if not fnd_file:
                         self.atrlogfiles_listbox.insert( Tk.END, f )
                  val = ['']

              val0 = val[0]

           if val != '':
              self.gip[ entry_name ].set( val0 )





       # if entry_name = prd_entry  check to see that the file exists

       # read the value from the entry text box
       val = self.gip[ entry_name ].get()
       try:    val = val.strip()
       except: pass

       # for the atr files if there is a

       if  entry_type == 'return_key' and entry_name == 'atrfile':
                 lball = self.atrlogfiles_listbox.get(0, Tk.END )
                 fnd_file = False
                 for n in lball:
                     if n == val:  fnd_file = True
                 if not fnd_file and val != '':
                     self.atrlogfiles_listbox.insert( Tk.END, val )


       # check that the files exist

       if entry_name in [ 'prdfile', 'atrfile', 'argscript', 'resdir']:
#                 print 'checking the existance of file', val
                 if not os.access(val, os.R_OK) and val != '' :
                     wstr = '%s file not found\n' % entry_name
                     wstr = '%s\n%s' % ( wstr, val)
                     showwarning('', wstr)


       # save the values away in the config file

       self.save_arg_user_inputs_config()

       return val





######################################################################################
    def  save_arg_user_inputs_config( self ):
       '''Saves the ARG Get user input settings into the config file, ready for next
       time the program is run

       Parameters:  None
       Returns:     None
       '''


       # Go through the list of entry boxes in the gip form and save the values away in the config file
       for name in self.gip_names_list:
             self.save_pygram_config( 'gip_%s' % name ,   self.gip[ name ].get() )



       # Save the atr logfiles from the listbox
       tstr = ''
       lball = self.atrlogfiles_listbox.get(0, Tk.END )

       # join all the files together into a multiline string (concatenate the files with \n)
       for n in lball:
          tstr = tstr + '\n' + n
       tstr = tstr.strip()
       if tstr != '':
               self.save_pygram_config( 'gip_%s' % 'atrlogfiles' ,  tstr )



       # Save the savedir
       self.save_pygram_config( 'savedir' ,  self.savedir )

######################################################################################
    def  read_arg_user_inputs_config( self ):
       '''Reads the ARG Get user input settings from the config file and
       populates the ARG get user inptut form

       Parameters:  None
       Returns:     None
       '''


       # Now populate the form with the values from previous runs by loading the data from the config data

       for name in self.gip_names_list:
           self.gip[ name ] .set(     self.read_pygram_config(   'gip_%s' % name ))

       logfiles = self.read_pygram_config(   'gip_%s' % 'atrlogfiles' ).splitlines()
       self.atrlogfiles_listbox.delete( 0, Tk.END )
       for logf in logfiles:
          if logf != '':
                self.atrlogfiles_listbox.insert( Tk.END, logf )

       if 'gip_copy_atrlogfiles_on' not in self.pyconfig:
            self.gip[ 'copy_atrlogfiles_on' ].set( 1 )

       if 'gip_run_refpout_from_vrampsearch' not in self.pyconfig:
            self.gip[ 'run_refpout_from_vrampsearch' ].set( 0 )


       if 'gip_runmode' not in self.pyconfig:
            self.gip[ 'runmode' ].set( 'all' )




#####################################################################################
#####################################################################################
##### GUI Functions
#####################################################################################
    def add_all_logfiles_dialog(self):
       '''Loads a list of Logfiles into pygram. The logfiles are either specified on the command line
       (usually only for Linux users) or it will pop up a dialog for the user to enter the filenames

       Parameters:  None
       Returns   :  None
       Updates   :  self.atr_logfiles'''


       if len(sys.argv[1:]) > 0 :
          self.atr_logfiles = sys.argv[1:]
       else:
          self.atr_logfiles = self.get_readfiles_dialog( 'Select ATR Log files to load', 'loaddir' ,  )

       for f in self.atr_logfiles:
            self.add_logfile( f )


#####################################################################################
    def copy_all_logfiles(self, logfiles_dir ):
       '''Copys all the logfiles listed in self.atr_logfiles into logfiles_dir.
       If logfiles_dir does not exist it will create it.

       Parameters:
          logfiles_dir     : Name of the directory in which to copy the files
       Returns   :
          None
       Reads     :
          self.atr_logfiles: List of logfiles which will be copied'''


       if not os.path.isdir( logfiles_dir ) :
              os.makedirs( logfiles_dir )


       for f in self.atr_logfiles:
            shutil.copy2( f, logfiles_dir )




#####################################################################################
    def get_readfiles_dialog(self, message, dirtype, def_filetype=None):
       '''Pops up a dialog and prompts the user to enter a list of filenames.
       It will check that each filename can be read.
       It will prompt the user with a dialog multiple times. This allows the user
       to specify multiple sets of files from multiple directories. Clicking on 'Cancel'
       will complete it. CTL Select is used to select multiple files from the dialog window.

       The directory of the first file file is saved away in the config file with the 'dirtype' key.
       This config file will be read subsequent times when pygram is rerun and will open the
       dialog at the last used directory.

       Parameters :
           message :   String to be displayed that instructs the user to select which files
           dirtype :   Type of purpose of file (e.g. 'loaddir' used to define atr logfiles) This
                         is used to save the saved directory configuration id
           def_filetype:  The default filetype extention to display in the dialog

       Returns
           filenames : List of full path filenames'''

       filenames = []

       if 1:

           dirname = self.read_pygram_config( dirtype )

           filetypes = [('logfile', '*.log'), ('csvfile', '*.csv'), ('text', '*.txt'), ('s2p', '*.s2p'), ('Excel', '*.xls'), ('all', '*.*')]

           if def_filetype != None:
              ft = [ def_filetype ]
              ft.extend( filetypes )
              filetypes = ft


           filenames = []
           f_lst = [ 'dummy' ]
           finstr = ''
#           while len( f_lst ) >= 1:

           if 1:
               f_lst = askopenfilename(
                                   initialdir=dirname,
                                   multiple=True,
                                   title='%s (%s)%s' % (message, dirtype, finstr),
                                   filetypes=filetypes )
               # add the selected files to our filenames list, but make sure they are not already there,
               # (just in case the user hit OK twice and renetered the same files twice)

               print '(get_readfiles_dialog)  f_lst =', [ f_lst ]

               #BUG in python http://bugs.python.org/issue5712
               if isinstance(f_lst, unicode):
                    f_lst = tuple(self._split_tkstring(f_lst))


               for f in f_lst:
                   if f not in filenames:
                      filenames.append( f )
               finstr = " (selected %d files)  click 'Cancel' if finished" % len(filenames)

               if filenames != [] and filenames[0] != '' :
                  dirname = os.path.dirname(  os.path.abspath(filenames[-1]) )

           if filenames == [] or filenames[0] == '' :
              print "\n*** ERROR *** (get_readfiles_dialog) No files were specified for '%s' (%s)\n" % ( message, dirtype )
              return



           self.save_pygram_config( dirtype, dirname )


       for f in filenames:
          if not os.access(f, os.R_OK):
               print "*** ERROR *** (get_readfiles_dialog) Cannot read or find (%s) file '%s'" % (dirtype, f)
          else:
#              print ".(get_readfiles_dialog) Selected (%s) file '%s'" % (dirtype, f)
               pass


       return filenames

#####################################################################################
    def get_savefile_directory_dialog(self):
       '''Get the name of the directory where the pypgram output files and plots
       will be saved

       Parameters : None
       Returns    : None
       Updates    : self.savedir'''


       self.savedir  = self.get_directory_dialog('Select Directory to Save Output Results', 'savedir')


#####################################################################################
    def get_directory_dialog(self, message, dirtype ):
       '''Pops up a dialog and prompts the user to enter a directory.
       If the directory does not exist it will create it (after prompting the user though).

       The directory name will be saved away in the config file with the 'dirtype' key.
       The config file will be read subsequently when pygram is rerun and will open the
       dialog at the last used directory.

       This dialog on Windows is not very friendly (thanks to the Tix/Tkinster/Gates)
       It seems to be ok for selecting existing directories, but care must be taken
       when creating new directories. You seem to have to navigate up a directory and
       enter the name of the directory in the box. Make sure the full path name of the
       directory is displayed correctly above the entry box.

       Parameters :
           message :   String to be displayed that instructs the user to select which files
           dirtype :   Type of purpose of file (e.g. 'loaddir' used to define atr logfiles) This
                         is used to save the saved directory configuration id
           def_filetype:  The default filetype extention to display in the dialog

       Returns
           filenames : List of full path filenames'''


       last_used_directory = self.read_pygram_config( dirtype )


       dirname = askdirectory( title='%s (%s)' % ( message, dirtype ) ,
                                    initialdir=last_used_directory , )

       dirname = os.path.abspath(dirname)

       if not os.path.isdir( dirname ) :
          if askyesno("Create New Directory?", "%s\nDirectory '%s' does not exist." % (message, dirname)):
              os.makedirs( dirname )

       if dirname == '' or dirname == () or not os.path.isdir( dirname ) :
          print "*** ERROR ***  (get_directory_dialog) No valid directory was specified for '%s' (%s)" % ( message, dirtype)
          return
       else:
          print "     .(get_directory_dialog) Selected '%s' (%s) directory '%s'" % (message, dirtype, dirname)


#       self.save_pygram_config( dirtype,  os.path.dirname( dirname )  )
       self.save_pygram_config( dirtype,  dirname )

       return dirname

#####################################################################################

    def _split_tkstring(self,text):
        '''Function for spliting a string returned form Tix askopenfile into a
        list of separate filenames. This gets reound a bug introduced in Python 2.6 in the Tix module'''

        while text:
            part, sep, text = text.partition(u' ')
            if part.startswith(u'{'):
                if part.endswith(u'}'):
                    yield part.lstrip(u'{').rstrip(u'}')
                else:
                    rest, sep, text = text.partition(u'}')
                    yield part.lstrip(u'{') + u' ' + rest
                    text = text[1:] #space
            else:
                yield part



#####################################################################################
    def wloadfile( self ):
         '''GUI function to loads a list of Logfiles into pygram.
         It loads the logfiles and writes out statistics about the data contained in the logfiles
         (print_column_list) (print_values_list) and updates the GUI and status messages.

         The directory of the first file file is saved away in the config file with the 'loaddir' key.
         This config file will be read subsequent times when pygram is rerun and will open the
         dialog at the last used directory.


         Parameters:  None
         Returns   :  None
         Updates   :  self.atr_logfiles'''


         last_used_directory = self.read_pygram_config( 'loaddir' )


         filenames = askopenfilename( defaultextension='.log',
                                     initialdir=last_used_directory,
                                     title='Select Log Files to Load',
                                     multiple=True,
                                     filetypes=[('logfile', '*.log'), ('csvfile', '*.csv'), ('text', '*.txt'), ('s2p', '*.s2p'), ('all', '*.*')] )

         #BUG in python http://bugs.python.org/issue5712
         if isinstance(filenames, unicode):
              filenames = tuple(self._split_tkstring(filenames))

         # get the checkbox that determines whether we are getting the nominal conditions based on vramp search tests
         if self.vramp_search_enable.get() :
             self.vramp_search_testname = self.vramp_search_testname_good
         else:
             self.vramp_search_testname = self.vramp_search_testname_bad



## >>>> ## temporary fix to work with python 2.6.2 ## askopenfilename doesn't return a list
##         filenames = [ filenames ]



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



#####################################################################################
    def gen_values_dict(self):
         '''Generates the values dictionary for the standard list of column names
         (i.e. the names listed in self.values_dict_names)

         Parameters: None
         Returns   : None
         Updates   : self.values_dict[]
         '''


         cll = []
         for n in  self.data:
            if n != '' :
               cll.append(n)
         cll.sort()

         for c in cll:
            if c in self.value_dict_names:
               self.add_values_dict( c )



#####################################################################################

    def find_clicked_object( self, event , click_type ):
        '''Trys to determine where the cursor is in relation to everything
           on the window


        Parameters :
            event      :  window manager event data
            click_type :  seems to be ignore this!!!

        Returns :
            graph_item , ctl_item

            where:
               graph_item :  either 'xaxis' 'yaxis' 'format' 'filter'
               ctl_item   :  if the user clicked on the 'ctlfrm' part of the window then ctl_item = event.widget and graph_item=''
        '''


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
        '''Calls do_event
        '''

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





    def do_event_obsolete( self, event, click_type ):
       '''Any time the user clicks on the left hand control region it generates an
       event which triggers this function.
       This function will process each button click

       Parameters:
            event      :  Event info from Tk
            click_type :  Further event information which pygram works out,
                            e.g. key buttonrelease doublepress
       '''


#       print '(do_event)', event.widget, click_type

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


####################################################################################


    def do_event( self, event, click_type ):
       '''Any time the user clicks on the left hand control region it generates an
       event which triggers this function.
       This function will process each button click

       Parameters:
            event      :  Event info from Tk
            click_type :  Further event information which pygram works out,
                            e.g. key buttonrelease doublepress
       '''


#       print '(do_event)', event.widget, click_type

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
#                print 'value clicked    = ', n, name, values
                
                try:
                  val_letter = n[0]
                except:
                  # nothing useful is selected therefore return without doing anything
                  return
                
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
                     self.value_dict_names.append( name )

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
 #            print '(wupdate_filter_cond_list)', c
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
#               print '(wupdate_filter_value_list)  values_list[ %s ] = %s %s' % ( name,self.values_dict[ name ], self.values_dict_count[ name ])
#               print '(wupdate_filter_value_list)',  len( self.data[ name ]), self.data[ name ]
                for v in self.values_dict[ name ]:
                  e = seq[j]
                  txt = str(self.truncate_value(v))
                  if len(txt) > 35:
                      txt = txt[:10] + '..' + txt[-22:]
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

