from abc import ABC
from typing import List, Type, Tuple, Dict, Any

from ng_errors import ExecutionError


class IO:
    def __init__(self, name: str):
        self.name = name

    def check(self, item):
        raise NotImplementedError

    def copy(self):
        raise NotImplementedError

class I(IO):
    def __init__(self, name: str, *types: Type):
        super().__init__(name)
        self.name = name
        self.types = set(types)

    def check(self, item):
        if item is None or Any in self.types:
            return
        if type(item) not in self.types:
            raise ExecutionError(f"Invalid Type, Expected:{self.types}, got: {type(item)}")

    def copy(self):
        return I(self.name, *self.types)

    def __str__(self):
        return f'I({self.name}, {[x for x in self.types]})'


class VarIO(IO):
    def __init__(self, name: str, iType: Type, defaultCnt: int):
        super().__init__(name)
        self.iType = iType
        self.cnt = defaultCnt

    def check(self, item):
        if item is None or self.iType == Any:
            return
        if isinstance(item, self.iType):
            raise ExecutionError(f"Invalid Type, Expected:{self.iType}, got: {type(item)}")

    def copy(self):
        return VarIO(self.name, self.iType, self.cnt)

    def __str__(self):
        return f'VarI({self.name}, {self.cnt} * {self.iType}'


class O(IO):
    def __init__(self, name: str, oType: Type):
        super().__init__(name)
        self.name = name
        self.oType = oType

    def check(self, item):
        if item is None or self.oType == Any:
            return
        if isinstance(item, self.oType):
            raise ExecutionError(f"Invalid Type, Expected:{self.oType}, got: {type(item)}")

    def copy(self):
        return O(self.name, self.oType)

    def __str__(self):
        return f'O({self.name}, {self.oType.__name__})'


_ID_GEN = 0


class Node(ABC):
    _INPUTS: List[IO] = []
    _OUTPUTS: List[IO] = []

    def __init__(self):
        global _ID_GEN
        # Node ID -> (output idx, child input idx)
        self.children: Dict[int, Tuple[int, int]] = {}

        self.nodeID = _ID_GEN
        _ID_GEN += 1

        self.inputs: List[IO] = [x.copy() for x in self._INPUTS]
        self.outputs: List[IO] = [x.copy() for x in self._OUTPUTS]

    # TODO def draw?

    def addChild(self, n: 'Node', outIdx: int, inIdx: int):
        if not 0 <= outIdx < len(self.outputs):
            raise IndexError(f"{self}: Invalid output idx: {outIdx}")
        if not 0 <= inIdx < len(n.inputs):
            raise IndexError(f"{n}: Invalid input idx: {inIdx}")

        self.children[n.nodeID] = (outIdx, inIdx)

    def execute(self, inputs: List[Any]) -> List[Any]:

        # TODO remove
        # temp = [f"{x}" for x in self.INPUTS]
        # print(f"Executing {self}, {inputs}, {temp}")

        if len(inputs) != len(self.inputs):
            raise ExecutionError(f"{self}: Invalid number of inputs, expected: {len(self.inputs)}, got: {len(inputs)}")

        for idx in range(len(inputs)):
            a = inputs[idx]
            b = self.inputs[idx]
            b.check(a)

        # TOCHANGE check outputs?
        #   Might not be necessary since they will be checked by the next node?

        return self._execute(inputs)

    def _execute(self, inputs: List[Any]) -> List[Any]:
        raise NotImplementedError

    def __str__(self):
        return f'{self.__class__.__name__}_{self.nodeID}'
