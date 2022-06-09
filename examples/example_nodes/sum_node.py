from typing import List, Any, Dict

from nodepasta.node import Node, InPort, OutPort

class SumNode(Node):
    _INPUTS = [InPort("a", "float"), InPort("b", "float")]
    _OUTPUTS = [OutPort("value", "float")]
    CLASSNAME = "Sum"

    def _execute(self, inputs: List[Any]) -> List[Any]:
        return [inputs[0] + inputs[1]]

    def getArgs(self) -> Dict[str, any]:
        return {}