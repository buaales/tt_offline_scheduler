"调度器模型"

class Task:

    _node_id = 0
    _task_id = 0

    def __init__(self, offset: int, wect: int, deadline: int, peroid: int, delta: float)
        self._offset: int = offset
        self._wect: int = wect
        self._deadline: int = deadline
        self._peroid: int = peroid
        self._delta: float = delta
