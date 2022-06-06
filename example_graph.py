
from example_nodes import const_source, nullable_input, output_node, sum_node
from nodepasta.node_graph import NodeGraph

from nodepasta.tk_node_graph import TKNodeGraph, NodeManager, Vec

import tkinter as tk

if __name__ == '__main__':
    ng = NodeGraph()

    src1 = const_source.ConstSource(10)
    src2 = const_source.ConstSource(2)

    ng.addNodes(src1, src2)

    powerN = nullable_input.Power()
    sumN = sum_node.SumNode()
    outN = output_node.OutputNode()

    ng.addNodes(powerN, sumN, outN)

    src1.addChild(powerN, 0, 0)
    src2.addChild(powerN, 0, 1)

    powerN.addChild(sumN, 0, 0)
    src2.addChild(sumN, 0, 1)

    sumN.addChild(outN, 0, 0)

    root = tk.Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    f = tk.LabelFrame(root, text='CANVAS')
    f.grid(row=0, column=0, sticky='nesw')

    f.columnconfigure(0, weight=1)
    f.rowconfigure(0, weight=1)

    nodeMan = NodeManager()

    nodeMan.addNode(src1, Vec(30, 20))
    nodeMan.addNode(sumN, Vec(200, 20))
    nodeMan.addNode(powerN, Vec(100, 100))
    nodeMan.addNode(outN, Vec(300, 100))

    nodeMan.setPortTypeColor("float", "lightgreen")

    nGraph = TKNodeGraph(f, nodeMan)
    nGraph.grid(row=0, column=0, sticky='nesw')

    root.mainloop()