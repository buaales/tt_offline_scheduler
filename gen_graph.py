import sys
import time
import random
import networkx
import os
import matplotlib.pyplot as plt
from multiprocessing import Pool


from msg_scheduler import model as mmodel
from scheduler import model as tmodel

def gen_network_large(network: mmodel.Network, idx: int):
    # 1. generate a random tree and select one with 8 end-node
    enode_num = 0
    while enode_num < 40:
        enode_num = 0
        g = networkx.generators.random_tree(72)
        # check the number of end-node
        for n in g.nodes():
            if networkx.degree(g, n) == 1:
                enode_num += 1
    print("get one wiht endnode_num %d" % enode_num)
    # 1.1 write into file
    networkx.readwrite.graphml.write_graphml(g, 
        "./output/graph_large_gen/graph_{}.graphml".format(idx))

    return

def gen_network_medium(network: mmodel.Network, idx: int):
    # 1. generate a random tree and select one with 8 end-node
    enode_num = 0
    while enode_num != 16:
        enode_num = 0
        g = networkx.generators.random_tree(24)
        # check the number of end-node
        for n in g.nodes():
            if networkx.degree(g, n) == 1:
                enode_num += 1
    print("get one wiht endnode_num %d" % enode_num)
    # 1.1 write into file
    networkx.readwrite.graphml.write_graphml(g, 
        "./output/graph_medium_gen/graph_{}.graphml".format(idx))

    return

def gen_network_small(network: mmodel.Network, idx: int):
    # 1. generate a random tree and select one with 4 endnode
    enode_num = 0
    while enode_num != 4:
        enode_num = 0
        g = networkx.generators.random_tree(6)
        # check the number of end-node
        for n in g.nodes():
            nei = list(g.neighbors(n))
            if len(nei) == 1:
                enode_num += 1
    print("get one wiht endnode_num %d" % enode_num)
    # 1.1 write into file
    networkx.readwrite.graphml.write_graphml(g, 
        "./output/graph_small_gen/graph_{}.graphml".format(idx))

    return

def gen_network(net_type: int, idx: int):
    network = mmodel.Network()
    # 1. calls sub-function
    if net_type == 0:
        gen_network_small(network, idx)
    elif net_type == 1:
        gen_network_medium(network, idx)
    elif net_type == 2:
        gen_network_large(network, idx)
    else:
        print("[Benchmark Gen][ERR]: Unkown network type")
        return None
    # 2. return network
    return network

def gen_network_into_file(net_type: int, start_idx, end_idx):
    idx = start_idx
    while idx < end_idx:
        start = time.time()
        gen_network(net_type, idx)
        idx += 1
        stop = time.time()
        print("idx %d spend time: %f" % (idx, (stop - start)) )

# 生成文本格式的图存储到文件中

if __name__ == "__main__":
    print('Parent process %s.' % os.getpid())
    p = Pool(4)
    size = 300 // 4
    for i in range(4):
        p.apply_async(gen_network_into_file, args=(2, size*i, size*(i+1)))
    print('Waiting for all subprocesses done...')
    p.close()
    p.join()
    print('All subprocesses done.')