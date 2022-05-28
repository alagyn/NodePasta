from typing import List, Any

from node import Node, I, O

class SumNode(Node):
    INPUTS = [I("a", float), I("b", float)]
    OUTPUTS = [O("value", float)]

    def _execute(self, inputs: List[Any]) -> List[Any]:
        return [inputs[0] + inputs[1]]
