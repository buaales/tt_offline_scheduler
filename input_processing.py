import sys
if sys.platform == 'darwin':
    import matplotlib
    matplotlib.use("TkAgg")
import time
import json
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

from msg_scheduler import model as mmodel
from scheduler import model as tmodel

def setup_frame_constraints(task_dict: dict, solver_ret_dcit: dict):
    
    for node in task_dict:
        tasks = task_dict[node]
        for task in tasks:
            if isinstance(task, tmodel.FreeTask) or isinstance(task, tmodel.ConsumerTask):
                continue
            # check
            assert task.vlink != None, "Shaper or Producer's vlink is None!"
            # setup frame constraints
            _receiver = task.vlink.receive_task
            # msg start after sender's deadline
            _offset =  solver_ret_dcit['{}_phi'.format(task.name)] + solver_ret_dcit['{}_deadline'.format(task.name)]
            # msg end before receiver's offset
            _deadline = solver_ret_dcit['{}_phi'.format(_receiver.name)]
            #print('{}, {}'.format(task.name, _receiver.name))
            #print('{}, {}, {}, {}'.format(task.peroid, _offset, _deadline, _receiver.offset0))
            task.set_frame(peroid=task.peroid, min_offset=_offset, max_offset=_deadline)
    
    return

def gen_network_from_file(path: str):
    # 1. get graph from file
    g = nx.readwrite.graphml.read_graphml(path)
    # 2. generate network
    node_name_map = {}
    network = mmodel.Network()
    for n in g.nodes():
        #print("n = {}".format(n))
        nei = list(g.neighbors(n))
        if len(nei) == 1:
            new_node = mmodel.EndNode(f'node_{n}')
        else:
            new_node = mmodel.SwitchNode(f'switch_{n}')
        network.add_node(new_node)
        node_name_map[n] = new_node.name
    for e in g.edges:
        network.add_link(node_name_map[e[0]], node_name_map[e[1]])

    return network

def get_model_from_files(graph_path: str, commu_pair_path: str, taskset_path: str):
    
    task_dict = dict()
    commu_pair = dict()
    # gen network
    network: mmodel.Network = gen_network_from_file(graph_path)
    # gen taskset
    try:
        taskset_file = open(taskset_path, "r", encoding='utf-8')
    except IOError as e:
        print("Can't open taskset file: {}".format(taskset_path))
        exit(0)
    taskset = json.load(taskset_file)

    for node_name in taskset:
        #print(node_name)
        _node = network[node_name]
        _tasks = taskset[node_name]
        _list = list()
        for _td in _tasks:
            #print(_td)
            _id = _td['task_id']
            if _td['task_type'] == 'FreeTask':
                _task = tmodel.FreeTask(network, f'{node_name}_{_id}', node_name)
            elif _td['task_type'] == 'ProducerTask':
                _task = tmodel.ProducerTask(network, f'{node_name}_{_id}', node_name)
                _task.delta = _td['delta']
            elif _td['task_type'] == 'ConsumerTask':
                _task = tmodel.ConsumerTask(network, f'{node_name}_{_id}', node_name)
                _task.delta = _td['delta']
            elif _td['task_type'] == 'ShaperTask':
                _task = tmodel.ShaperTask(network, f'{node_name}_{_id}', node_name)
                _task.delta = _td['delta']
            else:
                raise RuntimeError("Unkown Task Type!")
            _task.peroid = _td['peroid']
            _task.deadline0 = _td['deadline']
            _task.wcet = _td['wcet']
            _task.offset0 = _td['offset']
            #print(_task)
            _list.insert(_id, _task)
        #print(_list)
        task_dict[_node] = _list
    #print(task_dict)
    
    # gen commu_pair
    try:
        commu_pair_file = open(commu_pair_path, "r", encoding='utf-8')
    except IOError as e:
        print("Can't open commu_pair file: {}".format(commu_pair_path))
        exit(0)
    commu_pair_json = json.load(commu_pair_file)
    #print(commu_pair_json)
    for pair in commu_pair_json:
        _p_str = pair['ProducerTask']
        [_p_node_id, _p_task_id] = _p_str.split('_')
        _p = task_dict['node_{}'.format(_p_node_id)][int(_p_task_id)]
        #print("Task {}'s wcet is {}".format(_p_str, _p.wcet))
        _c_str = pair['ConsumerTask']
        [_c_node_id, _c_task_id] = _c_str.split('_')
        _c = task_dict['node_{}'.format(_c_node_id)][int(_c_task_id)]
        #print("Task {}'s wcet is {}".format(_c_str, _c.wcet))
        if 'ShaperTask' in pair:
            #P-S-C
            _s_str = pair['ShaperTask']
            [_s_node_id, _s_task_id] = _s_str.split('_')
            _s = task_dict['node_{}'.format(_s_node_id)][int(_s_task_id)]
            #print("Task {}'s wcet is {}".format(_s_str, _s.wcet))
            _p.set_virtual_link([_s])
            _s.set_virtual_link([_c])
            commu_pair[_s] = [_p, _s, _c]
        else:
            _p.set_virtual_link([_c])
            commu_pair[_c] = [_p, _c]

    #return
    return network, task_dict, commu_pair

if __name__ == "__main__":
    get_model_from_files("./input/example/graph.graphml",
                         "./input/example/comm_pair.json",
                         "./input/example/taskset.json")