''' The Solver Model '''
import time

from msg_scheduler import model as MModel
from scheduler import model as TModel
from gurobipy import *

class Solver:
    ''' The Solver Class '''
    def __init__(self, network: MModel.Network, task_dict: dict, util: float, commu_dict: dict):
        self._network = network
        self._task_dict = task_dict
        self._free_util = util * 0.75
        self._commu_pair = commu_dict
        self._solver = Model("tt_schduler")
        self._vars = {}
        print("#### util: {}".format(util))
        #self.f = open("./output/constraint_sample.txt", 'w')

    def __build_var(self):
        '''
        Build vars for every communication task
        '''
        # build for max_min Intermediate variables
        self._vars["min"] = self._solver.addVar(vtype=GRB.CONTINUOUS, name="min")
        #self.f.writelines("min\n")
        for node in self._task_dict:
            tasks = self._task_dict[node]
            for task in tasks:
                # traverse task list in each node
                # skip free-task
                if isinstance(task, TModel.FreeTask):
                    continue
                # phi var and deadline var
                self._vars["{}_phi".format(task.name)] = self._solver.addVar(vtype=GRB.CONTINUOUS,
                                                        name="{}_phi".format(task.name))
                self._vars["{}_deadline".format(task.name)] = self._solver.addVar(vtype=GRB.CONTINUOUS,
                                                        name="{}_deadline".format(task.name))
                self._vars["{}_d_plus".format(task.name)] = self._solver.addVar(vtype=GRB.CONTINUOUS,
                                                        name="{}_d_plus".format(task.name))
                self._vars["{}_d_sub".format(task.name)] = self._solver.addVar(vtype=GRB.CONTINUOUS,
                                                        name="{}_d_sub".format(task.name))
                #self._vars["{}_wcet".format(task.name)] = self._solver.addVar(vtype=GRB.Real,
                #                                        name="{}_wcet".format(task.name))
                #self.f.writelines("{}_phi\n".format(task.name))
                #self.f.writelines("{}_deadline\n".format(task.name))

    def __build_constraints(self):
        '''
        Build constraints
        '''
        # d_ic, d_pi
        delay = 1000
        s = self._solver
        for node in self._task_dict:
            tasks = self._task_dict[node]
            for task in tasks:
                # skip free-task and consumer-task
                if isinstance(task, TModel.FreeTask):
                    continue
                
                #_phi0 = int(task.offset0 * 1000)
                #_d0 = int(task.deadline0 * 1000)
                _my_wcet = int(task.wcet)
                _my_period = int(task.peroid)
                _my_delta = task.delta
                
                # constraints for d
                _d = self._vars['{}_deadline'.format(task.name)]
                s.addConstr(_d >= _my_wcet, 'c_{}_d_0'.format(task.name))
                s.addConstr(_d <= _my_period, 'c_{}_d_1'.format(task.name))

                # constraints for phi
                _phi = self._vars['{}_phi'.format(task.name)]
                s.addConstr(_phi >= 0, 'c_{}_phi_0'.format(task.name))
                s.addConstr(_phi + _d <= _my_period, 'c_{}_phi_1'.format(task.name))

                _d_plus = self._vars["{}_d_plus".format(task.name)]
                _d_sub = self._vars["{}_d_sub".format(task.name)]
                s.addConstr(_d_plus >= 0, 'c_{}_d_plus'.format(task.name))
                s.addConstr(_d_sub >= 0, 'c_{}_d_sub'.format(task.name))

                # perpare vars
                if isinstance(task, TModel.ConsumerTask):
                    if not task in self._commu_pair:
                        continue
                    _producer = self._commu_pair[task][0]
                    assert isinstance(_producer, TModel.ProducerTask), "Not P-C pair's P"
                    _p_phi = self._vars["{}_phi".format(_producer.name)]
                    _p_deadline = self._vars["{}_deadline".format(_producer.name)]
                    _d_p_s = delay
                    _c_phi = _phi + _d
                    _c_deadline = 0
                    _d_s_c = 0
                elif isinstance(task, TModel.ShaperTask):
                    _producer = self._commu_pair[task][0]
                    assert isinstance(_producer, TModel.ProducerTask), "Not P-S-C pair's P"
                    _consumer = self._commu_pair[task][2]
                    assert isinstance(_consumer, TModel.ConsumerTask), "Not P-S-C pair's C"
                    _p_phi = self._vars['{}_phi'.format(_producer.name)]
                    _p_deadline = self._vars["{}_deadline".format(_producer.name)]
                    _c_phi = self._vars['{}_phi'.format(_consumer.name)]
                    _c_deadline = self._vars['{}_deadline'.format(_consumer.name)]
                    _d_p_s = _d_s_c = delay
                elif isinstance(task, TModel.ProducerTask):
                    continue
                else:
                    raise RuntimeError('Unkown Communication Pair')
                
                # min
                _min = self._vars['min']
                _k = 2
                # constraints for d_plus and d_sub
                _expr_temp = (_phi - _p_phi - _p_deadline - _d_p_s) * (1 - _my_delta) - (_c_phi - _phi - _d - _d_s_c) * _my_delta + _d_sub - _d_plus
                s.addConstr(_expr_temp == 0, "c_{}_dd".format(task.name))
                # min
                _expr_temp = (_c_phi - _phi - _d - _d_s_c) + (_phi - _p_phi - _p_deadline - _d_p_s) - _k * (_d_plus + _d_sub)
                s.addConstr(_min <= _expr_temp, 'min_{}'.format(task.name))
                #self.f.writelines("min <= {}\n".format(_expr_temp_str))
            # Add util constraints
            '''
            _count = 0
            _task1, _task2 = None, None
            for task in tasks:
                if isinstance(task, TModel.FreeTask):
                    continue
                _count += 1
                if _count == 1:
                    _task1 = task
                elif _count == 2:
                    _count = 0
                    _task2 = task
                    _task1_wcet = int(_task1.wcet)
                    _task2_wcet = int(_task2.wcet)
                    _task1_deadline = self._vars["{}_deadline".format(_task1.name)]
                    _task2_deadline = self._vars["{}_deadline".format(_task2.name)]
                    s.addQConstr(_task1_wcet * _task2_deadline + _task2_wcet * _task1_deadline <= ((2/5)*(1-self._free_util))*_task1_deadline*_task2_deadline)
                    print("add {0} * {3}_d2 + {1} * {2}_d1 <= 0.4 * 0.5 * 0.75 * {2}_d1 * {3}_d2".format(_task1_wcet, _task2_wcet, _task1.name, _task2.name))
                else:
                    raise RuntimeError("Error Count!")
            
            assert _task1, "Error _task1 == None"
            _task1_wcet = int(_task1.wcet)
            _task1_deadline = self._vars["{}_deadline".format(_task1.name)]
            s.addConstr( ((1-self._free_util)/5) * _task1_deadline >= _task1_wcet )
            '''
            for task in tasks:
                if isinstance(task, TModel.FreeTask):
                    continue
                _wcet = int (task.wcet)
                _d = self._vars["{}_deadline".format(task.name)]
                print("##### {}".format(1-self._free_util))
                s.addConstr( ( (1-self._free_util) / 5) * _d >= _wcet)
            
        # set objective: max_min
        _min = self._vars['min']
        s.setObjective(_min, GRB.MAXIMIZE)


    def solve(self, file_path: str):
        try:
            # build var
            #self.f.writelines("###### Vars ######\n")
            self.__build_var()
            # build constraints
            #self.f.writelines("###### Contrains ######\n")
            self.__build_constraints()
            # solver
            #print("Slover started!")
            #_t0 = time.clock()
            self._solver.optimize()
            #_t1 = time.clock()
            #print("Slover finished in %f s!" % (_t1 - _t0))

            retdict = {}
            # output
            with open(file_path, 'w') as f:
                for var in self._solver.getVars():
                    try:
                        x = var.getAttr("x")
                        f.writelines('{}, {}\n'.format(var.varName, var.x))
                        retdict[var.varName] = int(var.x)
                    except AttributeError as e:
                        f.close()
                        return None
                f.close()

            return retdict
        except GurobiError as e:
            print("Gurobi Error: %s" % (e.message))

