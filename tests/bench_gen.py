

from msg_scheduler import model as mmodel
from scheduler import model as tmodel
import sys
import time
import random
import networkx

def gen_network_large(network: mmodel.Network):
    pass

def gen_network_medium(network: mmodel.Network):
    pass

def gen_network_small(network: mmodel.Network):
    # 1. generate a random tree and select one with 4 endnode

    enodenum = 0
    while enodenum != 4:
        # gen
        seed = random.randint(1, 9999)
        g = networkx.generators.random_tree(6, seed)
        network = mmodel.Network()
        # check the number of end-node
        for n in g.nodes():
            nei = list(g.neighbors(n))
            if len(nei) == 1:
                enodenum += 1
    
    # generate network
    node_name_map = {}
    for n in g.nodes():
        nei = list(g.neighbors(n))
        if len(nei) == 1:
            new_node = mmodel.EndNode('app_{n}')
        else:
            new_node = mmodel.SwitchNode('msg_{n}')
        network.add_node(new_node)
        node_name_map[n] = new_node.name
    for e in g.edges:
        network.add_link(node_name_map[e[0]], node_name_map[e[1]])

    return

def gen_network(net_type: int):
    network = mmodel.Network()
    # 1. calls sub-function
    if net_type == 0:
        gen_network_small(network)
    elif net_type == 1:
        gen_network_medium(network)
    elif net_type == 3:
        gen_network_large(network)
    else:
        print("[Benchmark Gen][ERR]: Unkown network type")
        return None
    # 2. return network
    return network

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

    # 1. Gen a network
    network = gen_network(net_type)

    # 2. Gen App Sets
    # 遍历 Node节点生成任务集合
    #task_sets = gen_task_set(periods, utilization, granuolarity)

    # 3. 建立通信链路
    #gen_virtual_links()

# Test
if __name__ == "__main__":
    while True:
        start = time.time()
        gen_network(0)
        stop = time.time()
        print("time: %d", stop - start)
