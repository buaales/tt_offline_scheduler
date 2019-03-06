"测试集生成模块"

from msg_scheduler import model as mmodel
from scheduler import model as tmodel
import time

def gen_network_large(network: mmodel.Network):
    pass

def gen_network_medium(network: mmodel.Network):
    pass

def gen_network_small(network: mmodel.Network):
    pass

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
    network: mmodel.Network = gen_network(net_type)

    # 2. Gen App Sets
    # 遍历 Node节点生成任务集合
    task_sets = gen_task_set(periods: int, utilization: float, granuolarity: int)

    # 3. 建立通信链路
    gen_virtual_links()
