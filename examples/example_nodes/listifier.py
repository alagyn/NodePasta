from nodepasta.node import Node, Port
from nodepasta.argtypes import NodeArg, FLOAT


class ListifierNode(Node):
    DESCRIPTION = "Takes a variable number of inputs and puts them in a list"
    _INPUTS = [Port("Inputs", FLOAT, "The inputs", variable=True)]
    _OUTPUTS = [Port("Output", "List[float]", "The output list")]
    NODETYPE = "Listifier"

    def init(self):
        self.a = self.inputs[0]
        self.out = self.outputs[0]

    def setup(self) -> None:
        self.a = self.inputs[0]
        self.out = self.outputs[0]

    def execute(self) -> None:
        # Input is variable, therefore
        # a.value is a list of every input value
        self.out.value(self.a.value())
