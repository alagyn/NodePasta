from nodepasta.node import Node, InPort, OutPort

class Power(Node):
    _INPUTS = [InPort("base", "float"), InPort("power", "float")]
    _OUTPUTS = [OutPort("value", "float")]
    NODETYPE = "Power"

    def setup(self) -> None:
        pass

    def execute(self) -> None:
        if self.inputs[1].value is None:
            powr = 2
        else:
            powr = self.inputs[1].value

        out = pow(self.inputs[0].value, powr)

        self.outputs[0].setValue(out)
