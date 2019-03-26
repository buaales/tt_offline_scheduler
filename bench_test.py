import sys
import gen_bench as gb

from msg_scheduler import model as mmodel
from msg_scheduler import constrains, analyzer
from scheduler import model as tmodel
from scheduler import solver_gurobi as tsolver
from gurobipy import *

if __name__ == '__main__':
    # setup param
    peroids = [50, 75]
    util = 0.75
    gran = 1
    net_type = 2
    times = 3
    # call gen_model
    network, task_dict = gb.gen_model(peroids, util, gran, net_type, times)
    # draw the network
    network.draw()
    # check param
    f = open("./output/bench_test.txt", 'w')
    # print param for each node
    for node in task_dict:
        f.writelines("######## Node {} ########\n".format(node.name))
        tasks = task_dict[node]
        real_util = 0
        for i in range(12):
            task = tasks[i]
            real_util += task.wcet / task.peroid
            #print("per {}".format(task.peroid))
            f.writelines('task id: {}, task type: {}'.format(i, type(task)))
            _phi0 = int(task.offset0 * 1000)
            _d0 = int(task.deadline0 * 1000)
            _wcet0 = int(task.wcet * 1000)
            f.writelines('\toffset0: {}, wcet: {}, deadline0: {}, peroid: {}'.format(_phi0, _wcet0, _d0, task.peroid * 1000))
            if isinstance(task, tmodel.CommTask):
                f.writelines(', delta: {}\n'.format(task.delta))
            else:
                f.writelines('\n')
        f.writelines('check util: %f\n' % real_util)

    f.writelines("######## END ########\n")
    f.close()

    # test solver
    solver = tsolver.Solver(network, task_dict, util * 0.75)
    solver.solve("./output/gurobi.txt")
    
    '''
    sc = mmodel.Scheduler(network)
    for node in task_dict:
        sc.add_apps(task_dict[node])

    hook = constrains.Z3Hook()
    sc.add_constrains(hook)
    df = hook.to_dataframe()
    an = analyzer.Analyzer(df, network, sc.app_lcm)
    '''
    #an.print_by_time()
