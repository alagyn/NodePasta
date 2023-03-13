import imgui as im
import imgui.imnodes as imnodes

from nodepasta.nodegraph import NodeGraph
from nodepasta.node import Node
from nodepasta.ports import IOPort

class ImNodeGraph:
    def __init__(self, ng: NodeGraph) -> None:
        self.ng = ng
        imnodes.PushAttributeFlag(imnodes.AttributeFlags.EnableLinkDetachWithDragClick)

        io = imnodes.GetIO()
        io.SetLinkDetachedWithModifierClick(im.ImKey.Mod_Ctrl)
        io.SetEmulateThreeButtonMouseMod(im.ImKey.Mod_Alt)


    def render(self):
        imnodes.BeginNodeEditor()
        imnodes.MiniMap(0.2, imnodes.MiniMapLocation.TopRight)

        for node in self.ng:
            self._renderNode(node)

        imnodes.EndNodeEditor()

        # This has to happen after EndNodeEditor
        ret, linkData = imnodes.IsLinkCreated()
        if ret:
            self.ng.makeLinkByID(linkData[1], linkData[3])

        ret, linkID = imnodes.IsLinkDestroyed()
        if ret:
            self.ng.unlinkByID(linkID)

    def _renderNode(self, node: Node):
        if not imnodes.IsNodeSelected(node.nodeID):
            imnodes.SetNodeGridSpacePos(node.nodeID, im.Vec2(node.pos.x, node.pos.y))
        else:
            pos = imnodes.GetNodeGridSpacePos(node.nodeID)
            node.pos.x = pos.x
            node.pos.y = pos.y

        imnodes.BeginNode(node.nodeID)

        imnodes.BeginNodeTitleBar()
        im.Text(node.NODETYPE)
        imnodes.EndNodeTitleBar()

        # TODO args

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
