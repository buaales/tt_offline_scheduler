import sys
sys.path.append("..")
import gen_bench as gb


if __name__ == '__main__':
    # setup param
    periods = [50, 75]
    util = 0.5
    gran = 1
    net_type = 0
    times = 8
    # call gen_model
    network, task_dict = gb.gen_model(periods, util, gran, net_type, times)
    # draw the network
    network.draw()
    # check param
    f = open("../output/bench_test.txt", 'w')
    # print param for each node
    for node in task_dict:

