from collections import deque
from typing import Dict, List, Set, Iterator, Tuple, Optional, Type

import json

from .node import Node, Link, NODE_ERR_CN
from .ng_errors import ExecutionError, NodeGraphError, NodeDefError
from .utils import Vec

_NODES = 'nodes'
_LINKS = 'links'
_POS = 'pos'

_CLASS = 'class'
_ARGS = 'args'


class NodeGraph:
    def __init__(self):
        # NodeID -> Node
        self.nodeLookup: Dict[int, Node] = {}
        # noinspection PyTypeChecker
        self.traversal: List[Node] = None

        self._nodeTypes: Dict[str, Type[Node]] = {}

    def __len__(self) -> int:
        return len(self.nodeLookup)

    def __iter__(self) -> Iterator[Node]:
        return self.nodeLookup.values().__iter__()

    def _loadFromFile(self, filename: str):
        try:
            with open(filename, mode='r') as f:
                jGraph = json.load(f)
        except json.JSONDecodeError as err:
            raise NodeGraphError(f"NodeGraph::loadFromFile() Cannot load file, JSON Error: {err}")

        nodeList = []

        if _NODES not in jGraph or len(jGraph[_NODES]) == 0:
            raise NodeGraphError(f"NodeGraph::loadFromFile() No nodes defined in file")

        if _LINKS not in jGraph:
            raise NodeGraphError(f'NodeGraph::loadFromFile() Cannot load file, links not defined ')

        for idx, n in enumerate(jGraph[_NODES]):
            try:
                nodeClass = n[_CLASS]
            except KeyError:
                raise NodeGraphError(f"NodeGraph::loadFromFile() Node #{idx}, no class was defined")

            try:
                args = n[_ARGS]
            except KeyError:
                raise NodeGraphError(f"NodeGraph::loadFromFile() Node #{idx}, no args were defined")

            try:
                pos = n[_POS]
            except KeyError:
                raise NodeGraphError(f"NodeGraph::loadFromFile() Node #{idx}, no pos was defined")

            try:
                nodeType = self._nodeTypes[nodeClass]
            except KeyError:
                raise NodeGraphError(f'NodeGraph::loadFromFile() Node #{idx}, class type "{nodeClass}" not registered')

            if len(pos) != 2:
                raise NodeGraphError(f'NodeGraph::loadFromFile() Node #{idx}, invalid pos length')

            newNode = nodeType(**args)
            newNode.pos = Vec(pos[0], pos[1])
            nodeList.append(newNode)
            self.addNodes(newNode)

        for idx, link in enumerate(jGraph[_LINKS]):
            if len(link) != 4:
                raise NodeGraphError(f'NodeGraph::loadFromFile() Link #{idx}, invalid length')
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
        self.nodeLookup = {}
        self.traversal = None

        try:
            self._loadFromFile(filename)
        except:
            self.nodeLookup = {}
            self.traversal = None
            raise

    def registerNodeClass(self, nodeType: Type[Node]):
        if nodeType.NODETYPE == NODE_ERR_CN:
            raise NodeDefError(f"Node::init() Node class {nodeType.__name__}, NODETYPE class variable not set")
        try:
            x = self._nodeTypes[nodeType.NODETYPE]
            if x != nodeType:
                raise NodeGraphError(f'NodeGraph::registerNodeClass() Node Type "{nodeType.NODETYPE}" '
                                     f'already defined as {x.__name__}, cannot redefine as {nodeType.__name__}')
            return
        except KeyError:
            pass

        self._nodeTypes[nodeType.NODETYPE] = nodeType

    def writeToFile(self, filename: str):
        # NodeID -> list index
        relativeLookup = {}

        # noinspection PyTypeChecker
        nodeList: List[Node] = [None] * len(self.nodeLookup)

        for idx, node in enumerate(self.nodeLookup.values()):
            relativeLookup[node.nodeID] = idx
            nodeList[idx] = node

        nodeJList = []
        linkJList = []

        for node in nodeList:
            nodeJList.append({
                _CLASS: node.NODETYPE,
                _ARGS: node.getArgs(),
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

    def addNodes(self, *nodes: Node):
        for n in nodes:
            if n.nodeID not in self.nodeLookup:
                self.nodeLookup[n.nodeID] = n
        self.traversal = None

    def makeLink(self, parent: Node, outIdx: int,
                 child: Node, inIdx: int) -> Tuple[Link, Optional[Link]]:
        if parent.nodeID not in self.nodeLookup:
            raise NodeGraphError(f'NodeGraph.makeLink() Cannot make link, '
                                 f'parent not in this graph: "{str(parent)}"')
        if child.nodeID not in self.nodeLookup:
            raise NodeGraphError(f'NodeGraph.makeLink() Cannot make link, '
                                 f'child not in this graph: "{str(child)}"')

        # noinspection PyProtectedMember
        out = parent._addChild(child, outIdx, inIdx)
        self.traversal = None
        return out

    def _recurGenTraversal(self, out: deque[Node], curNode: Node, ahead: Set[int], behind: Set[int]):
        ahead.add(curNode.nodeID)

        for link in curNode:
            childID = link.child.nodeID
            if childID in ahead:
                # TODO better logging
                raise ExecutionError(
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

        q = deque(self.nodeLookup.values())

        while len(q) > 0:
            if len(ahead) > 0:
                raise Exception("Ahead set should be empty")

            curItem = q.popleft()
            if curItem.nodeID in behind:
                # Skip since alread added
                continue
            self._recurGenTraversal(newQ, curItem, ahead, behind)

        self.traversal: List[Node] = list(newQ)

    def execute(self):
        if self.traversal is None:
            self.genTraversal()

        # NodeID -> input list
        inputMap: Dict[int, List[any]] = {}

        # Init inputs to correct len arrays
        for n in self.nodeLookup.values():
            inputMap[n.nodeID] = [None] * n.numInputs()

        for n in self.traversal:
            outputs = n.execute(inputMap[n.nodeID])

            for link in n:
                # TODO remove
                # print(n, self.nodeLookup[link.child.nodeID], link.outIdx, link.inIdx)
                try:
                    if inputMap[link.child.nodeID][link.inIdx] is None:
                        inputMap[link.child.nodeID][link.inIdx] = outputs[link.outIdx]
                    else:
                        # TODO better logging
                        raise ExecutionError("Input already assigned")
                except KeyError:
                    raise ExecutionError("Child node is not in this node graph")
