from typing import Type, Dict

import imgui as im
import imgui.imnodes as imnodes

from nodepasta.nodegraph import NodeGraph
from nodepasta.node import Node
from nodepasta.ports import IOPort
from nodepasta.utils import Vec
from nodepasta.impasta.imgui_arg_handlers import ImArgHandler
from nodepasta.errors import NodeTypeError

# Add node popup ID
_ADD_NODE_PU = "Add Node"

DEF_COLOR = im.ColorConvertFloat4ToU32(im.Vec4(1.0, 1.0, 1.0, 1.0))


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

            if self._hoveredNode is not None:
                im.Text(self._hoveredNode.docs())

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
        for iPort in node.getInputPorts():
            try:
                color = iPort.color
            except:
                try:
                    color = self._colors[iPort.port.typeStr]
                except KeyError:
                    color = DEF_COLOR
                iPort.color = color
            # Set the port color
            imnodes.PushColorStyle(imnodes.Col.Pin, color)
            # Render the port
            imnodes.BeginInputAttribute(iPort.portID)
            self._renderPort(iPort)
            imnodes.EndInputAttribute()
            imnodes.PopColorStyle()

        for oPort in node.getOutputPorts():
            # Set the port color
            try:
                color = oPort.color
            except:
                try:
                    color = self._colors[oPort.port.typeStr]
                except KeyError:
                    color = DEF_COLOR
                oPort.color = color
            imnodes.PushColorStyle(imnodes.Col.Pin, color)
            # Render the port
            imnodes.BeginOutputAttribute(oPort.portID)
            self._renderPort(oPort)
            imnodes.EndOutputAttribute()
            # Pop off the color
            imnodes.PopColorStyle()

        imnodes.EndNode()

        for link in node:
            imnodes.PushColorStyle(imnodes.Col.Link, link.pPort.color)
            imnodes.Link(link.linkID, link.pPort.portID, link.cPort.portID)
            imnodes.PopColorStyle()

    def _renderPort(self, port: IOPort):
        im.Text(port.port.name)

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
