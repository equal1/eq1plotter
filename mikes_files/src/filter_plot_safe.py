print 'this is the pygram_script.py'
import __main__ 
import __main__ as M
self = M.mag
self.status.set( 'Run Script Running Again' )



# for each logfile find its peak and q
def calc_filter_properties( s2pfile_idx ):
    '''Measure the Peak and Q response for the s2p data from the given logfile index number.
     Look through all record
    
    peak_value, freq_peak, lower_3dB_freq, upper_3dB_freq, bw, q = None
    

    start_rn = self.logfile_record_range[ s2pfile_idx ][0]
    end_rn   = self.logfile_record_range[ s2pfile_idx ][1]

    col = 's21_mag'
    
    if col in self.data and start_rn >= 0:
    
        # Find the peak s21 value
        peak_rn     = None
        peak_value  = None
        for i in range(start_rn,end_rn):
            val = self.data[col][rn]
            if val not in UNDEFS:
                if peak_value == None or val > peak_value:
                    peak_value = val
                    peak_rn = rn
                    
      
        # Find the lower 50% s21 value,
        # starting at the peak value record look backwards until we find the 50% value
        lower_3dB_rn = None
        lower_3dB    = None
        rn = peak_rn
        while(rn > start_rn):
            val = self.data[col][rn]
            if val not in UNDEFS:
                if lower_3dB == None and val < peak_val * 0.5:
                    lower_3dB = val
                    lower_3dB_rn = rn
            rn += -1
 
        # Find the upper 50% s21 value
        # starting at the peak value record look forwards until we find the 50% value
        upper_3dB_rn = None
        upper_3dB    = None
        rn = peak_rn
        while(rn <= end_rn):
            val = self.data[col][rn]
            if val not in UNDEFS:
                if upper_3dB == None and val < peak_val * 0.5:
                    upper_3dB = val
                    upper_3dB_rn = rn
            rn += +1
              
    
    # Get the frequencies, and calculate Q          
    fcol = 'Freq(MHz)'
    if peak_rn:
        freq_peak = self.data[fcol][peak_rn]    
    if lower_3dB_rn:
        lower_3dB_freq = self.data[fcol][lower_3dB_rn]       
    if upper_3dB_rn:
        upper_3dB_freq = self.data[fcol][upper_3dB_rn]
    if lower_3dB_rn and upper_3dB_rn and peak_rn:
        bw = upper_3dB_freq - lower_3dB_freq
        q = freq_peak/bw



    return peak_value, freq_peak, lower_3dB_freq, upper_3dB_freq, bw, q








s2pfile = r'T:\WI_Engineering\Public\AD1146\S39_SMD\S12D26B01SN1_QTUNNER.S2P'
self.add_logfile(s2pfile)
#self.add_all_logfiles_dialog()

print 'we have data for the following:'
print self.data.keys()


# Get a list of logfiles
# go through each of them and check that they are s2p data
# and get the start record for the logfile and determine if it is
# a valid s2p data set

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
    

# for each logfile find its peak and q
def calc_peak_data

# find the peak 


# Look through all the tuner cal data and build a lookup table between the tuner load and the
# the record number.
# The Tuner Cal data is measured using the 'Measure Sparams s2p' TestName 

cal2rn = {}

for rn in range( rn_start, rn_finish ):
    testname = self.data['TestName'][rn]
    if testname == 'Measure Sparams s2p' and self.data['mwavepy'][rn]:
        tuner_load_str = 'NOTSET'
        try:
        
        
            tuner_load_str = '%d %s %s %s %s %s %s' % \
              ( self.data['Freq(s2p)' ][rn]/1e6,
                self.data['VSWR' ][rn], self.data['Phase(degree)'][rn], 
                self.data['VSWR2'][rn], self.data['Phase2'       ][rn], 
                self.data['VSWR3'][rn], self.data['Phase3'       ][rn]  ) 
            if tuner_load_str not in cal2rn:
                cal2rn[ tuner_load_str ] = 0
            cal2rn[ tuner_load_str ] = rn
            
        except:
            print "ERROR Could not find TUNER setting for 'Measure Sparams s2p' test line=%s load=[%s] mwvepy=%s" % \
               (self.data['linenumber'][rn], tuner_load_str, self.data['mwavepy'][rn] )

print 'FOUND %s TUNER SETTING SPARAMS' % (len(cal2rn))





self.add_new_column('mwavepy_tuner_rn')
self.add_new_column('Pout_pm_raw(dBm)')
self.add_new_column('Pout_pm Corrected(dBm)')
self.add_new_column('S21_op_pm Corrected Power Loss(dB)')
self.add_new_column('PAE Corrected(%)')
self.add_new_column('ACLR FOM Corrected(dBm)')
self.add_new_column('Load_Tuner_Loss Measured')
self.add_new_column('Load_Tuner_Loss Delta')


for fstr in ['1950', '3900', '5850']:
    self.add_new_column('S11_op_pm %s VSWR'  % fstr)
    self.add_new_column('S11_op_pm %s Phase' % fstr)
    self.add_new_column('S11_op_pm %s Z(ohm)' % fstr)
    self.add_new_column('S11_op_pm %s Zreal(ohm)'  % fstr)
    self.add_new_column('S11_op_pm %s Zimag(ohm)'  % fstr)
    self.add_new_column('S11_op_pm %s Zmag(ohm)'   % fstr)
    self.add_new_column('S11_op_pm %s Zphi'        % fstr)
    self.add_new_column('S11_op_pm %s Mag'         % fstr)


# Go through all the measurement records and add a column containing the mwavepy pointer for the matching
# Tuner load network
# The Performance data is measured using the 'ACLR' TestName 
at_load_cascaded_spar = {}  
atr_op_pm_1freq_dict = {}
substrate_s2p_1freq_dict = {}
tuner_loss_spars_dict = {}

mismatch_count = 0
for rn in range( rn_start, rn_finish ):
    testname = self.data['TestName'][rn]
    tuner_rn = None
    
    

    if testname == 'ACLR' :
    
   
      try:
           tuner_load_str = '%s %s %s %s %s %s' % \
            ( 
            self.data['VSWR' ][rn], self.data['Phase(degree)'][rn], 
            self.data['VSWR2'][rn], self.data['Phase2'       ][rn], 
            self.data['VSWR3'][rn], self.data['Phase3'       ][rn]  ) 
            
            
      except:
           str = '%s %s %s %s %s %s' % \
          ( 
            self.data['VSWR' ][rn], self.data['Phase(degree)'][rn], 
            self.data['VSWR2'][rn], self.data['Phase2'       ][rn], 
            self.data['VSWR3'][rn], self.data['Phase3'       ][rn]  ) 
           print 'ERROR in ACLR TUNER SETTING [%s]' % str
           continue


      
#      print 'phase2= %s <%s>' % ( type(self.data['Phase2'][rn]), self.data['Phase2'][rn])

      for fstr in ['1950', '3900', '5850']:
#      for fstr  in  ['1950']:
      
      
        if self.data['Phase2'][rn] == 90.0 and self.data['Phase3'][rn] == 60.0 and \
           self.data['VSWR'][rn]          == 15.0   and \
           self.data['Phase(degree)'][rn] == 110.0  and \
           self.data['Freq(MHz)'][rn]     == 1950.0 :

            dbg = True
        else:
            dbg = False
            
        tuner_load_freq_str = '%s %s' % (fstr, tuner_load_str)
            
            
        if tuner_load_freq_str in cal2rn:
            tuner_rn = cal2rn[ tuner_load_freq_str ]
            self.data['mwavepy_tuner_rn'][rn] = tuner_rn
            
        else:
            mismatch_count +=1

        
        # While we are at it lets get the raw pout data by backing out the original calibration value used
        #
        pn = 'Pout_pm(dBm)'
        cn = 'S21_op_pm(dB)'
        if pn in self.data and cn in self.data  and fstr == '1950':
            pwr_orig = self.data[pn][rn]
            cal_orig = self.data[cn][rn]
            pwr_raw  =  pwr_orig + cal_orig
            self.data[ 'Pout_pm_raw(dBm)' ][rn] =  pwr_raw


        # now we have all the data needed to recalculate the loss
        #  but only do this if we have valid tuner_load match
        if tuner_rn :
        
                
            substrate_s2p_1freq = substrate_s2p.get_single_frequency_spars(float(fstr))
            atr_op_pm_1freq = atr_op_pm.get_single_frequency_spars(float(fstr))
            
            tuner_loss_spars = self.data['mwavepy'][tuner_rn]
            
            
            # Cascade the sparameters for the substrate followed by the tuner followed by the atr (attenuator, cables and switch)
            spar1 =  substrate_s2p_1freq ** tuner_loss_spars
            spar2 =  spar1 ** atr_op_pm_1freq
#            spar2 =  spar1
            
            substrate_s21_db = s21_db(substrate_s2p_1freq)  
            tuner_s21_db     = s21_db(tuner_loss_spars) 
            atr_s21_db       = s21_db(atr_op_pm_1freq)
            cascaded_s21_db  = s21_db(spar2)
            sum_s21_db       = substrate_s21_db + tuner_s21_db + atr_s21_db

            Gp = s21_mag(spar2)**2 / ( 1 - s11_mag(spar2)**2 )
            cal_corrected_db = 10 * math.log10(Gp)

            tuner_loss_orig = self.data['Load_Tuner_Loss'][rn]

            if dbg:
                print 'dbg found ',   rn,  fstr, s11_mag(spar2), self.data['Freq(s2p)'][rn],
                at_load_cascaded_spar[fstr]      = spar2
                substrate_s2p_1freq_dict[fstr]   = substrate_s2p_1freq
                atr_op_pm_1freq_dict[fstr]       = atr_op_pm_1freq
                tuner_loss_spars_dict[fstr]      = tuner_loss_spars
                
            if 0 and fstr == '1950' and \
               self.data['VSWR'][rn]          == 15.0   and \
               self.data['Phase(degree)'][rn] == 110.0  and \
               self.data['Freq(MHz)'][rn]     == 1950.0 :
              print '(%5d  { %3d %3d }     %0.3f %0.3f %0.3f sum=%0.3f cas=%0.3f delta=%0.3f LOSS=%0.3f) %0.3f %0.3f' % \
               (rn, self.data['Phase2'][rn], self.data['Phase3'][rn],
                 substrate_s21_db, tuner_s21_db, atr_s21_db,
                 sum_s21_db,  cascaded_s21_db,  cascaded_s21_db-sum_s21_db, cal_corrected_db,
                 cal_orig, cal_corrected_db-cal_orig,
                 )


            # Save the data away so that it can be plotted
            if fstr == '1950':
                dcPwr         = self.data['Vbat(A)'][rn]  * self.data['Vbat(V)'][rn] 
                rfInPwr       = dBm_to_W( self.data['Pwr In(dBm)'][rn] )
                aclr          = self.data['ACLR 5MHz(dBc)'][rn]
                
                pwr_corrected = pwr_raw - cal_corrected_db  - 0.65    # adjust also for the typical substrate loss, so that we report the pwr at the output rather than at the drain.
                rfOutPwr      = dBm_to_W( pwr_corrected )
                pae_corrected =  (rfOutPwr / (dcPwr + rfInPwr)) * 100
                fom_corrected = pae_corrected - aclr
                
                
                
                
                self.data['S21_op_pm Corrected Power Loss(dB)'][rn]  = cal_corrected_db
                self.data['Pout_pm Corrected(dBm)' ][rn]  = pwr_corrected
                self.data['PAE Corrected(%)'       ][rn]  = pae_corrected
                self.data['ACLR FOM Corrected(dBm)'][rn]  = pae_corrected - aclr


            self.data['S11_op_pm %s Mag'   % fstr ][rn]         = s11_mag(spar2)
            self.data['S11_op_pm %s VSWR'  % fstr ][rn]         = mag2vswr( s11_mag(spar2))
            self.data['S11_op_pm %s Phase' % fstr ][rn]         = s11_phase(spar2)

            s11 = s11_reflcoeff(spar2)
                            
            Z = 50 * (1 + s11)/(1 - s11)
            self.data['S11_op_pm %s Zreal(ohm)'  % fstr ][rn] = Z.real
            self.data['S11_op_pm %s Zimag(ohm)'  % fstr ][rn] = Z.imag
            self.data['S11_op_pm %s Zmag(ohm)'   % fstr ][rn] = abs(Z)
            self.data['S11_op_pm %s Zphi'        % fstr ][rn] = math.atan2(Z.imag,Z.real)*(360.0/(2*math.pi))



            if fstr == '1950' and \
            self.data['Phase2'][rn] == 90.0 and self.data['Phase3'][rn] == 60.0 and \
               self.data['VSWR'][rn]          == 15.0   and \
               self.data['Phase(degree)'][rn] == 110.0  and \
               self.data['Freq(MHz)'][rn]     == 1950.0 :
              print '%5d [ %4d %4d ]  (%0.3f %0.3f %0.3f cas=%0.3f) tuner_vswr=%0.3f   load_vswr=%0.3f %0.1fdeg Z=(%0.2f %0.2fj)ohm' % \
               (rn, self.data['Phase2'][rn], self.data['Phase3'][rn],
                 substrate_s21_db, tuner_s21_db, atr_s21_db,  cascaded_s21_db,  
                    mag2vswr( s11_mag(tuner_loss_spars)), mag2vswr( s11_mag(spar2)), s11_phase(spar2),
                    Z.real, Z.imag
                    
                    
                 )
              print_s11( at_load_cascaded_spar[fstr] ,  'Cascaded s11 ',  int(fstr))



            # We have the tuner measurement data, lets write back the tuner loss
            if fstr == '1950':
                tuner_loss_meas    = s21_mag(tuner_loss_spars)**2 / ( 1 - s11_mag(tuner_loss_spars)**2 )
                tuner_loss_meas_db = 10 * math.log10(tuner_loss_meas)
                self.data['Load_Tuner_Loss Measured'][rn]       = tuner_loss_meas_db
                self.data['Load_Tuner_Loss Measured'][tuner_rn] = tuner_loss_meas_db
                
                if self.data['Load_Tuner_Loss'][rn] not in UNDEFS:
                    self.data['Load_Tuner_Loss Delta'][rn]       = -tuner_loss_meas_db + self.data['Load_Tuner_Loss'][rn]
                    self.data['Load_Tuner_Loss Delta'][tuner_rn] = -tuner_loss_meas_db + self.data['Load_Tuner_Loss'][rn]

                
                

#                    g.update_filter_conditions('VSWR', vswr)
#                    xyd = g.plot_graph_data( xynames, None, 'no save', 'Spur (30MHz filt) Vbat=%0.1f Pin=%0.0f Freq=%0.0f VSWR=%0.0f:1 %s' % ( vbat, pin, freq, vswr, part ) )
#                    rt  = g.measure_value( xyd,      'ymax',          '',       -36 )
### rt =  [ value , [ val_min, val_avg, val_max ], [xv, yv, rn, sn, c, d,], [ fail_count , 1 ] ]
### rt =  [ value , [ val_min, val_avg, val_max ], [xv, yv, rn, sn, c, d,], [ -1 , -1 ] ]
### rt =  None



# print the s11 details for the direct load measurement

print at_load_cascaded_spar.keys()

for freq in [1950, 3900, 5850]:

    print '========================================'

    print freq
    direct_load_s2p_1freq = direct_load_s2p.get_single_frequency_spars(freq)
    print_s11( direct_load_s2p_1freq,  'Direct Load Measurement',  freq )
    print '- - - - - - - - - - - - - - - - - -'
    print_s11( at_load_cascaded_spar['%s' % freq] ,  'Cascaded Load ',  freq )
    print '- - - - - - - - - - - - - - - - - -'
    print_s11( substrate_s2p_1freq_dict['%s' % freq] ,  'substrate',  freq )
    print_s11( tuner_loss_spars_dict['%s' % freq]    ,  'tuner',      freq )
    print_s11( atr_op_pm_1freq_dict['%s' % freq]     ,  'atr',        freq )




# print the s11 details for the substrate , tuner, atr

# print the s11 details for the constructed load

if mismatch_count > 0:
        print "ERROR There were %s performance measurements for which there was no TUNER spar data" % mismatch_count





self.gen_values_dict()

self.status.set( 'Run Script Finished' )