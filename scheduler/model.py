"""调度器模型"""

from msg_scheduler import model

class Task(model.Application):
    """端节点上的可执行任务"""

    def __init__(self, network: model.Network, name: str, node_name: str):
        super().__init__(network, name, node_name)
    # period
    # Application already has period.
    # offset0
    @property
    def offset0(self) -> int:
        return self._offset0
    @offset0.setter
    def offset0(self, offset0: int):
        self._offset0 = offset0
    # wcet
    @property
    def wcet(self) -> int:
        return self._wcet
    @wcet.setter
    def wcet(self, wcet:int):
        self._wcet = wcet
    # deadline0
    @property
    def deadline0(self) -> int:
        return self._deadline0
    @deadline0.setter
    def deadline0(self, deadline0: int):
        self._deadline0 = deadline0
    

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


class ConsumerTask(CommTask):
    """消费者实时通信类任务"""

    def __init__(self, network: model.Network, name: str, node_name: str):
        super().__init__(network, name, node_name)


class ShaperTask(CommTask):
    """Shaper实时通信类任务"""

    def __init__(self, network: model.Network, name: str, node_name: str):
        super().__init__(network, name, node_name)
