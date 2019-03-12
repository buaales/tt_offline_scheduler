"测试集生成模块"

import sys
import time
import random
import networkx
import matplotlib.pyplot as plt

from msg_scheduler import model as mmodel
from scheduler import model as tmodel

def gen_network_from_file(path: str):
    # 1. get graph from file
    g = networkx.readwrite.graphml.read_graphml(path)
    # 2. generate network
    node_name_map = {}
    network = mmodel.Network()
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

    return network

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