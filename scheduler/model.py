"""调度器模型"""

from msg_scheduler import model

class Task(model.Application):
    """端节点上的可执行任务"""

    def __init__(self, network: model.Network, name: str, node_name: str):
        super().__init__(network, name, node_name)
    # period
    # Application already has period.
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
        self._wcet = wcet
    # deadline
    @property
    def deadline(self) -> int:
        return self._deadline
    @deadline.setter
    def deadline(self, deadline: int):
        self._deadline = deadline
    

class FreeTask(Task):
    """通信无关的实时任务"""

    def __init__(self, network: model.Network, name: str, node_name: str):
        super().__init__(network, name, node_name)

class CommTask(Task):
    """通信类是实时任务"""

    def __init__(self, network: model.Network, name: str, node_name: str):
        super().__init__(network, name, node_name)

    @property
    def delta(self) -> float:
        return self._delta
    @delta.setter
    def delta(self, delta):
        self._delta = delta

class ProducerTask(CommTask):
    """生产者实时通信类任务"""

    def __init__(self, network: model.Network, name: str, node_name: str):
        super().__init__(network, name, node_name)


class CustomerTask(CommTask):
    """消费者实时通信类任务"""

    def __init__(self, network: model.Network, name: str, node_name: str):
        super().__init__(network, name, node_name)


class ShaperTask(CommTask):
    """Shaper实时通信类任务"""

    def __init__(self, network: model.Network, name: str, node_name: str):
        super().__init__(network, name, node_name)
