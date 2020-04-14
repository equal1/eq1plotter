print 'this is the princomp.py'
import __main__ 
import __main__ as M
self = M.mag
self.status.set( 'Run Script ' )





from numpy import mean,cov,cumsum,dot,linalg,size,flipud

def princomp(A,numpc=0):
     # computing eigenvalues and eigenvectors of covariance matrix
     M = (A-mean(A.T,axis=1)).T # subtract the mean (along columns)
     [latent,coeff] = linalg.eig(cov(M))
     p = size(coeff,axis=1)
     idx = argsort(latent) # sorting the eigenvalues
     idx = idx[::-1]       # in ascending order
     # sorting eigenvectors according to the sorted eigenvalues
     coeff = coeff[:,idx]
     latent = latent[idx] # sorting eigenvalues
     if numpc < p and numpc >= 0:
          coeff = coeff[:,range(numpc)] # cutting some PCs if needed
     score = dot(coeff.T,M) # projection of the data in the new space
     return coeff,score,latent


from PIL import Image
from pylab import imread,subplot,imshow,title,gray,figure,show,NullLocator
A = imread('face.png') # load an image
#A = imread('face.jpg') # load an image


A = mean(A,2) # to get a 2-D array
full_pc = size(A,axis=1) # numbers of all the principal components
print 'Number of all the principal components', full_pc
i = 1
dist = []
print 'A[]=', A
for numpc in range(0,18,3): # 0 10 20 ... full_pc
      print 'doing numpc', numpc
      coeff, score, latent = princomp(A,numpc)
      print '================================='
      print 'A=', A.size, A.shape
      print 'latent=', latent.size, latent.shape
      print 'coeff=', coeff.size, coeff.shape
      print 'score=', score.size, score.shape
      Ar = dot(coeff,score).T+mean(A,axis=0) # image reconstruction
      # difference in Frobenius norm
      dist.append(linalg.norm(A-Ar,'fro'))
      # showing the pics reconstructed with less than 50 PCs
      ax = subplot(2,3,i,frame_on=False)
      ax.xaxis.set_major_locator(NullLocator()) # remove ticks
      ax.yaxis.set_major_locator(NullLocator())
      i += 1
      imshow(Ar.real)
      title('PCs # '+str(numpc))
      gray()

show()




self.status.set( 'Run Script Finished' )