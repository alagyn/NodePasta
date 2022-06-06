from typing import List, Any

from nodepasta.node import Node, OutPort

class ConstSource(Node):
    _OUTPUTS = [OutPort("value", "float")]

    def __init__(self, value: float):
        super().__init__()

        self.value = float(value)


    def _execute(self, inputs: List[Any]) -> List[Any]:
        return [self.value]