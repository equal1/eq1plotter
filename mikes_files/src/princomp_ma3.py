print 'this is the princomp.py'
import __main__ 
import __main__ as M
self = M.mag
self.status.set( 'Run Script ' )

from numpy import mean,cov,double,cumsum,dot,linalg,array,rank
from pylab import plot,subplot,axis,stem,show,figure
import numpy
import scipy.linalg as slin

def make_fake_data():
    #                  DR1 DR2 C14
    #                 rows=#data_points
    #                      cols=variables   Fpk, DR1, DR2, C14

    n = 3
    A = numpy.ndarray([n**3,3])
    Y = numpy.ndarray([n**3])

    vals = numpy.linspace( 0.0,1.0,n)

    row = 0
    for DR1 in vals:
        for DR2 in vals:
            for C14 in vals:


                Fpk = 2700 - 400*DR1 - 100*DR2 + 50*C14

                # Row number
                Y[ row ] = Fpk
                A[ row, 0 ] = DR1
                A[ row, 1 ] = DR2
                A[ row, 2 ] = C14
                row += 1

    return A, Y

def princomp(A):
     """ performs principal components analysis
         (PCA) on the n-by-p data matrix A
         Rows of A correspond to observations, columns to variables.

     Returns :
      coeff :
        is a p-by-p matrix, each column containing coefficients
        for one principal component.
      score :
        the principal component scores; that is, the representation
        of A in the principal component space. Rows of SCORE
        correspond to observations, columns to components.
      latent :
        a vector containing the eigenvalues
        of the covariance matrix of A.
     """
     # computing eigenvalues and eigenvectors of covariance matrix
     M = (A-mean(A.T,axis=1)).T # subtract the mean (along columns)
     [latent,coeff] = linalg.eig(cov(M)) # attention:not always sorted
     score = dot(coeff.T,M) # projection of the data in the new space

     idx = argsort(latent) # sorting the eigenvalues
     idx = idx[::-1]       # in ascending order
     # sorting eigenvectors according to the sorted eigenvalues
     coeff = coeff[:,idx]
     latent = latent[idx] # sorting eigenvalues

     return coeff,score,latent




# A = array([ [2.4,0.7,2.9,2.2,3.0,2.7,1.6,1.1,1.6,0.9,0.3],
#             [2.5,0.5,2.2,1.9,3.1,2.3,2,1,1.5,1.1,0.1] ])


A,Y = make_fake_data( )
print 'A=' , A


lu = slin.lu_factor(cm)

soln = slin.lu_solve(lu,Y)
print 'soln=', soln

#coeff, score, latent = princomp(A)
#
# print 'A=', A.size, A.shape
#
# print 'latent=', latent.size, latent.shape
# print 'coeff=', coeff.size, coeff.shape
# print 'score=', score.size, score.shape
#
#
# #print 'A.T=' , A.T
# print 'coeff=', coeff
# print 'score=', score
# print 'latent=', latent
#
# # every eigenvector describe the direction
# # of a principal component.
# m = mean(A,axis=1)
#
#
# figure()
# subplot(121)
#
# plot([0, -coeff[0,0]*2]+m[0], [0, -coeff[0,1]*2]+m[1],'--k')
# plot([0, coeff[1,0]*2]+m[0], [0, coeff[1,1]*2]+m[1],'--k')
# plot(A[0,:],A[1,:],'ob') # the data
# axis('equal')
# subplot(122)
# # new data
# plot(score[0,:],score[1,:],'*g')
# axis('equal')
# show()
# print 'coeff=', coeff
# print 'score=', score
# print 'latent=', latent
#
#

