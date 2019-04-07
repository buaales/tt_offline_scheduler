import typing
import networkx
import networkx.algorithms.approximation
import matplotlib.pyplot as plt
import pprint
import math
import pandas
from fractions import Fraction
from collections import defaultdict


class Frame:
    _id = 0

    def __init__(self, app: 'Application', peroid: int, length: int = 1):
        self._app = app
        self._offset: int = 0
        self._peroid: int = peroid
        self._length: int = length
        self._id = Frame._id
        self._min_offset = 0
        self._max_offset = peroid
        Frame._id += 1

    @property
    def app(self) -> 'Application':
        return self._app

    @property
    def length(self) -> int:
        return self._length

    @length.setter
    def length(self, length):
        self._length = length

    @property
    def peroid(self) -> int:
        return self._peroid

    @peroid.setter
    def peroid(self, p):
        self._peroid = p

    @property
    def offset(self):
        return self._offset

    @property
    def id(self):
        return self._id

    @offset.setter
    def offset(self, length):
        self._offset = length

    @property
    def min_offset(self):
        return self._min_offset

    @min_offset.setter
    def min_offset(self, min_offset):
        self._min_offset = min_offset

    @property
    def max_offset(self):
        return self._max_offset

    @max_offset.setter
    def max_offset(self, max_offset):
        self._max_offset = max_offset        

    def __eq__(self, value: 'Frame'):
        return value._id == self._id

    def __hash__(self):
        return hash(self._id)

    def __str__(self):
        return f'{self._id}:{self._peroid}'


class NamedObj:
    def __init__(self, name: str):
        self._name = name

    def __eq__(self, value):
        return (isinstance(value, Node) and value._name == self._name) or (value == self._name)

    def __hash__(self):
        return hash(self._name)

    @property
    def name(self):
        return self._name

    def __str__(self):
        return self.name


class Node(NamedObj):
    """代表网络中的节点，节点之间可以互联"""

    def __init__(self, name: str):
        super().__init__(name)


class EndNode(Node):
    """网络中的计算节点"""

    def __init__(self, name: str):
        super().__init__(name)


class SwitchNode(Node):
    """网络中的交换机"""

    def __init__(self, name: str, delay: int = 1, membound: int = 999999):
        super().__init__(name)
        self._delay = delay  # no internal delay
        self._membound = membound  # unlimited membound

    @property
    def delay(self):
        return self._delay

    @delay.setter
    def delay(self, delay: int):
        self._delay = delay

    @property
    def membound(self):
        return self._membound

    @membound.setter
    def membound(self, bound: int):
        self._membound = bound


class Link:
    """代表一条数据流链路，链接了两个节点"""

    def __init__(self, node1: Node, node2: Node):
        self._node1 = node1
        self._node2 = node2

    @property
    def node1(self):
        return self._node1

    @property
    def node2(self):
        return self._node2

    def __hash__(self):
        return hash((self.node1.name, self.node2.name))

    def __eq__(self, value):
        return self.node1 == value.node1 and self.node2 == value.node2

    def __str__(self):
        return f'{self._node1.name} -> {self._node2.name}'


class Network:
    """网络拓扑"""

    def __init__(self):
        self._node_name_map: typing.Dict[str, Node] = dict()
        self._nodes: typing.Set[Node] = set()
        self._end_nodes: typing.Set[EndNode] = set()
        self._msg_nodes: typing.Set[SwitchNode] = set()
        self._link_name_map: typing.Dict[typing.Tuple[str, str], Link] = dict(
        )
        self._links: typing.Set[Link] = set()
        self._neighbor: typing.DefaultDict[Node, typing.Set[Node]] = defaultdict(
            set)  # 每个节点的邻居节点

        self._graph = networkx.DiGraph()

    @property
    def end_nodes(self):
        return self._end_nodes

    @property
    def msg_nodes(self):
        return self._msg_nodes

    def add_neighbor(self, node_me: Node, node_neighbor: Node):
        if node_me not in self._nodes:
            raise Exception("Node not in network")
        if node_neighbor in self._neighbor[node_me]:
            raise Exception("neighbor redefined")
        self._neighbor[node_me].add(node_neighbor)

    def add_node(self, node: Node) -> 'Network':
        self._nodes.add(node)
        self._node_name_map[node.name] = node
        if isinstance(node, EndNode):
            self._end_nodes.add(node)
        elif isinstance(node, SwitchNode):
            self._msg_nodes.add(node)
        return self

    def add_link(self, node1_name: str, node2_name: str) -> 'Network':
        node1 = self[node1_name]
        node2 = self[node2_name]
        link1 = Link(node1, node2)
        link2 = Link(node2, node1)
        self._links.add(link1)
        self._links.add(link2)

        self.add_neighbor(node1, node2)
        self.add_neighbor(node2, node1)

        self._graph.add_edge(node1.name, node2.name)
        self._graph.add_edge(node2.name, node1.name)

        self._link_name_map[(node1.name, node2.name)] = link1
        self._link_name_map[(node2.name, node1.name)] = link2
        return self

    def get_link_by_name(self, node1: typing.Union[Node, str], node2: typing.Union[Node, str]):
        if isinstance(node1, Node):
            node1 = node1.name
        if isinstance(node2, Node):
            node2 = node2.name
        return self._link_name_map[(node1, node2)]

    def get_link_helper(self):
        def helper(node_name1: str, node_targets: typing.Union[typing.List[str], str]):
            if node_name1 is None:
                raise Exception('node_name1 should not be None')
            if not isinstance(node_targets, list):
                node_targets = [node_targets]

            for n in node_targets:
                print('add {} {}'.format(node_name1, n))
                self.add_link(node_name1, n)
            return helper

        return helper

    def __getitem__(self, name: str) -> Node:
        return self._node_name_map[name]

    def __str__(self):
        return pprint.pformat(self._neighbor)

    @property
    def graph(self):
        return self._graph

    def draw(self):
        networkx.draw_networkx(self.graph)
        plt.axis('off')
        plt.show()


class VirtualLink(NamedObj):
    """数据流虚链路"""

    def __init__(self, name: str, network: Network, app: 'Application', sender: Node,
                 receivers: typing.List[Node], receive_task):
        super().__init__(name)
        self._network: Network = network
        self._sender: Node = sender
        self._receivers: typing.List[Node] = receivers
        self._receive_task = receive_task # TODO: TEMP ADD
        self._app: 'Application' = app

        self._steiner_tree: networkx.classes.Graph = None
        self._reciever_path: typing.Dict[str, typing.List[str]] = defaultdict(list)  # 从发送者到每个接收者的斯坦纳树路径

        self._init_virtual_link(sender.name, [x.name for x in receivers])

    def _init_virtual_link(self, sender: str, receivers: typing.List[str]):
        g = self._network.graph.to_undirected()
        res = networkx.algorithms.approximation.steiner_tree(g, [sender] + receivers)
        self._steiner_tree = res
        for recv in receivers:
            path = networkx.algorithms.shortest_simple_paths(res, sender, recv)
            self._reciever_path[recv].extend(next(path))

    def __str__(self):
        return pprint.pformat(self._reciever_path)

    @property
    def receiver_path(self) -> typing.Dict[str, typing.List[str]]:
        return self._reciever_path

    @property
    def app(self):
        return self._app
    
    @property
    def receive_task(self):
        return self._receive_task

    def draw(self):
        g = self._network.graph.to_undirected()
        res = networkx.algorithms.approximation.steiner_tree(g, [self._sender] + self._receivers)
        networkx.draw_networkx(g, networkx.shell_layout(g), ax=None)
        networkx.draw_networkx_edges(
            res, pos=networkx.shell_layout(g), edge_color='r')
        plt.axis('off')
        plt.show()


class Application(NamedObj):
    """代表运行在一个节点上的应用程序
    一个应用程序可以包含多条虚链路
    并在其生命周期内发送一个数据帧
    """

    def __init__(self, network: Network, name: str, sender_node_name: str):
        super().__init__(name)
        self._network: Network = network
        self._vlink: VirtualLink = None
        self._frame: Frame = None
        self._host_node: Node = network[sender_node_name]
        self._peroid: int = 1
        self._max_delay: int = 0
        self._depend_on_list: typing.Set['Application'] = set()

    def set_virtual_link(self, receivers: typing.List['Application']) -> 'Application':
        if self._frame is not None:
            raise Exception("only one vlink in per application")
        if len(receivers) != 1:
            raise Exception("only one receiver in per vlink")
        vlink = VirtualLink(f'{self.name}_vlink', self._network, self, self._host_node, [
            x._host_node for x in receivers], receivers[0])
        self._vlink = vlink
        return self

    def set_frame(self, peroid: int, max_delay: int = 9999, min_offset: int = 0, max_offset: int = 9999999) -> 'Application':
        """定义一个在某虚链路上发送的数据帧

        Arguments:
            peroid {int} -- 帧的周期
            max_delay {int} -- 帧的最大延迟
        """
        if self._frame is not None:
            raise Exception("only one frame in per application")
        self._frame = Frame(self, peroid)
        self._frame.min_offset = min_offset
        self._frame.max_offset = max_offset
        self._max_delay = max_delay
        self._peroid = peroid
        return self

    def depend_on(self, app: 'Application') -> 'Application':
        if app.peroid != self.peroid:
            raise Exception("app I depend on has an unequal peroid to me")
        self._depend_on_list.add(app)
        return self

    @property
    def vlink(self) -> VirtualLink:
        return self._vlink

    @property
    def frame(self) -> Frame:
        return self._frame

    @property
    def peroid(self) -> int:
        return self._peroid
    @peroid.setter
    def peroid(self, peroid: int):
        self._peroid = peroid

    @property
    def node(self) -> Node:
        return self._host_node

    @property
    def deps(self) -> typing.Set['Application']:
        return self._depend_on_list

    def check(self) -> bool:
        return self._frame is not None and self._vlink is not None


class MiddleResultMap:
    def __getitem__(self, key: typing.Tuple[Link, Frame]):
        pass

    def __setitem__(self, key: typing.Tuple[Link, Frame], value):
        pass


class ModelHook:
    """模型构建过程中会逐次调用该类中的函数
    """

    def _set_env(self, lcm: int, network: Network, app_name_map: typing.Dict[str, Application]):
        self._lcm = lcm
        self._network = network
        self._app_name_map = app_name_map
        self._frame_id_map = {app.frame.id: app.frame for app in self._app_name_map.values() if app.frame is not None}

    def __init__(self):
        self._middle_result = MiddleResultMap()
        self._frames_on_link: typing.DefaultDict[Link, typing.Set[typing.Tuple[Frame, int]]] = defaultdict(set)
        self._lcm = 0
        self._app_last_link: typing.Dict[Application, Link] = dict()

    @staticmethod
    def get_var_name(frame: Frame, frame_seq_in_peroid: int, link: Link) -> str:
        start_node = link.node1
        end_node = link.node2
        return f'{frame.app}#{frame.id}#{start_node}#{end_node}#{frame_seq_in_peroid}'

    def extract_var_name(self, name: str) -> typing.Tuple[Application, Frame, Link]:
        (app_name, frame_id, start_node_name, end_node_name, frame_seq_in_peroid) = name.split('#')
        return self._app_name_map[app_name], self._frame_id_map[int(frame_id)], Link(self._network[start_node_name],
                                                                                     self._network[end_node_name])

    def get_frames_on_link(self, link: Link) -> typing.Set[typing.Tuple[Frame, int]]:
        return self._frames_on_link[link]

    def on_send_from_sender(self, app: Application, node: EndNode, frame: Frame, frame_seq_in_peroid: int,
                            start_link: Link):
        print(f'{app}: send from {node}')

    def on_add_to_link(self, app: Application, link: Link, frame: Frame, frame_seq_in_peroid: int):
        """当新的数据帧需要经过该链路时被调用
        
        Arguments:
            link {Link} -- 数据帧经过的链路
            frame {Frame} -- 新加入的数据帧
        """
        print(f'{app}: send frame_{frame.id} on {link}')
        self._frames_on_link[link].add((frame, frame_seq_in_peroid))

    def on_switch(self, app: Application, switch: SwitchNode, frame: Frame, frame_seq_in_peroid: int, before_link: Link,
                  after_link):
        """当帧经过一个交换机时被调用
        
        Arguments:
            app {Application} -- [description]
            switch {SwitchNode} -- [description]
            before_link {Link} -- [description]
            after_link {[type]} -- [description]
        """
        print(f'{app}: frame_{frame.id} get switch {switch}')

    def on_received(self, app: Application, receiver: EndNode, frame: Frame, frame_seq_in_peroid: int, first_link: Link,
                    last_link: Link):
        """当帧到达接收者时被调用
        
        Arguments:
            app {Application} -- 应用
            receiver {EndNode} -- 接收者
            first_link {Link} -- 发送者的链路
            last_link {Link} -- 接收者的链路
        """
        print(f'{app}: frame_{frame.id} arrive in {receiver}')
        self._app_last_link[app] = last_link

    def solve(self):
        return {}

    def to_dataframe(self):
        df = pandas.DataFrame(columns=['app', 'frame', 'link', 'time_slot'])
        result = self.solve()
        for key, value in result.items():
            app, frame, link = self.extract_var_name(key)
            _fraction: Fraction = value.as_fraction()
            _numerator: int = _fraction.numerator
            _denominator: int = _fraction.denominator
            df.loc[len(df)] = [app, frame, link, _numerator // _denominator]
        return df


class Scheduler:
    def __init__(self, network: Network):
        self._network: Network = network
        self._apps: typing.List[Application] = list()
        self._app_name_map: typing.Dict[str, Application] = dict()

    def add_apps(self, apps: typing.List[Application]):
        self._apps.extend(apps)
        self._app_name_map.update([(app.name, app) for app in apps])

    @staticmethod
    def _lcm(a, b):
        return int((a * b) / math.gcd(a, b))

    @property
    def app_lcm(self):
        result = 1
        for app in self._apps:
            result = self._lcm(result, app.peroid)
        return result

    @staticmethod
    def _app_topo_sort(apps: typing.List[Application]):
        g = networkx.DiGraph()
        for app in apps:
            g.add_node(app.name)
            for dep in app.deps:
                g.add_edge(dep.name, app.name)
        return list(networkx.algorithms.topological_sort(g))

    def _solve_vlink(self, vlink: VirtualLink, hook: ModelHook):
        # 从vlink头到尾进行遍历
        first_link: Link = None
        for recv, path in vlink.receiver_path.items():
            for frame_seq_in_peroid in range(self.app_lcm // vlink.app.peroid):
                start_node: str = None
                for idx, path_item in enumerate(path):
                    if start_node is None:
                        start_node = path_item
                        hook.on_send_from_sender(vlink.app, self._network[start_node], vlink.app.frame,
                                                 frame_seq_in_peroid,
                                                 self._network.get_link_by_name(start_node, path[idx + 1]))
                        continue
                    end_node: str = path_item
                    link: Link = self._network.get_link_by_name(start_node, end_node)
                    if first_link is None:
                        first_link = link
                    hook.on_add_to_link(vlink.app, link, vlink.app.frame, frame_seq_in_peroid)
                    if end_node == recv:
                        hook.on_received(vlink.app, self._network[end_node], vlink.app.frame, frame_seq_in_peroid,
                                         first_link, link)
                    else:
                        start_node = end_node
                        hook.on_switch(vlink.app, self._network[end_node], vlink.app.frame, frame_seq_in_peroid, link,
                                       self._network.get_link_by_name(end_node, path[idx + 1]))

    def add_constrains(self, hook: ModelHook):
        # 开始遍历每一个应用的每一个帧的发送序列
        hook._set_env(self.app_lcm, self._network, self._app_name_map)
        sorted_app = self._app_topo_sort(self._apps)
        for app_name in sorted_app:
            app = self._app_name_map[app_name]
            if app.check():
                self._solve_vlink(app.vlink, hook)


