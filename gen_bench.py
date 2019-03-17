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

def gen_task_wect_for_each_node(tasks, periods):
    # 1. 验证所有任务周期设置正确
    for task in tasks:
        assert task.period in periods, 'Gen_task_wect: 周期检查失败!'
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
        tasks[i].wcet = frees[i] * tasks[i].period

    for i in range(6):
        tasks[i+6].wect = coums[i] * tasks[i+6].period

def gen_task_set_for_each_node(network, node, periods, utilization):
    '''
    每个节点12个任务：7个free,2个producer，2个consumer和1个shaper
    每个任务的周期从periods中随机选择
    节点总的利用率为utilization
    '''
    # 1. 初始化任务集
    tasks = []
    for i in range(7):
        task = tmodel.FreeTask(network,
            f'{node.name}_{i}', node.name)
        task.period = random.choice(periods)
        tasks.append(task)
    # 通信相关任务不应该在此初始化周期，因为通信依赖的任务要求同周期
    for i in range(7, 9):
        task = tmodel.ProducerTask(network,
            f'{node.name}_{i}', node.name)
        #task.period = random.choice(periods)
        tasks.append(task)
    for i in range(9, 11):
        task = tmodel.ConsumerTask(network,
            f'{node.name}_{i}', node.name)
        #task.period = random.choice(periods)
        tasks.append(task)
    for i in range(11, 12):
        task = tmodel.ShaperTask(network,
            f'{node.name}_{i}', node.name)
        #task.period = random.choice(periods)
        tasks.append(task)

    return tasks

def gen_virtual_links(task_dict, network: mmodel.Network, periods):
    '''
    生成虚链路
    '''
    # 1. 遍历所有节点，对每两对节点进行处理
    node_num = len(network.end_nodes)
    # 验证端节点个数为偶数
    assert node_num % 2 == 0, '端节点个数不为偶数！'
    for i in range(node_num // 2):
        _node_1 = network[f'node_{}'.format(i)]
        _node_2 = network[f'node_{}'.format(i+node_num//2)]
        # 2. Map:
        # node_1_p_1 --> node_2_s_1 --> node_1_c_1
        # node_2_p_1 --> node_1_s_1 --> node_2_c_1
        # node_1_p_2       -->          node_2_c_2
        # node_2_p_2       -->          node_1_c_2
        _task_list_1 = task_dict[_node_1]
        _task_list_2 = task_dict[_node_2]
        _period = random.choice(periods)
        # 2.1 设置周期和虚链路
        _task_list_1[7].period = _period #node_1_p_1
        _task_list_2[11].period = _period #node_2_s_1
        _task_list_1[9].period = _period #node_1_c_1
        _task_list_1[7].set_virtual_link([_task_list_2[11]]).set_frame(_period)
        _task_list_2[11].set_virtual_link([_task_list_1[9]]).set_frame(_period)
        # 2.2
        _period = random.choice(periods)
        _task_list_2[7].period = _period
        _task_list_1[11].period = _period
        _task_list_2[9].period = _period
        _task_list_2[7].set_virtual_link([_task_list_1[11]]).set_frame(_period)
        _task_list_1[11].set_virtual_link([_task_list_2[9]]).set_frame(_period)
        # 2.3
        _period = random.choice(periods)
        _task_list_1[8].period = _period
        _task_list_2[10].period = _period
        _task_list_1[8].set_virtual_link([_task_list_2[10]]).set_frame(_period)
        # 2.4
        _period = random.choice(periods)
        _task_list_2[8].period = _period
        _task_list_1[10].period = _period
        _task_list_2[8].set_virtual_link([_task_list_1[10]]).set_frame(_period)

def gen_comm_delta_for_each_node(tasks):
    # communication task idx from 7 to 11
    for i in range(7, 12):
        _task = tasks[i]
        # Check Class Type
        assert isinstance(_task, tmodel.ShaperTask), 'Gen_shaper_delta: 实例类型不为ShaperTask'
        # producer
        if isinstance(_task, tmodel.ProducerTask):
            _task.delta = 0
        # consumer
        elif isinstance(_task, tmodel.ConsumerTask):
            _task.delta = 1
        # shaper task
        else:
            _task.delta = random.uniform(0.4, 0.6)

def gen_phi0_and_d0(task_dict, delay_avg, delay_max, delay_min):

    node_num = len(network.end_nodes)
    delay_avg = (delay_max + delay_min) / 2

    for i in range(node_num // 2):
        _node_1 = network[f'node_{}'.format(i)]
        _node_2 = network[f'node_{}'.format(i+node_num//2)]
        # Map
        # node_2_p_1 --> node_1_s_1 --> node_2_c_1
        # node_1_p_1 --> node_2_s_1 --> node_1_c_1
        # node_1_p_2       -->          node_2_c_2
        # node_2_p_2       -->          node_1_c_2
        # 1. 处理 node 1 上的 shaper task
        _producer = task_dict[_node_2][7]
        _shaper = task_dict[_node_1][11]
        _consumer = task_dict[_node_2][9]
        _s = min((delay_max-delay_min)/(2*_shaper.delta),
                (delay_max-delay_min)/(2*(1-_shaper.delta)))

        _producer.offset0 = 0
        _producer.deadline0 = _producer.period # 无用，乘0
        _consumer.offest0 = 0 # 无用，乘0
        _consumer.deadline0 = _consumer.period
        _shaper.offset0 = _producer.T + delay_avg - _shaper.delta * _s
        _shaper.deadline0 = _consumer.T - delay_avg - _consumer.wcet + (1 - _shaper.delta) * _s
        # 2. 处理 node 2 上的 shaper task
        _producer = task_dict[_node_1][7]
        _shaper = task_dict[_node_2][11]
        _consumer = task_dict[_node_1][9]
        _s = min((delay_max-delay_min)/(2*_shaper.delta),
                (delay_max-delay_min)/(2*(1-_shaper.delta)))

        _producer.offset0 = 0
        _producer.deadline0 = _producer.period # 无用，乘0
        _consumer.offest0 = 0 # 无用，乘0
        _consumer.deadline0 = _consumer.period
        _shaper.offset0 = _producer.T + delay_avg - _shaper.delta * _s
        _shaper.deadline0 = _consumer.T - delay_avg - _consumer.wcet + (1 - _shaper.delta) * _s
        # 处理余下的两对p-c
        _producer = task_dict[_node_1][8]
        _consumer = task_dict[_node_2][10]
        _producer.offset0 = 0
        _producer.deadline0 = _producer.period # 无用，乘0
        _consumer.offest0 = 0 # 无用，乘0
        _consumer.deadline0 = _consumer.period

        _producer = task_dict[_node_2][8]
        _consumer = task_dict[_node_1][10]
        _producer.offset0 = 0
        _producer.deadline0 = _producer.period # 无用，乘0
        _consumer.offest0 = 0 # 无用，乘0
        _consumer.deadline0 = _consumer.period

def gen_model(periods: int, utilization: float, granuolarity: int, net_type: int, times: int):
    '''
    功能描述：
        生成测试集
    参数描述：
        periods: 任务周期集合, 单位：毫秒
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
    task_dict = {}
    for node in network.end_nodes:
        task_dict[node] = gen_task_set_for_each_node(network, node, periods, utilization)
    # plt.show()
    # 3. 建立通信链路
    gen_virtual_links(task_dict, network, periods)
    # 4. 计算任务集中任务的Wect
    for node in task_dict:
        gen_task_wect_for_each_node(task_dict[node], periods)
    # 5. 生成亲和性参数delta
    for node in task_dict:
        gen_shaper_delta_for_each_node(task_dict[node])
    # 6. 计算phi_0参数和D_0参数
    gen_phi0_and_d0(task_dict,)

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
