import sys
import tkinter as tk

from nodepasta.nodegraph import NodeGraph
from .example_nodes import const_source, power_node, output_node, sum_node, offset_node, listifier, enumNode
from nodepasta.errors import NodeGraphError
from nodepasta.tk.tk_node_graph import TKNodeGraph

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
        output_node.OutputNode,
        offset_node.OffsetNode,
        listifier.ListifierNode,
        enumNode.EnumNode
    ]

    for t in nodeTypes:
        ng.registerNodeClass(t)

    root = tk.Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    f = tk.LabelFrame(root, text='CANVAS')
    f.grid(row=0, column=0, sticky='nesw')

    f.columnconfigure(0, weight=1)
    f.rowconfigure(0, weight=1)

    ngFrame = TKNodeGraph(f, ng)
    ngFrame.setPortTypeColor("float", "lightgreen")
    ngFrame.setPortTypeColor('int', "brown")


    def reload():
        try:
            ng.loadFromFile(filename)
            ngFrame.reset()
            ngFrame.reloadGraph()
        except NodeGraphError as err:
            print("ERROR:", str(err))
            exit()


    reload()

    ngFrame.grid(row=0, column=0, sticky='nesw')


    def execute():
        try:
            ng.execute()
        except NodeGraphError as e:
            # Set an error message in the info box
            ngFrame.setErrorMessage(f'{e.loc}: {e.msg}')


    btnFrame = tk.LabelFrame(root, text='Buttons')
    btnFrame.grid(row=1, column=0, sticky='sw')


    def save():
        file = 'out.json'
        print(f"Saving to {file}")
        ng.saveToFile(file)


    tk.Button(btnFrame, text="Execute", command=execute).grid(row=0, column=0, sticky='w')
    tk.Button(btnFrame, text="Reload", command=reload).grid(row=0, column=1, sticky='w')
    tk.Button(btnFrame, text='Save', command=save).grid(row=0, column=2, stick='w')

    root.state('zoomed')

    root.mainloop()
