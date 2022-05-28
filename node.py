from abc import ABC
from typing import List, Type, Tuple, Dict, Set, Any

from ng_errors import ExecutionError, NodeDefError

class I:
    def __init__(self, name: str, *types: Type):
        self.name = name
        self.types = set(types)

    def check(self, item):
        if type(item) not in self.types:
            raise ExecutionError(f"Invalid Type, Expected:{self.types}, got: {type(item)}")



class O:
    def __init__(self, name: str, oType: Type):
        self.name = name
        self.oType = oType

class Node(ABC):
    INPUTS: List[I] = []
    OUTPUTS: List[O] = []

    _ID_GEN = 0

    def __init__(self):
        # Node ID -> (output idx, child input idx)
        self.children: Dict[int, Tuple[int, int]] = {}

        self.nodeID = self._ID_GEN
        self._ID_GEN += 1

    # TODO def draw?

    def setChild(self, n: 'Node', outIdx: int, inIdx: int):
        self.children[n.nodeID] = (outIdx, inIdx)

    def execute(self, inputs: List[Any]) -> List[Any]:
        if len(inputs) != len(self.INPUTS):
            raise ExecutionError("Invalid number of inputs")

        for idx in range(len(inputs)):
            a = inputs[idx]
            b = self.INPUTS[idx]
            b.check(a)

        # TOCHANGE check outputs?
        #   Might not be necessary since they will be checked by the next node?

        return self._execute(inputs)


    def _execute(self, inputs: List[Any]) -> List[Any]:
        raise NotImplementedError
