from typing import List, Any, Dict

from nodepasta.node import Node, OutPort
from nodepasta.argtypes import NodeArg, FLOAT

class ConstSource(Node):
    _OUTPUTS = [OutPort("value", "float")]
    _ARGS = [NodeArg("value", FLOAT, value=2, display='Value')]
    NODETYPE = "Source"

    def __init__(self):
        super(ConstSource, self).__init__()
        self.v = self.args['value']

    def _execute(self, inputs: List[Any]) -> List[Any]:
        return [self.v.value]