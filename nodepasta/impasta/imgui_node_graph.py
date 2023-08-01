from typing import Type, Dict

import imgui as im
import imgui.imnodes as imnodes

from nodepasta.nodegraph import NodeGraph
from nodepasta.node import Node
from nodepasta.ports import IOPort
from nodepasta.utils import Vec
from nodepasta.impasta.imgui_arg_handlers import ImArgHandler

# Add node popup ID
_ADD_NODE_PU = "Add Node"


class ImNodeGraph:

    def __init__(self, ng: NodeGraph) -> None:
        self.ng = ng
        imnodes.PushAttributeFlag(
            imnodes.AttributeFlags.EnableLinkDetachWithDragClick
        )

        io = imnodes.GetIO()
        io.SetLinkDetachedWithModifierClick(im.ImKey.Mod_Ctrl)
        io.SetEmulateThreeButtonMouseMod(im.ImKey.Mod_Alt)

        self._argHandlers: Dict[str, Type[ImArgHandler]] = {}

    def registerArgHandler(self, datatype: str, handler: Type[ImArgHandler]):
        self._argHandlers[datatype] = handler

    def render(self):
        imnodes.BeginNodeEditor()
        imnodes.MiniMap(0.2, imnodes.MiniMapLocation.TopRight)

        self._addNodePopup()

        for node in self.ng:
            self._renderNode(node)

        imnodes.EndNodeEditor()

        startPortId = im.IntRef()
        endPortId = im.IntRef()
        # This has to happen after EndNodeEditor
        if imnodes.IsLinkCreated(startPortId, endPortId):
            self.ng.makeLinkByID(startPortId.val, endPortId.val)

        linkId = im.IntRef()
        if imnodes.IsLinkDestroyed(linkId):
            self.ng.unlinkByID(linkId.val)

    def _renderNode(self, node: Node):
        if not imnodes.IsNodeSelected(node.nodeID):
            imnodes.SetNodeGridSpacePos(
                node.nodeID, im.Vec2(node.pos.x, node.pos.y)
            )
        else:
            pos = imnodes.GetNodeGridSpacePos(node.nodeID)
            node.pos.x = pos.x
            node.pos.y = pos.y

        imnodes.BeginNode(node.nodeID)

        imnodes.BeginNodeTitleBar()
        im.Text(node.NODETYPE)

        im.Dummy(im.Vec2(0, 5))

        for arg in node.args.values():
            self._argHandlers[arg.argType].render(arg)

        imnodes.EndNodeTitleBar()

        # TODO varports
        for iPort in node.getInputPorts():
            imnodes.BeginInputAttribute(iPort.portID)
            self._renderPort(iPort)
            imnodes.EndInputAttribute()

        for oPort in node.getOutputPorts():
            imnodes.BeginOutputAttribute(oPort.portID)
            self._renderPort(oPort)
            imnodes.EndOutputAttribute()

        imnodes.EndNode()

        for link in node:
            imnodes.Link(link.linkID, link.pPort.portID, link.cPort.portID)

    def _renderPort(self, port: IOPort):
        im.Text(port.port.name)

    def _addNodePopup(self) -> None:
        if (im.IsWindowFocused(im.FocusedFlags.RootAndChildWindows)
                and imnodes.IsEditorHovered() and not im.IsAnyItemHovered()
                and im.IsKeyDown(im.ImKey.A)
                and im.IsMouseReleased(im.MouseButton.Left)):
            im.OpenPopup(_ADD_NODE_PU)

        if not im.BeginPopup(_ADD_NODE_PU):
            return
        pos = im.GetMousePosOnOpeningCurrentPopup()

        for nodeType in self.ng.nodeTypes():
            if im.Selectable(nodeType.NODETYPE):
                self.ng.addNode(nodeType).pos = Vec(pos.x, pos.y)

        im.EndPopup()