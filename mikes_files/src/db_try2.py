import math
import fractions
print 'hello mikey'




def isqrt(n):
    xn = 1
    xn1 = (xn + n/xn)/2
    while abs(xn1 - xn) > 1:
        xn = xn1
        xn1 = (xn + n/xn)/2
    while xn1*xn1 > n:
        xn1 -= 1
    return xn1

def primes2(n):
    """ Input n>=6, Returns a list of primes, 2 <= p < n """
    n, correction = n-n%6+6, 2-(n%6>1)
    sieve = [True] * (n/3)
    for i in xrange(1,int(n**0.5)/3+1):
      if sieve[i]:
        k=3*i+1|1
        sieve[      k*k/3      ::2*k] = [False] * ((n/6-k*k/6-1)/k+1)
        sieve[k*(k-2*(i&1)+4)/3::2*k] = [False] * ((n/6-k*(k-2*(i&1)+4)/6-1)/k+1)
    return [2,3] + [3*i+1|1 for i in xrange(1,n/3-correction) if sieve[i]]

prms = primes2( 1000 )[1:]

print 'primes :', prms

Ns = []
for i in prms:
    for j in prms:
        Ns.append( i*j )

Ns = set(Ns)
Ns = list(Ns)
Ns.sort()
Ns = Ns[1:]

print 'Ns= ', Ns



N = 151

for N in Ns:
    fnd = False
    Nrt = math.sqrt(N)
    if int(Nrt)==Nrt:
        print 'factors of:', N, '=', Nrt, Nrt, '  Perfect square!'
        continue
    for a in  prms[3:100]:

        F = []
        serlen = 100
        for i in range(serlen):
            F.append( a**(i+2) % N )

        for ofs in range(1,serlen/2):
            eqc = 0
            for i in range(serlen/2):
                if F[i] == F[i+ofs]:
                    eqc += 1

            if eqc == serlen/2:
                break

#        g = math.sqrt(a**ofs) + 1
#        h = math.sqrt(a**ofs) - 1
        g = isqrt(a**ofs) + 1
        h = isqrt(a**ofs) - 1
        fg = fractions.gcd(g,N)
        fh = fractions.gcd(h,N)

        if fh * fg == N and fh != 1  and fg != 1:
            fnd = True
            break

    if fnd:
        print 'factors of:', N, '=', fg, fh, '  using seed=', a, '  p=', ofs
    else:
        print '       cannot find factors of:', N, ' using seed=', a, '  p=', ofs


