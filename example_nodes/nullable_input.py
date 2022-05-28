from typing import List, Any

from node import Node, I, O

class Power(Node):
    INPUTS = [I("base", float), I("power", float, type(None))]
    OUTPUTS = [O("Result", float)]

    def _execute(self, inputs: List[Any]) -> List[Any]:
        if inputs[1] is None:
            powr = 2
        else:
            powr = inputs[1]

        return [pow(inputs[0], powr)]
