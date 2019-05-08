import sys
import time
import random
import networkx
import os
import matplotlib.pyplot as plt
from multiprocessing import Pool


from msg_scheduler import model as mmodel
from scheduler import model as tmodel

def gen_network_huge(network: mmodel.Network, file_idx: int):
    # 43 switch and 432 endnode
    enode_num = 0
    while enode_num != 23:
        enode_num = 0
        g = networkx.generators.random_tree(66)
        # check the number of end-node
        for n in g.nodes():
            if networkx.degree(g, n) == 1:
                enode_num += 1
    print("Get one with endnode_num %d, index %d" % (enode_num, file_idx))
    # add endnode to 48 endnodes
    num_list = [9 if x%2==1 else 10 for x in range(43)]
    times, idx = 0, 66
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
    #check
    enode_num = 0
    total_num = 0
    for n in g.nodes():
        total_num += 1
        if networkx.degree(g, n)  == 1:
            enode_num += 1
    assert enode_num == 432, "Large Check failed in enode_num"
    assert total_num == 475, "Large Check failed in total_num"
    # 1.1 write into file
    networkx.readwrite.graphml.write_graphml(g,
        "./output/graph_huge_gen/graph_{}.graphml".format(file_idx))

    return

def gen_network_large(network: mmodel.Network, file_idx: int):
    # 15 switch and 48 endnode
    # 1. generate a random tree and select one with 8 end-node
    enode_num = 0
    while enode_num != 18:
        enode_num = 0
        g = networkx.generators.random_tree(33)
        # check the number of end-node
        for n in g.nodes():
            if networkx.degree(g, n) == 1:
                enode_num += 1
    print("Get one with endnode_num %d, index %d" % (enode_num, file_idx))
    # add endnode to 48 endnodes
    num_list = [2 for x in range(15)]
    times, idx = 0, 33
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
    #check
    enode_num = 0
    total_num = 0
    for n in g.nodes():
        total_num += 1
        if networkx.degree(g, n)  == 1:
            enode_num += 1
    assert enode_num == 48, "Large Check failed in enode_num"
    assert total_num == 63, "Large Check failed in total_num"
    # 1.1 write into file
    networkx.readwrite.graphml.write_graphml(g,
        "./output/graph_large_gen/graph_{}.graphml".format(file_idx))

    return

def gen_network_medium(network: mmodel.Network, file_idx: int):
    # 13 switch and 36 end
    # 1. generate a random tree and select one with 8 end-node
    enode_num = 0
    while enode_num != 10:
        enode_num = 0
        g = networkx.generators.random_tree(23)
        # check the number of end-node
        for n in g.nodes():
            if networkx.degree(g, n) == 1:
                enode_num += 1
    print("Get one with endnode_num %d, index %d" % (enode_num, file_idx))
    # add endnode to 16 endnodes
    num_list = [2 for x in range(13)]
    times, idx = 0, 23
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
    #check
    enode_num = 0
    total_num = 0
    for n in g.nodes():
        total_num += 1
        if networkx.degree(g, n)  == 1:
            enode_num += 1
    assert enode_num == 36, "Medium Check failed in enode_num"
    assert total_num == 49, "Medium Check failed in total_num"
    # 1.1 write into file
    networkx.readwrite.graphml.write_graphml(g,
        "./output/graph_medium_gen/graph_{}.graphml".format(file_idx))

    return

def gen_network_small(network: mmodel.Network, idx: int):
    # 1. generate a random tree and select one with 4 endnode
    enode_num = 0
    while enode_num != 6:
        enode_num = 0
        g = networkx.generators.random_tree(10)
        # check the number of end-node
        for n in g.nodes():
            nei = list(g.neighbors(n))
            if len(nei) == 1:
                enode_num += 1
    print("Get one with endnode_num %d, index %d" % (enode_num, idx))
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
    elif net_type == 3:
        gen_network_huge(network, idx)
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

    gen_network_into_file(2, 0, 100)
