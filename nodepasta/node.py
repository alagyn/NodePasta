import abc
from abc import ABC
from typing import List, Dict, Any, Optional, Iterator

from nodepasta.errors import ExecutionError, NodeDefError
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
            raise NodeDefError(f"InPort.init()", f"No Type defined and allowAny=False: {self}")

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


class Link:
    def __init__(self, linkID: int, parent: 'Node', child: 'Node', outIdx: int, inIdx: int):
        self.linkID = linkID
        self.outIdx = outIdx
        self.inIdx = inIdx
        self.parent = parent
        self.child = child

    def __str__(self):
        return f'{self.parent}:{self.outIdx} -> {self.child}:{self.inIdx}'


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
    _ARGS: List[NodeArg] = []
    NODETYPE = NODE_ERR_CN

    def __init__(self, *, noneCapable: bool = True):
        self.nodeID = -1

        # Out Port IDX -> LinkID -> Link
        self._children: List[Dict[int, Link]] = [{}] * len(self._OUTPUTS)
        # In Port IDX -> Link
        self._parents: List[Optional[Link]] = [None] * len(self._INPUTS)

        self._noneCapable = noneCapable

        self.args: Dict[str, NodeArg] = {x.name: x.copy() for x in self._ARGS}

        self.pos = Vec()

    def inputs(self) -> Iterator[InPort]:
        return self._INPUTS.__iter__()

    def outputs(self) -> Iterator[OutPort]:
        return self._OUTPUTS.__iter__()

    def numInputs(self) -> int:
        """
        Returns the number of input ports
        :return: the number of input ports
        """
        return len(self._INPUTS)

    def numOutputs(self) -> int:
        """
        Returns the number of output ports
        :return: the number of output ports
        """
        return len(self._OUTPUTS)

    def __iter__(self) -> _NodeLinkIter:
        return _NodeLinkIter(self._children.__iter__())

    def execute(self, inputs: List[Any]) -> List[Any]:
        if len(inputs) != len(self._INPUTS):
            raise ExecutionError(f"Node.execute()",
                                 f"{self}: Invalid number of inputs, expected: {len(self._INPUTS)}, got: {len(inputs)}")
        if not self._noneCapable:
            for idx, x in enumerate(inputs):
                if x is None:
                    raise ExecutionError(f'Node.execute()', f'{self}: Input {self._INPUTS[idx]} is none')

        return self._execute(inputs)

    def unloadArgs(self) -> Dict[str, any]:
        return {x.name: x.getJSON() for x in self.args.values()}

    def loadArgs(self, args: Dict[str, any]) -> None:
        for key, val in args.items():
            try:
                self.args[key].loadJSON(val)
            except KeyError:
                raise NodeDefError("Node.loadArgs()",
                                   f"{self} Invalid Argument name {key}:{val}")

    @abc.abstractmethod
    def _execute(self, inputs: List[Any]) -> List[Any]:
        raise NotImplementedError

    def __str__(self):
        return f'{self.__class__.__name__}_{self.nodeID}'
