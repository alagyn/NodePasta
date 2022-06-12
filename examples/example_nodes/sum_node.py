from typing import List, Any, Dict

from nodepasta.node import Node, InPort, OutPort

class SumNode(Node):
    _INPUTS = [InPort("a", "float"), InPort("b", "float")]
    _OUTPUTS = [OutPort("value", "float")]
    NODETYPE = "Sum"

    def __init__(self):
        super(SumNode, self).__init__(noneCapable=False)

    def _execute(self, inputs: List[Any]) -> List[Any]:
        return [inputs[0] + inputs[1]]
