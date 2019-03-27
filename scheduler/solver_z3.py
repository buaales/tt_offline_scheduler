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
        self._solver = z3.Solver()
        self._var_name_map: typing.Dict[str, z3.ArithRef] = dict()

    def __build_var(self):
        pass

    def __build_constrains(self):
        pass

    def solve(self, file_path: str):
        pass
