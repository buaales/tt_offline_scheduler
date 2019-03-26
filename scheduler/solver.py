''' The Solver Model '''
import time

from msg_scheduler import model as MModel
from scheduler import model as TModel
from gurobipy import *

class Solver:
    ''' The Solver Class '''
    def __init__(self, network: MModel.Network, task_dict: dict, free_util: float):
        self._network = network
        self._task_dict = task_dict
        self._free_util = free_util
        self._solver = Model("tt_schduler")
        self._vars = {}

    def __build_var(self):
        '''
        Build vars for every communication task
        '''
        # build for min_max Intermediate variables
        self._vars["max"] = self._solver.addVar(vtype=GRB.INTEGER, name="max")

        for node in self._task_dict:
            tasks = self._task_dict[node]
            for task in tasks:
                # traverse task list in each node
                # skip free-task
                if isinstance(task, TModel.FreeTask):
                    continue
                # phi var and deadline var
                self._vars["{}_phi".format(task.name)] = self._solver.addVar(vtype=GRB.INTEGER,
                                                        name="{}_phi".format(task.name))
                self._vars["{}_deadline".format(task.name)] = self._solver.addVar(vtype=GRB.INTEGER,
                                                        name="{}_deadline".format(task.name))
                #self._vars["{}_wcet".format(task.name)] = self._solver.addVar(vtype=GRB.INTEGER,
                #                                        name="{}_wcet".format(task.name))

    def __build_constrains(self):
        '''
        Build constrains
        '''
        s = self._solver

        for node in self._task_dict:
            tasks = self._task_dict[node]
            expr = -(1 - self._free_util)
            for task in tasks:
                # skip free-task
                if isinstance(task, TModel.FreeTask):
                    continue
                _phi0 = int(task.offset0 * 1000)
                _d0 = int(task.deadline0 * 1000)
                _wcet0 = int(task.wcet * 1000)
                _delta = task.delta
                # constrains for d
                _d = self._vars['{}_deadline'.format(task.name)]
                s.addConstr(_d >= 0, 'c_{}_d_0'.format(task.name))
                s.addConstr(_d <= _d0, 'c_{}_d_1'.format(task.name))
                # constrains for phi
                _phi = self._vars['{}_phi'.format(task.name)]
                s.addConstr(_phi >= _phi0, 'c_{}_phi_0'.format(task.name))
                s.addConstr(_phi <= _d - _wcet0, 'c_{}_phi_1'.format(task.name))
                # part of util constrains
                #_wcet = self._vars['{}_wcet'.format(task.name)]
                #s.addConstr(_wcet == _wcet0, 'c_{}_wcet'.format(task.name))
                # expr += _wcet / _d
                # max
                _max = self._vars['max']
                _expr_temp = (_phi - _phi0) * _delta - (_d0 - _d) * (1 - _delta) + _d - _phi
                s.addConstr(_max >= _expr_temp, 'max_{}'.format(task.name))
                _expr_temp = (_d0 - _d) * (1 - _delta) - (_phi - _phi0) * _delta + _d - _phi
                s.addConstr(_max >= _expr_temp, 'max_{}'.format(task.name))
            # Add util constrains
            # s.addConstr(expr <= 0, 'u_{}'.format(node.name))

        # set objective: min_max
        _max = self._vars['max']
        s.setObjective(_max, GRB.MINIMIZE)


    def solve(self, file_path: str):
        try:
            # build var
            self.__build_var()
            print(len(self._solver.getVars()))
            for v in self._solver.getVars():
                print(3)
                print(v.varName)
            print(2)
            # build constrains
            self.__build_constrains()
            # solver
            print("Slover started!")
            _t0 = time.clock()
            self._solver.optimize()
            _t1 = time.clock()
            print("Slover finished in %f s!" % (_t1 - _t0))

            # output
            with open(file_path, 'w') as f:
                for var in self._solver.getVars():
                    f.writelines('{}, {}\n'.format(var.varName, var.x))
        except GurobiError as e:
            print("Gurobi Error: %s" % (e.message))

