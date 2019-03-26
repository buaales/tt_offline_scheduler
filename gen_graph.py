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
    while enode_num < 42:
        enode_num = 0
        g = networkx.generators.random_tree(36)
        # check the number of end-node
        for n in g.nodes():
            if networkx.degree(g, n) == 1:
                enode_num += 1
    print("Get one with endnode_num %d, index %d" % (enode_num, idx))
    # 1.1 write into file
    networkx.readwrite.graphml.write_graphml(g,
        "./output/graph_large_gen/graph_{}.graphml".format(idx))

    return

def gen_network_medium(network: mmodel.Network, file_idx: int):
    # 1. generate a random tree and select one with 8 end-node
    enode_num = 0
    while enode_num != 6:
        enode_num = 0
        g = networkx.generators.random_tree(10)
        # check the number of end-node
        for n in g.nodes():
            if networkx.degree(g, n) == 1:
                enode_num += 1
    print("Get one with endnode_num %d, index %d" % (enode_num, file_idx))
    # add endnode to 16 endnodes
    num_list = [3, 2, 2, 3]
    times, idx = 0, 10
    for node in list(g.nodes()):
        if networkx.degree(g, node) == 1:
            continue
        # it is switchNode, add endnode
        _num = num_list[times]
        for i in range(_num):
            g.add_node(idx)
            g.add_edge(idx, node)
            idx += 1
        times += 1
    assert times == 4, "Times is not equal 4"
    assert idx == 20, "Times is not equal 20"
    # 1.1 write into file
    networkx.readwrite.graphml.write_graphml(g,
        "./output/graph_medium_gen/graph_{}.graphml".format(file_idx))

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
    print("Get one with endnode_num %d, index %d" % enode_num, idx)
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
        start = time.clock()
        gen_network(net_type, idx)
        stop = time.clock()
        print("index %d spent time: %.2f" % (idx, (stop - start)))
        idx += 1

# 生成文本格式的图存储到文件中

if __name__ == "__main__":
    '''
    print('Parent process %s.' % os.getpid())
    p = Pool(4)
    size = 300 // 4
    start_idx = 0
    for i in range(4):
        p.apply_async(gen_network_into_file, args=(1, start_idx+size*i, start_idx+size*(i+1)))
    print('Waiting for all subprocesses done...')
    p.close()
    p.join()
    print('All subprocesses done.')
    '''
    gen_network_into_file(1, 0, 100)
