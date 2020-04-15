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


from __main__ import *


# Load the matplotlib and pylab libraries
#from   matplotlib.mlab    import load
import matplotlib
#import matplotlib.numerix as nx
import numpy as nu
from   pylab import *

import Tkinter as Tk
from   tkFileDialog   import askopenfilename, asksaveasfilename, askdirectory, askopenfilenames
from   tkSimpleDialog import askstring
from   tkMessageBox   import askyesno , showinfo, showwarning, showerror, askquestion
import ttk


from   matplotlib.widgets import Button, RectangleSelector
from   matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from   matplotlib.collections import LineCollection
from   matplotlib.colors import colorConverter
from   matplotlib.lines import Line2D   

import pylab as plb
import numpy as npy
from matplotlib.patches import Circle 	# for drawing smith chart

try:
    import scipy
except ImportError:
    print "*** ERROR *** scipy import failed! Please install 'scipy' on this computer"


# General libraries for doing useful stuff
import re , os, getopt, math, commands, csv, types
import glob, time, shutil, getpass, subprocess, traceback
from copy import deepcopy

import Tix
from   pprint import pprint
import gc

try:
    import mwavepy
    import pygram_mwavepy
    got_mwavepy = True
except ImportError:
    print "...warning no 'mwavepy' library module found, cannot run any MWAVEPY S2P analysis"
    got_mwavepy = False

## import the excel stuff if we can, we may be on linux and we may not be able to run the excel spreadsheet functions
try:
      from xlrd import open_workbook
      from xlwt import Workbook,easyxf,Formula
      from xlutils.copy import *
      got_xl_import = True

except ImportError:
      print '...warning no Excel library modules found, cannot import xlrd,xlwt,xlutils'
      got_xl_import = False


UNDEFS = [ None, '', 'undefined', 'None', 'none', '[]', [] ]

try:
    import pyodbc
except ImportError:
    print "...warning no 'pyodbc' library module found, cannot load any Database results"


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


      self.pid = os.getpid()

      # Make the pygram  version number by using the sos revision number and manipulating the string
      txt = '$Revision: 1.281 $'                   # sos revision number, auto assigned by sos when doing a checkin
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
                                   ['WCDMA-Band1'  , 1950, 1980, 1920],       \
                                   ['WCDMA-Band2'  , 1880, 1850, 1910],       \
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
      [[[ 836, 898, 1748, 1880, -1, -1], [1.0, 0.0, 25, 3.5, 3.0], 'N35' , [ None, None, None, 3.5, None]],
       [[ 836, 898, 1748, 1880, -1, -1], [1.0, 0.0, 25, 2.7, 3.0], 'N27' , [ None, None, None, 2.7, None]],
       [[ 836, 898, 1748, 1880, -1, -1], [1.0, 0.0, 25, 3.8, 3.0], 'N38' , [ None, None, None, 3.8, None]],
       [[ 1950, 1880, -1, -1], [1.0, 0.0, 25, 3.4, 3.0], 'N34' , [ None, None, None, 3.4, None]],
      ]


      self.value_dict_names_original_list = [ 'logfilename', 'SN', 'TestName', 'Temp(C)', 'Test Freq(MHz)', 'Serial Number',
                                               'HB_LB', 'Sub-band', 'Vbat(Volt)', 'Freq(MHz)', 'Pwr In(dBm)', 'Pout(dBm)',
                                               'VSWR', 'Phase(degree)', 'Source VSWR', 'Source Phase(degree)',
                                               'Vramp Voltage', 'Regmap', 'csvfilename'  , 
                                               'ibcom', 'gpib_addr',  'duration(sec)',  'scpi_wr', 'scpi_rd', 'ControlSignals',
                                               'cal_additional_op_pm', 'cal_additional_op_psa',
                                            ]
#                                              'Regmap', 'Process', 'Ref Pout(dBm)'  ]
      self.value_dict_names_original_list.sort()
      self.xaxis_reduced_list  =  [ 'Freq(MHz)', 'Temp(C)', '[Time] Time',  '[Time] VAM', '[Time] VRAMP', '[Time] SCOPE CHANNEL 4',
                                    'VSWR', 'Phase(degree)', 'Source VSWR', 'Source Phase(degree)',
                                    'Pwr In(dBm)', 'Pout(dBm)', 'VAM(volt)', 'Vbat(Volt)', 'ControlSignals',
                                    'Vramp Voltage', 'Frequency of Spur (MHz)', 'PSA Pwr Out(dBm)', 'Ref Pout(dBm)', 'Step',
                                    'phi', 's11_phi','s21_phi', 'Time(sec)',
                                   ]

      self.yaxis_reduced_list  =  [ 'Pwr Gain(dB)',
                                    'Pout(dBm)' ,                 
                                    'Pout_pm(dBm)' ,
                                    'PSA Pwr Out(dBm)',
                                    'ACLR Max(dBc)',
                                    'ACLR FOM40',
                                    'ACPR -400KHz(dB)',
                                    'ACPR +400KHz(dB)',
                                    'ACPR 400KHz(dB)',
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
                                    'Vbat(A)',
                                    'Magnitude',
                                    'Vmux(V)',
                                    'Temp_Vmux(C)',
                                    's11_vswr',
                                    's21_dB',
                                  ]

      # series_seperated_list is a list that causes data to be split into seperate series based on these column names.
      self.series_seperated_list = [ 'Freq(MHz)' ,
                                     'Process',
                                     'Pwr In(dBm)',
   #                                  'Pout(dBm),
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
                                     'ControlSignals',
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
      self.values_dict             = {}
      self.values_dict             = {}
      self.values_dict_count       = {}
      self.values_dict_count_total = {}

      self.filter_conditions = []
      self.series_conditions = []
      self.xynames = [ None, None ]
      self.xnames_ordered = []
      self.ynames_ordered = []
      self.y2names_ordered = []
      self.spec_limits = None

      self.interactive = 0
      self.xlimits = []
      self.ylimits = []
      self.y2limits = []
      self.xaxis_limits = []
      self.yaxis_limits = []
      self.y2axis_limits = []
      self.xgrid = None
      self.ygrid = None
      self.y2grid = None

      self.part_list = {}
      self.failed_part_list = {}

      self.arg_noload_logfiles = False




      self.numgrids    = 15
      self.numcontours = 8
#                                 left  right  top    bottom
      self.plot_position       = [0.06, 0.75,  0.92,  0.07 ]
      self.conditions_location = [ 0.76 , 0.88 ]   # window coordinates
      self.legend_location     = [ 0.95, 0.0   ]   # graph data coordinates
      self.color_list = [ 'b','g','r','c','m','y', 'k', 'orange','violet', 'brown', 'purple' ]
#      self.dash_list = [ [1,0], [3,2], [10,4], [5,8], [8, 10] ]
#      self.dash_list = [ (1,0), (3,2), (10,4), (5,8), (8, 10) ]
      self.dash_list = [ (None,None), (3,2), (10,4), (5,8), (8, 10) ]
      self.plot_marker = '.'
      self.plot_linewidth = 2
      self.save_plot_count = -1
      self.parameter_plot_count = -1
      
      self.plottype = None
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


      self.read_pygram_config()

      # Create the main window
      self.win_init()


      self.plot_data = None

      self.vramp_search_testname_bad = 'VRamp Search_NO_MATCH'  ## Intentionally miss-defined so that VRamp Search tests are not detected
      self.vramp_search_testname_good = 'VRamp Search'  
      self.arg_parent = 'interactive'
      self.exit_after_processing=False


      self.vramp_search_testname = self.vramp_search_testname_bad
      self.run_refpout_from_vrampsearch = 0
      self.arg_process_multiparts = 0

      self.board_trace_data = {}      
      
      self.atlantis_site = 'Greensboro'
      self.atlantis_set_dsn(self.atlantis_site)
      self.mercury_site = ''
      self.mercury_set_dsn(self.mercury_site)

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


      if got_mwavepy:
            mwavepy.touchstone.touchstone.load_file = pygram_mwavepy.mwavepy_load_file
            mwavepy.Network.read_touchstone         = pygram_mwavepy.mwavepy_read_touchstone
#            mwavepy.Network.interpolate             = mwavepy_interpolate
            mwavepy.Network.change_frequency        = pygram_mwavepy.mwavepy_change_frequency
            mwavepy.Network.get_single_frequency_spars = pygram_mwavepy.get_single_frequency_spars





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

        # First set all sweep params to nominal
        for swp in sweep_params_list:
            # for s2p logfiles only reset the vbat and temp conditions
            if 's2p' not in tdesc['logfiletype'] or   swp in [ 'Vbat(Volt)','Temp(C)']:
#                print '(set_filter_conditions) ', tdesc['logfiletype'], swp
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

    def reset_filter_conditions( self, fct=None ):
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
        self.y2limits = []

        self.xgrid = ''
        self.ygrid = ''
        self.y2grid = ''


    ########################################################################################################
    def set_spec_limits( self, fct=None, limval=None ):
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
       
       if fct==None: return

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
               if y and p[6]:
                     y *= 1/p[6]


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


           # default colors for limit lines
           c1 = 'k'   # black
           c2 = 'y'   # yellow
           # if the measurement type is an xmin, xtyp, xmax measurement then we need to swap the x and y axes
           if mtype[0].lower() == 'x':
               t = y
               y = x
               x = t
               c1 = 'y'
               c2 = 'k'


           if limname != None  and limname != '' :
               if at_val == None:
                    if type( y ) != types.ListType:  
                        self.spec_limits.append( [ y , limname + ' = ' + str(y) , 2, c1] )
                    else:
                        for yt in y:
                            yt = float(yt)
                            self.spec_limits.append( [ yt , limname + ' = ' + str(yt) , 2, c1] )

               else:
                   if type( x )    != types.ListType:
                      if type( y ) != types.ListType:  
                           self.spec_limits.append( [[[x*0.97, y],[x*1.03, y]]  , limname + ' = ' + str(y) , 2, c1] )
                      else:
                          for yt in y:
                              yt = float(yt)
                              self.spec_limits.append( [[[x*0.97, yt],[x*1.03, yt]]  , limname + ' = ' + str(yt) , 2, c1] )
                   else:
                      if x[0] != None and x[1] != None:
                         self.spec_limits.append( [[[float(x[0])*0.97, y],[float(x[-1])*1.03, y]]  , '%s = %s @ %s' % ( limname, str(y), x) , 2, c1] )
                      elif x[0] != None:
                         self.spec_limits.append( [[[float(x[0])*0.97, y],[float(x[0])*1.03, y]]  , '%s = %s @ %s' % ( limname, str(y), x) , 2, c1] )
                      elif x[-1] != None:
                         self.spec_limits.append( [[[float(x[-1])*0.97, y],[float(x[-1])*1.03, y]]  , '%s = %s @ %s' % ( limname, str(y), x) , 2, c1] )


           if x != None:
              if type( x ) != types.ListType:
                    if type( y ) != types.ListType:
                        y = float(y)
                        self.spec_limits.append( [[[ x, y*1.1],[x, y*0.9]] , '' , 2, c2] )
                    else:
                        for yt in y:
                            yt = float(yt)
                            self.spec_limits.append( [[[ x, yt*1.1],[x, yt*0.9]] , '' , 2, c2] )
              else:
                 for xt in x:
                     if type( y ) != types.ListType:
                        y = float(y)
                        self.spec_limits.append( [[[ xt, y*1.1],[xt, y*0.9]] , '' , 2, c2] )
                     else:
                        for yt in y:
                            yt = float(yt)
                            self.spec_limits.append( [[[ xt, yt*1.1],[xt, yt*0.9]] , '' , 2, c2] )



                         
###################################################################
    def set_xyaxes_limits( self, tdesc=None ):
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
        self.y2limits = []

        if tdesc == None: return

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


        # Normally set the polar plot off
        bval = False
        if 'polar_phase_plot' in tdesc:
             bval = tdesc['polar_phase_plot']
        self.polar_phase_plot.set( bval )




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


        print '(write_xl_part_info) data_dict = ', data_dict

        for name in data_dict:
            if name not in self.values_dict:
                 self.add_values_dict(name)
            # get rid of any empty values
            tstr = ''
            for v in self.values_dict[name]:
                if v not in [None, '']:
                    tstr +=  v + '\n'
#                    break        # only use the first non-None value
    
            # remove trailing new-line char
            if len(tstr)>0:
               tstr = tstr[:-1]
                    
#            tstr = ' '.join( self.values_dict[name])
            ws    = wb.get_sheet(  data_dict[name][0] )
            row   = data_dict[name][1]
            col   = data_dict[name][2]
            style = data_dict[name][3]

            ws.write(row , col , tstr, self.excel_style[ style ])
            
            # make up the name for the excel sheet name
            # find the serial number or number if there are more than one
            if name == 'Serial Number':               
                part = re.findall('_sn0*(\d+)',tstr, re.I)
                if len(part) >= 1:
                    for p in part:
                        tstr = 'SN' + p + ' '

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
           if self.xl_type == 'prd' and grps:
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

           if self.xl_type == 'perf_log2':
              row_hdr = 5
#              self.prd_header_lst = [ '#', 'parameters', 'data', 'upper limit', 'pass/fail', 'comments']
              self.prd_header_lst = [ '#', 'parameters', 'data', 'lower limit', 'upper limit', 'pass/fail', 'comments']

           if self.xl_type == 'perf_log':
              row_hdr = 5
              self.prd_header_lst = [ '#', 'parameters', 'data', 'limit', 'pass/fail', 'comments']

           if self.xl_type == 'mktg_plots':
              row_hdr = 5
              self.prd_header_lst = [ '#', 'parameters', 'vs (x-axis)' ]

           if self.xl_type == 'filter_cm':
              row_hdr = 2
              self.prd_header_lst = [ '#', 'parameters', 'meas', 'max', 'typical', 'min', 'debug', 'conditions' ]


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

#           print '(get_prd_data) n2c=', n2c


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
               if self.xl_type in ['perf_log', 'perf_log2']:
                   result_col_data  = n2c[ 'data' ]
                   result_col_passfail  = n2c[ 'pass/fail' ]
                   comments_col     = n2c[ 'comments' ]
               if self.xl_type == 'mktg_plots':
                   result_col_plots  = n2c[ 'vs (x-axis)' ]
                   result_col_passfail  = n2c[ 'pass/fail' ]
                   comments_col     = n2c[ 'Notes' ]
               if self.xl_type == 'filter_cm':
                   result_col_min  = n2c[ 'meas' ]
                   result_col_max  = n2c[ 'meas' ]
                   result_col_typ  = n2c[ 'meas' ]
                   result_col_data  = n2c[ 'meas' ]
                   comments_col     = n2c[ 'debug' ]


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
                    elif self.xl_type in ['perf_log', 'perf_log2']:
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
                    elif self.xl_type == 'filter_cm':
                        pdata = { 'sheet_num' : snum,
                                  'sheet_name': s.name,
                                  'sub-band'  : sheet_band,
                                  'row'       : row,
                                  'result_col_min' : result_col_min,
                                  'result_col_typ' : result_col_typ,
                                  'result_col_max' : result_col_max,
                                  'comments_col'        : comments_col,
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


                        if val.lower() == 'tbd':
                            val = ''

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


#           print '(get_prd_data) prd_list = ', prd_list

        return prd_list

###################################################################
    def get_test_desc( self, tdesc, prdl, idnum=None, arg_testmode = 'list' ):

        ''' Gets the test desc data (tdesc) associated with a PRD test (prd1)
        If the prd1['parameters'] matches the tdesc['parameter'] name then it
        returns tdesc, if not it returns None. If multiple tests match then make
        sure the last match is the one required (more specific paramter names
        should be placed after the generic names)
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



        if self.xl_type in ['perf_log', 'perf_log2', ]:
            # Ignore the frequency at the beginning of the Test name
            pname = re.sub( '^\d+','',  pname)

        if self.xl_type == 'mktg_plots':
            # Ignore the band at the beginning of the Test name
            pname = re.sub( '^\S+','',  pname)

        if self.xl_type == 'filter_cm':
            # Ignore the frequency at the end of the parameter
            pname = re.sub( '\d+mhz','mhz',  pname)

        ret_val = None

        if 1:
           tname =  re.sub( '\s+','', tdesc[ 'parameter' ] ).lower()
           tln = len(tname)

           if len(pname) < tln : return ret_val

           if tname[ :tln ] == pname[ :tln ] :
  
#               print '(get_test_desc)  arg_testmode=<%s>    idnum=<%s>   prdl[#]=<%s>' % (arg_testmode,  idnum, prdl['#'] )
           
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

                    if prdl['#'].upper() == idn.upper():
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
              if test_desc['xynames'][0] == tc[0] or \
                 test_desc['xynames'][1] == tc[0] :
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
#        grps = re.search( r'^\s*(\d+)\s*MHz', prd_test[ 'parameters' ] )
        grps = re.search( r'(\d+)\s*mhz', prd_test[ 'parameters' ].lower() )   # Frequency value can be anywhere in the parameter
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
           
#           debug print statement parses each prd_test condition to PYGRAM syntax
#           example: (gen_graph_table_row)            c=<Pin = 35 dBm>  ['Pwr In(dBm)', 'F', 35.0] 
#           print '(gen_graph_table_row)            c=<%s>  %s ' % (c, cgtc)

           if cgtc == None:
               self.graph_table_row_debug( test_desc,prd_test,[] )
               print "*** ERROR *** (gen_graph_table_row) cannot make a condition (filter) from '%s'" % c
               add_condition = False
               continue

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
           if test_desc['xynames'][0] == cgtc[0] or \
              test_desc['xynames'][1] == cgtc[0] :
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



#        self.graph_table_row_debug( test_desc,prd_test,g_row )




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

               ntc = [ mnum, tc[0], 'measure', tc[1],  at_val, None, None ]
            

               if re.search( r'(at_xval|at_xrange)', tc[1]) and ( at_val == '' or at_val == None ):
                   self.graph_table_row_debug( test_desc,prd_test,[] )
                   print "*** ERROR *** (gen_graph_table_row) for # %s '%s'."  % ( prd_test[ '#'], test_desc['parameter'] )
                   print "             Measurement %s requires an X axis value or range to measure."  % ( ntc )
                   print "             Expecting a PRD Condition (or filter) for '%s'"  % ( test_desc[ 'xynames' ][0] )
#                   sys.exit()
               if re.search( r'(at_yval|at_yrange)', tc[1]) and ( at_val == '' or at_val == None ):
                   self.graph_table_row_debug( test_desc,prd_test,[] )
                   print "*** ERROR *** (gen_graph_table_row) for # %s '%s'."  % ( prd_test[ '#'], test_desc['parameter'] )
                   print "             Measurement %s requires an Y axis value or range to measure."  % ( ntc )
                   print "             Expecting a PRD Condition (or filter) for '%s'"  % ( test_desc[ 'xynames' ][1] )
#                   sys.exit()

               # if there is no limval in the test_desc then use the limit value from the prd
               # determine which min/typ/max test to do from the test_desc
               if limval == None:
                   if    re.search( r'min', tc[0], re.I) and prd_test['min']     != '':
                        limval = prd_test['min']
                   elif  re.search( r'max', tc[0], re.I) and prd_test['max']     != '':
                        limval = prd_test['max']
                   elif  re.search( r'typ', tc[0], re.I) and prd_test['typical'] != '':
                        limval = prd_test['typical']

                   elif self.xl_type == 'perf_log' and re.search( r'limit', tc[0], re.I) and prd_test['limit'] != '':
                        limval = prd_test['limit']
                   # perf_log2 type files must have both a lower limit and an upper limit column
                   # but both of them do not need to populated though
                   elif self.xl_type == 'perf_log2' and re.search( r'limit', tc[0], re.I):
                         
                       if prd_test['upper limit'] != '' and prd_test['lower limit'] != '':
                           limval = [ prd_test['lower limit'], prd_test['upper limit'] ]
                       elif prd_test['upper limit'] != '':
                           limval = prd_test['upper limit']
                       elif prd_test['lower limit'] != '':
                           limval = prd_test['lower limit']
                       else:
                           limval = None


#               print '(gen_graph_table_row) adding MEASURE' , [ ntc, limval ]

               if limval != None and limval != '':
                  try:
                    limval = float(limval)
                  except:
                    pass
                  ntc[5] = limval
                  g_row.append(ntc)
                  
                  
               # Add the scaling value if present to the ntc 
               if 'scale_value' in test_desc:
                    ntc[6] = test_desc['scale_value'][0]

               mnum += 1


        # debug print statements

        self.graph_table_row_debug( test_desc,prd_test,g_row )


        return g_row

###################################################################
    def  exit(self):
        sys.exit()

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
        prd_txt = re.sub( '\s+', ' ', prd_txt)  # remove multiple space chars




        # look for any conditions which have two < or two > characters (or unicode <= / >= chars)
        if re.search( u'(<|>|\u2264|\u2265)', prd_txt):

#            print '(gen_graph_table_condition) found gt lt chars', prd_txt
            #                  '  5db     <         Pout    <        30db '
            grps = re.search( u'(\S+) ?', prd_txt, re.I)
            grps = re.search( u'(\S+) ?(<=|<|\u2264) ?(.*) ?(<=|<|\u2264) ?(\S+)', prd_txt, re.I)

            if not grps:
                grps = re.search( u'(\S+) ?(>=|>|\u2265) ?(\S+) ?(>=|>\u2265) ?(\S+)', prd_txt, re.I)


            if grps:
               name  = grps.groups()[2].strip()
               p1    = grps.groups()[0].strip()
               p2    = grps.groups()[4].strip()
               gtlt  = grps.groups()[1].strip()

               if re.search(u'(<|<=|\u2264)', gtlt):

                  val1 = p1
                  val2 = p2
               else:
                  val1 = p2
                  val2 = p1

               val1   = re.sub( '[ a-zA-Z\.\,]+$', '', val1)  # remove any trailing units
               val2   = re.sub( '[ a-zA-Z\.\,]+$', '', val2)  # remove any trailing units
               val    = '%s..%s' % ( val1, val2 )




            if not grps:
                  grps = re.search( u'(\S+) ?(>=|>|\u2265) ?(\S+)', prd_txt, re.I)
                  if grps:
                      name  = grps.groups()[0].strip()
                      val   = grps.groups()[2].strip()
                      val   = re.sub( '[ a-zA-Z\.\,]+$', '', val)  # remove any trailing units
                      val   = '%s..' % val

            if not grps:
                  grps = re.search( u'(\S+) ?(<=|<|\u2264) ?(\S+)', prd_txt, re.I)
                  if grps:
                      name  = grps.groups()[0].strip()
                      val   = grps.groups()[2].strip()
                      val   = re.sub( '[ a-zA-Z\.\,]+$', '', val)  # remove any trailing units
                      val   = '..%s' % val


#            print '(gen_graph_table_condition) found gtlt condition,  %s = %s' % ( name, val )




        # look for an '=' char to separate the name and the value
        if (name == None or val == None) and re.search('=',prd_txt):
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
        if    re.search( r'^(Freq|fin)',name,re.I) and not \
              re.search( r's2p',name,re.I):              name = 'Freq(MHz)'
        elif  re.search( r'^vbat$',name,re.I):            name = 'Vbat(Volt)'
        elif  re.search( r'^(H|L)B_?IN',name,re.I):      name = 'Pwr In(dBm)'
        elif  re.search( r'^pin',name,re.I):             name = 'Pwr In(dBm)'
        elif  re.search( r'temp',name,re.I):             name = 'Temp(C)'
        elif  re.search( r'temp',name,re.I):             name = 'Temp(C)'
        elif  re.search( r'vramp',name,re.I):            name = 'Vramp Voltage'
        elif  re.search( r'^pout$',name,re.I):           name = 'Pout(dBm)'
        elif  re.search( r'^p$',name,re.I):              name = 'Pout(dBm)'
        elif  re.search( r'ref\s*pout$',name,re.I):       name = 'Ref Pout(dBm)'
        elif  re.search( r'ref2\s*pout$',name,re.I):       name = 'Ref2 Pout(dBm)'

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
              # val  = re.sub( '[ a-zA-Z\.\,]+$', '', val)  # remove any trailing units
              val = self.strip_units(val)


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

            # val1   = re.sub( '[ a-zA-Z\.\,]+$', '', val1)  # remove any trailing units
            # val2   = re.sub( '[ a-zA-Z\.\,]+$', '', val2)  # remove any trailing units
            val1 = self.strip_units(val1)
            val2 = self.strip_units(val2)

            val    = '%s..%s' % ( val1, val2 )





        # look for 'up to'
        if not grps and commas == False:
            grps = re.search( '(up) ?to (\S+)', val, re.I)
            if not grps:
                grps = re.search( u'(<|\u2264) ?(\S+)', val, re.I)

            if grps:
              val   = grps.groups()[1].strip()
              # val  = re.sub( '[ a-zA-Z\.\,]+$', '', val)  # remove any trailing units
              val = self.strip_units(val)

              val   = '..%s' % val

        # look for 'down to'
        if not grps and commas == False:
            grps = re.search( '(down) ?to (\S+)', val, re.I)
            if not grps:
                grps = re.search( u'(>|\u2265) ?(\S+)', val, re.I)

            if grps:
              val   = grps.groups()[1].strip()
              #val  = re.sub( '[ a-zA-Z\.\,]+$', '', val)  # remove any trailing units
              val = self.strip_units(val)

              val   = '%s..' % val



        # if we get to this point and grps is None then we have a simple value
        if not grps:
              #val  = re.sub( '[ a-zA-Z\.\,]+$', '', val)  # remove any trailing units
              #val  = re.sub(r'([ 0-9\.\,\-]+|[ _0-9a-zA-Z\,]+).*$', r'\1', val)  # remove any trailing units
              val = self.strip_units(val)

              if name == 'VSWR':
                  val  = re.sub( ':.*', '', val)  # remove any trailing N:1


        # look for ',' or multiple values in val used to define a list

        val_l = val.split(',')
        if len(val_l) <= 1:  val_l = val.split()

        if len(val_l) >= 2:
#          print '(gen_graph_table_condition) found comma split values'
           val = []
           for v in val_l:

               # vs = re.sub( r'[ a-zA-Z\.\,]+$', '', v  ).strip()
               # vs = re.sub( r'([0-9\.]+) ?[a-zA-Z\.]+$', r'\1', v  ).strip()
              vs = self.strip_units(v)

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

        return [ name,  'F', val ]

###################################################################
    def strip_units(self, txt):
        '''Remove any trailing unit characters from txt
        Only do this if the txt is a numeric value.
        Otherwise return the txt unchanged
        '''

        txt = re.sub( r'([0-9\.]+) ?[a-zA-Z\.]+$', r'\1', txt.strip()  )

        return txt

###################################################################




###################################################################
###################################################################
###### Measurement functions
###################################################################



    def maxy2x( self, x, y, limits=None, serial_number=None):
       ''' Finds the x value where y is a max
           warning only works if y is an increasing quantity!!!'''
       maxval =  self.maxyval( x, y, limits)
       return self.measure_value( xyd, 'x_at_yval', maxval, serial_number=serial_number )

    def miny2x( self, x, y, serial_number=None):
       ''' Finds the x value where y is a min
           warning only works if y is an increasing quantity!!!'''
       minval =  self.minyval( x, y, limits)
       return self.measure_value( xyd, 'x_at_yval', minval, serial_number=serial_number )

    def maxyval( self, x, y, limits=None, serial_number=None):
       if limits == None: meas_type = 'ymax'
       else:              meas_type = 'ymax_limits'
       return self.measure_value( xy, meas_type, limits, serial_number=serial_number ) - 1e-12

    def minyval( self, x, y, limits=None, serial_number=None):
       if limits == None: meas_type = 'ymin'
       else:              meas_type = 'ymin_limits'
       return self.measure_value( xyd, meas_type, limits, serial_number=serial_number ) + 1e-12



    def y2x( self, x, y, yval, serial_number=None):
       return self.measure_value( xyd, 'x_at_yval', yval, serial_number=serial_number )

    def x2y( self, x, y, t, serial_number=None):
       return self.measure_value( xyd, 'y_at_xval', t, serial_number=serial_number )


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

    def measure_value( self, xyd, measure_type, at_value=None, limit=None, serial_number=None, atr=None):
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
          scale_value = None : scales the measurement data by this value

       Returns:   [ val [min, avg, max], [ x, y, sn, c, d ], [ #fails, #parts] ]'''


       if measure_type not in [ 'xmin',     'ymin',     'xmax',      'ymax',
                                'x_at_yval',            'y_at_xval' ,
                                'xmin_at_yval',         'ymin_at_xval',       'xmax_at_yval', 'ymax_at_xval',
                                'ymin_at_xrange',       'ymax_at_xrange',
                                'min_ymin_at_xrange' ,  'max_ymax_at_xrange', 'yavg_at_xrange',
                                'max_ymin_at_xrange' ,  'min_ymax_at_xrange', 'avg_ymax_at_xrange',
                                'min_ymin', 'max_ymax', 'max_ymaxdiff', 'min_ymaxdiff' , 'avg_ymaxdiff',
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
       # Expand series
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
                    v = self.measure_value( xydi, measure_type, av, limit, serial_number=serial_number, atr=atr)
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

       # Check to see if this measurement is specific to a given Serial Number part
       # If so, look through all the records and check to see if at least one record matches
       # the Serial Number. If one record matches continue on with the rest of the measurement
       # if no record match abort the measure on this series returning None
       do_measure = True
       if serial_number != None:
           do_measure = False   
           for rn in rnl:
                serial_num = self.data[ 'Serial Number' ][ rn ]
                if serial_num.upper() in serial_number:
                    do_measure = True
                    break
                      
       if not do_measure:
           return None
           
           
       
       # Now do the same again and look for a match on the ATR number
       do_measure = True
       if atr != None:
           do_measure = False   
           for rn in rnl:
                a = self.data[ 'Station Number' ][ rn ]
                try:     
                    a = int(a)
                    a = str(a)
                except:  
                    pass
                if a in atr:
                    do_measure = True
                    break

       if not do_measure:
           return None


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

       if re.search('ymaxdiff', measure_type )                            : measure_type = 'ymaxdiff'
       
       

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
       elif measure_type == 'ymaxdiff' :
          idxmax = self.meas_minmax_ix(y,'max')
          idxmin = self.meas_minmax_ix(y,'min')

          # # # # # # # # # # # # # # # # #
          #  get the min max avg values
#           yv =   y[ idx ]
#           xv =   x[ idx ]
          rn = rnl[ idxmax ]
          val_max = y[ idxmax ]
          val_min = y[ idxmin ]
          val_avg = (val_max + val_min) / 2.0

          val = val_max - val_min

          x_val_max = x[ idxmax ]
          x_val_min = x[ idxmin ]

#           print   '(measure_value)     val_min = ( %s , %s )     val_max = ( %s , %s )   ymaxdiff = %s' % \
#                 ( x_val_min, val_min, x_val_max, val_max,  val )



# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
       elif measure_type == 'ymax_at_xrange' or measure_type == 'ymin_at_xrange' or measure_type == 'yavg_at_xrange':
       # get the max y value for xvalues between at_value[0] and at_value[1]

          if isinstance( at_value, types.StringTypes ) and re.search(r'\.\.', at_value):
               r1,r2 = self.get_filter_value_range( at_value )
               at_value = [r1,r2]

          if at_value == None or at_value == '':
             print '*** ERROR *** (measure_value) at_value is None, this needs to be a range for measure_type=', measure_type


          # first calculate the yvalues at the x at_value's
          vv = self.measure_value( xyd, 'y_at_xval', at_value[0], limit, serial_number=serial_number)
          if vv == None or vv == NaN :
              y0 = None
          else:
              y0 = vv[0]

          vv = self.measure_value( xyd, 'y_at_xval', at_value[1], limit, serial_number=serial_number)
          if vv == None or vv == NaN :
              y1 = None
          else:
              y1 = vv[0]

#          print '    (measure_value) [y0,y1] =', [y0,y1]
#           if y0 == None and y1 == None :
#                return None

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
    def measure_plot_data( self, xyd, fct, limval, oplog=None, prd_test=None, wb=None, subdir=None, serial_number=None, atr=None):
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

           print '&&&(measure_plot)&&&', p


           yupper = None
           ylower = None


           idnum = ''
           if len(p) > 5 and p[1] == 'measure':

              idnum     = str( p[0] )
              mtype      = p[2][:]
              if p[3]:                at_val     = p[3]
              else:                   at_val     = None
              if p[4]:                limname    = p[4]
              else:                   limname    = None
              td_prd_col_name                    = None


           elif len(p) > 5 and p[2] == 'measure':


              idnum     = str( p[0] )
              mtype      = p[3][:]
              if p[4]:                at_val     = p[4]
              else:                   at_val     = None
              if p[5]:                limname    = p[5]
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
            
                  if isinstance(limname,types.ListType) and len(limname) == 2:
                     y  = None
                     y1 = float(limname[0])
                     y2 = float(limname[1])
                     if y1 > y2:
                        yupper = y1
                        ylower = y2
                     else:
                        yupper = y2
                        ylower = y1
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

              # Scale the limits if necessary
              if p[6]:
                 if y:   y *= 1/p[6]


              tstr = '\n   Measure = %s;   At X = %s;    Limit = %s' % ( mtype, x , y )
              self.selected_filter_conditions_str  = '%s\n%s' % ( self.selected_filter_conditions_str, tstr)

              # Do the actual measuring here using the x y data from the graph plot
              val = self.measure_value( xyd, mtype , x , y, serial_number=serial_number, atr=atr)

              tstr = '   Result =       %s\n' % (val)
              self.selected_filter_conditions_str  = '%s\n%s' % ( self.selected_filter_conditions_str, tstr)



              style = 'nomeas'

              if (type(val) == types.ListType or type(val) == types.TupleType) and val[0] != None :

                  pf    = 'PASS'
                  style = 'pass'

                  print '&&&&&  measure &&&&&', mtype, val[0], y

                  # only compare against a limit if we have a valid limit
                  if y != None and not isinstance(limname,types.ListType):
                      
                      if ((mtype[:4] == 'ymax' or mtype[:4] == 'xmax' or mtype[:3] == 'max')   and val[0]>y ) or  \
                         ((mtype[:4] == 'ymin' or mtype[:4] == 'xmin' or mtype[:3] == 'min' )  and val[0]<y ) or  \
                         ( mtype[:3] == 'avg'  and td_prd_col_name == 'min' and val[0]<y ) or \
                         ( mtype[:3] == 'avg'  and td_prd_col_name == 'max' and val[0]>y ) :
                           pf = 'FAIL'
                           style = 'fail'
                           
                           
#                       print '(measure_plot_data) td_prd_col_name=', td_prd_col_name, ' mtype=', mtype, '   val[0] = ', val[0],'  y = ', y, pf
#                       print '(measure_plot_data) prd_test[typical]' , prd_test['typical']
 
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
                      if self.xl_type == 'prd' or self.xl_type == 'filter_cm':
                          pf = pf + full_condition_selected_str

                      margin = abs( val[0]-y )

                      if pf != '':
                         fail_stat =  '%s/%s'  % ( len( self.failed_part_list ) , len( self.part_list ) )
                      else:
                         fail_stat =  '%s'     % (                                len( self.part_list ) )

                      pf = '%s mgn:%0.3f (%s)'  % ( pf, margin, fail_stat )

                  elif isinstance(limname,types.ListType):   # we have both upper and lower limits
                      
                      if ((mtype[:4] == 'ymax' or mtype[:4] == 'xmax' or mtype[:3] == 'max')   and val[0]>yupper) or  \
                         ((mtype[:4] == 'ymax' or mtype[:4] == 'xmax' or mtype[:3] == 'max')   and val[0]<ylower) or  \
                         ((mtype[:4] == 'ymin' or mtype[:4] == 'xmin' or mtype[:3] == 'min' )  and val[0]>yupper ) or  \
                         ((mtype[:4] == 'ymin' or mtype[:4] == 'xmin' or mtype[:3] == 'min' )  and val[0]<ylower ) or  \
                         ( mtype[:3] == 'avg'  and td_prd_col_name == 'min' and val[0]>yupper ) or \
                         ( mtype[:3] == 'avg'  and td_prd_col_name == 'min' and val[0]<ylower ) or \
                         ( mtype[:3] == 'avg'  and td_prd_col_name == 'max' and val[0]>yupper ) or \
                         ( mtype[:3] == 'avg'  and td_prd_col_name == 'max' and val[0]<ylower ) :
                           pf = 'FAIL'
                           style = 'fail'
                      # indicate whether the result includes measurements made over the full range of filter conditions.
                      full_condition_selected_str = xyd[6]
                      if self.xl_type == 'prd' or self.xl_type == 'filter_cm':
                         pf = pf + full_condition_selected_str

                  else:
                      pf = '(%s)'  % ( len( self.part_list ) )



                  # Scale the data for the report if necessary
                  if p[6]:
                    val[0] *= p[6]
                    if len(val)>=2 and len(val[1])==3:
                        val[1][0] *= p[6]
                        val[1][1] *= p[6]
                        val[1][2] *= p[6]


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
                 elif re.search('limit', td_prd_col_name, re.I) :
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

                     if self.xl_type == 'filter_cm':
                          tstr = ret_val.split()[0]

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


    def add_logfiles( self, logfilenames=None, csvlogfile=None, vmux_names_file=None, temperature=None ):
      '''Loads a Log file into pygram.  All data read from the file is loaded into internal dict self.data[]
      Clears all previously loaded Logfile data, and runs self.add_logfile

      Parameters:
         logfilename = None    :  Name of filename containing ATR style log data
         cvslogfile  = None    :  Name of filename containing csv style data (including vmux analog files)
         vmux_name_file = None :  (obsolete) Name of lookup table for vmux signal names and vmux address mux.
         temperature = None    :  If data does not contain any temperature data, set the temperature data to this value (normally 25C)

      Returns   :   None'''

      if isinstance(logfilenames, types.StringTypes) :
            logfilenames = [ logfilenames ]

      for logfilename in logfilenames:
          self.add_logfile( logfilename, csvlogfile, vmux_names_file, temperature )
      self.win_load()


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
            reader = csv.reader(fip, delimiter=',', skipinitialspace=True, )

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
    def remove_logfile(self, logfilename ):
        '''Removes all data records from self.data that match the logfile name
        They are not actually removed, all fields are set to none'''
        
        
        logfilename = self.get_filename_from_fullpath( logfilename )
        
        lgn = 'logfilename'
        if lgn in self.data:
            for rn in range(self.datacount):
                if self.data[lgn][rn] == logfilename:
                    for n in self.data:
                        self.data[n][rn] = None
                        
        
                
    ###################################################################
    def add_logfile(self, logfilename=None, csvfilename=None, vmux_names_file=None, temperature=None):

        if logfilename.find('Constellation|') == 0:
            cnxn = self.connect(self.atlantis_dsn)
            cursor = cnxn.cursor()
            self.atlantis_load_session(cursor, logfilename)
            cnxn.close()
        elif logfilename.find('Mercury|') == 0:
            cnxn = self.connect(self.mercury_dsn)
            cursor = cnxn.cursor()
            self.mercury_load_session(cursor, logfilename)
            cnxn.close()
        else:
            self.add_logfile_core(logfilename, csvfilename, vmux_names_file, temperature)


    ###################################################################
    def add_logfile_core(self, logfilename=None, csvfilename=None, vmux_names_file=None, temperature=None):
      '''Loads a Log file into pygram.  All data read from the file is loaded into internal dict self.data[]

      Parameters:
         logfilename = None    :  Name of filename containing ATR style log data
         cvslogfile  = None    :  Name of filename containing csv style data (including vmux analog files)
         vmux_name_file = None :  (obsolete) Name of lookup table for vmux signal names and vmux address mux.
         temperature = None    :  If data does not contain any temperature data, set the temperature data to this value (normally 25C)

      Returns   :   None'''



      time_start = time.time()

      if  self.arg_noload_logfiles == True:
            return

      # # first check to see what type of logfile this is, if its a csv file then assume it is a vmux logfile, and retspecify the file varaibles
      # if logfilename != None and re.search(r'.csv', logfilename  ) and csvfilename==None and vmux_names_file==None:
      #    csvfilename = logfilename
      #    logfilename = None
      #    vmux_names_file = 'Riserva_vmux_signals.csv'



      self.status.set( '(add_logfile) LOADING LOGFILE RESULTS: %s %s ' % ( logfilename, csvfilename ) )

      try:
          self.root.update()
      except: pass
      
#### !!!!!!!
#### !!!!!!!
#### !!!!!!!
          # Wipe the data structure clean so that we load the logfile faster
          # (by starting with an empty self.data structure we can add new 
          #  much faster)
          # But we must save away the previous data structure so that it can
          # be merged in at the end
      
      #  This deepcopy was found to be too slow, therefore we now do an explicit copy of 
      #  each col                
#      previous_data = deepcopy( self.data )
      previous_data = {}
      for col in self.data:
            previous_data[col] = self.data[col][:]
      time_copy = time.time()
      previous_datacount = self.datacount
          
      del self.data    
      self.data = {}
      self.datacount = 0
#### !!!!!!!
#### !!!!!!!
#### !!!!!!!

      self.atrsectioncount = 0
      self.csvsectioncount = 0

      last_serial_number = None


      self.logfile_type      = 'excel'
      self.s2p_subsample     = None
      rn_start = self.datacount

      if logfilename != None:

          self.logfilename      =  logfilename
          self.logfiledir       = os.path.dirname( logfilename )
          self.logfilebasename  = os.path.basename( logfilename )
          ( dummy , self.logfile_extension ) = os.path.splitext(  logfilename )




          self.logfilenames.append( logfilename )

          linecount = 0

          try:
#            fip = open(logfilename, "rb")
            fip = open(logfilename, "rU")
#            reader = csv.reader(fip, delimiter='\t')
          except IOError:
            print "*** ERROR (load_logfile) could not read file " , logfilename

          try:
              dialect = csv.Sniffer().sniff(fip.read(4096))
              delim = dialect.delimiter
          except csv.Error:
              delim = '\t'
              print "*** warning (load_logfile) cannot determine type of logfile not read file (guessing tab delimitted)" , logfilename

          if delim not in [',']:
              delim = '\t'

          fip.seek(0)
          reader = csv.reader(fip, delimiter=delim)

          print " ...reading logfile '%s'" % logfilename

          cnum = 1
          opcol2name = []
          section_data = {}
          in_section_header = False
          previous_row = None


          name = 'record_num'
          if name not in self.data :
            self.data[ name ] = [None] * self.datacount
            opcol2name.append(name)
          name = 'logfilename'
          if name not in self.data :
            self.data[ name ] = [None] * self.datacount
            opcol2name.append(name)
          name = 'logfiledir'
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


          ### Enable the reading of Touchstone .SNP network analyzer files
          if re.search('s\d+p$', self.logfile_extension.lower()):
#          if self.logfile_extension.lower() in ['.s1p', '.s2p', '.s3p', '.s4p',] :

               self.s2p_type = 'real_imag'
               self.logfile_type = self.logfile_extension.lower()[1:]
               # self.logfile_type = 's2p'
               # if self.logfile_extension.lower() == '.s1p':
               #     self.logfile_type = 's1p'
               # elif self.logfile_extension.lower() == '.s3p':
               #     self.logfile_type = 's3p'
               # elif self.logfile_extension.lower() == '.s4p':
               #     self.logfile_type = 's4p'

               num_ports =  int( re.findall('s(\d+)p', self.logfile_type)[0] )

               done_column_header = True
               current_test_colnum2colname = []

               S_names = [  'Freq(s2p)' ]
               for m in range(1, num_ports+1):
                   for n in range(1, num_ports+1):
                        if m < 10 and n < 10:
                            sport = 's%d%d' % ( m, n )
                        else:
                            sport = 's%02d%02d' % ( m, n )
                        S_names.append( '%s_mag' % sport )
                        S_names.append( '%s_phi' % sport )

               # look at each column heading name and create a new data_column and fill it with nulls up to the

               # S_names = [  'Freq(s2p)',  \
               #               's11_mag','s11_phi', \
               #               's21_mag','s21_phi', \
               #               's12_mag','s12_phi', \
               #               's22_mag','s22_phi']
               # if self.logfile_type == 's1p':
               #    S_names = [  'Freq(s2p)',  \
               #               's11_mag','s11_phi', ]
               # if self.logfile_type == 's3p':
               #    S_names = [  'Freq(s2p)',  \
               #               's11_mag','s11_phi',
               #               's12_mag','s12_phi',
               #               's13_mag','s13_phi',
               #
               #               's21_mag','s21_phi',
               #               's22_mag','s22_phi',
               #               's23_mag','s23_phi',
               #
               #               's31_mag','s31_phi',
               #               's32_mag','s32_phi',
               #               's33_mag','s33_phi', ]
               #
               # if self.logfile_type == 's4p':
               #    S_names = [  'Freq(s2p)',  \
               #               's11_mag','s11_phi',
               #               's12_mag','s12_phi',
               #               's13_mag','s13_phi',
               #               's14_mag','s14_phi',
               #
               #               's21_mag','s21_phi',
               #               's22_mag','s22_phi',
               #               's23_mag','s23_phi',
               #               's24_mag','s24_phi',
               #
               #               's31_mag','s31_phi',
               #               's32_mag','s32_phi',
               #               's33_mag','s33_phi',
               #               's34_mag','s34_phi',
               #
               #               's41_mag','s41_phi',
               #               's42_mag','s42_phi',
               #               's43_mag','s43_phi',
               #               's44_mag','s44_phi',]



               for name in S_names:
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

#          self.s2p_subsample = 20
          self.s2p_subsample = False
          do_s2p_subsample = False
          subsample_count = 0
          self.s2p_type = None
          s21_val_prev = 0.0
          self.freq_mult = 1

          for row in reader:


            linecount += 1
            if len(row) < 1:
                continue

            if re.search('s\d+p$', self.logfile_type):

                 if len(row[0])>0 and row[0][0] == '#':
                     row[0] = re.sub('#\d+#', '#', row[0]) # strip off the leading byte count

                     if self.s2p_type == None:
                         if re.search(r'^#\s+.?Hz\s+S\s+MA\s+R'.lower(), row[0].lower()):
                            self.s2p_type = 'mag_phi'
                            do_s2p_subsample = self.s2p_subsample
                         elif re.search(r'^#\s+.?Hz\s+S\s+RI\s+R'.lower(), row[0].lower()):
                            self.s2p_type = 'real_imag'
                         elif re.search(r'^#\s+.?Hz\s+S\s+dB\s+R'.lower(), row[0].lower()): # Hz S  dB   R 50
                            self.s2p_type = 'db_phi'
                            do_s2p_subsample = self.s2p_subsample

                         freq_mult = re.findall(r'^#\s+(.?)Hz'.lower(), row[0].lower())
                         if len(freq_mult) == 1:
                             if freq_mult[0] == 'k':
                                    freq_mult = 1e3
                             elif freq_mult[0] == 'm':
                                    freq_mult = 1e6
                             elif freq_mult[0] == 'g':
                                    freq_mult = 1e9
                             else:
                                 freq_mult = 1
                         else:
                             freq_mult = 1
                         self.freq_mult = freq_mult

                     continue


                 if len( row ) == 1:
                     row = row[0].split()     # split the data on spaces

                 # sNp lines with '!' can be stripped, add it back in here
                 if row[0] == '':
                     row = row[1:]
                     row[0] = '!' + row[0]

                 if  re.search(r'^\s*!.*', row[0]) or  re.search(r'^\s*#.*', row[0] ) :  continue
                 if len(row) > 1 and ( re.search(r'2-Port', row[1]) or  re.search(r'VAR ', row[1] )) :  continue

                 # For SnP the data may be on multiple lines, therefore we must read in multiple lines
                 # to get the full sparam data
#                 if self.logfile_type in ['s3p','s4p'] and self.s2p_type != None:
                 if self.s2p_type != None:
                     lsname = len(S_names)
                     while len(row) < lsname:
                        row_next = reader.next()
                        linecount += 1
                        if len( row_next ) == 1:
                            row_next = row_next[0].split()
                        row.extend( row_next )

                 # In order to speed up the s2p loading, we subsample the data
                 if do_s2p_subsample:
                     subsample_count = (subsample_count + 1) % self.s2p_subsample
                     try:
                         s21_val = float(row[3])
                     except ValueError:
                         continue
                     abs_diff = abs( abs(s21_val) - s21_val_prev )
                     if subsample_count != 0 and (s21_val < -60 or abs_diff<0.1):    
                         continue
                     s21_val_prev = abs(s21_val)
                     
#                      s21_val = float(row[3])
#                      if not abs( s21_val - s21_val_prev )/ s21_val > 0.01:
                        
                     



            if len( row ) < 1 : continue

            if re.search(r'^\s*//\*+', row[0]) :  continue






            # Look for a new section header line
            #
            #      //Serial Number: A0B BOM-C SS SN001


            grps = re.search(r'^//(.*?):(.*)$', row[0])
            if not grps and len(row) > 1:
                grps = re.search(r'^(.*?):(.*)$', ''.join((row[0],row[1])))
            if grps:
               name  = grps.groups()[0].strip()
               name = re.sub(r'\.', '', name)
            
               if name == 'Comment' : name = 'Comment_Section'
            
               value = grps.groups()[1].strip()
               
               if name != 'Serial Number':
                   try:
                      value = float(value)
                   except: pass
               section_data[ name ] = value
               self.logfile_type = 'atr'



               if in_section_header == False:
                    in_section_header = True
                    
               if name == 'Serial Number':
                    if value != last_serial_number:   
                        last_serial_number = value        
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



            # Look for a test header line in the log file of the form:
            #
            #     //T#    TestName        Sw Matrix       S21(dB) Tuner Loss(dB)  ...
            #
            # or if its a simulation results file :
            #
            #     fin     vam     phase(outRl[::,1])[0, ::]


            if re.search(r'^\s*//T#\s*$', row[0]) or \
                    (previous_row and len(previous_row[0]) >= 2 and  previous_row[0][:2] == '--'):
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
                  
                  name = re.sub('1.2MHz\(dB', '1200kHz(dB', name )
                  name = re.sub('1.8MHz\(dB', '1800kHz(dB', name )
                  
                  name = re.sub(r'\.', '', name)
                  
                  
                  
                  if name in current_test_colnum2colname:
                       if name not in UNDEFS and name.lower() != 'n/a':
                          print '*** ERROR *** Repeated column name <%s> at line %s of logfile %s' % (name, linecount, logfilename )

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
                     


            # Now look for an excel file with no column header
            # if this is
            if self.logfile_type == 'excel' and done_column_header == False and re.match( r'^[\-\+0-9]', row[0] ) and len(row) >= 2 :
               
                current_test_colnum2colname = []


                # look at each column heading name and create a new data_column and fill it with nulls up to the
                for cnum in range(len(row)):
                    if cnum == 0:  name = 'X'
                    elif len(row) == 2 and cnum == 1: name = 'Y'
                    else:
                        name = 'Y' + str(cnum)
                        
                    current_test_colnum2colname.append( name )
                
                    if name not in self.data :
                     self.data[ name ] = [None] * self.datacount
                     opcol2name.append(name)

                done_column_header_pre = True
                done_column_header     = True



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
                        grps = re.search( r'(\d+)\s*\s*(\d+)\s*[:;]\s*(\d+)\s*[:;]\s*(\d+)', fld)           #searching for:   '38{13:9;8};'
 
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




            if ( self.logfile_type == 'atr'   and first_field_is_number  and done_column_header == True ) or \
               ( self.logfile_type == 'excel' and done_column_header == True ) or \
               ( self.s2p_type != None   and done_column_header == True ):



                 
                


                self.datacount = self.datacount + 1
                in_section_header = False
                c2num = {}

                value_list_dict = {}
                value_list_max_len = None

                # Write the value of each column into the data[] dictionary by adding it to the end.
                for i in range( 0 , len(row)):
    
                      if i >= len(current_test_colnum2colname):
    #                    print '*** ERROR **** (add_logfile)', linecount, [ len(row), row[i]], i, len(current_test_colnum2colname), row
                         continue
                      name  = current_test_colnum2colname[ i ]
                      value = row[i].strip()
                      
#                       # strip off any trailing commas (,)    #  NOT SURE WE WANT TO WAISTE THE CPU CYCLES DOING THIS
#                       if value[-1] == ',':                   #   THE S2P file(IS OBVIOUSLY WRONG !!
#                         value = value[:-1]
                        
                      value_orig = value
                      
    
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

                      if name == 'Waveform':
                          try:
                                value = os.path.basename( value )
                          except ValueError:
                              pass

    
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
    
    
    
                      # Look to see if this value is a list, if so we will write out the first element in the list
                      # and then the remainder will be writen out at the end of this loop
                      if len(value_orig) > 2 and value_orig[0] == '[' and value_orig[-1] == ']':
                           value_list = value_orig[1:-1].split(',')
                           value_len  = len(value_list)
                           if value_len >= 1:
                              value = value_list[0]
                              try:
                                value = float(value)
                              except: pass
                           if value_len > 1:
                                value_list_dict[ name ] = value_list
                                if value_list_max_len == 0 or value_len > value_list_max_len:
                                    value_list_max_len = value_len

                      if value == '[]':
                          value = None
                      if value == 'undefined' :
                          value = None
                      if isinstance( value, types.StringTypes ) and value.lower() == 'nan' :
                          value = None
                      # if value == 'None' :
                      #     value = None

                             
        
        
        
                      ##############################################################################
                      # Save the ordinary data in the self.data array
                      # but only if this column has not been done already
                      # print '(load_logfile) name=<%s> value=<%s>' % ( name, value)
                      if name not in c2num or c2num[ name ] != 'done' :
                          self.data[ name ].append( value )
                          c2num[ name ] = 'done'
                      #
                      ##############################################################################
    
    
    
                # save the record number as well
                self.data[ 'record_num' ].append( self.datacount+previous_datacount )
                c2num[ 'record_num' ] = 'done'

                # save the record number as well
                self.data[ 'logfilename' ].append( self.logfilebasename )
                c2num[ 'logfilename' ] = 'done'

                # save the record number as well
                self.data[ 'logfiledir' ].append( self.logfiledir )
                c2num[ 'logfiledir' ] = 'done'

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


                # The data for the row has just been saved away as a new self.data record
                # However if any of the columns was a value_list then we need to replicate the
                # entire record and change the value for each of the value_list columns
                
                if value_list_max_len > 1:

                    datacount_start = self.datacount-1
                
                    for vl_idx in range( 1, value_list_max_len ):
                        self.datacount += 1
                        for n in self.data:
                            if   n in value_list_dict:
                                if vl_idx < len( value_list_dict[ n ] ):
                                    v = value_list_dict[ n ][ vl_idx ]
                                else:
                                    v = None
                            elif n == 'record_num':
                                v  = self.datacount + previous_datacount 
                            else:
                                v = self.data[ n ][ datacount_start ]
                                
                            try:
                                v = float(v)
                            except: pass

                            self.data[ n ].append( v )                             

            if self.logfile_type == 'excel' and done_column_header_pre == True:
                  done_column_header     = True
                  done_column_header_pre = False


          # end of row in reader loop
          fip.close()
          time_read = time.time()

          print '   .read %s %6d lines, read in records %6d to %6d' % (self.logfile_type, linecount, rn_start, self.datacount),


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

       
          # If there were no sections in this logfile
          # add the mising_columns on the whole file
          if len(rn_sf_list) == 0:
              self.add_missing_columns( rn_start, self.datacount )

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

      self.logfiles.insert( Tk.END, self.get_filename_from_fullpath( logfilename ) + ' (%s)' % (self.datacount))


      time_missing = time.time()
#### !!!!!!!
#### !!!!!!!
#### !!!!!!!
      # Merge the just loaded data structure with the previous data structure
      self.data = self.merge_data_dicts( previous_data, self.data )
      self.datacount += previous_datacount
#### !!!!!!!
#### !!!!!!!
#### !!!!!!!
      time_merge = time.time()




      if '@Prated' in self.values_dict:
          del self.values_dict[ '@Prated' ]
      self.add_values_dict( '@Prated' )    # reset the TestName values_dict


#       try:
#           self.win_load( logfilename, csvfilename, self.datacount-rn_start )
#       except Tk._tkinter.TclError:
#           print '@@@@ FOUND THE _tkinter.TclError '
          


      files = ', '.join( self.logfilenames + self.csvfilenames )
      try:
          z = self.root.winfo_toplevel()
          z.wm_title('PYGRAM Graphing Tool  version:  ' + self.pygram_version + '     ' + files )
      except Tk._tkinter.TclError:
          print '@@@@ FOUND THE _tkinter.TclError again'


      print r' (Loading Time %0.2f/%0.2f/%0.2f/%0.2f/%0.2f [%0.2f] sec)' % ( \
            time_copy-time_start,   \
            time_read-time_copy,    \
            time_missing-time_read, \
            time_merge-time_missing,\
            time.time()-time_merge, \
            time.time()-time_start,   \
            )


    ###################################################################
    def merge_data_dicts( self, previous_data, new_data ):
        '''Take the previous_data dict and append new_data
        The merged dicts are returned
        '''

        # First get the datacount length from the previous_data, (any column 
        # as they should be all the same length) and then create an empty column
        empty_col_list = []
        col_len = 0
        for col in previous_data:
            col_len = len( previous_data[col] )
            if col_len > 0:
                empty_col_list = [None] * col_len
                break
                
        # Then get the datacount length from the new_data, (any column will do)
        new_data_empty_col_list = []
        col_len = 0
        for col in new_data:
            col_len = len( new_data[col] )
            if col_len > 0:
                new_data_empty_col_list = [None] * col_len
                break

        for col in previous_data:
            if col not in new_data:
                new_data[col] = new_data_empty_col_list[:]
                
        for col in new_data:
            if col not in previous_data:
                previous_data[col] = empty_col_list[:]
            previous_data[col] += new_data[col]
#            previous_data[col].extend( new_data[col] )
   
        return previous_data    

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

              self.add_new_column( 'logfiledir' )
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
                 self.data[ 'logfiledir' ].append( self.logfiledir )
                 self.data[ 'linenumber' ].append( str( rescount ) )

              print '   .read %6d db records, read in records %6d to %6d' % (rescount, rn_start, self.datacount)

#         except Exception:
#             print "*** ERROR (load_logfile) could not read file " , logfilename



              self.db_cursor.close()



      self.add_missing_columns( rn_start, self.datacount)




      self.win_load( logfilename, num_records= self.datacount-rn_start )


    ###################################################################
    def create_values_dict( self, allcols=False ):
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
             self.values_dict_count_total = {}
             if allcols == False:
                 for name in self.value_dict_names:
                   self.add_values_dict( name )
             elif allcols == True:
                 for name in self.data:
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
                     self.values_dict_count_total[ name ]
                     self.values_dict_count[ name ]'''

         if rn_finish == None:
            rn_finish = self.datacount

         # Create an new empty column if the column name does not already exist (shouldn't occur though) 
         if name not in self.data:
            self.add_new_column( name )
            self.add_values_dict( name, rn_start, rn_finish )
            return


         # If we have a valid column name, start countin the number of values
         if isinstance( name, types.StringTypes ):
              
              if not name in self.values_dict:
                   self.values_dict[ name ] = []
                   self.values_dict_count[ name ] = []
                   self.values_dict_count_total[ name ] = 0
    
                   # If the number of different values exceeds 200 then abort the dictionary,
    
#                   print '(add_values_dict) COL <%s> <%s> <%s>' % (name, len( self.data[name]), self.datacount)
                    
                   for rn in range(rn_start,rn_finish):
#                       print '(add_values_dict) %d  <%s> <%s> ' % (rn ,name,  self.data[name][rn])
                       val =  self.data[name][rn]    
                       
                       # Make sure we skip all the None values, we dont want to count them
                       skip = False
#                        try:
#                            if val in UNDEFS:
#                                 skip = True  
#                        except AttributeError:
#                             skip = True            
                          
                       if skip:
                            continue
                             
                       try:
                         # we found a value which we've seen before, increamet the count
                         idx = self.values_dict[ name ].index( val )
                         self.values_dict_count[ name ][ idx ] += 1
    
                       except Exception:
                           if len( self.values_dict_count[ name ] ) < 200 :
                               # we found a new value  , add it to the list, and set the count to 1
                               self.values_dict[ name ].append(  val )
                               self.values_dict_count[ name ].append( 1 )
#                                print "...warning (add_values_dict) attempt to create values_dict for column '%s' which has too many different values" % ( name )
#     #                          raise Exception
#                                break
                           # if we have more than 200 different values stop counting. This column is
                           # likely not to be a condition column but rather a measurement where
                           # each value is different, and we don't need to keep a good count for it
                           else:
                                break
                
                       try: 
                           if val not in UNDEFS:
                               self.values_dict_count_total[ name ] += 1
                       except AttributeError:
                           pass

                
                  
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


      if rn_start==None or  rn_finish==None : return

      rn_sum = rn_finish - rn_start

      if rn_sum == 0:  return

      # Add missing column data to the end of the existing data.
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
#                  print '(add_logfile) vramp data ',self.data['Vramp File'][rn], [ vramp_release, hb_lb, seg, voltage, full_filespec, pcl_level ]

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

      self.copy_column_data(  'Vramp', 'Vramp Voltage', rn_start, rn_finish,  )

      
      #-----------------------------
      # Create new columns for Freq
      #-----------------------------
      self.add_new_column( 'Freq(MHz)' )

      # If we see Freq(s2p) data then copy it to Freq(MHz) overriding the original data.
      # s2p data comes from the ENA so we ignore the original Freq(MHz) data and use the Freq(s2p) instead
      if 'Freq(s2p)' in self.data :
           self.add_new_column( 'Freq(MHz)' )
           self.add_new_column( 'Freq(GHz)' )
           for rn in range( rn_start, rn_finish ):
              if (self.data['Freq(s2p)'][rn]) not in UNDEFS:                               # tests if there is data in 'Freq(s2p)' log file columnPortOut(dBm)
                self.data['Freq(MHz)'][rn] = ( self.data['Freq(s2p)'][rn] * self.freq_mult ) / 1e6
                self.data['Freq(GHz)'][rn] = ( self.data['Freq(s2p)'][rn] * self.freq_mult ) / 1e9


#      self.add_math_data('Freq(MHz)','Freq','*', 1e6)

      # GSO Char Rack data uses 'Frequency' in MHz
      if 'Frequency' in self.data :
           self.add_new_column( 'Freq(MHz)' )
           self.add_new_column( 'Freq(GHz)' )
           for rn in range( rn_start, rn_finish ):
              if (self.data['Frequency'][rn]) not in UNDEFS:                               # tests if there is data in 'Freq(s2p)' log file columnPortOut(dBm)
                self.data['Freq(MHz)'][rn] = ( self.data['Frequency'][rn] * self.freq_mult )
                self.data['Freq(GHz)'][rn] = ( self.data['Frequency'][rn] * self.freq_mult ) / 1e3


      # the old gui uses 'Test Freq(MHz)' copy this to Freq(MHz) and Freq(GHz) values
      if 'Test Freq(MHz)' in self.data:
           self.add_new_column('Freq(GHz)')
           for rn in range( rn_start, rn_finish ):
              if self.data['Freq(MHz)'][rn] == None and ('Freq(s2p)' not in self.data or self.data['Freq(s2p)'][rn] in UNDEFS):
                  self.data['Freq(MHz)'][rn] = self.data['Test Freq(MHz)'][rn]
              if self.data['Test Freq(MHz)'][rn] != None :   self.data['Freq(GHz)'][rn] = self.data['Test Freq(MHz)'][rn] / 1e3

 
      # add the HB_LB column
      self.add_new_column( 'HB_LB' )
      for rn in range( rn_start, rn_finish ):
          if 'Freq(MHz)' in self.data and self.data['Freq(MHz)'][rn] != None:
              f = self.data['Freq(MHz)'][rn]
              if float(f) > 1200 :    self.data['HB_LB'][rn] = 'HB'
              else:                   self.data['HB_LB'][rn] = 'LB'
          elif 'Sw Matrix' in self.data :
              f = self.data['Sw Matrix'][rn]
              if f != None and len(f) >= 1:
                if   f[0] == 'H' : self.data['HB_LB'][rn] = 'HB'
                elif f[0] == 'L' : self.data['HB_LB'][rn] = 'LB'
              
      


      # add the sub-band data column
      if 'Freq(MHz)' in self.data and rn_finish <= len(self.data['Freq(MHz)']):
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
                      if f_low <= f <= f_up:   
                            self.data['Sub-band' ][rn] = b[0]

      # ensure that empty VSWR and Phase fields default to vswr=1:1 and phase=0deg
      if 'VSWR' in self.data and 'Phase(degree)' in self.data:
            self.add_new_column('VSWR')
            self.add_new_column('Phase(degree)')
            for rn in range( rn_start, rn_finish ):
                vswr  = self.data['VSWR'][rn]
                if vswr in UNDEFS:
                    self.data['VSWR'][rn] = 1.0
                phase = self.data['Phase(degree)'][rn]
                if phase in UNDEFS:
                    self.data['Phase(degree)'][rn] = 0.0

      self.scale_data( 'Load VSWR', 'VSWR', 1, rn_start=rn_start, rn_finish=rn_finish )
      self.scale_data( 'VSWR', 'vswr', 1, rn_start=rn_start, rn_finish=rn_finish )
      self.scale_data( 'Phase(degree)', 'phi', 1, rn_start=rn_start, rn_finish=rn_finish )


      # Calculate Magnitude data for plotting polar plots when there is VSWR but no Magnitude
      if 'VSWR' in self.data:
            self.add_new_column('Magnitude')
            self.add_new_column('VSWR')
            for rn in range( rn_start, rn_finish ):
                vswr = self.data['VSWR'][rn]
                mag  = self.data['Magnitude'][rn]
                if mag in UNDEFS and vswr not in UNDEFS:
                    mag = (vswr-1)/(vswr+1)
                    if mag <= 0.01:
                            mag = 0.01
                    self.data['Magnitude'][rn] = mag


      self.create_sparams_columns(rn_start, rn_finish)

##  To get S11 and S22 in VSWR, need to use (1+ mag (S11, or 22))/(1- mag (S11, or 22)),   email from H.Sun 12nov09

      # mwavepy
      # If we have the sparameter data then load it into mwavepy and create a mwavepy network
      n = 'Freq(s2p)'
      if got_mwavepy and n in self.data and self.s2p_type == 's2p':
          self.add_new_column( 'mwavepy' )
                # Get the list of the different 2port sparmaters.
          sparam_sets = self.get_sparam_sets()
          # But first we need to convert the s2p data if it happens to be in real imaginary format into magnitude phase format
          for spst in sparam_sets:
            for rn in range( rn_start, rn_finish ):
               if n in self.data and self.data[n][rn] not in UNDEFS:
                   sparam_name = '%s%s' % (rn, spst)
                   vals = self.s2p_to_touchstone_lines(rn, spst)
                   if vals != None:
                        self.data['mwavepy'][rn] = mwavepy.Network([ sparam_name, vals])




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
#             if -200 > t > 200 :
#               t = self.ambient_temperature
             self.data['Temp(C)'][rn] = self.nearest( t, 1, self.ambient_temperature )
             
      self.scale_data( 'Temperature', 'Temp(C)', 1, rn_start, rn_finish )
         
      if  'Temp(C)' in self.data:
        for rn in range( rn_start, rn_finish ):
            t = self.data['Temp(C)'][rn]
            if -200 > t or t > 200 :
                 self.data['Temp(C)'][rn] == self.ambient_temperature

      # convert a temperature sensor value from the vmux pin into an absolute die temperature
      # equation taken from emirical data from sfrank based on data for ergo 7828_TM_L006_sn002 16jul12
      nam = 'Vmux(V)'
      if nam in self.data:
          new_nam = 'Temp_Vmux(C)'
          self.add_new_column( new_nam )

          for rn in range( rn_start, rn_finish ):
             v =  self.data[nam][rn]
             if isinstance(v, types.FloatType):
                 t =  (v - 0.405)/0.00641 
                 self.data[new_nam][rn] = t



      # look for the process in the serial number. If not found we will assume it is 'TT'

      self.add_new_column( 'Serial Number' )
      for rn in range( rn_start, rn_finish ):
            if self.data['Serial Number'][rn] == None:
               self.data['Serial Number'][rn] = self.db_serial_number

      # if we have a logfile with the word golden in it then this is a golden unit logfile and
      # we should mark it golden by giving the serial number a 'G' suffix  
      if re.search('golden', self.data[ 'logfilename' ][rn_start],  re.I):
        sn_suffix = 'G'
      else:
        sn_suffix = ''
        
      if 'Serial Number' in self.data :
        old_fullname = ''
        shortname    = ''
        for rn in range( rn_start, rn_finish ):
           self.add_new_column( 'SN' )
           fullname = self.data['Serial Number'][rn]
           fullname = str(fullname)
           if fullname != old_fullname:
                 try:
                     shortname = re.sub(r'.*([sS][nN]\d+)[_ ]?.*', r'\1', fullname, re.I )
                 except:
                     shortname = fullname
                 old_fullname = fullname
           self.data['SN'][rn] = shortname + sn_suffix
           self.data['Serial Number'][rn] = fullname + sn_suffix
           
           




      # seperate the fields in the serial number in case we want to match
      if 'Serial Number' in self.data and rn_finish > 0:
        fullname = self.data['Serial Number'][rn_start]
        fullname = str(fullname)
        flds = fullname.split('-')
        fl   = len(flds)
        for rn in range( rn_start, rn_finish ):
           fullname = self.data['Serial Number'][rn]
           fullname = str(fullname)
           flds = fullname.split('-')
           if len(flds) == 1 and flds[0] == '': continue
           for i,n in enumerate( flds ):
              inm = 'SN_fld' + str(i)
              if inm not in self.data: self.add_new_column( inm )
              self.data[ inm ][rn] = flds[i]






      self.add_new_column( 'Process' )
      for rn in range( rn_start, rn_finish ):
          x = re.search( r'(FF|SS|S_|F_)', self.data['Serial Number'][rn].upper() )
          if x :
            n = x.groups()
            x = n[0]
            if x == 'S_': x = 'SS'
            if x == 'F_': x = 'FF'
            self.data['Process'][rn] = x
          else:
            self.data['Process'][rn] = 'TT'




      self.add_new_column( 'Part Number (Chip ID)' )
      self.add_new_column( 'chipid' )
      for rn in range( rn_start, rn_finish ):
          if self.data['Part Number (Chip ID)'][rn] == None and self.data['chipid'][rn] != None :
                    self.data['Part Number (Chip ID)'][rn] = self.data['chipid'][rn].strip()



      # Correct the 'Ext Ctrl Bits' column
      # 1) strip off the trailing mode
      # 2) add the mode to new column ControlMode
      
      if 'Ext Ctrl Bits' in self.data or \
         'ControlSignals' in self.data  :
         self.add_new_column( 'ControlBits' )
         self.add_new_column( 'ControlMode' )
         self.add_new_column( 'ControlSignals' )
         self.add_new_column( 'Ext Ctrl Bits' )

         for rn in range( rn_start, rn_finish ):
         
            # get the current control signals from 'Ext Ctrl Bits' or if 'ControlSignals' is defined use this
            ctrl_bits = ''
            if  'Ext Ctrl Bits'  in self.data:
               ctrl_bits = self.data['Ext Ctrl Bits'][rn]
            if  'ControlSignals' in self.data:
               t_ctrl_bits = self.data['ControlSignals'][rn]
               if t_ctrl_bits not in UNDEFS:
                   ctrl_bits = t_ctrl_bits
                                
            self.data['ControlSignals'][rn] = ctrl_bits

            if isinstance(ctrl_bits,types.StringTypes):       
                wds = ctrl_bits.split()
                
                if len(wds) >= 1:
                  bits = wds[0].strip()
                  self.data['ControlBits'][rn] = bits
                  try:
                     bits = float(bits)
                  except: pass
                  self.data['Ext Ctrl Bits'][rn] = bits
              
                if len(wds) >= 2:
                  mode = wds[1]
                  mode = re.sub('[\(\)]','',mode)
                  self.data['ControlMode'][rn]  = mode
            else:
                # dont have a string so it must be a number or a None
                self.data['Ext Ctrl Bits'][rn] = ctrl_bits
                self.data['ControlSignals'][rn] = ctrl_bits
                self.data['ControlBits'][rn] = ctrl_bits




      # At this point we should have all the standard sweep variables setup
      # and we should be ok to generate the values_dict (a list of all values in self.data[]  for a given column name)

      if self.value_dict_names == []:
          for vdn in self.value_dict_names_original_list:
            if vdn in self.data:
                self.value_dict_names.append( vdn )
#               self.values_dict[ vdn ] = []

#       self.value_dict_names = []    
#       for vdn in self.data:
#          self.value_dict_names.append( vdn )



#      self.values_dict_done = 0
#      self.create_values_dict(allcols=True)



      # if the product number is not set then look at the list of part numbers numbers in fld 0
      # if there is only one value then assume that this is the product number
      #
      if self.product == None:
          if 'Part Number (Chip ID)' in self.data:
             self.add_values_dict( 'Part Number (Chip ID)')

             if len( self.values_dict['Part Number (Chip ID)' ] ) == 1 :
                self.product = self.values_dict['Part Number (Chip ID)' ][0]


      self.add_math_data( 'Pwr Gain(dB)', 'ActualPout', '-', 'ActualPin', rn_start=rn_start, rn_finish=rn_finish )
      self.scale_data( 'NC_Target',     'DesiredPout' , 1,  rn_start, rn_finish )
      self.scale_data( 'NC_Target',     'DesiredPout' , 1,  rn_start, rn_finish )
      self.scale_data( 'ACLR(dBc)',     'ACLR(NdBc)' , -1,  rn_start, rn_finish )

      self.add_math_data( 'Maximum Adj Channel (dBm)', 'Forward Power (dBm)', '+', 'Maximum Adj Channel (dBc)', rn_start=rn_start, rn_finish=rn_finish )
      self.add_math_data( 'Maximum Alt Channel1 (dBm)', 'Forward Power (dBm)', '+', 'Maximum Alt Channel1 (dBc)', rn_start=rn_start, rn_finish=rn_finish )


      self.scale_data( 'Vbat(A)',     'Vbat_I(Amp)' , 1,  rn_start, rn_finish )
      self.scale_data( 'Vbat_I(Amp)', 'Vbat_I(mA)' , 1000,  rn_start, rn_finish )
      self.scale_data( 'Vbat_I(Amp)', 'Vbat_I(uA)' , 1000000,  rn_start, rn_finish )
#       self.scale_data( 'Vbat_I(mA)',  'Vbat_I(Amp)', 0.001,  rn_start, rn_finish )
#       self.scale_data( 'Vbat_I(Amp)', 'Vbat_I(uA)' , 1000000,  rn_start, rn_finish )
#       self.scale_data( 'Vbat(A)',     'Vbat_I(uA)' , 1000000,  rn_start, rn_finish )

      self.scale_data( 'Vbat', 'Vbat(Volt)', 1, rn_start, rn_finish )


      self.add_orfs_data( rn_start, rn_finish )
      self.add_noise_offset_data( rn_start, rn_finish )
      
      # function to add column for harmonics in dBc and convert harmonics to dBc from dBm 
      self.add_harmonics_dBc_data( rn_start, rn_finish )


      self.scale_data( 'TestGroup',     'TestName' , 1,  rn_start, rn_finish )



#      # function to add missing column 'Linear Gain' and calculate Gain from Pin(dBm) and Pout(dBm)
#      self.add_linear_gain(rn_start, rn_finish )
      
      self.spur_file_missing  = 0
      if ('TestName' in self.data)  and  ('Spurious (ETSI reduced)' in  self.data['TestName'] or \
                                          'Spurious (ETSI full)'    in  self.data['TestName'] or \
                                          'Spurious (ETSI full)'    in  self.data['TestName'] or \
                                          'Spurious (SA Mode)'      in  self.data['TestName'] or \
                                          'Spurious Emissions'      in  self.data['TestName'] or \
                                          'Spurious Emissions WCDMA' in  self.data['TestName'] or \
                                          'Spurious (quick)'        in  self.data['TestName'] ):

         if 'Frequency of Spur (MHz)' in self.data:

             self.add_spurious_data(  1, rn_start, rn_finish )
             self.add_spurious_data(  2, rn_start, rn_finish )
             self.add_spurious_data(  5, rn_start, rn_finish )
             self.add_spurious_data( 10, rn_start, rn_finish )
             self.add_spurious_data( 15, rn_start, rn_finish )
             self.add_spurious_data( 20, rn_start, rn_finish )
             self.add_spurious_data( 30, rn_start, rn_finish )
             self.add_spurious_data( None, rn_start=rn_start, rn_finish=rn_finish  )
             self.add_spurious_data( 12, rn_start, rn_finish, remove_harmonics=False )






      # make sure every data name in the data dictionary is the adjusted in length to the same value (self.datacount)
      for n in self.data:
        self.add_new_column( n )


      self.scale_data('Arb1Leveled', 'Vramp(V)', 1, rn_start, rn_finish)


      self.add_vmux_columns( rn_start, rn_finish )

      self.add_vmux_values( rn_start, rn_finish )


      self.add_aclr_data(  rn_start, rn_finish )
      self.add_acp_data(  rn_start, rn_finish )

      self.add_all_power_values( rn_start, rn_finish )

      if 'TestName' in self.values_dict:
          del self.values_dict[ 'TestName' ]
      self.add_values_dict( 'TestName')    # reset the TestName values_dict

      if 'Freq(MHz)' in self.values_dict:
          del  self.values_dict[ 'Freq(MHz)']
      self.add_values_dict('Freq(MHz)' )

      if 0 and self.logfile_type == 'atr':
          self.calculate_test_time_statistics( rn_start, rn_finish ) 


    ############################################################################
    def get_sparam_sets(self):
        '''Get a list of the different sets of sparam parameters in the data'''
        
        sparam_lst = []
        max_port = 0
        for col in self.data:
            grps = re.search('^s(\d\d+)(.*)_mag$', col)
            if grps:
                if grps.groups()[1] not in sparam_lst:
                    sparam_lst.append( grps.groups()[1] )
                portstr = grps.groups()[0]
                plen = len(portstr)
                if plen > 2:
                    port = int(portstr[:2])
                else:
                    port = int(portstr[0])
                if not max_port or port > max_port:
                    max_port = port
            else:
                 grps = re.search('^S_(.+)_s(\d\d+)_mag$', col)
                 if grps:
                    if grps.groups()[1] not in sparam_lst:
                        sparam_lst.append( grps.groups()[0] )
                    portstr = grps.groups()[1]
                    plen = len(portstr)
                    if plen > 2:
                        port = int(portstr[:2])
                    else:
                        port = int(portstr[0])
                    if not max_port or port > max_port:
                        max_port = port

        return sparam_lst, max_port


    ############################################################################
    def create_sparams_columns(self, rn_start, rn_finish):

      # Get the list of the different 2port sparmaters.
      sparam_sets, max_port = self.get_sparam_sets()

      if len(sparam_sets) > 0 and max_port > 0:
           S_names = []
           for m in range(1, max_port +1):
               for n in range(1, max_port +1):
                    if m < 10 and n < 10:
                        sport = 's%d%d' % ( m, n )
                        S_names.append( sport )
                    else:
                        sport = 's%02d%02d' % ( m, n )
                        S_names.append( sport )
                        if n < 10:
                            sport = 's%02d%d' % ( m, n )
                            S_names.append( sport )

      # But first we need to convert the s2p data if it happens to be in real imaginary format into magnitude phase format
      for spst in sparam_sets:
        # for S in ['s11', 's12', 's13', 's14',
        #           's21', 's22', 's23', 's24',
        #           's31', 's32', 's33', 's34',
        #           's41', 's42', 's43', 's44',
        #           ]:
        for S in S_names:
            for SS in [ S + spst, 'S_%s_%s' % (spst,S) ]:
                 S_mag = SS + '_mag'
                 S_phi = SS + '_phi'
                 S_phase = SS + '_phase'
                 S_r   = SS + '_r'
                 S_i   = SS + '_i'
                 S_vswr = SS + '_vswr'
                 S_dB = SS + '_dB'
                 if S_mag in self.data and S_phi in self.data:

                     self.add_new_column( S_r )
                     self.add_new_column( S_i )
        #             self.add_new_column( S_phase )

                     for rn in range( rn_start, rn_finish ):
                       if self.data[S_mag][rn] in UNDEFS: continue
                       if self.s2p_type == 'real_imag':
                          r = self.data[S_mag][rn]
                          i = self.data[S_phi][rn]
                          self.data[S_r][rn] = r
                          self.data[S_i][rn] = i
                          self.data[S_mag][rn] = sqrt( r*r +  i*i )
                          self.data[S_phi][rn] = math.atan2(i,r)*(360.0/(2*math.pi))

                          if self.data[S_phi][rn] < 0:
                             self.data[S_phi][rn] += 360.0
                          elif self.data[S_phi][rn] > 360:
                             self.data[S_phi][rn] -= 360.0

                       elif self.s2p_type == 'mag_phi':
                          mag = self.data[S_mag][rn]
                          phi = self.data[S_phi][rn]
                          phi = (phi*2*math.pi)/360.0
                          r = mag*math.cos( phi )
                          i = mag*math.sin( phi )
                          self.data[S_r][rn] = r
                          self.data[S_i][rn] = i
                       elif self.s2p_type == 'db_phi':
                          db = self.data[S_mag][rn]
                          mag = 10**(float(db)/20.0)
                          self.data[S_mag][rn] = mag
                          phi = self.data[S_phi][rn]
                          phi = (phi*2*math.pi)/360.0
                          r = mag*math.cos( phi )
                          i = mag*math.sin( phi )
                          self.data[S_r][rn] = r
                          self.data[S_i][rn] = i

                       # self.data[S_phase][rn] = self.data[S_phi][rn]
                       # if self.data[S_phase][rn] > 180.0:
                       #      self.data[S_phase][rn] -= 360.0



                     # for the s11 calculate the real and imaginary impedance
                     if S[:3] == 's11':
                       self.add_new_column('%s_Zreal(ohm)' % SS)
                       self.add_new_column('%s_Zimag(ohm)' % SS)
                       for rn in range( rn_start, rn_finish ):
                           if self.data[S_r][rn] in UNDEFS: continue
                           r = self.data[S_r][rn]
                           i = self.data[S_i][rn]
                           s11 = complex(r,i)
                           Z = 50 * (1 + s11)/(1 - s11)
                           self.data['%s_Zreal(ohm)' % SS ][rn] = Z.real
                           self.data['%s_Zimag(ohm)' % SS ][rn] = Z.imag



                     # calculate the VSWR
                     if S[:3] in ['s11', 's22', 's33', 's44']:
                       self.add_new_column( S_vswr )
                       for rn in range( rn_start, rn_finish ):
                          if (self.data[S_mag][rn]) not in UNDEFS:      # tests if there is data in 's11_mag' log file column

                            try:
                                denominator = (1 - self.data[S_mag][rn])
                            except TypeError:
                                print S_mag, rn, self.data[S_mag][rn]
                                raise
                            if abs(denominator) < 1e-6: denominator = 1e-6
                            self.data[S_vswr][rn] = (1 + self.data[S_mag][rn]) / denominator

                     # calculate the dB value
                     self.add_new_column( S_dB )
                     for rn in range( rn_start, rn_finish ):
                          if (self.data[S_mag][rn]) not in UNDEFS:        # tests if there is data in 's22_mag' log file column
                               self.data[S_dB][rn] =  20*log10(self.data[S_mag][rn])



    ######################################################################################
    #  make up touchstone format lines
    ######################################################################################
    def s2p_to_touchstone_lines(self, rn, spst):
        '''Using the record index rn collect the sparameter data and create a mini touchstone
        format line list. The purpose of this is so that the mwavepy load touchstone file 
        function can be used to create a mwavepy network'''
        
        oplines = '# Hz S RI R 50\n'
        
        freq_name = 'Freq(s2p)'
        if freq_name not in self.data or self.data[freq_name][rn] in UNDEFS:
            return None
            
        sline = '%s ' % self.data[freq_name][rn] 
#        print '-------------'


        for S in ['s11', 's21', 's12', 's22']:
            S = S + spst
            mag_name = S + '_mag'
            phi_name = S + '_phi'
            
            if mag_name not in self.data or phi_name not in self.data:
                return None
                
            mag = self.data[ mag_name ][rn]
            phi = self.data[ phi_name ][rn]

            if mag in UNDEFS or phi in UNDEFS:
                return None 
            
            mag = float(mag)
            phi = float(phi)
            phi = (2*math.pi*phi) / 360  
            r = mag*math.cos( phi )
            i = mag*math.sin( phi )
            
            sline +=  ' %0.7g %0.7g' % (r,i)
            
#            print mag_name, mag, phi_name, phi,  r, i  
            
        oplines += sline
        
        return oplines 


    ######################################################################################
#     def add_linear_gain( self, rn_start, rn_finish ): 
#     
#       if 'Pwr In(dBm)' in self.data and 'Pout(dBm)' in self.data:
#          self.add_new_column( 'Linear Gain (dB)')
#          
#          for rn in range( rn_start, rn_finish ):
#             if (self.data['Pwr In(dBm)'][rn]) not in UNDEFS:
#                 if (self.data['Pout(dBm)'][rn]) not in UNDEFS:
#                     self.data['Linear Gain (dB)'][rn] = self.data['Pout(dBm)'][rn] - self.data['Pwr In(dBm)'][rn] 
      
      
    ######################################################################################
    def add_harmonics_dBc_data( self, rn_start, rn_finish ):
      '''add new columns for 2nd and 3rd Harmonics (dBc) and perform calculations from dBm to dBc for 
         new columns.  Also, tests if data is present in the Harmonics (dBm) column prior to 
         calculation.  Record number start (rn_start) and finish (rn_finish) are passed into function.'''
         
      if '2nd Harmonics Amplitude(dBm)' in self.data and '3rd Harmonics Amplitude(dBm)' in self.data and 'PortOut(dBm)' in self.data:
         self.add_new_column( '2nd Harmonics Amplitude(dBc)' )
         self.add_new_column( '3rd Harmonics Amplitude(dBc)' )
        
         for rn in range( rn_start, rn_finish ):
            if (self.data['2nd Harmonics Amplitude(dBm)'][rn]) not in UNDEFS:             # tests if there is data in '2nd Harmonics Amplitude(dBm)' log file column
                if (self.data['3rd Harmonics Amplitude(dBm)'][rn]) not in UNDEFS:         # tests if there is data in '3rd Harmonics Amplitude(dBm)' log file column   
                    if (self.data['PortOut(dBm)'][rn]) not in UNDEFS:                     # tests if there is data in 'PortOut(dBm)' log file column
                        self.data['2nd Harmonics Amplitude(dBc)'][rn] = self.data['2nd Harmonics Amplitude(dBm)'][rn] - self.data['PortOut(dBm)'][rn] 
                        self.data['3rd Harmonics Amplitude(dBc)'][rn] = self.data['3rd Harmonics Amplitude(dBm)'][rn] - self.data['PortOut(dBm)'][rn]


    ######################################################################################
    def add_orfs_data( self, rn_start, rn_finish ):
      ''' Add the ORFS data. Calculate the maximum of the + and - orfs data and save it.
          -400kHz -> -400kHz
           400kHz -> +400kHz
           max    ->  400kHz
           
           The same is done for 400kHz, 600kHz, 1200kHz, 1800kHz columns'''
           
      

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

            
      # create a new orfs column with the worst of the +ve and -ve values,
      # the +ve value is stored in the 'Sw Pwr 400KHz(dBm)' column, make this the column where the max value is stored

      if 'Sw Pwr -1200kHz(dBm)' in self.data and 'Sw Pwr 1200kHz(dBm)' in self.data:
         self.add_new_column( 'Sw Pwr +1200kHz(dBm)' )
         self.add_new_column( 'Sw Pwr -1200kHz(dBm)' )
         self.add_new_column( 'Sw Pwr 1200kHz(dBm)' )

         for rn in range( rn_start, rn_finish ):
            maxval = max( self.data[ 'Sw Pwr -1200kHz(dBm)' ][rn], self.data[ 'Sw Pwr 1200kHz(dBm)' ][rn] )
            self.data[ 'Sw Pwr +1200kHz(dBm)' ][rn] =  self.data[ 'Sw Pwr 1200kHz(dBm)' ][rn]
            self.data[ 'Sw Pwr 1200kHz(dBm)'  ][rn] =  maxval
            
      if 'Sw Pwr -1800kHz(dBm)' in self.data and 'Sw Pwr 1800kHz(dBm)' in self.data:
         self.add_new_column( 'Sw Pwr +1800kHz(dBm)' )
         self.add_new_column( 'Sw Pwr -1800kHz(dBm)' )
         self.add_new_column( 'Sw Pwr 1800kHz(dBm)' )

         for rn in range( rn_start, rn_finish ):
            maxval = max( self.data[ 'Sw Pwr -1800kHz(dBm)' ][rn], self.data[ 'Sw Pwr 1800kHz(dBm)' ][rn] )
            self.data[ 'Sw Pwr +1800kHz(dBm)' ][rn] =  self.data[ 'Sw Pwr 1800kHz(dBm)' ][rn]
            self.data[ 'Sw Pwr 1800kHz(dBm)'  ][rn] =  maxval       
           



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

      # copy Adj Pwr Out(dBm) to Pout(dBm) and visa versa 
      self.copy_column_data(  'Adj Pwr Out(dBm)', 'Pout(dBm)', rn_start, rn_finish,  )
      # copy Adj Pwr Out(dBm) to Pout(dBm) and visa versa 
      self.copy_column_data(  'Delivered Power (dBm)', 'Pout(dBm)', rn_start, rn_finish,  )
      self.copy_column_data(  'PAE (%)', 'PAE(%)', rn_start, rn_finish,  )
      self.copy_column_data(  'Power In (dBm)', 'Pwr In(dBm)', rn_start, rn_finish,  )

      self.copy_column_data(  'Pin', 'Pwr In(dBm)', rn_start, rn_finish,  )

      self.add_math_data('Pwr Gain SA(dB)', 'Pout_SA(dBm)', '-', 'Pwr In(dBm)', rn_start, rn_finish, )


      # Add pout data to non power and efficiency tests
      self.add_vramp2pout_data( rn_start, rn_finish )




      # Calculate Pout data from the AMAM DIstortion test data (and Calibrate using Power & Eff test)
      # Also adds the Ref Pout and Rated Pout data
      self.calc_amam_pout( rn_start, rn_finish )
          


      # Convert the available power numbers into a generic column 'Pout' with units of dBm,W,V
      if 'Adj Pwr Out(dBm)' in self.data or 'PSA Pwr Out(dBm)' in self.data or 'Pout(dBm)' in self.data or 'Pout_pm(dBm)' in self.data:
         self.add_new_column( 'Pout(dBm)'  )
         self.add_new_column( 'Pout(W)'  )
         self.add_new_column( 'Pout(V)'  )
         self.add_new_column( 'Poutpk(V)'  )
         for rn in range( rn_start, rn_finish ):
             pdbm = None
             # Decide on which of the possible power measurement values is to be mapped to the main Pout(dBm) value
             if      'Pout_sa(dBm)' in self.data and self.data[ 'Pout_sa(dBm)' ][rn] != None:
                     pdbm = self.data[ 'Pout_sa(dBm)' ][rn]
             elif    'Pout_pm(dBm)' in self.data and self.data[ 'Pout_pm(dBm)' ][rn] != None:
                     pdbm = self.data[ 'Pout_pm(dBm)' ][rn]
             elif    'PSA Pwr Out(dBm)' in self.data and self.data[ 'PSA Pwr Out(dBm)' ][rn] != None:
                     pdbm = self.data[ 'PSA Pwr Out(dBm)' ][rn]
             elif   'Pout(dBm)' in self.data and self.data[ 'Pout(dBm)' ][rn] != None:
                     pdbm = self.data[ 'Pout(dBm)' ][rn]
             elif    'Adj Pwr Out(dBm)' in self.data and self.data[ 'Adj Pwr Out(dBm)' ][rn] != None:
                     pdbm = self.data[ 'Adj Pwr Out(dBm)' ][rn]

             # Make sure we dont redefine Pout(dBm) for the 5G tests
             if self.data['TestName'][rn] in ['ACLR 5G', 'Capture IQ 5G']:
                 if  'Pout(dBm)' in self.data and self.data[ 'Pout(dBm)' ][rn] != None:
                     pdbm = self.data[ 'Pout(dBm)' ][rn]

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

      # Convert the available power numbers into a generic column 'Pout' with units of dBm,W,V
      if 'Pin(dBm)' in self.data or 'Pwr In(dBm)' in self.data:
         self.add_new_column( 'Pin(dBm)'  )
         self.add_new_column( 'Pin(mW)'  )
         self.add_new_column( 'Pin(V)'  )
         self.add_new_column( 'Pinpk(V)'  )
         for rn in range( rn_start, rn_finish ):
             pdbm = None
             # Decide on which of the possible power measurement values is to be mapped to the main Pout(dBm) value
             if    'Pwr In(dBm)' in self.data and self.data[ 'Pwr In(dBm)' ][rn] != None:
                     pdbm = self.data[ 'Pwr In(dBm)' ][rn]
             elif    'Pin(dBm)' in self.data and self.data[ 'Pin(dBm)' ][rn] != None:
                     pdbm = self.data[ 'Pin(dBm)' ][rn]


             if pdbm != None :

                 try:
                     pw = 10**( (pdbm-30.0)/10.0 )
                     pv = sqrt( self.characteristic_impedance * pw )
                     self.data[ 'Pin(dBm)' ][rn]  = pdbm
                     self.data[ 'Pin(mW)'   ][rn]  = pw * 1000
                     self.data[ 'Pin(V)'   ][rn]  = pv
                     self.data[ 'Pinpk(V)'   ][rn]  = pv * 1.414213562
                 except:
                     pass



      # Convert the available power numbers into a generic column 'Pout' with units of dBm,W,V
      if 'Pwr In(dBm)' in self.data and 'Pout(dBm)' in self.data :
         self.add_new_column( 'Pwr Gain(dB)'  )
         for rn in range( rn_start, rn_finish ):
            if 1 or ( self.data['TestName'][rn] in ['Output Power & Efficiency'] ):
                try:
                    self.data['Pwr Gain(dB)'][rn]  = self.data['Pout(dBm)'][rn] - self.data['Pwr In(dBm)'][rn]
                except: pass
         self.add_slope( 'Pwr In(dBm)', 'Pout(dBm)', 'Pwr Gain Variation(dB/dB)', rn_start, rn_finish)
         self.add_slope( 'Pwr In(dBm)', 'Pout(dBm)',  'Gain Linearity(dB/dB)', rn_start, rn_finish, -1)

      if 'Pwr In(dBm)' in self.data and 'Pout_pm(dBm)' in self.data and 'TestName' in self.data :
         self.add_new_column( 'Pwr Gain(dB)'  )
         for rn in range( rn_start, rn_finish ):
            if ( self.data['TestName'][rn] == 'ACLR'):
                try:
                    self.data['Pwr Gain(dB)'][rn]  = self.data['Pout_pm(dBm)'][rn] - self.data['Pwr In(dBm)'][rn]
                except: pass
         self.add_slope( 'Pwr In(dBm)', 'Pout_pm(dBm)', 'Pwr Gain Variation(dB/dB)', rn_start, rn_finish)
         self.add_slope( 'Pwr In(dBm)', 'Pout_pm(dBm)', 'Gain Linearity(dB/dB)', rn_start, rn_finish, -1)

      if 'Pin_cplr(dBm)' in self.data and 'Pout_SA(dBm)' in self.data:
          self.add_math_data('Pwr Gain SA(dB)', 'Pout_SA(dBm)', '-', 'Pin_cplr(dBm)', rn_start, rn_finish, )

      if 'Pin_cplr(dBm)' in self.data and 'Pout(dBm)' in self.data:
          self.add_math_data( 'Pwr Gain(dB)', 'Pout(dBm)', '-', 'Pin_cplr(dBm)', rn_start, rn_finish )


    
#       # Convert the available power numbers into a generic column 'Pout' with units of dBm,W,V
#       if 'Pwr In(dBm)' in self.data and 'Pout(dBm)' in self.data and 'TestName' in self.data :
#          self.add_new_column( 'Pwr Gain(dB)'  )
#          for rn in range( rn_start, rn_finish ):
# #            if ( self.data['TestName'][rn] == 'Output Power & Efficiency'):
#             if (( self.data['TestName'][rn] == 'Output Power & Efficiency') or ( self.data['TestName'][rn] == 'ACLR')):
#                 try:
#                     self.data['Pwr Gain(dB)'][rn]  = self.data['Pout(dBm)'][rn] - self.data['Pwr In(dBm)'][rn]
#                 except: pass
#          self.add_slope( 'Pwr In(dBm)', 'Pout(dBm)', 'Pwr Gain Variation(dB/dB)', rn_start, rn_finish)
#          self.add_slope( 'Pwr In(dBm)', 'Pout(dBm)', 'Gain Linearity(dB/dB)', rn_start, rn_finish, -1)



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




#          # Add Pout slope data (vs Vramp)
#          self.add_slope( vam_name, 'Poutpk(V)', 'AMAM conversion Voutpk/VAM (dV/dV)', rn_start, rn_finish)
#          self.add_slope( vam_name, 'Pout(dBm)', 'Power Control Slope (dB/V)', rn_start, rn_finish)

 
      self.add_slope( 'Vramp(V)', 'Poutpk(V)', 'AMAM conversion Voutpk/VAM (dV/dV)', rn_start, rn_finish)
      self.add_slope( 'Vramp(V)', 'Pout(dBm)', 'Power Control Slope (dB/V)', rn_start, rn_finish)
 
     
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
         name = 'Log File Format Version'
         if name in self.data and self.data[name][rn_start] == 'Pypat' :

            

            self.add_ref_pout_data_pypat( rn_start, rn_finish, matchname='Vramp' )
            self.add_rated_power_values( rn_start, rn_finish )

         else:
         
#         if 1==1 or self.vramp_search_testname in self.values_dict[ 'TestName' ]:
             rnl_list = self.get_nom_conditions( rn_start, rn_finish)

             # for each of the nominal cond list go through the

             if rnl_list != None and len( rnl_list ) > 0 :
                 for rnl in rnl_list:
                     self.update_nom_conditions( rnl )
#                     self.add_ref_pout_data( rnl, rn_start, rn_finish, testname='Power_and_Eff',             matchname='Vramp Voltage')
                     self.add_ref_pout_data( rnl, rn_start, rn_finish, testname='Output Power & Efficiency', matchname='Vramp Voltage')
                     self.add_ref_pout_data( rnl, rn_start, rn_finish, testname='AM-AM AM-PM Distortion'   , matchname='Step')

                 self.add_rated_power_values( rn_start, rn_finish )


      self.scale_data('ActualPout', 'Pout(dBm)', 1, rn_start, rn_finish)
      self.scale_data('ActualPin', 'Pwr In(dBm)', 1, rn_start, rn_finish)






    ######################################################################################
    def copy_pout_data( self, rn_start, rn_finish ):
        '''Copy 'Adj Pwr Out(dBm)' to 'Pout(dBm)' and visa versa 
        '''

        self.add_new_column( 'Adj Pwr Out(dBm)'  )
        self.add_new_column( 'Pout(dBm)'  )
        for rn in range( rn_start, rn_finish ):
            p_adj = self.data[ 'Adj Pwr Out(dBm)' ][rn]
            p_out = self.data[ 'Pout(dBm)' ][rn]
            if p_out not in UNDEFS:
                self.data[ 'Adj Pwr Out(dBm)' ][rn] = p_out
            else:
                if p_adj not in UNDEFS:
                    self.data[ 'Pout(dBm)' ][rn] = p_adj

    ######################################################################################
    def copy_column_data( self, name1, name2, rn_start, rn_finish, enable_reverse_copy=True ):
        '''Copies data from one column to another column , 
        if the data in name1 column exists it is copied to name2 column
        else the data in name2 column is copied to name1 column
        '''

        if name1 in self.data:
            self.add_new_column( name1 )
            self.add_new_column( name2 )
            for rn in range( rn_start, rn_finish ):
                value1 = self.data[ name1 ][rn]
                value2 = self.data[ name2 ][rn]
                if value1 not in UNDEFS:
                    self.data[ name2 ][rn] = value1
                else:
                    if enable_reverse_copy:
                        if value2 not in UNDEFS:
                            self.data[ name1 ][rn] = value2

    ######################################################################################
    def get_vramp_or_pin(self, rn):
        '''Determine whether the test record is a linear or saturated type test
        and return the controlling value of Vramp or Pin'''
        
        
        if 'ControlMode' in self.data and self.data['ControlMode'][rn] in ['LB','HB']:
            return 'Vramp'
        else:
            return 'Pwr In(dBm)'


    ######################################################################################
    def add_ref_pout_data_pypat( self, rn_start, rn_finish, matchname ):
         '''For pypat based logfoiles add 'Ref Pout', 'Ref2 Pout' , and 'Pwr Variation' data
         ''' 

         if 'NC_Match'  not in self.data or \
            'Pout(dBm)' not in self.data:
                 return


         N_voltage_list = [ 'N20','N21','N22','N23','N24','N25','N26','N27','N28','N29',
                           'N30','N31','N32','N33','N34','N35','N36','N37','N38','N39',
                           'N40','N41','N42','N43','N44','N45','N46','N47','N48','N49',
                           'N50','N51','N52','N53','N54','N55','N56','N57','N58','N59', ]

         vramp2pout = {}
         vramp2rn   = {}

         self.add_new_column( 'Ref Pout(dBm)'      )
         self.add_new_column( 'Pwr Variation(dB)' )
         self.add_new_column( 'Ref2 Pout(dBm)'      )
         self.add_new_column( 'Pwr2 Variation(dB)' )

         # First build up the vramp2pout and vramp2rn dicts
         for rn in range( rn_start, rn_finish ):

            # Only use the Output Power and Efficiency tests or power search tests to build up the vramp2pout dicts
            testname     = self.data[ 'TestName' ][rn]
            if not isinstance(testname,  types.StringTypes) or \
                not ( testname in ['Output Power & Efficiency','Edge ORFS Modulation'] or 'search' in testname.lower() ):
                continue
            
            nc_match_fld = self.data['NC_Match' ][rn]
            ptarget      = self.data['NC_Target'][rn]
            pout         = self.data['Pout(dBm)'][rn]
            matchname = self.get_vramp_or_pin(rn)
            vramp        = self.data[ matchname ][rn]
#              ptarget       not in UNDEFS  and \
            if nc_match_fld not in UNDEFS  and \
              pout          not in UNDEFS  and \
              vramp         not in UNDEFS:
                nc_match_vals = nc_match_fld.split(',')
                for nc_match_name in nc_match_vals:
                    nc_match_name = nc_match_name.strip()
                    if nc_match_name not in UNDEFS:
                        
                        if nc_match_name not in vramp2pout:
                            vramp2pout[ nc_match_name ] = {}
                            vramp2rn[   nc_match_name ] = {}
                            
                            # determine whether this is a center of band nominal condition or 
                            # an 'at_frequency' nonminal condition
                            # If the NC name ends with a number then it an 'at_frequency' NC 
                            # and we give it an 'Ref2 Pout(dBm)' else if it contains
                            # some non digits then it is a center_of_band NC so 
                            # save it as a 'Ref Pout(dBm)' value 
                            nc_names = nc_match_name.split('_')
                            nc_name_tail = nc_names[-1]
                            try:
                                x = int(nc_names[-1])
                                txt = '2'
                            except:
                                txt = ''
                            self.add_new_column( 'Ref%s Pout(dBm) %s'      % (txt, nc_names[0] ))
                            self.add_new_column( 'Pwr%s Variation(dB) %s' % (txt, nc_names[0] ))
                        
                        vramp2pout[ nc_match_name ][ vramp ] = pout
                        vramp2rn[ nc_match_name ][ vramp ] = rn
        
#          for  nc_match_name in vramp2pout:
#             print '-------------------------------'
#             print '<%s>' % nc_match_name
#             for vramp in vramp2rn[ nc_match_name ]:
#                 print '    <%s>    %10s' % (vramp, vramp2pout[ nc_match_name ][vramp])
        
           
         # Then write out the 'Ref Pout', values for all NC_Reference values
         for rn in range( rn_start, rn_finish ):
            nc_reference_fld = self.data['NC_Reference' ][rn]
            matchname = self.get_vramp_or_pin(rn)
            vramp        = self.data[ matchname ][rn]
            
            if self.data['linenumber'][rn] == 10858:
                ln = True
            else:
                ln = False
            
            
            if ln :    print '_pypat X nc_reference_fld=',   nc_reference_fld
            
            if nc_reference_fld not in UNDEFS and \
                vramp not in UNDEFS:
                
                
                                
                nc_reference_vals = nc_reference_fld.split(',')
                new_nc_reference_vals = []
                for nc_reference_name in nc_reference_vals:
                    nc_reference_name = nc_reference_name.strip()
                    if nc_reference_name not in UNDEFS:
                    
#                       if ln :    print '_pypat     nc_reference_name=',   nc_reference_name
                       
                       # Split the name on '_' characters. If the last part is an integer then
                       # we have an At-freq NC_Reference
                       nc_names = nc_reference_name.split('_')
                       nc_name_tail = nc_names[-1]
                       try:
                         nc_freq_int = int(nc_name_tail)
                         ref_pout_txt = '2'
                       except:
                         nc_freq_int  = None
                         ref_pout_txt = ''     

                         
                       # Remove any bogus NC_Reference names 
                       keep_nc_ref = False
                       # If the nc name tail is a frequency and it is the same as the current frequency
                       # then keep the NC_Reference_name
                       freq = self.data[ 'Freq(MHz)' ][rn]
                       
                       if freq not in UNDEFS:
                       
                           f = int(float(freq))
                       
                           if nc_freq_int == f:
                             keep_nc_ref = True
     
                           # If the nc name tail is a subband and it is the same as the current subband
                           # then keep the NC_Reference_name
                           
                           if nc_freq_int == None:
                               fidx = self.get_subband_idx_from_freq(f)
                               fsubband =   self.freq_sub_band_list[fidx][0]                 
                       
                               if nc_name_tail in fsubband:
                                    keep_nc_ref = True

                       if ln :    
#                            print '_pypat       keep_nc_ref=%s (nc_name_tail=%s  nc_freq_int=%s ref_pout_txt=%s freq=%s f=%s fidx=%s fsubband=%s' % \
#                                  ( keep_nc_ref, nc_name_tail, nc_freq_int, ref_pout_txt, freq, f, fidx, fsubband )
#                            print '_pypat    vramp=', vramp, nc_reference_name
                          pass
                    
                       if keep_nc_ref  and nc_reference_name in vramp2pout and \
                           vramp in vramp2pout[nc_reference_name] :
                                                          
                               new_nc_reference_vals.append( nc_reference_name )

#                               if ln :    print '>>>\n\n_pypat     NEW new_nc_reference_vals=', new_nc_reference_vals , '\n\n'

                               # determine whether this is a center of band nominal condition or 
                               # an 'at_frequency' nonminal condition
                               
                               pout = '?'
                               ref_pout = '?'
                           
                               name = 'Ref%s Pout(dBm)' % ref_pout_txt
                               
                               if name in self.data:
                                    ref_pout =  vramp2pout[nc_reference_name][vramp]
                                    self.data[name][rn] = ref_pout

                    
                                    if nc_names[0] in N_voltage_list:
                                        name = 'Ref%s Pout(dBm) %s'      % (ref_pout_txt, nc_names[0] )  
                                        if name in  self.data:                            
                                            self.data[name][rn] = ref_pout     



                new_nc_reference_names = ','.join(new_nc_reference_vals)
                self.data['NC_Reference' ][rn] = new_nc_reference_names[:]

#                if ln :    print ">>>\n\n_pypat     NEW WRITING self.data['NC_Reference' ][rn]=", self.data['NC_Reference' ][rn] , '\n\n'


         # Then write out the 'Pwr Variation', values for all NC_Reference values
         for rn in range( rn_start, rn_finish ):
            nc_reference_fld = self.data['NC_Reference' ][rn]
            matchname = self.get_vramp_or_pin(rn)
            vramp        = self.data[ matchname ][rn]
            if nc_reference_fld not in UNDEFS and \
                vramp not in UNDEFS:
                nc_reference_vals = nc_reference_fld.split(',')
                for nc_reference_name in nc_reference_vals:
                    nc_reference_name = nc_reference_name.strip()
                    if nc_reference_name not in UNDEFS and \
                       nc_reference_name in vramp2pout and \
                       vramp in vramp2pout[nc_reference_name] :
                       
                           # determine whether this is a center of band nominal condition or 
                           # an 'at_frequency' nonminal condition
                           
                           pout = '?'
                           ref_pout = '?'
                           
                           nc_names = nc_reference_name.split('_')
                           nc_name_tail = nc_names[-1]
                           try:
                             x = int(nc_names[-1])
                             txt = '2'
                           except:
                             txt = ''                       
                       
                           name = 'Ref%s Pout(dBm) %s'      % (txt, nc_names[0] )
                           ref_pout = self.data[name][rn]
                    
                           name = 'Pwr%s Variation(dB) %s' % (txt, nc_names[0]  )
                           pout = self.data['Pout(dBm)'][rn]
                           if name in self.data and pout not in UNDEFS and ref_pout not in UNDEFS and \
                                   not isinstance(pout,types.StringTypes) and  \
                                   not isinstance(ref_pout,types.StringTypes):
                                self.data[name][rn] = pout - ref_pout
                
                                if nc_names[0] in N_voltage_list:
                                    name = 'Pwr%s Variation(dB)' % txt
                                    self.data[name][rn] = pout - ref_pout



    ######################################################################################
    def dbg_print(self, prefix_text, rn, name ):            
    
         try:
             print '%s     self.data[%s][%s]=   %s' % (prefix_text, name, rn, self.data[name][rn])
         except:
             print '%s     self.data[%s][%s]=   CANNOT PRINT' % (prefix_text, name, rn)


    ######################################################################################
    def get_timestamp( self, rn ):
        ''' returns the timestamp in seconds for the current test'''
        
        if 'Date' not in self.data or 'Time' not in self.data: 
            return None
            
        
        d = self.data['Date'][rn]
        t = self.data['Time'][rn]
        
        if d != None and t != None:
            d  = '%s' % d
            t  = '%s' % t
            dt = '%s %s' % (d, t)
        else:
            return None
        
        
        dpar = 'd'
        mpar = 'm'
        # swap month and day if needed, 
        # if the first field in the date is greater than 12 then month and  need to be swapped
        num = re.findall('^\d+', d.strip())
        if len(num) > 0 and int(num[0]) > 12:
            dpar = 'm'
            mpar = 'd'
        
        # also the year might be 2 or 4 characters long, so choose the appropriate Year format character
        ypar = 'y'
        num = re.findall('\d+$', d.strip())
        if len(num) > 0 and len(num[0]) > 2:
            ypar = 'Y'
        

        if   d.find('-'):  
            fmt = '%%%s-%%%s-%%%s' % ( mpar, dpar, ypar )
        elif d.find('/'):
#            fmt = "%m/%d/%Y"
            fmt = '%%%s/%%%s/%%%s' % ( mpar, dpar, ypar )
        elif d.find(':'):
#            fmt = "%m:%d:%Y"
            fmt = '%%%s:%%%s:%%%s' % ( mpar, dpar, ypar )
        else:  
#            fmt = "%m-%d-%Y"
            fmt = '%%%s-%%%s-%%%s' % ( mpar, dpar, ypar )
                
        if t[-1:].lower() == 'm':
            fmt = fmt + ' %I:%M:%S %p'
        else:
            fmt = fmt + ' %H:%M:%S'


        
        try:
           tstruct = time.strptime( dt , fmt)
        except:
           return None

        timestamp = time.mktime( tstruct ) + 0.0
        
        return timestamp
        
        
        
        

    ######################################################################################
    def  calculate_test_time_statistics( self, rn_start, rn_finish ): 
        '''Gets the run time for each test and calculates the run time statistics for each type of test
        Writes out a statistics summary to a runtime logging file for tracking how runtimes vary over time'''
        
        
        
        
        
        
        
        
        for n in ['Date','Time','TestName']:
            if n not in self.data: 
                return




# 
# 
#    "//DUT Test GUI Version Number: Rev. A1.00.338"
#    
#    "//Test Date & Time: 11-20-2010 0:57:55
#    "//Station Number: 6"
#    "//Script File Name: l:\Lab & Testing\XS\TXM\Spec Test\MD\7806\ATRPRD_maddog_temp.txt"
#    "//Serial Number: xAM7806-TU-DE-SN002"
#    "//Chip Model: Mad Dog TxM 7806"


        name = 'Log File Format Version'
        if name in self.data and self.data[name][rn_start] == 'Pypat' :
            mode = 'Pypat'
        else:
            mode = 'old_atr_gui'


        self.add_new_column( 'timestamp' )
        self.add_new_column( 'test_full_time' )
        self.add_new_column( 'test_run_time' )
        self.add_new_column( 'test_setup_time' )
        
        # first get the runtimes of each test.
        # but do not calculate for the first test only calculate for second and sebsequent tests
        # (this is to seperate the setup time for a test
        # from its actual run time)
        
        prev_testnum = None
        prev_timestamp = None
        prev_testname   = None
        for rn in range( rn_start, rn_finish ): 
        
            testnum   = self.data[ '//T#'][rn]
            testname  = self.data[ 'TestName'][rn]
            
            # amam tests have multiple lines per test run, only look at the step == 1 line  
            if testname == 'AM-AM AM-PM Distortion' and self.data['Step'][rn] > 1.5 : 
                continue

            
            
            timestamp = self.get_timestamp( rn )
            if timestamp == None :
                continue
                
            self.data['timestamp'][rn] = timestamp
            if prev_timestamp != None:
                test_full_time =  timestamp - prev_timestamp
                
                # spurious tests which take less than a second are bogus so ignore and continue
                if isinstance(testname,types.StringTypes) and testname[:8] == 'Spurious' and test_full_time < 0.1:
                   continue

                self.data['test_full_time'][rn] = test_full_time
        
            if mode == 'Pypat':
                if testname != prev_testname:
                    new_test = True
                else:
                    new_test = False
            else:
                if testnum != prev_testnum:
                    new_test = True
                else:
                    new_test = False
                
            
                
            if prev_timestamp != None:
                if not new_test:
                    self.data[ 'test_run_time' ][rn] = test_full_time
            
            prev_testnum = testnum
            prev_timestamp = timestamp
            prev_testname = testname
            

        # Go round a second time this time look at the first test only            
        prev_testnum = None
        prev_timestamp = None
        prev_testname  = None
        for rn in range( rn_start, rn_finish ): 
        
            testnum        = self.data[ '//T#'][rn]
            test_full_time = self.data['test_full_time'][rn]
            testname       = self.data[ 'TestName'][rn]

            if mode == 'Pypat':
                if testname != prev_testname:
                    new_test = True
                else:
                    new_test = False
            else:
                if testnum != prev_testnum:
                    new_test = True
                else:
                    new_test = False
                
                    # if the next record has the same test number then
                    # use the next test_run_time as the current test_run_time
                    
                    # and make the setup time the difference between the actual test_full_time and the next tests test_run_time
                    
            if prev_timestamp != None:
                if new_test:
                    
                    
                    try:
                        if mode != 'Pypat' and  self.data[ '//T#'][rn+1] == testnum or \
                           mode == 'Pypat' and  self.data[ 'TestName'][rn+1] == testname:
                            next_test_time = self.data[ 'test_run_time' ][rn+1]
                            self.data[ 'test_run_time' ][rn] = next_test_time
                            
                            test_setup_time = test_full_time - next_test_time
                            self.data[ 'test_setup_time' ][rn] = test_full_time - next_test_time
                    except: pass
                                
                
            prev_testnum = testnum
            prev_timestamp = timestamp
            prev_testname = testname
            
            
        del  self.values_dict['TestName']
        self.add_values_dict('TestName', rn_start, rn_finish  )
        tnl = self.values_dict[ 'TestName']
        tnl.sort()
            
        testname_total_run_time   = {}
        testname_total_full_time  = {}
        testname_total_setup_time = {}
        testname_average_run_time   = {}
        testname_average_setup_time = {}
        testname_total_run_time_count = {}
        testname_total_setup_time_count = {}
        
        for tn in tnl:
            testname_total_run_time[ tn ]  = 0.0
            testname_total_full_time[ tn ] = 0.0
            testname_total_setup_time[ tn ] = 0.0
            testname_total_run_time_count[ tn ] = 0.0
            testname_total_setup_time_count[ tn ] = 0.0
        total_test_time = 0.0

        for rn in range( rn_start, rn_finish ):
            tn = self.data['TestName'][rn]
            if isinstance(tn,types.StringTypes) and tn in testname_total_run_time:

                trt = self.data['test_run_time'][rn]
                tft = self.data['test_full_time'][rn]

                # spurious tests which take less than a second are bogus so ignore and continue
                if tn[:8] == 'Spurious' and trt < 0.1: 
                    continue
                # amam tests have multiple lines per test run, only look at the step == 1 line  
                if tn == 'AM-AM AM-PM Distortion' and self.data['Step'][rn] > 1.5 : 
                    continue
                    
                if trt != None:
                    testname_total_run_time[ tn ] += trt 
                    testname_total_run_time_count[ tn ] += 1.0
                if tft != None:
                    testname_total_full_time[ tn ] += tft
                    total_test_time += tft


                tst = self.data['test_setup_time'][rn]
                if tst != None:
                    testname_total_setup_time[ tn ] += tst
                    testname_total_setup_time_count[ tn ] += 1.0


        print '\n@@@@@@@@@  TEST TIME RUN STATISTICS @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
        try:
            print '@@ TestName                Num_of_Tests   Avg_Run_Time  Num_of_setups  Avg_Setup_time  Total_time %'
            for tn in tnl:
                if testname_total_run_time_count[tn] > 0.1:
                    testname_average_run_time[tn] = testname_total_run_time[tn]/testname_total_run_time_count[tn]
                else:
                    testname_average_run_time[tn] = 0.0
                if testname_total_setup_time_count[tn] > 0.1:
                    testname_average_setup_time[tn] = testname_total_setup_time[tn]/testname_total_setup_time_count[tn]
                else:
                    testname_average_setup_time[tn] = 0.0
                    
                tft = testname_total_full_time[ tn ]
                print '@@ %-30s %5d %10.3f(sec)   %5d %10.3f(sec)  %s (%4.1f%%)' % ( tn, \
                    testname_total_run_time_count[ tn ],
                    testname_average_run_time[ tn ],
                    testname_total_setup_time_count[ tn ],
                    testname_average_setup_time[ tn ],
                    self.sec2timestr( tft ),
                    100.0 * tft/ total_test_time ,
                     )
                    
            print '@@@@@   TOTAL TEST TIME =', self.sec2timestr( total_test_time ),  '(hours:mins:secs)'
            print '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n'
        except:
            pass
        
    ######################################################################################
    def sec2timestr(self, sec):
        '''Converts a float value in seconds to a H:M:S string'''

        t = sec
        s = t % 60   # num seconds
        t = (t-s) / 60  #num mins
        m = t % 60
        h = (t-m) / 60
         
        tstr = '%3.0f:%02.0f:%02.0f' % ( h, m, s )
        
        return tstr

    ######################################################################################
    def add_vmux_values( self, rn_start, rn_finish ):
        '''Adds copies of the Vmux(V) values for each VMUX signal selection
        Then goes through all records and adds the Vmux_* values to all the
        other records which match the same conditions'''
        
        if 'Vmux(V)' in self.data and 'VMUX' in self.data:
            
            # Map the Vmux(V) voltage value into new Vmux_<signame> columns        
            new_vmux_sig_list = []
            for rn in range( rn_start, rn_finish ):
                vmux_val = self.data['Vmux(V)'][rn]
                vmux_sig = self.data['VMUX'][rn]                
                if vmux_sig not in UNDEFS and vmux_val not in UNDEFS:
                    new_sig = 'Vmux_%s(V)' % vmux_sig
                    if new_sig not in new_vmux_sig_list:
                        new_vmux_sig_list.append(new_sig)
                        self.add_new_column( new_sig )
                    
                    self.data[new_sig][rn] = vmux_val
                    
            # Get a list of all the Registers that could be being swept
            reg_list = []
            for col in self.data:
                if col[:4] == 'REG_':
                    if col not in reg_list:
                        reg_list.append(col)     
            
            # Get a list of all other conditions that could be being swept
            cond_list = ['Register', 'ControlSignals', 'Freq(MHz)', 
              'Phase(degree)', 'Pwr In(dBm)', 'Temp(C)',
              'VSWR', 'Vbat(Volt)', 'Vramp Voltage' ]
              
            cond_list.extend(reg_list)
            new_cond_list = []
            for cond in cond_list:
                if cond in self.data:
                    new_cond_list.append(cond)
            cond_list = new_cond_list
            
            # Go through all the records from the first record to the last
            # looking for matching conditions
            done = [None] * rn_finish
            conds = [None] * rn_finish
            for rn in range(rn_finish):
                conds[rn] = self.get_cond_value_list_from_rn(rn, cond_list )
            rn = 0
            while rn < rn_finish:
                if not done[rn]:
#                    cond_vals = self.get_cond_value_list_from_rn(rn, cond_list )
                    cond_rn_list = [rn]
                    for rnc in range(rn+1, rn_finish):
#                        if not done[rn] and self.compare_conditions( rnc, cond_list, conds[rn] ):
                        if not done[rn] and conds[rn] == conds[rnc]:
                            cond_rn_list.append(rnc)
                    done[rn] = True
                
#                    print '(add_vmux_values) ', rn, conds[rn], cond_rn_list
                
                    # We now have cond_rn_list which is a list of record numbers 
                    # that have the same conditions. We can now mirror all the
                    # non null Vmux_signame values to all other records in this
                    # list
                    for vmux_sig in new_vmux_sig_list:
                        vmux_sig_val_list = []
                        for rnv in cond_rn_list:
                            if self.data[vmux_sig][rnv] not in UNDEFS:
                                val = self.data[vmux_sig][rnv]
                                vmux_sig_val_list.append(val)
                        
                        vmux_sig_val = sum(vmux_sig_val_list)/len(vmux_sig_val_list)
#                        print '    (add_vmux_values)   ', vmux_sig, vmux_sig_val, vmux_sig_val_list
                        for rnv in cond_rn_list:
                            if self.data[vmux_sig][rnv] in UNDEFS:
                                val = self.data[vmux_sig][rnv] = vmux_sig_val
                            done[rnv] = True
                        
                     
                
                rn += 1
                       
                

    ######################################################################################
    def add_vmux_columns( self, rn_start, rn_finish ):

#      return

      # Add some special vmux columns
      pname = '[csv] Script File Name'
      if pname in self.data:

          name_a   = '[Time] AVDDRV3_TM'
          name_b   = '[Time] FB_TM'
          new_name = '[Time] AVDDRV3*'



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
      if 'PSA Pwr Out(dBm)' in self.data:
          if 'ACLR -5MHz(dBc)'   in self.data and \
             'ACLR -10MHz(dBc)' in self.data and \
             'ACLR +5MHz(dBc)'   in self.data and \
             'ACLR +10MHz(dBc)'  in self.data    :
              self.add_new_column( 'Pwr Gain (PSA)' )
              self.add_new_column( 'Pout(dBm)' )
                       
              self.add_new_column( 'ACLR 5MHz(dBc)' )
              self.add_new_column( 'ACLR 5MHz Delta(dBc)' )
              self.add_new_column( 'ACLR 10MHz(dBc)' )
              self.add_new_column( 'ACLR FOM' )
              self.add_new_column( 'ACLR FOM40' )


            

# Gain = Pwr at Center Freq (dBc)  -  Pwr In (dBm)
#  ACLR-5 = -Pwr at Center Freq (dBc)  +  Pwr at -5MHz Offset (dBc)
#  ACLR5  = -Pwr at Center Freq (dBc)  +  Pwr at 5MHz Offset (dBc)
#  ACLR5  = -Pwr at Center Freq (dBc)  +  Pwr at -10MHz Offset (dBc)
#  ACLR10 = -Pwr at Center Freq (dBc)  +  Pwr at 10MHz Offset (dBc)

              
              for rn in range( rn_start, rn_finish ):
                if self.data['PSA Pwr Out(dBm)'][rn] != None and self.data['TestName'][rn][:4] == 'ACLR':
                   self.data['Pwr Gain (PSA)'][rn] = self.data['PSA Pwr Out(dBm)'][rn] - self.data['Pwr In(dBm)'][rn]
                   self.data[ 'Pout(dBm)' ][rn]    = self.data['PSA Pwr Out(dBm)'][rn]
                   self.data[ 'ACLR 5MHz(dBc)' ][rn] = max( self.data[ 'ACLR +5MHz(dBc)' ][rn], self.data[ 'ACLR -5MHz(dBc)' ][rn] )
                   self.data[ 'ACLR 5MHz Delta(dBc)' ][rn] =  self.data[ 'ACLR +5MHz(dBc)' ][rn] - self.data[ 'ACLR -5MHz(dBc)' ][rn] 
                   self.data[ 'ACLR 10MHz(dBc)' ][rn] = max( self.data[ 'ACLR +10MHz(dBc)' ][rn], self.data[ 'ACLR -10MHz(dBc)' ][rn] )
                   if 'PAE(%)' in self.data and self.data[ 'PAE(%)' ][rn] != None:
                       self.data[ 'ACLR FOM' ][rn] =  self.data[ 'PAE(%)' ][rn]  - self.data[ 'ACLR 5MHz(dBc)' ][rn]
                       aclr40 = max( -40, self.data[ 'ACLR 5MHz(dBc)' ][rn])
                       self.data[ 'ACLR FOM40' ][rn] =  self.data[ 'PAE(%)' ][rn]  - aclr40
#  ACLR-5 = -Pwr at Center Freq (dBc)  +  Pwr at -5MHz Offset (dBc)

    ###################################################################
    def add_acp_data( self,  rn_start, rn_finish ):
      '''Function for creating new ACP and ACPR data based on the + and - offset data
      '''

      # Look through the list of columns looking for columns that match the ACP
      # names, remove the + and - characters to make up a list of new columns
      #  which will contain the max of the + and -
      acp_list = []
      for column in self.data:
            # Look for any columns that start with ACP or ACPR
            if re.match(r'ACP(R)? [\+\-]', column):
                # Then remove the +\- and add it to the list
                new_column = re.sub('[\+\-]', '', column)
                if new_column not in acp_list:
                    acp_list.append(new_column)


      # Foreach of the new columns make sure there is both the + and - ACP 
      # column, and then add the new_column.
      for new_column in acp_list:
          pcol = re.sub(r' ', ' +',new_column)
          ncol = re.sub(r' ', ' -',new_column)
          if pcol in self.data and ncol in self.data:
              self.add_new_column(new_column)
              # Go through all non null records and add the max value
              for rn in range( rn_start, rn_finish ):
                  pdat = self.data[ pcol ][ rn ]
                  ndat = self.data[ ncol ][ rn ]
                  if pdat not in UNDEFS and ndat not in UNDEFS:
                      self.data[ new_column ][ rn ] = max( pdat, ndat)
                        
        



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
                if self.data[ name ][ rn ] not in UNDEFS:
                     self.data[ new_name ][ rn ] = self.data[ name ][ rn ] * scale

    ###################################################################
    def add_math_data( self, new_name, name1, oper1, name2, oper2=None, name3=None, rn_start=None, rn_finish=None ):
       ''' Creates a new column 'new_name' by calculating name1 oper1 name2 oper2 name3
          oper2 and name3 are optional.
          It takes the values from left to right,

         Updates:  self.data[ new_name ]

         Parameters:

             new_name  :   Name of new column which will be have the scaled data
             name1     :   Name of existing column to be used in calculation, or a fixed numerical value
             oper1     :   '+', '-', '*', '/'
             name2     :   Name of existing column to be used in calculation, or a fixed numerical value
             oper2     :   '+', '-', '*', '/'
             name3     :   Name of existing column to be used in calculation, or a fixed numerical value
             rn_start  :  starting record number, defaults to the first record number 0
             rn_finish :  finish record number. Only records between rn_start and rn_finish will be calculated. defaults to the last record self.datacount

         Returns:  None'''

       if rn_start == None:
           rn_start = 0
       if rn_finish == None:
           rn_finish = self.datacount
           
       try:
         v1 = float(name1)
         v1_fixed = 1
       except:
         v1_fixed = 0
         if isinstance(name1,types.ListType):
            v1_fixed = 2

       try:
         v2 = float(name2)
         v2_fixed = 1
       except:
         v2_fixed = 0
         if isinstance(name1,types.ListType):
            v3_fixed = 2

       try:
         v3 = float(name3)
         v3_fixed = 1
       except:
         v3_fixed = 0 
         if isinstance(name3,types.ListType):
            v3_fixed = 2
         

       if (v1_fixed!=0 or name1 in self.data) and \
          (v2_fixed!=0 or name2 in self.data) and \
          (name3 == None or v3_fixed!=0 or name3 in self.data):
           self.add_new_column( new_name )
           for rn in range( rn_start, rn_finish ):
                # If any of the values are a two element list choose the LB or HB index
                if v1_fixed == 2 or v3_fixed == 2 or v3_fixed == 2:
                    hblb = self.data[ 'HB_LB' ][ rn ]
                    if hblb == 'LB':
                        hblb_idx = 0
                    else:
                        hblb_idx = 1
                
                if   v1_fixed == 0:
                    v1 = self.data[ name1 ][ rn ]
                elif v1_fixed == 2:
                    v1 = name1[hblb_idx]

                if   v2_fixed == 0:
                    v2 = self.data[ name2 ][ rn ]
                elif v2_fixed == 2:
                    v2 = name2[hblb_idx]
                
                tmp = None
                if v1 not in UNDEFS and v2 not in UNDEFS:
                     v1 = float(v1)
                     v2 = float(v2)
                     if oper1 == '+':
                        tmp = v1 + v2
                     elif oper1 == '-':
                        tmp = v1 - v2
                     elif oper1 == '*':
                        tmp = v1 * v2
                     elif oper1 == '/':
                        tmp = v1 / v2
                     
                     if name3!=None:
                        if   v3_fixed == 0:
                            v3 = self.data[ name3 ][ rn ]
                        elif v3_fixed == 2:
                            v3 = name3[hblb_idx]

                        if v3 not in UNDEFS:
                             v3 = float(v3)
                             if oper2 == '+':
                                tmp = tmp + v3
                             elif oper2 == '-':
                                tmp = tmp - v3
                             elif oper2 == '*':
                                tmp = tmp * v3
                             elif oper2 == '/':
                                tmp = tmp / v3
                        else:
                            tmp = None   
                        
                if tmp:        
                    self.data[ new_name ][ rn ] = tmp


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
             Then repeat this operation and make further Ref Pout columns specific to each nominal condition
                    self.data['Ref Pout(dBm) N2.7' ][rn]  = vramp2pout[nominal_condition_name][vramp] 
                    self.data['Ref2 Pout(dBm) N2.7'][rn]  = vramp2pout[nominal2_condition_name][vramp]
                    self.data['Ref Pout(dBm) N3.5' ][rn]  = vramp2pout[nominal_condition_name][vramp] 
                    self.data['Ref2 Pout(dBm) N3.5'][rn]  = vramp2pout[nominal2_condition_name][vramp]
        
             If there was 'Ref Pout' but no 'Ref2 Pout' then copy 'Ref Pout' to 'Ref2 Pout'

          5) At the same time as doing 4) create 'Pwr Variation' data 
                    self.data['Pwr Variation(dB)'][rn]  =  self.data['Pout(dBm)'][rn] - self.data['Ref Pout(dBm)'][rn]
                    self.data['Pwr2 Variation(dB)'][rn] =  self.data['Pout(dBm)'][rn] - self.data['Ref2 Pout(dBm)'][rn]

                    self.data['Pwr Variation(dB) N2.7'][rn]  =  self.data['Pout(dBm)'][rn] - self.data['Ref Pout(dBm) N2.7'][rn]
                    self.data['Pwr2 Variation(dB) N2.7'][rn] =  self.data['Pout(dBm)'][rn] - self.data['Ref2 Pout(dBm) N2.7'][rn]
                    self.data['Pwr Variation(dB) N3.5'][rn]  =  self.data['Pout(dBm)'][rn] - self.data['Ref Pout(dBm) N3.5'][rn]
                    self.data['Pwr2 Variation(dB) N3.5'][rn] =  self.data['Pout(dBm)'][rn] - self.data['Ref2 Pout(dBm) N3.5'][rn]



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
      if matchname not in self.data                     :  return


#       print '\n(add_cal_pout_data) DOING matchname ', matchname, rn_start, rn_finish
#       print ' rnl=', rnl

      if matchname == 'Step':
         matchname_str = 'AMAM Staircase'
      else:
         matchname_str = 'Vramp'


     # 3.
      # Go through all the records looking for the Power and Efficiency records that match the nominal conditions
      # and save away the vramp pout in a vramp2calpout dict.
      # (if there weren't any, look for PSA test results instead)


      current_nominal_condition_root_name = rnl[2]
      # get rid of any '.' characters as these interfer with the id name used in the Tk list boxes!!!! 
      current_nominal_condition_root_name = re.sub('\.',',',current_nominal_condition_root_name)
      

      # Nominal Center of Band Condition and Reference Power for Center Frequency of Band tests
      self.add_new_column( 'nominal conditions' )
      self.add_new_column( 'nominal conditions ref' )
      self.add_new_column( 'nominal conditions rn' )    # This is a column to indicate which nominal test record number (rn) is associated with this test.

      self.add_new_column( 'Ref Pout(dBm)' )
      self.add_new_column( 'Pwr Variation(dB)' )
      self.add_new_column( 'Ref2 Pout(dBm)' )
      self.add_new_column( 'Pwr2 Variation(dB)' )

      ref_pout_cn  =  'Ref Pout(dBm) %s'      % current_nominal_condition_root_name
      ref2_pout_cn =  'Ref2 Pout(dBm) %s'     % current_nominal_condition_root_name
      pwr_var_cn   =  'Pwr Variation(dB) %s'  % current_nominal_condition_root_name
      pwr2_var_cn  =  'Pwr2 Variation(dB) %s' % current_nominal_condition_root_name
      
      self.add_new_column( ref_pout_cn )        
      self.add_new_column( ref2_pout_cn )
      self.add_new_column( pwr_var_cn )
      self.add_new_column( pwr2_var_cn )

      # Nominal Conditions and Reference Power for exact frequency tests
      self.add_new_column( 'nominal2 conditions' )
      self.add_new_column( 'nominal2 conditions ref' )
      self.add_new_column( 'nominal2 conditions rn' )    # This is a column to indicate which nominal test record number (rn) is associated with this test.

      
      
      
      



      multi_warn_done = False
      rpc = {}
      test_count = 0
      rated_power_count = 0
      ref_pout_count    = 0

#       print '(add_cal) self.nom_freq_list', self.nom_freq_list
#       print '(add_cal) self.freq_sub_band_list', self.freq_sub_band_list 

      vramp2pout = {}
      vramp2rn   = {}


      for fn, fbl in zip( self.nom_freq_list, self.freq_sub_band_list ):
         if fn < 0:   continue     # a negative freq signifies that there were no tests found at a freq within the subband
         flw = fbl[1]   # lower freq of the subband
         fup = fbl[2]   # upper freq of the subband
         subbandname = fbl[0]

         vramp2pout = {}
         vramp2rn   = {}



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
                                if 0:
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
                          if 0:
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
             
                        

         # Dont bother going any further with this subband if there are no measurements made within this band
         if subband_rn_count == 0:
            continue
                      


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
             if 0:
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
             if 0:
                 print "    (add_ref_pout_data) ) [ %s,%s] '%s' data which met the nominal conditions for freq=%s was found. Therefore 'Ref Pout' data will be calculated"  % ( rn_start, rn_finish, matchname_str,  fn)      
             pass
        
#          print '$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$'
#          for ncn in vramp2pout:
#             print ncn
#             print '$ $ $ $ $ $ $ $ $  $ $ $ $'
#             for v in vramp2pout[ncn]:
#                 print  '%10s   %10s' % ( v, vramp2pout[ncn][v] )
#             print '$ $ $ $ $ $ $ $ $  $ $ $ $'
#          print '$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$'

                   
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
             
             
             
             
             rn_pout  = self.data['Pout(dBm)'][rn]
             nominal2_condition_name = '%s_%d' % ( current_nominal_condition_root_name, int(rnfreq) )
             
             ncn   = nominal_condition_name
             n2cn  = nominal2_condition_name

             # Only ref pwr and pwr variation when the sub-band or the record and the cureent sub-ban of the outer loop are the same
             if self.data['Sub-band'][rn] ==  subbandname:  
                      
                 # Firt Go
                 # . . . . . . . . . . . . 
                 # first write the 'Ref Pout' and 'Pwr Variation' by using the 'center of band' condition                
                 if ncn in vramp2pout and rn_vramp in vramp2pout[ ncn ] :
    
                    refpwr  =  vramp2pout[ ncn ][ rn_vramp ]
                    self.data[ ref_pout_cn ][rn]  =  refpwr
                    
#                     if  self.data['linenumber'][rn] == 8573:
#                         print '###############################'
#                         print 'linenumber' , self.data['linenumber'][rn]
#                         print 'ncn', ncn
#                         print 'rn_vramp', rn_vramp
#                         print 'refpwr',   refpwr
#                         print 'ref_pout_cn' , ref_pout_cn
#                         print '###############################'
                        
                        
    #                self.data['nominal conditions rn'][rn] = vramp2rn[ncn][ rn_vramp ]
                    if rn_pout != None:
                        self.data[ pwr_var_cn ][rn] = rn_pout - refpwr
    
    
                 # second write the 'Ref2 Pout' and 'Pwr2 Variation' by using the 'at frequency' condition
                 if n2cn in vramp2pout and \
                      rn_vramp in vramp2pout[n2cn ] :
    
                    refpwr  =  vramp2pout[ n2cn ][ rn_vramp ]
                    self.data[ref2_pout_cn][rn]  =  refpwr
    #                self.data['nominal2 conditions rn'][rn] = vramp2rn[n2cn][ rn_vramp ]
                    if rn_pout != None:
                        self.data[pwr2_var_cn][rn] = rn_pout - refpwr
                        
                        # if for this record the 'Ref2 Pout' exists but the 'Ref Pout' does not exist
                        # then this must be a measurement made with a spot frequency vramp search
                        # in this case provide a fall back 'Ref Pout' value by copying it from the 'Ref2 Pout'
                        if self.data[ref_pout_cn][rn] == None:
                            self.data[ref_pout_cn][rn]  =  refpwr
                            self.data[pwr_var_cn][rn] = rn_pout - refpwr
                 # . . . . . . . . . . . . 
               
               
                
                 ncn   = self.data['nominal conditions ref'][rn]
                 n2cn  = self.data['nominal2 conditions ref'][rn]
    
                 # Second Go
                 # . . . . . . . . . . . . 
                 # first write the 'Ref Pout' and 'Pwr Variation' by using the 'center of band' condition                
                 if ncn in vramp2pout and \
                      rn_vramp in vramp2pout[ ncn ] :
    
                    refpwr  =  vramp2pout[ ncn ][ rn_vramp ]
                    self.data['Ref Pout(dBm)'][rn]  =  refpwr
                    self.data['nominal conditions rn'][rn] = vramp2rn[ncn][ rn_vramp ]
                    if rn_pout != None:
                        self.data['Pwr Variation(dB)'][rn] = rn_pout - refpwr
    
    
                 # second write the 'Ref2 Pout' and 'Pwr2 Variation' by using the 'at frequency' condition
                 if n2cn in vramp2pout and \
                      rn_vramp in vramp2pout[n2cn ] :
    
                    refpwr  =  vramp2pout[ n2cn ][ rn_vramp ]
                    self.data['Ref2 Pout(dBm)'][rn]  =  refpwr
                    self.data['nominal2 conditions rn'][rn] = vramp2rn[n2cn][ rn_vramp ]
                    if rn_pout != None:
                        self.data['Pwr2 Variation(dB)'][rn] = rn_pout - refpwr
                        
                        # if for this record the 'Ref2 Pout' exists but the 'Ref Pout' does not exist
                        # then this must be a measurement made with a spot frequency vramp search
                        # in this case provide a fall back 'Ref Pout' value by copying it from the 'Ref2 Pout'
                        if self.data['Ref Pout(dBm)'][rn] == None:
                            self.data['Ref Pout(dBm)'][rn]  =  refpwr
                            self.data['Pwr Variation(dB)'][rn] = rn_pout - refpwr
                 # . . . . . . . . . . . . 
                


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
            if self.data['TestName'][rn] == 'VRamp Search' and  self.data[ 'Vramp Voltage' ][rn] not in UNDEFS:
                tpwr = '%0.1f' % self.data['TRP Target Power(dBm)'][rn]
                if tpwr[-1] == '0': tpwr = tpwr[:-2]
#                print "(add_rated_power_values)  self.data[ 'Vramp Voltage' ][rn] = <%s>" %  self.data[ 'Vramp Voltage' ][rn]
                tvramp =  '%0.3f' % float( self.data[ 'Vramp Voltage' ][rn])
                subband = self.data['Sub-band'][rn]
                for cn in  ['nominal conditions ref', 'nominal2 conditions ref']:
                
                   # For the 'nominal conditions ref' make sure that the frequency for this vramp search is
                   # at the center of band, ie ignore this vramp search if it is not run at the center of band frequency 
                   # (However for 'nominal2 conditions ref' is an at frequecny condition so don't skip it, we want 
                   # it added to the rated_power_cond regardless)
                   if cn == 'nominal conditions ref':
#                       print '(add_rated_power_values) rn=%s, linenumber=%s subband=%s self.sub_band_list[:4]=%s' % \
#                             (rn, self.data['linenumber'][rn], subband, self.sub_band_list[:4] )
                      try:
                         idx = self.sub_band_list[:4].index( subband )
                      except: 
                         continue
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
                                self.data['@Prated'][rn] = float(tpwr)
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


      col_list = [ 'Vramp Voltage' , 'Process' , 'Vbat(Volt)', 'Temp(C)', 'HB_LB', 'Freq(MHz)', 'VSWR', 'Phase(degree)', 'Pwr In(dBm)', 'Regmap' ]

      # make sure all the columns exist and they are the correct length
      for col in col_list:
         self.add_new_column( col )

      if 'TestName' in self.data  and  'Vramp Voltage' in self.data and ('Output Power & Efficiency' in  self.data['TestName']):
        pae_count = 0
        pae_cond_count = 0
        vramp2pout = {}
        self.add_new_column( 'Pout(dBm)' )
        for rn in range( rn_start, rn_finish ):
           if ( self.data['TestName'][rn] == 'Output Power & Efficiency' )  and self.data['Vramp Voltage'][rn] != None :
              pae_count += 1
              ls = []
              try:
                  for col in col_list:
                      ls.append( str(self.data[ col ][rn]) )
#                 ls=[ str(self.data['Vramp Voltage'  ][rn]) ,
#                      str(self.data['Process'        ][rn]) ,
#                      str(self.data['Vbat(Volt)'     ][rn]) ,
#                      str(self.data['Temp(C)'        ][rn]) ,
#                      str(self.data['HB_LB'          ][rn]) ,
#                      str(self.data['Freq(MHz)'      ][rn]) ,
#                      str(self.data['VSWR'           ][rn]) ,
#                      str(self.data['Phase(degree)'  ][rn]) ,
#                      str(self.data['Pwr In(dBm)'    ][rn]) ,
#                      str(self.data['Segments'       ][rn]) ,
#                      str(self.data['Regmap'         ][rn]) , ]

                  cond = ' '.join( ls )

                  vramp2pout[ cond ] = self.data['Pout(dBm)'][rn]
                  pae_cond_count +=1
              except Exception:
                pass

#        print '(add_vramp2pout_data)   pae_count = %d    pae_cond_count = %d' % (pae_count, pae_cond_count)

        vramp_count = 0
        vramp_cond_count = 0

        for rn in range( rn_start, rn_finish ):
           if ( self.data['TestName'][rn] != 'Output Power & Efficiency' ) and self.data['Vramp Voltage'][rn] != None :
              vramp_count += 1
              ls = []
              try:
                  for col in col_list:
                      ls.append( str(self.data[ col ][rn]) )
#               try:
#                 ls=[ str(self.data['Vramp Voltage'  ][rn]) ,
#                      str(self.data['Process'        ][rn]) ,
#                      str(self.data['Vbat(Volt)'     ][rn]) ,
#                      str(self.data['Temp(C)'        ][rn]) ,
#                      str(self.data['HB_LB'          ][rn]) ,
#                      str(self.data['Freq(MHz)'      ][rn]) ,
#                      str(self.data['VSWR'           ][rn]) ,
#                      str(self.data['Phase(degree)'  ][rn]) ,
#                      str(self.data['Pwr In(dBm)'    ][rn]) ,
#                      str(self.data['Segments'       ][rn]) ,
#                      str(self.data['Regmap'         ][rn]) , ]

                  cond = ' '.join( ls )

                  if cond in vramp2pout:
                     pout = vramp2pout[ cond ]
                     # Only store a new value if there the Pout(dBm) value is empty,
                     # we don't want to overwrite any existing Pout(dBm) data
                     if not isinstance( self.data['Pout(dBm)'][rn], types.FloatType ):
                         self.data['Pout(dBm)'][rn] = pout
                     vramp_cond_count += 1
 #                  print '   ', cond
              except Exception:
                pass

#        print '(add_vramp2pout_data)  pae_cond_count = %d  vramp_count = %d    vramp_cond_count = %d' % (pae_cond_count, vramp_count, vramp_cond_count)


    ###################################################################
    def add_noise_offset_data( self, rn_start, rn_finish ):
      ''' Adds 'RX_Noise_Band1' and RX_Noise_Band2 data.
      
      Parameters:
           rn_start:    starting record to scan
           rn_finish:   last record to scan
      Updates:          self.data[ 'RxNoiseBand1(dBm/Hz)', self.data[ 'RxNoiseBand2(dBm/Hz)]
      Note:             RxNoiseBand1(dBm/Hz) is 190MHz offset from Fundamental
                        RxNoiseBand2(dBm/Hz) is 80MHz offset from Fundamental'''

      band1Freqs = range( 1920, 1981, 1)
      band2Freqs = range( 1850, 1911, 1)
      if 'TestName' in self.data and 'RxFreq(MHz)' in self.data  and  'RxNoise(dBm/Hz)' in self.data and 'Test Freq(MHz)' in self.data:
        self.add_new_column( 'RxNoiseBand1(dBm/Hz)' )
        self.add_new_column( 'RxNoiseBand2(dBm/Hz)' )
        for rn in range( rn_start, rn_finish ):
           if (( self.data['TestName'][rn] == 'Noise' )  and ( self.data['Test Freq(MHz)'][rn]  in band1Freqs)):
              if ( self.data['RxFreq(MHz)'][rn] == (self.data['Test Freq(MHz)'][rn] + 190)):  
                self.data['RxNoiseBand1(dBm/Hz)'][rn] = self.data['RxNoise(dBm/Hz)'][rn]
           if (( self.data['TestName'][rn] == 'Noise' )  and ( self.data['Test Freq(MHz)'][rn]  in band2Freqs)):
              if ( self.data['RxFreq(MHz)'][rn] == (self.data['Test Freq(MHz)'][rn] + 80)):  
                self.data['RxNoiseBand2(dBm/Hz)'][rn] = self.data['RxNoise(dBm/Hz)'][rn]   
              



    ###################################################################

    def add_spurious_data( self, freq_thres=None, rn_start=None, rn_finish=None, remove_harmonics=True ):

        ''' Create new Spurious data columns containing the orginal spur data with data points
        closer than some frequency threshold removed
        
        Parameters:
            freq_thres:   Spurs which are Spur-Freq < freq_thres are removed
            rn_start:     Starting record number to scan
            rn_finish:    Last record number to scan
            remove_harmonics : if True (default) it will remove all ahamonic spurs.  
        Returns:          None
        Updates:          self.data[ 'Amplitude of Spur, no harmonic xxxMHz (dBm)'] '''


        # hamonic amplitude
        # we want to null out
        
        # any spurs that are really harmonics.
        # we do this by redefining the amplitude of the spur as a low value

        #self.harmonic_freq_thresh = 50.0   # (MHz)  # any frequency which is less than this value from a harmoinic is categorized as a harmonic and will be nulled



        if freq_thres != None:
            if remove_harmonics == True:
                cname = 'Amplitude of Spur, no harmonic %sMHz (dBm)' % freq_thres
            else:
                cname = 'Amplitude of Spur, including harmonics %sMHz (dBm)' % freq_thres
            
        else:
            cname = 'Amplitude of Spur, no harmonic {spur_filter_table}MHz (dBm)'
            
            

        self.add_new_column( cname )

        num_spurtests = 0
        num_spurs_det = 0


        for rn in range( rn_start, rn_finish ):

           num_spurtests += 1

           if self.data['TestName'][rn] == 'Spurious (ETSI full)'    or \
              self.data['TestName'][rn] == 'Spurious (ETSI reduced)' or \
              self.data['TestName'][rn] == 'Spurious (SA Mode)'      or \
              self.data['TestName'][rn] == 'Spurious Emissions'      or \
              self.data['TestName'][rn] == 'Spurious Emissions WCDMA' or \
              self.data['TestName'][rn] == 'Spurious (quick)'            :
              freq = self.data['Freq(MHz)'][rn]


              f = self.data['Frequency of Spur (MHz)'][rn]
              amp = self.data['Amplitude of Spur (dBm)'][rn]


              if amp not in UNDEFS and f not in UNDEFS:

                  harmonic_float  = float(f)/float(freq)
                  harmonic_int    = int( harmonic_float + 0.5 )
                  harmonic_dist   = harmonic_float - harmonic_int
                  freq_dist       = freq * abs( harmonic_dist )
                    

                  if freq_thres == None:
                     freq_thres_tmp = self.get_spur_freq_thres_from_table( freq, harmonic_int )
                  else:
                     freq_thres_tmp = freq_thres

                  num_spurs_det +=1
                  
                  # If we want to include the harmonic spurs then
                  # make the freq_thres_tmp impossibly small (ie -1)
                  # so that all values of freq_dist will be output
                  if remove_harmonics==False and harmonic_int > 1:
                       freq_thres_tmp = -1 
                    
                  # Any spur that is less than the filter distance away from 
                  # the fundamental is nulled out (or less than the filter 
                  # distance away from a harmonic) 
                  if freq_dist < freq_thres_tmp:
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





            if self.spur_file_missing > 0:
                return 0

            file2open = 'spur_freq_threshold_table.csv'


            try:
                f = open(file2open, "rb")              # don't forget the 'b'!
            except  Exception:
                print "*** ERROR *** cannot read spur filter file: '%s'" % file2open
                self.spur_file_missing += 1
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
    def add_pypat_record( self, values_dict ):
        '''Adds a new record to the self.data array. The data typically
        comes from pypat. Parameter values_dict is a dictioanry of
        data that is to be added. The keys are the columnnames and the
        data is the values'''
        
        self.datacount +=1
        
        # add the record number data
        cn = 'record_num'
        self.add_new_column( cn )
        self.data[ cn ][self.datacount-1] = self.datacount
        
        # add the value_dict data to the self.data array
        for cn in values_dict:
            cn1 = re.sub('^\d+\|', '', cn)    # Get rid of the ouput prefix e.g. '000|Pout(dBm)' -> 'Pout(dBm)'
            self.add_new_column( cn1 )
            val = values_dict[ cn ]
            if val != None and val != '':
                try:    val = float(val)          # Turn the value from a string into a float value if we can
                except: pass
                self.data[ cn1 ][self.datacount-1] = val
                
                
        # fill the unused columns with None to pad them out.
        for name in self.data :
          num_appends = self.datacount - len(self.data[name])
          for i in range(num_appends):
              self.data[ name ].append( None )
              

        # add all the missing column data that is expected for an atr type logfile
        self.logfile_type = 'atr'
        self.add_missing_columns( self.datacount-1, self.datacount )

    ###################################################################
    def draw_pypat_record( self, values_dict ):

        pass



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

      full_filespec = '%s' % full_filespec
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

           x = re.search( r'(\d\.\d+)v_ramp.txt$', full_filespec, re.I )
           if x :
                n = x.groups()
                return '', '', '', n[0], full_filespec, ''

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
          name:        Name of filter to change, if the name ends with '_pattern'
                    then this denotes a regular expression pattern match.
                    Then real column name is actually the name with the '_pattern'
                    suffix removed. 
          values:      Value to change filter (optional)
          tolerance:   currently ignored (optional)
       Reads:
       Updates:        self.filter_conditions  , self.values_dict[name] self.values_dict_count[name]
       Returns:        None'''




      # if values is None then remove the filter name completely
      # else look for name in existing filter_conditions and change the entry for the filter
      # if the name does not exist add it to the end.


      pattern_match = False
      # Error if the name of this filter is not in self.data
      if name not in self.data:
         
         # look for a pattern match filter
         if name[-8:] == '_pattern' and name[:-8] in self.data:
             pattern_match = True
             name = name[:-8]
         else:
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


         # Look for an interplote filter condition
         # A condition value which is a number starting with an '&' character
        
      if isinstance( values, types.StringTypes):
         atvals = re.findall('&-?[\d\.]*\d+', values)
         if len(atvals) == 1:
            atval = atvals[0]
            oper = '&'
#            values = float( re.findall('[\d\.]+', atval)[0] )
            values = atval
         elif len(atvals) > 1:
            values = atvals
            oper = '&'


      if isinstance( values, types.StringTypes) and \
           re.search(r'\.\.', values) and \
           not pattern_match:

         if oper == '=':
             val1 = re.sub(r'\.\.\S+','',values)
             val2 = re.sub(r'\S+\.\.','',values)
    
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




      if pattern_match:
        oper = 'REGEX'


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


      # If the filter name happens to be in the values_dict
      # look to see if all or none of the filter values are in the values_dict
      # if they are all in the values_dict then every compare with this filter 
      # will match (oper = 1). If none of the filter values are in the values 
      # dict we know every compare with this filiter will not match (oper = 0).
      # We do this to speed up processing, there is no pont in comparing values
      # on a record by record basis if we know ahead of time that the value
      # does not exist at all, or it is the only value in the list 

      comp0 = 0
      comp1 = 0

      if name in self.values_dict and not pattern_match:


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


         if not comp0 and comp1:     # only values that match are in the filter
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

      # Go through all the exiting filters looking for this filter name
      # if found then replace the existing filter with the new one (new_c) we just made
      for i in range(len(self.filter_conditions)):
         c = self.filter_conditions[i]
         if c[0] == name:
            self.filter_conditions[ i ] = new_c

            return

      # If the filter was not found, add the new filter onto the end of the 
      # filter list
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


#        # Split the data based on the standart parameter sweep names, this will ensure that there will be separate lines for each condition
#        # Except if we are doing Frequency of Spur plot then don't split it up!
#        if xname != 'Frequency of Spur (MHz)' and xname[:5] != '[Time]' :
# 
#          for sc in self.value_dict_names:
#             if sc != xname and sc in self.series_seperated_list and sc != 'Vramp Voltage':
#                # for wcdma linear products we will be sweeping pwr in and ploting pout on the x-axis, 
#                # in this case we don't want to split the series on pwer in
# #               if sc == 'Pwr In(dBm)' and xname in ['Pout(dBm)', 'Ref Pout(dBm)', 'Ref2 Pout(dBm)', 'Pout_pm(dBm)', 'EVM Total Pout over a slot (dBm)', 'ACLR Pout(dBm)' ] : continue
#                if sc not in series_conditions_done:
#                    series_conditions_done[ sc ] = 'done'
#                    full_series_conditions.append( sc )
# 
#        print '(select_data) full_series_conditions = ', full_series_conditions


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
         
         # if we have a filter on a phase then make sure we wrap properly
         if re.search('phase|phi', name.lower()):
            phase_name = True
         else:
            phase_name = False
         
         filter_conditions_match_count[ name ] = 0
         self.values_filtered_dict[ name ] = []
#        selected_count[ name ] = 0
#        selected_values[ name ] = []


       for fc in self.filter_conditions:

         name = fc[0]
         if name not in self.data:
            continue
         oper = fc[1]
         tolerance = None
         filter_values = fc[2:]

         # if we are filtering on a Pout value, these are likely to be imprecise, so widen the limits by 0.1 dB to make sure we accept close values.
#         if re.search( r'Pout', name , re.I) or re.search( r'VSWR', name , re.I):
         if re.search( r'Pout', name , re.I):
             tolerance = 0.2
         else:
             tolerance = None    # a tolerance of None means that the compare_value default tolerance is used (probably set to 0.001)



         if oper == '1' or oper == '&':
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
                            toler = 3
                        else:
                            toler = tolerance    # a tolerance of None means that the compare_value default tolerance is used (probably set to 0.001)
                       
                        if self.compare_values( val_rn , val_filter, toler, oper, val_filter2, phase_name=phase_name ):     # look out for this! - the filter 'value' might not be of the same type as the data dictionary value.
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
       first_rn = None
       self.values_selected_dict = {}
       for fc in self.filter_conditions:
                 vdn = fc[0]
                 if vdn not in self.data:
                    continue
                 self.values_selected_dict[ vdn ] = []
                 for rn in range( self.datacount ):
                     if rn_good_list[ rn ]:
                         valrn = self.data[vdn][rn]
                         if valrn not in self.values_selected_dict[ vdn ]:
                              self.values_selected_dict[ vdn ].append( valrn )
                         if first_rn == None:
                            first_rn = rn

       # Supplement the values_selected_dict with all the values from the values_dict_names list
       for vdn in self.value_dict_names:
            if vdn not in self.values_selected_dict and vdn in self.data:
                 self.values_selected_dict[ vdn ] = []
                 for rn in range( self.datacount ):
                     if rn_good_list[ rn ]:
                         valrn = self.data[vdn][rn]
                         if valrn not in self.values_selected_dict[ vdn ]:
                              self.values_selected_dict[ vdn ].append( valrn )
                         if first_rn == None:
                            first_rn = rn

       #### DETERMINE HOW TO SPLIT THE DATA INTO DIFFERENT SERIES ####
       # Split the data based on the standard parameter sweep names, this will 
       # ensure that there will be separate lines for each condition
       # The parameter names that will be used to split the data are
       # put into list
       #                  full_series_conditions
       # 
       # If graphs are being plotted as a series of points examine this list
       # and remove any parameters that are unintentionaly splitting the data 
       
       # Except if we are doing Frequency of Spur plot then don't split it up!
       if 1 or xname != 'Frequency of Spur (MHz)' and xname[:5] != '[Time]' :


         # Find out if the selected data is using a linear type modulation
         if first_rn == None: first_rn = 0

         test_type = 'saturated'

         if 'Modulation' in self.data and  len(self.data['Modulation']) > first_rn and \
            ( self.data['Modulation'][first_rn] in ['wcdma','hsupa','hsdpa','edge','tdscdma', 'EDGE-Option', 'GSM_1M0833333', None] or \
              self.data['Modulation'][first_rn][0] == 'E' or  \
              self.data['Modulation'][first_rn][0] == 'T'):
              
            test_type = 'linear'
         else:
            test_type = 'saturated'

         # If we have an Pin type xaxis assume 'linear', linear type operation is more likely if the xaxis is Pin
         if (xname == 'Pwr In(dBm)' or re.search('^Pin',xname)):
             test_type = 'linear'
            
         # Any ACP type test must be linear type test
         for nam in xynames:
            if len(nam) >= 3 and nam[:3] in ['ACP','ACL'] or re.search('gain',nam.lower()):
              test_type = 'linear'

         if self.force_line_on.get()== False:

             for sc in self.value_dict_names:
                if sc not in xynames and sc in self.series_seperated_list and sc != 'Vramp Voltage':
                   if re.search('_phi$|phase', xname.lower()) and (sc == 'Freq(MHz)' or re.search('contour',self.plottype)):
                       continue
                   if  (sc == 'Pwr In(dBm)' or re.search('^Pin',sc)) and (( test_type == 'linear') or self.plottype in ['contour']) :
                       continue
                   if  (sc == 'Pwr In(dBm)' or re.search('^Pin',sc)) and xynames[0][:4] == 'Pout' :
                       continue
                   if self.logfile_type != 'atr':
                       continue
                   if sc not in series_conditions_done:
                       if sc in self.data:
                          series_conditions_done[ sc ] = 'done'
                          full_series_conditions.append( sc )
         else:
             # Split only if the data differs on color or lines style

             n  = self.color_series.get()
             if n.strip() != '':
                 full_series_conditions.append( n )

             n = self.line_series.get()
             if n.strip() != '':
                 full_series_conditions.append( n )

       print '(select_data) full_series_conditions = ', full_series_conditions


       #--------------------------------------------------------------------
       # Go through the series_conditions looking for unique set of values.
       # If unique then create a new series, if not then add to the existing series
       #--------------------------------------------------------------------

       full_series_conditions_no_xynames = []
       sc = None
       for sc in full_series_conditions:
           if sc not in xynames:
              full_series_conditions_no_xynames.append( sc )

       full_series_conditions =   full_series_conditions_no_xynames

       if 1 or sc and sc in self.data:
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



#       self.create_values_dict()



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
              if name not in self.data:
                  continue
              oper = fc[1]
              tolerance = None
              values = fc[2:]
              count = 0


              if re.search( r'Pout', name , re.I):
                 tolerance = 0.3
              else:
                 tolerance = None





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
#                  print '(select_data)', values 
                  if len(values) > 0:
                      vl = [ values[0] ]
                      tol = tolerance
                  else:
                      vl = []

              # go through the each filters extreme values, looking to see if this value exists in the  values_selected_dict
              # and add an '*' character to mark each filter which is not fully included

              sel_lst =  self.values_selected_dict[ name ]
              sel_lst.sort()

              fcs_str = ''

              for v in vl:


                  # ok - for Pout filters which are less than 10dB set the tolerance to 2dB so that we don't filter out data that is close enough
                 if   re.search( r'Pout', name , re.I): 
                    if    v < 10:
                        toler = 3
                    elif  v < 15:
                        toler = 1
                    else:
                        toler = tol
                 else:
                    toler = tol    # a tolerance of None means that the compare_value default tolerance is used (probably set to 0.001)

                 full_condition_selected = False
                 for vs in sel_lst:
                    if self.compare_values(vs, v, toler) :
                       full_condition_selected = True
                       break
                 if full_condition_selected == False and oper != 'REGEX':
                       fcs_str = fcs_str + '*'
                       full_condition_selected_str = full_condition_selected_str + '*'
                       break

#              print '(select_data)   self.values_filtered_dict[ %s ] = %s' % ( name,  self.values_filtered_dict[ name ] )
#              print '(select_data)   self.values_selected_dict[ %s ] = %s' % ( name,  self.values_selected_dict[ name ] )




              if len( sel_lst ) < 22:
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

            tstr = "  .(select_data) Split data series based on columns %s" % (series_unique_names)
            print tstr


#        print '\n(select_data_new) series_data    '           , series_data
#        print '\n(select_data_new) series_values    '           , series_values
#        print '\n(select_data_new) series_unique_name_value_str', series_unique_name_value_str
#        print '\n(select_data_new) series_unique_values'        , series_unique_values
#        print '\n(select_data_new) series_unique_names         ', series_unique_names


       return series_data, series_values, series_unique_name_value_str, series_unique_values, series_unique_names, full_condition_selected_str



    ########################################################################
    def compare_values( self, val_data , val_filter, tolerance=None, oper='=', val_filter2=None, phase_name=False ):
         '''Compares a value against a limit.
         
         Parameter:
             val_data:     Data value to compare
             val_filter:   Filter Value to compare with val_data
             tolerance:    Comparison is made with +/- tolerance.  If None tolerance = 0.001
             oper:         Comparison operator '=', '<', '>','<<', 'REGEX' 
             val2_filter:  If operator '<<' then comparison used 
         Returns:
             1:   comparison true
             0:   comparison false
         '''


         # simple equate, with all oper values, if val1 == val2 then it is a match
         if val_data == val_filter: return 1

         if tolerance == None:      tolerance = 0.000001


         # if the val aint the same then try a little harder
         try:

           if oper == '=' and abs( val_data - val_filter ) <= tolerance :
              return 1

           if oper == '<' and val_data <= (val_filter + tolerance) :
              return 1

           if oper == '>' and val_data >= (val_filter - tolerance) :
              return 1

           if oper == '<<' and not phase_name and (val_filter - tolerance) <= val_data <= (val_filter2 + tolerance) :
              return 1

           # When comparing phases if one filter is positive and the other negative we must make sure that
           # the phase is properly wrapped
           if oper == '<<' and phase_name:
              # if one phase is positive and the other phase is negative
              # add 360 to all the values to unwrap the phase and compare properly
              if val_filter<0: val_filter += 360.0
              if val_filter2<0: val_filter2 += 360.0
              if val_data<0:   val_data += 360.0
              if  (min(val_filter,val_filter2) - tolerance) <= val_data <= (max(val_filter,val_filter2) + tolerance) :
                  return 1

           if oper == 'REGEX':
                if re.search( val_filter, val_data ):
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



         # dont try to split up phase data series data
         if re.search('_phi$|Phase', xname ) : return [s[:]]


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

           if isinstance(d, types.StringTypes):
                continue
           try:
              d = float( d )
           except Exception:
              if d != '[]':
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


         if imax != None and imin != None and do_split :  
            rng = float(self.data[xname][imax])  -  float(self.data[xname][imin])
         else:
            # if the imax and imin are still defined as None it means there was no data in the series
            # in which case just return the original series
            return [s[:]]

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
        if v not in UNDEFS:
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
      for i in lip:
          if i != None:
            i_r = i * 2*pi/360.0
          else:
            i_r = None  
          lop.append( i_r )
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
             pwr = self.data[ 'Adj Pwr Out(dBm)' ][rn]                                                                                            #            xi            x , y,  refst,reffn
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


      if 'TestName' in self.data  and  'Vramp Voltage' in self.data and  ('Output Power & Efficiency' in  self.data['TestName']) :

        vramp2pout = {}
        self.add_new_column( 'Adj Pwr Out(dBm)' )


        if not 'AM-AM' in self.data: return

        self.add_new_column( 'Pout(dBm)'  )

        for rn in range( rn_start, rn_finish ):

           # find the power and efficiency tests
           if ( self.data['TestName'][rn] == 'Output Power & Efficiency' or self.data['TestName'][rn] == 'Power_and_Eff' ) and self.data['Vramp Voltage'][rn] != None and self.data['Adj Pwr Out(dBm)'][rn] != None :


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
             if ( self.data['TestName'][rn] == 'Output Power & Efficiency') :
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
    def add_slope( self, x_col_name, y_col_name, op_col_name, rn_start=0, rn_finish=None, offset = 0  ):
         '''Creates a new column name 'op_col_name' by calculating the slope of 'y_col_name' wrt ''x_col_name'
         
         Parameters:
              x_col_name:      x column name from the self.data array
              y_col_name:      y column name from the self.data array
              op_col_name:     New Column name to create for the slope
              rn_start:        Starting record number  (default 0)
              rn_finish:       Last record number (default self.datacount)
              offset:          Adds and offset to the slope. -1 offset will normalise the slope to 0 
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
         if x_col_name in [ 'Pout(dBm)', 'Adj Pwr Out(dBm)', 'PSA Pwr Out(dBm)', 'Vramp(V)' ] :
            ignore_col_lst = [ 'Step', 'Vramp Voltage', x_col_name, y_col_name ]
         else:
            ignore_col_lst = [ x_col_name, y_col_name ]



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



#          for i in range(20):
#              print '(add_slope)', cond_list[ i ]

         slope_calc_count = 0
         slope_try_count = 0
         
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

#               print '               m4',  rn_finish,  [ x , y ], rns, rni, done_list[ rni ], cond_list[ rni ], condi, slope_try_count
#               print y_m1, x_m1, y_m2, x_m2




               if x == None or y == None:
                    done_list[ rni ] = True
                    continue

               slope = None

               slope_try_count += 1  


               try:
                 dy =  y - y_m2
                 dx =  x - x_m2         
                 slope = dy/dx

                 if rni > rns:    # dont write the first one as it would be less than rn_start
                    self.data[ op_col_name ][rni_m1]  = slope + offset
                    slope_calc_count += 1



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
         if ( ( self.data['TestName'][rn] == 'Output Power & Efficiency') and
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

#     def plot_polar_data( self, xynames,  logfilename ):
#       '''Polar Graph Plotting function  - obsolete
#       '''
# 
# 
#       print '...plotting polar data for:' , xynames[2]
# 
#       self.xydata = self.get_data( xynames,  conditions=[] )
# 
#       rootfilename = re.sub(r'\..*', '', logfilename)
# 
# 
#       vswr_lst = self.get_unique_vals( self.xydata[3] )
# 
#       xrad = self.deg2rad(self.xydata[0])
# 
# 
# 
# 
# 
#       idx_min, idx_max = self.get_minmax_idx( self.xydata[2] )
# 
#       xmin, xmax = self.get_minmax( xrad )
#       ymin, ymax = self.get_minmax( self.xydata[1] )
# 
#       # set the resolution of the color grid
#       #n = 800
#       n = 100
#       xser = linspace(xmin,xmax, n)
#       yser = linspace(ymin,ymax, n)
#       X,Y = meshgrid( xser, yser )
#       # generate interpolated Z values for the fine XY grid, (griddata requires matplotlib v0.98)
#       Z = matplotlib.mlab.griddata(xrad, self.xydata[1], self.xydata[2],  X, Y)
# 
#       figure()
#       ax1 = subplot(111, polar=True)
# 
#      # pcolormesh( X, Y, Z, alpha=0.2)   # pcolormesh runs a lot faster than pcolor for the polar plot!
# 
#       # Make the color coding sensible for binary alert register values
#       if re.search(r'Alert Reg', xynames[2]) :
#         vmx = 1.0; vmn = 0.0
#       else:
#         vmx = None ; vmn = None
# 
#       pcolormesh( X, Y, Z, alpha=0.2, vmin=vmn,vmax=vmx )   # pcolormesh runs a lot faster than pcolor for the polar plot!
# 
#       # make sure the Magnitude axis is set to 1.0 (which is VSWR of infinity) to match Smith Chart scaling
#       axis([0,1,0,1])
# 
#       #grid()
#       # make the magnitude labels invisible (it clutters the plot, and we are more interested in vswr)
#       setp( ax1.get_yticklabels(), visible=False)
# 
#       colorbar()
# 
# 
# 
# 
# 
#       title( xynames[2] )
# 
# 
# 
#       if not re.search(r'Alert Reg', xynames[2]) :
# 
#         # draw contour lines
#         ax3 = contour(X, Y, Z )
#         clabel(ax3)
# 
#         # annotate the min and max values
#         self.annotate_polar_val(   'max = %0.3fv' % self.xydata[2][idx_max]   , idx_max, 0.2, 0.9 )
#         self.annotate_polar_val(   'min = %0.3fv' % self.xydata[2][idx_min]   , idx_min, 0.6, 0.9 )
# 
#       # draw dots where each loadpull sample was measured
#       scatter(xrad, self.xydata[1],marker='^',s=1)
#       axis([0,1,0,1])
# 
# 
#       y = 0.25
#       for txt in [ 'Band = %s' % ( self.data['HB_LB'][-1] ) ,
#                    'Seg  = %s' % ( self.data['Segments'][-1] ) ,
# 
#                    'Freq = %dMHz' % ( self.data['Freq(MHz)'][-1] ) ,
#                    'Vbat  = %sv' % ( self.data['Vbat(Volt)'][-1] ) ,
#                    'VAM  = %sv' % ( self.data['Vramp Voltage'][-1] ) ,
#                    'VSWR = %s' % vswr_lst ,
#                    '',
#                    'Date = %s %s' % ( self.data['Date'][-1],self.data['Time'][-1]) ,
#                    'Vramp Rel = %s' % ( self.data['Vramp Release'][-1] ) ,
#                    'Logfile = %s' % ( self.data['logfilename'][-1]) , ]:
#          self.annotate_figure( txt, 0.02 , y )
#          y = y - 0.025
# 
# 
# 
#       #legend(shadow=True,pad = 0.1,labelsep = 0.001, prop = matplotlib.font_manager.FontProperties(size='smaller') )
#       name = rootfilename + ' ' + xynames[2]
#       name = re.sub('[<>]', '_', name )
#       print '...saving png file: ', name
#       savefig( name )


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
    def get_line_style_indexes( self, series_unique_values, series_unique_names, listcount, listlen, ycount, ylen, interp_idx ):

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
              cidx += interp_idx
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


    def get_selected_plot_data( self, selected_record_list, xynames, xysel=None ):
          '''Weed out any bad data from the selected data. Bad data is any data that is not numeric
              Bad data is converted to None
              String data is converted into index data obtained by looking up 
              the value in the value_dict[name]
              
          Parameter:
              selected_record_list:    List of record to select from
              xynames:                 List of x and y column names
              xysel:                   Index to select which axis to use from xynames 
          Returns:
              dlst:                    List of data values, with non numeric data removed (or set to None)
              rnlst:                   List of records, with non numeric data removed (or set to None)     
          '''


          if xysel != None:
              xyname = xynames[ xysel ]
          else:
              xyname = xynames

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


                  if xyv == None or xyv == '':
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
                  elif isinstance(xyv, types.StringTypes):
                      # If the xyv value is a string then look it up in the
                      # values_dict and convert the string into it into and index
                      # number
                      try:
                        dlst.append( self.values_dict[ xyname ].index(xyv) )
                        got_data = True
                      except ValueError, KeyError:
                        dlst.append( None )
                      rnlst.append( rn )
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
    def get_selected_rn_list(self, xynames=None, conditions=None):
        '''Using the current x and y axes and the current filter conditions, get
        a full list of record numbers
        '''

        ynames = []
        xnames = []
        if xynames == None:
            self.xynames = []
            for n  in self.xnames_ordered:
                self.xynames.append( n )
                xnames.append(n)
            for n  in self.ynames_ordered:
                self.xynames.append( n )
                ynames.append(n)
            for n  in self.y2names_ordered:
                self.xynames.append( n )
                y2names.append(n)
            xynames = self.xynames

        if len(xynames) < 2:
            return []

        series_data, series_values, sunvs, suv, sun, fcss = self.select_data( conditions, xynames )

        rnsd = []
        axes_names = xnames[:]
        axes_names.extend(ynames)
        for sda in series_data:
            for rn in sda:
                # Check that there are valid x and y values for all the axes for this record
                good_data = True
                for ax in axes_names:
                    if self.data[ax][rn] in UNDEFS:
                        good_data = False
                        break
                if good_data:
                    rnsd.append( rn )
        rnsd.sort()

        return rnsd


    #####################################################################################
    def plot_graph_data( self, xynames,  conditions=None, savefile=None, titletxt=None, enable_golden_unit_data=True ):
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
        
        self.plottype = None
        xyd = self.plot_graph_data_core( 'xy_scatter_plot', xynames,  conditions, savefile, titletxt)
        return xyd

    ###################################################################
#     def plot_polar_data( self, xynames,  conditions, savefile=None, titletxt=None):
#         xyd = self.plot_graph_data_core( 'polar_contour_plot', xynames,  conditions, savefile, titletxt)
#         return xyd

    ###################################################################
    def plot_interactive_graph( self ):
        self.interactive = True


#         # get the x and y axes from the selections in the X and Y axis tabs
#         self.xynames = []
#         xysel_lst =  self.xnames.curselection()
#         
#         
#         for i in xysel_lst:
#            n = self.xnames.get( int(i) )
#            print '    X=', i, n
#            self.xynames.append( n )
# 
#         xysel_lst =  self.ynames.curselection()
#         for i in xysel_lst:
#            n = self.ynames.get( int(i) )
#            self.xynames.append( n )
# #           self.graph_title.set('')

        self.plottype = None

        self.xynames = []
        for n  in self.xnames_ordered:
            self.xynames.append( n )
        for n  in self.ynames_ordered:
            self.xynames.append( n )
        for n  in self.y2names_ordered:
            self.xynames.append( n )



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
    def interpolate_scatter_data(self,x,y,rnl,filter,interp_idx):
        '''function that intertolates the y data based on the filter value.
        In general the x,y,rnl lists will be made up values where the same x value
        is repeated two or more times. This function will split the x,y,rnl lists
        into sub-lists which have the same x values. Then sub-list is taken and an
        single interpolated Y value is computed from the filter interpolation value.
        A new reduced set of x,y,rnl lists is returned, containing the interpolated Y values

        :param x:
        :param y:
        :param rnl:
        :param f:
        :return x:    List of unique X values taken from the original list
        :return y:    Interolated Y value list which match the X values
        :return rnl:  RN (record_number) list, numbers are the first rn's from the X list
        '''

        xret = []
        yret = []
        rnlret = []

        sl_x = []
        xp = None  #previous x value

        #if filter[1] == '&':
        interpolation_name = filter[0]
        interpolation_val  = filter[2+interp_idx]
        interpolation_val = interpolation_val[1:]
        interpolation_val = float(interpolation_val)

        yil = []
        fil = []
        sd = []
        for idx in range(len(x)+1):
            # Calculate the interpolated value every time we see the x value change, or at the very end of the list
            if idx == len(x) or (xp and x[idx] != xp):
                # compare function which sorts the list into ascending x values
                self.sort_column = 0
                sd.sort( self.compare_columns )
                yn = []
                xn = []
                for tl in sd:
                  xn.append( tl[0] )
                  yn.append( tl[1] )
                yval = np.interp(interpolation_val,xn,yn )
                xret.append(xp)
                yret.append(yval)
                rnlret.append(rni)
                sd = []
            if idx < len(x):
                rni = rnl[idx]                           # record number
                xi = x[idx]                              # x value
                yi = y[idx]                              # y value
                fi =  self.data[interpolation_name][rni] # filter value
                sd.append( [fi, yi, rni] )
            xp = xi


        return xret, yret, rnlret


    ###################################################################
    def plot_graph_data_core( self, plottype, xynames,  conditions, savefile=None, titletxt=None):
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


      line = None
      
      

      

      # find out if we have multiple xaxis selected, if so then we will be doing a contour map of some sort
      xysel_lst =  self.xnames.curselection()
      if len(xysel_lst) == 2:
         plottype = 'contour'


      xynames_orig = xynames[:]

      if self.plottype != None:
        plottype = self.plottype

      xynames = list(xynames)

      # Look to see if the contour map is a polar plot, this is when
      #    one xaxis is a phase, the other xaxis is a magnitude or a vswr 
      if plottype == 'contour': 
        theta_idx = None
        r_idx = None
        r_i = None
        for i in [0,1]:
        
            if re.search( 'phase|_phi', xynames[i].lower()):
                theta_idx = xynames.index(  xynames[i] )
                
            # if the one of the xaxies is a vswr then replace it with a magnitude
            if re.search( 'magnitude|mag|vswr', xynames[i].lower()) :                  
                r_idx     = xynames.index(  xynames[i] )
                r_i = i
                
#        print 'r_idx and theta_idx =', r_idx, theta_idx
                
        if r_idx!=None and theta_idx!=None:    
            plottype = 'polar_contour_plot'
            if re.search( 'VSWR', xynames[r_i]):
               xynames[r_i] =  'Magnitude'
            if re.search('_vswr$',xynames[r_i]):
               xynames[r_i] =  re.sub( '_vswr', '_mag', xynames[r_i] )


#        print xynames[ :2 ], theta_idx, r_idx , plottype


      if self.polar_phase_plot.get():
          plottype = 'polar_phase_plot'
          
          

      self.plottype = plottype

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
            self.fig.clear()
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
            self.fig.clear()
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

      if plottype in ['polar_contour_plot','contour'] :  ynames_str =  ' '.join( xynames[2:] )
      else                                    :  ynames_str =  ' '.join( xynames[1:] )

      # Find out the start of the y2 axes
      y2count_start = None
      y2names_str = ""
      if len(self.y2names_ordered) > 0 and plottype in ['xy_scatter_plot']:
         y2count_start = len(xynames_orig) - len(self.y2names_ordered)
         y2names_str = ' '.join(xynames_orig[y2count_start:])
         ynames_str = ' '.join(xynames_orig[1:y2count_start])

      subdir = ''
      if savefile != None:

          # If the savefile is a list then the list items are the file and directory
          if type(savefile) == types.TupleType or type(savefile) == types.ListType :

                # If the first item is a list then 
                # [ [ '/subdir' ] , savefile ]
                if type(savefile[0]) == types.ListType:
                   subdir   = savefile[0][1:]
                   savefile = savefile[1]
                else:   # [ savefile, subdir ]
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

        if len(self.y2names_ordered) > 0:
            self.ax2 = self.ax.twinx()

        self.fig.subplots_adjust( left=self.plot_position[0], right=self.plot_position[1], top=self.plot_position[2], bottom=self.plot_position[3]  )


      elif plottype in [  'polar_contour_plot',  'polar_phase_plot'] :
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

      elif plottype ==  'contour':
        self.fig.clf()
        self.numcontours = self.update_entry_box( self.numcontours, self.wnumcontours)
        self.ax = self.fig.add_subplot(1,1,1, alpha=0.5, polar=False)
        self.fig.subplots_adjust( left=self.plot_position[0], right=self.plot_position[1], top=self.plot_position[2], bottom=self.plot_position[3]  )

      if re.search( 'polar', plottype):         
          self.draw_smith_chart_grid()
          # Set the grid properties
          setp( self.ax.get_yticklabels(), visible=False)
          self.ax.set_rmax(1.0)
          grid(False)

      if 1:
        self.xaxis_limits = self.get_axis_limits( self.xlimits, self.xscl_min.get(), self.xscl_max.get() )
        self.yaxis_limits = self.get_axis_limits( self.ylimits, self.yscl_min.get(), self.yscl_max.get() )
        if y2names_str != '':
            self.y2axis_limits = self.get_axis_limits( self.y2limits, self.y2scl_min.get(), self.y2scl_max.get() )

        if series_data != []:

          xname = xynames[0]
          yname = xynames[1]


          
          
          self.ax.set_title( titletxt )
          if self.logfile_type == 'atr' or self.plottype in ['polar_phase_plot']:
              self.graph_title.set( titletxt )
          else:
              self.graph_title.set( self.logfilebasename )


          if plottype not in [ 'polar_contour_plot', 'polar_phase_plot']  :
              xlab = self.ax.set_xlabel( xynames[0] )
              if plottype != 'contour' :      
                  ylab = self.ax.set_ylabel( ynames_str )
              else:
                  ylab = self.ax.set_ylabel( xynames[1] )

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
          xinterpvals = []
          yvals  = []
          rnvals = []
          snvals = []
          cvals  = []
          dvals  = []
          lblvals  = []
          found_interpolation = False


          if  plottype in ['polar_contour_plot','contour']: ycount_start = 2
          else:                                             ycount_start = 1


          # Re-write the gui xy axes selection if it is empty based on the xynames list
          # but we have to be careful when we have multiple X axes for contour and polar plots
          self.xnames_ordered = []
          self.ynames_ordered = []
          self.y2names_ordered = []
          for i,nam in enumerate(xynames_orig):
              if i < ycount_start:
                  self.xnames_ordered.append(nam)
              elif y2count_start==None or i < y2count_start:
                  self.ynames_ordered.append(nam)
              else:
                  self.y2names_ordered.append(nam)

          self.select_columns(self.xaxis_col_list,  self.xnames_ordered )
          self.select_columns(self.yaxis_col_list,  self.ynames_ordered )
          self.select_columns(self.y2axis_col_list,  self.y2names_ordered )
          self.wupdate_filter_cond_list()

          yidx = 0
          for ycount in range( ycount_start, len(xynames)):

              sn  = ''
              sn_full = ''
              rn  = 0

              xpol   = []
              x2pol  = []
              xinterppol = []
              ypol   = []
              rnpol  = []

              for sd,sn,sv in zip(series_data,series_unique_name_value_str, series_unique_values):

                    #--------------------------------------------------------
                    # even though we have tried to split the data up into separate series, it is possible that
                    # the data contains repeated tests with the same conditions. If this happens we should try to
                    # further split the data into further series for plotting.

                    # To detect whether the series needs to be split we need to look at the X values and see if they
                    # progress in a more or less monotonic fashion.
                    #--------------------------------------------------------

                    sd_new = self.get_sub_series( xynames[0], sd )

                    if plottype == 'contour':
                        sd_new = [sd]

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

                    # If there is an interpolated filter condition (ie '&') then check to see if there is are multiple vinterpolated values
                    # If we have multiple interpolated values then loop through each one of them
                    interp_len = 1
                    if plottype == 'xy_scatter_plot':
                         for f in self.filter_conditions:
                              if f[1] == '&':
                                 interp_len = len(f)-2
                                 break

                    for interp_idx in range(interp_len):
                       sdi = 0
                       for sdai in range(len(sd_new)):
                          sda = sd_new[sdai]

                          if sda == [] :
                               continue

                          trn = sda[0]
        #                 print sdai, self.data['linenumber'][trn]  , self.data['//T#'][trn], self.data['TestName'][trn],  self.data['Test Freq(MHz)'][trn], sda

                          x2 = None
                          if plottype == 'polar_phase_plot' :
                             x,rnl = self.get_selected_plot_data( sda, xynames, 0 )
                             x     = self.deg2rad(x)
                          elif plottype == 'contour' :
                             x,rnl = self.get_selected_plot_data( sda, xynames, 0 )
                             x2,rnl = self.get_selected_plot_data( sda, xynames, 1 )
                          elif plottype == 'polar_contour_plot' :
                             x,rnl = self.get_selected_plot_data( sda, xynames, theta_idx )
                             x     = self.deg2rad(x)
                             x2,rnl = self.get_selected_plot_data( sda, xynames, r_idx )
                          else:
                             x,rnl = self.get_selected_plot_data( sda, xynames, 0 )
                          if x == []: continue
                          y,rnl = self.get_selected_plot_data( sda, xynames, ycount )
                          if y == []: continue


        #                  print 'FILTER_CONDITIONS', self.filter_conditions
        #                  print '%s %s lens : x=%s  x2=%s  y=%s' % ( plottype, xynames, len(x) ,len(x2), len(y))
                          # Look for an interpolated  filter condition (with an '@' operator)
                          found_interpolation = False
                          xinterp = []
                          for f in self.filter_conditions:
                            if f[1] == '&':
                                interpolation_name = f[0]
                                oper = f[1]
                                interpolation_val  = f[2]
                                interpolation_val = re.sub('^&','',interpolation_val)
                                interpolation_val = float(interpolation_val)
                                found_interpolation = True
                                # Get the plotdata values for this interpolated name
                                xinterp, dummy_rnl = self.get_selected_plot_data( sda, interpolation_name )
                                break

                          if plottype not in  ['polar_contour_plot','contour','polar_phase_plot'] and( xynames[0] == 'Frequency of Spur (MHz)' or self.sort_data_on.get() ) :
                              x, y, rnl = self.sort_selected_data( x, y, rnl )

                          # If we plotting a regular scatter plot and we also have an intepolation filter (ie '&') then
                          # We need to take all the data that has the same X values and interpolate a single Y value
                          # that matches the intepolation filter value.
                          if plottype == 'xy_scatter_plot':
                                for f in self.filter_conditions:
                                    if f[1] == '&':
                                        x,y,rnl = self.interpolate_scatter_data(x,y,rnl,f,interp_idx)
                                        break



                          # Adjust the lengths of the x,y lists so they are the same length
                          xlen = len(x)
                          ylen = len(y)
                          if xlen < ylen:
                             y = y[:xlen]
                             rnl = rnl[:xlen]
                          if xlen > ylen:
                             x = x[:ylen]
                             if  plottype in ['polar_contour_plot','contour'] :
                                x2 = x2[:ylen]
                                if xinterp != []:
                                    xinterp = xinterp[:ylen]
                             rnl = rnl[:ylen]

                          if len(x) == 0 : continue

                          c, d, c_idx, d_idx = self.get_line_style_indexes( sv, series_unique_names, sdai, len(sd_new), yidx, len(xynames[1:]), interp_idx )

                          y2_color = 'k'
                          if ycount==y2count_start and y2names_str != "":
                            y2lab = self.ax2.set_ylabel( y2names_str )
                            y2_color = c
                            self.ax2.tick_params( 'y', colors = y2_color )

                          sdi +=1

                          if sn == '' :
                             if len(xynames)>2:
                                 sn = xynames[ycount]   # make sure there is a label string
                             if found_interpolation:
                                     sn += ' %s:%s ' % ( f[0], f[2+interp_idx][1:])
                             sn_full = sn
                          else:

                             # truncate the sn name so that it only contains the color and line series values
                             sn = ''
                             if found_interpolation:
                                 sn = ' %s:%s ' % ( f[0], f[2+interp_idx][1:])
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
                                  if len(xynames)>2:
                                      sn = xynames[ycount] + sn
                             sn_full = sn

                          if not found_interpolation and sdi > 1  :     sn = ''    # stop multiple repeated series names from cluttering up the legend


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

                          if plottype in [ 'xy_scatter_plot', 'polar_phase_plot'] :
                              if y2count_start == None or ycount < y2count_start:
                                  line, = self.ax.plot( x, y, color=c, dashes=d, label=sn, marker=marker, linewidth=linewidth, picker=5 )
                              else:
                                  line, = self.ax2.plot( x, y, color=c, dashes=d, label=sn, marker=marker, linewidth=linewidth, picker=5 )
                              lbl =  line._label
                              done_a_plot = True
                          else:
                              line = None
                              lbl = 'PoLaR'
                              if plottype == 'contour':
                                lbl = 'CoNtOuR'

                              # concatantate all the x, x2, and y data to form a single list

                              xpol.extend( x )
                              x2pol.extend( x2 )
                              xinterppol.extend( xinterp )
                              ypol.extend( y )
                              rnpol.extend( rnl )

                          #
                          ###############################################################################

                          xvals.append(x)
                          x2vals.append(x2)
                          xinterpvals.append(xinterp)
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



              # If we have interpolated data we need to Grid the data first and
              # interoplate. 
              if found_interpolation == True and plottype != 'xy_scatter_plot':
                    xmin,  xmax   = self.get_minmax( xpol  )
                    x2min, x2max  = self.get_minmax( x2pol )   
                    x2interpmin, x2interpmax  = self.get_minmax( xinterppol )
#                     print '- - X  ', len(xpol), xmin, xmax
#                     print '- - X2 ', len(x2pol), x2min, x2max
#                     print '- - XI ', len(xinterppol), x2interpmin, x2interpmax
#                     print '- - y  ', len(ypol)



                    GX, GX2, GXI = np.mgrid[xmin:xmax:50j, x2min:x2max:50j, interpolation_val:interpolation_val:1j]

                    try:
                        from scipy.interpolate import griddata
                    except ImportError:
                        print "*** ERROR *** scipy import failed! Please install 'scipy' python module on this computer"
                        
                        
                    Y = griddata((xpol,x2pol,xinterppol), ypol, (GX, GX2, GXI), method='linear')
                    YS = Y[:,:,0]
                    XS = GX[:,:,0]
                    X2S  = GX2[:,:,0]
#                    print GX.shape, GX2.shape, GXI.shape, Y.shape, XS.shape, X2S.shape, YS.shape
                    
                    
                    xpol = GX.reshape( 50*50 )
                    x2pol = GX2.reshape( 50*50 )
                    ypol = YS.reshape( 50*50 )
                    
                  #                             theta  R     Y    theta, R
#                    Z = matplotlib.mlab.griddata(xpol, x2pol, ypol,   X,   X2 )
                    
                    

              ########################################################################
              ## Plot the polar contour plot
              ####
              if plottype == 'polar_contour_plot':




                  # Due to bugs in matplotlib we first need to do a couple of cleaning up things with the data

                  # In order for the polar contour plot to work
                  # the phase data needs to sweep from 0 to 2*pi
                  # but the data usually is from -pi to +pi. Therefore
                  # we need to add 2*pi to the negative xpol angle data
                  # to make the negative angles all positive
                  for xi in range(len(xpol)):
                       theta = xpol[xi]
                       
                       # if the phase is negative
                       # add enogh full cycles to make it positive
                       if theta < 0:
                       # get the number of full cycles
                         t  = theta/(2*nu.pi)
                         nt = int( -t ) +1
                         theta = theta + nt*2*nu.pi                              
                         xpol[xi] = theta                    
                       


                  # Shift the data so that the series data for a given VSWR starts with the minimum phase
                                    # (or 359.9 to be more precise)
                  xpl    = []
                  x2pl   = []
                  ypl    = []
                  xplss  = []
                  x2plss = []
                  yplss  = []
                  x2plz  = None
                  xpmin  = None
                  xpmin_ssidx  = None
                  yp0 = None
                  done_yp0 = False
                  
                  ssidx = 0
                  for xp, x2p, yp in zip(xpol,x2pol,ypol):
                  
                    # Save the 1:1 y value, we shall be copying it to create separate values for each of the phase angles.
                    if yp0 == None and x2p < 0.01:
                        yp0 = yp

                  
                    # At this point ignore the 1:1 data as there is only one value and it needs to be copied once for each of the phase angles
                    if x2p < 0.01: continue
#                    print 'data=', xp, x2p, yp, ssidx, xpmin_ssidx, xpmin
                  
                    # If the VSWR value is the same as the previous one, then look to see if this is the minimum phase (x2)
                    # if so record the index
                    if x2plz == None or x2p == x2plz:
                        if xpmin_ssidx == None or xp <  xpmin:
                            xpmin     = xp
                            xpmin_ssidx = ssidx
                            
                            
                    else:  # the vswr (x2p)
                        # copy the subseries to the output, starting at the minimum position
                        
                        if not done_yp0:
                            done_yp0 = True
                            for j in range(ssidx): 
                                jidx = (j + xpmin_ssidx) % ssidx
                                xpl.append(xplss[jidx])
                                x2pl.append(0.0)
                                ypl.append(yp0)
                        
                        for j in range(ssidx): 
                            jidx = (j + xpmin_ssidx) % ssidx
                            xpl.append(xplss[jidx])
                            x2pl.append(x2plss[jidx])
                            ypl.append(yplss[jidx])
                        # initialize for the next subseries
                        xplss  = []
                        x2plss = []
                        yplss  = []
                        x2plz   = xp
                        xpmin  = None
                        xpmin_idx  = None
                        ssidx = 0
                        
                    xplss.append(xp)
                    x2plss.append(x2p)
                    yplss.append(yp)
                    
                    ssidx += 1
                    
                    
                  # copy the final subseries to the output, starting at the minimum position
                  for j in range(ssidx): 
                      jidx = (j + xpmin_ssidx) % ssidx
                      xpl.append(xplss[jidx])
                      x2pl.append(x2plss[jidx])
                      ypl.append(yplss[jidx])
                    
    
                  # copy the data back to original working lists
                  xpol = xpl
                  x2pol = x2pl
                  ypol = ypl
                       

                
                  # To show the contours joining up all the way round
                  # we need to duplicate the first data value at the end
                  #
                  
                    
#                   
#                   # copy the data back to original working lists
#                   xpol = xpl
#                   x2pol = x2pl
#                   ypol = ypl
                  xplz = xpol[0]
                  for xp, x2p, yp in zip(xpol,x2pol,ypol):
                       if ( -0.01 <= (xp - xplz) < 0.1):
                            xpl.append( xp  + 2*nu.pi*(359.9/360.) )
#                            xpl.append( xp - 0.0001 )
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

                  # Do the contour polar plot
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
                  
                  if not found_interpolation:
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
                      if name in [ 'VSWR', 'Pout(dBm)', 'Pwr In(dBm)'] : continue
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

              elif plottype == 'contour':


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
#                   
#                       # Get the min and max values for the data
#                       idx_min, idx_max = self.get_minmax_idx( y )
#                       xmin,  xmax   = self.get_minmax( x  )    # theta
#                       x2min, x2max  = self.get_minmax( x2 )    # r
#                       # Create a Mesh grid to provide a continuous surface on which
#                       # the contours can be calcuulated on.
#                       # Set the resolution of the grid
                  
                  
                  if len(x) <= 2 or len(x2) <= 2:
                    print '*** ERROR *** X axis and X2 axis data does not have enough data points, check that you have filtered the correct data'                  
                  
#                       n = 50
#                       xser  = linspace(xmin,xmax, n)
#                       x2ser = linspace(x2min,x2max, n)
#                       X,X2  = meshgrid(xser,x2ser)

                  
                  X,X2  = meshgrid(xser,x2ser)
#                  print 'X,X2=', X, X2
#                  print 'x,x2=', xpol, x2pol
                  Z = matplotlib.mlab.griddata(xpol, x2pol, ypol,   X,   X2 )
              
                  self.ax.grid(False)
                  # Do the contour polar plot
                  if self.contourfill.get():
                      CS = self.ax.contourf( X, X2, Z, int(self.numcontours)  )
                      colorbar( CS, ax=None, aspect=100, shrink=0.9, pad=0.07, fraction=0.03, orientation='horizontal' )
                  else:
                      CS = self.ax.contour( X, X2, Z , int(self.numcontours), alpha=1.0, colors=c, linestyles='solid', linewidths=linewidth, label=sn )
                      self.ax.clabel(CS, fontsize=9, inline=1)

                  # draw dots where the actual data points lie
                  if not found_interpolation:
                      self.ax.grid(False)
                      self.ax.scatter(xpol, x2pol,marker=marker,s=5, alpha=0.5)
                      self.ax.grid(False)

                  if self.xaxis_limits == []:
                         self.xaxis_limits = [xmin, xmax]
                  if self.yaxis_limits == []:
                         self.yaxis_limits = [x2min, x2max]

#                  print 'XYNAMES = ', xynames

                  lbl =  'CoNtOuR'
                  done_a_plot = True




          # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
          # - - - finished plotting the data  - - - - - - - - - - - - - - - - -
          # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

          if self.spec_limits != None:
              self.add_spec_limits( 'red', [100,0] )

          if self.legend_location and done_a_plot and plottype not in ['polar_contour_plot']:

                lines, labels = self.ax.get_legend_handles_labels()
                if y2names_str != "":
                    lines2, labels2 = self.ax2.get_legend_handles_labels()
                    lines = lines + lines2
                    labels = labels + labels2

                try:
                    self.legend = self.ax.legend(lines, labels, shadow = True,
                                            labelspacing = 0.001,
#                                            labelsep     = 0.001,
                                            loc  = self.legend_location,
                                            prop = matplotlib.font_manager.FontProperties(size='smaller'),
#                                            pad  = 0.01 )
                                            borderpad  = 0.01 )
                except:
                    self.legend = self.ax.legend(lines, labels, shadow = True,
#                                            labelspacing = 0.001,
                                            labelsep     = 0.001,
                                            loc  = self.legend_location,
                                            prop = matplotlib.font_manager.FontProperties(size='smaller'),
                                            pad  = 0.01 )
#                                            borderpad  = 0.01 )


                if plottype not in ['contour']:
                    self.legend.set_picker(self.my_legend_picker)





          #--------------------------------------------------------
          # Write out the conditions on the plot on the top RHS
          # note we dont print out variables which are swept,
          # (instead the swept vairaibles  will be written out in the graph legend)
          #--------------------------------------------------------

          if self.draw_conditions.get() and self.conditions_location :
 
              clist = [ ''                     ,
                            'Part Number (Chip ID)',
                            'Chip Model'           ,
                            'Serial Number'        ,
                            'EventID'              ,
                            ''                     ,
                            'ControlSignals'       ,
                            'ControlMode'          ,
                            'Sub-Band'             ,
                            'Freq(MHz)'            ,
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
                            'Register'             ,
                            'Vramp Release'        ,
                            'logfilename'          ,
                            'logfiledir'           ,
                            'csvfilename'            ]
              for n in self.data:
                            if re.match('REG_|VMUX|Bitfield_',n):
                                clist.append(n)
 
 
              line_sel = self.line_series.get()
              color_sel = self.color_series.get()
 
              y = self.conditions_location[1]
              self.annotate_figure( 'CONDITIONS:' , self.conditions_location[0]  , y )
              y = y - 0.018
              for name in clist:
              
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
                     
                     if self.list2str( values_list ).strip() == '':
                        continue
                                  
                     if tname == color_sel:
                        color_line_str = ' (Color)'
                     elif tname == line_sel:
                        color_line_str = ' (Line)'
                     else:
                        color_line_str = ''
                        
                     txt = '%s = %s%s' % ( tname, self.list2str( values_list ), color_line_str )
                 
                     
                 
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
              print "*** ERROR *** (plot_graph_data_core) There is no numerical data for one or more of the axes '%s', please choose axes which contain numerical data, or select different filter values" % xynames




          ## ADD CODE TO LOOP ROUND MULTIPLE LIMITS SO THAT WE GET ZOOMED IN VERSIONS OF THE PLOTS IN ADDITION

          # Set the axes limits, the limits were calculated earlier on


          if plottype != ['polar_contour_plot', 'polar_phase_plot']:
          
#               print 'LIMITS X:', self.xaxis_limits 
#               print 'LIMITS Y:', self.yaxis_limits 
          
              if self.xaxis_limits != [] :
                  self.ax.set_xlim( ( self.xaxis_limits[0] , self.xaxis_limits[1] ) )

              if self.yaxis_limits != [] :
                  self.ax.set_ylim( ( self.yaxis_limits[0] , self.yaxis_limits[1] ) )


              self.ax.grid()

              if y2names_str != "":
                  if self.y2axis_limits != [] :
                      self.ax2.set_ylim( ( self.y2axis_limits[0] , self.y2axis_limits[1] ) )
                  self.ax2.grid( color = y2_color )



              # Set the number of grid lines

              g = self.xgrd_step.get()
              lim = self.ax.set_xlim()
              try:  self.ax.set_xticks( self.get_grid_ticks( lim, self.xgrid, g ) )
              except: pass


              g = self.ygrd_step.get()
              lim = self.ax.set_ylim()
              self.ax.set_yticks( self.get_grid_ticks( lim, self.ygrid, g ) )

              if y2names_str != "":
                  g = self.y2grd_step.get()
                  lim = self.ax2.set_ylim()
                  self.ax2.set_yticks( self.get_grid_ticks( lim, self.y2grid, g ) )


          if plottype in ['polar_phase_plot', 'polar_contour_plot']:

                  # Set the grid properties
                  setp( self.ax.get_yticklabels(), visible=False)
                  self.ax.set_rmax(1.0)
                  grid(False)








          #--------------------------------------------------------
          # save the plot file
          #--------------------------------------------------------

          self.savefilename = savefilename


          if savefile != None:


              savefilename = self.clean_savefilename( savefilename )

              self.save_plot_count = int( self.save_plot_count)
              if int( self.save_plot_count) >= 0:
                self.save_plot_count = self.save_plot_count + 1
                savefilename = 'P%03d_%s' % ( self.save_plot_count, savefilename )


              reldirname = ''
              dirname = ''
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
              if 0 and subdir != '' and subdir != None and isinstance( subdir , types.ListType ) and len( subdir ) >=2 and subdir[1] != None:

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
             
             xmin, xmax = xlim()
             # if we have no list get the current xaxis
             
             if type( lines ) != types.ListType:   
                pl[0] = [ [ xmin , lines ], [xmax , lines ] ]
#              elif len(lines) == 2:   # a two element list means two separate lines
#                 pl[0] = [ [ xmin , lines[0] ], [xmax , lines[0]] , [xmax , lines[1] ], [xmin , lines[1] ] ]

             if pl[0][0][0]  == None or pl[0][1][0]  == None : continue
             if pl[0][0][1]  == None or pl[0][1][1]  == None : continue

             lim = array( pl[0] )
             x = lim[ : , 0  ]
             y = lim[ : , 1  ]


             if len(pl) > 2 and pl[2] != None :  thickness = pl[2]
             else:                               thickness = 1
             if len(pl) > 3 and pl[3] != None :  color     = pl[3]
             if len(pl) > 4 and pl[4] != None :  dashes    = pl[4]


             colors = color.split()
             if len(colors) > 1:
                 color_line = colors[0]
                 color_text = colors[1]
             else:
                 color_line = color
                 color_text = color


             self.ax.plot( x , y , color_line, dashes=dashes, linewidth=thickness, zorder=0)

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
                if len(colors)>1:
                    yofs = 0
                else:
                    yofs = 3
                annotate( text, xy=(txtx, txty),  color=color_text, textcoords='offset points', xytext=(0,yofs),
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
         if not isnan(xi) and not isnan(x2i) and not isnan(yi) and yi != 'None' :

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

    def loop( self, tkmainloop=True ):
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


        if self.exit_after_processing == True:
            sys.exit()

        self.run_mode = 'gui'
        print '  ...waiting for user input'
        self.status.set( 'waiting for user input' )



        if tkmainloop==True:
            Tk.mainloop()


###################################################################################################
    def get_cond_value_list_from_rn( self, rn, cond_list ):
        '''Make up a list with all the conditions values found for a record number 
        in the self.data array. The conditions used are those defined by cond_list
            '''
        tstr = ''
        cond_vals = []
        for col in cond_list:
            cond_vals.append( self.data[col][rn] )

        return cond_vals



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

            if col[0] == '@' or \
               col in ignore_lst or \
               (col in self.values_dict_count and len( self.values_dict_count[col]) <= 1 ) \
               or col not in self.data: 
                   continue
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

        for col in [ 'linenumber' , 'Pout(dBm)' ]:   
            if col in self.data:
               tstr = tstr + '%s=%s \n' % ( col, self.truncate_value( self.data[col][rn]) )


#        self.dbg_print( '(get_cond_str_from_rn)  start' , 11708, 'Ref Pout(dBm)' )
#        self.dbg_print( '(get_cond_str_from_rn)       ' , 11708, 'Ref2 Pout(dBm)' )
#        self.dbg_print( '(get_cond_str_from_rn)       ' , 11708, 'NC_Reference' )



        for col in self.value_dict_names:

            

#          print  '(get_cond_str_from_rn)', col, len( self.values_dict_count[ col ] )

          if col not in [ 'HB_LB' ] and col in self.values_dict_count:
             if len( self.values_dict_count[col] ) > 1:
                if col[0] == '@' : continue
                
#                print '(get_cond_str_from_rn)            ', rn, col ,  self.data[col][rn]
                
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
            if hasattr(gca(),'texts') and len(x.texts) > 0:
                del gca().texts[-1]

        # if no object is selected and we have a control key pressed then delete the last text
        if self.sel_object == None and self.key == 'control':
            x = gca()
            del gca().texts[-1]


        self.sel_object = None


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

               if 1 or hasattr(gca(),'texts') and len(x.texts) > 0:
                   try:
                       gca().texts[-1].xytext = [ event.xdata, event.ydata ]
                   except IndexError:
                       pass

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

              thisline = self.series_picked[ self.pick_count ]
              grps =  re.search( r'Line2D\((.*)\)', str(thisline) )
              if grps and self.pick_count_total > 0:
                self.pick_count = (self.pick_count) % self.pick_count_total
                self.pick_data = True
                sn = grps.groups()[0]
                xdata = thisline.get_xdata()
                ydata = thisline.get_ydata()
                ind = self.series_picked_ind[ self.pick_count ]

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

                   if re.search( 'polar', self.plottype) and not self.polar_annotate_full.get():
                      txt = self.get_polar_marker_impedance_txt( sn, ind, rn ) 
                      bbox=dict(boxstyle="round", fc="0.95", ec=None )
                   else:
                      bbox=None

                   self.sel_object = self.ax.annotate( txt, xy=xy_data,
                       horizontalalignment='left', verticalalignment='bottom', fontsize=10,
                       xytext=xy_text, textcoords='data',
    #                  xytext=(-50, 30), textcoords='offset points',
    #                   arrowprops=dict(arrowstyle="->"),
                       bbox=bbox,
                       arrowprops=dict(facecolor=arrow_color, edgecolor=arrow_color, shrink=0.02,width=0.1,headwidth=4, alpha=1),

                   )
   #            		print 'get_position = ',  self.sel_object.get_position()
                   self.pick_min_x = self.sel_object.get_position()[0]
                   self.pick_min_y = self.sel_object.get_position()[1]


                   self.canvas.draw()
   #               print '(on_button_press) self.sel_object', dir( self.sel_object )
                   self.pick_count = (self.pick_count + 1) % self.pick_count_total

                except Exception, err:
                   self.pick_data = False
                   print "(on_button_press) Line not found in self.plot_rndata dict,  clicked on line '%s', ind=%s\n  List of lines available:" % ( str(sn), str(ind) )
                   for s in self.plot_rndata:
                      print "                    '%s'"% s

                   print traceback.format_exc()


# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
    #############################################################################
    def get_polar_marker_impedance_txt( self, sn, ind, rn ):
        '''Create a text string containing the impedance information, similar to the
         ADS smith chart marker info

         Assume that X is the phase, and Y is the magnitude
         Report the following 
            freq, 
            mag, phase, vswr
            impedance R + jX
        '''
        
        txt = ''  
        rad = self.plot_xdata[ sn ][ ind ]
        mag = self.plot_ydata[ sn ][ ind ]
        
        freq = self.data['Freq(MHz)'][rn]
        deg = (rad * 360)/(2*pi)
        if deg > 180:     deg = deg - 360
        if deg < -180:    deg = deg + 360
        
        vswr = mag2vswr( mag )
        
        r,i  = magphase2ri( mag , deg )
        reff = complex( r,i ) 
        Z = 50 * (1 + reff)/(1 - reff)
        
        txt = 'Freq=%0.1fMHz\nMag = %0.6f / %0.1f deg\nZ = %+0.2f %+0.2fj (ohm)\nVSWR = %0.1f : 1' % \
        (freq, mag, deg, Z.real, Z.imag, vswr)
        
        
        return txt
        
        
    ###############################################################################
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

#                print '(on_pick) ind = ', type( ind ), len(ind), ind
                if type( ind ) != types.IntType:
                   for i  in ind:

#                     print '(on_pick)', self.mouse_pick_xdata, xinc, self.mouse_pick_ydata, yinc, xdata[i], ydata[i]
                     xd = xdata[i]
                     # for polar plots , negative phases need to be turned into +ve values 
                     if re.search('polar',self.plottype) and xdata[i] < 0: 
                         xd += 2*nu.pi
                     xdiff = abs( self.mouse_pick_xdata - xd )
                     ydiff = abs( self.mouse_pick_ydata - ydata[i] )
                     if (xdiff < xinc and ydiff < yinc):
#                      if (self.mouse_pick_xdata-xinc  < xdata[i] < self.mouse_pick_xdata+xinc ) and \
#                         (self.mouse_pick_ydata-yinc  < ydata[i] < self.mouse_pick_ydata+yinc ) :

                        self.series_picked[ self.pick_count_total ] = thisline
                        self.series_picked_ind[ self.pick_count_total ] = i
                        self.pick_count_total += 1
#                        print'(on_pick)X: mouse_pos=[%s:%s]  series_picked=%s ind=%s data=[%s:%s]'% (self.mouse_pick_xdata, self.mouse_pick_ydata, thisline, i, xdata[i], ydata[i])
                     else:
#                        print'(on_pick) . mouse_pos=[%s:%s]  series_picked=%s ind=%s data=[%s:%s]'% (self.mouse_pick_xdata, self.mouse_pick_ydata, thisline, i, xdata[i], ydata[i])
                        pass
                else:
                     i = ind
                     xdiff = abs( self.mouse_pick_xdata - xdata[i] )
                     ydiff = abs( self.mouse_pick_ydata - ydata[i] )
                     if xdiff < xinc and ydiff < yinc:

#                     if (self.mouse_pick_xdata-xinc  < xdata[i] < self.mouse_pick_xdata+xinc ) and \
#                        (self.mouse_pick_ydata-yinc  < ydata[i] < self.mouse_pick_ydata+yinc ) :

                        self.series_picked[ self.pick_count_total ] = thisline
                        self.series_picked_ind[ self.pick_count_total ] = i
                        self.pick_count_total += 1
#                        print'(on_pick)single X: mouse_pos=[%s:%s]  series_picked=%s ind=%s data=[%s:%s]'% (self.mouse_pick_xdata, self.mouse_pick_ydata, thisline, i, xdata[i], ydata[i])
                     else:
#                        print'(on_pick)single . mouse_pos=[%s:%s]  series_picked=%s ind=%s data=[%s:%s]'% (self.mouse_pick_xdata, self.mouse_pick_ydata, thisline, i, xdata[i], ydata[i])
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
#         runscript = Tix.Button(butfrm, name='script',  text='Run\nScript', width=5, height=2, command=self.run_script)                 .grid( column=3, row=0, sticky=Tix.SW)
  #        quit    = Tix.Button(butfrm, name='quit',    text='Quit',          width=5, height=2, command=sys.exit    )                  .grid( column=3, row=0, sticky=Tix.S)
          quit    = Tix.Button(butfrm, name='quit',    text='Quit',          width=5, height=2, command=self.doDestroy    )                  .grid( column=4, row=0, sticky=Tix.S)







          #----------------------------------------
          # Create a 'notebook' area with multiple tabs to allow the user to load log files and specify the x and y axes, and filter conditions
          #----------------------------------------

          self.nb = Tix.NoteBook(ctlfrm, name='nb', ipadx=0, ipady=0)
          self.nb['bg'] = 'gray'
          #nb.nbframe['backpagecolor'] = 'gray'

          tb = self.nb.add('load',   label="Load",   underline=0)
          self.nb.add('xaxis',  label="Xaxis",  underline=0)
          self.nb.add('yaxis',  label="Yaxis",  underline=0)
          self.nb.add('y2axis',  label="Y2axis",  underline=1)
          self.nb.add('filter', label="Filter", underline=0)
#          self.nb.add('distortion',  label="Dist",  underline=0)
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

          loadfile     = Tix.Button(tabfrm, name='loadfile',  text='Load\nPypat\nLogfiles',   width=10, command=self.wloadfile  ) .grid( column=1, row=1 )
          loadadb      = Tix.Button(tabfrm, name='loadadb',    text='Load\nConstellation\nDB Results', width=10, command=self.atlantis_load_db )    .grid( column=2, row=1 )
          loaddb       = Tix.Button(tabfrm, name='loaddb',    text='Load\nMercury\nDB Results', width=10, command=self.mercury_load_db )    .grid( column=3, row=1 )
          Tk.Label(  tabfrm, text='')                   .grid( row=2, column=2 )
          loadgip      = Tix.Button(tabfrm, name='loadgip',   text='Load and Run\nARG Script',     width=10, command=self.get_arg_user_inputs_dialog  )   .grid( column=2, row=3 )

          
          self.vramp_search_enable     = Tk.IntVar(master=tabfrm)
#          Tk.Label( tabfrm, text='Use Vramp Search\nto calc\nRef Pout(dBm):' )                     .grid( column=3, row=4,sticky=Tk.S)
#          Tk.Checkbutton( tabfrm, name='vramp_search_entry' , variable=self.vramp_search_enable )  .grid( column=3, row=3,sticky=Tk.N)
          self.vramp_search_enable.set( True )
          

          Tk.Label(  tabfrm, text='')                   .grid( row=4, column=2 )

          self.script_file_name  = Tk.StringVar(master=tabfrm)
          Tk.Entry(  tabfrm, name='script_file_name' , width=20, justify='right', textvariable=self.script_file_name )                      .grid( row=5, column=1, columnspan=2, sticky=Tk.W+Tk.E)

          Tk.Button( tabfrm, name='browse_button', text="Browse",  width=7, command=self.browse_script_file) .grid( row=5, column=3 )

          runscript = Tix.Button(tabfrm, name='script',  text='Run\nScript', width=5, height=2, command=self.run_script)   .grid( column=2, row=6,)

          script_file_name = self.read_pygram_config( 'script_file_name' )
          self.script_file_name.set( script_file_name )

          Tk.Label(  tabfrm, text='')                   .grid( row=7, column=2 )
          Tk.Label(  tabfrm, text='')                   .grid( row=8, column=2 )
          clearfile    = Tix.Button(tabfrm, name='clearfile', text='Clear All\nLogfiles', width=10, command=self.wclearfiles) .grid( column=2, row=9 )
          # insert the already loaded logfiles into the listbox

          self.logfiles = listbox
          #for f in  self.logfilenames :
          #  self.logfiles.insert( Tk.END, f )



          fsz = 10


          #----------------------------------------
          # Create the Xaxis, Yaxis, and Y2axis Tab pages
          #----------------------------------------




          for xy in ('X', 'Y', 'Y2' ):

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
              if xy == 'Y2' :
                self.y2axis_tabfrm = tabfrm
                tab=self.nb.y2axis
                base_name     =  self.y2name     = Tk.StringVar(master=tabfrm)
                base_text     =  self.y2text     = Tk.StringVar(master=tabfrm)
                base_full_list = self.y2full     = Tk.IntVar(master=tabfrm)
                base_scl_auto =  self.y2scl_auto = Tk.IntVar(master=tabfrm)
                base_scl_max  =  self.y2scl_max  = Tk.StringVar(master=tabfrm)
                base_scl_min  =  self.y2scl_min  = Tk.StringVar(master=tabfrm)
                base_grd_step  =  self.y2grd_step  = Tk.StringVar(master=tabfrm)




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
              if xy == 'Y2' :
                self.y2axis_col_list  = names



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
              
              Tix.Button(tabfrm, name='updscale',  text='Update Scale', width=10, command=self.update_graph_scale ).grid( columnspan=2, column=2, row=9 )
              base_scl_auto.set( True )
              base_grd_step.set( '' )

              # set the x and y axes according to the initial xynames values
              # and select them in the listbox areas


              if xy == 'X' : self.xnames = names
              if xy == 'Y' : self.ynames = names
              if xy == 'Y2' : self.y2names = names
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
          Tk.Label( tabfrm, font=("Helvetica", fsz), textvariable=self.filter_name) .grid( column=0, row=6, sticky='w')

          # add the filter range selction entry boxes
          self.filter_value_min      = Tk.StringVar(master=tabfrm)
          Tk.Entry( tabfrm, width=10, textvariable=self.filter_value_min, name='filter_value_min' ).grid( column=1, row=6, sticky='w')
          self.filter_value_max      = Tk.StringVar(master=tabfrm)
          Tk.Entry( tabfrm, width=10, textvariable=self.filter_value_max, name='filter_value_max' ).grid( column=2, row=6, sticky='w')
#


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






          #----------------------------------------
          # format Tab
          #----------------------------------------

          tab=self.nb.format
          tabfrm = Tix.Frame(tab, name='format')
          tabfrm.pack(side=Tix.TOP, padx=2)


          self.graph_title      = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Graph Title:', font=("Helvetica", fsz) ) .grid( columnspan=3, column=0, row=1, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.graph_title, validate='all', validatecommand=self.update_graph_title ) .grid( columnspan=3, column=0, row=2, sticky='w')
          self.graph_title.set('')







          self.wplot_position      = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Graph Location', font=("Helvetica", fsz) )    .grid( columnspan=3, column=0, row=3, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.wplot_position )        .grid( columnspan=3, column=0, row=4, sticky='w')
          self.plot_position = self.update_entry_box( self.plot_position, self.wplot_position )

          self.wconditions_location      = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Conditions Location:    Draw Conditions', font=("Helvetica", fsz) )  .grid( column=0, row=5, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.wconditions_location )      .grid( columnspan=3, column=0, row=6, sticky='w')
          self.conditions_location = self.update_entry_box( self.conditions_location, self.wconditions_location )

          self.draw_conditions    = Tk.IntVar(master=tabfrm)
#          Tk.Label( tabfrm, text='Draw Conditions',  font=("Helvetica", fsz) )    .grid( column=1, row=5, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.draw_conditions )                 .grid( column=2, row=5, sticky='w')
          self.draw_conditions.set( False )



          self.wlegend_location      = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Legend Location:      Smaller Legend', font=("Helvetica", fsz) )  .grid( column=0, row=7, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.wlegend_location )      .grid( columnspan=3, column=0, row=8, sticky='w')
          self.legend_location     = self.update_entry_box( self.legend_location,     self.wlegend_location )

          self.small_legend    = Tk.IntVar(master=tabfrm)
#          Tk.Label( tabfrm, text='Smaller Legend',  font=("Helvetica", fsz) )  .grid( column=1, row=7, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.small_legend )                 .grid( column=2, row=7, sticky='w')
          self.small_legend.set( True )

          self.wcolor_list      = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Clr Ordr: r g b c m y k orange violet brown', font=("Helvetica", fsz) )       .grid( columnspan=3, column=0, row=11, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.wcolor_list )                                              .grid( columnspan=3, column=0, row=12, sticky='w')
          self.update_entry_box( self.color_list, self.wcolor_list )

          self.wdash_list      = Tk.StringVar(master=tabfrm)

          self.wplot_linewidth      = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Line Width:', font=("Helvetica", fsz) )      .grid( columnspan=3, column=0, row=15, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.wplot_linewidth )      .grid( columnspan=3, column=0, row=16, sticky='w')
          self.update_entry_box( self.plot_linewidth, self.wplot_linewidth )

          self.wplot_marker      = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Line Mkr: . , o v ^ < > 1-7 s p x h H D d + | _ ', font=("Helvetica", fsz) )  .grid( columnspan=3, column=0, row=17, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.wplot_marker )                                              .grid( columnspan=3, column=0, row=18, sticky='w')
          self.update_entry_box( self.plot_marker, self.wplot_marker )

          self.wnumgrids      = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Default Number of Grid Lines:', font=("Helvetica", fsz) ) .grid( columnspan=3, column=0, row=19, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.wnumgrids )                         .grid( columnspan=3, column=0, row=20, sticky='w')
          self.update_entry_box( self.numgrids, self.wnumgrids )

          self.wnumcontours     = Tk.StringVar(master=tabfrm)
          Tk.Label( tabfrm, text='Number of Contour Lines (for Polar plots):', font=("Helvetica", fsz) ) .grid( columnspan=3, column=0, row=21, sticky='w')
          Tk.Entry( tabfrm, width=40, textvariable=self.wnumcontours )                      .grid( columnspan=3, column=0, row=22, sticky='w')
          self.update_entry_box( self.numcontours, self.wnumcontours )

#           self.contour_plot    = Tk.IntVar(master=tabfrm)
#           Tk.Label( tabfrm, text='Contour Plot',  font=("Helvetica", fsz) )  .grid( column=1, row=23, sticky='e')
#           Tk.Checkbutton( tabfrm, variable=self.contour_plot )               .grid( column=2, row=23, sticky='w')
#           self.contour_plot.set( False )



          self.contourfill    = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Color-Filled Contour Plot',  font=("Helvetica", fsz) )  .grid( column=0, row=24, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.contourfill )                             .grid( column=2, row=24, sticky='w')
          self.contourfill.set( False )

          self.polar_phase_plot    = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Polar Phase Plot',  font=("Helvetica", fsz) )  .grid( column=0, row=25, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.polar_phase_plot )               .grid( column=2, row=25, sticky='w')
          self.polar_phase_plot.set( False )


          self.contourmaxval    = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Display Max Contour Value',  font=("Helvetica", fsz) )  .grid( column=0, row=26, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.contourmaxval )                           .grid( column=2, row=26, sticky='w')
          self.contourmaxval.set( True )

          self.contourminval    = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Display Min Contour Value',  font=("Helvetica", fsz) )  .grid( column=0, row=27, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.contourminval )                           .grid( column=2, row=27, sticky='w')
          self.contourminval.set( True )

          self.polar_annotate_full    = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Annotate full data for Polar plot',  font=("Helvetica", fsz) )  .grid( column=0, row=28, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.polar_annotate_full )                             .grid( column=2, row=28, sticky='w')
          self.polar_annotate_full.set( False )


          self.line_on     = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Lines On:',  font=("Helvetica", fsz) ) .grid( column=0, row=29, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.line_on )                .grid( column=2, row=29, sticky='w')
          self.line_on.set( True )


          self.sort_data_on     = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Sort Data Points:',  font=("Helvetica", fsz) )  .grid( column=0, row=30, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.sort_data_on )                    .grid( column=2, row=30, sticky='w')
          self.sort_data_on.set( True )


          self.force_line_on     = Tk.IntVar(master=tabfrm)
          Tk.Label( tabfrm, text='Force Lines:',  font=("Helvetica", fsz) ) .grid( column=0, row=31, sticky='e')
          Tk.Checkbutton( tabfrm, variable=self.force_line_on )                .grid( column=2, row=31, sticky='w')
          self.force_line_on.set( True )



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
## RUN external script
#############################################################################################################
    def browse_script_file( self ):

        file = self.get_readfiles_dialog( 'Select python script file to run', 'scriptdir' , ('Python', '*.py') )[0]
        self.script_file_name.set(file)
        self.save_pygram_config( 'script_file_name',  file ) 


#############################################################################################################
    def run_script( self ):

        global g
        import __main__
        g = __main__.mag

        file = self.script_file_name.get()
        if os.access( file, os.R_OK ): 
            self.save_pygram_config( 'script_file_name',  file ) 
            txt = 'Running Script: %s' % file
            self.status.set( txt )
            print txt
            time.sleep(0.1)
            execfile( file, globals(), globals())
        else:
            txt = "*** ERROR *** cannot find or read script file '%s'" % file
            self.status.set( txt )
            print txt


#############################################################################################################
## Live Data: Other applications can draw graphs with these functions
#############################################################################################################
    def live_plot_start( self ):
    
        self.live_plot_clear()
        

        
        self.live_data_collection = LineCollection( self.live_data_points['Segments'],
            linewidths = 2,
        )
        #    colors = ['black',],
        #    transOffset = ax.transData,
        #    )
        
        self.ax.add_collection(self.live_data_collection)
    
#############################################################################################################   
    def live_plot_clear( self ):
   
        
        self.live_data_points = {}
        self.live_data_axes   = None

        self.live_data_points['Segments'] = [[(None,None)]]        
        self.live_data_points['Colors'] = [None]
        self.live_data_points['Lines' ] = [None]
        
        self.live_data_max_colors = 0
        self.live_data_max_lines = 0
        self.live_data_line_parameter = ''
        self.live_data_color_parameter = ''
        
        
        
        self.update_color_list()
       
     
        

#############################################################################################################
    def live_data_add_point( self, values_dict ):
    
        if not self.live_data_axes: return
        
        xaxis  = self.live_data_axes[0]
        yaxis  = self.live_data_axes[1]
        y2axis = self.live_data_axes[2]
    
        x  = None
        y  = None
        y2 = None
        for cn in values_dict:
            cn1 = re.sub('^\d+\|', '', cn)
#            cn1 = cn
            if cn1 == xaxis:
                x =  values_dict[ cn  ]
            if cn1 == yaxis:
                y =  values_dict[ cn  ]
            if cn1 == y2axis:
                y2 = values_dict[ cn ]
                    
        print '(live_data_add_point) x,y = ', (x,y)
                    
        if x != None and y != None:            
                    
            if 'Color' in values_dict: 
                cidx = values_dict['Color']
            else:
                cidx = 0
            cidx = int(cidx)
                
#             if cidx > self.live_data_max_colors:
#                 self.live_data_max_colors = cidx
              
            if 'Line' in values_dict: 
                lidx = values_dict['Line' ] 
            else:
                lidx = 0
            lidx = int(lidx)
            
            
            
            # Data points are separated into separated lines. The
            # Color and Line indexs are combined to create a line_index
            line_index = cidx + ( lidx * (self.live_data_max_colors)) 

            print '# (live_data_add_point) adding x,y' , (x,y), cidx, lidx, line_index, self.live_data_max_colors, self.live_data_max_lines

        
            
            segs = self.live_data_points['Segments']    
            cols = self.live_data_points['Colors']                          
            lins = self.live_data_points['Lines']
            while len( segs ) < line_index+1:
                segs.append( [ (None,None) ] )  
                cols.append( self.color_list_rgba[ cidx ] )  
                lins.append( self.dash_list_tuple[ lidx ] )         
            segs[ line_index ].append( (x,y) )
            cols[ line_index ] = self.color_list_rgba[ cidx ]
            lins[ line_index ] = self.dash_list_tuple[ lidx ]
      
       
#            print '# (live_data_add_point) live_data_points' , self.live_data_points['Segments']
       
            self.live_data_collection.set_segments(self.live_data_points['Segments'])
            self.live_data_collection.set_color(self.live_data_points['Colors'])
            self.live_data_collection.set_linestyles(self.live_data_points['Lines'])
#        self.live_data_collection.set_linestyles([  ( 0, (1,2) ), ] )


        
        
#        self.fig.canvas.draw()

#############################################################################################################
    def live_data_setup_axes(self):
    
            self.color_series.set( self.live_data_color_parameter )
            self.line_series.set( self.live_data_line_parameter )

            self.ax.set_xlabel( self.live_data_axes[0] )
            self.ax.set_ylabel( self.live_data_axes[1] + str(self.live_data_axes[2] ))


            # xaxis 
            self.xaxis_col_list.selection_clear(0, Tk.END)
            added = self.select_listbox_name( self.live_data_axes[0], self.xaxis_col_list )
            if not added:
                self.xaxis_col_list.insert( Tix.END, self.live_data_axes[0]  )     
                added = self.select_listbox_name( self.live_data_axes[0], self.xaxis_col_list )

            # yaxis 
            self.yaxis_col_list.selection_clear(0, Tk.END)
            added = self.select_listbox_name( self.live_data_axes[1], self.yaxis_col_list )
            if not added:
                self.yaxis_col_list.insert( Tix.END, self.live_data_axes[1]  )     
                added = self.select_listbox_name( self.live_data_axes[1], self.yaxis_col_list )


    
#############################################################################################################
    def live_data_clear_points( self ):
        pass

#############################################################################################################
    def update_color_list(self):
    
        self.color_list          = self.update_entry_box( self.color_list,          self.wcolor_list )

        # Make a list of colors cycling through the rgbcmyk series.
        self.color_list_rgba = [colorConverter.to_rgba(c) for c in self.color_list]
        
        self.dash_list_tuple = [] 
        for d in self.dash_list:
            self.dash_list_tuple.append( (0,( d[0], d[1])) )



#############################################################################################################
    def update_graph_scale( self , xlm=None, ylm=None):

       self.update_graph_scale_core(xlm, ylm)
       self.canvas.draw()

#############################################################################################################
    def update_graph_scale_core( self , xlm=None, ylm=None):
        '''Updates the graph scale
        Parameters: None
        Returns:    none

        '''
        
#        print '(update_graph_scale)', xlm, ylm
        
        if xlm != None and (isinstance( xlm, types.ListType) or isinstance( xlm, types.TupleType)) and len(xlm) == 2:
            self.xscl_min.set(xlm[0])
            self.xscl_max.set(xlm[1])

        if ylm != None and (isinstance( ylm, types.ListType) or isinstance( xlm, types.TupleType)) and  len(ylm) == 2:
            self.yscl_min.set(ylm[0])
            self.yscl_max.set(ylm[1])
        
        
        if 1:      
              self.xaxis_limits = self.get_axis_limits( self.xlimits, self.xscl_min.get(), self.xscl_max.get() )
              self.yaxis_limits = self.get_axis_limits( self.ylimits, self.yscl_min.get(), self.yscl_max.get() )
              self.y2axis_limits = self.get_axis_limits( self.y2limits, self.y2scl_min.get(), self.y2scl_max.get() )

              if self.xaxis_limits != [] :
                  self.ax.set_xlim( ( self.xaxis_limits[0] , self.xaxis_limits[1] ) )

              if self.yaxis_limits != [] :
                  self.ax.set_ylim( ( self.yaxis_limits[0] , self.yaxis_limits[1] ) )

              if self.y2axis_limits != [] :
                  self.ax.set_y2lim( ( self.y2axis_limits[0] , self.y2axis_limits[1] ) )

              self.ax.grid(True)

              # Set the number of grid lines

              g = self.xgrd_step.get()

              lim = self.ax.set_xlim()
              try:  self.ax.set_xticks( self.get_grid_ticks( lim, self.xgrid, g ) )
              except: pass


              g = self.ygrd_step.get()

              lim = self.ax.set_ylim()
              self.ax.set_yticks( self.get_grid_ticks( lim, self.ygrid, g ) )


#############################################################################################################
    def update_graph_title( self ):
        '''Updates the graph title from gui control entry box
        Parameters: None
        Returns:    none
        Reads:      self.graph_tile   gui entry box
        '''

        title( self.graph_title.get() )





#############################################################################################################
    def pdebug( self, name):
    
        print '(PDEBUG) 1' , name
        if name in self.values_dict:
            print '(PDEBUG) 2' , self.values_dict[ name ]
            print '(PDEBUG) 3' ,  self.values_dict_count[ name ] 
            print '(PDEBUG) 4' ,  self.values_dict_count_total[ name ]
        else:
            print 'NOT FOUND'


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


          # Creat a new 'values_dict' . This is a list of columns names and the
          # number of different values that the column contains 
          # First get the list of standard column 
          for vdn in self.value_dict_names_original_list:
              if vdn in self.data:
                  if vdn not in self.value_dict_names:
                      self.value_dict_names.append( vdn )

          self.values_dict_done = 0
          # Go through ALL the columns counting the number of differen values each column contains
          self.create_values_dict(allcols=True)



          # this updates the list of columns in the gui, and is listed on each of the axes, and on the fileter page
          # which also includes the color and line style selection boxes.

          # This should be run every time the list of columns changes






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

          # Before we clear everything from the Axis column lists
          # record the selection so that we can reapply it afterwards

          xnames_sel_lst = []
          xysel_lst =  self.xaxis_col_list.curselection()
          for i in xysel_lst:
             col = self.xaxis_col_list.get( int(i) )
             col = self.remove_count_from_column(col)
             xnames_sel_lst.append( col )

          ynames_sel_lst = []
          xysel_lst =  self.yaxis_col_list.curselection()
          for i in xysel_lst:
             col = self.yaxis_col_list.get( int(i) )
             col = self.remove_count_from_column(col)
             ynames_sel_lst.append( col )

          y2names_sel_lst = []
          xysel_lst =  self.y2axis_col_list.curselection()
          for i in xysel_lst:
             col = self.y2axis_col_list.get( int(i) )
             col = self.remove_count_from_column(col)
             y2names_sel_lst.append( col )

          fnames_sel_lst = []
          xysel_lst =  self.filter_column_list.curselection()
          for i in xysel_lst:
             col = self.filter_column_list.get( int(i) )
             col = self.remove_count_from_column(col)
             fnames_sel_lst.append( col )


          # Clear the listboxes

          self.xaxis_col_list.delete(0, Tk.END)
          full_list = self.xfull.get()
          for c in cll:
              vc, dc, val_count_str = self.get_values_count_str( c )
              if (full_list and vc > 0) or dc > 0:
                    self.xaxis_col_list.insert( Tix.END, '%s  %s' % (c, val_count_str ))

          self.yaxis_col_list.delete(0, Tk.END)
          full_list = self.yfull.get()
          for c in cll:
              vc, dc, val_count_str = self.get_values_count_str( c )
              if (full_list and vc > 0) or dc > 0:
                    self.yaxis_col_list.insert( Tix.END, '%s  %s' % (c, val_count_str ))

          self.y2axis_col_list.delete(0, Tk.END)
          full_list = self.y2full.get()
          for c in cll:
              vc, dc, val_count_str = self.get_values_count_str( c )
              if (full_list and vc > 0) or dc > 0:
                    self.y2axis_col_list.insert( Tix.END, '%s  %s' % (c, val_count_str ))

          self.filter_column_list.delete(0, Tk.END)
          full_list = self.ffull.get()
          for c in cll:
            vc, dc, val_count_str = self.get_values_count_str( c )
            if (full_list and vc > 0) or dc > 0:
                self.filter_column_list.insert( Tix.END, '%s  %s' % (c, val_count_str ) )


          # Reselect all the names that were originally selected (if we can)


          self.select_columns( self.xaxis_col_list, xnames_sel_lst )
          self.select_columns( self.yaxis_col_list, ynames_sel_lst )
          self.select_columns( self.y2axis_col_list, y2names_sel_lst )
          self.select_columns( self.filter_column_list, fnames_sel_lst )


          # for i in range(  self.xaxis_col_list.size() ):
          #     col = self.xaxis_col_list.get( int(i) )
          #     col = self.remove_count_from_column(col)
          #     if  col in   xnames_sel_lst:
          #           self.xaxis_col_list.activate(i)
          #           self.xaxis_col_list.selection_set(i)
          #           self.xaxis_col_list.see(i)
          #
          #
          # for i in range(  self.yaxis_col_list.size() ):
          #     col = self.yaxis_col_list.get( int(i) )
          #     col = self.remove_count_from_column(col)
          #     if  col in   ynames_sel_lst:
          #           self.yaxis_col_list.activate(i)
          #           self.yaxis_col_list.selection_set(i)
          #           self.yaxis_col_list.see(i)
          #
          #
          # for i in range(  self.filter_column_list.size() ):
          #     col = self.filter_column_list.get( int(i) )
          #     col = self.remove_count_from_column(col)
          #     if  col in   fnames_sel_lst:
          #           self.filter_column_list.activate(i)
          #           self.filter_column_list.selection_set(i)
          #           self.filter_column_list.see(i)

          # Remove any axes that dont exist (they can be removed after loading a new log file)
          xnames_ordered_new = []
          for col in self.xnames_ordered:
              if col in self.data:
                  xnames_ordered_new.append(col)
          self.xnames_ordered = xnames_ordered_new

          ynames_ordered_new = []
          for col in self.ynames_ordered:
              if col in self.data:
                  ynames_ordered_new.append(col)
          self.ynames_ordered = ynames_ordered_new

          y2names_ordered_new = []
          for col in self.y2names_ordered:
              if col in self.data:
                  y2names_ordered_new.append(col)
          self.y2names_ordered = y2names_ordered_new




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
            vc, dc, val_count_str = self.get_values_count_str( c )
            if dc > 1:           
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
            vc, dc, val_count_str = self.get_values_count_str( c )
            if dc > 1:           
              linst.insert( Tix.END, c )

          self.linst = linst

          self.nb.update()



#############################################################################################################
    def select_gui_cols(self, gui_list,  sel_list ):
          for i in range( gui_list.size() ):
              col = gui_list.get( int(i) )
              col = self.remove_count_from_column(col)
              if  col in  sel_list:
                    gui_list.activate(i)
                    gui_list.selection_set(i)
                    gui_list.see(i)




#############################################################################################################
    def select_columns( self, column_list, sel_list ):
        '''Select the list of columns in the list'''

        for i in range(  column_list.size() ):
              col = column_list.get( int(i) )
              col = self.remove_count_from_column(col)
              if  col in  sel_list:
                    column_list.activate(i)
                    column_list.selection_set(i)
                    column_list.see(i)
              else:
                    column_list.selection_clear(i)



#############################################################################################################
    def get_values_count_str( self, column ):
        '''Return a string containing the number of non empty values for the 
        given column name, plus the number of different values. If the number 
        of different value sis greater than 99 then ignore don't report it 
        (as is typical with  measurement result values)
        
        Returns:
           value_count, diff_count, 'value_count:diff_count'
           value_count, diff_count, 'value_count'              if value count is 0
           value_count, diff_count, 'value_count:*'            if diff_count > 99
        '''
        
        val_count = 0
        diff_count = 0
        
        if column in self.values_dict_count_total:
            val_count = self.values_dict_count_total[ column ]
            count_str = '%s'        
            if val_count  != 0:
                diff_count = len( self.values_dict_count[ column ] )
#                 if diff_count < 99:
#                     count_str += ':%s' % (diff_count)
        

        count_str = '%s' % val_count 
        
        if val_count > 0:
            if diff_count < 99:
                count_str = '<%s:%s>' % (count_str, diff_count)
            else:
                count_str = ''       
        
        
        return val_count, diff_count, count_str

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

          for xy in ('X', 'Y', 'Y2' ):


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

              if xy == 'Y2' :
                base_name     =  self.y2name
                base_text     =  self.y2text
                base_names    =  self.y2axis_col_list
                xyname        =  xynames[1]      #####   ???????  Not sure whether this is still in play or not
                lim           =  self.y2limits
                base_scl_auto =  self.y2scl_auto
                base_scl_max  =  self.y2scl_max
                base_scl_min  =  self.y2scl_min
                base_full     =  self.y2full



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

                  if xy == 'Y2':
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
              if xy == 'Y2' :
                self.y2limits  = lim



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

                     name = self.remove_count_from_column( name )

                     done = False
                     for i in range( listbox.size() ):
                         if name ==  self.remove_count_from_column( listbox.get( i )) :
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
####  MERCURY  DATABASE FUNCTIONS  FOR LOADING CHARACTERIZATION RACK RESULTS ########
#####################################################################################

    def mercury_load_db( self, site = None, update_form=None ):
      '''Create a new window for entering the database results
      Parameters:   None
      Returns:      None
      '''



      fsz = 10

      ##########################################################
      #
      # Create a new window for entering the database results
      #
      ##########################################################

      self.dbwin = Tix.Toplevel( master=self.root, name = 'dbwin' )
      self.dbwin.title("Load test results from Mercury Database (GSO Characterization Racks)")

      dbfrm = Tix.Frame(self.dbwin, name='dbfrm')
      dbfrm.grid()



      ##########################################################
      #
      # Add a list box to select the available databases
      #
      ##########################################################

      # Sitename Selection
      vallist = ['San Jose', 
                 'Greensboro', 
                 'Cedar Rapids', 
                 'England', 
                 'Phoenix',
                 'Boston',
                 'Denmark',
#                 'Shanghai',
                 'Westlake',
                ]

      self.mercury_db   =  Tk.StringVar(master=dbfrm)
      Tk.Label( dbfrm, text='Select Site:',  ) .grid( column=0, row=0, sticky='w')
      wgt = Tix.ComboBox(dbfrm, label='', dropdown=1, 
          command=self.mercury_update_search_form,
          name='mercury_db', editable=1,
          variable=self.mercury_db,
          options='listbox.height 5  listbox.width 15 entry.width 15 label.width 0 label.anchor w entry.state normal')
      wgt.grid( column=0, row=1, sticky='w' )
      self.mercury_db_list = wgt
      # add the list of Sitenames
      wgt.insert( Tix.END, '' )
      for name in vallist:
        wgt.insert( Tix.END, name )
     
      if site == None:
        site = 'San Jose'
      self.mercury_db.set(site)
        

#          command=self.mercury_update_search_form,

      self.mercury_site = site
      self.mercury_set_dsn(self.mercury_site)
      
      

      # Part Number Selection
      self.mercury_partnum   =  Tk.StringVar(master=dbfrm)
      Tk.Label( dbfrm, text='Part Number:',  ) .grid( column=1, row=0, sticky='w')
#       wgt = Tix.ComboBox(dbfrm, label='', dropdown=1, name='mercury_partnum_wgt', editable=1,
#           variable=self.mercury_partnum,
#           options='listbox.height 5  listbox.width 15 entry.width 15 label.width 0 label.anchor w entry.state normal')
#       wgt.grid( column=1, row=1, sticky='w' )
      wgt = ttk.Combobox(dbfrm,textvariable=self.mercury_partnum, )
      wgt.grid( column=1, row=1, sticky='w' )
      self.mercury_partnums = wgt 
      
       
      

      # JTS Job Selection
      vallist = ['none']
      self.mercury_jtsnums   =  Tk.StringVar(master=dbfrm)
      Tk.Label( dbfrm, text='JTS Job:',  ) .grid( column=2, row=0, sticky='w')
      wgt = Tix.ComboBox(dbfrm, label='', dropdown=1, name='mercury_jtsnums', editable=1,
          variable=self.mercury_jtsnums,
          options='listbox.height 5  listbox.width 15 entry.width 15 label.width 0 label.anchor w entry.state normal')
      wgt.grid( column=2, row=1, sticky='w' )
      # add the list of Sitenames
      wgt.insert( Tix.END, '' )
      for name in vallist:
        wgt.insert( Tix.END, name )
      self.mercury_jtsnums.set(vallist[0])


      
      # Date Selection
      self.mercury_datestart   =  Tk.StringVar(master=dbfrm)
      self.mercury_datestop    =  Tk.StringVar(master=dbfrm)
      Tk.Label( dbfrm, text='Date From:',  ) .grid( column=3, row=0, sticky='w')
      Tk.Label( dbfrm, text='Date To:',  )   .grid( column=4, row=0, sticky='w')
      Tk.Entry( dbfrm, width=15, textvariable=self.mercury_datestart).grid( column=3, row=1, sticky='w')
      Tk.Entry( dbfrm, width=15, textvariable=self.mercury_datestop).grid( column=4, row=1, sticky='w')
      
      now_seconds = time.time()
      one_month_ago =   time.strftime("%m/%d/%Y", time.localtime(now_seconds - (60*60*24*31)))   # from one month ago
      today =           time.strftime("%m/%d/%Y", time.localtime(now_seconds + (60*60*24*1 )))   # to tomorrow
      self.mercury_datestart.set( one_month_ago )
      self.mercury_datestop.set( today )

      # Session Description
      self.mercury_desc   =  Tk.StringVar(master=dbfrm)
      Tk.Label( dbfrm, text='Session Description:',  ) .grid( column=0, row=2, sticky='w')
      Tk.Entry( dbfrm, width=47, textvariable=self.mercury_desc ).grid( columnspan=2, column=0, row=3, sticky='w')
      
      # Test Plan Name
      self.mercury_testplan   =  Tk.StringVar(master=dbfrm)
      Tk.Label( dbfrm, text='Test Plan Name:',  ) .grid( column=2, row=2, sticky='w')
      Tk.Entry( dbfrm, width=47, textvariable=self.mercury_testplan ).grid( columnspan=2, column=2, row=3, sticky='w')

      # Session Status
      vallist = ['Published', 'Testing']
      self.mercury_sesstatus   =  Tk.StringVar(master=dbfrm)
      Tk.Label( dbfrm, text='Session Status:',  ) .grid( column=0, row=4, sticky='w')
      wgt = Tix.ComboBox(dbfrm, label='', dropdown=1, name='mercury_sesstatus', editable=1,
          variable=self.mercury_sesstatus,
          options='listbox.height 5  listbox.width 15 entry.width 15 label.width 0 label.anchor w entry.state normal')
      wgt.grid( column=0, row=5, sticky='w' )
      # add the list of Sitenames
      wgt.insert( Tix.END, '' )
      for name in vallist:
        wgt.insert( Tix.END, name )
      self.mercury_sesstatus.set('')
      
      # Board Number
      self.mercury_boardnum   =  Tk.StringVar(master=dbfrm)
      Tk.Label( dbfrm, text='Board Number:',  ) .grid( column=1, row=4, sticky='w')
      Tk.Entry( dbfrm, width=20, textvariable=self.mercury_boardnum ).grid( columnspan=1, column=1, row=5, sticky='w')

      # Session ID
      self.mercury_sesid   =  Tk.StringVar(master=dbfrm)
      Tk.Label( dbfrm, text='Session ID:',  ) .grid( column=2, row=4, sticky='w')
      Tk.Entry( dbfrm, width=20, textvariable=self.mercury_sesid  ).grid( columnspan=1, column=2, row=5, sticky='w')
      
      # Tester Name Selection
      Tk.Label(dbfrm, text="Tester:") .grid( column=4, row=3, sticky='w')
      shl = Tix.ScrolledHList(dbfrm, name='topdb_list', options='hlist.columns 1' )
      shl.grid  (rowspan=4, column=4, row=4, sticky='w')
      shl.hlist['selectmode'] = Tix.EXTENDED
      self.mercury_tester_list = shl.hlist
      self.mercury_tester_list.config(separator='.', width=21, height=5, drawbranch=0, indent=10)
      self.mercury_tester_list.column_width(0, chars=20)
#      self.mercury_tester_list.header_create(0, itemtype=Tix.TEXT, text='Database')
      self.mercury_tester_selall_checked   = Tk.IntVar(master=dbfrm)
      Tk.Checkbutton( dbfrm, variable=self.mercury_tester_selall_checked, 
        command=self.mercury_select_all_testers, text='Select All' ).grid( column=4, row=3)
      self.mercury_tester_sel   = Tk.IntVar(master=dbfrm)



      # Charting Options
      vallist = ['Create charts later']
      self.mercury_chartopt   =  Tk.StringVar(master=dbfrm)
      Tk.Label( dbfrm, text='Charting Options:',  ) .grid( column=0, row=6, sticky='w')
      wgt = Tix.ComboBox(dbfrm, label='', dropdown=1, name='mercury_chartopt', editable=1,
          variable=self.mercury_chartopt,
          options='listbox.height 5  listbox.width 15 entry.width 15 label.width 0 label.anchor w entry.state normal')
      wgt.grid( column=0, row=7, sticky='w' )
      # add the list of Sitenames
      wgt.insert( Tix.END, '' )
      for name in vallist:
        wgt.insert( Tix.END, name )
      self.mercury_chartopt.set(vallist[0])
      
      # Alias Sets
      vallist = ['none']
      self.mercury_aliasset   =  Tk.StringVar(master=dbfrm)
      Tk.Label( dbfrm, text='Alias Set:',  ) .grid( column=1, row=6, sticky='w')
      wgt = Tix.ComboBox(dbfrm, label='', dropdown=1, name='mercury_aliasset', editable=1,
          variable=self.mercury_aliasset,
          options='listbox.height 5  listbox.width 15 entry.width 15 label.width 0 label.anchor w entry.state normal')
      wgt.grid( column=1, row=7, sticky='w' )
      # add the list of Sitenames
      wgt.insert( Tix.END, '' )
      for name in vallist:
        wgt.insert( Tix.END, name )
      self.mercury_aliasset.set(vallist[0])








      w =     Tk.Label(dbfrm, text=' ') .grid( row=8, column=0 )

      #shl = Tix.tixTList(dbfrm, name='script_list', options='hlist.columns 5 hlist.header 1 ' )
      #shl = Tix.TList(dbfrm, name='script_list' )
      shl = Tix.ScrolledHList(dbfrm, name='script_list', options='hlist.columns 7 hlist.header 1 ' )
      shl.grid  (columnspan=6, column=0, row=9 )
      scriptlist=shl.hlist
      scriptlist.column_width(2,0)
      scriptlist.config(separator='.', width=200, height=20, drawbranch=0, indent=10,   selectmode=Tk.EXTENDED )
#          names   = Tk.Listbox(tabfrm, name='lb', width=40, height=40, yscrollcommand=axis_sb.set, exportselection=0, selectmode=Tk.EXTENDED)

      scriptlist.column_width(0, chars=40)
      scriptlist.column_width(1, chars=10)
      scriptlist.column_width(2, chars=50)
      scriptlist.column_width(3, chars=10)
      scriptlist.column_width(4, chars=40)
      scriptlist.column_width(5, chars=20)
      scriptlist.column_width(6, chars=20)

      scriptlist.header_create(0, itemtype=Tix.TEXT, text='Board No.')
      scriptlist.header_create(1, itemtype=Tix.TEXT, text='Session ID')
      scriptlist.header_create(2, itemtype=Tix.TEXT, text='Session Description')
      scriptlist.header_create(3, itemtype=Tix.TEXT, text='Part No.')
      scriptlist.header_create(4, itemtype=Tix.TEXT, text='Test Plan Name')
      scriptlist.header_create(5, itemtype=Tix.TEXT, text='Test Date [Test Time]')
      scriptlist.header_create(6, itemtype=Tix.TEXT, text='Tester')

      self.mercury_session_list = scriptlist


      self.mercury_sessions_selall_checked   = Tk.IntVar(master=dbfrm)
      Tk.Checkbutton( dbfrm, variable=self.mercury_sessions_selall_checked, \
        command=self.mercury_select_all_sessions, \
        text='Select All' ).grid( column=0, row=10, sticky='w')
#       self.mercury_sessions_showhide   = Tk.IntVar(master=dbfrm)
#       Tk.Checkbutton( dbfrm, variable=self.mercury_sessions_showhide, text='Show/Hide Routines' ).grid( column=1, row=10, sticky='e')
      self.mercury_sessions_applycolor   = Tk.IntVar(master=dbfrm)
      Tk.Checkbutton( dbfrm, variable=self.mercury_sessions_applycolor, text='Apply Status Color' ).grid( column=1, row=10, sticky='w')
      self.mercury_sessions_applyalias   = Tk.IntVar(master=dbfrm)
      Tk.Checkbutton( dbfrm, variable=self.mercury_sessions_applyalias, text='Apply AliasSet|Offsets' ).grid( column=2, row=10, sticky='e')
      self.mercury_run_report   = Tk.IntVar(master=dbfrm)
      Tk.Checkbutton( dbfrm, variable=self.mercury_run_report, text='Run Report' ).grid( column=3, row=10, sticky='e')


      Tk.Button(dbfrm, text="Search",       command=self.mercury_search) .grid(row=3, column=5)
      if update_form == 'argform':
          Tk.Button(dbfrm, text="Add\nResults", command=self.mercury_load_all_sessions_arg) .grid(row=10, column=4)
      else:
          Tk.Button(dbfrm, text="Load\nResults", command=self.mercury_load_all_sessions) .grid(row=10, column=4)

      Tk.Button(dbfrm, text="Close",        command=self.dbwin.destroy  ) .grid(row=10, column=5)

      self.mercury_search_count   =  Tk.StringVar(master=dbfrm)
      Tk.Label( dbfrm, text='Found: ?', textvariable=self.mercury_search_count  ) .grid( column=5, row=5, sticky='w')
      self.mercury_search_count.set(  'Found: 0   ')
      self.mercury_selected_count   =  Tk.StringVar(master=dbfrm)
      Tk.Label( dbfrm, text='Selected: ?', textvariable=self.mercury_selected_count ) .grid( column=5, row=6, sticky='w')
      self.mercury_selected_count.set('Selected: 0')


      self.dbwin.bind("<ButtonRelease>", self.mercury_do_event_buttonrelease,      )


      self.mercury_get_parts_testers_list( site )



#      self.dbwin.bind("<ButtonRelease>", self.do_dbwin_event_buttonrelease,      )
      #self.dbwin.bind("<Control-ButtonRelease>", self.do_event_ctlbuttonrelease,      )
#      self.dbwin.bind("<Double-Button>", self.do_dbwin_event_doublebuttonpress,  )
      #self.dbwin.bind("<Key>",           self.do_event_key,                )


    #########################################################
    def mercury_update_search_form(self, event=None):
        '''When ever someone changes the 'Site' setting on the form
        we redraw the form with the new site name. This will mainly cause the 
        database server name to change'''
        
        # Look to see if the site name is valid and look to see if has changed.
        site_from_form = self.mercury_db.get()
        if self.mercury_site not in ['', None] and site_from_form not in ['', None]:
            if self.mercury_site != site_from_form:
                self.mercury_site = site_from_form
                
                # Redraw the form but this time give it a new site name
                self.mercury_set_dsn(self.mercury_site)
                self.mercury_get_parts_testers_list(self.mercury_site)

    #########################################################
    def mercury_do_event_buttonrelease(self, event=None):
         
         if str(event.widget) == '.dbwin.dbfrm.script_list.f1.hlist':
            n = self.mercury_session_list.info_selection()
            self.mercury_selected_count.set('Selected: %d' % len(n))

    ##########################################################
    def mercury_select_all_testers(self):
        '''Select all or no testers'''
        
        if self.mercury_tester_selall_checked.get() == False:
            self.mercury_tester_list.selection_clear()
            
        if self.mercury_tester_selall_checked.get() == True:
            for tester in self.mercury_testerlist:
                self.mercury_tester_list.selection_set(tester)


    ##########################################################
    def mercury_select_all_sessions(self):
        '''Select all or no testers'''
        
        if self.mercury_sessions_selall_checked.get() == False:
            self.mercury_session_list.selection_clear()
            self.mercury_selected_count.set('Selected: %d' % 0)
        if self.mercury_sessions_selall_checked.get() == True:
            for key in self.mercury_search_list:
                self.mercury_session_list.selection_set(key)
            self.mercury_selected_count.set('Selected: %d' % len(self.mercury_search_list))



    ##########################################################
    def connect( self, dsn ):
        '''Connect to a database using a given DSN string'''
        
        cnxn = pyodbc.connect(dsn)
        return cnxn
    
    ##########################################################
    def mercury_get_parts_testers_list( self, site ):
        ''' Get a list of parts and testers that are available at this site database'''


        # Open up a database connection
        cnxn = self.connect(self.mercury_dsn)
        cursor = cnxn.cursor()

        # Get a unique list of part or product names
        # Query database for Part Numbers (Remote sites don't have the tsPartNumbers table)
        if site == 'Greensboro':
           sql = '''SELECT vcProductFamily 
                    FROM Mercury_Cache.dbo.tsPartNumbers
                    ORDER BY vcProductFamily ASC'''
        else:
           sql = '''SELECT DISTINCT vcProductFamily
                    FROM tsSessions
                    ORDER BY vcProductFamily ASC'''

        # Execute the database SQL query, (result is accesible through the cursor)
        cursor.execute(sql)
        # Extract the query result as a list of rows
        rows = cursor.fetchmany(400) # limit it to 400 rows max
        parts = []
        for row in rows:
            parts.append( row[0] )

        self.mercury_partlist = parts

        # Update the parts list
        self.mercury_partlist.insert(0,'All Parts')
        self.mercury_partnums['values'] = self.mercury_partlist
        self.mercury_partnum.set('All Parts')



        # Get a unique list of tester names
        if site == 'Greensboro':
            sql = '''SELECT * 
                      FROM Mercury_Cache.dbo.tsTestSystems 
                      ORDER BY vcTesterName ASC'''
        else:
            sql = '''SELECT * 
                     FROM Mercury_Cache.dbo.tsTestSystems
                     WHERE NOT vcTesterName IN ('NJENSENT60PXP3','NJENSENT61PXP1','JREADDEV','OSORENSENT60PXP')
                     ORDER BY vcTesterName ASC'''

#         sql = '''SELECT distinct
#             vcTesterName
#             FROM tsSessions a LEFT JOIN JTS_Cache.dbo.tsJTS b ON b.biJobID=a.iJobID 
#             order by vcTesterName
#               '''
        # Execute the database SQL query, (result is accesible through the cursor)
        cursor.execute(sql)
        # Extract the query result as a list of rows
        rows = cursor.fetchmany(400) # limit it to 400 rows max
        testers = []
        for row in rows:
            testers.append( row[0] )

        self.mercury_testerlist = testers

        # Close the database as we have no other data to retrieve at this point
        cnxn.close()

        self.mercury_tester_list.delete_all()
        for name in self.mercury_testerlist:
            e = name
            self.mercury_tester_list.add(e, itemtype=Tix.TEXT, text=name)

        return parts, testers




    ##########################################################     
    def mercury_set_dsn(self, site):

        if re.match(r'San Jose',site):     server = 'SVCARFTSDBNEW'
        elif site == 'Greensboro':         server = 'RFGSOCCCDB'
        elif site == 'Cedar Rapids':       server = 'criarftsdb'
        elif site == 'England':            server = 'ENGRFTSDB'
        elif site == 'Phoenix':            server = 'PHXRFTSDB3'
        elif site == 'Boston':             server = 'BOSTONRFTS'
        elif site == 'Denmark':            server = 'DMKRFTSDB2'
        elif site == 'Shanghai':           server = 'SHANGHAIRFTSDB'
        elif site == 'Westlake':           server = 'LACRFTSDB'
        else:                              server = 'SVCARFTSDBNEW'

        self.mercury_dsn = \
               'PROVIDER=MSDASQL;'     + \
               'driver={SQL Server};'  + \
               'server=%s;' % server   + \
               'database=Mercury;'     + \
               'uid=WebUser;'          + \
               'pwd=Web;'






    ##########################################################
    def mercury_search(self):
        '''Reads mercury database form values and performs search based on 
        form values and finds and populates the form listbox with tests which
        match the search criteria'''
 
        # Read the search criteria values from the form and get an SQL query string
        sql = self.mercury_get_search_sql_string()
        # Open up a database connection
        cnxn = self.connect(self.mercury_dsn)
        cursor = cnxn.cursor()
        # Execute the database SQL query, (result is accesible through the cursor)
        cursor.execute(sql)
        
        # Extract the query result as a list of rows
#        rows = cursor.fetchmany(400) # limit it to 400 rows max
        rows = cursor.fetchall() # limit it to 400 rows max
        # Clear any previous results from the GUI
        self.mercury_session_list.delete_all()
        # Go through each test results row, and write the values into the scriptlist columns
        
        self.mercury_search_list = {}
        for row in rows:
            e = '%s|%s' % ( row.vcTesterName, row.biSessionID )  # e is a unique index value
            self.mercury_session_list.add(e, itemtype=Tix.TEXT, text=row.vcBoardNumber)
            self.mercury_session_list.item_create(e, 1, itemtype=Tix.TEXT, text='  %s' % row.biSessionID)
            self.mercury_session_list.item_create(e, 2, itemtype=Tix.TEXT, text=row.vcSessionDesc)
            self.mercury_session_list.item_create(e, 3, itemtype=Tix.TEXT, text='  %s' % row.vcPartFamily)
            self.mercury_session_list.item_create(e, 4, itemtype=Tix.TEXT, text=row.vctestplanName)
            t = time.strftime( "  %d%b%y_%H%M", datetime.datetime.timetuple(row.dtSessionStartTime))
            self.mercury_session_list.item_create(e, 5, itemtype=Tix.TEXT, text=t.lower())
            self.mercury_session_list.item_create(e, 6, itemtype=Tix.TEXT, text=row.vcTesterName)
            self.mercury_search_list[ e ] = [  row.vcTesterName, row.biSessionID, row.vcPartFamily, row.vcBoardNumber, row.vctestplanName ] 
            
        
        self.mercury_search_count.set(  'Found: %d    ' % len(rows))
        self.mercury_selected_count.set('Selected: %d' % 0)
            
        # close the database once we are done
        cnxn.close()


    ############################################################################
    def mercury_delete_vars(self):

        del  self.mercury_db
        del  self.mercury_tester_list
        del  self.mercury_partnum
        del  self.mercury_sesstatus
        del  self.mercury_desc
        del  self.mercury_boardnum
        del  self.mercury_testplan
        del  self.mercury_datestart
        del  self.mercury_datestop


    ############################################################################
    def mercury_get_search_sql_string(self):
        '''Make up an SQL string to select the tests based on the Search form values'''
 
        # Get the search criteria values from the selection form    
        
        site            = self.mercury_site
        testers         = self.mercury_tester_list.info_selection()
        part            = self.mercury_partnum.get()
        testStatus      = self.mercury_sesstatus.get()
        txtSessionDesc  = self.mercury_desc.get()
        txtBoard        = self.mercury_boardnum.get()
        txtTestPlanName = self.mercury_testplan.get()
        dtSessionStartTime   = self.mercury_datestart.get()
        dtSessionFinishTime  = self.mercury_datestop.get()


        # Construct an SQL query string
        sql = '''SELECT 
            vcBoardNumber, 
            ISNULL(b.vcPartFamily, vcProductFamily) AS vcPartFamily, 
            biSessionID, 
            vctestplanName, 
            dtSessionStartTime, 
            dtSessionEndTime, 
            siStatusID, 
            vcSessionDesc, 
            vcTesterName,
            bPublished FROM tsSessions a LEFT JOIN JTS_Cache.dbo.tsJTS b ON b.biJobID=a.iJobID
            '''


        if site == "Greensboro":
            sql += ''' LEFT JOIN Prod_Correlation_Tracker_Cache.dbo.tsCorrelationTracker c 
                ON a.iJobID = c.biCorrelationID 
                WHERE 
                '''
        else:
            sql += ' WHERE \n'

        sql += "bHidden=0 AND \n"
 
        if part != "All Parts":
            sql += "(b.vcPartFamily = '" + part + "' OR vcProductFamily = '" + part + "') AND \n"

        if len(testers) > 0:
            testers_str = ""
            for tester in testers:
                testers_str += "'%s'," % tester
            sql += "vcTesterName IN ( " + testers_str[:-1] + " ) AND \n"
           
        if testStatus == "Published":
            sql += "bPublished In (1) AND \n"
        elif testStatus == "Testing":
            sql +=  "siStatusID In (11) AND \n"
        else:
            sql += "siStatusID In (2,4,11,12) AND \n"

        if txtSessionDesc.strip() != "":
          if re.search(r'%%', txtSessionDesc):
            SplitDesc = txtSessionDesc.split("%")
            sql +=  "vcSessionDesc Like '%" + SplitDesc[0] + "%" + SplitDesc[1] + "%' AND \n"
          else:
            sql += "vcSessionDesc Like '%" + txtSessionDesc + "%' AND \n"

        if txtBoard.strip() !=  "":
            sql += "vcBoardNumber Like '%" + txtBoard + "%' AND \n"

        if txtTestPlanName.strip() != "":
            sql += "vcTestPlanName Like '%" + txtTestPlanName + "%' AND "
        
        sql += "dtSessionStartTime BETWEEN '" + dtSessionStartTime + "' AND '" + dtSessionFinishTime + "'"
        sql += " ORDER BY  dtSessionStartTime "
        
        
#        print 'SQL = ', sql
        
        return sql

        
    ##########################################################
    def mercury_load_all_sessions(self):
        '''Loads all the selected tests from the Mercury Test Selection form into
        Pygram self.data'''
        
        n = self.mercury_session_list.info_selection()

        # Open up a database connection
        cnxn = self.connect(self.mercury_dsn)
        cursor = cnxn.cursor()

        if len(n) > 0 :
            for r in n:
                self.mercury_load_session(cursor, r)

        # close the database once we are done
        cnxn.close()

        # prints out all the available column names (useful when defining the conditions)
        self.print_column_list()                    
        self.print_values_list()
        self.done_list_columns = True
        self.gen_values_dict()
        self.status.set( 'waiting for user input' )
        self.root.update()

        self.dbwin.destroy()


    ##########################################################
    def mercury_load_all_sessions_arg(self, dummy_arg=None):
        '''Add selected tests to the ARG form'''

        n = self.mercury_session_list.info_selection()

        # don't add the file if its there already
        lball = self.atrlogfiles_listbox.get(0, Tk.END )

        if len(n) > 0 :
            for r in n:
                r = 'Mercury|' + r
                fnd_file = False
                for n in lball:
                    if n == r:  fnd_file = True
                if not fnd_file:
                         self.atrlogfiles_listbox.insert( Tk.END, r )

        self.dbwin.destroy()


    ##########################################################
    def mercury_load_session(self, cursor, key):
        '''Loads all the selected tests from the Mercury Test Selection form into
        Pygram self.data'''


#        print '(mercury_load_test_res) key=', key

        # Get the tester and session keys so that we can select the full 
        # test results for this test        
        try:
           logfilename = re.sub('\|', '_', key)
           key = re.sub('^Mercury\|', '' , key)
           [(vcTesterName,biSessionID)] = re.findall(r'(.*)\|(\d+)$', key)
        except ValueError:
            print "*** Error *** (mercury_load_session) bad Mercury DB selection key '%s'" % key
            return

        

        # Get a list of distinct session test names
        # like:
        #     test_GSMComposite_v2
        #     test_TxMSave50OhmStateAdjustArb1
        #     TraceLoss     
        sql = '''Select distinct    
           name
           from Mercury_Cache.dbo.sysObjects 
           where name like 't_%s%%'
           '''  % (biSessionID)


        cursor.execute(sql)
        
        # Extract the query result as a list of rows
        rows = cursor.fetchmany(400) # limit it to 400 rows max

#        search_row = self.mercury_search_list[key]
#        logfilename = '%s_%s_%s' % ( search_row[2], search_row[3], search_row[1] )
        logfilename = re.sub(r'\s+','',logfilename)

        rn_start = self.datacount

        for row in rows:
            self.mercury_load_test(cursor, row[0], key, logfilename )

        # Update the main pygram gui tabs 
        rn_finish =  self.datacount
        
        # Update the main pygram gui tabs 
        self.logfiles.insert( Tk.END, self.get_filename_from_fullpath( logfilename ) + ' (%s)' % (rn_finish-rn_start))
        
        self.win_load( logfilename, num_records=rn_finish-rn_start )




    ##########################################################
    def  mercury_load_test(self, cursor, testplan_id, key, logfilename):
        '''Load the results for a single testplan'''
        
        try:
            search_row = self.mercury_search_list[key]
        except AttributeError:
            print '*** Error *** Must use Mercury Load Results Form before loading from DB can be done'
            return

        # =[ vcTesterName, biSessionID, vcPartFamily, vcBoardNumber, vctestplanName ] 
        vcTesterName  = search_row[0]
        biSessionID   = search_row[1]
        vcPartFamily  = search_row[2]
        vcBoardNumber = search_row[3]
        vctestplanName   = search_row[4]

        self.status.set( 'Loading Mercury Database results for %s' % logfilename )
        
        
        # Get list of columns for this testplan
        count = self.mercury_count_test_rows( cursor, vcTesterName, testplan_id)

        # Get a count of how many test lines there are
        columns = self.mercury_get_test_columns( cursor, vcTesterName, testplan_id)
 
        
#        print '(mercury_load_test)', vcBoardNumber, count, len(columns), search_row
#        print columns
        
        # Add the data
        self.mercury_add_test_data( cursor, vcTesterName, vcBoardNumber, biSessionID, testplan_id, columns, logfilename)





    ##########################################################
    def  mercury_add_test_data(self, cursor, vcTesterName, vcBoardNumber, biSessionID, testplan_id, columns, logfilename):
        '''Add the Mercury test data into pygram self.data'''
        
        self.freq_mult = 1

        # Make an SQL friendly string containing all the colummn names 
        columns_str = ''
        for col in columns:
            columns_str += '[%s],' % col
        columns_str = columns_str[:-1]    # remove the last ',' character
                
#        sql = 'RF9840_SN008|24325|Select %s from  %s Order by DataID' % ( colnames, TableString )
        sql = "Select %s from  %s%s Order by DataID" % ( columns_str, "Mercury_Cache.." , testplan_id )

#        print '(mercury_add_test_data) sql=', sql

        cursor.execute(sql)
        
        # Extract the query result as a list of rows
        rows = cursor.fetchall() 
        
        rn_start = self.datacount
        rn_finish = rn_start + len(rows)
        self.datacount = rn_finish


        for col in columns:
            self.add_new_column(col)

        rn = rn_start
        for row in rows:
            for i, col in enumerate(columns):
                self.data[col][rn] = row[i]
            rn += 1        

        # Then add a few bits of static data that were not available in the last query
        self.mercury_add_misc_columns(rn_start, rn_finish,
              vcTesterName, vcBoardNumber, biSessionID, testplan_id, logfilename )


        self.logfile_type = 'mercury_db'
        
        # Make all columns the same length
        for col in self.data:
            self.add_new_column(col)
        
        # Add the extra columns that Pygrams normally fudges such as Pout(dBm) etc
        self.add_missing_columns( rn_start, rn_finish)

        
    #################################################################################################################
    def mercury_add_misc_columns( self, rn_start, rn_finish, vcTesterName, vcBoardNumber, biSessionID, testplan_id, logfilename ):
        '''Add misc data columns to self.data'''
        

        testname = re.sub(r't_\d+_','',testplan_id)

        self.add_new_column( 'vcTesterName' )
        self.add_new_column( 'vcBoardNumber' )
        self.add_new_column( 'biSessionID' )
        self.add_new_column( 'testplan_id' )
        self.add_new_column( 'logfilename' )
        self.add_new_column( 'record_num' )
        self.add_new_column( 'TestName' )
        
        for rn in range(rn_start,rn_finish):
            self.data[ 'vcTesterName' ][rn]  = vcTesterName    
            self.data[ 'vcBoardNumber' ][rn] = vcBoardNumber
            self.data[ 'biSessionID' ][rn]   = biSessionID
            self.data[ 'testplan_id' ][rn]   = testplan_id
            self.data[ 'logfilename' ][rn]   = logfilename
            self.data[ 'record_num' ][rn]    = rn
            self.data[ 'TestName' ][rn]      = testname
            

            


    ############################################################
    def mercury_count_test_rows( self, cursor, vcTesterName, testplan_id):
        '''Get a count of the number of individual tests for this testplan session'''
        
        
        sql = '''Select count(*) from Mercury_Cache..SysColumns 
            where ID = (Select ID from Mercury_Cache..SysObjects 
            where Name = '%s') ''' % testplan_id

        cursor.execute(sql)
        
        # Extract the query result as a list of rows
        rows = cursor.fetchmany(400) # limit it to 400 rows max

        if len(rows) == 1:
            return rows[0]
        else:
            print "*** Error *** (mercury_count_test_rows) bad Mercury DB data '%s'" % rows
            return None
        

        
    ############################################################
    def mercury_get_test_columns( self, cursor, vcTesterName, testplan_id):
        ''' Get a list of column heading names for this testplan session '''

        sql = '''select b.name, a.Name,  
            colid from mercury_cache.dbo.syscolumns a 
                  Join mercury_cache.dbo.sysobjects b  on b.id=a.id 
            where      b.type='u'  and  b.name in( '%s' )  order by b.name
            '''  % ( testplan_id )


        cursor.execute(sql)
        
        # Extract all the column data
        rows = cursor.fetchmany(400) # limit it to 400 rows max

        # Build the list containing the column names
        columns = []
        for r in rows:
           columns.append(r[1])

        return columns



#####################################################################################
####  ATLANTIS DATABASE FUNCTIONS  FOR LOADING CONSTELATION RESULTS #################
#####################################################################################

    def atlantis_load_db( self, site = None, update_form=None ):
      '''Create a new window for entering the database results
      Parameters:   None
      Returns:      None
      '''



      fsz = 10

      ##########################################################
      #
      # Create a new window for entering the database results
      #
      ##########################################################

      self.adbwin = Tix.Toplevel( master=self.root, name = 'adbwin' )
      self.adbwin.title("Load test results from Atlantis Database (Constellation Testbench results)")

      adbfrm = Tix.Frame(self.adbwin, name='adbfrm')
      adbfrm.grid()



      ##########################################################
      #
      # Add a list box to select the available databases
      #
      ##########################################################

      # Sitename Selection
      vallist = ['San Jose', 
                 'Greensboro', 
                 'Cedar Rapids', 
                 'England', 
                 'Phoenix',
                 'Boston',
                 'Denmark',
#                 'Shanghai',
                 'Westlake',
                ]

      self.atlantis_db   =  Tk.StringVar(master=adbfrm)
      Tk.Label( adbfrm, text='Select Database:',  ) .grid( column=0, row=0, sticky='w')
      wgt = Tix.ComboBox(adbfrm, label='', dropdown=1, 
          command=self.atlantis_update_search_form,
          name='atlantis_db', editable=1,
          variable=self.atlantis_db,
          options='listbox.height 5  listbox.width 15 entry.width 15 label.width 0 label.anchor w entry.state normal')
      wgt.grid( column=0, row=1, sticky='w' )
      self.atlantis_db_list = wgt
      # add the list of Sitenames
      wgt.insert( Tix.END, '' )
      for name in vallist:
        wgt.insert( Tix.END, name )
     
      if site == None:
        site = 'Greensboro'
      self.atlantis_db.set(site)
        

#          command=self.atlantis_update_search_form,

      self.atlantis_site = site
      self.atlantis_set_dsn(self.atlantis_site)
      
          

      # Part Number Selection
      self.atlantis_partnum   =  Tk.StringVar(master=adbfrm)
      Tk.Label( adbfrm, text='Part Number:',  ) .grid( column=1, row=0, sticky='w')
#       wgt = Tix.ComboBox(dbfrm, label='', dropdown=1, name='atlantis_partnum_wgt', editable=1,
#           variable=self.atlantis_partnum,
#           options='listbox.height 5  listbox.width 15 entry.width 15 label.width 0 label.anchor w entry.state normal')
#       wgt.grid( column=1, row=1, sticky='w' )
      wgt = ttk.Combobox(adbfrm,textvariable=self.atlantis_partnum, )
      wgt.grid( column=1, row=1, sticky='w' )
      self.atlantis_partnums = wgt 
      
      # Tester Name 
      self.atlantis_teststation   =  Tk.StringVar(master=adbfrm)
      Tk.Label( adbfrm, text='Test Station:',  ) .grid( column=2, row=0, sticky='w')
      Tk.Entry( adbfrm, width=20, textvariable=self.atlantis_teststation  ).grid( columnspan=1, column=2, row=1, sticky='w')
       
      

      
      # Date Selection
      self.atlantis_datestart   =  Tk.StringVar(master=adbfrm)
      self.atlantis_datestop    =  Tk.StringVar(master=adbfrm)
      Tk.Label( adbfrm, text='Date From:',  ) .grid( column=3, row=0, sticky='w')
      Tk.Label( adbfrm, text='Date To:',  )   .grid( column=4, row=0, sticky='w')
      Tk.Entry( adbfrm, width=15, textvariable=self.atlantis_datestart).grid( column=3, row=1, sticky='w')
      Tk.Entry( adbfrm, width=15, textvariable=self.atlantis_datestop).grid( column=4, row=1, sticky='w')
      
      now_seconds = time.time()
      today =           time.strftime("%m/%d/%Y", time.localtime(now_seconds+ (60*60*24*1)))
      one_month_ago =   time.strftime("%m/%d/%Y", time.localtime(now_seconds- (60*60*24*31)))
      self.atlantis_datestart.set( one_month_ago )
      self.atlantis_datestop.set( today )

      # Serial Number
      self.atlantis_serialnum   =  Tk.StringVar(master=adbfrm)
      Tk.Label( adbfrm, text='Serial Number:',  ) .grid( column=0, row=2, sticky='w')
      Tk.Entry( adbfrm, width=20, textvariable=self.atlantis_serialnum ).grid( columnspan=1, column=0, row=3, sticky='w')

      # Session Description
      self.atlantis_desc   =  Tk.StringVar(master=adbfrm)
      Tk.Label( adbfrm, text='Test Description:',  ) .grid( column=1, row=2, sticky='w')
      Tk.Entry( adbfrm, width=35, textvariable=self.atlantis_desc ).grid( columnspan=2, column=1, row=3, sticky='w')

      # Session Description
      self.atlantis_eventid   =  Tk.StringVar(master=adbfrm)
      Tk.Label( adbfrm, text='EventID:',  ) .grid( column=2, row=2, sticky='w')
      Tk.Entry( adbfrm, width=20, textvariable=self.atlantis_eventid ).grid( columnspan=2, column=2, row=3, sticky='w')


      # TestGroup Name
      self.atlantis_testgroup   =  Tk.StringVar(master=adbfrm)
      Tk.Label( adbfrm, text='Test Name:',  ) .grid( column=3, row=2, sticky='w')
      Tk.Entry( adbfrm, width=47, textvariable=self.atlantis_testgroup ).grid( columnspan=2, column=3, row=3, sticky='w')
      


      w =     Tk.Label(adbfrm, text=' ') .grid( row=8, column=0 )

      #shl = Tix.tixTList(dbfrm, name='script_list', options='hlist.columns 5 hlist.header 1 ' )
      #shl = Tix.TList(dbfrm, name='script_list' )
      shl = Tix.ScrolledHList(adbfrm, name='script_list', options='hlist.columns 8 hlist.header 1 ' )
      shl.grid  (columnspan=6, column=0, row=9 )
      scriptlist=shl.hlist
      scriptlist.column_width(2,0)
      scriptlist.config(separator='.', width=200, height=20, drawbranch=0, indent=10,   selectmode=Tk.EXTENDED )
#          names   = Tk.Listbox(tabfrm, name='lb', width=40, height=40, yscrollcommand=axis_sb.set, exportselection=0, selectmode=Tk.EXTENDED)

      scriptlist.column_width(0, chars=45)
      scriptlist.column_width(1, chars=10)
      scriptlist.column_width(2, chars=40)
      scriptlist.column_width(3, chars=10)
      scriptlist.column_width(4, chars=25)
      scriptlist.column_width(5, chars=20)
      scriptlist.column_width(6, chars=20)
      scriptlist.column_width(7, chars=300)

      scriptlist.header_create(0, itemtype=Tix.TEXT, text='Serial Num')
      scriptlist.header_create(1, itemtype=Tix.TEXT, text='EventID')
      scriptlist.header_create(2, itemtype=Tix.TEXT, text='Test Description')
      scriptlist.header_create(3, itemtype=Tix.TEXT, text='Part Num')
      scriptlist.header_create(4, itemtype=Tix.TEXT, text='Test Group Name')
      scriptlist.header_create(5, itemtype=Tix.TEXT, text='Test Date [Test Time]')
      scriptlist.header_create(6, itemtype=Tix.TEXT, text='Test Station')
      scriptlist.header_create(7, itemtype=Tix.TEXT, text='Conditions')

      self.atlantis_session_list = scriptlist


      self.atlantis_sessions_selall_checked   = Tk.IntVar(master=adbfrm)
      Tk.Checkbutton( adbfrm, variable=self.atlantis_sessions_selall_checked, \
        command=self.atlantis_select_all_sessions, \
        text='Select All' ).grid( column=0, row=10, sticky='w')
#       self.atlantis_sessions_showhide   = Tk.IntVar(master=dbfrm)
#       Tk.Checkbutton( dbfrm, variable=self.atlantis_sessions_showhide, text='Show/Hide Routines' ).grid( column=1, row=10, sticky='e')
#       self.atlantis_sessions_applycolor   = Tk.IntVar(master=adbfrm)
#       Tk.Checkbutton( adbfrm, variable=self.atlantis_sessions_applycolor, text='Apply Status Color' ).grid( column=1, row=10, sticky='w')
#       self.atlantis_sessions_applyalias   = Tk.IntVar(master=adbfrm)
#       Tk.Checkbutton( adbfrm, variable=self.atlantis_sessions_applyalias, text='Apply AliasSet|Offsets' ).grid( column=2, row=10, sticky='e')
#       self.atlantis_run_report   = Tk.IntVar(master=adbfrm)
#       Tk.Checkbutton( adbfrm, variable=self.atlantis_run_report, text='Run Report' ).grid( column=3, row=10, sticky='e')


      Tk.Button(adbfrm, text="Search",       command=self.atlantis_search) .grid(row=1, column=5)
#      Tk.Button(adbfrm, text="Refresh",      command=self.atlantis_search  ) .grid(row=4, column=5)

      if update_form == 'argform':
          Tk.Button(adbfrm, text="Add\nResults", command=self.atlantis_load_all_sessions_arg) .grid(row=10, column=4)
      else:
          Tk.Button(adbfrm, text="Load\nResults", command=self.atlantis_load_all_sessions) .grid(row=10, column=4)
      Tk.Button(adbfrm, text="Close",        command=self.adbwin.destroy  ) .grid(row=10, column=5)

      self.atlantis_search_count   =  Tk.StringVar(master=adbfrm)
      Tk.Label( adbfrm, text='Found: ?', textvariable=self.atlantis_search_count  ) .grid( column=5, row=2, sticky='w')
      self.atlantis_search_count.set(  'Found: 0   ')
      self.atlantis_selected_count   =  Tk.StringVar(master=adbfrm)
      Tk.Label( adbfrm, text='Selected: ?', textvariable=self.atlantis_selected_count ) .grid( column=5, row=3, sticky='w')
      self.atlantis_selected_count.set('Selected: 0')


      self.adbwin.bind("<ButtonRelease>", self.atlantis_do_event_buttonrelease,      )
      self.atlantis_session_list.bind("<Double-Button>", self.atlantis_load_all_sessions )


      self.atlantis_get_parts_list( site )

 
      # Fill in the form with values from a previous run
      names = [ 'Atlantis_site', 
                'Atlantis_PartNum',
                'Atlantis_TestDesc',
                'Atlantis_SerialNum',
                'Atlantis_TestGroup',
                'Atlantis_Station',
               ]
      widgets = [ self.atlantis_db, 
                  self.atlantis_partnum,
                  self.atlantis_desc,
                  self.atlantis_serialnum,
                  self.atlantis_testgroup,
                  self.atlantis_teststation,
                ]
      for name, widget in zip( names, widgets ):
          if name in self.pyconfig and self.pyconfig[ name ] != '':
               widget.set(self.pyconfig[ name ])

#      self.adbwin.bind("<ButtonRelease>", self.do_adbwin_event_buttonrelease,      )
      #self.adbwin.bind("<Control-ButtonRelease>", self.do_event_ctlbuttonrelease,      )
#      self.adbwin.bind("<Double-Button>", self.do_adbwin_event_doublebuttonpress,  )
      #self.adbwin.bind("<Key>",           self.do_event_key,                )


    #########################################################
    def atlantis_update_search_form(self, event=None):
        '''When ever someone changes the 'Site' setting on the form
        we redraw the form with the new site name. This will mainly cause the 
        database server name to change'''
        
        # Look to see if the site name is valid and look to see if has changed.
        site_from_form = self.atlantis_db.get()
        if self.atlantis_site not in ['', None] and site_from_form not in ['', None]:
            if self.atlantis_site != site_from_form:
                self.atlantis_site = site_from_form
                
                # Redraw the form but this time give it a new site name
                self.atlantis_set_dsn(self.atlantis_site)
                self.atlantis_get_parts_list(self.atlantis_site)

    #########################################################
    def atlantis_do_event_buttonrelease(self, event=None):
         
         
         if str(event.widget) == '.adbwin.adbfrm.script_list.f1.hlist':
            n = self.atlantis_session_list.info_selection()
            self.atlantis_selected_count.set('Selected: %d' % len(n))

    ##########################################################
    def atlantis_select_all_testers(self):
        '''Select all or no testers'''
        
        if self.atlantis_tester_selall_checked.get() == False:
            self.atlantis_tester_list.selection_clear()
            
        if self.atlantis_tester_selall_checked.get() == True:
            for tester in self.atlantis_testerlist:
                self.atlantis_tester_list.selection_set(tester)


    ##########################################################
    def atlantis_select_all_sessions(self):
        '''Select all or no testers'''
        
        if self.atlantis_sessions_selall_checked.get() == False:
            self.atlantis_session_list.selection_clear()
            self.atlantis_selected_count.set('Selected: %d' % 0)
        if self.atlantis_sessions_selall_checked.get() == True:
            for key in self.atlantis_search_list:
                self.atlantis_session_list.selection_set(key)
            self.atlantis_selected_count.set('Selected: %d' % len(self.atlantis_search_list))

    
    ##########################################################
    def atlantis_get_parts_list( self, site ):
        ''' Get a list of parts and testers that are available at this site database'''


        # Open up a database connection
        
        
        cnxn = self.connect(self.atlantis_dsn)
        cursor = cnxn.cursor()

        sql = r"""
          SELECT DISTINCT 
          PartNum
          FROM TestEvents
          ORDER BY PartNum
          """
        
        
        

        # Execute the database SQL query, (result is accesible through the cursor)
        cursor.execute(sql)
        # Extract the query result as a list of rows
        rows = cursor.fetchmany(4000) # limit it to 400 rows max
        parts = []
        for row in rows:
            parts.append( row[0] )

        self.atlantis_partlist = parts

        # Update the parts list
        self.atlantis_partlist.insert(0,'All Parts')
        self.atlantis_partnums['values'] = self.atlantis_partlist
        self.atlantis_partnum.set('All Parts')


        return parts




    ##########################################################     
    def atlantis_set_dsn(self, site):

        if re.match(r'San Jose',site): server = 'RFGSOSQLDB';       database = 'Atlantis-SJ'
        elif site == 'Greensboro':     server = 'RFGSOSQLDB'; database='Atlantis'
        elif site == 'Cedar Rapids':   server = 'xxxx';       database = 'xxxx'
        elif site == 'England':        server = 'xxxx';       database = 'xxxx'
        elif site == 'Phoenix':        server = 'xxxx';       database = 'xxxx'
        elif site == 'Boston':         server = 'xxxx';       database = 'xxxx'
        elif site == 'Denmark':        server = 'xxxx';       database = 'xxxx'
        elif site == 'Shanghai':       server = 'xxxx';       database = 'xxxx'
        elif site == 'Westlake':       server = 'xxxx';       database = 'xxxx'
        else:                          server = 'xxxx';       database = 'xxxx'



        self.atlantis_dsn = r'''PROVIDER=MSDASQL;
            app=pygram_dev;
            driver={SQL Server};
            server=%s;
            database=%s;
            uid=CPERptUser;
            pwd=Zlyg:@50JWJvi/]=94TGo;
            Connect Timeout=90;
            connection reset=false;
            min pool size=1;
            max pool size=50;''' % (server,database)




    ##########################################################
    def atlantis_search(self):
        '''Reads atlantis database form values and performs search based on 
        form values and finds and populates the form listbox with tests which
        match the search criteria'''
 
        # Read the search criteria values from the form and get an SQL query string
        sql = self.atlantis_get_search_sql_string()
        
        
        
        # Open up a database connection
        cnxn = self.connect(self.atlantis_dsn)
        cursor = cnxn.cursor()
        
        # Execute the database SQL query, (result is accesible through the cursor)       
        cursor.execute(sql)
        
        

        
        # Extract the query result as a list of rows
#        rows = cursor.fetchmany(400) # limit it to 400 rows max
        rows = cursor.fetchall() # limit it to 400 rows max
        # Clear any previous results from the GUI
        
        
        self.atlantis_session_list.delete_all()
        # Go through each test results row, and write the values into the scriptlist columns
        
        self.atlantis_search_list = {}
        for row in rows:
            e = '%s|%s' % ( row.Station, row.EventID )  # e is a unique index value
            self.atlantis_session_list.add(e, itemtype=Tix.TEXT, text=row.SerialNum)
            self.atlantis_session_list.item_create(e, 1, itemtype=Tix.TEXT, text='  %s' % row.EventID)
            self.atlantis_session_list.item_create(e, 2, itemtype=Tix.TEXT, text=row.TestDesc)
            self.atlantis_session_list.item_create(e, 3, itemtype=Tix.TEXT, text='  %s' % row.PartNum)
            self.atlantis_session_list.item_create(e, 4, itemtype=Tix.TEXT, text=row.TestGroup)
            timestr = time.strftime( "  %d%b%y_%H%M", datetime.datetime.timetuple(row.StartTime))
            self.atlantis_session_list.item_create(e, 5, itemtype=Tix.TEXT, text=timestr.lower())
            self.atlantis_session_list.item_create(e, 6, itemtype=Tix.TEXT, text=row.Station)
            condstr = self.atlantis_reduce_condition_str(row.CondList)
            self.atlantis_session_list.item_create(e, 7, itemtype=Tix.TEXT, text=condstr)
            self.atlantis_search_list[ e ] = [  row.SerialNum, row.EventID, row.TestDesc, row.PartNum, row.TestGroup, timestr, row.Station, condstr ] 
            
        
        self.atlantis_search_count.set(  'Found: %d    ' % len(rows))
        self.atlantis_selected_count.set('Selected: %d' % 0)
            
        # close the database once we are done
        cnxn.close()

    ############################################################################
    def atlantis_reduce_condition_str(self, full_cond_str ):
        '''Function that takes the TestEvents.CondList value in the database and
        reduces it down to a a string which only shows parameters that are varied
        ''' 
        
        condlist = full_cond_str.split(',')
        op_cond_str = ''
        seperator = ''
        for cond in condlist:
            condvals = cond.split('/')
            if len(condvals) > 2 or \
               (len(condvals) > 1 and re.search(':', condvals[1])):
                op_cond_str += '%s%s=%s' % (seperator, condvals[0], condvals[1:])
                seperator = ' ,'

        return op_cond_str
        

    ############################################################################
    def atlantis_delete_vars(self):

        del  self.atlantis_db
        del  self.atlantis_teststation
        del  self.atlantis_partnum
        del  self.atlantis_desc
        del  self.atlantis_serialnum
        del  self.atlantis_testgroup
        del  self.atlantis_datestart
        del  self.atlantis_datestop


    ############################################################################
    def atlantis_get_search_sql_string(self):
        '''Make up an SQL string to select the tests based on the Search form values'''
 



#         sql = r"""
# SELECT DISTINCT 
#   T1.EventID,
#   T1.PartNum AS 'Part Number',
#   T1.TestGroup AS 'TestGroup',
#   T1.PartRev AS 'Part Revision',
#   T1.Station AS 'Station',
#   T1.Operator AS 'Operator',
#   T1.[Descriptor],
#   T1.[Serial Number],
#   T1.[TestLibrary Name],
#   T1.[TestLibrary Version],
#   T1.LoopNum AS 'Test Loop',
#   T1.Cond0 AS 'Temperature',
#   T1.Cond1 AS 'Frequency',
#   T1.Cond2 AS 'V2G',
#   T1.Cond3 AS 'VBat',
#   T1.Cond4 AS 'Gpio',
#   T1.Cond5 AS 'Modulation',
#   T1.Cond6 AS 'Input Power',
#   T1.Cond7 AS 'LTE_Band',
#   T1.Result0 AS 'Gain (dB)',
#   T1.Result1 AS 'Forward Power (dBm)',
#   T1.Result2 AS 'Delivered Power (dBm)',
#   T1.Result3 AS 'Power In (dBm)',
#   T1.Result4 AS 'Total Power (Watts)',
#   T1.Result5 AS 'IcqV2G (mA)',
#   T1.Result6 AS 'PAE (%)'
# 
# INTO #ma024577_LUMAD01_051314_1117_Temp2
# 
# FROM 
# 
# (SELECT DISTINCT 
#   TE.EventID,
#   TE.PartNum,
#   TE.TestGroup,
#   TE.PartRev,
#   TE.Station,
#   TE.Operator,
#   H0.[AttrValue] AS 'Descriptor',
#   H1.[AttrValue] AS 'Serial Number',
#   H2.[AttrValue] AS 'TestLibrary Name',
#   H3.[AttrValue] AS 'TestLibrary Version',
#   C0.LoopNum,
#   C0.CondValue AS Cond0,
#   C1.CondValue AS Cond1,
#   C2.CondValue AS Cond2,
#   C3.CondValue AS Cond3,
#   C4.CondValue AS Cond4,
#   C5.CondValue AS Cond5,
#   C6.CondValue AS Cond6,
#   C7.CondValue AS Cond7,
#   R0.ResValue AS Result0,
#   R1.ResValue AS Result1,
#   R2.ResValue AS Result2,
#   R3.ResValue AS Result3,
#   R4.ResValue AS Result4,
#   R5.ResValue AS Result5,
#   R6.ResValue AS Result6
# 
# FROM 
#   TestEvents AS TE (NOLOCK) 
#   LEFT  JOIN AttributeData AS H0 WITH (INDEX(PK_AttributeData),NOLOCK) ON H0.EventID = TE.EventID AND H0.Attribute = 'Descriptor'
#   LEFT  JOIN AttributeData AS H1 WITH (INDEX(PK_AttributeData),NOLOCK) ON H1.EventID = TE.EventID AND H1.Attribute = 'Serial Number'
#   LEFT  JOIN AttributeData AS H2 WITH (INDEX(PK_AttributeData),NOLOCK) ON H2.EventID = TE.EventID AND H2.Attribute = 'TestLibrary Name'
#   LEFT  JOIN AttributeData AS H3 WITH (INDEX(PK_AttributeData),NOLOCK) ON H3.EventID = TE.EventID AND H3.Attribute = 'TestLibrary Version'
#   JOIN CondData AS C0 WITH (INDEX(PK_CondData), NOLOCK) ON (TE.EventID = C0.EventID AND C0.Param = 'Temperature') 
#   LEFT JOIN CondData AS C1 WITH (INDEX(PK_CondData), NOLOCK) ON (TE.EventID = C1.EventID AND C0.LoopNum = C1.LoopNum AND C1.Param = 'Frequency') 
#   LEFT JOIN CondData AS C2 WITH (INDEX(PK_CondData), NOLOCK) ON (TE.EventID = C2.EventID AND C0.LoopNum = C2.LoopNum AND C2.Param = 'V2G') 
#   LEFT JOIN CondData AS C3 WITH (INDEX(PK_CondData), NOLOCK) ON (TE.EventID = C3.EventID AND C0.LoopNum = C3.LoopNum AND C3.Param = 'VBat') 
#   LEFT JOIN CondData AS C4 WITH (INDEX(PK_CondData), NOLOCK) ON (TE.EventID = C4.EventID AND C0.LoopNum = C4.LoopNum AND C4.Param = 'Gpio') 
#   LEFT JOIN CondData AS C5 WITH (INDEX(PK_CondData), NOLOCK) ON (TE.EventID = C5.EventID AND C0.LoopNum = C5.LoopNum AND C5.Param = 'Modulation') 
#   LEFT JOIN CondData AS C6 WITH (INDEX(PK_CondData), NOLOCK) ON (TE.EventID = C6.EventID AND C0.LoopNum = C6.LoopNum AND C6.Param = 'Input Power') 
#   LEFT JOIN CondData AS C7 WITH (INDEX(PK_CondData), NOLOCK) ON (TE.EventID = C7.EventID AND C0.LoopNum = C7.LoopNum AND C7.Param = 'LTE_Band') 
#   LEFT JOIN ResultData AS R0 WITH (INDEX(PK_ResultData), NOLOCK) ON (TE.EventID = R0.EventID AND C0.LoopNum = R0.LoopNum AND R0.Param = 'Gain (dB)') 
#   LEFT JOIN ResultData AS R1 WITH (INDEX(PK_ResultData), NOLOCK) ON (TE.EventID = R1.EventID AND C0.LoopNum = R1.LoopNum AND R1.Param = 'Forward Power (dBm)') 
#   LEFT JOIN ResultData AS R2 WITH (INDEX(PK_ResultData), NOLOCK) ON (TE.EventID = R2.EventID AND C0.LoopNum = R2.LoopNum AND R2.Param = 'Delivered Power (dBm)') 
#   LEFT JOIN ResultData AS R3 WITH (INDEX(PK_ResultData), NOLOCK) ON (TE.EventID = R3.EventID AND C0.LoopNum = R3.LoopNum AND R3.Param = 'Power In (dBm)') 
#   LEFT JOIN ResultData AS R4 WITH (INDEX(PK_ResultData), NOLOCK) ON (TE.EventID = R4.EventID AND C0.LoopNum = R4.LoopNum AND R4.Param = 'Total Power (Watts)') 
#   LEFT JOIN ResultData AS R5 WITH (INDEX(PK_ResultData), NOLOCK) ON (TE.EventID = R5.EventID AND C0.LoopNum = R5.LoopNum AND R5.Param = 'IcqV2G (mA)') 
#   LEFT JOIN ResultData AS R6 WITH (INDEX(PK_ResultData), NOLOCK) ON (TE.EventID = R6.EventID AND C0.LoopNum = R6.LoopNum AND R6.Param = 'PAE (%)') 
# 
# 
# WHERE 
#     TE.[DataClass] IN ( 'Apps' ) 
#     AND TE.PartNum = 'RF3256' 
#     AND (TE.[TestGroup] IN ( 'LTE_PA_Test'))
#     AND (H1.Attribute='Serial Number' AND H1.[AttrValue] IN ( 'b15_sn027'))
#     AND (TE.StartTime BETWEEN '2013-05-08 00:00:00' AND '2014-05-15 23:59:59')
#     AND (R0.ResValue IS NOT NULL OR  R1.ResValue IS NOT NULL OR  R2.ResValue IS NOT NULL OR  R3.ResValue IS NOT NULL OR  R4.ResValue IS NOT NULL OR  R5.ResValue IS NOT NULL OR  R6.ResValue IS NOT NULL)
# 
#      ) AS T1 
# 
# WHERE (Cond5 IN ('TU005_QP_000008_00768D2', 'TU005_QP_000025_00768D2', 'TU010_QP_000012_01536D2', 'TU010_QP_000050_01536D2', 'TU020_QP_000100_03072D2')
# OR Cond5 IS NULL)
# 
# 
# ORDER BY EventID, 'Test Loop' 
# 
# OPTION(LOOP JOIN, FORCE ORDER);
# """
        # Get the search criteria values from the selection form    
        
        site            = self.atlantis_site
        Station         = self.atlantis_teststation.get().strip()
        PartNum         = self.atlantis_partnum.get().strip()
        TestDesc        = self.atlantis_desc.get().strip()
        SerialNum       = self.atlantis_serialnum.get().strip()
        TestGroup       = self.atlantis_testgroup.get().strip()
        SessionStartTime   = self.atlantis_datestart.get().strip()
        SessionFinishTime  = self.atlantis_datestop.get().strip()
        EventID         = self.atlantis_eventid.get().strip()

        # Remember the settings for next time
        self.pyconfig[ 'Atlantis_eventID' ]    = EventID
        self.pyconfig[ 'Atlantis_site' ]       = site
        self.pyconfig[ 'Atlantis_PartNum' ]    = PartNum
        self.pyconfig[ 'Atlantis_TestDesc' ]   = TestDesc
        self.pyconfig[ 'Atlantis_SerialNum' ]  = SerialNum
        self.pyconfig[ 'Atlantis_TestGroup' ]  = TestGroup
        self.pyconfig[ 'Atlantis_Station' ]    = Station
        self.save_pygram_config()
        

        # sql to get a list of column names from the TestEvents table
        sql =  """
            SELECT ORDINAL_POSITION, COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME='TestEvents'
            """

        # sql to find the tests which match 
        #  PartNumber,  SerialNum, TestGroup, Station, and Date Range
        sql = r"""
            SELECT DISTINCT 
              EventID,
              PartNum,
              TestGroup,
              PartRev,
              Station,
              Operator,
              TestDesc,
              SerialNum,
              StartTime,
              CondList
            
            FROM TestEvents
            
            WHERE 
        """
        

        sql += "StartTime BETWEEN '" + SessionStartTime + "' AND '" + SessionFinishTime + "'"
        sql += self.atlantis_add_sql_where_cond( PartNum,   'PartNum',  cond='All Parts')
        sql += self.atlantis_add_sql_where_cond( EventID,   'EventID')
        sql += self.atlantis_add_sql_where_cond( SerialNum, 'SerialNum')
        sql += self.atlantis_add_sql_where_cond( Station,   'Station'  )
        sql += self.atlantis_add_sql_where_cond( TestGroup, 'TestGroup')
        sql += self.atlantis_add_sql_where_cond( TestDesc,  'TestDesc' )
        sql += " ORDER BY StartTime "
    

        return sql

        
    ##########################################################
    def atlantis_add_sql_where_cond( self, column_id, column_str, cond = None):
        '''Create an SQL snippet to add a single WHERE filter''' 

        sql = ''
        if column_id and column_id != cond:
            column_id = re.sub('\*', '%', column_id)
            if re.search(r'\%',column_id):
                sql =  " AND %s LIKE '%s'\n" % (column_str, column_id)
            else:
                sql =  " AND %s = '%s'\n" %    (column_str, column_id) 

        return sql
        
    ##########################################################
    def atlantis_load_all_sessions_arg(self, dummy_arg=None):
        '''Add selected tests to the ARG form'''

        n = self.atlantis_session_list.info_selection()

        # don't add the file if its there already
        lball = self.atrlogfiles_listbox.get(0, Tk.END )

        if len(n) > 0 :
            for r in n:
                r = 'Constellation|' + r
                fnd_file = False
                for n in lball:
                    if n == r:  fnd_file = True
                if not fnd_file:
                         self.atrlogfiles_listbox.insert( Tk.END, r )

        self.atlantis_db_loaded = True

        self.adbwin.destroy()

    ##########################################################
    def atlantis_load_all_sessions(self, dummy_arg=None):
        '''Loads all the selected tests from the atlantis Test Selection form into
        Pygram self.data'''
        
        n = self.atlantis_session_list.info_selection()

        # Open up a database connection
        cnxn = self.connect(self.atlantis_dsn)
        cursor = cnxn.cursor()

        if len(n) > 0 :
            for r in n:
                self.atlantis_load_session(cursor, r)

        # close the database once we are done
        cnxn.close()

        self.win_load()

        # prints out all the available column names (useful when defining the conditions)
        self.print_column_list()                    
        self.print_values_list()
        self.done_list_columns = True
        self.gen_values_dict()
        self.status.set( 'waiting for user input' )
        self.root.update()

        self.atlantis_db_loaded = True

        self.adbwin.destroy()

    ##########################################################
    def atlantis_load_session(self, cursor, key):
        '''Loads all the selected tests from the atlantis Test Selection form into
        Pygram self.data'''


        # Get the tester and session keys so that we can select the full 
        # test results for this test        
        try:
           key = re.sub('^Constellation\|', '' , key)
           [(Station,EventID)] = re.findall(r'(.*)\|(\d+)$', key)
        except (ValueError,TypeError):
            print "*** Error *** (atlantis_load_session) bad atlantis DB selection key '%s'" % key
            return



#        search_row = self.atlantis_search_list[key]
#         logfilename = '%s_%s_%s' % ( search_row[3], search_row[0], search_row[1] )
#         logfilename = re.sub(r'\s+','',logfilename)

        rn_start = self.datacount
#        EventID, PartNum = search_row[1], search_row[3]
        self.atlantis_load_test(cursor, EventID, mode='full_load' )

        return

    ##########################################################
    def  atlantis_load_test(self, cursor, eventid, logfilename=None, mode='no_sweepdata'):
        '''Load the results for a single EventID'''


        self.freq_mult = 1

        # Go into each of the Atlantis Database tables and read the data available for this EventID
        tevnames, test_events_data, partnum, serialnum, testdesc = self.atlantis_get_table_data(cursor, eventid, 'TestEvents')

        # Make up a log name based on the partnumber serialnum and eventid 
        if logfilename == None:
           logfilename = '%s_%s_%s_%s' % ( partnum, serialnum, testdesc, eventid )
           logfilename = re.sub(r'\s+','',logfilename)
        self.status.set( 'Loading Atlantis Database results for %s' % logfilename )

        attribnames, attribute_data = self.atlantis_get_attribute_table_data(cursor, eventid, 'AttributeData' )
        condnames, cond_data, rlen  = self.atlantis_get_loopnum_table_data(cursor, eventid, 'CondData' )
        resnames, result_data, rlen = self.atlantis_get_loopnum_table_data(cursor, eventid, 'ResultData' )

        # Give the user the option not to load the full sweep data, as this may be too large. 
        if mode.lower() == 'full_load':
            sweep_data, sweep_rlen = self.atlantis_get_sweepdata_table_data(cursor, eventid, partnum )
        else:
            sweep_data = {}
            sweep_rlen = 0
            
        
        rn_start = self.datacount
        
        # Update the Pygram data dict with all the database values
        self.atlantis_add_to_main_data_dict(    \
                    test_events_data, \
                    attribute_data,   \
                    cond_data,        \
                    result_data,      \
                    rlen,             \
                    sweep_data,       \
                    sweep_rlen,       \
                    logfilename,      \
                    )

        # Then add a few bits of static data that were not available in the last query
        rn_finish =  self.datacount
        self.atlantis_add_misc_columns(rn_start, rn_finish, logfilename )

        self.logfile_type = 'atlantis_db'
        
        # Make all columns the same length
        for col in self.data:
            self.add_new_column(col)
        
        # Add the extra columns that Pygram normally fudges such as Pout(dBm) etc
        self.add_missing_columns( rn_start, rn_finish)

        # Update the main pygram gui tabs 
        self.logfiles.insert( Tk.END, self.get_filename_from_fullpath( logfilename ) + ' (%s)' % (rn_finish-rn_start))
                           
        return  eventid, partnum


    ############################################################################
    def atlantis_get_table_data(self, cursor, EventID, table):
        '''Get the column names and the data for the table name, and matching EventID
        '''
        # THINK ABOUT REMOVING THE COLUMN NAME SEARCH AND REPLACING WITH A 
        # HARD CODED COLUMN LIST
        # Get list of TestEvent Column names
        sql =  """
            SELECT ORDINAL_POSITION, COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME='%s'
            """ % (table)
        cursor.execute(sql)
        rows = cursor.fetchall() 
        columns = []
        for i,r in enumerate(rows):
            columns.append(r[1])

        sql = """
            SELECT DISTINCT * FROM %s
            WHERE EventID = %s
            """ % (table, EventID)
        cursor.execute(sql)
        rows = cursor.fetchall() 
        data = {}        
        for i,r in enumerate(rows):
            for j,d in enumerate(r):
                data[ columns[j] ] = d
       
        return  columns, data, data['PartNum'], data['SerialNum'], data['TestDesc']



    ############################################################################
    def atlantis_get_attribute_table_data(self, cursor, EventID, table):
        '''Get the column names and the data for the AttributeData table, and matching EventID
        '''

        sql = """
            SELECT DISTINCT Attribute,AttrValue 
            FROM %s
            WHERE EventID = %s 
            ORDER BY Attribute
            """ % (table, EventID)
        cursor.execute(sql)
        rows = cursor.fetchall() 
        data = {}
        params = []
        for i,r in enumerate(rows):
            param   = r[0]
            value   = r[1]
            data[param] = value
            params.append(param)
            
        return  params, data

    ############################################################################
    def atlantis_get_loopnum_table_data(self, cursor, EventID, table):
        '''Get the column names and the data for the table name, and matching EventID
        '''

        if table == 'ResultData':
            valuename = 'ResValue'
        elif  table == 'CondData':
            valuename = 'CondValue'

        sql = """
            SELECT DISTINCT LoopNum,Param,%s 
            FROM %s
            WHERE EventID = %s 
            ORDER BY LoopNum, Param
            """ % (valuename, table, EventID)
        cursor.execute(sql)
        rows = cursor.fetchall() 
        data = {}
        params = []

        if len(rows) > 0:
            # Get the number of LoopNums, so that we know how big to make the result lists for each parameter.
            # The query returns the data ordered by LoopNum, therefore the highest LoopNum
            # must be in the last row, and smallest in the first row
            max_loopnum = int(rows[-1][0])
            min_loopnum = int(rows[0][0])
            len_loopnum = max_loopnum - min_loopnum + 1

            for i,r in enumerate(rows):
                loopnum = r[0]
                param   = r[1]
                value   = r[2]
                if param not in data:
                    data[param] = [None] * (len_loopnum)
                    params.append(param)
                data[param][loopnum - min_loopnum] = value
            
        if len(rows) > 0:
            param_len = len_loopnum
        else:
            param_len = 0
            
        return  params, data, param_len
        
    ############################################################################
    def atlantis_get_sweepdata_table_data(self, cursor, EventID, PartNum):
        '''Get the column names and the data for the SweepData table, and matching EventID, and PartNum
        '''
        
        sql = """
            SELECT DISTINCT CondData.LoopNum, SweepParams.TestName,  SweepData.ArrayPoint, SweepData.XValue,  SweepData.YValue, SweepData.ZValue, SweepParams.XParam,  SweepParams.YParam, SweepParams.ZParam
            FROM  TestEvents
               INNER JOIN SweepData ON SweepData.EventID=TestEvents.EventID 
               INNER JOIN CondData ON CondData.EventID=TestEvents.EventID and SweepData.LoopNum = CondData.LoopNum
               INNER JOIN SweepParams ON SweepParams.SweepID=SweepData.SweepID 
            WHERE TestEvents.EventID=%s and SweepParams.PartNum='%s' 
            ORDER BY CondData.LoopNum, SweepParams.TestName, SweepData.ArrayPoint
            """ % (EventID, PartNum)
        cursor.execute(sql)
        rows = cursor.fetchall() 
        sweep_data = {}

        if len(rows) > 0:
            # Get the number of LoopNums, so that we know how big to make the result lists for each parameter.
            # The query returns the data ordered by LoopNum, therefore the highest LoopNum
            # must be in the last row, and smallest in the first row
            max_loopnum = int(rows[-1][0])
            min_loopnum = int(rows[0][0])
            len_loopnum = max_loopnum - min_loopnum + 1

            for i,r in enumerate(rows):
                LoopNum    = r[0]
                TestName   = re.sub('\.','',r[1])
                TestName_x = '%s %s' % (TestName, r[6])
                TestName_y = '%s %s' % (TestName, r[7])
                TestName_z = '%s %s' % (TestName, r[8])
                ArrayPoint = r[2]
                if 'XValue' not in sweep_data:
                    sweep_data['XValue'] = {}
                    sweep_data['YValue'] = {}
                    sweep_data['ZValue'] = {}

                if TestName_x not in sweep_data['XValue']:
                    sweep_data['XValue'][TestName_x] = [None] * len_loopnum
                    sweep_data['YValue'][TestName_y] = [None] * len_loopnum
                    sweep_data['ZValue'][TestName_z] = [None] * len_loopnum

                data[param][loopnum - min_loopnum] = value
                sweep_data['XValue'][TestName_x][Loopnum - min_loopnum] = r[3]
                sweep_data['YValue'][TestName_y][Loopnum - min_loopnum] = r[4]
                sweep_data['ZValue'][TestName_z][Loopnum - min_loopnum] = r[5]
            
        if len(rows) > 0:
            sweep_length = len_loopnum
        else:
            sweep_length = 0
            
        return  sweep_data, sweep_length

    ############################################################################
    def  atlantis_add_to_main_data_dict( self, test_events_data, attribute_data,
                                        cond_data, results_data, data_length, 
                                        sweep_data, sweep_length,  logfilename):
        
        if data_length == 0 and sweep_length == 0:
            return


        # Figure out how many records we want to add
        # This is either data_length or sweep_length if we are doing a sweep test
        rn_start = self.datacount
        if sweep_length == 0:
            rn_finish = rn_start + data_length
            sweep_inc = 1                     
        else:
            rn_finish = rn_start + sweep_length
            sweep_inc = sweep_length/data_length  # The number of arraypoints in each sweep (number of frequency points in an s2p test)
        self.datacount = rn_finish


        # TestEvents data is Static it does not change within the same EventID
        # So write the same value into each record that has the same EventID
        for colr in test_events_data:
            col = re.sub('\.', '_', colr)
            self.add_new_column(col)
            for rn in range(rn_start, rn_finish):
                val = test_events_data[col]
                try:
                    val = float(val)
                except:
                    pass
                self.data[col][rn] = val

                
        # AttributeData data is Static it does not change within the same EventID
        for colr in attribute_data:
            col = re.sub('\.', '_', colr)
            self.add_new_column(col)
            for rn in range(rn_start, rn_finish):
                val = attribute_data[colr]
                try:
                    val = float(val)
                except:
                    pass
                self.data[col][rn] = val


        # CondData changes from one record to the next
        # Write a different condition for each test measurment
        for colr in cond_data:
            col = re.sub('\.', '_', colr)
            self.add_new_column(col)
            i = 0
            for rn in range(rn_start, rn_finish):
                val = None
                try:
                    val = cond_data[colr][i]
                    val = float(val)
                except:
                    pass
                self.data[col][rn] = val
                i = (rn+1 - rn_start)/sweep_inc

        
        if data_length > 0:
            for colr in results_data:
                col = re.sub('\.', '_', colr)
                self.add_new_column(col)
                i = 0
                for rn in range(rn_start, rn_finish):
                    val = results_data[colr][i]
                    try:
                        val = float(val)
                    except:
                        pass
                    self.data[col][rn] = val
                    i = (rn+1 - rn_start)/sweep_inc


        # If we have Sweep data, go through the list of sweep_data breaking out
        # the different testnames and different 'XValue','YValue','ZValue'
        if sweep_length > 0:
            # Go through all the X,Y,Zvalues for each of the sweep TestNames
            # and create a seperate column for each of them
            valnames = ['XValue','YValue','ZValue']
            for valname in valnames:
                for testname in sweep_data[valname]:
                    colname = 'sweep %s %s' % (testname, valname)
                    self.add_new_column( colname )
                    # Go through the LoopNum's and ArrayPoint's for the column
                    # and copy the sweep_data
                    i = 0
                    for loop in range(data_length):
                        for arraypoint in range(sweep_inc):
                            self.data[colname][i+rn_start] = sweep_data[valname][testname][i]                                        
                            i += 1        

        return        

    #################################################################################################################
    def atlantis_add_misc_columns( self, rn_start, rn_finish,logfilename ):
        '''Add misc data columns to self.data'''
        

        self.add_new_column( 'logfilename' )
        self.add_new_column( 'record_num' )
        
        for rn in range(rn_start,rn_finish):
            self.data[ 'logfilename' ][rn]   = logfilename
            self.data[ 'record_num' ][rn]    = rn

        return

       



    ############################################################
    def atlantis_count_test_rows( self, cursor, key):
        '''Get a count of the number of individual tests for this testplan session'''
        
        search_row = self.atlantis_search_list[key]
        EventID   = search_row[1]

        sql = '''SELECT COUNT(*) from ResultData
            WHERE EventID = %s''' % EventID

        cursor.execute(sql)
        
        # Extract the query result as a list of rows
        rows = cursor.fetchmany(400) # limit it to 400 rows max

        if len(rows) == 1:
            return rows[0]
        else:
            print "*** Error *** (atlantis_count_test_rows) bad atlantis DB data '%s'" % rows
            return None
        

        
    ############################################################
    def atlantis_get_test_columns( self, cursor, key):
        ''' Get a list of column heading names for this testplan session '''


        search_row = self.atlantis_search_list[key]
        EventID   = search_row[1]

        sql = '''SELECT DISTINCT Param
                 FROM CondData
                 WHERE EventID = %s
            '''  % ( EventID )

        cursor.execute(sql)
        
        # Extract all the column data
        rows = cursor.fetchall() # limit it to 400 rows max

        # Build the list containing the column names
        CondColumns = []
        for r in rows:
           CondColumns.append(r[0])



        sql = '''SELECT DISTINCT Param
                 FROM ResultData
                 WHERE EventID = %s
            '''  % ( EventID )

        cursor.execute(sql)
        
        # Extract all the column data
        rows = cursor.fetchall() # limit it to 400 rows max

        # Build the list containing the column names
        ResultColumns = []
        for r in rows:
           ResultColumns.append(r[0])


        sql = '''SELECT DISTINCT Attribute
                 FROM AttributeData
                 WHERE EventID = %s
            '''  % ( EventID )

        cursor.execute(sql)
        
        # Extract all the column data
        rows = cursor.fetchall() # limit it to 400 rows max

        # Build the list containing the column names
        AttributeColumns = []
        for r in rows:
           AttributeColumns.append(r[0])


        return  CondColumns, ResultColumns, AttributeColumns


    ##########################################################
    #### END OF ATLANTIS DB FUNCTIONS  #######################
    ##########################################################


#####################################################################################
#### Configuration Functions
#####################################################################################
    def read_pygram_config( self, param=None, config_file=None ):
         '''Reads PYGRAM configuration data from the config file
         
         Parameter:
              param:   Key name , if None then it reads all the parameters in the config file
         Returns:
              Value of param
         Reads:
              File self.pyconfig_file
         '''


         fip = None
         try:
             if config_file == None:
                cfile = self.pyconfig_file
                fip = open( cfile )
             else:
                cfile = config_file
                fip = open( cfile )
         except: pass
    
         if fip:
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



         else: 
            print "*** warning *** (read_pygram_config) unable to read pygram configuration file '%s'" % cfile


         if param != None and param in self.pyconfig:
#            print "      .(read_pygram_config) reading config param ( %s = %s ) in file '%s'" % (param,self.pyconfig[ param ],self.pyconfig_file)
            return self.pyconfig[ param ]
         else:

            return ''


#####################################################################################
    def save_pygram_config( self, param=None, value=None, filename=None ):
         '''Updates PYGRAM configuration data in the config file
         
         Parameter:
              param:   Key name,  if param is None it save the ini file with no changes.
              value:   Value of param
         Returns:
              None
         Updates:
              File self.pyconfig_file
         '''


#         self.read_pygram_config()

         if param != None:
             value = str(value)
             self.pyconfig[ param ] = value

         if filename == None:
             fop = open( self.pyconfig_file, 'w' )
         else:
             fop = open( filename, 'w' )

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
                              'arg_process_multiparts',
                              'copy_atrlogfiles_on',
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

      Tk.Button( gipfrm, name='arg_browse_atlantis_button', text="Browse\nConst\nDB",   width=7  ) .grid( row=i+1, column=2,sticky=Tk.N )
      Tk.Button( gipfrm, name='arg_browse_mercury_button', text="Browse\nMercury\nDB",   width=7  ) .grid( row=i+2, column=2,sticky=Tk.N )
      Tk.Button( gipfrm, name='atr_remove_selected_button', text="Remove\nSelected",   width=7  ) .grid( row=i+3, column=2,sticky=Tk.N )
      Tk.Button( gipfrm, name='atr_remove_all_button',      text="Remove\nAll",   width=7  )      .grid( row=i+4, column=2,sticky=Tk.N )

      name =  'copy_atrlogfiles_on'
      self.gip[ name ]   = Tk.IntVar(master=gipfrm)
      Tk.Label( gipfrm, text='Copy\nLogfiles:' )                                                     .grid( column=2, row=i+5,sticky=Tk.S)
      Tk.Checkbutton( gipfrm, name='%s_entry' % name , variable=self.gip[ name ] )                   .grid( column=2, row=i+6,sticky=Tk.N)


      gipatrfrm = Tk.Frame(gipfrm, name='gipatrfrm')
      scrollbar = Tk.Scrollbar(gipatrfrm, orient=Tk.VERTICAL)
      self.atrlogfiles_listbox   = Tk.Listbox(gipatrfrm, name='lb', width=148, height=15, yscrollcommand=scrollbar.set,selectmode=Tk.EXTENDED)
      scrollbar.config(command=self.atrlogfiles_listbox.yview)
      self.atrlogfiles_listbox.grid  (column=1, row=0, sticky='w' )
      scrollbar.grid(column=2, row=0, sticky='wns' )

      gipatrfrm.grid( row=i+1, rowspan=4, column = 1 )

      i += 7
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

#       name =  'run_refpout_from_vrampsearch'
#       self.gip[ name ]   = Tk.IntVar(master=gipfrm)
#       Tk.Label( gipfrm, text='Use Vramp Search\nto calc\nRef Pout(dBm):' )                                 .grid( column=2, row=i+1,sticky=Tk.S)
#       Tk.Checkbutton( gipfrm, name='%s_entry' % name , variable=self.gip[ name ] )                         .grid( column=2, row=i+2,sticky=Tk.N)

      name =  'arg_process_multiparts'
      self.gip[ name ]   = Tk.IntVar(master=gipfrm)
      Tk.Label( gipfrm, text='Run\nMultiple\nParts' )                                 .grid( column=2, row=i+1,sticky=Tk.S)
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
      Tk.Button( gipbtnfrm, text="Run",    width=7,    command=self.get_arg_user_inputs_dialog_run    ) .grid( row=0, column=1 )
#      Tk.Button( gipbtnfrm, text="Run (No Load)", width=12, command=self.get_arg_user_inputs_dialog_run_nologfiles )    .grid( row=0, column=2 )
      Tk.Button( gipbtnfrm, text="Cancel", width=7,    command=self.get_arg_user_inputs_dialog_cancel ) .grid( row=0, column=3 )
      Tk.Button( gipbtnfrm, text="Preload Form", width=12, command=self.get_arg_user_inputs_dialog_preload )    .grid( row=0, column=4 )
      Tk.Button( gipbtnfrm, text="Run NoLoad", width=12, command=self.get_arg_user_inputs_dialog_run_noload )    .grid( row=0, column=5 )
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

    def get_arg_user_inputs_dialog_preload(self):
         
      directory = r'L:\Lab & Testing\Test Scripts\Pypat Verification\Regressions\results'
      ini_filename = askopenfilename( defaultextension='.ini',
                                     initialdir=directory,
                                     title='Select ini File to Load',
                                     multiple=False,
                                     filetypes=[('all', '*.*'),('ini', '*.ini')] )

      # Fill the form with the values from the previous run (values stored in the pygram config file)
      
      
      self.read_pygram_config( config_file=ini_filename)
      self.save_pygram_config()
      self.read_arg_user_inputs_config()



    #---------------------------------------------------------------------------------
    def get_arg_user_inputs_dialog_run(self):
       '''Function is run when the Run button is pressed. With all the values entered into the form
       It sets the main valiables required by the ARGPRD script, and saves the values in the config file.
       It uses the argscript file and run the argscript using execfile().
       '''

       # Start the run with a completely clean slate, (clear everything that moves)
       self.wclearfiles()
       self.arg_noload_logfiles = False

       self.argscript   =  self.get_arg_user_inputs_do_entry( event= 'argscript' ).strip()
       self.prdfile     =  self.get_arg_user_inputs_do_entry( event= 'prdfile'   ).strip()
       self.savedir     =  self.get_arg_user_inputs_do_entry( event= 'resdir'    ).strip()
       self.arg_runmode =  self.gip['runmode'].get()
       self.arg_testnum =  self.get_arg_user_inputs_do_entry( event= 'testnum'   ).strip()
       self.copy_atrlogfiles = self.gip['copy_atrlogfiles_on'].get()
#       self.run_refpout_from_vrampsearch = self.gip['run_refpout_from_vrampsearch'].get()
       self.arg_process_multiparts = self.gip['arg_process_multiparts'].get()

       if self.run_refpout_from_vrampsearch:
          self.vramp_search_testname = self.vramp_search_testname_good
       else:
          self.vramp_search_testname = self.vramp_search_testname_bad
   
       self.arg_parent = 'interactive'



       # Read the list of atr logfiles
       self.arg_logfiles = self.atrlogfiles_listbox.get(0, Tk.END )
       
       self.get_arg_user_inputs_dialog_run_core()

    #---------------------------------------------------------------------------------
    def get_arg_user_inputs_dialog_run_noload(self):
       '''Function is run when the Run button is pressed. With all the values entered into the form
       It sets the main valiables required by the ARGPRD script, and saves the values in the config file.
       It uses the argscript file and run the argscript using execfile().
       '''

       # Start the run with a completely clean slate, (clear everything that moves)
#       self.wclearfiles()

       self.argscript   =  self.get_arg_user_inputs_do_entry( event= 'argscript' ).strip()
       self.prdfile     =  self.get_arg_user_inputs_do_entry( event= 'prdfile'   ).strip()
       self.savedir     =  self.get_arg_user_inputs_do_entry( event= 'resdir'    ).strip()
       self.arg_runmode =  self.gip['runmode'].get()
       self.arg_testnum =  self.get_arg_user_inputs_do_entry( event= 'testnum'   ).strip()
       self.copy_atrlogfiles = self.gip['copy_atrlogfiles_on'].get()
#       self.run_refpout_from_vrampsearch = self.gip['run_refpout_from_vrampsearch'].get()
       self.arg_process_multiparts = self.gip['arg_process_multiparts'].get()

       if self.run_refpout_from_vrampsearch:
          self.vramp_search_testname = self.vramp_search_testname_good
       else:
          self.vramp_search_testname = self.vramp_search_testname_bad
   
       self.arg_parent = 'interactive'



       # Read the list of atr logfiles
       self.arg_logfiles = self.atrlogfiles_listbox.get(0, Tk.END )
       
       self.arg_noload_logfiles = True
       self.get_arg_user_inputs_dialog_run_core()

       
    #--------------------------------------------------------------------------------------------------------   
    def get_arg_user_inputs_dialog_run_core(self, exit=False ):
    
    
       self.exit_after_processing=exit
       self.run_mode = 'script'    
       lball = self.arg_logfiles
    
       # Color the golden unit log 'golden'
       
       new_arg_logfiles = []
       for n in self.arg_logfiles:
            new_arg_logfiles.append(n)
       
       self.arg_logfiles = new_arg_logfiles
        
       for n in self.arg_logfiles:
             if 'golden' in n.lower():
                # remove this 'golden' n from the arg_logfiles and add it to the beginning of the list 
                # also revove the yellow color from the color list and add this to the beginning    
                self.arg_logfiles.remove(n)
                new_arg_logfiles = [n]
                new_arg_logfiles.extend(self.arg_logfiles)
                self.arg_logfiles = new_arg_logfiles

                if 'y' in self.color_list:
                    self.color_list.remove('y')
                    color_list_no_yellow = self.color_list
                    color_list_yellow = ['y']
                    color_list_yellow.extend(color_list_no_yellow)
                    self.color_list = color_list_yellow
                    self.update_entry_box( self.color_list, self.wcolor_list )
                    
                break
    
       # join all the files together into a multiline string (concatenate the files with \n)
       self.atr_logfiles = []
       for n in self.arg_logfiles:
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
                tstr = re.sub( '[,;]', ' ', self.arg_testnum.strip() )  # change any ',' delimiter to a space delimiter
                tstr = tstr.upper()
                self.arg_testnum_list =  tstr.split()                # split using the ' ' space character delimiter

                # Print warning if we don't have any valid test ID numbers specified
                if len( self.arg_testnum.strip() ) == 0 or len( self.arg_testnum_list ) == 0:
                    num_warnings += 1
                    showwarning('', "'Run List of Tests' was specified but no Test ID Numbers have been entered.\nPlease enter one or more valid Test ID Numbers (which must match the Test ID Number used in the PRD" )


       if self.arg_parent == 'interactive':
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


       if self.arg_parent == 'interactive':
           self.gipwin.destroy()
       
       self.win_load()

       # Run the Script File
       execfile( self.argscript, globals(), locals() )

       # get rid of any xlims and ylims
       self.set_xyaxes_limits()   # reset the axes
       self.set_spec_limits()     # reser the spec limits

       self.arg_noload_logfiles = False

 
       ini_file = os.path.join( self.savedir, 'arg.ini')
       self.save_pygram_config(filename=ini_file)

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
           elif entry_name == 'arg_browse_atlantis':
                self.atlantis_load_db(update_form='argform')
                entry_name = 'atrfile'
                return
           elif entry_name == 'arg_browse_mercury':
                self.mercury_load_db(update_form='argform')
                entry_name = 'atrfile'
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
       populates the ARG from

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

#        if 'gip_run_refpout_from_vrampsearch' not in self.pyconfig:
#             self.gip[ 'run_refpout_from_vrampsearch' ].set( 0 )


       if 'gip_runmode' not in self.pyconfig:
            self.gip[ 'runmode' ].set( 'all' )

       if 'arg_process_multiparts' not in self.pyconfig:
            self.gip[ 'arg_process_multiparts' ].set( 0 )

#####################################################################################
    def get_arg_parts_list_files(self):
        '''Return a list of filenames for each part so that multiple parts can 
        be processed one at a time.

        If the arg_process_multiparts flag is set then:
        The self.arg_logfiles list is examined, and each filepath is examined to
        find the base directory, and a list of logfiles which match _SNxxx_ 
        pattern. From this a list is created
        #               part        logfiles for part          save directory
        part_list = [  ['sn001',  ['c:/pwr_sn001.log', ...], 'L:/CMOS_PA/DVT/sn001'], 
                       ['sn002',  ['c:/pwr_sn002.log', ...], 'L:/CMOS_PA/DVT/sn002'],]
        
        If the arg_process_multiparts is not set then a single part list is 
        returned containing the original logfiles and savedir
        '''
        
        # If we are not doing multi part processing return with the original 
        # list of logfiles
        if not self.gip['arg_process_multiparts'].get():
            part_list = [[ '?', self.atr_logfiles, self.savedir]]
            return part_list
        
        
        part_list = []
        parts = []
        dirnames = []
        logfiles = []        
        
        
        # get a list of part and directory names

        for f in self.atr_logfiles:            
            
            dirname = os.path.split(f)[0]
            if dirname not in dirnames:
                dirnames.append(dirname)
            if re.search('.log$', f, re.I):
                logfiles_in_dir = glob.glob( r'%s/*.log' % dirname )
            elif  re.search('.s2p$', f, re.I):     
                logfiles_in_dir = glob.glob( r'%s/*.s2p' % dirname )
            
            for logfile in logfiles_in_dir:
                logfile_root = os.path.split(logfile)[0]
                logfile_name = os.path.split(logfile)[1]
                part = re.findall('_sn0*(\d+)[._]',logfile_name, re.I)
                if len(part) == 1:
                    if part[0] not in parts:
                        parts.append(part[0])
                    if logfile not in logfiles:
                        logfiles.append(logfile)
        
        # now we have a list of:
        #    parts:  part number,
        #    dirnames:  directories where the log files are located
        #    logfiles:  all logfiles that have matching part numbers
        
        # go through each of the part numbers and build our parts_list
        for cur_part in parts:
            cur_part_logfiles = []
            for logfile in logfiles:
                logfile_name = os.path.split(logfile)[1]
                part = re.findall('_sn0*(\d+)[._]',logfile_name, re.I)[0]
                if part == cur_part:
                    cur_part_logfiles.append(logfile)
            cur_part_savedir = os.path.join( self.savedir, 'SN%s' % (cur_part))
            part_list.append([ cur_part, cur_part_logfiles, cur_part_savedir])
    
        return part_list
            # get the fileroot



    #######################################################################################################################
    def create_offset_target(self, target, minmax):
        '''Create new target line, which is offset from the input
        #   [ [1500,-3],   [1650,-3], ]    <- input target
        #   [ [1500,-3.2], [1650,-3.2] ]   <- ouput offset target
        '''

        yoffset = (self.ylimits[1] - self.ylimits[0]) / 50.0
        xoffset = (self.xlimits[1] - self.xlimits[0]) / 50.0

        dx = (target[1][0] - target[0][0])/xoffset    # x delta expressed as a fraction of xaxis range
        dy = (target[1][1] - target[0][1])/yoffset

        # Calculate the angle of the line
        # ang = 0 for horizontal lines dx/r = 1 -> acos(1) = 0 deg
        ang = ango = math.atan2(dy,dx)

        # Rotate by +/-90deg (the shaded line is points are offset 90deg relative to the original line)
        # The sign of the rotation depends on whether we are doing a '>' or '<'
        if  minmax.lower() == '<':
            if dx > 0:
                ang += pi/2.
            else:
                ang -= pi/2.
        else:
            if dx > 0:
                ang -= pi/2.
            else:
                ang += pi/2.

        # print target, minmax, (ang)*(180/pi), (ang-ango)*(180/pi),  dx, dy


        yofs =  math.sin(ang) * yoffset    # a horizontal delta (dx) results in a y offset
        xofs =  math.cos(ang) * xoffset    # a vertical delta (dy) results in an x offset

        new_target = []
        i = 0
        for point in target:
            if isinstance(point, types.StringTypes):   # skip over any text options
                continue
            new_target.append([point[0] + xofs, point[1] + yofs])

        return new_target


    #######################################################################################################################
    def plotdata(self, xynames, xlim=None, ylim=None, title=None, speclim=None, y2lim=None):
        '''Function to plot the data, setup the axes, and measure the results'''

        self.xlimits = xlim
        self.ylimits = ylim
        self.y2limits = y2lim

        if speclim == [] or speclim != None:
            self.define_spec_limits(speclim)

        xyd = self.plot_graph_data(xynames, titletxt=title, savefile=title)
        return xyd

    #######################################################################################################################
    def define_spec_limits( self, target=None, text='', color='red', minmax='x' ):
        '''Defines a set of spec limits from parameter 'target' which are drawn on the plot.

        This fucntion translates a target definition of the spec limits into
        the lower level self.spec_limit definition.

        The target can have the following different formats:

        target = -50
        target = '> -56 Limit of ACPR green'
        target = [ [23,-48],[27,-50], '> green Mikes Limit' ]
        target = [[[18, -34],   [19, blim], '< red'],
                  [[19, -34],   [20, -38], 'cyan'],
                  [[20, -40],   [20, -38], ], ]
        target = []
        target = None

        If the target is a number (either a float or int) then a horizontal line is drawn
        in across the graph at the y value of the number.

        If the value is a string it is split into a space seperated list of words which
        which includes the Y value of the spec line, and option words to specify the color
        the greater/lessthan indicator and text placed on the line

        The target may be a 2 or 3 element list defining a single spec line with start point
        and end point and an optional string. The string contains anotation text and color
        and greater/less than indicator.

        The target may also be a list of spec lines with each line defined as above.

        When options string is present in the above list format as the third item of a spec line
        It consists of a space seperated list of words.
        A word which is a color is recognized as the color of the line
        A word which is '<' '>' or 'x' is recognized as the greater than or less than
        indicator with a shaded region placed above or below the line. An 'x' indicates
        no shading.
        All other words in the options string are the annotation text that is added to the
        line as an annotations. The greaterthan/lessthan and the color words are removed
        and do not appear in the anotated text.

        When multple spec lines are defined the option str parameters are 'remembered' from
        one line to the next. So the color need only be defined on the first spec line,
        all subsequent spec lines will use the same color if the color is not defined.
        The same applies to the greater/lessthan indicators

        If target is an empty list , this will remove all self.spec_limits from the graph

        If target is None, the self.spec_limit is left as is, so the previous spec_limits
        definition will be reused on the next plot
        '''

        # table of colors for the light shading regions for greater/lessthan spec limits
        # they are lighter versions of the same base color
        color_shade_tab = {
            'red'    : '#FFEEEE',
            'green'  : '#EEFFEE',
            'blue'   : '#EEEEFF',
            'cyan'   : '#E7FFFF',
            'magenta': '#FFEEFF',
            'black'  : '#EEEEEE',
            'yellow' : '#FFFFE7'
        }

        if target == []:
            self.spec_limits = None
        elif target != None:

            self.spec_limits = []
            color_shade = color_shade_tab[color]

            if not isinstance(target, types.ListType)  and \
               not isinstance(target, types.TupleType) :

               # if the target is string split it up into words
               # and identify the colors Y limit value, and minmax
               if isinstance(target, types.StringTypes):
                    target_str = target
                    wds = target_str.split()
                    found_limit = False
                    wdsn = wds[:]
                    for wd in wds:
                        if wd.lower() in color_shade_tab.keys():
                            color = wd.lower()
                            wdsn.remove(wd)
                        if wd in ['x', '<', '>']:
                            minmax = wd
                            wdsn.remove(wd)
                        if found_limit == False:
                            try:
                                x = float(wd)
                                found_limit = True
                                target = x
                                wdsn.remove(wd)
                            except ValueError :
                                pass

                    text = ' '.join(wdsn)

               target = [ [g.xlimits[0],target], [g.xlimits[1],target],
                          '%s %s %s' % (minmax,color, text) ]


            # Put the target into a sub list if target[0][0] is not a two element list
            try:
                x = len(target[0][0])
                if x != 2:
                    target = [ target ]
            except TypeError:
                target = [ target ]

            for tg in target:
                tgn = tg[:]
                text = ''

                if len(tg)> 2 and isinstance(tg[2], types.StringTypes):
                    opts = tg[2].split()
                    optslwr = tg[2].lower().split()
                    # get the minmax value
                    for mm in ['x','<','>']:
                        if mm in optslwr:
                            minmax = mm
                            idx = optslwr.index(mm)
                            del opts[idx]
                            optslwr.remove(mm)
                            break
                    # get the color
                    for clr in ['red', 'green', 'blue', 'cyan', 'magenta', 'black', 'yellow' ]:
                        if clr in optslwr:
                            color = clr
                            color_shade = color_shade_tab[color]
                            idx = optslwr.index(clr)
                            del opts[idx]
                            optslwr.remove(clr)
                            break
                    text = ' '.join(opts)
                    tgn.remove(tg[2])


                if minmax in ['>','<']:
                    tg_shaded = self.create_offset_target(tg, minmax)
                    self.spec_limits.append([tg_shaded, text, 20, '%s %s' % (color_shade, color)])
                    text = ''

                self.spec_limits.append([tgn, text, 3, color])
        else:
            self.spec_limits = None


    def set_color(self, column ):
        self.color_series.set( column  )
    def set_line(self, column ):
        self.line_series.set( column  )

    ############################################################################
    def read_board_loss_files( self, board_loss_files ):
        '''Function that reads in a list of s2p files for board trace loss
        and creates a separate self.board_trace_data[ <port> ] structure
        for each port. This structure is the same as a regular self.data
        used for the main measurement data.
        
        Note: This function will overwrite the self.data structure
        so run this function before reading in any of the regular
        ATR measurement files
        '''
        
        
        
        self.board_loss_data = {}
        
        dirroot =  board_loss_files['directory']
        # 
        for k in board_loss_files:
            if k != 'directory':
                self.wclearfiles()
                file = os.path.join( dirroot, board_loss_files[k] )
                self.add_logfile( file )        
                self.board_loss_data[ k ] =  self.data               
        self.wclearfiles()
        
        
    ############################################################################
    def get_board_trace_loss(self, path, sparam, freq):
        '''Function that looks up the board trace loss value for a given trace 
        path for the sparam, and returns the value.
        '''
        
        if path not in self.board_loss_data:
            print '(get_board_trace_loss) *** Error *** no board trace data for ', path
        
        data = self.board_loss_data[path]
        
        if 'Freq(MHz)'  not in data:
            print "(get_board_trace_loss) *** Error *** no 'Freq(MHz)' for board trace data ", path
            
        if sparam not in data:
            print "(get_board_trace_loss) *** Error *** no '%s' for board trace data %s" % (sparam, path)
            
        # Find the closest record number to the freq given    
        fn = 'Freq(MHz)'
        rnlen = len(data[fn])
        fmin = data[fn][0]
        fmax = data[fn][-1]
        val  = None
        
        ratio = ((freq-fmin)/(fmax-fmin))
        
        if ratio >=0 and ratio <= 1.0:
            idx_est = rnlen * ratio
          
            idx     = int(idx_est)
            min_found = False
            idx_min = None
            diff_prev = None
            
            # first move the index back to a point that is less than the our freq
            while data[fn][idx] >= freq:
                idx -= 1
            
            idx_min = idx
            
            # then move the index idx upwards back up again
            # and look for the minimum difference 
            while min_found:
                f = data[fn][idx]
                diff = abs(f-freq)
                if diff < abs(data[fn][idx_min]-freq) :
                    idx_min = idx
                
                # if the difference is getting larger change the direction
                # of the idx increment
                if diff_prev and diff > diff_prev:
                    min_found = True
                diff_prev = diff
                            
                idx += 1
                
            val = data[sparam][idx_min]
        elif ratio < 0:
            val = data[sparam][0]
        elif ratio > 1:
            val = data[sparam][-1]
 
        return val 
    ############################################################################
    def deembed_board_trace_loss_scalar( self, new_name, sparam ):
        '''Function that creates a new column by taking the data from the spamam
        column and dembeds the board_loss_data from it
        
        This function assumes that read_board_loss_files() has been run and
        the self.board_loss_data[ k ] data structure is available containing
        the input and output trace path losses. 
        
        This function loops through self.data[sparam][] records and finds the
        coresponding filename associated with the record. The filename
        should contain the ports names eg.  
    
        .../RF9840_EN.0_P036Z8H_SN001_TRX3_ANT.s2p
                                      ^^^^ ^^^
        If the port names match with the keys in the board_loss_data dict
        then the board_loss_data is demebeded from the sparam data and
        written into the new column with name 'new_name'. Demembedding is
        done in a scalar manner (ie the sparam value minus each of the port
        values for the given frequency.
        '''
        
        if sparam in self.data:
           self.add_new_column( new_name )
           for rn in range( 0, self.datacount ):
                if self.data[ sparam ][ rn ] not in UNDEFS:
                     orig_value = self.data[ sparam ][ rn ] 
                     freq = self.data[ 'Freq(MHz)' ][ rn ] 
                     logfile = self.data[ 'logfilename' ][ rn ] 
                     portnames = self.get_board_trace_ports_from_logfile( logfile )
                     if len(portnames) == 2:
                          deembed_value = orig_value
                          for port in portnames:
                              loss_value = self.get_board_trace_loss( port, sparam, freq)   
                              if loss_value:
                                  deembed_value -= loss_value
                              else:
                                  break
                          if loss_value:
                              self.data[ new_name ][ rn ]  = -deembed_value
                     else:                      
                          print '''(deembed_board_trace_loss_scalar) *** Error *** for logfile %s[%s]
 the name has ambiguous portnames %s''' % ( logfile, self.data[ 'linenumber' ][ rn ], portnames)
                        
    ############################################################################
    def get_board_trace_ports_from_logfile( self, logfile ):
        '''Finds the board portnames in the logfile'''
         
        file = os.path.split(logfile)[1]
           
        fnd_ports = []
        for port in self.board_loss_data:
            portu = '(_%s_|_%s\.)' % (port,port)
            if re.search(portu,file,re.I):
                fnd_ports.append(port)
        
        return fnd_ports   
                        
                        
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

       self.win_load()

       return self.atr_logfiles

######################################################################
    def add_all_atlantis_dialog(self):
       '''Pops up a dialog box prompting the user to select Constellation (Atlantis) results'''

       self.atlantis_db_loaded = False

       self.atlantis_load_db()

       while self.atlantis_db_loaded == False:
           time.sleep(0.1)

       return



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
           if f.find('Constellation|') != 0 and \
              f.find('Mercury|') != 0:

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

           filetypes = [('logfiles', ('*.log','*.s2p','*.txt')),('logfile', '*.log'), ('csvfile', '*.csv'), ('text', '*.txt'), ('s1p', '*.s1p'), ('s2p', '*.s2p'), ('Excel', '*.xls'), ('all', '*.*')]

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
                                     filetypes=[('logfiles', ('*.log','*.s2p','*.txt')), ('csvfile', '*.csv'), ('s1p', '*.s1p'), ('s2p', '*.s2p'), ('all', '*.*')] )

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



         if filenames in UNDEFS or filenames == () or filenames[0] == '': return




         self.save_pygram_config( 'loaddir', os.path.dirname(  os.path.abspath(filenames[0]) ) )


         for f in filenames:
            self.add_logfile( f )

         self.win_load()


         self.print_column_list()                    # prints out all the available column names (useful when defining the conditions)
         self.print_values_list()
         self.done_list_columns = True

         self.gen_values_dict()

         print '  ...waiting for user input'
         self.status.set( 'waiting for user input' )
         self.root.update()



#####################################################################################
    def gen_values_dict(self,allcols=False):
         '''Generates the values dictionary for the standard list of column names
         (i.e. the names listed in self.values_dict_names)

         Parameters: allcols
            if False it will only update the values_dict for the standard value_dict_names
            if True it updates for all columns
         Returns   : None
         Updates   : self.values_dict[]
         '''


         cll = []
         for n in  self.data:
            if n != '' :
               cll.append(n)
         cll.sort()

         for c in cll:
            if allcols or c in self.value_dict_names:
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

#        if re.search( 'filter_value_', ctl_action ):
#            print '(do_event) <%s:%s:%s:%s:%s>' % (event, click_type, graph_action, ctl_action, self.keysym)




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

               if re.search('y2axis', page):
                  base_names =  self.y2names
                  base_name  =  self.y2name
                  base_text  =  self.y2text



               if click_type in ['buttonrelease', 'ctlbuttonrelease', 'key']:

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
                   current_column_name = n


                   # create an ordered list of selected columns
                   # first find out how many are selected 
                   # which will inlcude the most recent one selected
                   xysel_lst = base_names.curselection()
                   num_sel = len(xysel_lst)
                   if click_type in ['buttonrelease', 'ctlbuttonrelease']:
                       # we want a list that is only num_sel-1
                       if re.search('xaxis', page):
                            self.xnames_ordered = self.add_ordered_axis( n, num_sel, self.xnames_ordered)
                       if re.search('yaxis', page):
                            self.ynames_ordered = self.add_ordered_axis( n, num_sel, self.ynames_ordered)
                       if re.search('y2axis', page):
                            self.y2names_ordered = self.add_ordered_axis( n, num_sel, self.y2names_ordered)

                   if re.search('xaxis', page): 
#                        self.xynames[0] = n
                        pass
                   if re.search('yaxis', page):
                       self.graph_title.set('')

               if re.search('yaxis', page) and click_type == 'ctlbuttonrelease':
                  self.graph_title.set('')







           if re.search('filter', page) and click_type == 'buttonrelease':

             # for some reason I  cannot get the element name to work if it contains number characters
             # therefore I am mapping the value index into a letter

             # if we click in the flist area, fill out the vlist window with a list of the values and the selected status
             if re.search( 'fltr_list' , ctl_action ):
                n = self.flist.info_selection()
                if len(n) > 0:
                    name = n[0]
                    self.filter_name.set( name )
                    self.filter_value_min.set( '' )
                    self.filter_value_max.set( '' )
                    self.add_values_dict( name )
    #               print 'filter clicked = ', name, self.values_dict[name], n
    
                    self.wupdate_filter_value_list( name )
    
                    self.filter_column_list.selection_clear(0, Tk.END)
                    self.select_listbox_name( name, self.filter_column_list )


             if re.search( 'value_list' , ctl_action ):
                n = self.flist.info_selection()
                if len(n) > 0:
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
    
                    filter_values = ()
                    new_c = None
                    for c in self.filter_conditions:
                       n = c[0]
                       if n == name:
                          filter_values = ( c[2:] )
                          new_c = []
                    # make up a new filter_values list with the value changed
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

#                self.create_values_dict()

                name = self.filter_column_list.get(Tk.ACTIVE)
                name = self.remove_count_from_column(name)

                self.filter_name.set( name )
                self.filter_value_min.set( '' )
                self.filter_value_max.set( '' )

#               print '(do_event) filter double' , name

                # add or remove the filter
                exists_already = 0
                for c in self.filter_conditions:
                   n = c[0]
                   if n == name:
                      exists_already = 1

                if exists_already :  self.wdelfilter( )
                else              :  self.waddfilter( )

           # Update the filer range if the user types into the filter range entry boxes
#           if re.search( 'filter_value_', ctl_action ) and self.keysym == 'Return':
           if re.search( 'filter_value_', ctl_action ) and click_type == 'key' and self.keysym == 'Return':
           
           
                # Only do something if a filter has been selected
                name = self.filter_name.get()
                if name.strip() != '':
                    self.wupdate_filter_range()
                
#                print '(do_event) <%s:%s:%s:%s:%s>' % (event, click_type, graph_action, ctl_action, self.keysym)


################################################################################
    def add_ordered_axis( self, n, num_sel, ordered_list):




        n = self.remove_count_from_column(n)

        # if n in ordered_list:
        #     ordered_list.remove(n)
        #     return ordered_list

        # then make sure the list is num_sel long
        if num_sel == 0:
            ordered_list = []
        elif num_sel == 1:
           ordered_list = [n]
        else:       
           if n not in ordered_list:
               ordered_list.append(n)            
               ordered_list = ordered_list[-num_sel:]

        return ordered_list


#####################################################################################
    def remove_count_from_column(self, name):
        name = re.sub(r'\s+<.*>\s*$','',name)
        name = name.strip()
        return name

#####################################################################################
    def wallon( self ):

        pass


#####################################################################################
    def walloff( self ):

       pass

#####################################################################################

    def waddfilter( self ):

                name = self.filter_column_list.get( Tk.ACTIVE )
                name = self.remove_count_from_column(name)

                # determine if this is already an existing filter name. If it is then ignore the request
                exists_already = 0

                for c in self.filter_conditions:
                   n = c[0]
                   if n == name:
                      exists_already = 1

                if not exists_already:
                  self.addfilter(name, '=')

#####################################################################################
    def addfilter(self, name, type):
    
          self.filter_conditions.append( ( name, type ) )
          self.wupdate_filter_cond_list( name )
          self.add_values_dict( name )
          self.wupdate_filter_value_list( name )
          if name not in self.value_dict_names:
             self.value_dict_names.append( name )
    
#####################################################################################
    def wupdate_filter_range(self):
        '''When the gui filter range is selected then this will be defined instead of using the
        definition of individually selected value values_list.'''
        
        name = self.filter_name.get()
        min_val =  self.filter_value_min.get()
        max_val =  self.filter_value_max.get()
    
        # build the range specifier string used to define the filter
        cond = '%s..%s' % ( min_val.strip(), max_val.strip() )
    
        # dont update anything if both the min and max values are empty
        if cond != '..':
            self.update_filter_conditions( name, cond )
        else:
            self.update_filter_conditions( name, None )


        self.wupdate_filter_cond_list( name )
        self.wupdate_filter_value_list( name, update_entry=False )


#####################################################################################
    def wdelfilter( self ):

                name = self.filter_column_list.get( Tk.ACTIVE )
                name = self.remove_count_from_column(name)

                if name == '':
                  n = self.flist.info_selection()
                  name = n[0]
                  self.wupdate_filter_cond_list(name)

                self.update_filter_conditions( name, None )
                self.wupdate_filter_cond_list( None )
                self.vlist.delete_all()

#####################################################################################

    def wupdate_column_lists( self ):

          #print '(wupdate_column_lists)'
          self.win_load( )


#####################################################################################


#     def wmorefilter( self ):
#           self.filter_column_list.delete(0,Tk.END)
#           cll = []
#           for col in self.data:
#             if col != '':
#                cll.append(col)
#           cll.sort()
#           for c in cll:
#              self.filter_column_list.insert( Tix.END, c )
#####################################################################################

#     def wlessfilter( self ):
#           self.filter_column_list.delete(0,Tk.END)
#           for c in self.value_dict_names:
#              self.filter_column_list.insert( Tix.END, c )

#####################################################################################



    def wupdate_filter_cond_list( self, name = None ):

          if name == None:
              n = self.flist.info_selection()
              if len(n) > 0:
                 name = n[0]

          self.flist.delete_all()
          for c in self.filter_conditions:
 #            print '(wupdate_filter_cond_list)', c
             e = c[0]
             self.flist.add(e, itemtype=Tix.TEXT, text=c[0])
             txt = self.list2str( c[2:] )
             self.flist.item_create(e, 1, itemtype=Tix.TEXT, text=txt)

          if name != None:
             try:
                 self.flist.selection_set( name )
             except:
                 pass

#####################################################################################


    def wupdate_filter_value_list( self, name, update_entry=True):
        '''This function populates the filter values listbox and the filter range entry boxes with the
        current contents of the filter_conditions for the selected filter 'name'
        The update_entry option will allow the entry boxes to be updated with the filter conditions.
        '''
        
        seq= 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        filter_values = None
        filter_type   = None
        for c in self.filter_conditions:
           n = c[0]
           if n == name:
              filter_values = ( c[2:] )
              filter_type = c[1]

        self.vlist.delete_all()
        j = 0
        self.add_values_dict( name )
        
        

#        print '(wupdate_filter_value_list)  values_list[ %s ] len = %s' % ( name, len(self.values_dict_count[ name ]))
#        print '(wupdate_filter_value_list)  filter_values = ' , filter_type, (filter_values)
#                print '(wupdate_filter_value_list)',  len( self.data[ name ]), self.data[ name ]


        # Look if the filter_values define a range or a list
        # if it is a range then fill in the min and max values and set the filter_values to an empty list 
        fmin = ''
        fmax = ''

        if filter_type != '=':
            
            if   filter_type == '<<' and len(filter_values) == 2:    # min and max
                fmin = filter_values[0]
                fmax = filter_values[1]
            elif filter_type == '<' and len(filter_values) == 1:     # max only
                fmax = filter_values[0]
            elif filter_type == '>' and len(filter_values) == 1:     # min only
                fmin = filter_values[0]

            filter_values = None
        
        if update_entry:
            self.filter_value_max.set( '%s' % fmax )
            self.filter_value_min.set( '%s' % fmin )

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

      # ARGPRD script variables

      self.xl_cell_done = {}
      self.oplogfilenames = []

      try:
          del self.xl_tmpfile
      except: pass







#####################################################################################


    def doDestroy(self):
         self.root.destroy()
         sys.exit()
#####################################################################################

    def createCommonButtons(self, master):
         ok     = Tix.Button(master, name='ok',     text='OK',     width=6, command=self.doDestroy) .grid( column=0, row=9,  sticky=Tix.SW)
         apply  = Tix.Button(master, name='apply',  text='Apply',  width=6, command=self.doDestroy) .grid( column=1, row=9,  sticky=Tix.S)
         cancel = Tix.Button(master, name='cancel', text='Cancel', width=6, command=self.doDestroy) .grid( column=2, row=9,  sticky=Tix.S)
         quit   = Tix.Button(master, name='quit',   text='Quit',   width=6, command=sys.exit      ) .grid( column=3, row=9,  sticky=Tix.S)


    #######################################################################################
    def smith(self, smithR=1, chart_type = 'z',ax=None):
    	''' 
    	plots the smith chart of a given radius
    	takes:
    		smithR - radius of smith chart
    		chart_type: string representing contour type: acceptable values are 
    			'z': lines of constant impedance
    			'y': lines of constant admittance
    		ax - matplotlib.axes instance 
    	'''
    	##TODO: fix this function so it doesnt suck
    	if ax == None:
    		ax1 = plb.gca()
    	else:
    		ax1 = ax
    
    	# contour holds matplotlib instances of: pathes.Circle, and lines.Line2D, which 
    	# are the contours on the smith chart 
    	contour = []
    	
    	# these are hard-coded on purpose,as they should always be present
    	rHeavyList = [0,1]
    	xHeavyList = [1,-1]
    
    	#TODO: fix this
    	# these could be dynamically coded in the future, but work good'nuff for now 
    	rLightList = plb.logspace(3,-5,9,base=.5)
    	xLightList = plb.hstack([plb.logspace(2,-5,8,base=.5), -1*plb.logspace(2,-5,8,base=.5)]) 
    	
    	# cheap way to make a ok-looking smith chart at larger than 1 radii
    	if smithR > 1:
    		rMax = (1.+smithR)/(1.-smithR)
    		rLightList = plb.hstack([ plb.linspace(0,rMax,11)  , rLightList ])
    		
    	if chart_type is 'y':
    		y_flip_sign = -1
    	else:
    		y_flip_sign = 1
    	# loops through Light and Heavy lists and draws circles using patches
    	# for analysis of this see R.M. Weikles Microwave II notes (from uva)
    	for r in rLightList:
    		center = (r/(1.+r)*y_flip_sign,0 ) 
    		radius = 1./(1+r)
    		contour.append( Circle( center, radius, ec='grey',fc = 'none'))
    	for x in xLightList:
    		center = (1*y_flip_sign,1./x)
    		radius = 1./x
    		contour.append( Circle( center, radius, ec='grey',fc = 'none'))
    			
    	for r in rHeavyList:
    		center = (r/(1.+r)*y_flip_sign,0 )
    		radius = 1./(1+r)
    		contour.append( Circle( center, radius, ec= 'black', fc = 'none'))	
    	for x in xHeavyList:
    		center = (1*y_flip_sign,1./x)
    		radius = 1./x	
    		contour.append( Circle( center, radius, ec='black',fc = 'none'))
    	
    	#draw x and y axis
#    	ax1.axhline(0, color='k')
#    	ax1.axvline(1*y_flip_sign, color='k')
#    	ax1.grid(0)
    	#set axis limits
#    	ax1.axis('equal')
    	ax1.axis(smithR*npy.array([-1., 1., -1., 1.]))
    	
    	# loop though contours and draw them on the given axes
    	for currentContour in contour:
    		ax1.add_patch(currentContour)
    
###############################################################################################    
    def draw_smith_circle(self, circ_type, vconst=50, color='k',alpha=0.5,linewidth=1):
         '''Draw a circle on the polar plot from a series of impedance points R + jX. Depending 
         on the circ_type. For circ_type = 'real' the real R part is kept constannt using the value vconst
         and the X impedance is swept and for circ_type = 'imag' the X part is constant value vconst
         and the real part is swept. Each impedance point is converted into the reflection coefficient
         and it is added to the line segment as magnitude and phase values. This results in a circlular
         line being plotted on the polar plot.'''
          

         # set the number of line segments used for the circles
         nsegs = 100.0   
         
         # set the impedance sweep range for each end of the circle arc
         # real impedance can only be positive though  
         imax = 8.0
         if circ_type != 'real':
            imin = 0.0
         else:
            imin = -imax
         
         inc = imax/nsegs
         
         imin -= inc
         imax += inc
         
         z0 = complex(50.0,0)
         phil = []
         magl = []
         for i in arange(imin,imax,inc):
              # when sweeping we need to values close together areound zero and spaced out for large values
              # use an exp to space them out 
              v = nu.e**abs(i)
              if i<0: v = -v
              if circ_type == 'real':
                  z = complex( vconst, v )
              else:
                  z = complex( v, vconst )
              refl = (z-z0)/(z+z0)
              mag, phi = ri2magphase( refl.real , refl.imag )
              magl.append(mag)
              phi = (phi/360.0)*2*nu.pi
              phil.append(phi)

         ln = Line2D(phil, magl, color=color, alpha=alpha, lw=linewidth)
         self.ax.add_line(ln) 

    ################################################################################
    def draw_smith_chart_grid(self):
         '''Draw the smith chart axes lines.
        This is done using a series of circles, by plotting impedance poinst
        with constant R and constant X'''
        
         linewidth=2
         alpha = 0.3
         rlist = [ 10, 25,  50, 100, 200]
         for r in rlist:
             self.draw_smith_circle('real', vconst=r, color='grey', alpha=alpha,linewidth=linewidth)
         for r in rlist:
             self.draw_smith_circle('imag', vconst= r, color='grey', alpha=alpha,linewidth=linewidth)
             self.draw_smith_circle('imag', vconst=-r, color='grey', alpha=alpha, linewidth=linewidth)
         ln = Line2D([0,nu.pi],[1,1], color='grey', alpha=alpha, lw=linewidth)
         self.ax.add_line(ln) 
    

#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################

def mag2dB( mag ):
    if mag <= 0:  mag = 1e-12
    dB  = 20*math.log10(mag)
    return dB

def dB2mag( dB ):
    mag = 10**(float(dB)/10.0)
    return mag
    
def vswr2mag( vswr ):
    vswr = float(vswr)
    mag = (vswr-1)/(vswr+1) 
    return mag                                                                  

def mag2vswr( mag ):
    mag = float(mag)
    if mag < 1:
        vswr = (1+mag)/(1-mag)
    else:
        vswr = 1e6
    return vswr
    
def ri2phase( r , i ):
    r = float(r)
    i = float(i)
    phase = math.atan2(i,r)*(360.0/(2*math.pi))
    return phase
    
def ri2mag( r , i ):
    r = float(r)
    i = float(i)
    mag = math.sqrt(r*r + i*i)
    return mag

def magphase2ri( mag , phase ):
    mag = float(mag)
    phase = float(phase)
    phi = (2*math.pi*phase) / 360  
    r = mag*math.cos( phi )
    i = mag*math.sin( phi )
    return r , i

def ri2magphase( r , i ):
    r = float(r)
    i = float(i)
    
    phase = math.atan2(i,r)*(360.0/(2*math.pi))
    mag = math.sqrt(r*r + i*i)
    return mag,phase


#######################################################################################
def dBm_to_W(dbm):
    W = dBm_to_mW(dbm) / 1000.0
    return W
#######################################################################################
def dBm_to_mW(dbm):
    mW = 10.0**(dbm/10.0)
    return mW

