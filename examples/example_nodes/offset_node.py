from typing import Any, List, Dict
from nodepasta.node import Node, InPort, OutPort
from nodepasta.argtypes import NodeArg, INT

class OffsetNode(Node):
    _INPUTS = [InPort("value", "int")]
    _OUTPUTS = [OutPort("value", "int")]
    NODETYPE = "Offset"
    ARGS = [NodeArg("offset", INT, "Offset", 2)]

    def __init__(self, offset: int):
        super(OffsetNode, self).__init__()
        self.offset = offset

    def getArgs(self) -> Dict[str, any]:
        return {"offset": self.offset}

    def _execute(self, inputs: List[Any]) -> List[Any]:
        if inputs[0] is not None:
            return [inputs[0] + self.offset]
        else:
            return [None]