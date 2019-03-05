"""调度器模型"""

from msg_scheduler import model

class Task(model.NamedObj):
    """端节点上的可执行任务"""

    def __init__(self, name: str, node_id: int, task_id: int):
        super().__init__(name)
        self._node_id = node_id
        self._task_id = task_id
    # offset
    @property
    def offest(self) -> int:
        return self._offset
    @offset.setter
    def offset(self, offset:int):
        self._offset = offset
    # wcet
    @property
    def wcet(self) -> int:
        return self._wcet
    @wcet.setter
    def wcet(self, wcet:int):
        self._wect = wcet
    # deadline
    @property
    def deadline(self) -> int:
        return self._deadline
    @deadline.setter
    def deadline(self, deadline: int):
        self.deadline = deadline
    #peroid
    @property
    def peroid(self) -> int:
        return self._peroid
    @peroid.setter
    def peroid(self, peroid:int):
        self._peroid = peroid

class FreeTask(Task):
    """通信无关的实时任务"""

    def __init__(self, name: str, node_id: int, task_id: int):
        super().__init__(name, node_id, task_id)

class CommTask(Task):
    """通信类是实时任务"""

    def __init__(self, name: str, node_id: int, task_id: int):
        super().__init__(name, node_id, task_id)

    @property
    def delta(self) -> float:
        return self._delta
    @delta.setter
    def delta(self, delta):
        self._delta = delta

class ProducerTask(CommTask):
    """生产者实时通信类任务"""

    def __init__(self, name: str, node_id: int, task_id: int):
        super().__init__(name, node_id, task_id)


class CustomerTask(CommTask):
    """消费者实时通信类任务"""

    def __init__(self, name: str, node_id: int, task_id: int):
        super().__init__(name, node_id, task_id)


class ShaperTask(CommTask):
    """Shaper实时通信类任务"""

    def __init__(self, name: str, node_id: int, task_id: int):
        super().__init__(name, node_id, task_id)
