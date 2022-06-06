import tkinter as tk
from tkinter import ttk
from enum import IntEnum

from typing import Optional, List, Dict

from .node import Node
from .ng_errors import NodeGraphError


class Vec:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


class PosNode:
    def __init__(self, node: Node, pos: Optional[Vec] = None):
        self.node = node
        self.pos = pos if pos is not None else Vec()


class NodeManager:
    def __init__(self):
        self.nodes: List[PosNode] = []
        self.portColors: Dict[str, str] = {}

    def addNode(self, n: Node, pos: Optional[Vec] = None):
        self.nodes.append(PosNode(n, pos))

    def setPortTypeColor(self, typeStr: str, color: str):
        self.portColors[typeStr] = color

    def __len__(self):
        return len(self.nodes)

    def __iter__(self):
        return self.nodes.__iter__()


PORT_VERT_OFFSET = 10
PORT_HORZ_OFFSET = 0

PORT_SIZE = 10
HALF_PORT = PORT_SIZE / 2

IO_HEIGHT = PORT_SIZE * 2

LINE_WIDTH = 4

PORT_TAG = 'port'
NODE_TAG = "node"
DEF_PORT_COLOR = "grey50"


class _PortIO(IntEnum):
    IN = 0
    OUT = 1


class _PortRef:
    def __init__(self, portID, node: Node, idx: int, io: _PortIO, color: str):
        self.portID = portID
        self.node = node
        self.idx = idx
        self.io = io
        self.color = color


class _LinkRef:
    def __init__(self, parent: Node, child: Node, outPort: _PortRef, inPort: _PortRef):
        self.parent = parent
        self.child = child
        self.oPort = outPort
        self.iPort = inPort


class _NodeRef:
    def __init__(self, node: Node):
        self.node = node


class TKNodeGraph(tk.Frame):
    def __init__(self, parent, nodeMan: NodeManager):
        super().__init__(parent)

        self.nodeMan = nodeMan

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
        self._curPortLineID = 0
        self._curPortID = 0

        self._lowestNode = None

        # Port Canvas ID -> PortRef
        self._portRefs: Dict[int, _PortRef] = {}
        # Node Canvas ID -> NodeRef
        self._nodeRefs: Dict[int, _NodeRef] = {}
        # Link Canvas ID -> LinkRef
        self._linkRefs: Dict[int, _LinkRef] = {}

        # Do last?
        if len(self.nodeMan) > 0:
            self.loadNodesFromManager()

    def _bindNodeEvents(self):
        self.nodeCanvas.tag_bind(NODE_TAG, "<Enter>", self._hoverNode)
        self.nodeCanvas.tag_bind(NODE_TAG, "<Leave>", self._unhoverNode)
        self.nodeCanvas.tag_bind(NODE_TAG, "<B1-Motion>", self._startNodeDrag)

    def _bindPortEvents(self):
        self.nodeCanvas.tag_bind(PORT_TAG, "<Enter>", self._hoverPortEvent)
        self.nodeCanvas.tag_bind(PORT_TAG, "<Leave>", self._unhoverPortEvent)
        self.nodeCanvas.tag_bind(PORT_TAG, "<B1-Motion>", self._startPortDrag)
        self.nodeCanvas.bind("<ButtonRelease-1>", self._releasedDrag)

    def loadNodesFromManager(self):
        for node in self.nodeMan:
            self._drawNode(node)

    def _drawPort(self, x, y, fill: str, nodeTag: str) -> int:
        a = x - HALF_PORT
        b = y - HALF_PORT
        return self.nodeCanvas.create_oval(a, b, a + PORT_SIZE, b + PORT_SIZE, fill=fill, tags=[PORT_TAG, nodeTag])

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

    def _portCoords(self, portID: int) -> Vec:
        # noinspection PyTypeChecker
        c = self.nodeCanvas.coords(portID)

        x = (c[0] + c[2]) / 2
        y = (c[1] + c[3]) / 2
        # noinspection PyTypeChecker
        return Vec(x, y)

    def _startPortDrag(self, e):
        if not self._draggingPort:
            self._draggingPort = True
            portID = self._current()
            self._curPortID = portID

            self._dragStart = self._portCoords(portID)

            # TODO color
            self._curPortLineID = self.nodeCanvas.create_line(self._dragStart.x, self._dragStart.y, e.x, e.y,
                                                              fill="grey50", width=LINE_WIDTH)
            self.nodeCanvas.lower(self._curPortLineID, self._lowestNode)
        else:
            self.nodeCanvas.coords(self._curPortLineID, self._dragStart.x, self._dragStart.y, e.x, e.y)

    def _startNodeDrag(self, e):
        if not self._draggingNode:
            self._draggingNode = True
            nodeID = self._current()

    def _current(self) -> int:
        return self.nodeCanvas.find_withtag(tk.CURRENT)[0]

    def _releaseLinkDrag(self):
        self._draggingPort = False
        c = self._current()
        fail = True
        try:
            ref = self._portRefs[c]
            ref2 = self._portRefs[self._curPortID]

            if c != self._curPortID and ref.io != ref2.io:
                fail = False

                loc = self._portCoords(c)
                self.nodeCanvas.coords(self._curPortLineID, self._dragStart.x, self._dragStart.y, loc.x, loc.y)

                # TODO make link
        except KeyError:
            pass

        if fail:
            self.nodeCanvas.delete(self._curPortLineID)

    def _releaseNodeDrag(self):
        # TODO
        self._draggingNode = False

    def _releasedDrag(self, _):
        if self._draggingPort:
            self._releaseLinkDrag()
        if self._draggingNode:
            self._releaseNodeDrag()

    def _getPortColor(self, portID: int) -> str:
        try:
            ref = self._portRefs[portID]
            return ref.color
        except KeyError:
            pass

        return DEF_PORT_COLOR

    def _drawNode(self, n: PosNode):
        minNodes = max(n.node.numInputs(), n.node.numOutputs())

        height = IO_HEIGHT * minNodes

        # TODO
        width = 40

        nodeTag = str(n.node)

        nodeID = self.nodeCanvas.create_rectangle(n.pos.x, n.pos.y, n.pos.x + width, n.pos.y + height, fill='grey60',
                                                  tags=[NODE_TAG, nodeTag])
        if self._lowestNode is None:
            self._lowestNode = nodeID

        usableHeight = height - (2 * PORT_VERT_OFFSET)

        # INPUTS
        if n.node.numInputs() > 0:
            iPortX = n.pos.x - PORT_HORZ_OFFSET
            iPortY = n.pos.y + PORT_VERT_OFFSET
            try:
                iPortDeltaY = usableHeight / (n.node.numInputs() - 1)
            except ZeroDivisionError:
                iPortDeltaY = 0
            iPortTextX = iPortX - PORT_SIZE

            for idx, x in enumerate(n.node.inputs()):
                # TODO color
                color = DEF_PORT_COLOR
                portID = self._drawPort(iPortX, iPortY, fill=color, nodeTag=nodeTag)
                self.nodeCanvas.create_text(iPortTextX, iPortY, text=x.name, anchor='e', tags=[nodeTag])
                iPortY += iPortDeltaY

                self._portRefs[portID] = _PortRef(portID, n.node, idx, _PortIO.IN, color)

        # OUTPUTS
        if n.node.numOutputs() > 0:
            oPortX = n.pos.x + width + PORT_HORZ_OFFSET
            oPortY = n.pos.y + PORT_VERT_OFFSET
            try:
                oPortDeltaY = usableHeight / (n.node.numOutputs() - 1)
            except ZeroDivisionError:
                oPortDeltaY = 0
            oPortTextX = oPortX + PORT_SIZE

            for idx, x in enumerate(n.node.outputs()):
                color = self.nodeMan.portColors[x.typeStr] if x.typeStr in self.nodeMan.portColors else DEF_PORT_COLOR
                portID = self._drawPort(oPortX, oPortY, fill=color, nodeTag=nodeTag)
                self.nodeCanvas.create_text(oPortTextX, oPortY, text=x.name, anchor='w', tags=[nodeTag])
                oPortY += oPortDeltaY

                self._portRefs[portID] = _PortRef(portID, n.node, idx, _PortIO.OUT, color)
