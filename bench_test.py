import sys
import gen_bench as gb

from msg_scheduler import model as mmodel
from scheduler import model as tmodel

if __name__ == '__main__':
    # setup param
    peroids = [50, 75]
    util = 0.75
    gran = 1
    net_type = 0
    times = 8
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
            f.writelines('\toffset0: {}, wcet: {}, deadline0: {}, peroid: {}'.format(task.offset0, task.wcet, task.deadline0, task.peroid))
            if isinstance(task, tmodel.CommTask):
                f.writelines(', delta: {}\n'.format(task.delta))
            else:
                f.writelines('\n')
        f.writelines('check util: %f\n' % real_util)

    f.writelines("######## END ########\n")
