from argparse import ArgumentParser
import os

import imgui as im
import imgui.imnodes as imnodes
import imgui.implot as implot
import imgui.glfw as glfw

from nodepasta.impasta.imgui_node_graph import ImNodeGraph
from nodepasta.impasta.imgui_arg_handlers import IntHandler, FloatHandler, EnumHandler
from nodepasta.nodegraph import NodeGraph
from nodepasta.impasta.imgui_arg_handlers import getDefaultArgHandlers

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
    imnodes.StyleColorsDark()

    imnodes.PushColorStyle(imnodes.Col.TitleBar, im.GetColorU32(im.Vec4(0.5, 0.2, 0.2, 1.0)))

    imnodes.PushColorStyle(imnodes.Col.TitleBarHovered, im.GetColorU32(im.Vec4(0.6, 0.4, 0.4, 1.0)))

    imnodes.PushColorStyle(imnodes.Col.TitleBarSelected, im.GetColorU32(im.Vec4(0.5, 0.3, 0.3, 1.0)))

    # Set the background clear color
    clearColor = im.Vec4(0.45, 0.55, 0.6, 1.0)

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

    # Register the default argument handlers
    argtypes = getDefaultArgHandlers()

    for k, v in argtypes.items():
        gui.registerArgHandler(k, v)

    while True:
        # Init for new frame
        glfw.NewFrame()
        im.NewFrame()

        # Make a window for the graph to live in
        io = im.GetIO()
        im.SetNextWindowPos(im.Vec2(0, 0))
        im.SetNextWindowSize(io.DisplaySize)
        im.Begin("Graph", flags=WINDOW_FLAGS)

        # Render some buttons
        if im.Button("Save"):
            print(f"Saving to {args.input_file}")
            ng.saveToFile(args.input_file)

        im.SameLine()

        if im.Button("Execute"):
            ng.setupNodes()
            print(ng.str_traversal())
            print("------------------- Executing --------------")
            try:
                ng.execute()
            except Exception as err:
                print("Error Executing:", err)

        # Render graph
    # TODO load graph
        gui.render()

        # End the window
        im.End()
        # Tell backends to render frame
        im.Render()
        glfw.Render(window, clearColor)

        if glfw.ShouldClose(window):
            break

    # Shutdown GLFW
    glfw.Shutdown(window)
    # Destroy contexts
    # Must do this in the reverse as they were initialized
    imnodes.DestroyContext()
    im.DestroyContext()


if __name__ == '__main__':
    main()
