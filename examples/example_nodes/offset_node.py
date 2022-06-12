from typing import Any, List, Dict
from nodepasta.node import Node, InPort, OutPort
from nodepasta.argtypes import NodeArg, FLOAT

class OffsetNode(Node):
    _INPUTS = [InPort("value", "float")]
    _OUTPUTS = [OutPort("value", "float")]
    NODETYPE = "Offset"
    _ARGS = [NodeArg("offset", FLOAT, "Offset", 2)]

    def __init__(self):
        super(OffsetNode, self).__init__()
        self.offset = self.args['offset']

    def _execute(self, inputs: List[Any]) -> List[Any]:
        if inputs[0] is not None:
            return [inputs[0] + self.offset.value]
        else:
            return [None]