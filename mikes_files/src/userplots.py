

logfile = r'T:/CMOS_PA/shared/Projects/Orion (RF5228 RF5238)/Eng_Test_Results/MikeAsker/orion_EDGE_Pypat_default_ma1_EVB_MTK_ES2_SN18_atr6_17jun15_1630.log'
g.wclearfiles()
g.add_logfiles(logfile)

spec_limit = [ [[17,-50], [20,-50],'< cyan Pout Max'],
               [[20,-50], [25,-40], ],
               [[25,-40], [25,-32], '>' ],
               [[22,-58], [22,-56], '< green'],
               [[22,-56], [29,-42], '> Pout Min' ], ]


g.update_filter_conditions( 'Vbat(Volt)',  3.5    )
g.set_color( 'Freq(MHz)'  )
g.set_line( 'Temp(C)'  )

#               Xname        Yname             Xlimits    Ylimits       Title          Spec(opt)
g.plotdata( ['Pout(dBm)','ACP +400KHz(dBm)'],  [16,30],  [-60,-30], 'Mikes ACPR Plot', spec_limit)



