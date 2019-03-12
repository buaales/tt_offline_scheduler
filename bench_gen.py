"测试集生成模块"

import sys
import time
import random
import networkx
import matplotlib.pyplot as plt

from msg_scheduler import model as mmodel
from scheduler import model as tmodel

def gen_network_large(network: mmodel.Network):
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
        gen_network_large_star(network, idx)
    else:
        print("[Benchmark Gen][ERR]: Unkown network type")
        return None
    # 2. return network
    return network

def gen_network_into_file(net_type: int):
    idx = 0
    while idx < 1000:
        start = time.time()
        gen_network(net_type, idx)
        idx += 1
        stop = time.time()
        print("spend time: %f" % (stop - start))

def gen_network_from_file(network: mmodel.Network, g: networkx.Graph):
    # generate network
    node_name_map = {}
    for n in g.nodes():
        nei = list(g.neighbors(n))
        if len(nei) == 1:
            new_node = mmodel.EndNode(f'app_{n}')
        else:
            new_node = mmodel.SwitchNode(f'msg_{n}')
        network.add_node(new_node)
        node_name_map[n] = new_node.name
    for e in g.edges:
        network.add_link(node_name_map[e[0]], node_name_map[e[1]])

    return

def gen_model(periods: int, utilization: float, granuolarity: int, net_type: int):
    '''
    功能描述：
        生成测试集
    参数描述：
        peroids: 任务周期集合, 单位：毫秒
        utilization: 任务集总体利用率
        granuolarity: 任务调度时间粒度，单位：微秒
        net_type: small(0), medium(1), large(2)
    '''
    # Check utilization
    if (utilization < 0) or (utilization > 1):
        print("[Benchmark Gen][ERR]: utilization wrong value")
        return None

    # 1. 从生成好的图像文件中获取网络
    network = gen_network(net_type)

    # 2. Gen App Sets
    # 遍历 Node节点生成任务集合
    #task_sets = gen_task_set(periods, utilization, granuolarity)

    # 3. 建立通信链路
    #gen_virtual_links()


# 生成文本格式的图存储到文件中
'''
if __name__ == "__main__":
    gen_network_into_file(1)
'''

# 测试生成的图是否合格
'''
if __name__ == "__main__":
    idx = random.randint(0, 100)
    file_name = './output/graph_medium_gen/graph_{}.graphml'.format(idx)
    g = networkx.readwrite.graphml.read_graphml(file_name)
    #g = networkx.complete_graph(5)
    print("draw graph_%d" % idx)
    networkx.draw_networkx(g)
    plt.show()
'''