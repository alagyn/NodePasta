from nodepasta.node import Node, Port
from nodepasta.argtypes import NodeArg, FLOAT


class OffsetNode(Node):
    DESCRIPTION = "Adds a constant output to the input"
    _INPUTS = [Port("value", FLOAT, "The input")]
    _OUTPUTS = [Port("output", FLOAT, "The output")]
    NODETYPE = "Offset"
    _ARGS = [NodeArg("offset", FLOAT, "Offset", "The constant offset", 2)]

    def init(self):
        pass

    def setup(self) -> None:
        self.offset = self.args['offset']

    def execute(self) -> None:
        v = self.inputs[0].value()
        if v is not None:
            self.outputs[0].value(v + self.offset.value)
