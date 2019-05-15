import sys
import time
import struct
import re
import input_processing as ips
import pandas as pd

from msg_scheduler import model as mmodel
from msg_scheduler import constrains, analyzer
from scheduler import model as tmodel
#from scheduler import solver_z3 as tsolver
#from scheduler import solver_gurobi_new as tsolver
from scheduler import solver_gekko as tsolver
from scheduler import edfsim

##
# Input Files
##
graph_path: str = "./input/example/graph.graphml"
commu_pair_path: str = "./input/example/comm_pair.json"
taskset_path: str = "./input/example/taskset.json"
##
# Output Files
##
split_output_path: str = "./output/split_result.txt"
task_sch_result_path_prefix: str = "./output/task_sch_result"
msg_sch_result_path: str = "./output/msg_sch_result.bin"

def calculate_free_utils(task_dict: dict):
    utils = dict()

    for node in task_dict:
        _tasks = task_dict[node]
        _util = 0
        for _task in _tasks:
            if not isinstance(_task, tmodel.FreeTask):
                continue
            # add to _util
            _util += _task.wcet / _task.peroid
        # store into utils
        utils[node] = _util
    
    # return
    return utils

def gen_msg_sch_table(df: pd.DataFrame):
    # FIXME: do not use temp files
    try:
        f = open(msg_sch_result_path, 'wb')

        string = str(df.sort_values('time_slot'))
        str_list = string.split(sep='\n')
        for s in str_list:
            _list = s.split()
            if not len(_list) == 7:
                continue
            # only match receiver
            _reveiver = _list[5]
            if not re.match(r'node_\d+$', _reveiver):
                continue
            # write binary file
            _node_id = int(_list[1].split(sep='_')[1])
            _task_id = int(_list[1].split(sep='_')[2])
            #print("{}, {}".format(_node_id, _task_id))
            _msg_id = ((_node_id & 0xFF) << 8) | (_task_id & 0xFF)
            _entry_value = (_msg_id << 48) | (int(_list[6]) & 0xFFFFFFFFFFFF)
            _entry = struct.pack('Q', _entry_value)
            f.write(_entry)
        f.close()
    except IOError as e:
        print("can't open file {}".format(msg_sch_result_path))
        exit(0)

def single_task_schedule(tasks: list, solver_result_dict: dict, path: str):
    # re-setup phi and deadline
    tasks4edf = []
    for task in tasks:
        _tid = int(task.name.split('_')[2])
        #print(_tid)
        if isinstance(task, tmodel.FreeTask):
            _C = int(task.wcet)
            _T = int(task.peroid)
            _offset = int(task.offset0)
            _D = int(task.deadline0)
            _task: edfsim.Task = edfsim.Task(C=_C, D=_D, T=_T, offset=_offset, tid=_tid)
        else:
            # re-setup
            _C = int(task.wcet)
            _T = int(task.peroid)
            _offset = solver_result_dict['{}_phi'.format(task.name)]
            _D = solver_result_dict['{}_deadline'.format(task.name)]
            _task: edfsim.Task = edfsim.Task(C=_C, D=_D, T=_T, offset=_offset, tid=_tid)
        tasks4edf.append(_task)
    # do edf sim
    # dump taskset
    #for task in tasks4edf:
    #    print('Task(tid={}, T={}, C={}, D={}, offset={})'.format(task.tid, task.T, task.C, task.D, task.offset))
    _t0 = time.clock()
    logs = edfsim.testEDFSim(tasks4edf,[], True)
    _t1 = time.clock()

    # gen task schudle table (binary)
    try:
        f = open(path, 'wb')
        for log in logs:
            _task_id = log[0]
            _end_time = log[2] + log[3]
            print("add entry: task_id: {}, end at {}".format(_task_id, _end_time))
            _entry_value = ((_task_id & 0xFFFF) << 48) | (_end_time & 0xFFFFFFFFFFFF)
            _entry = struct.pack('Q', _entry_value)
            f.write(_entry)
        f.close()
    except IOError as e:
        print("Can't open file {}".format(paht))
        exit(0)

    return _t1 - _t0

if __name__ == '__main__':
    split_time = 0
    task_sche_time = 0
    msg_sche_time = 0

    # Get Models from configs
    network, task_dict, commu_pair = ips.get_model_from_files(
        graph_path,
        commu_pair_path,
        taskset_path
    )
    network.draw()
    # Calculate util for each node
    utils = calculate_free_utils(task_dict)

    solver = tsolver.Solver(network, task_dict, utils, commu_pair)
    solver_result_dict, split_time = solver.solve(split_output_path)

    if not solver_result_dict:
        print("\x1b[31m#### 拆分问题无解\x1b[0m")
        exit(0)
    
    print("-- 密度测试 --")
    for node in task_dict:
        tasks = task_dict[node]
        s = 0
        for task in tasks:
            if isinstance(task, tmodel.FreeTask):
                s += task.wcet / task.deadline0
            else:
                s += task.wcet / solver_result_dict["{}_deadline".format(task.name)]
        print("{}: s={}".format(node.name, s))
    
    print("\n-- 任务调度 --")
    temp_sum = 0
    count = 0
    for node in task_dict:
        _tasks = task_dict[node]
        #print(node.name)
        _path = "{}_{}.bin".format(task_sch_result_path_prefix, node.name)
        _cost_time = single_task_schedule(_tasks, solver_result_dict, _path)
        count += 1
        temp_sum += _cost_time
    task_sche_time = temp_sum / count

    print("\n-- 通信调度 --")
    ips.setup_frame_constraints(task_dict, solver_result_dict)
    
    sc = mmodel.Scheduler(network)
    for node in task_dict:
        sc.add_apps(task_dict[node])
    
    hook = constrains.Z3Hook()
    _t0 = time.time()
    sc.add_constrains(hook)
    df = hook.to_dataframe()
    _t1 = time.time()
    msg_sche_time = _t1 - _t0
    if df.empty:
        print("\x1b[31m#### 通信调度无解\x1b[0m")
        exit(0)

    # gen msg schedule
    gen_msg_sch_table(df)
    # print
    an = analyzer.Analyzer(df, network, sc.app_lcm)
    an.print_by_time()

    print("\n-- 调度完成 --")
    print("-- 拆分用时： %.3fs" % (split_time))
    print("-- 单节点任务调度用时： %.3fs" % (task_sche_time))
    print("-- 通信调度用时： %.3fs" % (msg_sche_time))

    while True:
        pass