#!/tools/gnu/Linux/bin/python

# Load the pygram libraries 

import sys
#sys.path.append(r'/projects/sw/release')
#sys.path.append(r'N:\sw\release')
from pygram_dev import *


###################################################################
#
# Create an pygram instance, this creates an epygram data structure 
# into which we will load all the logfile data
#
###################################################################

mag = pygram()
#g = mag

###################################################################
#
# read in the logfiles
#
###################################################################

for p in sys.argv[1:]:
   mag.add_logfile(  p  )


mag.loop()
