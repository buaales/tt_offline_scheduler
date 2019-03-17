import sys
sys.path.append("..")
import gen_bench as gb


if __name__ == '__main__':
    #
    periods = [50, 75]
    util = 0.5
    gran = 1
    network, task_dict = gen_model(periods, util, gran, 0, 0)
