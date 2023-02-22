from nodepasta.argtypes import NodeArg, FLOAT
from nodepasta.node import Node, Port


class ConstSource(Node):
    _OUTPUTS = [Port("value", "float", "The output")]
    _ARGS = [NodeArg("value", FLOAT, value=2, display='Value', descr="The output value")]
    NODETYPE = "Source"
    DESCRIPTION = "Outputs a constant value"

    def init(self):
        self.v = self.args['value']

    def setup(self) -> None:
        pass

    def execute(self) -> None:
        self.outputs[0].value(self.v.value)
