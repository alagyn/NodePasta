
from example_nodes import const_source, power_node, output_node, sum_node
from nodepasta.node_graph import NodeGraph

from nodepasta.tk_node_graph import TKNodeGraph, Vec

import tkinter as tk

if __name__ == '__main__':
    ng = NodeGraph()

    src1 = const_source.ConstSource(10)
    src2 = const_source.ConstSource(2)

    ng.addNodes(src1, src2)

    powerN = power_node.Power()
    sumN = sum_node.SumNode()
    outN = output_node.OutputNode()

    ng.addNodes(powerN, sumN, outN)

    ng.makeLink(src1, 0, powerN, 0)
    ng.makeLink(src2, 0, powerN, 1)

    ng.makeLink(powerN, 0, sumN, 0)
    ng.makeLink(src2, 0, sumN, 1)

    ng.makeLink(sumN, 0, outN, 0)

    ng.execute()

    root = tk.Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    f = tk.LabelFrame(root, text='CANVAS')
    f.grid(row=0, column=0, sticky='nesw')

    f.columnconfigure(0, weight=1)
    f.rowconfigure(0, weight=1)

    ngFrame = TKNodeGraph(f, ng)

    ngFrame.setPos(src1, Vec(30, 60))
    ngFrame.setPos(src2, Vec(30, 90))
    ngFrame.setPos(powerN, Vec(130, 20))
    ngFrame.setPos(sumN, Vec(200, 60))
    ngFrame.setPos(outN, Vec(300, 100))

    ngFrame.setPortTypeColor("float", "lightgreen")

    ngFrame.reloadGraph()

    ngFrame.grid(row=0, column=0, sticky='nesw')

    root.mainloop()