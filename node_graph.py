from collections import deque
from typing import Dict, List, Deque, Optional, Set

from node import Node
from ng_errors import ExecutionError

class NodeGraph:
    def __init__(self):
        self.nodes: List[Node] = []

        self.nodeLookup: Dict[int, Node] = {}

        self.traversal: Optional[List[Node]] = None

    def addNode(self, n: Node):
        self.nodes.append(n)

        self.nodeLookup[n.nodeID] = n
        self.traversal = None

    def _recurGenTraversal(self, out: deque[Node], curNode: Node, ahead: Set[int], behind: Set[int]):
        behind.add(curNode.nodeID)

        for child in curNode.children.keys():
            if child in behind:
                # TODO better logging
                raise ExecutionError("Circular Dependancy Detected")
            if child in ahead:
                # Skip if already ahead
                continue

            node = self.nodeLookup[child]
            self._recurGenTraversal(out, node, ahead, behind)

        behind.remove(curNode.nodeID)
        ahead.add(curNode.nodeID)
        out.append(curNode)


    def genTraversal(self):
        newQ = deque()
        ahead: Set[int] = set()
        behind: Set[int] = set()

        q = deque(self.nodes)

        while len(q) > 0:
            curItem = q.popleft()
            if curItem.nodeID in ahead:
                # Skip since alread added
                continue
            self._recurGenTraversal(newQ, curItem, ahead, behind)

        self.nodes = list(newQ)

    def execute(self):
        if self.traversal is None:
            self.genTraversal()

        # NodeID -> input list
        inputMap: Dict[int, List[any]]  = {}

        # Init inputs to correct len arrays
        for n in self.nodes:
            inputMap[n.nodeID] = [None for _ in n.INPUTS]

        for n in self.traversal:
            outputs = n.execute(inputMap[n.nodeID])

            for childID, (outIdx, inIdx) in n.children.items():
                try:
                    if inputMap[childID][inIdx] is None:
                        inputMap[childID][inIdx] = outputs[outIdx]
                    else:
                        # TODO better logging
                        raise ExecutionError("Input already assigned")
                except KeyError:
                    raise ExecutionError("Child node is not in this node graph")