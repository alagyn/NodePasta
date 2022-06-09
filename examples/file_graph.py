import sys
import tkinter as tk

from example_nodes import const_source, power_node, output_node, sum_node
from nodepasta.ng_errors import NodeGraphError
from nodepasta.node_graph import NodeGraph
from nodepasta.tk_node_graph import TKNodeGraph

if __name__ == '__main__':
    filename = ''
    try:
        filename = sys.argv[1]
    except IndexError:
        print("Usage: example_file_graph.py [filename]")
        exit()

    ng = NodeGraph()

    nodeTypes = [
        const_source.ConstSource,
        power_node.Power,
        sum_node.SumNode,
        output_node.OutputNode
    ]

    for t in nodeTypes:
        ng.registerNodeClass(t)

    try:
        ng.loadFromFile(filename)
    except NodeGraphError as err:
        print("ERROR:", str(err))
        exit()

    ng.execute()

    root = tk.Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    f = tk.LabelFrame(root, text='CANVAS')
    f.grid(row=0, column=0, sticky='nesw')

    f.columnconfigure(0, weight=1)
    f.rowconfigure(0, weight=1)

    ngFrame = TKNodeGraph(f, ng)
    ngFrame.setPortTypeColor("float", "lightgreen")
    ngFrame.reloadGraph()

    ngFrame.grid(row=0, column=0, sticky='nesw')

    root.mainloop()
