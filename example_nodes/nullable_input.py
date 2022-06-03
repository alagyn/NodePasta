from typing import List, Any

from node import Node, I, O

class Power(Node):
    _INPUTS = [I("base", float), I("power", float)]
    _OUTPUTS = [O("value", float)]

    def _execute(self, inputs: List[Any]) -> List[Any]:
        if inputs[1] is None:
            powr = 2
        else:
            powr = inputs[1]

        return [pow(inputs[0], powr)]
