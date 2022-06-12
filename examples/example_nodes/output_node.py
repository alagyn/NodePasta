from typing import Any, List, Dict
from nodepasta.node import Node, InPort

class OutputNode(Node):
    _INPUTS = [InPort("value", allowAny=True)]
    NODETYPE = "Output"

    def _execute(self, inputs: List[Any]) -> List[Any]:
        print(inputs[0])
        return []
