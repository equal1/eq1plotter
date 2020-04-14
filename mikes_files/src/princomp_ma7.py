import numpy as np
import scipy
import matplotlib.pyplot as plt


print 'This is script princomp_ma7.py'
import __main__ as M
self = M.mag
self.status.set( 'running script' )


use_real_data = 1

if use_real_data:



    if 1:
        self.wclearfiles()
        cols = 'CR0_requested CR1_requested C14'.split()     # These are the columns names containing all the dependent coefficient values
        mcolname = 'Fpk(MHz)'
        self.add_logfile( r'C:\Log File\cr0_cr1_sweep_ma2_xxxx_atrMA1_18feb15_1409.log')
        self.win_load()
#        self.update_filter_conditions( 'C14' , 0.5 )
#        self.update_filter_conditions( 'CR1_requested', '-1..0.6' )
    else:
        cols = self.xnames_ordered
        mcolname = self.ynames_ordered[0]


    # Get an array of all the measurement values.
    b_raw = np.array(self.data[mcolname] )
    # Then filter the value and choose only those values that have good non-null X and Y values
    self.xnames_ordered = cols
    self.ynames_ordered = [mcolname]    # needed so that we can also filter out X and Y data values that are UNDEF
    b_idxs = self.get_selected_rn_list()
    b = b_raw[b_idxs]
    # print 'b_raw.shape and b.shape=', b_raw.shape, b.shape


    # Make up an array of the correct shape, and fill it with data from the pygram data array for the selected coefficients
    A= np.zeros( (len(cols)+1, len(b)))    # Make up an empty array big enough to hold all the coefficient values plus 1 for the y0 coefficient
    for i,c in enumerate(cols):          # Copy each column list of coefficient values into the coefficient array A
        a1 = np.array( self.data[c] )
        a2 = a1[b_idxs]                  # Only use the filtered cooefficient values for which there are valid measurement results
        A[i] = a2
    # Finally add an all ones row to A for the y0 Constant
    A[len(cols)] = np.array( ( [1.] * len(b) ))
    A = A.T                              # Transpose the array to make it the right shape for lstsq and qr operations
    # print 'A.shape=', A.shape



else:
    # A simple test case to see that the curve fitting decomposition is working
    # Example illustrating a common use of qr: solving of least squares problems
    # What are the least-squares-best m and y0 in y = y0 + mx for the following data: {(0,1), (1,0), (1,2), (2,1)}.
    # Solution is y0 = 0, m = 1.
    # The answer is provided by solving the over-determined matrix equation Ax = b,
    A = np.array([[0, 1], [1, 1], [1, 1], [2, 1]])
    b = np.array([1,0,2,1])




# A few of the measurement results may be bad, filter them out using numpy's 'where index' syntax
print 'A.shape=', A.shape
print A

print 'b.shape=', b.shape
print b

print "\n------------------"
print "Solutions compared"
print "------------------\n"

# solve Ax = b using the standard numpy function
x_lstsq = scipy.linalg.lstsq(A,b)[0]
print x_lstsq,' Ax=b (Least Squares solution)\n'

# Solve Ax = b using Q and R
Q,R = scipy.linalg.qr(A, mode='economic')  # qr decomposition of A
Qb = np.dot(Q.T,b)        # computing Q^T*b (project b onto the range of A)
#x_qr = scipy.linalg.solve(R,Qb) # solving R*x = Q^T*b
x_qr = scipy.linalg.solve_triangular(R,Qb, check_finite=False) # solving R*x = Q^T*b

print 'Q=', Q.shape, Q
print 'R=', R.shape, R
print x_qr,'Rx=y  (QR decomposition solution)'


if use_real_data:

    # Regenerate the entire measurements data based on component analysis
    pcolname = 'Predicted'
    self.add_new_column( pcolname )
    dcolname = 'Delta'
    self.add_new_column( dcolname )

    # go through all the valid coefficient values
    # and use the coefficient components to recreate the measurement data
    # cols_rev = cols[:]
    # cols_rev.reverse()
    for idx in b_idxs:
        predicted_val = 0
        dstr = ''
        for i,coeffname in enumerate(cols):
            coeffval = self.data[coeffname][idx]
            predicted_val += coeffval*x_qr[i]
        # Add the y0 constant
        predicted_val += x_qr[-1]
        self.data[pcolname][idx] = predicted_val
        self.data[dcolname][idx] = self.data[mcolname][idx] - predicted_val
    self.add_values_dict( pcolname )
    self.add_values_dict( dcolname )

    # Update the GUI with the new data
    self.win_load()
    self.xnames_ordered = cols
    self.ynames_ordered.append( 'Predicted' )
    self.select_columns( self.xaxis_col_list, self.xnames_ordered )
    self.select_columns( self.yaxis_col_list, self.ynames_ordered )
    self.plot_interactive_graph()



self.status.set( 'script finished' )