''' z3 Slover Model '''
import time
import z3
import typing

from msg_scheduler import model as MModel
from scheduler import model as TModel

class Solver:
    ''' The Solver Class '''
    def __init__(self, network: MModel.Network, task_dict: dict, free_util: float):
        self._network = network
        self._task_dict = task_dict
        self._free_util = free_util
        self._solver = z3.Optimize()
        self._var_name_map: typing.Dict[str, z3.ArithRef] = dict()

    def __build_var(self):
        '''
        Build vars for every communication task
        '''
        # build for min_max Intermediate variables
        self._var_name_map["max"] = z3.Real("max")

        for node in self._task_dict:
            tasks = self._task_dict[node]
            for task in tasks:
                # traverse task list in each node
                # skip free-task
                if isinstance(task, TModel.FreeTask):
                    continue
                # phi var and deadline var
                self._var_name_map["{}_phi".format(task.name)] = z3.Real("{}_phi".format(task.name))
                self._var_name_map["{}_deadline".format(task.name)] = z3.Real("{}_deadline".format(task.name))

    def __build_constraints(self):
        '''
        Build constraints
        '''
        s = self._solver

        for node in self._task_dict:
            tasks = self._task_dict[node]
            expr = 0
            for task in tasks:
                # skip free-task
                if isinstance(task, TModel.FreeTask):
                    continue
                _phi0 = int(task.offset0 * 1000)
                _d0 = int(task.deadline0 * 1000)
                _wcet0 = int(task.wcet * 1000)
                _delta = task.delta
                # constraints for d
                _d = self._var_name_map['{}_deadline'.format(task.name)]
                s.add(_d >= 0)
                s.add(_d <= _d0)
                # constraints for phi
                _phi = self._var_name_map['{}_phi'.format(task.name)]
                s.add(_phi >= _phi0)
                s.add(_phi <= _d - _wcet0)
                # part of util constraints
                expr += _wcet0 / _d
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
            #s.add(expr <= (1-self._free_util))

        # set objective: min_max
        _max = self._var_name_map['max']
        h = s.minimize(_max)
        return h

    def solve(self, file_path: str):
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
            return None
        #self._solver.lower(h)

        # return a dict {var.name: value}
        model = self._solver.model()
        retdict = {}
        for var in model:
            retdict[var.name] = model[var].as_decimal(2)
        return retdict
