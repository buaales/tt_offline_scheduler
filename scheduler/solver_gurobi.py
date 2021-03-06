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
        self.f = open("./output/constraint_sample.txt", 'w')

    def __build_var(self):
        '''
        Build vars for every communication task
        '''
        # build for min_max Intermediate variables
        self._vars["max"] = self._solver.addVar(vtype=GRB.INTEGER, name="max")
        self.f.writelines("max\n")
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
                self.f.writelines("{}_phi\n".format(task.name))
                self.f.writelines("{}_deadline\n".format(task.name))

    def __build_constraints(self):
        '''
        Build constraints
        '''
        s = self._solver
        for node in self._task_dict:
            tasks = self._task_dict[node]
            expr = -(1 - self._free_util)
            expr_str = " -(1 - 0.75 * 0.75) "
            for task in tasks:
                # skip free-task
                if isinstance(task, TModel.FreeTask):
                    continue
                _phi0 = int(task.offset0 * 1000)
                _d0 = int(task.deadline0 * 1000)
                _wcet0 = int(task.wcet * 1000)
                _period0 = int(task.peroid * 1000)
                _delta = task.delta
                # constraints for d
                _d = self._vars['{}_deadline'.format(task.name)]
                s.addConstr(_d >= _wcet0, 'c_{}_d_0'.format(task.name))
                s.addConstr(_d <= _d0, 'c_{}_d_1'.format(task.name))
                self.f.writelines("{} >= {}\n".format('{}_deadline'.format(task.name), _wcet0))
                self.f.writelines("{} <= {}\n".format('{}_deadline'.format(task.name), _d0))
                # constraints for phi
                _phi = self._vars['{}_phi'.format(task.name)]
                s.addConstr(_phi >= _phi0, 'c_{}_phi_0'.format(task.name))
                s.addConstr(_phi <= _period0 - _d , 'c_{}_phi_1'.format(task.name))
                self.f.writelines("{} >= {}\n".format('{}_phi'.format(task.name), _phi0))
                self.f.writelines("{} <= {} - {}\n".format('{}_phi'.format(task.name), _period0, '{}_deadline'.format(task.name)))
                # part of util constraints
                # expr += _wcet / _d
                expr_str += " + {} / {}".format(_wcet0, '{}_deadline'.format(task.name))
                # max
                _max = self._vars['max']
                _expr_temp = (_phi - _phi0) * _delta - (_d0 - _d) * (1 - _delta) + _d - _phi
                s.addConstr(_max >= _expr_temp, 'max_{}'.format(task.name))
                _expr_temp_str = "({} - {}) * {} - ({} - {}) * (1 - {}) + {} - {}".format('{}_phi'.format(task.name),
                                _phi0, _delta, _d0, '{}_deadline'.format(task.name), _delta, '{}_deadline'.format(task.name), '{}_phi'.format(task.name))
                self.f.writelines("max >= {}\n".format(_expr_temp_str))
                _expr_temp = (_d0 - _d) * (1 - _delta) - (_phi - _phi0) * _delta + _d - _phi
                s.addConstr(_max >= _expr_temp, 'max_{}'.format(task.name))
                _expr_temp_str = "({} - {}) * (1 - {}) - ({} - {}) * {} + {} - {}".format(_d0, '{}_deadline'.format(task.name),
                                _delta, '{}_phi'.format(task.name), _phi0, _delta, '{}_deadline'.format(task.name), '{}_phi'.format(task.name))
                self.f.writelines("max >= {}\n".format(_expr_temp_str))
                # Not right
                _expr_temp = 5 * _wcet0 / ( 0.95 - self._free_util)
                s.addConstr(_d >= _expr_temp, 'd_{}'.format(task.name))
            # Add util constraints
            # s.addConstr(expr <= 0, 'u_{}'.format(node.name))
            self.f.writelines("{} <= 0\n".format(expr_str))

        # set objective: min_max
        _max = self._vars['max']
        s.setObjective(_max, GRB.MINIMIZE)


    def solve(self, file_path: str):
        try:
            # build var
            self.f.writelines("###### Vars ######\n")
            self.__build_var()
            # build constraints
            self.f.writelines("###### Contrains ######\n")
            self.__build_constraints()
            return
            # solver
            print("Slover started!")
            _t0 = time.clock()
            self._solver.optimize()
            _t1 = time.clock()
            print("Slover finished in %f s!" % (_t1 - _t0))

            # check util
            for node in self._task_dict:
                _util = 0
                tasks = self._task_dict[node]
                for task in tasks:
                    _wcet0 = int(task.wcet * 1000)
                    if isinstance(task, TModel.FreeTask):
                        _dd = task.deadline0 * 1000
                        _util += _wcet0 / _dd
                    else:
                        _dd = self._solver.getVarByName('{}_deadline'.format(task.name))
                        _util += _wcet0 / _dd.x
                print("{} util is {}".format(node.name, _util))
            # output
            with open(file_path, 'w') as f:
                for var in self._solver.getVars():
                    f.writelines('{}, {}\n'.format(var.varName, var.x))
        except GurobiError as e:
            print("Gurobi Error: %s" % (e.message))

