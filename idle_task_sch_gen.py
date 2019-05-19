import struct

if __name__ == '__main__':
    path = './output/node_0.bin'
    peroid = 1000000
    try:
        f = open(path, 'wb')
        f.write(struct.pack('Q', 1+1))
        # all RR schedule
        entry_value = ((-1 & 0xFFFF) << 48) | (0 & 0xFFFFFFFFFFFF)
        f.write(struct.pack('Q', entry_value))
        # end entry
        entry_value = ((-1 & 0xFFFF) << 48) | (peroid & 0xFFFFFFFFFFFF)
        f.write(struct.pack('Q', entry_value))
    except IOError as e:
        print(e)
        exit(0)