from nodepasta.node import Node, Port
from nodepasta.argtypes import FLOAT


class Power(Node):
    DESCRIPTION = "Calculates Exponentials"
    _INPUTS = [Port("base", FLOAT, "The base"), Port("power", FLOAT, "The exponent")]
    _OUTPUTS = [Port("value", FLOAT, "The output")]
    NODETYPE = "Power"

    def init(self) -> None:
        pass

    def setup(self) -> None:
        pass

    def execute(self) -> None:
        if self.inputs[1].value() is None:
            powr = 2
        else:
            powr = self.inputs[1].value()

        out = pow(self.inputs[0].value(), powr)

        self.outputs[0].value(out)
