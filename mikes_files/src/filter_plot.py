print 'this is the pygram_script.py'
import __main__ 
import __main__ as M
self = M.mag
self.status.set( 'Run Script Running Again' )


############################################################################################################
def get_logfile_idxs():
    '''# Get a list of logfiles
    # go through each of them and check that they are s2p data
    # and get the start record for the logfile and determine if it is
    # a valid s2p data set
    '''
    
    self.logfile_record_range = []
    for logfile in self.values_dict['logfilename']:
        start_rn = None
        end_rn = None
        for rn in range(0,self.datacount):
            if self.data['logfilename'][rn] == logfile:
                if start_rn == None:
                    col = 's11_r'
                    if col in self.data and self.data[col] not in UNDEFS:
                        start_rn = rn
                    else:
                        start_rn = -1
                if start_rn != None:
                    end_rn = rn
        self.logfile_record_range.append( (start_rn,end_rn) )

############################################################################################################
def calc_filter_properties( s2pfile_idx ):
    '''Measure the Peak and Q response for the s2p data from the given logfile index number.
     Look through the s21_mag data for all records which match this logfile
     and find the peak and 50% values'''
    
    peak_value = None
    peak_value_dB = None
    freq_peak = None
    lower_3dB_freq = None
    upper_3dB_freq = None
    bw = None 
    q = None
    
    start_rn = self.logfile_record_range[ s2pfile_idx ][0]
    end_rn   = self.logfile_record_range[ s2pfile_idx ][1]


    if 's21_mag' in self.data and start_rn >= 0:
        maglist = self.data['s21_mag'][start_rn:end_rn+1]

        # Find the peak s21 value
        peak_rn     = None
        peak_value  = None
        for rn,val in enumerate(maglist):
            if val not in UNDEFS:
                if peak_value == None or val > peak_value:
                    peak_value = val
                    peak_rn = rn                    
      
        # Find the lower 50% s21 value,
        # starting at the peak value record look backwards until we find the 50% value
        lower_3dB_rn = None
        lower_3dB    = None
        rn = peak_rn
        while(rn >= 0):
            val = maglist[rn]
            if val not in UNDEFS:
                if lower_3dB == None and val < peak_value * 0.5:
                    lower_3dB = val
                    lower_3dB_rn = rn
            rn += -1
 
        # Find the upper 50% s21 value
        # starting at the peak value record look forward until we find the 50% value
        upper_3dB_rn = None
        upper_3dB    = None
        rn = peak_rn
        while(rn < len(maglist)):
            val = maglist[rn]
            if val not in UNDEFS:
                if upper_3dB == None and val < peak_value * 0.5:
                    upper_3dB = val
                    upper_3dB_rn = rn
            rn += +1
              
    # Get the frequencies, and calculate Q          
    fcol = 'Freq(MHz)'
    if peak_rn:
        freq_peak = self.data[fcol][peak_rn+start_rn]  
        peak_value_dB  = mag2dB( peak_value )  
    if lower_3dB_rn:
        lower_3dB_freq = self.data[fcol][lower_3dB_rn+start_rn]       
    if upper_3dB_rn:
        upper_3dB_freq = self.data[fcol][upper_3dB_rn+start_rn]
    if lower_3dB_rn and upper_3dB_rn and peak_rn:
        bw = upper_3dB_freq - lower_3dB_freq
        q = freq_peak/bw

    filter_props = [      
        [ 'fp_MagIL',        peak_value_dB  ],
        [ 'fp_FreqPk',       freq_peak      ],
        [ 'fp_Freq3dBLower', lower_3dB_freq ],
        [ 'fp_Freq3dBUpper', upper_3dB_freq ],
        [ 'fp_BW',           bw             ],
        [ 'fp_Q',            q              ],
                    ]

    return filter_props
    
################################################################################
def add_filename_properties( s2pfile_idx ):   
    '''Take the filename for the given index, split it up and store it as the
    '''
    
    filename = self.values_dict['logfilename'][ s2pfile_idx ]
    
    # Split the s2p filename up into different parts
    (fdir,fname_fext) = os.path.split(filename)
    (fname,fext)      = os.path.splitext(fname_fext)
    flds = fname.split('_')
    
    # Add them into the data     
    update_data_column( s2pfile_idx, 'fp_fdir', fdir )
    update_data_column( s2pfile_idx, 'fp_fext', fext )
    update_data_column( s2pfile_idx, 'fp_fname', fname )
    for i, fld, in enumerate(flds):
        update_data_column( s2pfile_idx, 'fp_f%d' % i, fld )
    
################################################################################
def add_filter_properties( s2pfile_idx, filter_props ):   
    '''Take the list of filter porperties and store each into the data array
    for the given s2p file index
    '''

    for col_val in filter_props:
        update_data_column( s2pfile_idx, col_val[0], col_val[1] )
    
################################################################################
def update_data_column( s2pfile_idx, column_name, value ):
    ''' Add a new column for the given s2pfile index, and 
    save with the given value '''
    
    self.add_new_column( column_name )
    
    (start_rn,end_rn) = self.logfile_record_range[s2pfile_idx]
    
    # Save away the value in the first and only record for this idx
    self.data[column_name][start_rn] = value

# If we need to write to every record with this idx then uncomment this    
#     for rn in range(start_rn,end_rn+1):
#         self.data[column_name][rn] = value

    self.add_values_dict( column_name )

################################################################################
##  MAIN PROG STARTS HERE   ####################################################
################################################################################


# Start off with a clean slate
#self.wclearfiles()

filedir = r'T:\WI_Engineering\Public\AD1146\S39_SMD'
files = [
r'S39SMDB01SN1_D14T2_QANA_CUDOWN.S2P',
r'S39SMDB01SN1_D14T2_QANA_CUUP.S2P',
r'S39SMDB01SN1_D14T2_QANT_CUDOWN.S2P',
r'S39SMDB01SN1_D14T2_QANT_CUUP.S2P',
]

# Load some s2p files
# for f in files:
#     s2pfile = os.path.join( filedir, f )
#     self.add_logfile(s2pfile)
# self.add_all_logfiles_dialog()

# Find the record number indexs for each of the s2p logfiles
get_logfile_idxs()


for col in self.values_dict:
    print '(VALUES_DICT)', col,  self.values_dict[col] 

# For each logfile find its peak and q
for s2pfile_idx, s2pfile in enumerate( self.values_dict['logfilename']):
     filter_props =  calc_filter_properties( s2pfile_idx )
     add_filename_properties( s2pfile_idx )
     add_filter_properties( s2pfile_idx, filter_props )

# Update the GUI with the new data
self.win_load()

self.status.set( 'Run Script Finished' )