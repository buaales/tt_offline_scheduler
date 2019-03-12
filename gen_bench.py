"测试集生成模块"

import sys
import time
import random
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

from msg_scheduler import model as mmodel
from scheduler import model as tmodel

def gen_network_from_file(path: str):
    # 1. get graph from file
    g = nx.readwrite.graphml.read_graphml(path)
    # 2. generate network
    node_name_map = {}
    network = mmodel.Network()
    for n in g.nodes():
        nei = list(g.neighbors(n))
        if len(nei) == 1:
            new_node = mmodel.EndNode(f'node_{n}')
        else:
            new_node = mmodel.SwitchNode(f'switch_{n}')
        network.add_node(new_node)
        node_name_map[n] = new_node.name
    for e in g.edges:
        network.add_link(node_name_map[e[0]], node_name_map[e[1]])

    # nx.draw_networkx(g)

    return network

def gen_task_set_for_each_node(network, node, periods, utilization):
    '''
    每个节点12个任务：6个free,2个producer，2个customer和2个shaper
    每个任务的周期从periods中随机选择
    节点总的利用率为utilization
    '''
    # 1. 初始化任务集
    tasks = []
    for i in range(6):
        # print("Init FreeTask {} in node {}".format(
        #    '{}_{}'.format(node.name, i), node.name
        #))
        task = tmodel.FreeTask(network, 
            f'{node.name}_{i}', node.name)
        task.period = random.choice(periods)
        tasks.append(task)
    for i in range(6, 8):
        #print("Init ProdTask {} in node {}".format(
        #    '{}_{}'.format(node.name, i), node.name
        #))
        task = tmodel.ProducerTask(network, 
            f'{node.name}_{i}', node.name)
        task.period = random.choice(periods)
        tasks.append(task)
    for i in range(8, 10):
        #print("Init CustTask {} in node {}".format(
        #    '{}_{}'.format(node.name, i), node.name
        #))
        task = tmodel.CustomerTask(network, 
            f'{node.name}_{i}', node.name)
        task.period = random.choice(periods)
        tasks.append(task)
    for i in range(10, 12):
        #print("Init ShapTask {} in node {}".format(
        #    '{}_{}'.format(node.name, i), node.name
        #))
        task = tmodel.ShaperTask(network, 
            f'{node.name}_{i}', node.name)
        task.period = random.choice(periods)
        tasks.append(task)
    # 2. 根据利用率计算WCET
    u_free = utilization * 0.75
    u_coum = utilization * 0.25
    temps = [random.randint(1000, 9999) for x in range(6)]
    frees = [temps[i]/sum(temps)*u_free for i in range(6)]
    #print(frees)
    #print(sum(frees))
    temps = [random.randint(1000, 9999) for x in range(6)]
    coums = [temps[i]/sum(temps)*u_coum for i in range(6)]
    #print(coums)
    #print(sum(coums))
    #print(sum(frees)+sum(coums))

    for i in range(6):
        tasks[i].wcet = frees[i] * tasks[i].peroid

    for i in range(6):
        tasks[i+6].wect = coums[i] * tasks[i+6].peroid

    return tasks
    

def gen_model(periods: int, utilization: float, granuolarity: int, net_type: int, times: int):
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
    if net_type == 0:
        path = './output/graph_small_gen/graph_{}.graphml'.format(times)
    elif net_type == 1:
        path = './output/graph_medium_gen/graph_{}.graphml'.format(times)
    elif net_type == 3:
        path = './output/graph_large_gen/graph_{}.graphml'.format(times)
    else:
        print("[Benchmark Gen][ERR]: Unkown network type")
        return
    
    network: mmodel.Network = gen_network_from_file(path)
    
    # 2. Gen App Sets
    # 遍历 Node节点生成任务集合
    #task_sets = gen_task_set(periods, utilization, granuolarity)
    for node in network.end_nodes:
        gen_task_set_for_each_node(network, node, periods, utilization)
    # plt.show()
    # 3. 建立通信链路
    #gen_virtual_links()


# 生成文本格式的图存储到文件中
if __name__ == '__main__':
    periods = [10, 30, 100]
    net_type = 0
    times = 1
    u = 0.75
    gen_model(periods, u, 1, net_type, times)

# 测试生成的图是否合格
'''
if __name__ == "__main__":
    idx = random.randint(0, 100)
    file_name = './output/graph_small_gen/graph_{}.graphml'.format(idx)
    g = nx.readwrite.graphml.read_graphml(file_name)
    #g = networkx.complete_graph(5)
    print("draw graph_%d" % idx)
    nx.draw_networkx(g)
    plt.show()
'''