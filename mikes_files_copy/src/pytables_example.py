import numpy as np
import tables as tb
ndim = 60000
h5file = tb.openFile('test.h5', mode='w', title="Test Array")
root = h5file.root
x = h5file.createCArray(root,'x',tb.Float64Atom(),shape=(ndim,ndim))
x[:1000,:1000] = np.random.random(size=(1000,1000)) # Now put in some data
h5file.close()

