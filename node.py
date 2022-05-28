from abc import ABC
from typing import List, Type, Tuple, Dict, Set, Any

from ng_errors import ExecutionError, NodeDefError

class IO:
    def __init__(self, name: str):
        self.name = name

class I(IO):
    def __init__(self, name: str, *types: Type):
        super().__init__(name)
        self.name = name
        self.types = set(types)

    def check(self, item):
        if item is None or Any in self.types :
            return
        if type(item) not in self.types:
            raise ExecutionError(f"Invalid Type, Expected:{self.types}, got: {type(item)}")

    def __str__(self):
        return f'I({self.name}, {[x for x in self.types]})'

class O(IO):
    def __init__(self, name: str, oType: Type):
        super().__init__(name)
        self.name = name
        self.oType = oType

    def __str__(self):
        return f'O({self.name}, {self.oType.__name__})'

class _ListWrap:
    def __init__(self, inputs: List[IO]):
        self._inputs = inputs

    def __getattr__(self, item):
        for idx, x in enumerate(self._inputs):
            if x.name == item:
                return idx

        raise KeyError(item)

_ID_GEN = 0

class Node(ABC):
    INPUTS: List[I] = []
    OUTPUTS: List[O] = []

    def __init__(self):
        global _ID_GEN
        # Node ID -> (output idx, child input idx)
        self.children: Dict[int, Tuple[int, int]] = {}

        self.nodeID = _ID_GEN
        _ID_GEN += 1

        self.i = _ListWrap(self.INPUTS)
        self.o = _ListWrap(self.OUTPUTS)

    # TODO def draw?

    def addChild(self, n: 'Node', outIdx: int, inIdx: int):
        if not 0 <= outIdx < len(self.OUTPUTS):
            raise IndexError(f"{self}: Invalid output idx: {outIdx}")
        if not 0 <= inIdx < len(n.INPUTS):
            raise IndexError(f"{n}: Invalid input idx: {inIdx}")

        self.children[n.nodeID] = (outIdx, inIdx)

    def execute(self, inputs: List[Any]) -> List[Any]:

        # TODO remove
        # temp = [f"{x}" for x in self.INPUTS]
        # print(f"Executing {self}, {inputs}, {temp}")

        if len(inputs) != len(self.INPUTS):
            raise ExecutionError(f"{self}: Invalid number of inputs, expected: {len(self.INPUTS)}, got: {len(inputs)}")

        for idx in range(len(inputs)):
            a = inputs[idx]
            b = self.INPUTS[idx]
            b.check(a)

        # TOCHANGE check outputs?
        #   Might not be necessary since they will be checked by the next node?

        return self._execute(inputs)


    def _execute(self, inputs: List[Any]) -> List[Any]:
        raise NotImplementedError

    def __str__(self):
        return f'{self.__class__.__name__}_{self.nodeID}'