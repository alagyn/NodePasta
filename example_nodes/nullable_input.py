from typing import List, Any

from nodepasta.node import Node, InPort, OutPort

class Power(Node):
    _INPUTS = [InPort("base", "float"), InPort("power", "float")]
    _OUTPUTS = [OutPort("value", "float")]

    def _execute(self, inputs: List[Any]) -> List[Any]:
        if inputs[1] is None:
            powr = 2
        else:
            powr = inputs[1]

        return [pow(inputs[0], powr)]
