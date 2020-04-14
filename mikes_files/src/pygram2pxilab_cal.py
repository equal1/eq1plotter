
#g.wclearfiles()
#logfiles = g.add_all_logfiles_dialog()


#logfile = r'L:\Lab & Testing\Test Stations\Calibration\pxilab\results\pxilab_calibraton_calibration__04aug16_1609.log'
#logfile = r'L:\Lab & Testing\Test Stations\Calibration\pxilab\results\pxilab_calibration_calibration__24aug16_1121.log'
#logfile = r'L:\Lab & Testing\Test Stations\Calibration\pxilab\results\pxilab_calibration_calibration_cal_22feb17_1606.log'
#logfile = r'L:\Lab & Testing\Test Stations\Calibration\pxilab\results\pxilab_calibration_5G_calibration__16mar17_1302.log'
#logfile = r'L:\Lab & Testing\Test Stations\Calibration\pxilab\results\pxilab_calibration_5G_thru_cal_26apr17_1045.log'
#logfile = r'L:\Lab & Testing\Test Stations\Calibration\pxilab\results\pxilab_calibration_5G_thru_thru_loaner_vst2_05jun17_1340.log'
#logfile = r'L:\Lab & Testing\Test Stations\Calibration\pxilab\results\pxilab_calibration_5G_thru_thru_new_vst2_05jun17_1610.log'
#logfile = r'L:\Lab & Testing\Test Stations\Calibration\pxilab\results\pxilab_calibration_5G_thru_thru_calibration_14jun17_1101.log'
#logfile = r'L:\Lab & Testing\Test Stations\Calibration\pxilab\results\pxilab_calibration_5G_debug2_AD1175_E3.065.2_P9_31jul17_1729.log'
#logfile = r'L:\Lab & Testing\Test Stations\Calibration\pxilab\results\pxilab_calibration_5G_debug2_cal_cal_01aug17_1348.log'
#logfile = r'L:\Lab & Testing\Test Stations\Calibration\pxilab\results\pxilab_calibration_5G_debug4_thru_calibration_12jan18_1113.log'
logfile = r'L:\Lab & Testing\Test Stations\Calibration\pxilab\results\pxilab_calibration_5G_debug4_thru_calibration_28jun18_0858.log'

g.add_logfiles(logfile)

opfile = logfile + '.csv'

fop = open(  opfile, 'w' )

# spec_limit = [ [[17,-50], [20,-50],'< cyan Pout Max'],
#                [[20,-50], [25,-40], ],
#                [[25,-40], [25,-32], '>' ],
#                [[22,-58], [22,-56], '< green'],
#                [[22,-56], [29,-42], '> Pout Min' ], ]


g.update_filter_conditions( 'Description',  'HB Input Path'    )
g.set_color( 'Pin'  )
#                    Xname     Yname        Xlimits    Ylimits
res_ip = g.plotdata( ['Freq','Pout_pm(dBm)'],  [0,7e9],  [-100,0])   # power measured at the DUT input port
res_ipc = g.plotdata( ['Freq','Pin_cplr(dBm)'],  [0,7e9],  [-100,0])   # input coupler power


g.update_filter_conditions( 'Description',  'Output Paths'    )
res_opc = g.plotdata( ['Freq','Pout_pm(dBm)'],  [0,7e9],  [-100,0])   # power measured on the output coupler using a thru
res_sa = g.plotdata( ['Freq','Pout_sa(dBm)'],  [0,7e9],  [-100,0]) # power measured on the SA using a thru

#  res = [xvals, yvals, rnvals, snvals, cvals, dvals, full_condition_selected_str, xynames]


xs = res_ip[0][0]      #   frequencies
ps = res_ip[3]       #   desired input power level sent to the siggen
yipcs = res_ipc[1]   # power measured at the input coupler using power sensor PM2
yipduts = res_ip[1]     # power measured at the DUT input port using the output side power sensor PM1
yopcs = res_opc[1]     # power measured at the output coupler using the output side power sensor PM1
yopsas = res_sa[1]     # power measured at the SA




def write_out_val_list( vals, copy=None ):
    txt = ''
    validx1 = 0
    for validx in range(len(vals)+2):
        val = vals[validx1]
        if validx > 0 and validx < len(vals):
            validx1 += 1
        if copy!=None:
            if validx == 0:  val = copy[0]
            if validx == len(vals)+1:  val = copy[1]
        txt += '%s, ' % val
        print val, ',',

    print ''
    fop.write('%s\n' % txt)

def write_out_val_table( xs, ps, y1s, y2s, xcopy=None, pcopy=None ):
    '''Writes out a 2D table of calibration y1s - y2s numbers. If either the y1s are None
    then they default to 0.0 allowing tables of positive, negative and difference values
    to be written.
    The rows are the power levels, and the columns are the frequency values.
    The first and last rows and columns are duplicated to define extreme ranges so that
    offsets for all possible power and frequencies are output, even if outside the calibrated range.
    (This is needed mainly for the low power calibration where calibration is not reliable using
    the Power Sensors.)
    '''
    pidx1 = 0
    for pidx in range(len(ps)+2):
        txt = ''
        xidx1 = 0
        for xidx in range(len(xs)+2):
            if y1s:
                y1 = y1s[pidx1][xidx1]
            else:
                y1 = 0.0
            if y2s:
                y2 = y2s[pidx1][xidx1]
            else:
                y2 = 0.0

            y = float(y1) - float(y2)

            # We add extra rows and columns before and after the table to extend the range
            # so that we can calibrate for any frequency and power level, even if it is outside the
            # calibrated range. Sometimes we want to copy the data to the extreme ranges sometimes
            # we want to force very small or very large numbers to define the extreme ranges
            # this is controlled with the xcopy and pcopy parameters
            if xidx > 0 and xidx < len(xs):
                xidx1 += 1
            if xcopy!=None:
                if xidx == 0:  y = xcopy[0]
                if xidx == len(xs)+1:  y = xcopy[1]
            if pcopy!=None:
                if pidx == 0:  y = pcopy[0]
                if pidx == len(ps)+1:  y = pcopy[1]

            txt += '%s, ' % y
            print y, ',',
        print ''
        fop.write('%s\n' % txt[:-2])  # remove the last ',' comma

        if pidx > 0 and pidx < len(ps):
            pidx1 += 1

    print ''


xfs = []
for y in ps:
    lst = []
    for x in xs:
        lst.append(float(x))
    xfs.append(lst)

yps = []
for y in ps:
    lst = []
    for x in xs:
        lst.append(float(y))
    yps.append(lst)

write_out_val_list( xs, copy=[0,30e9] )
write_out_val_list( ps, copy=[-200,+200] )

write_out_val_table( xs, ps, xfs, None, xcopy=[0,30e9] )       # Frequency Table
write_out_val_table( xs, ps, yps, None,pcopy=[-200,+200] )       # Desired Pin Table
write_out_val_table( xs, ps, yipduts, None, pcopy=[-200,+200] ) #mm  # DUT Measured PIN Table
write_out_val_table( xs, ps, yps, yipduts )  # cc  # Siggen offset ( Desired Power - Actual power at DUT input )
write_out_val_table( xs, ps, yipduts, yipcs )  # Input Coupler offset ( Actual power at DUT input - IP Coupler Power )
write_out_val_table( xs, ps, yipduts, yopcs )  # Output Coupler offset ( Actual power at DUT Output - OP Coupler Power )
write_out_val_table( xs, ps, yipduts, yopsas )  # Output VST SA offset ( Actual power at DUT Output - OP VST SA Power )
write_out_val_table( xs, ps, yipcs, None, pcopy=[-200,+200] )   # mm  # Power Measured at the IP Coupler with the IP Power Sensor
write_out_val_table( xs, ps, yopcs, None, pcopy=[-200,+200] )   # mm  # Power Measured at the OP Coupler with the OP Power Sensor
write_out_val_table( xs, ps, yopsas, None, pcopy=[-200,+200] )  #mm  # Power Measured at the VST SA using the VST SA


fop.close()


