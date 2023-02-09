from nodepasta.node import Node, Port
from nodepasta.argtypes import FLOAT


class SumNode(Node):
    DESCRIPTION = "Adds two values together"
    _INPUTS = [
        Port("a", FLOAT, "The first value"),
        Port("b", FLOAT, "The second value")
    ]
    _OUTPUTS = [Port("value", FLOAT, "The output")]
    NODETYPE = "Sum"

    def init(self):
        self.a = self.inputs[0]
        self.b = self.inputs[1]
        self.out = self.outputs[0]

    def execute(self) -> None:
        if self.a.value() is None or self.b.value() is None:
            self.out.value(None)

        self.out.value(self.a.value() + self.b.value())
