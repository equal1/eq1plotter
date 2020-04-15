
x = 0b00000001              # x is the input value written as a 8 bit binary value
y = 0                       # y will hold the result, set it to 0 to start with

for i in range(8):          # loop through all 8 bits,  'i' will increment 0..7
    y = y << 1              # shift the current y value one bit to the left (same as multiplying by 2)
    if x & ( 1<<i ) > 0 :   # Take 1 and shift by 'i' places to the left and 'and' it with x ,
                            # this will get the i'th bit form x, starting with the least significant bit, and 'and' it
        y = y + 1           # x, thhis will determine whether the bit i of x is a 1 or 0, if is is a 1 then increment y
                            # the next time round the loop y will be shifted. This will have the effect of reversing all 8 bits

print  bin(y)               # print out the binary result  ( Python 2.7 )
# print( bin(y) )           # print out the binary result  ( Python 3.5 )

