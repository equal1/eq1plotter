import numpy as np
import matplotlib.pyplot as plt


# x = np.array([0, 1, 2, 3])
# y = np.array([-1, 0.2, 0.9, 2.1])
#
#
# A = np.vstack([x, np.ones(len(x))]).T
# m, c = np.linalg.lstsq(A, y)[0]
# print m, c
#
# plt.plot(x, y, 'o', label='Original data', markersize=10)
# plt.plot(x, m*x + c, 'r', label='Fitted line')
# plt.legend()
# plt.show()


print 'this is the pygram_script.py'
import __main__
import __main__ as M
self = M.mag
self.status.set( 'Run Script Running Again' )



from sklearn import ensemble
from sklearn import datasets
from sklearn.utils import shuffle
from sklearn.metrics import mean_squared_error

###############################################################################
# Load data
# boston = datasets.load_boston()
# #X, y = shuffle(boston.data, boston.target, random_state=13)
# X, y = boston.data, boston.target
# X = X.astype(np.float32)
# offset = int(X.shape[0] * 0.9)
# X_train, y_train = X[:offset], y[:offset]
# X_test, y_test = X[offset:], y[offset:]
# ###############################################################################




import pprint
import scipy
import scipy.linalg   # SciPy Linear Algebra Library

A = scipy.array([[12, -51, 4], [6, 167, -68], [-4, 24, -41]])  # From the Wikipedia Article on QR Decomposition
Q, R = scipy.linalg.qr(A)

print "A:"
pprint.pprint(A)

print "Q:"
pprint.pprint(Q)

print "R:"
pprint.pprint(R)

from numpy import *

A = floor(random.rand(4,4)*20-10) # random matrix
b = floor(random.rand(4,1)*20-10)


A = array([[0, 1], [1, 1], [1, 1], [2, 1]])
b = array([[1], [0], [2], [1]])



# solve Ax = b using the standard numpy function
x = linalg.lstsq(A,b)

# solve Ax = b using Q and R
Q,R = linalg.qr(A) # qr decomposition of A
y = dot(Q.T,b)
xQR = linalg.solve(R,y)

print "\nSolution compared"
#print x.T,'Ax=b'
#print xQR.T,'Rx=y'
print x,'Ax=b'
print xQR,'Rx=y'


