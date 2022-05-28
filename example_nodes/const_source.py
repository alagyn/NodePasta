from typing import List, Any

from node import Node, O

class ConstSource(Node):
    OUTPUTS = [O("value", float)]

    def __init__(self, value: float):
        super().__init__()

        self.value = float(value)


    def _execute(self, inputs: List[Any]) -> List[Any]:
        return [self.value]