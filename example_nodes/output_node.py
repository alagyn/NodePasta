from typing import Any, List
from node import Node, I

class OutputNode(Node):
    INPUTS = [I("value", Any)]

    def _execute(self, inputs: List[Any]) -> List[Any]:
        print(inputs[0])
        return []