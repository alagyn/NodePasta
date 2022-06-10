import abc
from abc import ABC
from typing import List, Dict, Any, Optional, Iterator, Tuple

from nodepasta.errors import ExecutionError, NodeDefError, NodeTypeError
from nodepasta.utils import Vec
from nodepasta.argtypes import NodeArg


class IOPort:
    def __init__(self, name: str, typeStr: str):
        self.name = name
        self.typeStr = typeStr


class InPort(IOPort):
    def __init__(self, name: str, typeStr: Optional[str] = None, allowAny: bool = False):
        super().__init__(name, typeStr)
        self.allowAny = allowAny
        if (typeStr is None or len(typeStr) == 0) and not allowAny:
            raise NodeDefError(f"InPort::__init__() No Type defined and allowAny=False: {self}")

        if allowAny:
            self.typeStr = 'Any'

    def copy(self):
        return InPort(self.name, self.typeStr, self.allowAny)

    def __str__(self):
        return f'InPort({self.name}, type:{self.typeStr})'


class OutPort(IOPort):
    def __init__(self, name: str, typeStr: str):
        super().__init__(name, typeStr)

    def copy(self):
        return OutPort(self.name, self.typeStr)

    def __str__(self):
        return f'OutPort({self.name}, type: {self.typeStr})'


_LINK_ID_GEN = 0


class Link:
    def __init__(self, parent: 'Node', child: 'Node', outIdx: int, inIdx: int):
        global _LINK_ID_GEN
        self.linkID = _LINK_ID_GEN
        _LINK_ID_GEN += 1
        self.outIdx = outIdx
        self.inIdx = inIdx
        self.parent = parent
        self.child = child


_NODE_ID_GEN = 0


class _NodeLinkIter:
    def __init__(self, portIter: Iterator[Dict[int, Link]]):
        self._portIter = portIter
        self._curDIter = None

    def __next__(self) -> Link:
        if self._curDIter is None:
            self._curDIter = next(self._portIter).values().__iter__()
        while True:
            try:
                return next(self._curDIter)
            except StopIteration:
                pass

            self._curDIter = next(self._portIter).values().__iter__()


NODE_ERR_CN = "__ERROR__"


class Node(ABC):
    _INPUTS: List[InPort] = []
    _OUTPUTS: List[OutPort] = []
    ARGS: List[NodeArg] = []
    NODETYPE = NODE_ERR_CN

    def __init__(self, **kwargs):
        global _NODE_ID_GEN

        self.nodeID = _NODE_ID_GEN
        _NODE_ID_GEN += 1

        # Out Port IDX -> LinkID -> Link
        self._children: List[Dict[int, Link]] = [{}] * len(self._OUTPUTS)
        # In Port IDX -> Link
        self._parents: List[Optional[Link]] = [None] * len(self._INPUTS)

        self._inputs: List[InPort] = [x.copy() for x in self._INPUTS]
        self._outputs: List[OutPort] = [x.copy() for x in self._OUTPUTS]

        self.pos = Vec()

    def inputs(self) -> Iterator[InPort]:
        return self._inputs.__iter__()

    def outputs(self) -> Iterator[OutPort]:
        return self._outputs.__iter__()

    def numInputs(self) -> int:
        """
        Returns the number of input ports
        :return: the number of input ports
        """
        return len(self._inputs)

    def numOutputs(self) -> int:
        """
        Returns the number of output ports
        :return: the number of output ports
        """
        return len(self._outputs)

    def __iter__(self) -> _NodeLinkIter:
        return _NodeLinkIter(self._children.__iter__())

    def _addChild(self, n: 'Node', outIdx: int, inIdx: int) -> Tuple[Link, Optional[Link]]:
        if not 0 <= outIdx < len(self._outputs):
            raise IndexError(f"Node::addChild() {self} -> {n}: Invalid output idx: {outIdx}")
        if not 0 <= inIdx < len(n._inputs):
            raise IndexError(f"Node::addChild() {self} -> {n}: Invalid input idx: {inIdx}")

        i = n._inputs[inIdx]
        if not i.allowAny and self._outputs[outIdx].typeStr != i.typeStr:
            raise NodeTypeError(
                f"Node::addChild() {self} -> {n}: Invalid type, expected {i.typeStr},"
                f" got {self._outputs[outIdx].typeStr}")

        link = Link(self, n, outIdx, inIdx)
        self._children[outIdx][link.linkID] = link
        old = n._parents[inIdx]
        n._parents[inIdx] = link

        return link, old

    def execute(self, inputs: List[Any]) -> List[Any]:

        # TODO remove
        # temp = [f"{x}" for x in self.INPUTS]
        # print(f"Executing {self}, {inputs}, {temp}")

        if len(inputs) != len(self._inputs):
            raise ExecutionError(f"{self}: Invalid number of inputs, expected: {len(self._inputs)}, got: {len(inputs)}")

        return self._execute(inputs)

    @abc.abstractmethod
    def getArgs(self) -> Dict[str, any]:
        raise NotImplementedError

    @abc.abstractmethod
    def _execute(self, inputs: List[Any]) -> List[Any]:
        raise NotImplementedError

    def __str__(self):
        return f'{self.__class__.__name__}_{self.nodeID}'
