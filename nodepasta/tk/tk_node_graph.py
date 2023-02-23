import tkinter as tk
from enum import IntEnum

from typing import Optional, List, Dict, Iterator, Type, Tuple, Any, Sequence

from nodepasta.node import Node
from nodepasta.ports import IOPort, Link, _VarInPort, _VarOutPort, InPort, OutPort
from nodepasta.nodegraph import NodeGraph
from nodepasta.utils import Vec
from nodepasta.errors import NodeGraphError
from nodepasta.argtypes import NodeArgValue
from nodepasta.tk.tk_arg_handlers import TKArgHandler, DEF_HANDLERS, TKNotFoundHandler


# region Helper Classes

class _PortIO(IntEnum):
    IN = 0
    OUT = 1


class _NodeRef:
    def __init__(self, node: Node, nodeTag: str):
        self.node = node
        self.iPorts: List[_PortRef] = []
        self.oPorts: List[_PortRef] = []
        self.args: Dict[str, NodeArgValue] = {}
        self.argCanvasID = -1
        self.blockCanvasID = -1
        self.nodeTag = nodeTag
        self.numPorts = 0
        self.textTag = f'{nodeTag}_text'
        self.argWidth = 0
        self.argHeight = 0
        self.blockWidth = 0

    @property
    def pos(self) -> Vec:
        return self.node.pos

    @pos.setter
    def pos(self, v: Vec):
        self.node.pos = v

    def __iter__(self) -> Iterator[Link]:
        return iter(self.node)

    def __str__(self):
        return f"Ref({self.node}, pos: {self.node})"


class _VarPortRef:
    def __init__(self, varIdx: int, parent: '_PortRef', port: IOPort):
        self.canvasID = -1
        self.textCanvasID = -1
        if isinstance(port, _VarInPort):
            raise NodeGraphError("_VarPortRef.init()",
                                 "Cannot have a _VarPortRef reference a _VarInPort")
        if isinstance(port, _VarOutPort):
            raise NodeGraphError("_VarPortRef.init()",
                                 "Cannot have a _VarPortRef reference a _VarOutPort")
        if not isinstance(port, InPort) and not isinstance(port, OutPort):
            raise NodeGraphError("_VarPortRef.init()",
                                 "A _VarPortRef reference can only reference an InPort or OutPort")
        self.port = port
        self.parent = parent
        self.varIdx = varIdx
        self.links: List[Optional[_LinkRef]] = []

    def __str__(self):
        return f'VarPortRef {self.port}'


class _PortRef:
    def __init__(self, node: _NodeRef, port: IOPort, idx: int, io: _PortIO):
        self.nodeRef = node
        self.port = port
        self.textCanvasID = -1
        self.idx = idx
        self.varPorts: List[_VarPortRef] = []
        self.io = io
        self.btnWindowID = -1

    def __str__(self):
        return f'{self.nodeRef.node}:{self.io.name}:{self.idx}'


class _LinkRef:
    def __init__(self, canvasID: int, parent: _NodeRef, child: _NodeRef, outPort: _VarPortRef, inPort: _VarPortRef,
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

VAR_PORT_BTN_SIZE = 10


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
        self._canvToPortRef: Dict[int, _VarPortRef] = {}

        # Link ID -> LinkRef
        self._idToLink: Dict[int, _LinkRef] = {}
        # Link Canvas ID -> LinkRef
        self._canvToLinkRef: Dict[int, _LinkRef] = {}

        # PortID -> VarPortRef
        self._idToPortRef: Dict[int, _VarPortRef] = {}

        if registerDefArgHandlers:
            self._argTypeHandlers: Dict[str, TKArgHandler] = DEF_HANDLERS
        else:
            self._argTypeHandlers: Dict[str, TKArgHandler] = {}

        self._PIXEL = tk.PhotoImage(width=1, height=1)

        self._descrVar = tk.StringVar()
        descrFrame = tk.LabelFrame(self, text="Info")
        descrFrame.grid(row=0, column=1, sticky='nesw')

        tk.Label(descrFrame, textvariable=self._descrVar, anchor='w', justify='left', width=50, wraplength=350
                 ).grid(row=0, column=0, sticky='nesw')

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

    # region Info Funcs
    def setInfoMessage(self, msg: str):
        self._infoLabel.configure(fg="black")
        self._infoVar.set(msg)

    def setErrorMessage(self, msg: str):
        self._infoLabel.configure(fg="red")
        self._infoVar.set(msg)

    # endregion

    # region NodeGraph Funcs

    def unloadArgs(self) -> Dict[int, Dict[str, Any]]:
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
                    pVarPortRef = self._idToPortRef[link.pPort.portID]
                    cVarPortRef = self._idToPortRef[link.cPort.portID]
                    self._makeNewLink(link, pVarPortRef, cVarPortRef)

    def reset(self):
        self._idToNode = {}
        self._idToLink = {}
        self._canvToNodeRef = {}
        self._canvToLinkRef = {}
        self._canvToPortRef = {}
        self._lowestNode = None
        self._nodeCanvas.delete('all')

    # endregion

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
        if c is None:
            return
        try:
            nodeRef = self._canvToNodeRef[c]
            self._nodeCanvas.itemconfigure(c, outline="white")
            self._descrVar.set(nodeRef.node.docs())
        except KeyError:
            pass

    def _unhoverNode(self, _):
        c = self._current()
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
            if portID is None:
                return

            varPortRef = self._canvToPortRef[portID]

            self._dragStart = None

            if varPortRef.parent.io == _PortIO.IN:
                try:
                    link = varPortRef.links[0]
                except IndexError:
                    link = None

                if link is not None:
                    self._dragStart = self._portCoords(link.oPort.canvasID)
                    self._removeLink(link)
                    self._curPortID = link.oPort.canvasID

            if self._dragStart is None:
                self._dragStart = self._portCoords(portID)
                self._curPortID = portID

            self._curDragCID = self._nodeCanvas.create_line(self._dragStart.x, self._dragStart.y, canvPos.x, canvPos.y,
                                                            fill=LINK_COLOR, width=LINK_WIDTH)

            self._nodeCanvas.lower(self._curDragCID, self._lowestNode)
        else:
            if self._curDragCID is not None and self._dragStart is not None:
                self._nodeCanvas.coords(self._curDragCID, self._dragStart.x,
                                        self._dragStart.y, canvPos.x, canvPos.y)

    def _startNodeDrag(self, e):
        canvPos = self._canvCoord(e)
        if not self._draggingNode:
            self._draggingNode = True
            self._curDragCID = self._current()
            if self._curDragCID is None:
                return
            self._curNode = self._canvToNodeRef[self._curDragCID]
            self._dragStart = self._curNode.pos - canvPos

        if self._dragStart is None or self._curNode is None:
            return

        self._curNode.pos = canvPos + self._dragStart
        self._updateNode(self._curNode)

        for iport in self._curNode.iPorts:
            for varport in iport.varPorts:
                for link in varport.links:
                    if link is not None:
                        self._updateLink(link)
        for oport in self._curNode.oPorts:
            for varport in oport.varPorts:
                for link in varport.links:
                    if link is not None:
                        self._updateLink(link)

    def _releaseLinkDrag(self):
        self._draggingPort = False
        c = self._current()
        if self._curDragCID is not None:
            self._nodeCanvas.delete(self._curDragCID)
        if c is None:
            return

        try:
            varportRef1 = self._canvToPortRef[c]
            varportRef2 = self._canvToPortRef[self._curPortID]

            portRef1 = varportRef1.parent
            portRef2 = varportRef2.parent

            # TODO remove?
            self.setInfoMessage(f'{varportRef1} -> {varportRef2}')

            if c != self._curPortID and portRef1.io != portRef2.io:
                if portRef1.io == _PortIO.IN:
                    childRef = varportRef1
                    parentRef = varportRef2

                else:
                    childRef = varportRef2
                    parentRef = varportRef1

                try:
                    link, removed = self.nodeGraph.makeLink(parentRef.port, childRef.port)

                    if removed is not None:
                        linkRef = self._idToLink[removed.linkID]
                        self._nodeCanvas.delete(linkRef.canvasID)

                    self._makeNewLink(link, parentRef, childRef)
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

        x = int(c[0] + c[2]) // 2
        y = int(c[1] + c[3]) // 2
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
        return self._getTypeColor(self._canvToPortRef[portID].port.port.typeStr)

    def _drawPort(self, x, y, fill: str, nodeTag: str) -> int:
        a = x - HALF_PORT
        b = y - HALF_PORT
        return self._nodeCanvas.create_oval(a, b, a + PORT_SIZE, b + PORT_SIZE, fill=fill, tags=[PORT_TAG, nodeTag])

    def _movePort(self, portCID, x: int, y: int):
        self._nodeCanvas.coords(portCID, x - HALF_PORT, y - HALF_PORT, x + HALF_PORT, y + HALF_PORT)

    # endregion

    def _updateNode(self, n: _NodeRef):
        # noinspection PyTypeChecker
        x, y = self._nodeCanvas.coords(n.argCanvasID)
        self._nodeCanvas.move(n.nodeTag, n.pos.x - x, n.pos.y - y)

        self._arrangePortBlock(n)

        for portRef in n.iPorts:
            for varport in portRef.varPorts:
                color = self._getTypeColor(portRef.port.port.typeStr)
                self._nodeCanvas.itemconfigure(varport.canvasID, fill=color)

        for portRef in n.oPorts:
            for varport in portRef.varPorts:
                color = self._getTypeColor(portRef.port.port.typeStr)
                self._nodeCanvas.itemconfigure(varport.canvasID, fill=color)

    def _makeNewNode(self, n: Node, pos: Optional[Vec] = None):
        nodeTag = str(n)

        if pos is None:
            pos = n.pos
        else:
            n.pos = pos

        nodeFrame = tk.LabelFrame(self._nodeCanvas)
        tk.Label(nodeFrame, text=f'{n.NODETYPE}:{n.nodeID}').grid(row=0, column=0, sticky='nesw')
        argCanvasID = self._nodeCanvas.create_window(pos.x, pos.y, anchor='nw', window=nodeFrame,
                                                     tags=[NODE_HVR_TAG, nodeTag])

        nodeRef = _NodeRef(n, nodeTag)
        nodeRef.argCanvasID = argCanvasID

        self._idToNode[n.nodeID] = nodeRef

        for idx, arg in enumerate(n.args.values()):
            argFrame = tk.Frame(nodeFrame)
            try:
                argValue = self._argTypeHandlers[arg.argType].draw(argFrame, arg)
            except KeyError:
                argValue = TKNotFoundHandler.draw(argFrame, arg)
            argFrame.grid(row=idx + 1, column=0, sticky='nesw')
            nodeRef.args[arg.name] = argValue

        self._nodeCanvas.update()
        bounds = self._nodeCanvas.bbox(argCanvasID)
        nodeRef.argWidth = max(nodeRef.argWidth, abs(bounds[2] - bounds[0]))
        nodeRef.argHeight = max(nodeRef.argHeight, abs(bounds[3] - bounds[1]))

        self._makePortBlock(nodeRef)

    def _makeNewVarPort(self, varPortRef: _VarPortRef):
        nodeRef = varPortRef.parent.nodeRef

        textAnchor = 'w' if varPortRef.parent.io == _PortIO.IN else 'e'
        color = self._getTypeColor(varPortRef.parent.port.port.typeStr)

        portCanvID = self._drawPort(0, 0, fill=color, nodeTag=nodeRef.nodeTag)
        if varPortRef.parent.port.port.variable:
            text = varPortRef.varIdx
        else:
            text = varPortRef.parent.port.port.name

        textID = self._nodeCanvas.create_text(0, 0, text=text, anchor=textAnchor,
                                              tags=[nodeRef.nodeTag, nodeRef.textTag])

        self._nodeCanvas.update()
        bounds = self._nodeCanvas.bbox(textID)
        nodeRef.blockWidth = max(nodeRef.blockWidth, abs(bounds[2] - bounds[0]))

        varPortRef.canvasID = portCanvID
        varPortRef.textCanvasID = textID
        self._canvToPortRef[portCanvID] = varPortRef
        self._idToPortRef[varPortRef.port.portID] = varPortRef

    def _drawPorts(self, ports: Sequence[IOPort], nodeRef: _NodeRef, textAnchor: str,
                   portDir: _PortIO) -> Tuple[List[_PortRef], int, int]:
        out = []
        pcount = 0
        vpcount = 0
        for idx, p in enumerate(ports):
            vp = []
            portRef = _PortRef(nodeRef, p, idx, portDir)
            pcount += 1
            for varIdx, varport in enumerate(p.getPorts()):
                varPortRef = _VarPortRef(varIdx, portRef, varport)
                self._makeNewVarPort(varPortRef)
                vp.append(varPortRef)
                if p.port.variable:
                    vpcount += 1
            portRef.varPorts = vp
            out.append(portRef)
            if p.port.variable:
                portRef.textCanvasID = self._nodeCanvas.create_text(0, 0, text=p.port.name, anchor=textAnchor,  # type: ignore
                                                                    tags=[nodeRef.nodeTag, nodeRef.textTag])

        return out, pcount, vpcount

    def _addVarPort(self, portref: _PortRef):
        if not portref.port.port.variable:
            raise NodeGraphError("TKNodeGraph._addVarPort()",
                                 "DEV: Cannot add varport to non variable port")

        nextNum = len(portref.port.getPorts())
        varPort = portref.port.addVarPort()
        varPortRef = _VarPortRef(nextNum, portref, varPort)

        portref.nodeRef.numPorts += 1
        portref.varPorts.append(varPortRef)
        self._makeNewVarPort(varPortRef)
        self._updateNode(portref.nodeRef)

    def _remVarPort(self, portref: _PortRef):
        if not portref.port.port.variable:
            raise NodeGraphError("TKNodeGraph._remVarPort()",
                                 "DEV: Cannot rem varport on non variable port")
        if len(portref.port.getPorts()) > 1:
            for link in portref.varPorts[-1].links:
                if link is not None:
                    self._removeLink(link)
            portref.port.remVarPort()
            portref.nodeRef.numPorts -= 1
            varport = portref.varPorts.pop()
            self._nodeCanvas.delete(varport.textCanvasID, varport.canvasID)

            del self._canvToPortRef[varport.canvasID]
            del self._idToPortRef[varport.port.portID]

            self._updateNode(portref.nodeRef)

    def _makeVarBtns(self, port: _PortRef, x, y, tag):

        btnFrame = tk.Frame(self._nodeCanvas)

        addBtn = tk.Button(btnFrame, text="+", command=lambda e=port: self._addVarPort(e),
                           image=self._PIXEL,
                           compound='center',
                           padx=0, pady=0,
                           width=VAR_PORT_BTN_SIZE, height=VAR_PORT_BTN_SIZE)
        addBtn.grid(row=0, column=0,
                    ipadx=0, ipady=0,
                    )

        remBtn = tk.Button(btnFrame, text='-', command=lambda e=port: self._remVarPort(e),
                           image=self._PIXEL, compound='center',
                           padx=0, pady=0,
                           width=VAR_PORT_BTN_SIZE, height=VAR_PORT_BTN_SIZE)

        remBtn.grid(row=0, column=1)

        port.btnWindowID = self._nodeCanvas.create_window(x, y, window=btnFrame, anchor="w",
                                                          tags=[tag])

    def _makePortBlock(self, nodeRef: _NodeRef):
        if self._lowestNode is None:
            self._lowestNode = nodeRef.argCanvasID

        n = nodeRef.node

        nodeRef.iPorts, icnt, ivpcnt = self._drawPorts(n.inputs, nodeRef, "w", _PortIO.IN)
        nodeRef.oPorts, ocnt, ovpcnt = self._drawPorts(n.outputs, nodeRef, "e", _PortIO.OUT)

        if len(nodeRef.iPorts) > 0:
            lowestPort = nodeRef.iPorts[0].varPorts[0].canvasID
        else:
            lowestPort = nodeRef.oPorts[0].varPorts[0].canvasID

        numPorts = icnt + ivpcnt + ocnt + ovpcnt
        nodeRef.numPorts = numPorts

        rectCanvasID = self._nodeCanvas.create_rectangle(0, 0, 1,
                                                         1, fill=PORT_BLOCK_COLOR,
                                                         tags=[NODE_HVR_TAG, nodeRef.nodeTag])
        nodeRef.blockCanvasID = rectCanvasID
        self._canvToNodeRef[rectCanvasID] = nodeRef

        self._nodeCanvas.lower(rectCanvasID, lowestPort)

        self._arrangePortBlock(nodeRef)

    def _arrangePortBlock(self, nodeRef: _NodeRef):

        centerX = int(nodeRef.node.pos.x + (nodeRef.argWidth / 2))
        bottomY = int(nodeRef.node.pos.y + nodeRef.argHeight)

        ioWidth = max(nodeRef.argWidth, nodeRef.blockWidth + PORT_BLOCK_H_OFFSET)

        halfWidth = int(ioWidth / 2)
        leftX = centerX - halfWidth
        rightX = centerX + halfWidth
        ioHeight = nodeRef.numPorts * IO_HEIGHT

        self._nodeCanvas.coords(nodeRef.blockCanvasID, leftX, bottomY, rightX, bottomY + ioHeight)

        usableHeight = ioHeight - (2 * PORT_VERT_OFFSET)

        try:
            deltaY = usableHeight / (nodeRef.numPorts - 1)
        except ZeroDivisionError:
            deltaY = 0

        curY = bottomY + PORT_VERT_OFFSET
        iPortX = leftX - PORT_HORZ_OFFSET
        oPortX = rightX + PORT_HORZ_OFFSET

        def _align(ports: List[_PortRef], x, textOffset):
            nonlocal curY
            for p in ports:
                if p.port.port.variable:
                    self._nodeCanvas.coords(p.textCanvasID, x + textOffset, curY)
                    bounds = self._nodeCanvas.bbox(p.textCanvasID)
                    # TOFIX output port btn location
                    btnX = max(bounds[0], bounds[2]) + 10
                    if p.btnWindowID == -1:
                        self._makeVarBtns(p, btnX, curY, nodeRef.nodeTag)
                    else:
                        self._nodeCanvas.coords(p.btnWindowID, btnX, curY)
                    curY += deltaY
                for vp in p.varPorts:
                    self._movePort(vp.canvasID, x, int(curY))
                    self._nodeCanvas.coords(vp.textCanvasID, x + textOffset, curY)
                    curY += deltaY

        _align(nodeRef.oPorts, oPortX, -PORT_TEXT_OFFSET)
        _align(nodeRef.iPorts, iPortX, PORT_TEXT_OFFSET)

    def _makeNewLink(self, link: Link, pVarPortRef: _VarPortRef, cVarPortRef: _VarPortRef):
        parent = self._idToNode[link.pPort.node.nodeID]
        child = self._idToNode[link.cPort.node.nodeID]

        end1 = self._portCoords(pVarPortRef.canvasID)
        end2 = self._portCoords(cVarPortRef.canvasID)

        canvasID = self._nodeCanvas.create_line(
            end1.x, end1.y, end2.x, end2.y, fill=LINK_COLOR, width=LINK_WIDTH)
        self._nodeCanvas.lower(canvasID, self._lowestNode)

        linkRef = _LinkRef(canvasID, parent, child, pVarPortRef, cVarPortRef, link)
        self._idToLink[link.linkID] = linkRef
        self._canvToLinkRef[canvasID] = linkRef

        pVarPortRef.links.append(linkRef)
        try:
            cVarPortRef.links[0] = linkRef
        except IndexError:
            cVarPortRef.links.append(linkRef)

    def _updateLink(self, linkRef: _LinkRef):
        end1 = self._portCoords(linkRef.oPort.canvasID)
        end2 = self._portCoords(linkRef.iPort.canvasID)

        self._nodeCanvas.coords(linkRef.canvasID, end1.x, end1.y, end2.x, end2.y)

    def _removeLink(self, linkRef: _LinkRef):
        self.nodeGraph.unlink(linkRef.link)
        linkRef.oPort.links.remove(linkRef)
        linkRef.iPort.links[0] = None

        self._nodeCanvas.delete(linkRef.canvasID)
        del self._canvToLinkRef[linkRef.canvasID]

    def _addNewNode(self, nodeType: Type[Node], pos: Vec):
        self._nodeCanvas.delete(DIALOG_TAG)
        node = self.nodeGraph.addNode(nodeType)
        node.pos = pos
        self._makeNewNode(node)

    def _addNewNodeDialog(self, e):
        self._nodeCanvas.delete(DIALOG_TAG)
        pos = Vec(self._nodeCanvas.canvasx(e.x), self._nodeCanvas.canvasy(e.y))
        # TODO bind click outside of frame to cancel

        mainDialogFrame = tk.LabelFrame(self._nodeCanvas)
        tk.Label(mainDialogFrame, text='Add Node').grid(row=0, column=0, columnspan=2, sticky='new')
        dialogCanvas = tk.Canvas(mainDialogFrame, height=DIALOG_HEIGHT, borderwidth=0)
        dialogCanvas.grid(row=1, column=0)

        sb = tk.Scrollbar(mainDialogFrame, orient=tk.VERTICAL, command=dialogCanvas.yview)
        sb.grid(row=1, column=1, sticky='nse')
        dialogCanvas.configure(yscrollcommand=sb.set, yscrollincrement=0.5)

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
        dialogCanvas.configure(scrollregion=bbox, width=abs(bbox[0] - bbox[2]))

        self._nodeCanvas.create_window(pos.x, pos.y, anchor='center',
                                       window=mainDialogFrame, tags=[DIALOG_TAG])

    def _cancel(self, _):
        self._nodeCanvas.delete(DIALOG_TAG)

    def _deleteNode(self, _):
        cur = self._current()
        if cur is not None:
            try:
                node = self._canvToNodeRef[cur]
            except KeyError:
                return

            for port in node.iPorts:
                for varport in port.varPorts:
                    for link in varport.links:
                        if link is not None:
                            self._removeLink(link)
            for port in node.oPorts:
                for varport in port.varPorts:
                    for link in varport.links:
                        if link is not None:
                            self._removeLink(link)

            self.nodeGraph.removeNode(node.node)
            self._nodeCanvas.delete(node.nodeTag)
