''' z3 Slover Model '''
import time
import z3
import typing

from msg_scheduler import model as MModel
from scheduler import model as TModel
from fractions import Fraction

class Solver:
    ''' The Solver Class '''
    def __init__(self, network: MModel.Network, task_dict: dict, free_util: float):
        self._network = network
        self._task_dict = task_dict
        self._free_util = free_util
        self._solver = z3.Optimize()
        #self._solver = z3.Solver()
        self._var_name_map: typing.Dict[str, z3.ArithRef] = {}

    def __build_var(self):
        '''
        Build vars for every communication task
        '''
        # build for min_max Intermediate variables
        self._var_name_map["max"] = z3.Real("max")

        for node in self._task_dict:
            #print("node: {}".format(node.name))
            tasks = self._task_dict[node]
            for task in tasks:
                # traverse task list in each node
                # skip free-task
                if isinstance(task, TModel.FreeTask):
                    continue
                #print("\ttask: {}".format(task.name))
                # phi var and deadline var
                self._var_name_map["{}_phi".format(task.name)] = z3.Real("{}_phi".format(task.name))
                self._var_name_map["{}_deadline".format(task.name)] = z3.Real("{}_deadline".format(task.name))

        return

    def __build_constraints(self):
        '''
        Build constraints
        '''
        s = self._solver

        for node in self._task_dict:
            tasks = self._task_dict[node]
            # expr = 0
            for task in tasks:
                # skip free-task
                if isinstance(task, TModel.FreeTask):
                    continue
                _phi0 = int(task.offset0)
                _d0 = int(task.deadline0)
                _wcet0 = int(task.wcet)
                _delta = task.delta
                # constraints for d
                _d = self._var_name_map['{}_deadline'.format(task.name)]
                s.add(_d >= _wcet0)
                s.add(_d <= _d0)
                # constraints for phi
                _phi = self._var_name_map['{}_phi'.format(task.name)]
                s.add(_phi >= _phi0)
                s.add(_phi <= _d - _wcet0)
                # part of util constraints
                # expr += _wcet0 / _d
                # max
                _max = self._var_name_map['max']
                _expr_temp = (_phi - _phi0) * _delta - (_d0 - _d) * (1 - _delta) + _d - _phi
                s.add(_max >= _expr_temp)
                _expr_temp = (_d0 - _d) * (1 - _delta) - (_phi - _phi0) * _delta + _d - _phi
                s.add(_max >= _expr_temp)
                # Not right
                _expr_temp = 5 * _wcet0 / ( 0.95 - self._free_util)
                s.add(_d >= _expr_temp)
            # Add util constraints
            # s.add(expr <= (1-self._free_util))
        #  add task precedence constraints
        
        for node in self._task_dict:
            tasks = self._task_dict[node]
            for task in tasks:
                if isinstance(task, TModel.FreeTask) or isinstance(task, TModel.ConsumerTask):
                    continue
                
                _producer = task
                _shaper = task.vlink.receive_task
                if not isinstance(_shaper, TModel.ShaperTask):
                    continue
                _consumer = _shaper.vlink.receive_task
                if not isinstance(_consumer, TModel.ConsumerTask):
                    raise Exception("not a consumer")
                
                _s_phi = self._var_name_map['{}_phi'.format(_shaper.name)]
                _s_deadline = self._var_name_map['{}_deadline'.format(_shaper.name)]
                _p_phi = self._var_name_map['{}_phi'.format(_producer.name)]
                _p_deadline = self._var_name_map['{}_deadline'.format(_producer.name)]
                _c_phi = self._var_name_map['{}_phi'.format(_consumer.name)]
                #s.add(_r_phi >= _s_phi)
                s.add(_s_phi >= _p_phi + _p_deadline + 1000)
                s.add(_s_phi + _s_deadline + 1000 <= _c_phi)
        
        # set objective: min_max
        _max = self._var_name_map['max']
        h = s.minimize(_max)
        return

    def solve(self):
        # build var
        self.__build_var()
        # build constraints
        h = self.__build_constraints()
         
        # solver
        print("Slover started!")
        _t0 = time.clock()
        res = self._solver.check()
        _t1 = time.clock()
        print("Slover finished in %f s!" % (_t1 - _t0))

        if res != z3.sat:
            print(res)
            return None

        # return a dict {var.name: value}
        #min_max = self._solver.lower(h)
        model = self._solver.model()
        retdict = {}
        for var in model:
            _fraction: Fraction = model[var].as_fraction()
            _numerator: int = _fraction.numerator
            _denominator: int = _fraction.denominator
            retdict[var.name()] =  _numerator // _denominator # precision: 1us
        return retdict
