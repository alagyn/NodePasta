from typing import List, Any, Dict

from nodepasta.node import Node, OutPort

class ConstSource(Node):
    _OUTPUTS = [OutPort("value", "float")]
    CLASSNAME = "Source"

    def __init__(self, value: float):
        super().__init__()

        self.value = float(value)

    def getArgs(self) -> Dict[str, any]:
        return {"value": self.value}

    def _execute(self, inputs: List[Any]) -> List[Any]:
        return [self.value]