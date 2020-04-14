#!/usr/bin/python

"""
__version__ = "$Revision: 1.53 $"
__date__ = "$Date: 2013-04-15 17:37:20-07 $"
"""

import os, pprint, time, glob, re, math, types, traceback, sys

try:
    import mwavepy
    import numpy
    got_mwavepy = True
except ImportError:
    got_mwavepy = None    

# M.got_mwavepy = None    


from copy import deepcopy

if got_mwavepy:
    from scipy.interpolate import interp1d # for Network.interpolate()
    import scipy

print 'importing pygram_mwavepy', got_mwavepy

############################################################################
def mwavepy_interpolate(self, new_frequency,**kwargs):
        '''
		calculates an interpolated network. defualt interpolation type
		is linear. see notes about other interpolation types

		takes:
			new_frequency:
			**kwargs: passed to scipy.interpolate.interp1d initializer.
				  
		returns:
			result: an interpolated Network

		note:
			usefule keyward for  scipy.interpolate.interp1d:
			 kind : str or int
				Specifies the kind of interpolation as a string ('linear',
				'nearest', 'zero', 'slinear', 'quadratic, 'cubic') or as an integer
				specifying the order of the spline interpolator to use.

			
		'''
#        M.PRV( self.frequency.f , self.s)
#        M.PRV( new_frequency.f )
        interpolation_s = interp1d(self.frequency.f,self.s,axis=0,**kwargs)
        interpolation_z0 = interp1d(self.frequency.f,self.z0,axis=0,**kwargs)
        result = deepcopy(self)
        result.frequency = new_frequency
        result.s = interpolation_s(new_frequency.f)
#        M.PRV( result.frequency.f , result.s)
        
        result.z0 = interpolation_z0(new_frequency.f)
        return result

#########################################################################################        
def mwavepy_change_frequency(self, new_frequency, **kwargs):
        new_self = self.interpolate(new_frequency, **kwargs)
        new_self.frequency.start = new_frequency.start
        new_self.frequency.stop = new_frequency.stop
        return new_self

##########################################################################################
def get_single_frequency_spars(self, freq):
    '''Returns an network containing a single frequency point.
    It uses the spars of the nearest point, (ie it the spars are not interpolated)'''
    
    fnearest = None
    count = 0
    fdiff = None
    for f in self.frequency.f:

        if fnearest==None or abs((f/1e6)-freq) < fdiff:
            fdiff = abs((f/1e6)-freq)
            count += 1
            fnearest = f


    new_frequency = deepcopy(self.frequency)
    new_frequency.start = fnearest
    new_frequency.stop  = fnearest
    new_frequency.npoints  = 1
    
    new_self = self.change_frequency(new_frequency)
    
    # now fudge the Network so that it uses our desired freq
    freq = float(freq * 1e6)
    new_self.start = freq
    new_self.stop  = freq
    new_self.npoints  = 1
    new_self.f = [ freq ]
    
    return new_self



#########################################################################################        
def mwavepy_load_file(self, filename):
        """
        mwavepy function to Load sparam data into internal self.sparameters data structure.
        This is a modified version of the original mwavepy load_file method. Changes:
        
         1) We want to load the data which maybe touchstone format lines, directly from an ENA direct read
              operation. In which case the filename parameter is a two element list 
                 [ filename, [list of touchstone lines (> length 20) ]]
         2) mwavepy is a little fussy about the touchstone file format, and we need to make it more flexible
         3) We want to be able to define the sparams using a simplified format. eg. [0.325,0.856] for a lowband/highband s21 value
         4) We need to read in a Maury tuner calibration file (.tun) the filename parameter will have a suffix with the tuner settings,
            e.g "L:\Lab & Testing\Test Stations\Tuner Files\MT982EU30_2191_cal.tun TUNER:1950:3.0:135.0"  
            The whole file will be read in but only the section matching the TUNER spec will be loaded
        
        """
        
        
        # GET THE SPARAM INPUT LINES FROM FILENAME   
        
        # If the filename is a list then the this is NOT a touchstone file,
        # rather it is a list of single point s21_db values for LB and HB frequencies.
        # We will create an sparam network from these data points
        if not isinstance(filename,types.StringTypes):
           vals     = filename[1]
           filename = filename[0]
           if 0 and len(vals) < 20:
               lines = mwavepy_load_vals(filename, vals)
           else:
               lines = vals.split('\n')
           self.rank = 2
        else:
        
            if len(filename) < 1024:
                # We have a string so this is the name of a touchstone sparameter file
                # Now determine if this is a Maury tuner calibration file (.tun) 
    
                # Find out if this file is for a tuner 
                # if the finename parameter ends with TUNER:* add it back to the sparam_name
                tuner_spec = re.findall(r' TUNER:.*$', filename)
                if len(tuner_spec) > 0:
                    tuner_spec = tuner_spec[0]
                    filename = re.sub( tuner_spec, '', spm)
                else:
                    tuner_spec = ''
    
                # Read in the file which may be a regular touchstone file, or it may be
                # tuner file with a .tun extention.
                # If its a .tun look to see if it has been read in already
                # and read it in only if this is the first time.
                if tuner_spec == '' or self.tuner_file_lines == None:
                    # First we read it in the whole file
                    fip = open( filename, 'rU' )
                    fileread_str = fip.read()
                    fip.close()
                    # Split the file into separate lines, and sort out the line separation characters
                    fileread_str = fileread_str.replace('\r','\n')
                    lines = fileread_str.split('\n')
                    
                # For a tuner spec use the saved lines in the self.tuner_file_lines as our input
                # as we don't need to read it in again 
                if tuner_spec != '':
                    if  self.tuner_file_lines == None:
                       self.tuner_file_lines = lines
                    lines = self.tuner_file_lines
    
    
                # Now determine if this is a tuner calibration file. If it is we must
                if tuner_spec == '':
                    extention = filename.split('.')[-1].lower()
                    #self.rank = {'s1p':1, 's2p':2, 's3p':3, 's4p':4}.get(extention, None)
                    try:
                        self.rank = int(extention[1:-1])
                    except (ValueError):
                        raise (ValueError("filename does not have a s-parameter extention. It has  [%s] instead. please, correct the extension to of form: 'sNp', where N is any integer." %(extention)))
                else:
                    # the tuner file is always in a two port format 
                    self.rank = 2
    
    
                # IF TUNER FILE, THEN FILTER THE INPUT LINES TO SELECT THE SPARAMS THAT MATCH THE TUNER SPEC
                if tuner_spec != '':
                    lines = self.select_tuner_lines( lines, tuner_spec )

            else:
               lines = filename.split('\n')
               self.rank = 2
            
            
        # CONVERT THE SPARAM INPUT LINES INTO LIST values
        
        linenr = 0
        values = []
        for line in lines:
            linenr +=1
            if not line:
                break

            # remove comment extentions '!'
            # this may even be the whole line if '!' is the first character
            # everything is case insensitive in touchstone files
            line = line.split('!',1)[0].strip().lower()
            if len(line) == 0:
                continue
                

            # grab the [version] string
            if line[:9] == '[version]':
                self.version = line.split()[1]
                continue

            # grab the [reference] string
            if line[:11] == '[reference]':
                self.reference = [ float(r) for r in line.split()[2:] ]
                continue

            # the option line
            if line[0] == '#':
                if re.search(r'^#\d+', line):
                   continue

                toks = line[1:].strip().split()
                # fill the option line with the missing defaults
                toks.extend(['ghz', 's', 'ma', 'r', '50'][len(toks):])
                self.frequency_unit = toks[0]
                self.parameter = toks[1]
                self.format = toks[2]
                self.resistance = toks[4]
                if self.frequency_unit not in ['hz', 'khz', 'mhz', 'ghz']:
                    print 'ERROR: illegal frequency_unit [%s]',  self.frequency_unit
                    # TODO: Raise
                if self.parameter not in 'syzgh':
                    print 'ERROR: illegal parameter value [%s]', self.parameter
                    # TODO: Raise
                if self.format not in ['ma', 'db', 'ri']:
                    print 'ERROR: illegal format value [%s]', self.format
                    # TODO: Raise

                continue

            # collect all values without taking care of there meaning
            # we're seperating them later
            values.extend([ float(v) for v in line.split() ])




        # CONVERT values LIST INTO A NUMPY ARRAY self.sparameters 


        # let's do some postprocessing to the read values
        # for s2p parameters there may be noise parameters in the value list
        
        values = numpy.asarray(values)
        if self.rank == 2:
            # the first frequency value that is smaller than the last one is the
            # indicator for the start of the noise section
            # each set of the s-parameter section is 9 values long
            pos = numpy.where(numpy.sign(numpy.diff(values[::9])) == -1)
            if len(pos[0]) != 0:
                # we have noise data in the values
                pos = pos[0][0] + 1   # add 1 because diff reduced it by 1
                noise_values = values[pos*9:]
                values = values[:pos*9]
                self.noise = noise_values.reshape((-1,5))

        # reshape the values to match the rank
        self.sparameters = values.reshape((-1, 1 + 2*self.rank**2))
        # multiplier from the frequency unit
        self.frequency_mult = {'hz':1.0, 'khz':1e3,
                               'mhz':1e6, 'ghz':1e9}.get(self.frequency_unit)
        # set the reference to the resistance value if no [reference] is provided
        if not self.reference:
            self.reference = [self.resistance] * self.rank



############################################################################################
def select_tuner_lines( lines, tuner_spec ):
    '''Go throuth the tuner cal file lines and convert them into s2p format but only select
    the data that matches the tuner spec (freq, vswr, phase)'''
    
    
    # Extract the tuner spec data
    (tuner, freq, vswr, phase) = tuner_spec.split(':')
    # Cal the target mag
    target_mag    = vswr2mag(vswr)
    target_phase  = phase 
    target_r, target_i = magphase2ri( target_mag, target_phase )
    
    # Get a list of all the freq in the 'lines' and save the line number ranges for each freq in a dict.
    freq_range = {}
    f = None
    line_num = 0
    for line in lines:
        line_num += 1
        # looking line for 'Freq     1.78500 GHz,  3499 positions, default Gamma =  0.00000  0.00000'
        if line.find('Freq') >= 0:
            if f != None:
                freq_range[ f ].append(line_num)
            wds = line.split()
            if len(wds) > 3:
                f = wds[1].strip()
                m = wds[2].strip()
                f =  float(f)
                m =  m[0].upper()
                if m == 'G':
                    f = f*1e3
                if m == 'H':
                    f = f/1e6
                freq_range[ f ] = [line_num]    
    if f != None:
        freq_range[ f ].append(line_num)
    
    
    # Look in the target_freq section and get the 10 closest s11 sparam lines to the specified freq vswr phase
    
#     if target_freq not in freq_range:
#         M.prnm('e', 'Target frequency %s is not in tuner calibration file' % (target_freq))
    s = freq_range[ target_freq][0]
    f = freq_range[ target_freq][1]

    self.closest_to_target_list   = [None] * 10
    self.closest_to_target_filled =  None
    self.closest_to_target_max    =  None
    
    for i in range( s,f ):         
        self.add_to_list_if_s11_closer( i, lines, target_r, target_i )
    
    # Interpolate between the values to find the closes probe and cariage positions
    
    # For each frequencies finding the 10 closest probe cariage positions and interpolate
    # to get the sparams at the target probe carriage pos.
    
    # Build a touchstone format output 

#------------------------------------------------------------------------------------------
def add_to_list_if_s11_closer(self, i, lines, target_r, target_i):
    '''Adds the line specified by i to the closest_to_target_list if it is closer than the
    any others in the list'''

    wds = lines[i].split()

    s11_r = wds[0]
    s11_i = wds[1]
                        
    diff = abs((target_r - s11_r) + (target_i - s11_i))


    added_i_to_list = False

    # If the list is not yet filled then fill it up, we don't care about the min or max diff yet.
    filled = True    
    if not self.closest_to_target_filled:
        for ctt in self.closest_to_target_list:
            if ctt == None:
                ctt = [diff, i]
                added_i_to_list = True
                filled = False
    if filled:
        self.closest_to_target_filled = True
    
    # if the list is full see if the current diff is smaller than the previous largest diff,
    # if it is smaller then replace with this diff
    if filled:

        if diff < self.closest_to_target_list[ self.closest_to_target_max ]:
            self.closest_to_target_list[ self.closest_to_target_max ] = [diff, i]
            added_i_to_list = True  
    
    # If we added a value to the list we must find a new max value in the list, ready for the next time          
    if added_i_to_list: 
        ci = 0
        ctt_max = None
        for ctt in closest_to_target_list:
            if ctt == None:
                continue
            if ctt_max == None or ctt[0] > closest_to_target_list[ ctt_max ]:
                ctt_max = ci
            ci += 1
        self.closest_to_target_max = ctt_max
     
    

############################################################################################
def mwavepy_load_vals(filename, vals):
    '''Function that creates a sparamater touchstone list of lines from a set of dB values
    This is used as an alternative method of creating an mwavepy object.
    The data 'vals' contains a list of frequencies and coresponding list of gain magnitude values.   
    This function will convert the vals into a list of lines in touchstone format.'''
    
    
    fileread_str = '''
!Autogenerated by PYGRAM: XXXX
!Date: XXXX
!Data & Calibration Information:
!Freq	S11:SOLT2(ON)	S21:SOLT2(ON)	S12:SOLT2(ON)	S22:SOLT2(ON)
!PortZ  Port1:50+j0    Port2:50+j0
!Above PortZ is port z conversion or system Z0 setting when saving the data.
!When reading, reference impedance value at option line is always used.
# Hz S RI R 50
'''   



    for freq, mag in zip( vals[0], vals[1]):
    
        real = 10**(mag/20.0)
 
                   # 300000	1e-10	0	1	0	1	0	1e-10	0
        fileread_str += '%s 1e-10	0	%0.7g	0	%0.7g	0	1e-10	0\n'  \
                 % ( freq, real, real )



    lines = fileread_str.split('\n')
    
    lines_new = []
    for line in lines:
        if line != '':
            lines_new.append(line)
        
#    M.PRV(filename, vals)
#    print lines_new
    
    
    return lines_new


#######################################################################################################
def mwavepy_read_touchstone(self, filename):
    '''
    loads  values from a touchstone file. 
    
    takes:
    	filename - touchstone file name, string. 
    
    note: 
    	ONLY 'S' FORMAT SUPORTED AT THE MOMENT 
    	all work is tone in the touchstone class. 
    	
    This function replaces the mwavepy function read_touchstone. The only difference is that it 
    if the filename is a list then the self.name value is taken from the first item in the list
    (The original mwavepy function would just give an error)
    '''
    touchstoneFile = mwavepy.touchstone.touchstone(filename)
    
    if touchstoneFile.get_format().split()[1] != 's':
    	raise NotImplementedError('only s-parameters supported for now.')
    
    
    self.f, self.s = touchstoneFile.get_sparameter_arrays() # note: freq in Hz
    self.z0 = float(touchstoneFile.resistance)
    self.frequency.unit = touchstoneFile.frequency_unit # for formatting plots
    if isinstance(filename,types.StringTypes):
        self.name = os.path.basename( os.path.splitext(filename)[0])
    else:
        self.name = os.path.basename( os.path.splitext(filename[0])[0])

