import tkinter as tk
from enum import IntEnum

from typing import Optional, List, Dict, Iterator

from .node import Node, IOPort, Link, _NodeLinkIter
from .node_graph import NodeGraph
from .utils import Vec


# region Helper Classes

class _PortIO(IntEnum):
    IN = 0
    OUT = 1


class _NodeRef:
    def __init__(self, node: Node, canvasID: int, nodeTag: str,
                 iPorts: List['_PortRef'] = None, oPorts: List['_PortRef'] = None, links: List['_LinkRef'] = None):
        self.node = node
        self.iPorts = [] if iPorts is None else iPorts
        self.oPorts = [] if oPorts is None else oPorts
        self.links = [] if links is None else links

        self.canvasID = canvasID
        self.nodeTag = nodeTag

    @property
    def pos(self) -> Vec:
        return self.node.pos

    @pos.setter
    def pos(self, v: Vec):
        self.node.pos = v


    def __iter__(self) -> _NodeLinkIter:
        return self.node.__iter__()

    def __str__(self):
        return f"PosNode({self.node}, pos: {self.node})"


class _PortRef:
    def __init__(self, canvasID, node: _NodeRef, idx: int, io: _PortIO, typeStr: str):
        self.canvasID = canvasID
        self.posNode = node
        self.idx = idx
        self.io = io
        self.typeStr = typeStr


class _LinkRef:
    def __init__(self, canvasID: int, parent: _NodeRef, child: _NodeRef, outPort: _PortRef, inPort: _PortRef, link: Link):
        self.canvasID = canvasID
        self.parent = parent
        self.child = child
        self.oPort = outPort
        self.iPort = inPort
        self.link = link


# endregion


# region Consts

PORT_VERT_OFFSET = 10
PORT_HORZ_OFFSET = 0

PORT_SIZE = 10
HALF_PORT = PORT_SIZE / 2

IO_HEIGHT = PORT_SIZE * 2

LINK_WIDTH = 4

PORT_TAG = 'port'
NODE_TAG = "node"
DEF_PORT_COLOR = "grey50"


# endregion

class TKNodeGraph(tk.Frame):
    def __init__(self, parent, nodeGraph: NodeGraph):
        super().__init__(parent)

        self.nodeGraph = nodeGraph

        self.portColors: Dict[str, str] = {}

        self.rowconfigure(0, weight=3)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self.nodeCanvas = tk.Canvas(self)
        self.nodeCanvas.grid(row=0, column=0, stick='nesw')

        infoPanel = tk.Frame(self)
        infoPanel.grid(row=1, column=0, stick='nesw')

        self._bindPortEvents()
        self._bindNodeEvents()

        self._draggingPort = False
        self._draggingNode = False
        self._dragStart = Vec()
        self._curDragCID = 0
        self._curNode = None
        self._curPortID = 0

        self._lowestNode = None

        # Node ID -> PosNode
        self._idToNode: Dict[int, _NodeRef] = {}
        # Node Canvas ID -> PosNode
        self._canvToNodeRef: Dict[int, _NodeRef] = {}

        # Port Canvas ID -> PortRef
        self._canvToPortRef: Dict[int, _PortRef] = {}

        # Link ID -> LinkRef
        self._idToLink: Dict[int, _LinkRef] = {}
        # Link Canvas ID -> LinkRef
        self._canvToLinkRef: Dict[int, _LinkRef] = {}

        # Do last?
        if len(self.nodeGraph) > 0:
            self.reloadGraph()

    # region Setup Funcs
    def _bindNodeEvents(self):
        self.nodeCanvas.tag_bind(NODE_TAG, "<Enter>", self._hoverNode)
        self.nodeCanvas.tag_bind(NODE_TAG, "<Leave>", self._unhoverNode)
        self.nodeCanvas.tag_bind(NODE_TAG, "<B1-Motion>", self._startNodeDrag)

    def _bindPortEvents(self):
        self.nodeCanvas.tag_bind(PORT_TAG, "<Enter>", self._hoverPortEvent)
        self.nodeCanvas.tag_bind(PORT_TAG, "<Leave>", self._unhoverPortEvent)
        self.nodeCanvas.tag_bind(PORT_TAG, "<B1-Motion>", self._startPortDrag)
        self.nodeCanvas.bind("<ButtonRelease-1>", self._releasedDrag)

    # endregion

    def reloadGraph(self):
        for node in self.nodeGraph:
            try:
                posNode = self._idToNode[node.nodeID]
                self._updateNode(posNode)
            except KeyError:
                self._makeNewNode(node)

        for node in self.nodeGraph:
            for link in node:
                try:
                    linkRef = self._idToLink[link.linkID]
                    self._updateLink(linkRef)
                except KeyError:
                    self._makeNewLink(link)


    def _current(self) -> int:
        return self.nodeCanvas.find_withtag(tk.CURRENT)[0]

    def setPortTypeColor(self, typeStr: str, color: str):
        self.portColors[typeStr] = color

    def setPos(self, n: Node, pos: Vec):
        self._idToNode[n.nodeID].pos = pos

    # region Hover Events
    def _hoverPortEvent(self, _):
        portID = self._current()
        self._hoverPort(portID)

    def _unhoverPortEvent(self, _):
        portID = self._current()
        self._unhoverPort(portID)

    def _hoverPort(self, portID):
        self.nodeCanvas.itemconfigure(portID, fill='white')

    def _unhoverPort(self, portID):
        color = self._getPortColor(portID)
        self.nodeCanvas.itemconfigure(portID, fill=color)

    def _hoverNode(self, _):
        c = self._current()
        self.nodeCanvas.itemconfigure(c, outline="white")

    def _unhoverNode(self, _):
        c = self._current()
        self.nodeCanvas.itemconfigure(c, outline="black")

    # endregion

    # region Drag Events
    def _startPortDrag(self, e):
        # TODO differentiate between draggin in/out port
        #   dragging from out ports allows multiple links
        #   dragging from in ports grabs the end a link, if it exists,
        #   since there can only be one link into in an input
        if not self._draggingPort:
            self._draggingPort = True
            portID = self._current()
            self._curPortID = portID

            self._dragStart = self._portCoords(portID)

            # TODO color
            self._curDragCID = self.nodeCanvas.create_line(self._dragStart.x, self._dragStart.y, e.x, e.y,
                                                           fill="grey50", width=LINK_WIDTH)
            self.nodeCanvas.lower(self._curDragCID, self._lowestNode)
        else:
            self.nodeCanvas.coords(self._curDragCID, self._dragStart.x, self._dragStart.y, e.x, e.y)

    def _startNodeDrag(self, e):
        if not self._draggingNode:
            self._draggingNode = True
            self._curDragCID = self._current()
            self._curNode = self._canvToNodeRef[self._curDragCID]
            self._dragStart = self._curNode.pos - Vec(e.x, e.y)

        self._curNode.pos = Vec(e.x, e.y) + self._dragStart
        self._updateNode(self._curNode)

        for link in self._curNode.links:
            self._updateLink(link)

    def _releaseLinkDrag(self):
        self._draggingPort = False
        c = self._current()
        fail = True
        try:
            portRef1 = self._canvToPortRef[c]
            portRef2 = self._canvToPortRef[self._curPortID]

            if c != self._curPortID and portRef1.io != portRef2.io:
                fail = False

                self.nodeCanvas.delete(self._curDragCID)

                if portRef1.io == _PortIO.IN:
                    child = portRef1.posNode.node
                    parent = portRef2.posNode.node

                    inIdx = portRef1.idx
                    outIdx = portRef2.idx
                else:
                    child = portRef2.posNode.node
                    parent = portRef1.posNode.node

                    inIdx = portRef2.idx
                    outIdx = portRef1.idx

                link, removed = self.nodeGraph.makeLink(parent, outIdx, child, inIdx)

                if removed is not None:
                    linkRef = self._idToLink[removed.linkID]
                    self.nodeCanvas.delete(linkRef.canvasID)

                self._makeNewLink(link)

        except KeyError:
            pass

        if fail:
            self.nodeCanvas.delete(self._curDragCID)

    def _releaseNodeDrag(self):
        self._draggingNode = False

    def _releasedDrag(self, _):
        if self._draggingPort:
            self._releaseLinkDrag()
        if self._draggingNode:
            self._releaseNodeDrag()

    # endregion

    # region Port Utils

    def _portCoords(self, portID: int) -> Vec:
        # noinspection PyTypeChecker
        c = self.nodeCanvas.coords(portID)

        x = (c[0] + c[2]) / 2
        y = (c[1] + c[3]) / 2
        # noinspection PyTypeChecker
        return Vec(x, y)

    def _getTypeColor(self, typeStr: str) -> str:
        try:
            return self.portColors[typeStr]
        except KeyError:
            pass

        self.portColors[typeStr] = DEF_PORT_COLOR
        return DEF_PORT_COLOR

    def _getPortColor(self, portID: int) -> str:
        return self._getTypeColor(self._canvToPortRef[portID].typeStr)

    def _drawPort(self, x, y, fill: str, nodeTag: str) -> int:
        a = x - HALF_PORT
        b = y - HALF_PORT
        return self.nodeCanvas.create_oval(a, b, a + PORT_SIZE, b + PORT_SIZE, fill=fill, tags=[PORT_TAG, nodeTag])

    # endregion

    def _updateNode(self, n: _NodeRef):
        # noinspection PyTypeChecker
        x, y, _, _ = self.nodeCanvas.coords(n.canvasID)
        self.nodeCanvas.move(n.nodeTag, n.pos.x - x, n.pos.y - y)

        for port in n.iPorts:
            color = self._getTypeColor(port.typeStr)
            self.nodeCanvas.itemconfigure(port.canvasID, fill=color)

        for port in n.oPorts:
            color = self._getTypeColor(port.typeStr)
            self.nodeCanvas.itemconfigure(port.canvasID, fill=color)


    def _makeNewNode(self, n: Node, pos: Optional[Vec] = None):
        minNodes = max(n.numInputs(), n.numOutputs())

        height = IO_HEIGHT * minNodes

        # TODO
        width = 40

        nodeTag = str(n)

        if pos is None:
            pos = n.pos

        canvasNodeID = self.nodeCanvas.create_rectangle(pos.x, pos.y, pos.x + width, pos.y + height, fill='grey60',
                                                        tags=[NODE_TAG, nodeTag])

        posNode = _NodeRef(n, canvasNodeID, nodeTag)

        self._idToNode[n.nodeID] = posNode
        self._canvToNodeRef[canvasNodeID] = posNode

        if self._lowestNode is None:
            self._lowestNode = canvasNodeID

        usableHeight = height - (2 * PORT_VERT_OFFSET)

        def drawPorts(iterator: Iterator[IOPort], num: int, x: int, y: int,
                      textOffset: int, textAnchor: str, portDir: _PortIO) -> List[_PortRef]:
            try:
                deltaY = usableHeight / (num - 1)
            except ZeroDivisionError:
                deltaY = 0
            textX = x + textOffset

            out = []

            for idx, p in enumerate(iterator):
                color = self._getTypeColor(p.typeStr)
                portID = self._drawPort(x, y, fill=color, nodeTag=nodeTag)
                # noinspection PyTypeChecker
                self.nodeCanvas.create_text(textX, y, text=p.name, anchor=textAnchor, tags=[nodeTag])
                y += deltaY

                portRef = _PortRef(portID, posNode, idx, portDir, p.typeStr)
                self._canvToPortRef[portID] = portRef
                out.append(portRef)

            return out

        # INPUTS
        if n.numInputs() > 0:
            iPortX = pos.x - PORT_HORZ_OFFSET
            iPortY = pos.y + PORT_VERT_OFFSET
            posNode.iPorts = drawPorts(n.inputs(), n.numInputs(), iPortX, iPortY, -PORT_SIZE,
                                 'e', _PortIO.IN)

        # OUTPUTS
        if n.numOutputs() > 0:
            oPortX = pos.x + width + PORT_HORZ_OFFSET
            oPortY = pos.y + PORT_VERT_OFFSET
            posNode.oPorts = drawPorts(n.outputs(), n.numOutputs(), oPortX, oPortY, PORT_SIZE,
                                 'w', _PortIO.OUT)

    def _makeNewLink(self, link: Link):
        parent = self._idToNode[link.parent.nodeID]
        child = self._idToNode[link.child.nodeID]

        outPort = parent.oPorts[link.outIdx]
        inPort = child.iPorts[link.inIdx]

        end1 = self._portCoords(outPort.canvasID)
        end2 = self._portCoords(inPort.canvasID)

        # TODO link color
        canvasID = self.nodeCanvas.create_line(end1.x, end1.y, end2.x, end2.y, fill="grey50", width=LINK_WIDTH)
        self.nodeCanvas.lower(canvasID, self._lowestNode)

        linkRef = _LinkRef(canvasID, parent, child, outPort, inPort, link)
        self._idToLink[link.linkID] = linkRef
        self._canvToLinkRef[canvasID] = linkRef

        parent.links.append(linkRef)
        child.links.append(linkRef)

    def _updateLink(self, linkRef: _LinkRef):
        end1 = self._portCoords(linkRef.oPort.canvasID)
        end2 = self._portCoords(linkRef.iPort.canvasID)

        self.nodeCanvas.coords(linkRef.canvasID, end1.x, end1.y, end2.x, end2.y)