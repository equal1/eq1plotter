#!/usr/bin/python

# Load the libraries 
import sys, time
#sys.path.append(r'/projects/sw/user/masker/pygram/src')
sys.path.append(r'/projects/sw/release')
sys.path.append(r'N:\sw\release')
from pygram_dev import *


# start pygram
g = pygram()
g.savedir = 'N:/sw/user/masker/pygram/opfiles'

files = g.get_readfiles_dialog( 'Select ATR Log files to load', 'loaddir' ,  )

#files = [ 'N:/sw/user/masker/pygram/ipfiles/AM7801_TA5_T_U_CG_Spurs_ATR2_SN006S.log' ]



for file in files:

   file = file.strip()

   fileop = re.sub( r'.log$', '_mod1.log', file )
   f = open( file )
   fop = open( fileop, 'w' )

   for line in f:

       if line[:15] == '//Spurious Data':
           line = re.sub( r'//Spurious Data', '//Spurious Data\t\t\t\t\t', line )

       print >> fop , line,

   f.close()





