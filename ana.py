
file = open('./log', 'r')

d = {}
for line in file.readlines():
    num = int(line[10:])
    if not num in d:
        d[num] = 0

    d[num] += 1

for n in d:
    print('%d num is %d' % (n, d[n]))
