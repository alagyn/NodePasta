import tkinter as tk
from tkinter import ttk

from typing import Optional, List

from node import Node


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

    def addNode(self, n: Node, pos: Optional[Vec] = None):
        self.nodes.append(PosNode(n, pos))

    def __len__(self):
        return len(self.nodes)

    def __iter__(self):
        return self.nodes.__iter__()

PORT_VERT_OFFSET = 10
PORT_HORZ_OFFSET = 0

PORT_SIZE = 10
HALF_PORT = PORT_SIZE / 2

IO_HEIGHT = PORT_SIZE * 2

PORT_TAG = 'port'

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

        self.nodeCanvas.tag_bind(PORT_TAG, "<Enter>", self._hoverPort)
        self.nodeCanvas.tag_bind(PORT_TAG, "<Leave>", self._unhoverPort)

        # TODO
        self.portColors = {}

        # Do last?
        if len(self.nodeMan) > 0:
            self.loadNodesFromManager()

    def loadNodesFromManager(self):
        for node in self.nodeMan:
            self._drawNode(node)

    def _drawPort(self, x, y, fill: str):
        a = x - HALF_PORT
        b = y - HALF_PORT
        self.nodeCanvas.create_oval(a, b, a + PORT_SIZE, b + PORT_SIZE, fill=fill, tags=[PORT_TAG])

    def _hoverPort(self, x):
        portID = self.nodeCanvas.find_withtag(tk.CURRENT)[0]
        self.nodeCanvas.itemconfigure(portID, fill='white')

    def _unhoverPort(self, x):
        portID = self.nodeCanvas.find_withtag(tk.CURRENT)[0]
        self.nodeCanvas.itemconfigure(portID, fill='grey50')


    def _drawNode(self, n: PosNode):
        minNodes = max(len(n.node.inputs), len(n.node.outputs))

        height = IO_HEIGHT * minNodes

        # TODO
        width = 40

        self.nodeCanvas.create_rectangle(n.pos.x, n.pos.y, n.pos.x + width, n.pos.y + height, fill='grey60')

        usableHeight = height - (2 * PORT_VERT_OFFSET)

        if len(n.node.inputs) > 0:
            iPortX = n.pos.x - PORT_HORZ_OFFSET
            iPortY = n.pos.y + PORT_VERT_OFFSET
            iPortDeltaY = usableHeight / (len(n.node.inputs) - 1)
            iPortTextX = iPortX - PORT_SIZE
            self._drawPort(iPortX, iPortY, fill='green')

            for x in n.node.inputs:
                self._drawPort(iPortX, iPortY, fill='grey0')
                self.nodeCanvas.create_text(iPortTextX, iPortY, text=x.name, anchor='e')
                iPortY += iPortDeltaY


        if len(n.node.outputs) > 0:
            oPortX = n.pos.x + width + PORT_HORZ_OFFSET
            oPortY = n.pos.y + PORT_VERT_OFFSET
            oPortDeltaY = usableHeight / len(n.node.outputs)
            oPortTextX = oPortX + PORT_SIZE
            for x in n.node.outputs:
                self._drawPort(oPortX, oPortY, fill='grey40')
                self.nodeCanvas.create_text(oPortTextX, oPortY, text=x.name, anchor='w')
                oPortY += oPortDeltaY
