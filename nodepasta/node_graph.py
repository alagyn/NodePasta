from collections import deque
from typing import Dict, List, Set, Iterator, Tuple, Optional

from .node import Node, Link
from .ng_errors import ExecutionError, NodeGraphError

class NodeGraph:
    def __init__(self):
        self.nodeLookup: Dict[int, Node] = {}
        # noinspection PyTypeChecker
        self.traversal: List[Node] = None

    def __len__(self) -> int:
        return len(self.nodeLookup)

    def __iter__(self) -> Iterator[Node]:
        return self.nodeLookup.values().__iter__()

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
