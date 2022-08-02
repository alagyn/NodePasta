from nodepasta.node import Node, InPort, OutPort

class Power(Node):
    DESCRIPTION = "Calculates Exponentials"
    _INPUTS = [InPort("base", "float", "The base"), InPort("power", "float", "The exponent")]
    _OUTPUTS = [OutPort("value", "float", "The output")]
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
