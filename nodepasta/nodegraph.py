from collections import deque
from typing import Dict, List, Set, Iterator, Tuple, Optional, Type, Deque, Any

import json

from .node import Node, Link, NODE_ERR_CN
from .errors import ExecutionError, NodeGraphError, NodeDefError, NodeTypeError
from .utils import Vec
from .ports import IOPort
from .id_manager import IDManager

_NODES = 'nodes'
_LINKS = 'links'
_POS = 'pos'

_CLASS = 'class'
_ARGS = 'args'
_IN_VAR_PORTS = 'inVarPorts'
_OUT_VAR_PORTS = 'outVarPorts'


class NodeGraph:
    def __init__(self):
        # NodeID -> Node
        self._nodeLookup: Dict[int, Node] = {}
        self._portLookup: Dict[int, IOPort] = {}
        self._linkIDLookup: Dict[int, Link] = {}
        self._linkLookup: Dict[Tuple[int, int], Link] = {}

        self._traversal: Optional[List[Node]] = None

        self._nodeTypes: Dict[str, Type[Node]] = {}
        self._filename = ""
        self._idManager = IDManager()

        self.datamap: Dict[str, Any] = {}

    def __len__(self) -> int:
        return len(self._nodeLookup)

    def __iter__(self) -> Iterator[Node]:
        return self._nodeLookup.values().__iter__()

    def nodeTypes(self) -> Iterator[Type[Node]]:
        return sorted(self._nodeTypes.values(), key=lambda e: e.__name__).__iter__()

    def setupNodes(self):
        for node in self:
            node.init()
        for node in self:
            node.setup()

    def _loadFromJSON(self, jGraph):
        self._idManager.reset()
        nodeList = []

        if _NODES not in jGraph or len(jGraph[_NODES]) == 0:
            raise NodeGraphError("NodeGraph.loadFromFile()", f"No nodes defined in file")

        if _LINKS not in jGraph:
            raise NodeGraphError("NodeGraph._loadFromJSON()",
                                 f"Cannot load file, links not defined ")

        for idx, n in enumerate(jGraph[_NODES]):
            try:
                nodeClass = n[_CLASS]
            except KeyError:
                raise NodeGraphError("NodeGraph._loadFromJSON()",
                                     f"Node #{idx}, no class was defined")

            try:
                args = n[_ARGS]
            except KeyError:
                raise NodeGraphError("NodeGraph._loadFromJSON()",
                                     f"Node #{idx}, no args were defined")

            try:
                pos = n[_POS]
                if len(pos) != 2:
                    raise NodeGraphError(f'NodeGraph._loadFromJSON()',
                                         f'Node #{idx}, invalid pos length')
            except KeyError:
                raise NodeGraphError(f"NodeGraph._loadFromJSON()",
                                     f"Node #{idx}, no pos was defined")

            try:
                nodeType = self._nodeTypes[nodeClass]
            except KeyError:
                raise NodeGraphError(f'NodeGraph._loadFromJSON()',
                                     f'Node #{idx}, class type "{nodeClass}" not registered')

            try:
                inVarPorts = n[_IN_VAR_PORTS]
            except KeyError:
                raise NodeGraphError(f"NodeGraph._loadFromJSON()",
                                     f"Node #{idx}, varPorts field missing")

            try:
                outVarPorts = n[_OUT_VAR_PORTS]
            except KeyError:
                raise NodeGraphError(f"NodeGraph._loadFromJSON()",
                                     f"Node #{idx}, varPorts field missing")

            newNode = nodeType()
            newNode._init(self._idManager, inVarPorts, outVarPorts)
            newNode.loadArgs(args)
            newNode.pos = Vec(pos[0], pos[1])
            nodeList.append(newNode)
            self._addNode(newNode)

        for idx, link in enumerate(jGraph[_LINKS]):
            if len(link) != 2:
                raise NodeGraphError(f'NodeGraph._loadFromJSON()', f'Link #{idx}, invalid length')
            pPortId = link[0]
            cPortId = link[1]
            pPort = self._portLookup[pPortId]
            cPort = self._portLookup[cPortId]

            self.makeLink(pPort, cPort)

    def loadFromJSON(self, jGraph):
        """
        Clears the current graph and lodds the graph from a json object
        :param jGraph: The JSON dict-like object
        :return: None
        """
        self._nodeLookup = {}
        self._traversal = None
        try:
            self._loadFromJSON(jGraph)
        except:
            self._nodeLookup = {}
            self._traversal = None
            raise

    def loadFromFile(self, filename: str):
        """
        Clears the current graph and tries to load from the file
        :param filename: The graph filename
        :return: None
        """
        self._nodeLookup = {}
        self._traversal = None
        self._filename = filename
        try:
            with open(filename, mode='r') as f:
                jGraph = json.load(f)
        except json.JSONDecodeError as err:
            raise NodeGraphError("NodeGraph.loadFromFile()", f"Cannot load file, JSON Error: {err}")

        self.loadFromJSON(jGraph)
        self.genTraversal()

    def loadArgs(self, args: Dict[int, Dict[str, Any]]):
        for nodeID, arg in args.items():
            try:
                node = self._nodeLookup[nodeID]
            except KeyError:
                raise NodeGraphError('NodeGraph.loadArgs()',
                                     f"Cannot load args for node ID: {nodeID}. ID not in graph")

            node.loadArgs(arg)

    def registerNodeClass(self, nodeType: Type[Node]):
        if nodeType.NODETYPE == NODE_ERR_CN:
            raise NodeDefError(
                f"Node.init()", f"Node class {nodeType.__name__}, NODETYPE class variable not set")
        try:
            x = self._nodeTypes[nodeType.NODETYPE]
            if x != nodeType:
                raise NodeGraphError(f'NodeGraph.registerNodeClass()', f'Node Type "{nodeType.NODETYPE}" '
                                                                       f'already defined as {x.__name__}, cannot redefine as {nodeType.__name__}')
            return
        except KeyError:
            pass

        self._nodeTypes[nodeType.NODETYPE] = nodeType

    def getJSON(self) -> Dict[str, Any]:
        nodeList: List[Node] = [None] * len(self._nodeLookup)  # type: ignore

        # Node IDs don't matter and can be regenerated when the graph is reloaded
        # Port IDs however need to be rebased to zero and need to be constructed in
        # the exact same order every time
        rebasePortLookup = {}

        for idx, node in enumerate(self._nodeLookup.values()):
            nodeList[idx] = node
            for ip in node.getInputPorts():
                rebasePortLookup[ip.portID] = len(rebasePortLookup)
            for op in node.getOutputPorts():
                rebasePortLookup[op.portID] = len(rebasePortLookup)

        nodeJList = []
        linkJList = []

        for node in nodeList:

            nodeJList.append({
                _CLASS: node.NODETYPE,
                _ARGS: node.unloadArgs(),
                _POS: [node.pos.x, node.pos.y],
                _IN_VAR_PORTS: [len(x.getPorts()) for x in node.inputs],
                _OUT_VAR_PORTS: [len(x.getPorts()) for x in node.outputs]
            })

            for link in node:
                linkJList.append(
                    [rebasePortLookup[link.pPort.portID], rebasePortLookup[link.cPort.portID]]
                )

        out = {
            _NODES: nodeJList,
            _LINKS: linkJList
        }

        return out

    def saveToFile(self, filename: str):
        out = self.getJSON()
        with open(filename, mode='w') as f:
            json.dump(out, f, indent=2)

    def _addNode(self, node: Node):
        if node.nodeID == -1:
            node.nodeID = self._idManager.newNode()
            node.datamap._datamap = self.datamap  # type: ignore
            self._nodeLookup[node.nodeID] = node
            self._portLookup.update({
                x.portID: x for x in node.getInputPorts()
            })
            self._portLookup.update({
                x.portID: x for x in node.getOutputPorts()
            })
        else:
            raise NodeGraphError('NodeGraph.addNodes()',
                                 f"Cannot add node {node}, it already belongs to a node graph")
        self._traversal = None

    def addNode(self, nodetype: Type[Node]) -> Node:
        node = nodetype()
        node._init(self._idManager)
        self._addNode(node)
        return node

    def makeLinkByID(self, pPortID: int, cPortID: int):
        print(f"Linking {pPortID} -> {cPortID}")
        pPort = self._portLookup[pPortID]
        cPort = self._portLookup[cPortID]
        link, _ = self.makeLink(pPort, cPort)
        print(f'Linked: {link.linkID}')

    def makeLink(self, pPort: IOPort, cPort: IOPort) -> Tuple[Link, Optional[Link]]:
        """
        Makes a new link.
        :param parent: The parent node
        :param child: The child node
        :param addr: The address of the ports
        :return: The new link and an old link that was replaced, if it exists, else None
        """
        if pPort.node.nodeID not in self._nodeLookup:
            raise NodeGraphError(f'NodeGraph.makeLink()', f'Cannot make link, '
                                                          f'parent not in this graph: "{str(pPort.node)}"')
        if cPort.node.nodeID not in self._nodeLookup:
            raise NodeGraphError(f'NodeGraph.makeLink()', f'Cannot make link, '
                                                          f'child not in this graph: "{str(cPort.node)}"')
        if cPort.node.nodeID == pPort.node.nodeID:
            raise NodeGraphError('NodeGraph.makeLink()',
                                 f'Cannot make link, parent == child: {pPort.node} == {cPort.node}')

        # Check the typing on the inport
        if not cPort.allowAny and pPort.port.typeStr != cPort.port.typeStr:
            raise NodeTypeError(
                f"Node.addChild()", f"{pPort.node} -> {cPort.node}: Invalid type, expected {cPort.port.typeStr},"
                                    f" got {pPort.port.typeStr}")

        # Make new link
        linkID = self._idManager.newLink()
        link = Link(linkID, pPort, cPort)

        pPort.setLink(link)
        old = cPort.setLink(link)

        # Check for old link
        if old is not None:
            # Remove if present
            old.pPort.remLink(old)

        self._linkLookup[(pPort.portID, cPort.portID)] = link
        self._linkIDLookup[link.linkID] = link
        # Reset the traversal
        self._traversal = None
        return link, old

    def unlink(self, link: Link):
        """
        Removes a link
        :param link: The link to remove
        :return: None
        """
        link.pPort.remLink(link)
        link.cPort.remLink(link)
        del link

        self._traversal = None

    def unlinkByID(self, linkID: int):
        print(f"Unlinking {linkID}")
        link = self._linkIDLookup[linkID]

        self.unlink(link)

    def removeNode(self, node: Node):
        for link in node:
            self.unlink(link)

        for link in node.incoming():
            if link is not None:
                self.unlink(link)

        self._nodeLookup.pop(node.nodeID)

    def _recurGenTraversal(self, out: Deque[Node], curNode: Node, ahead: Set[int], behind: Set[int]):
        ahead.add(curNode.nodeID)

        for link in curNode:
            childID = link.cPort.node.nodeID
            if childID in ahead:
                raise ExecutionError('NodeGraph._recurGenTraversal()',
                                     f"Circular Dependancy Detected, Parent: {curNode}, Child: {link.cPort.node}")
            if childID in behind:
                # Skip if already behind
                continue

            node = link.cPort.node
            self._recurGenTraversal(out, node, ahead, behind)

        ahead.remove(curNode.nodeID)
        behind.add(curNode.nodeID)
        # print(f'Adding {curNode}')
        out.appendleft(curNode)

    def genTraversal(self):
        newQ = deque()
        ahead: Set[int] = set()
        behind: Set[int] = set()

        q = deque(self._nodeLookup.values())

        while len(q) > 0:
            if len(ahead) > 0:
                raise Exception("Ahead set should be empty")

            curItem = q.popleft()
            if curItem.nodeID in behind:
                # Skip since alread added
                continue
            self._recurGenTraversal(newQ, curItem, ahead, behind)

        self._traversal = list(newQ)

    def str_traversal(self) -> str:
        """
        Returns a string representation of the
        node graph's traversal. I.E., the order that
        the nodes are executed in
        """
        if self._traversal is None:
            self.genTraversal()

        lines = ["TRAVERSAL"]
        for x in self._traversal:
            lines.append(str(x))
        return "\n".join(lines)

    def execute(self):
        if self._traversal is None:
            self.genTraversal()

        if self._traversal is None:
            return

        # Reset input ports to None or []
        for n in self._nodeLookup.values():
            n.resetPorts()

        for n in self._traversal:
            n.execute()

    def getLinkByPortID(self, pPortID: int, cPortID: int):
        return self._linkLookup[(pPortID, cPortID)]
