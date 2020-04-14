
from __main__ import *

from math import *

import types

#######################################################################################################################
def create_offset_target(target, minmax):
    '''Create new target line, which is offset from the input
    #   [ [1500,-3],   [1650,-3], ]    <- input target
    #   [ [1500,-3.2], [1650,-3.2] ]   <- ouput offset target
    '''

    print 'target=', target

    yoffset = (g.ylimits[1] - g.ylimits[0]) / 50.0
    xoffset = (g.xlimits[1] - g.xlimits[0]) / 50.0

    dx = (target[1][0] - target[0][0])/xoffset    # x delta expressed as a fraction of xaxis range
    dy = (target[1][1] - target[0][1])/yoffset


    # Calculate the angle of the line
    # ang = 0 for horizontal lines dx/r = 1 -> acos(1) = 0 deg
    ang = ango = atan2(dy,dx)

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

    print target, minmax, (ang)*(180/pi), (ang-ango)*(180/pi),  dx, dy


    yofs =  sin(ang) * yoffset    # a horizontal delta (dx) results in a y offset
    xofs =  cos(ang) * xoffset    # a vertical delta (dy) results in an x offset

    new_target = []
    i = 0
    for point in target:
        if isinstance(point, types.StringTypes):   # skip over any text options
            continue
        new_target.append([point[0] + xofs, point[1] + yofs])

    print 'new_target=', new_target

    return new_target


#######################################################################################################################
def plt(xynames, x_axis=None, y_axis=None, titletxt=None, spec_limit=None):
    '''Function to plot the data, setup the axes, and measure the results'''

    g.xlimits = x_axis
    g.ylimits = y_axis

    if spec_limit == [] or spec_limit != None:
        make_spec_limits(spec_limit)

        print 'g.spec_limits=', g.spec_limits


    xyd = g.plot_graph_data(xynames, titletxt=titletxt, savefile=titletxt)


def make_spec_limits( target=None, text='', color='red', minmax='x' ):

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
        g.spec_limits = None
    elif target != None:

        g.spec_limits = []
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

            print 'tg=', tg

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
                tg_shaded = create_offset_target(tg, minmax)
                g.spec_limits.append([tg_shaded, text, 20, '%s %s' % (color_shade, color)])
                text = ''

            g.spec_limits.append([tgn, text, 3, color])
    else:
        g.spec_limits = None


logfile = r'T:/CMOS_PA/shared/Projects/Orion (RF5228 RF5238)/Eng_Test_Results/MikeAsker/orion_EDGE_Pypat_default_ma1_EVB_MTK_ES2_SN18_atr6_17jun15_1630.log'
g.wclearfiles()
g.add_logfiles(logfile)



spec_limit = [
               [[18, -34],   [19, -34], '< red'],
               [[19, -34],   [20, -38], 'cyan'],
               [[20, -40],   [20, -38], ],
               [[19, -44],   [20, -40], '> magenta'],
               [[18, -44],   [19, -44], 'm2'],
               [[18, -44],   [17, -40], 'blue' ],
               [[17, -40],   [17, -38], ],
               [[17, -38],   [18, -34], '<'],

               [[22, -34],   [23, -34], '> GrEen MIKE'],
               [[23, -34],   [24, -38], ],
               [[24, -40],   [24, -38], ],
               [[23, -44],   [24, -40], '<'],
               [[22, -44],   [23, -44], 'black m4'],
               [[22, -44],   [21, -40], ],
               [[21, -40],   [21, -38], 'yellow'],
               [[21, -38],   [22, -34], '>'],

               ]

#spec_limit = '> -56 Limit of ACPR green'
#spec_limit = -50
#spec_limit = [ [23,-48],[27,-50], '> green Mikes Limit' ]

#        Xname        Yname             Xlimits    Ylimits     Title          Spec(opt)
plt( ['Pout(dBm)','ACP +400KHz(dBm)'],  [16,30],  [-60,-30], 'Mikeys Plot', spec_limit)




