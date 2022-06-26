from nodepasta.argtypes import NodeArg, FLOAT
from nodepasta.node import Node, OutPort


class ConstSource(Node):
    _OUTPUTS = [OutPort("value", "float")]
    _ARGS = [NodeArg("value", FLOAT, value=2, display='Value')]
    NODETYPE = "Source"

    def __init__(self):
        super(ConstSource, self).__init__()
        self.v = self.args['value']

    def setup(self) -> None:
        pass

    def execute(self) -> None:
        self.outputs[0].setValue(self.v.value)
