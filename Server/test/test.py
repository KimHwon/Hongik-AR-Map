import recv
from queue import Queue

s = b'\x01\x23\xff\x00\x45\x67\x89\xab'
idx = s.find(b'\xff\x00')
for b in s[:idx]:
    print(hex(b))

l = []
l.append(s[:0])
print(l)