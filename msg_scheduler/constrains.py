from .model import ModelHook, Application, Link, Frame, SwitchNode, EndNode
import z3
import typing
import functools


class Z3Hook(ModelHook):
    """模型构建过程中会逐次调用该类中的函数
    """

    def __init__(self):
        super().__init__()
        self._solver: z3.Solver = z3.Solver()
        self._var_name_map: typing.Dict[str, z3.ArithRef] = dict()

    def get_var(self, frame: Frame, frame_seq_in_peroid, link: Link):
        name = self.get_var_name(frame, frame_seq_in_peroid, link)
        if name not in self._var_name_map:
            var = z3.Real(name)
            self._var_name_map[name] = var
            self._solver.add(var >= frame_seq_in_peroid * frame.peroid)
            self._solver.add(var < (frame_seq_in_peroid + 1) * frame.peroid)
            return var
        else:
            return self._var_name_map[name]

    def on_send_from_sender(self, app: Application, node: EndNode, frame: Frame, frame_seq_in_peroid: int,
                            start_link: Link):
        super().on_send_from_sender(app, node, frame, frame_seq_in_peroid, start_link)

        # 应用发送帧的offset应该满足min和max约束
        if frame_seq_in_peroid == 0:
            self._solver.add(self.get_var(frame, frame_seq_in_peroid, start_link) >= frame.min_offset)
            #self._solver.add(self.get_var(frame, frame_seq_in_peroid, start_link) <= frame.max_offset)

        # 应用发送帧的间隔必须等于周期
        if frame_seq_in_peroid > 0:
            self._solver.add(
                self.get_var(frame, frame_seq_in_peroid, start_link) - self.get_var(frame, frame_seq_in_peroid - 1,
                                                                                    start_link) == frame.peroid)
        # 生成应用级依赖约束
        for dep_app in app.deps:
            self._solver.add(
                self.get_var(frame, frame_seq_in_peroid, start_link) - self.get_var(dep_app.frame, frame_seq_in_peroid,
                                                                                    self._app_last_link[dep_app])
                >= 1)

    def on_add_to_link(self, app: Application, link: Link, frame: Frame, frame_seq_in_peroid: int):
        """当新的数据帧需要经过该链路时被调用
        
        Arguments:
            app {Application} -- 应用程序
            link {Link} -- 数据帧经过的链路
            frame {Frame} -- 新加入的数据帧
        """
        super().on_add_to_link(app, link, frame, frame_seq_in_peroid)
        if frame_seq_in_peroid != 0:
            return
        # 链路独占约束
        for other_frame, sed_in_peroid in self.get_frames_on_link(link):
            if other_frame == frame:
                continue
            for my_c in range(0, self._lcm // frame.peroid):
                for other_c in range(0, self._lcm // other_frame.peroid):
                    self._solver.add(my_c * frame.peroid + self.get_var(frame, frame_seq_in_peroid, link) !=
                                     other_c * other_frame.peroid + self.get_var(other_frame, frame_seq_in_peroid,
                                                                                 link))

    def on_switch(self, app: Application, switch: SwitchNode, frame: Frame, frame_seq_in_peroid: int, before_link: Link,
                  after_link):
        """当帧经过一个交换机时被调用
        
        Arguments:
            app {Application} -- [description]
            switch {SwitchNode} -- [description]
            before_link {Link} -- [description]
            after_link {[type]} -- [description]
        """
        super().on_switch(app, switch, frame, frame_seq_in_peroid, before_link, after_link)
        self._solver.add(self.get_var(frame, frame_seq_in_peroid, after_link) -
                         self.get_var(frame, frame_seq_in_peroid,
                                      before_link) >= switch.delay)

    def on_received(self, app: Application, receiver: EndNode, frame: Frame, frame_seq_in_peroid: int, first_link: Link,
                    last_link: Link):
        """当帧到达接收者时被调用
        
        Arguments:
            app {Application} -- 应用
            receiver {EndNode} -- 接收者
            first_link {Link} -- 发送者的链路
            last_link {Link} -- 接收者的链路
        """
        super().on_received(app, receiver, frame, frame_seq_in_peroid, first_link, last_link)
        self._solver.add(self.get_var(frame, frame_seq_in_peroid, last_link) -
                         self.get_var(frame, frame_seq_in_peroid, first_link) <= app.peroid)
        if frame_seq_in_peroid == 0:
            self._solver.add(self.get_var(frame, frame_seq_in_peroid, last_link) <= frame.max_offset)
        if frame_seq_in_peroid != 0:
            self._solver.add(self.get_var(frame, frame_seq_in_peroid, last_link) -
                             self.get_var(frame, frame_seq_in_peroid - 1, last_link) == app.peroid)
            self._solver.add(self.get_var(frame, frame_seq_in_peroid, last_link) <= frame.max_offset + app.peroid * frame_seq_in_peroid)

    @functools.lru_cache(maxsize=1)
    def solve(self):
        if self._solver.check() != z3.sat:
            print("Cannot solve")
            return None
        model = self._solver.model()
        res = {name: model[var] for name, var in self._var_name_map.items()}
        return res

    def print(self):
        print(self._solver)
