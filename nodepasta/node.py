from abc import ABC
from typing import List, Set, Dict, Any, Optional, Iterator

from .ng_errors import ExecutionError, NodeDefError


class InPort:
    def __init__(self, name: str, typeStr: Optional[str] = None, allowAny: bool = False):
        self.name = name
        self.typeStr = typeStr
        self.allowAny = allowAny
        if (typeStr is None or len(typeStr) == 0) and not allowAny:
            raise NodeDefError(f"InPort::__init__() No Type defined and allowAny=False: {self}")

        if allowAny:
            self.typeStr = 'Any'

    def copy(self):
        return InPort(self.name, self.typeStr, self.allowAny)

    def __str__(self):
        return f'InPort({self.name}, type:{self.typeStr})'


class OutPort:
    def __init__(self, name: str, typeStr: str):
        self.name = name
        self.typeStr = typeStr

    def copy(self):
        return OutPort(self.name, self.typeStr)

    def __str__(self):
        return f'OutPort({self.name}, type: {self.typeStr})'


_ID_GEN = 0


class _Link:
    def __init__(self, parent: 'Node', child: 'Node', outIdx: int, inIdx: int):
        self.outIdx = outIdx
        self.inIdx = inIdx
        self.parent = parent
        self.child = child


class Node(ABC):
    _INPUTS: List[InPort] = []
    _OUTPUTS: List[OutPort] = []

    def __init__(self):
        global _ID_GEN
        # Node ID -> (output idx, child input idx)
        self._children: Dict[int, _Link] = {}

        self.nodeID = _ID_GEN
        _ID_GEN += 1

        self._inputs: List[InPort] = [x.copy() for x in self._INPUTS]
        self._outputs: List[OutPort] = [x.copy() for x in self._OUTPUTS]

        self._parents: List[Optional[Node]] = [None for _ in self._inputs]

    # TODO def draw?

    def inputs(self) -> Iterator[InPort]:
        return self._inputs.__iter__()

    def outputs(self) -> Iterator[OutPort]:
        return self._outputs.__iter__()

    def __iter__(self) -> Iterator[int]:
        return self._children.keys().__iter__()

    def links(self) -> Iterator[_Link]:
        return self._children.values().__iter__()

    def numInputs(self) -> int:
        return len(self._inputs)

    def numOutputs(self) -> int:
        return len(self._outputs)

    def addChild(self, n: 'Node', outIdx: int, inIdx: int):
        if not 0 <= outIdx < len(self._outputs):
            raise IndexError(f"Node::addChild() {self} -> {n}: Invalid output idx: {outIdx}")
        if not 0 <= inIdx < len(n._inputs):
            raise IndexError(f"Node::addChild() {self} -> {n}: Invalid input idx: {inIdx}")

        i = n._inputs[inIdx]
        if not i.allowAny and self._outputs[outIdx].typeStr != i.typeStr:
            raise ExecutionError(
                f"Node::addChild() {self} -> {n}: Invalid type, expected {i.typeStr},"
                f" got {self._outputs[outIdx].typeStr}")

        self._children[n.nodeID] = _Link(self, n, outIdx, inIdx)
        n._parents[inIdx] = self

    def addInput(self, inPort: InPort, idx: int = -1):
        if idx < 0:
            start = len(self._parents) - idx + 1
        else:
            start = idx + 1

        try:
            self._parents.insert(idx, None)
            self._inputs.insert(idx, inPort)
        except IndexError as err:
            raise NodeDefError(f"Node::addInput() {self} cannot add input, invalid idx {err},"
                               f" input len: {len(self._inputs)}")

        for x in range(start, len(self._parents)):
            p = self._parents[x]
            if p is not None:
                p._children[self.nodeID].inIdx = x

    def addOutput(self, outPort: OutPort, idx: int = -1):
        if idx < 0:
            start = len(self._outputs) - idx + 1
        else:
            start = idx + 1

        try:
            self._outputs.insert(idx, outPort)
        except IndexError as err:
            raise NodeDefError(f"Node::addOutput() {self} cannot add output, invalid idx {err},"
                               f" output len: {len(self._outputs)}")

        for link in self._children.values():
            if link.outIdx >= start:
                link.outIdx += 1

    def remInput(self, idx: int):
        if self._parents[idx] is not None:
            del self._parents[idx]._children[self.nodeID]

        if idx < 0:
            start = len(self._inputs) - idx
        else:
            start = idx

        try:
            self._parents.pop(idx)
            self._inputs.pop(idx)
        except IndexError as err:
            raise NodeDefError(f'Node::remInput() {self} cannot remove input, invalid idx {err},'
                               f' input len: {len(self._inputs)}')

        for x in range(start, len(self._parents)):
            p = self._parents[x]
            if p is not None:
                p._children[self.nodeID].inIdx = x

    def remOutput(self, idx: int):
        if idx < 0:
            trueIdx = len(self._outputs) - idx
        else:
            trueIdx = idx

        # Remove all children using this output
        for nodeID, link in self._children.copy().items():
            if link.outIdx == trueIdx:
                # Remove parent link from child
                link.child._parents[link.inIdx] = None
                # Remove child from parent
                del self._children[nodeID]

        self._outputs.pop(idx)

    def execute(self, inputs: List[Any]) -> List[Any]:

        # TODO remove
        # temp = [f"{x}" for x in self.INPUTS]
        # print(f"Executing {self}, {inputs}, {temp}")

        if len(inputs) != len(self._inputs):
            raise ExecutionError(f"{self}: Invalid number of inputs, expected: {len(self._inputs)}, got: {len(inputs)}")

        return self._execute(inputs)

    def _execute(self, inputs: List[Any]) -> List[Any]:
        raise NotImplementedError

    def __str__(self):
        return f'{self.__class__.__name__}_{self.nodeID}'
