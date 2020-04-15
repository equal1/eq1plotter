#!/usr/bin/python 


# relsw.py 

# General purpose script to release sw 
# Mike Asker 25-jan-10



import sys,os,getpass,re



if len(sys.argv) < 2 or not os.access(sys.argv[1], os.R_OK) or getpass.getuser() != 'projmgr':
  print '''
  *** ERROR *** User (%s) needs to be logged in as 'projmgr', Or cannot find or read input <file>
  
  To Use on Linux:
    %%   su projmgr
    %%   cd /projects/sw/release     (or other release directory)

    %%   %s  <fullpath_filename>  [V]
          
  Descrition: 
    General purpose script to release sw  

  Operation:
    1) login or su to the projmgr account, and cd to the release directory
    2) Reads the full file pathname <fullpath_filename> and finds the software version string <version>
    3) Writes these files :
          a - <filename> as is to the current directory <cwd>/<filename>
          b - as is into <cwd>/archive/<filename><version>
          c - if <filename> name contains '_dev', and the V option is given then
                  remove '_dev' from name, and change <version> from 'X' to 'V'
                  and write to <cwd>/<filename_no_dev>''' % ( getpass.getuser(), os.path.basename(  sys.argv[0]) )
  sys.exit()


fullpath_filename = sys.argv[1]
swdir        = os.path.dirname( fullpath_filename )
swname       = os.path.basename( fullpath_filename )

if len(sys.argv) > 2 and sys.argv[2] == 'V':
  swname_v     = re.sub( r'_dev', '', swname, re.I )
else:
  swname_v    =   ''



fip = open( fullpath_filename )

ver = ''
oplines = []
for line in fip:
   oplines.append( line )
   grps = re.search( '\$Revision: 1.1 $', line ) 
   if grps:
      ver = grps.groups()[0]


if ver != '':
   swname_archive  = os.path.join( 'archive', '%s_%s' % (swname, ver ) )
else:
   swname_archive  = ''



fop1 = open( swname ,        'w' )
if ver != '' and swname_archive != '' :
   fop2 = open( swname_archive, 'w' )

if ver != '' and swname_v != '' :
   fop3 = open( swname_v ,      'w' ) 


for line in oplines:
  
   print >> fop1 , line, 

   if ver != '' and swname_archive != '' :  
         print >> fop2 , line, 

   if ver != '' and swname_v != '' : 
         grps = re.search( r'txt\s*=\s*re.sub.*Revision.*(X)', line)
         if grps:
           line = re.sub(r'X', 'V', line )
         print >> fop3 , line, 
   



