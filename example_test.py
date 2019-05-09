import sys
import time
import gen_bench as gb

from msg_scheduler import model as mmodel
from msg_scheduler import constrains, analyzer
from scheduler import model as tmodel
#from scheduler import solver_z3 as tsolver
#from scheduler import solver_gurobi_new as tsolver
from scheduler import solver_gekko as tsolver
from scheduler import edfsim


def do_test(split_output_path: str, s_delta=0.5):
    #return times
    split_time = 0
    task_sche_time = 0
    msg_sche_time = 0
    # call gen_model
    network, task_dict, commu_pair = gb.gen_example(50000, s_delta)
    # draw the network
    # network.draw()

    # test solver
    solver = tsolver.Solver(network, task_dict, 0.6, commu_pair)
    solver_result_dict, split_time = solver.solve(split_output_path)

    if not solver_result_dict:
        print("\x1b[31m#### Can't solve spliting\x1b[0m")
        time.sleep(3)
        return -1, -1, -1
    
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
    
    print("-- 任务调度 --")
    _temp_sum = 0
    _count = 0
    for node in task_dict:
        tasks = task_dict[node]
        print(node.name)
        # re-setup phi and deadline
        tasks4edf = []
        for task in tasks:
            _tid = int(task.name.split('_')[2]) + 1
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
        _t0 = time.time()
        edfsim.testEDFSim(tasks4edf,[])
        _t1 = time.time()
        _count += 1
        _temp_sum += _t1 - _t0
        
    task_sche_time = _temp_sum / _count
    print("-- 通信调度 --")
    gb.setup_frame_constraints(task_dict, solver_result_dict)
    
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
        return -2, -2, -2
    an = analyzer.Analyzer(df, network, sc.app_lcm)
    an.print_by_time()
    #an.animate()
    #print("Message Passing Solved in {} s!".format(_t1-_t0))
    return split_time, task_sche_time, msg_sche_time

if __name__ == '__main__':
    
    print("\x1b[32m####Starting test\x1b[0m")
    
    for delta in [0.1 * x for x in range(4, 5)]:
        t1, t2, t3 = do_test("./output/multi_delta/split_result_delta_{}".format(int(delta*10)), delta)
    
    print("#### Test Done! ####")

    while True:
        pass