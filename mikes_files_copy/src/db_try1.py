
print 'hello mikey'

import __main__ as M

print M.mag

g = M.mag

x= g.mercury_scriptlist.info_data( 'SJC-DCTR-PAR-1_24325' )

print 'x=', g.mercury_scriptlist['columns'].keys()

# dr =  dir(g.mercury_scriptlist.info_data)
# 
# for d in dr:
#     print d , type(d)
# 
# g.wclearfiles()
# 
# x = g.mercury_tester_list.info_selection()
# print x

#g.mercury_partnums.values = ['a','b']
#print g.mercury_partnum.values
#g.mercury_partnum.set('hello')



# for name in vallist:
#    g.mercury_partnums.insert( Tix.END, name )

# vars = g.mercury_partnums.config()
# for v in vars:
#     print v, vars[v]


# dr = dir(g.mercury_partnums)
# for d in dr:
#     print d 


#     def func(x, y):
#     #    y = 3 * y
#         return x*(1-x)*np.cos(4*np.pi*x) * np.sin(4*np.pi*y**2)**2
#     # on a grid in [0, 1]x[0, 1]
#     
#     grid_x, grid_y = np.mgrid[0:1:100j, 0:1:200j]
#     # but we only know its values at 1000 data points:
#     
#     points = np.random.rand(100, 2)
#     
#     print len(points), type(points)
#     print points
#     values = func(points[:,0], points[:,1])
#     # This can be done with griddata below we try out all of the interpolation methods:
#     print len(values), type(values)
#     print values
#     
#     from scipy.interpolate import griddata
#     
#     
#     grid_z2 = griddata(points, values, (grid_x, grid_y), method='cubic')
#     
#     # One can see that the exact result is reproduced by all of the methods to some degree, but for this smooth function the piecewise cubic interpolant gives the best results:
#     
#     import matplotlib.pyplot as plt
#     
#     #plt.subplot(222)
#     plt.imshow(grid_z2.T, extent=(0,1,0,1), origin='lower')
#     plt.title('tmp')
#     
#     # plt.gcf().set_size_inches(6, 6)
#     plt.show()