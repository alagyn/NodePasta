
from example_nodes import const_source, nullable_input, output_node, sum_node
from node_graph import NodeGraph

from tk_node_graph import TKNodeGraph, NodeManager, Vec

import tkinter as tk

if __name__ == '__main__':
    ng = NodeGraph()

    src1 = const_source.ConstSource(10)
    src2 = const_source.ConstSource(2)

    ng.addNodes(src1, src2)

    p = nullable_input.Power()
    s = sum_node.SumNode()
    o = output_node.OutputNode()

    ng.addNodes(p, s, o)

    src1.addChild(p, 0, 0)
    src2.addChild(p, 0, 1)

    p.addChild(s, 0, 0)
    src2.addChild(s, 0, 1)

    s.addChild(o, 0, 0)

    root = tk.Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    f = tk.LabelFrame(root, text='CANVAS')
    f.grid(row=0, column=0, sticky='nesw')

    f.columnconfigure(0, weight=1)
    f.rowconfigure(0, weight=1)

    nodeMan = NodeManager()

    nodeMan.addNode(src1, Vec(30, 20))
    nodeMan.addNode(s, Vec(200, 20))
    nodeMan.addNode(p, Vec(100, 100))

    nGraph = TKNodeGraph(f, nodeMan)
    nGraph.grid(row=0, column=0, sticky='nesw')

    root.mainloop()