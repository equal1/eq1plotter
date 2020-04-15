# -*- mode: python -*-


def TixTree ():
         print config
         config['TCL_root'] = r'C:\Python27\tcl\tcl8.5'
         tixroot = os.path.join (config['TCL_root'], os.path.pardir)
         for root, dirs, files in os.walk (tixroot):
                 for i in dirs:
                         if i.lower().startswith ('tix'):
                                 tixroot = os.path.join (tixroot, i)
                                 break
         tixroot = os.path.normpath (tixroot)
#         tixroot = r'C:\Python27\tcl\tix8.4.3'
         print ">>>TIXROOT", tixroot
         tixnm = os.path.join ('_MEI', os.path.basename (tixroot))
         tixdll = None
         dllroot=os.path.join (config['TCL_root'], os.path.pardir, os.path.pardir, "DLLs")
         dllroot = tixroot
         for root, dirs, files in os.walk (dllroot):
                 for i in files:
                         j = i.lower ()
                         if j.startswith ('tix') and j.endswith ('.dll'):
                                 tixdll = (root, i)
         print ">>>TIXDLL", tixdll[1]
         return Tree (tixroot, tixnm) + [(tixdll[1], os.path.join(tixdll[0], tixdll[1]), 'BINARY')]



a = Analysis(['pygram_gui_dev.py'],
             pathex=['N:\\sw\\user\\ma024577\\pygram\\src'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          TixTree(),
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='pygram_gui_dev.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
