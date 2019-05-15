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

def record_test_model(file, task_dict):
    # print param for each node
    file.writelines("######## TEST MODLE START ########\n")
    for node in task_dict:
        file.writelines("######## Node {} ########\n".format(node.name))
        tasks = task_dict[node]
        real_util = 0
        for i in range(12):
            task = tasks[i]
            real_util += task.wcet / task.peroid
            #print("per {}".format(task.peroid))
            file.writelines('task id: {}, task type: {}'.format(i, type(task)))
            _phi0 = int(task.offset0)
            _d0 = int(task.deadline0)
            _wcet0 = int(task.wcet)
            file.writelines('\toffset0: {}, wcet: {}, deadline0: {}, peroid: {}'.format(
                _phi0, _wcet0, _d0, task.peroid))
            if isinstance(task, tmodel.CommTask):
                file.writelines(', delta: {}\n'.format(task.delta))
            else:
                file.writelines('\n')
        file.writelines('check util: %f\n' % real_util)

    file.writelines("######## TEST  MODLE  END ########\n")

def do_test(peroids, util, gran, net_type, times):
    #return times
    split_time = 0
    task_sche_time = 0
    msg_sche_time = 0
    # call gen_model
    network, task_dict, commu_pair = gb.gen_test_model(peroids, util, gran, net_type, times)
    # draw the network
    # network.draw()
    # check param
    with open("./output/bench_test.txt", 'w') as f:
        record_test_model(f, task_dict)
        f.close()

    free_utils = dict()
    for node in task_dict:
        free_utils[node] = util*0.75

    # test solver
    solver = tsolver.Solver(network, task_dict, free_utils, commu_pair)
    solver_result_dict, split_time = solver.solve("./output/gurobi_result.txt")

    if not solver_result_dict:
        print("\x1b[31m#### Can't solve spliting\x1b[0m")
        time.sleep(3)
        return -1, -1, -1
    
    # 测试密度
    
    for node in task_dict:
        tasks = task_dict[node]
        s = 0
        for task in tasks:
            if isinstance(task, tmodel.FreeTask):
                s += task.wcet / task.deadline0
            else:
                s += task.wcet / solver_result_dict["{}_deadline".format(task.name)]
        print("{}: s={}".format(node.name, s))
    
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
    
    
    gb.setup_frame_constraints(task_dict, solver_result_dict)
    
    sc = mmodel.Scheduler(network)
    for node in task_dict:
        sc.add_apps(task_dict[node])

    _t0 = time.time()
    hook = constrains.Z3Hook()
    sc.add_constrains(hook)
    df = hook.to_dataframe()
    _t1 = time.time()
    msg_sche_time = _t1 - _t0
    if df.empty:
        return -2, -2, -2
    #an = analyzer.Analyzer(df, network, sc.app_lcm)
    #an.print_by_time()
    #an.animate()
    #print("Message Passing Solved in {} s!".format(_t1-_t0))
    return split_time, task_sche_time, msg_sche_time

if __name__ == '__main__':

    print("")

    # setup param
    peroids = [50000, 75000] #us
    gran = 1 # us
    net_type = 0

    for util in [i * 0.01 for i in range(70,100)]:
        print("\x1b[32m####Starting {} util test ####\x1b[0m".format(util))
        for times in range(200):
            print("\x1b[32m####Starting {} time test\x1b[0m".format(times))
            t1, t2, t3 = do_test(peroids, util, gran, net_type, times % 100)
            with open("./output/multi_util/caltime_{}.txt".format(int(util * 100)), "a") as f:    
                f.writelines('{},\t\t\t{},\t\t\t{}\n'.format(t1, t2, t3))
                f.close()
    
    print("#### Test Done! ####")

    while True:
        pass
