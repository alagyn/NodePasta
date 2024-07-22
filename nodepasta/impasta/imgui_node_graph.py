from typing import Type, Dict

import imgui as im
import imgui.imnodes as imnodes

from nodepasta.nodegraph import NodeGraph
from nodepasta.node import Node
from nodepasta.ports import IOPort, InPort
from nodepasta.utils import Vec
from nodepasta.impasta.imgui_arg_handlers import ImArgHandler
from nodepasta.errors import NodeTypeError

# Add node popup ID
_ADD_NODE_PU = "Add Node"

DEF_COLOR = im.ColorConvertFloat4ToU32(im.Vec4(1.0, 1.0, 1.0, 1.0))

HELP_TEXT = (
    "Controls\n"
    "------------------------------\n"
    "[Space Bar] - Add new node\n"
    "[Left Click] - Select nodes (can box select)\n"
    "[Right Click] - Pan the canvas\n"
    "[Backspace/Delete] - Remove selected node\n"
    "\n"
    "Click and drag from a port to create a link.\n"
    "Hold [Control] and Drag a link to disconnect it.\n"
    "Drop a link on the background to remove it"
)


class ImNodeGraph:

    def __init__(self, ng: NodeGraph) -> None:
        self.ng = ng
        imnodes.PushAttributeFlag(imnodes.AttributeFlags.EnableLinkDetachWithDragClick)

        io = imnodes.GetIO()

        io.SetLinkDetachedWithModifierClick(im.ImKey.Mod_Ctrl)
        io.SetEmulateThreeButtonMouseMod(im.ImKey.Mod_Alt)
        io.AltMouseButton = im.MouseButton.Right

        self._argHandlers: Dict[str, Type[ImArgHandler]] = {}

        self._colors: Dict[str, int] = {}

        self.needToSave = False

        self._hoveredNode: Node | None = None

        self.showHelp = im.BoolRef(True)

    def registerArgHandler(self, datatype: str, handler: Type[ImArgHandler]):
        self._argHandlers[datatype] = handler

    def registerTypeColor(self, datatype: str, color: im.Vec4):
        self._colors[datatype] = im.ColorConvertFloat4ToU32(color)

    def render(self):
        if im.BeginTable("node_graph_editor", 2, flags=im.TableFlags.SizingStretchProp):
            im.TableNextColumn()
            im.TableSetupColumn("editor", init_width_or_weight=0.7)
            imnodes.BeginNodeEditor()
            imnodes.MiniMap(0.2, imnodes.MiniMapLocation.TopRight)

            self._addNodePopup()

            for node in self.ng:
                self._renderNode(node)

            imnodes.EndNodeEditor()

            self._hoveredNode = None
            temp = im.IntRef(-1)
            if imnodes.IsNodeHovered(temp):
                self._hoveredNode = self.ng._nodeLookup[temp.val]

            if im.IsKeyDown(im.ImKey.Backspace) or im.IsKeyDown(im.ImKey.Delete):
                selectedNodes = im.IntList()
                imnodes.GetSelectedNodes(selectedNodes)
                for x in selectedNodes:
                    imnodes.ClearNodeSelection(x)
                    self.ng.removeNode(self.ng._nodeLookup[x])

            startPortId = im.IntRef()
            endPortId = im.IntRef()
            # This has to happen after EndNodeEditor
            if imnodes.IsLinkCreated(startPortId, endPortId):
                self.needToSave = True
                try:
                    self.ng.makeLinkByID(startPortId.val, endPortId.val)
                except NodeTypeError:
                    pass  # don't make links if the datatype is wrong

            linkId = im.IntRef()
            if imnodes.IsLinkDestroyed(linkId):
                self.needToSave = True
                self.ng.unlinkByID(linkId.val)

            im.TableNextColumn()

            if self.showHelp.val:
                if self._hoveredNode is not None:
                    im.Text(self._hoveredNode.docs())
                else:
                    im.Text(HELP_TEXT)

            im.EndTable()

    def _renderNode(self, node: Node):
        if not imnodes.IsNodeSelected(node.nodeID):
            imnodes.SetNodeGridSpacePos(node.nodeID, im.Vec2(node.pos.x, node.pos.y))
        else:
            pos = imnodes.GetNodeGridSpacePos(node.nodeID)
            node.pos.x = pos.x
            node.pos.y = pos.y

        imnodes.BeginNode(node.nodeID)

        imnodes.BeginNodeTitleBar()
        if im.IsKeyDown(im.ImKey.Mod_Alt):
            im.Text(str(node))
        else:
            im.Text(node.NODETYPE)
        imnodes.EndNodeTitleBar()

        for arg in node.args.values():
            if self._argHandlers[arg.argType].render(arg):
                self.needToSave = True

        # TODO varports
        for iPort in node.inputs:
            self._renderPort(iPort)

        for oPort in node.outputs:
            self._renderPort(oPort)

        imnodes.EndNode()

        for link in node:
            imnodes.PushColorStyle(imnodes.Col.Link, link.pPort.color)
            imnodes.Link(link.linkID, link.pPort.portID, link.cPort.portID)
            imnodes.PopColorStyle()

    def _renderPort(self, port: IOPort):
        try:
            color = port.color
        except:
            try:
                color = self._colors[port.port.typeStr]
            except KeyError:
                color = DEF_COLOR
            port.color = color
        # Set the port color
        imnodes.PushColorStyle(imnodes.Col.Pin, color)
        varports = port.getPorts()
        if port.port.variable:
            im.Text(port.port.name)
            im.SameLine()
            if im.Button(f" + ##{port.portID}"):
                newPort = port.addVarPort()
                self.ng._portLookup[newPort.portID] = newPort
            im.SameLine()
            im.BeginDisabled(len(varports) == 1)
            if im.Button(f" - ##{port.portID}"):
                port.remVarPort()
                self.ng._portLookup.pop(varports[-1].portID)
                varports = varports[:-1]
            im.EndDisabled()

        for varIdx, varport in enumerate(varports):
            # Render the port
            isInput = isinstance(port, InPort)
            if isInput:
                imnodes.BeginInputAttribute(varport.portID)
            else:
                imnodes.BeginOutputAttribute(varport.portID)

            if port.port.variable:
                im.Text(f"{varIdx}")
            else:
                im.Text(port.port.name)

            if isInput:
                imnodes.EndInputAttribute()
            else:
                imnodes.EndOutputAttribute()
        imnodes.PopColorStyle()

    def _addNodePopup(self) -> None:
        if (im.IsKeyDown(im.ImKey.Space) and imnodes.IsEditorHovered() and not im.IsAnyItemHovered()
                and not im.IsMouseDown(im.MouseButton.Left)):

            im.OpenPopup(_ADD_NODE_PU)

        if not im.BeginPopup(_ADD_NODE_PU):
            return

        for nodeType in self.ng.nodeTypes():
            if im.Selectable(nodeType.NODETYPE):
                self.needToSave = True
                pos = im.GetMousePosOnOpeningCurrentPopup()
                self.ng.addNode(nodeType).pos = Vec(pos.x, pos.y)

        im.EndPopup()
