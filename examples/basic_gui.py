from argparse import ArgumentParser
import os

import imgui as im
import imgui.imnodes as imnodes
import imgui.implot as implot
import imgui.glfw as glfw

from nodepasta.impasta.imgui_node_graph import ImNodeGraph
from nodepasta.nodegraph import NodeGraph

from .example_nodes import const_source, power_node, output_node, sum_node, offset_node, listifier, enumNode

WIDTH = 800
HEIGHT = 600

WINDOW_FLAGS = im.WindowFlags.NoResize | im.WindowFlags.NoCollapse | im.WindowFlags.NoMove

def main():
    parser = ArgumentParser()
    parser.add_argument("input_file")
    args = parser.parse_args()

    # Init GLFW
    window = glfw.Init(window_width=WIDTH, window_height=HEIGHT, title="ImPasta")

    if window is None:
        print("Error during GLFW init")
        exit(1)

    # Create contexts.
    im.CreateContext()
    imnodes.CreateContext()
    # Init glfw
    glfw.InitContextForGLFW(window)
    # Set imgui Style
    im.StyleColorsDark()
    # Set the background clear color
    clearColor = im.Vec4(0.45, 0.55, 0.6, 1.0)

    # TODO load graph
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
        print(f"Registering {t.NODETYPE}")
        ng.registerNodeClass(t)

    if os.path.exists(args.input_file):
        ng.loadFromFile(args.input_file)
    gui = ImNodeGraph(ng)

    while True:
        # Init for new frame
        glfw.NewFrame()
        im.NewFrame()

        # Make a window for the graph to live in
        io = im.GetIO()
        im.SetNextWindowPos(im.Vec2(0, 0))
        im.SetNextWindowSize(io.DisplaySize)
        im.Begin("Graph", closable=False, flags=WINDOW_FLAGS)

        # Render some buttons
        if im.Button("Save"):
            print(f"Saving to {args.input_file}")
            ng.saveToFile(args.input_file)

        im.SameLine()

        if im.Button("Execute"):
            ng.setupNodes()
            print(ng.str_traversal())
            print("------------------- Executing --------------")
            ng.execute()

        # Render graph
        gui.render()

        # End the window
        im.End()
        # Tell backends to render frame
        im.Render()
        glfw.Render(window, clearColor)

        if glfw.ShouldClose(window):
            break

    # Destroy contexts
    # Must do this in the reverse as they were initialized
    imnodes.DestroyContext()
    im.DestroyContext()
    # Shutdown GLFW
    glfw.Shutdown(window)

if __name__ == '__main__':
    main()