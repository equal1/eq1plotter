
            #  Add the Parameter data
            #  Look for Special  && lines

            if len(row0) > 1 and row0.find('$$Parametric') == 0:
               flds = row0.split('}')

               get_regs = False
            
               for fld in flds:
                 fld = fld.strip()
                 if len(fld) > 2:


                     if fld.find('Accumulated Reg Settings') > 0:  #searching for:   'Accumulated Reg Settings = 38{13:9;8};'
                        get_regs = True
                        amp_type = grps.groups()[0]
                        amp_type = amp_type.lower()
                        amp_prefix = '[$$Parametric] ' 
                        amp_array[ amp_prefix ] = []

 
                       
                     if get_regs:
                        grps = re.search( r'(\d+)\s*{\s*(\d+)\s*[:;]\s*(\d+)\s*[:;]\s*(\d+)', fld)           #searching for:   '38{13:9;8};'
 
                        if grps and len(grps.groups())==4 :
                            reg_num       = grps.groups()[0]
                            reg_stop_bit  = grps.groups()[1]
                            reg_start_bit = grps.groups()[2]
                            reg_value     = grps.groups()[3]

                            n = 'Reg%s[%s:%s]' % ( reg_num, reg_stop_bit, reg_start_bit ) 
                            colname = '%s %s' % ( amp_prefix,  n )
                            self.add_new_column( colname )
                            camp2num[ colname ] = 'done'

                            v = float( reg_value )
                            amp_array[ amp_prefix ].append( [colname, v ] )



