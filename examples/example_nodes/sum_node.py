from nodepasta.node import Node, InPort, OutPort


class SumNode(Node):
    DESCRIPTION = "Adds two values together"
    _INPUTS = [InPort("a", "float", "The first value"), InPort("b", "float", "The second value")]
    _OUTPUTS = [OutPort("value", "float", "The output")]
    NODETYPE = "Sum"

    def __init__(self):
        super(SumNode, self).__init__(noneCapable=False)
        self.a = self.inputs[0]
        self.b = self.inputs[1]
        self.out = self.outputs[0]

    def setup(self) -> None:
        pass

    def execute(self) -> None:
        if self.a.value is None or self.b.value is None:
            self.out.setValue(None)

        self.out.setValue(self.a.value + self.b.value)
