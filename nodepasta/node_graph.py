from collections import deque
from typing import Dict, List, Set, Iterator, Tuple, Optional, Type

import json

from .node import Node, Link, NODE_ERR_CN
from .errors import ExecutionError, NodeGraphError, NodeDefError, NodeTypeError
from .utils import Vec

_NODES = 'nodes'
_LINKS = 'links'
_POS = 'pos'

_CLASS = 'class'
_ARGS = 'args'


class NodeGraph:
    def __init__(self):
        # NodeID -> Node
        self._nodeLookup: Dict[int, Node] = {}
        # noinspection PyTypeChecker
        self._traversal: List[Node] = None

        self._nodeTypes: Dict[str, Type[Node]] = {}
        self._filename = ""
        self._nodeIDGen = 0
        self._linkIDGen = 0

    def __len__(self) -> int:
        return len(self._nodeLookup)

    def __iter__(self) -> Iterator[Node]:
        return self._nodeLookup.values().__iter__()

    def _loadFromFile(self, filename: str):
        try:
            with open(filename, mode='r') as f:
                jGraph = json.load(f)
        except json.JSONDecodeError as err:
            raise NodeGraphError("NodeGraph.loadFromFile()", f"Cannot load file, JSON Error: {err}")

        nodeList = []

        if _NODES not in jGraph or len(jGraph[_NODES]) == 0:
            raise NodeGraphError("NodeGraph.loadFromFile()", f"No nodes defined in file")

        if _LINKS not in jGraph:
            raise NodeGraphError("NodeGraph.loadFromFile()", f"Cannot load file, links not defined ")

        for idx, n in enumerate(jGraph[_NODES]):
            try:
                nodeClass = n[_CLASS]
            except KeyError:
                raise NodeGraphError("NodeGraph.loadFromFile()", f"Node #{idx}, no class was defined")

            try:
                args = n[_ARGS]
            except KeyError:
                raise NodeGraphError("NodeGraph.loadFromFile()", f"Node #{idx}, no args were defined")

            try:
                pos = n[_POS]
            except KeyError:
                raise NodeGraphError(f"NodeGraph.loadFromFile()", f"Node #{idx}, no pos was defined")

            try:
                nodeType = self._nodeTypes[nodeClass]
            except KeyError:
                raise NodeGraphError(f'NodeGraph.loadFromFile()',
                                     f'Node #{idx}, class type "{nodeClass}" not registered')

            if len(pos) != 2:
                raise NodeGraphError(f'NodeGraph.loadFromFile()', f'Node #{idx}, invalid pos length')

            newNode = nodeType()
            newNode.loadArgs(args)
            newNode.pos = Vec(pos[0], pos[1])
            nodeList.append(newNode)
            self.addNode(newNode)

        for idx, link in enumerate(jGraph[_LINKS]):
            if len(link) != 4:
                raise NodeGraphError(f'NodeGraph.loadFromFile()', f'Link #{idx}, invalid length')
            parent = nodeList[link[0]]
            outIdx = link[1]
            child = nodeList[link[2]]
            inIdx = link[3]

            self.makeLink(parent, outIdx, child, inIdx)

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
            self._loadFromFile(filename)
            self.genTraversal()
        except:
            self._nodeLookup = {}
            self._traversal = None
            raise

    def loadArgs(self, args: Dict[int, Dict[str, any]]):
        for nodeID, arg in args.items():
            try:
                node = self._nodeLookup[nodeID]
            except KeyError:
                raise NodeGraphError('NodeGraph.loadArgs()', f"Cannot load args for node ID: {nodeID}. ID not in graph")

            node.loadArgs(arg)

    def registerNodeClass(self, nodeType: Type[Node]):
        if nodeType.NODETYPE == NODE_ERR_CN:
            raise NodeDefError(f"Node.init()", f"Node class {nodeType.__name__}, NODETYPE class variable not set")
        try:
            x = self._nodeTypes[nodeType.NODETYPE]
            if x != nodeType:
                raise NodeGraphError(f'NodeGraph.registerNodeClass()', f'Node Type "{nodeType.NODETYPE}" '
                                                                       f'already defined as {x.__name__}, cannot redefine as {nodeType.__name__}')
            return
        except KeyError:
            pass

        self._nodeTypes[nodeType.NODETYPE] = nodeType

    def writeToFile(self, filename: str):
        # NodeID -> list index
        relativeLookup = {}

        # noinspection PyTypeChecker
        nodeList: List[Node] = [None] * len(self._nodeLookup)

        for idx, node in enumerate(self._nodeLookup.values()):
            relativeLookup[node.nodeID] = idx
            nodeList[idx] = node

        nodeJList = []
        linkJList = []

        for node in nodeList:
            nodeJList.append({
                _CLASS: node.NODETYPE,
                _ARGS: node.unloadArgs(),
                _POS: [node.pos.x, node.pos.y]
            })

            for link in node:
                parentIdx = relativeLookup[link.parent.nodeID]
                childIdx = relativeLookup[link.child.nodeID]
                linkJList.append(
                    [parentIdx, link.outIdx, childIdx, link.inIdx]
                )

        out = {
            _NODES: nodeJList,
            _LINKS: linkJList
        }

        with open(filename, mode='w') as f:
            json.dump(out, f)

    def addNode(self, node: Node):
        if node.nodeID == -1:
            node.nodeID = self._nodeIDGen
            self._nodeIDGen += 1
            self._nodeLookup[node.nodeID] = node
        else:
            raise NodeGraphError('NodeGraph.addNodes()',
                                 f"Cannot add node {node}, it already belongs to a node graph")
        self._traversal = None

    # noinspection PyProtectedMember
    def makeLink(self, parent: Node, outIdx: int,
                 child: Node, inIdx: int) -> Tuple[Link, Optional[Link]]:
        """
        Makes a new link.
        :param parent: The parent node
        :param outIdx: The idx of the output port
        :param child: The child node
        :param inIdx: The idx of the input port
        :return: The new link and an old link that was replaced, if it exists, else None
        """
        if parent.nodeID not in self._nodeLookup:
            raise NodeGraphError(f'NodeGraph.makeLink()', f'Cannot make link, '
                                                          f'parent not in this graph: "{str(parent)}"')
        if child.nodeID not in self._nodeLookup:
            raise NodeGraphError(f'NodeGraph.makeLink()', f'Cannot make link, '
                                                          f'child not in this graph: "{str(child)}"')
        if parent.nodeID == child.nodeID:
            raise NodeGraphError('NodeGraph.makeLink()',
                                 f'Cannot make link, parent == child: {parent} == {child}')
        if not 0 <= outIdx < len(parent._OUTPUTS):
            raise IndexError("NodeGraph.makeLink()", f"{parent} -> {child}: Invalid output idx: {outIdx}")
        if not 0 <= inIdx < len(child._INPUTS):
            raise IndexError("NodeGraph.makeLink()", f"{parent} -> {child}: Invalid input idx: {inIdx}")

        # Check the typing on the inport
        inPort = child._INPUTS[inIdx]
        if not inPort.allowAny and parent._OUTPUTS[outIdx].typeStr != inPort.typeStr:
            raise NodeTypeError(
                f"Node.addChild()", f"{parent} -> {child}: Invalid type, expected {inPort.typeStr},"
                                    f" got {parent._OUTPUTS[outIdx].typeStr}")

        # Make new link
        link = Link(self._linkIDGen, parent, child, outIdx, inIdx)
        self._linkIDGen += 1
        # Set link in parent
        parent._children[outIdx][link.linkID] = link

        # Check for old link
        old = child._parents[inIdx]
        if old is not None:
            # Remove if present
            self.unlink(old)
        # Set new link
        child._parents[inIdx] = link
        # Reset the traversal
        self._traversal = None
        return link, old

    # noinspection PyProtectedMember
    def unlink(self, link: Link):
        """
        Removes a link
        :param link: The link to remove
        :return: None
        """
        parent = link.parent
        child = link.child
        parent._children[link.outIdx].pop(link.linkID)
        child._parents[link.inIdx] = None
        self._traversal = None

    def _recurGenTraversal(self, out: deque[Node], curNode: Node, ahead: Set[int], behind: Set[int]):
        ahead.add(curNode.nodeID)

        for link in curNode:
            childID = link.child.nodeID
            if childID in ahead:
                raise ExecutionError('NodeGraph._recurGenTraversal()',
                                     f"Circular Dependancy Detected, Parent: {curNode}, Child: {link.child}")
            if childID in behind:
                # Skip if already behind
                continue

            node = link.child
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

        self._traversal: List[Node] = list(newQ)

    def execute(self):
        if self._traversal is None:
            self.genTraversal()

        # NodeID -> input list
        inputMap: Dict[int, List[any]] = {}

        # Init inputs to correct len arrays
        for n in self._nodeLookup.values():
            inputMap[n.nodeID] = [None] * n.numInputs()

        for n in self._traversal:
            outputs = n.execute(inputMap[n.nodeID])

            for link in n:
                try:
                    inputList = inputMap[link.child.nodeID]
                except KeyError:
                    raise ExecutionError("NodeGraph.execute()", f"Child node {link.child} is not in this node graph")

                try:
                    if inputList[link.inIdx] is None:
                        inputList[link.inIdx] = outputs[link.outIdx]
                    else:
                        raise ExecutionError("NodeGraph.execute()", f"Input already assigned, {link}")
                except IndexError:
                    raise ExecutionError("NodeGraph.execute()", f"Invalid input idx, {link}")
