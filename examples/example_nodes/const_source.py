from nodepasta.argtypes import NodeArg, FLOAT
from nodepasta.node import Node, OutPort


class ConstSource(Node):
    _OUTPUTS = [OutPort("value", "float", "The output")]
    _ARGS = [NodeArg("value", FLOAT, value=2, display='Value', descr="The output value")]
    NODETYPE = "Source"
    DESCRIPTION = "Outputs a constant value"

    def __init__(self):
        super(ConstSource, self).__init__()
        self.v = self.args['value']

    def setup(self) -> None:
        pass

    def execute(self) -> None:
        self.outputs[0].setValue(self.v.value)
