import numpy as np
'''
file = open('./log', 'r')

d = {}
for line in file.readlines():
    num = int(line[10:])
    if not num in d:
        d[num] = 0

    d[num] += 1

for n in d:
    print('%d num is %d' % (n, d[n]))
'''
if __name__ == '__main__':
    num = 6
    l = []
    for i in range(num):
        l.append(0.75)
    a = np.random.dirichlet(l * 100, size = 1)
    b = a[0]
    print (sum(b))

