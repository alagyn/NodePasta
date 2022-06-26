from nodepasta.node import Node, InPort, OutPort
from nodepasta.argtypes import NodeArg, FLOAT


class OffsetNode(Node):
    _INPUTS = [InPort("value", "float")]
    _OUTPUTS = [OutPort("output", "float")]
    NODETYPE = "Offset"
    _ARGS = [NodeArg("offset", FLOAT, "Offset", 2)]

    def __init__(self):
        super(OffsetNode, self).__init__()
        self.offset = self.args['offset']

    def setup(self) -> None:
        pass

    def execute(self) -> None:
        v = self.inputs[0].value
        if v is not None:
            self.outputs[0].setValue(v + self.offset.value)
