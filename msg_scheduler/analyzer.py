import subprocess
import sys
from collections import defaultdict

import pandas as pd
import networkx
import random
import functools
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from .model import Network, Link, Frame, Node
import io

if sys.platform == 'darwin':
    matplotlib.use("TkAgg")


class Analyzer:
    def __init__(self, df: pd.DataFrame, network: Network, lcm: int):
        self._df = df
        self._network = network
        self._graph = network.graph
        self._lcm = lcm

    def print_by_time(self):
        print(self._df.sort_values(by='time_slot'))

    def print_by_app(self):
        res = self._df.sort_values(by='app')
        print(res)

    def _animate_update(self, ax, time_slot):
        ax.clear()
        ax.set_title(f'Time slot: {time_slot}')
        edge_lable = dict()
        pos = networkx.spring_layout(self._graph, seed=0, scale=3)
        cur_table = self._df[self._df['time_slot'] == time_slot]
        for idx, cur_row in cur_table.iterrows():
            link = cur_row['link']
            edge_lable[(link.node1.name, link.node2.name)] = cur_row['app'].name

        networkx.draw_networkx_edges(self._graph, pos=pos, ax=ax, edge_color='gray')

        nodes = networkx.draw_networkx_nodes(self._graph, pos=pos, ax=ax, node_color="white", node_size=1000,
                                             node_shape='o')
        nodes.set_edgecolor('black')

        networkx.draw_networkx_labels(self._graph, pos=pos, ax=ax, font_size=8)

        networkx.draw_networkx_edge_labels(self._graph, pos=pos, edge_labels=edge_lable, ax=ax)
        ax.set_xticks([])
        ax.set_yticks([])

    def animate(self):
        fig, ax = plt.subplots(figsize=(8, 8))
        ani = animation.FuncAnimation(fig, functools.partial(self._animate_update, ax), frames=self._lcm, interval=650,
                                      repeat=True)

        # Set up formatting for the movie files
        ani.save('/tmp/res.mov', fps=1, dpi=100)
        plt.show()
        pass

    def export(self, hosts=("127.0.0.1",)):
        exported = io.StringIO()
        p = functools.partial(print, file=exported)

        node_app_map = {}
        for app in self._df['app'].unique():
            node_app_map[app.node] = app
        msg_core_app = defaultdict(list)

        app_count = 0
        for node in self._graph.nodes:
            if node.startswith('msg'):
                msg_core_app[node] = msg_core_app[node]
                for nei in self._graph.neighbors(node):
                    if nei.startswith('app'):
                        app_count += 1
                        msg_core_app[node].append(nei)

        p(len(msg_core_app), self._lcm)
        for i, ma in enumerate(msg_core_app.keys()):
            # inter msg server endpoint and app endpoint
            ip = random.Random(200 + i).choice(hosts)
            p(ma, ip, 10801 + i, 1 if i == 0 else 0, ip, 20801 + i)
        p()

        # 每个app什么时间槽发送一个消息
        for msg_node, app_nodes in msg_core_app.items():
            for app_node in app_nodes:
                app = node_app_map[app_node]
                for idx, row in self._df[self._df['app'] == app].iterrows():
                    if row['link'].node1.name == app_node and int(row['time_slot']) < app.peroid:
                        p(':', app.name)
                        p(row['time_slot'], app.peroid, msg_node)

        p()

        # 每个msg_core需要在什么时间把消息从哪转到哪
        def find_next_node_not_switch(frame: Frame, n: Node) -> Node:
            if not n.name.startswith('switch'):
                return n
            for _, r in self._df.iterrows():
                if r['link'].node1 != n or r['frame'].id != frame.id:
                    continue
                if not r['link'].node2.name.startswith('switch'):
                    return r['link'].node2
                else:
                    return find_next_node_not_switch(frame, r['link'].node2)

        def find_prev_node_not_switch(frame: Frame, n: Node) -> Node:
            if not n.name.startswith('switch'):
                return n
            for _, r in self._df.iterrows():
                if r['link'].node2 != n or r['frame'].id != frame.id:
                    continue
                if not r['link'].node1.name.startswith('switch'):
                    return r['link'].node1
                else:
                    return find_next_node_not_switch(frame, r['link'].node1)

        def cvt_node(node: Node):
            return node_app_map[node.name] if node.name.startswith('app') else node.name

        for msg_node in msg_core_app.keys():
            tlist = []
            for _, row in self._df.iterrows():
                if row['link'].node1 == msg_node:
                    # msg node需要转发该消息
                    target_node = find_next_node_not_switch(row['frame'], row['link'].node2)
                    tlist.append((msg_node, 'send', cvt_node(target_node), row['frame'].id, row['time_slot']))
                elif row['link'].node2 == msg_node:
                    target_node = find_prev_node_not_switch(row['frame'], row['link'].node1)
                    tlist.append((msg_node, 'recv', cvt_node(target_node), row['frame'].id, row['time_slot']))
            tlist = sorted(tlist, key=lambda x: int(x[4]))

            p(':', msg_node)
            p(self._lcm, len(msg_core_app[msg_node]), len(tlist))
            p('\n'.join(map(lambda xm: node_app_map[xm].name, msg_core_app[msg_node])))
            for x in tlist:
                for y in x[1:]:
                    p(y, end=' ')
                p()
            p()
        with open('/tmp/tt.txt.tmp', 'w+') as f:
            print(exported.getvalue(), file=f)

        for ip in hosts:
            subprocess.run(f'scp /tmp/tt.txt.tmp {ip}:/tmp/tt.txt'.split(' '))
        # print(exported.getvalue())
