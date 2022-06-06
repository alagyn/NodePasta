from typing import List, Any

from nodepasta.node import Node, InPort, OutPort

class SumNode(Node):
    _INPUTS = [InPort("a", "float"), InPort("b", "float")]
    _OUTPUTS = [OutPort("value", "float")]

    def _execute(self, inputs: List[Any]) -> List[Any]:
        return [inputs[0] + inputs[1]]
