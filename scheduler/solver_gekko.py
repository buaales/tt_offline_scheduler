''' The Solver Model '''
import time

from msg_scheduler import model as MModel
from scheduler import model as TModel
from gekko import GEKKO

class Solver:
    ''' The Solver Class '''
    def __init__(self, network: MModel.Network, task_dict: dict, free_util: float, commu_dict: dict):
        self._network = network
        self._task_dict = task_dict
        self._free_util = free_util
        self._commu_pair = commu_dict
        self._solver = GEKKO(remote=False)
        self._vars = {}
        #self.f = open("./output/constraint_sample.txt", 'w')

    def __build_var(self):
        '''
        Build vars for every communication task
        '''
        # build for max_min Intermediate variables
        self._vars["min"] = self._solver.Var(value=0)
        #self.f.writelines("min\n")
        for node in self._task_dict:
            tasks = self._task_dict[node]
            for task in tasks:
                # traverse task list in each node
                # skip free-task
                if isinstance(task, TModel.FreeTask):
                    continue
                # phi var and deadline var
                self._vars["{}_phi".format(task.name)] = self._solver.Var(value=0, lb=0, ub=task.peroid)
                self._vars["{}_deadline".format(task.name)] = self._solver.Var(value=task.wcet, lb=task.wcet, ub=task.peroid)
                self._vars["{}_d_plus".format(task.name)] = self._solver.Var(value=0, lb=0, ub=100)
                self._vars["{}_d_sub".format(task.name)] = self._solver.Var(value=0, lb=0, ub=100)


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
                
                _my_wcet = task.wcet
                _my_period = task.peroid
                _my_delta = task.delta
                
                _min = self._vars['min']
                _d_plus = self._vars["{}_d_plus".format(task.name)]
                _d_sub = self._vars["{}_d_sub".format(task.name)]
                _d = self._vars['{}_deadline'.format(task.name)]
                _phi = self._vars['{}_phi'.format(task.name)]

                s.Equation(_phi + _d <= _my_period)

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
                _k = 1
                # constraints for d_plus and d_sub
                _expr_temp = (_phi - _p_phi - _p_deadline - _d_p_s) * (1 - _my_delta) - (_c_phi - _phi - _d - _d_s_c) * _my_delta + _d_sub - _d_plus
                print(_expr_temp)
                s.Equation(_expr_temp == 0)
                # min
                _expr_temp = (_c_phi - _phi - _d - _d_s_c) + (_phi - _p_phi - _p_deadline - _d_p_s) - _k * (_d_plus + _d_sub)
                print(_expr_temp)
                s.Equation(_min <= _expr_temp)
                #self.f.writelines("min <= {}\n".format(_expr_temp_str))
            # Add util constraints

            _expr_temp = 0
            _count = 0
            for task in tasks:
                if isinstance(task, TModel.FreeTask):
                    continue
                _d = self._vars['{}_deadline'.format(task.name)]
                _expr_temp += task.wcet / _d
                _count += 1
                
            s.Equation(_expr_temp <= (1-self._free_util))
            print(_expr_temp)
            
        # set objective: max_min
        _min = self._vars['min']
        s.Obj(-1*_min)
        s.options.IMODE = 3


    def solve(self, file_path: str):
        # build var
        #self.f.writelines("###### Vars ######\n")
        self.__build_var()
        # build constraints
        #self.f.writelines("###### Contrains ######\n")
        self.__build_constraints()
        # solver
        #print("Slover started!")
        cost_time = 0
        try:
            _t0 = time.time()
            self._solver.solve()
            _t1 = time.time()
            cost_time = _t1 - _t0
        except Exception as e:
            print("\x1b[31m#### GEKKO Error: %s\x1b[0m" % (e))
            return None, cost_time
        
        retdict = {}
        # output
        with open(file_path, 'w') as f:
            for name in self._vars:
                var = self._vars[name]
                f.writelines('{}, {}\n'.format(name, var.value[0]))
                retdict[name] = int(var.value[0])

            f.close()

        return retdict, cost_time

