import tkinter as tk
from enum import IntEnum

from typing import Optional, List, Dict, Iterator, Type

from nodepasta.node import Node, IOPort, Link, _NodeLinkIter
from nodepasta.node_graph import NodeGraph
from nodepasta.utils import Vec
from nodepasta.errors import NodeGraphError
from nodepasta.argtypes import NodeArgValue
from nodepasta.tk.tk_arg_handlers import TKArgHandler, DEF_HANDLERS, TKNotFoundHandler


# region Helper Classes

class _PortIO(IntEnum):
    IN = 0
    OUT = 1


class _NodeRef:
    def __init__(self, node: Node, canvasID: int, nodeTag: str):
        self.node = node
        self.iPorts = []
        self.oPorts = []
        self.iLinks: List[Optional[_LinkRef]] = [None] * node.numInputs()
        self.oLinks: List[List[_LinkRef]] = [[]] * node.numOutputs()
        self.args: Dict[str, NodeArgValue] = {}
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
    def __init__(self, canvasID: int, textCanvasID: int, node: _NodeRef, idx: int, io: _PortIO, typeStr: str):
        self.portCanvasID = canvasID
        self.nodeRef = node
        self.idx = idx
        self.io = io
        self.typeStr = typeStr
        self.textCanvasID = textCanvasID

    def __str__(self):
        return f'{self.nodeRef.node}:{self.io.name}:{self.idx}'


class _LinkRef:
    def __init__(self, canvasID: int, parent: _NodeRef, child: _NodeRef, outPort: _PortRef, inPort: _PortRef,
                 link: Link):
        self.canvasID = canvasID
        self.parent = parent
        self.child = child
        self.oPort = outPort
        self.iPort = inPort
        self.link = link


# endregion

class _TKNode(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)


# region Consts

PORT_VERT_OFFSET = 10
PORT_HORZ_OFFSET = 0
PORT_TEXT_OFFSET = 10

PORT_SIZE = 10
HALF_PORT = PORT_SIZE / 2
PORT_BLOCK_H_OFFSET = 10

IO_HEIGHT = PORT_SIZE * 2

LINK_WIDTH = 4

PORT_TAG = 'port'
PORT_BLOCK_COLOR = "grey70"
NODE_HVR_TAG = "node"
DEF_PORT_COLOR = "grey50"
LINK_COLOR = "grey70"

DIALOG_TAG = 'dialog'
DIALOG_HEIGHT = 150

# endregion


class TKNodeGraph(tk.Frame):
    def __init__(self, parent, nodeGraph: NodeGraph, registerDefArgHandlers: bool = True):
        super().__init__(parent)

        self.nodeGraph = nodeGraph

        self.portColors: Dict[str, str] = {}

        self.rowconfigure(0, weight=3)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        self._nodeCanvas = tk.Canvas(self)
        self._nodeCanvas.grid(row=0, column=0, stick='nesw')

        v_scroll = tk.Scrollbar(self, orient=tk.VERTICAL, command=self._nodeCanvas.yview)
        self._nodeCanvas.configure(yscrollcommand=v_scroll.set)
        v_scroll.grid(row=0, column=1, sticky='nse')

        h_scroll = tk.Scrollbar(self, orient=tk.HORIZONTAL, command=self._nodeCanvas.xview)
        self._nodeCanvas.configure(xscrollcommand=h_scroll.set)
        h_scroll.grid(row=1, column=0, sticky='ews')

        infoPanel = tk.LabelFrame(self, text="Info")
        infoPanel.grid(row=2, column=0, stick='nesw')

        self._infoVar = tk.StringVar()
        self._infoLabel = tk.Label(infoPanel, textvariable=self._infoVar)
        self._infoLabel.grid(row=0, column=0, sticky='nesw')

        self._bindPortEvents()
        self._bindNodeEvents()
        self._bindKeyEvents()

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

        if registerDefArgHandlers:
            self._argTypeHandlers: Dict[str, TKArgHandler] = DEF_HANDLERS
        else:
            self._argTypeHandlers: Dict[str, TKArgHandler] = {}

        # Do last?
        if len(self.nodeGraph) > 0:
            self.reloadGraph()

    # region Setup Funcs
    def _bindNodeEvents(self):
        self._nodeCanvas.tag_bind(NODE_HVR_TAG, "<Enter>", self._hoverNode)
        self._nodeCanvas.tag_bind(NODE_HVR_TAG, "<Leave>", self._unhoverNode)
        self._nodeCanvas.tag_bind(NODE_HVR_TAG, "<B1-Motion>", self._startNodeDrag)
        self._nodeCanvas.tag_bind(NODE_HVR_TAG, "<Control-ButtonPress-3>", self._deleteNode)

    def _bindPortEvents(self):
        self._nodeCanvas.tag_bind(PORT_TAG, "<Enter>", self._hoverPortEvent)
        self._nodeCanvas.tag_bind(PORT_TAG, "<Leave>", self._unhoverPortEvent)
        self._nodeCanvas.tag_bind(PORT_TAG, "<B1-Motion>", self._startPortDrag)
        self._nodeCanvas.bind("<ButtonRelease-1>", self._releasedDrag)

    def _bindKeyEvents(self):
        self._nodeCanvas.bind('<Control-ButtonPress-1>', self._addNewNodeDialog)
        # TODO self.bind_all('<Control-KeyPress-r>', self._resetPan)
        self._nodeCanvas.bind('<ButtonPress-3>', self._startPan)
        self._nodeCanvas.bind('<B3-Motion>', self._panCanvas)
        self.bind('<KeyPress-Escape>', self._cancel)

    # endregion

    def setInfoMessage(self, msg: str):
        self._infoLabel.configure(fg="black")
        self._infoVar.set(msg)

    def setErrorMessage(self, msg: str):
        self._infoLabel.configure(fg="red")
        self._infoVar.set(msg)

    def unloadArgs(self) -> Dict[int, Dict[str, any]]:
        # Node ID -> Dict[argName, value]
        out = {}

        for node in self._idToNode.values():
            args = {}
            for name, argVal in node.args.items():
                args[name] = argVal.get()
            out[node.node.nodeID] = args

        return out

    def reloadGraph(self):
        """
        Reloads the graph visuals and updates nodes
        :return: None
        """
        for node in self.nodeGraph:
            try:
                nodeRef = self._idToNode[node.nodeID]
                # Make sure that the ref gets updated if reloaded
                nodeRef.node = node
                self._updateNode(nodeRef)
            except KeyError:
                self._makeNewNode(node)

        for node in self.nodeGraph:
            for link in node:
                try:
                    linkRef = self._idToLink[link.linkID]
                    self._updateLink(linkRef)
                except KeyError:
                    self._makeNewLink(link)

    def reset(self):
        self._idToNode = {}
        self._idToLink = {}
        self._canvToNodeRef = {}
        self._canvToLinkRef = {}
        self._canvToPortRef = {}
        self._lowestNode = None
        self._nodeCanvas.delete('all')

    def _current(self) -> Optional[int]:
        try:
            return self._nodeCanvas.find_withtag(tk.CURRENT)[0]
        except IndexError:
            return None

    def setPortTypeColor(self, typeStr: str, color: str):
        self.portColors[typeStr] = color

    def setPos(self, n: Node, pos: Vec):
        self._idToNode[n.nodeID].pos = pos

    def _canvCoord(self, e) -> Vec:
        return Vec(self._nodeCanvas.canvasx(e.x), self._nodeCanvas.canvasy(e.y))

    # region Hover Events
    def _hoverPortEvent(self, _):
        portID = self._current()
        self._hoverPort(portID)

    def _unhoverPortEvent(self, _):
        portID = self._current()
        self._unhoverPort(portID)

    def _hoverPort(self, portID):
        self._nodeCanvas.itemconfigure(portID, fill='white')

    def _unhoverPort(self, portID):
        color = self._getPortColor(portID)
        self._nodeCanvas.itemconfigure(portID, fill=color)

    def _hoverNode(self, _):
        c = self._current()
        # TODO hover
        if c in self._canvToNodeRef:
            self._nodeCanvas.itemconfigure(c, outline="white")

    def _unhoverNode(self, _):
        c = self._current()
        # TODO unhover
        if c in self._canvToNodeRef:
            self._nodeCanvas.itemconfigure(c, outline="black")

    # endregion

    # region Drag Events
    def _startPan(self, e):
        self._nodeCanvas.scan_mark(e.x, e.y)

    def _panCanvas(self, e):
        if self._dragStart is None:
            return

        self._nodeCanvas.scan_dragto(e.x, e.y, 1)

    def _startPortDrag(self, e):
        canvPos = self._canvCoord(e)
        if not self._draggingPort:
            self._draggingPort = True
            portID = self._current()

            portRef = self._canvToPortRef[portID]

            self._dragStart = None

            if portRef.io == _PortIO.IN:
                link = portRef.nodeRef.iLinks[portRef.idx]
                if link is not None:
                    self._dragStart = self._portCoords(link.oPort.portCanvasID)
                    self._removeLink(link)
                    self._curPortID = link.oPort.portCanvasID

            if self._dragStart is None:
                self._dragStart = self._portCoords(portID)
                self._curPortID = portID

            self._curDragCID = self._nodeCanvas.create_line(self._dragStart.x, self._dragStart.y, canvPos.x, canvPos.y,
                                                            fill=LINK_COLOR, width=LINK_WIDTH)

            self._nodeCanvas.lower(self._curDragCID, self._lowestNode)
        else:
            self._nodeCanvas.coords(self._curDragCID, self._dragStart.x, self._dragStart.y, canvPos.x, canvPos.y)

    def _startNodeDrag(self, e):
        canvPos = self._canvCoord(e)
        if not self._draggingNode:
            self._draggingNode = True
            self._curDragCID = self._current()
            self._curNode = self._canvToNodeRef[self._curDragCID]
            self._dragStart = self._curNode.pos - canvPos

        self._curNode.pos = canvPos + self._dragStart
        self._updateNode(self._curNode)

        for link in self._curNode.iLinks:
            if link is not None:
                self._updateLink(link)
        for port in self._curNode.oLinks:
            for link in port:
                self._updateLink(link)

    def _releaseLinkDrag(self):
        self._draggingPort = False
        c = self._current()
        self._nodeCanvas.delete(self._curDragCID)
        try:
            portRef1 = self._canvToPortRef[c]
            portRef2 = self._canvToPortRef[self._curPortID]

            # TODO remove?
            self.setInfoMessage(f'{portRef1} -> {portRef2}')

            if c != self._curPortID and portRef1.io != portRef2.io:

                if portRef1.io == _PortIO.IN:
                    child = portRef1.nodeRef.node
                    parent = portRef2.nodeRef.node

                    inIdx = portRef1.idx
                    outIdx = portRef2.idx
                else:
                    child = portRef2.nodeRef.node
                    parent = portRef1.nodeRef.node

                    inIdx = portRef2.idx
                    outIdx = portRef1.idx

                try:
                    link, removed = self.nodeGraph.makeLink(parent, outIdx, child, inIdx)

                    if removed is not None:
                        linkRef = self._idToLink[removed.linkID]
                        self._nodeCanvas.delete(linkRef.canvasID)

                    self._makeNewLink(link)
                except NodeGraphError as err:
                    self.setErrorMessage(str(err))

        except KeyError:
            pass

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
        c = self._nodeCanvas.coords(portID)

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
        return self._nodeCanvas.create_oval(a, b, a + PORT_SIZE, b + PORT_SIZE, fill=fill, tags=[PORT_TAG, nodeTag])

    def _movePort(self, portCID, x: int, y: int):
        self._nodeCanvas.coords(portCID, x - HALF_PORT, y - HALF_PORT, x + HALF_PORT, y + HALF_PORT)

    # endregion

    def _updateNode(self, n: _NodeRef):
        # noinspection PyTypeChecker
        x, y = self._nodeCanvas.coords(n.canvasID)
        self._nodeCanvas.move(n.nodeTag, n.pos.x - x, n.pos.y - y)

        for port in n.iPorts:
            color = self._getTypeColor(port.typeStr)
            self._nodeCanvas.itemconfigure(port.portCanvasID, fill=color)

        for port in n.oPorts:
            color = self._getTypeColor(port.typeStr)
            self._nodeCanvas.itemconfigure(port.portCanvasID, fill=color)

    def _makeNewNode(self, n: Node, pos: Optional[Vec] = None):
        nodeTag = str(n)

        if pos is None:
            pos = n.pos
        else:
            n.pos = pos

        nodeFrame = tk.LabelFrame(self._nodeCanvas)
        tk.Label(nodeFrame, text=f'{n.NODETYPE}:{n.nodeID}').grid(row=0, column=0, sticky='nesw')
        nodeCanvasID = self._nodeCanvas.create_window(pos.x, pos.y, anchor='nw', window=nodeFrame,
                                                      tags=[NODE_HVR_TAG, nodeTag])

        nodeRef = _NodeRef(n, nodeCanvasID, nodeTag)
        self._idToNode[n.nodeID] = nodeRef

        for idx, arg in enumerate(n.args.values()):
            argFrame = tk.Frame(nodeFrame)
            try:
                argValue = self._argTypeHandlers[arg.argType].draw(argFrame, arg)
            except KeyError:
                argValue = TKNotFoundHandler.draw(argFrame, arg)
            argFrame.grid(row=idx + 1, column=0, sticky='nesw')
            nodeRef.args[arg.name] = argValue

        self._makePortBlock(nodeRef)

    def _drawPorts(self, iterator: Iterator[IOPort], nodeRef: _NodeRef, textTag: str, textAnchor: str,
                   portDir: _PortIO) -> List[_PortRef]:
        out = []

        for idx, p in enumerate(iterator):
            color = self._getTypeColor(p.typeStr)
            portID = self._drawPort(0, 0, fill=color, nodeTag=nodeRef.nodeTag)
            # noinspection PyTypeChecker
            textID = self._nodeCanvas.create_text(0, 0, text=p.name, anchor=textAnchor,
                                                  tags=[nodeRef.nodeTag, textTag])

            portRef = _PortRef(portID, textID, nodeRef, idx, portDir, p.typeStr)
            self._canvToPortRef[portID] = portRef
            out.append(portRef)

        return out

    def _makePortBlock(self, nodeRef: _NodeRef):
        if self._lowestNode is None:
            self._lowestNode = nodeRef.canvasID

        n = nodeRef.node

        textTag = f"{nodeRef.nodeTag}_text"

        nodeRef.iPorts = self._drawPorts(n.inputs(), nodeRef, textTag, "w", _PortIO.IN)
        nodeRef.oPorts = self._drawPorts(n.outputs(), nodeRef, textTag, "e", _PortIO.OUT)

        if len(nodeRef.iPorts) > 0:
            lowestPort = nodeRef.iPorts[0].portCanvasID
        else:
            lowestPort = nodeRef.oPorts[0].portCanvasID

        # Update to foce the canvas to recalc bounds
        self._nodeCanvas.update()
        argBounds = self._nodeCanvas.bbox(nodeRef.canvasID)
        argWidth = abs(argBounds[2] - argBounds[0])

        centerX = int((argBounds[0] + argBounds[2]) / 2)
        bottomY = max(argBounds[1], argBounds[3])

        ioBounds = self._nodeCanvas.bbox(textTag)
        ioWidth = max(abs(ioBounds[2] - ioBounds[0]) + PORT_BLOCK_H_OFFSET, argWidth)

        numPorts = n.numInputs() + n.numOutputs()
        ioHeight = numPorts * IO_HEIGHT

        halfWidth = int(ioWidth / 2)
        leftX = centerX - halfWidth
        rightX = centerX + halfWidth

        rectCanvasID = self._nodeCanvas.create_rectangle(leftX, bottomY, rightX,
                                                         bottomY + ioHeight, fill=PORT_BLOCK_COLOR,
                                                         tags=[NODE_HVR_TAG, nodeRef.nodeTag])
        self._canvToNodeRef[rectCanvasID] = nodeRef

        self._nodeCanvas.lower(rectCanvasID, lowestPort)

        usableHeight = ioHeight - (2 * PORT_VERT_OFFSET)

        try:
            deltaY = usableHeight / (numPorts - 1)
        except ZeroDivisionError:
            deltaY = 0

        curY = bottomY + PORT_VERT_OFFSET
        iPortX = leftX - PORT_HORZ_OFFSET
        oPortX = rightX + PORT_HORZ_OFFSET

        for p in nodeRef.oPorts:
            self._movePort(p.portCanvasID, oPortX, curY)
            self._nodeCanvas.coords(p.textCanvasID, oPortX - PORT_TEXT_OFFSET, curY)
            curY += deltaY

        for p in nodeRef.iPorts:
            self._movePort(p.portCanvasID, iPortX, curY)
            self._nodeCanvas.coords(p.textCanvasID, iPortX + PORT_TEXT_OFFSET, curY)
            curY += deltaY

    def _makeNewLink(self, link: Link):
        parent = self._idToNode[link.parent.nodeID]
        child = self._idToNode[link.child.nodeID]

        outPort = parent.oPorts[link.outIdx]
        inPort = child.iPorts[link.inIdx]

        end1 = self._portCoords(outPort.portCanvasID)
        end2 = self._portCoords(inPort.portCanvasID)

        canvasID = self._nodeCanvas.create_line(end1.x, end1.y, end2.x, end2.y, fill=LINK_COLOR, width=LINK_WIDTH)
        self._nodeCanvas.lower(canvasID, self._lowestNode)

        linkRef = _LinkRef(canvasID, parent, child, outPort, inPort, link)
        self._idToLink[link.linkID] = linkRef
        self._canvToLinkRef[canvasID] = linkRef

        parent.oLinks[link.outIdx].append(linkRef)
        child.iLinks[link.inIdx] = linkRef

    def _updateLink(self, linkRef: _LinkRef):
        end1 = self._portCoords(linkRef.oPort.portCanvasID)
        end2 = self._portCoords(linkRef.iPort.portCanvasID)

        self._nodeCanvas.coords(linkRef.canvasID, end1.x, end1.y, end2.x, end2.y)

    def _removeLink(self, linkRef: _LinkRef):
        self.nodeGraph.unlink(linkRef.link)
        linkRef.parent.oLinks[linkRef.oPort.idx].remove(linkRef)
        linkRef.child.iLinks[linkRef.iPort.idx] = None

        self._nodeCanvas.delete(linkRef.canvasID)
        del self._canvToLinkRef[linkRef.canvasID]

    def _addNewNode(self, nodeType: Type[Node], pos: Vec):
        self._nodeCanvas.delete(DIALOG_TAG)
        node = nodeType()
        node.pos = pos
        self.nodeGraph.addNode(node)
        self._makeNewNode(node)

    def _addNewNodeDialog(self, e):
        self._nodeCanvas.delete(DIALOG_TAG)
        pos = Vec(self._nodeCanvas.canvasx(e.x), self._nodeCanvas.canvasy(e.y))
        # TODO bind escape and click outside of frame to cancel

        mainDialogFrame = tk.LabelFrame(self._nodeCanvas)
        tk.Label(mainDialogFrame, text='Add Node').grid(row=0, column=0, columnspan=2, sticky='new')
        dialogCanvas = tk.Canvas(mainDialogFrame, height=DIALOG_HEIGHT, borderwidth=0)
        dialogCanvas.grid(row=1, column=0)

        sb = tk.Scrollbar(mainDialogFrame, orient=tk.VERTICAL, command=dialogCanvas.yview)
        sb.grid(row=1, column=1, sticky='nse')
        dialogCanvas.configure(yscrollcommand=sb.set)

        dialogFrame = tk.Frame(dialogCanvas)
        for idx, nodeType in enumerate(self.nodeGraph.nodeTypes()):
            btn = tk.Button(dialogFrame,
                      text=nodeType.__name__,
                      command=lambda x=nodeType: self._addNewNode(x, pos)
                      )
            btn.grid(row=idx + 1, column=0, sticky='nesw')
            btn.bind('<MouseWheel>', lambda event: dialogCanvas.yview_scroll(-event.delta, 'units'))

        dialogCanvas.create_window(0, 0, anchor='nw', window=dialogFrame)
        dialogCanvas.update()
        bbox = dialogCanvas.bbox('all')
        dialogCanvas.configure(scrollregion=bbox, width=abs(bbox[0]-bbox[2]))

        self._nodeCanvas.create_window(pos.x, pos.y, anchor='center', window=mainDialogFrame, tags=[DIALOG_TAG])

    def _cancel(self, e):
        print("ASDF")
        self._nodeCanvas.delete(DIALOG_TAG)

    def _deleteNode(self, e):
        cur = self._current()
        if cur is not None:
            try:
                node = self._canvToNodeRef[cur]
            except KeyError:
                return

            for link in node.iLinks:
                if link is not None:
                    self._removeLink(link)
            for port in node.oLinks:
                for link in port:
                    self._removeLink(link)

            self.nodeGraph.removeNode(node.node)
            self._nodeCanvas.delete(node.nodeTag)
