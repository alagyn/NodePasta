from nodepasta.node import Node, OutPort, InPort
from nodepasta.argtypes import NodeArg, FLOAT

class ListifierNode(Node):
    _INPUTS = [
        InPort("Inputs", 'float', variable=True, cnt=2)
    ]
    _OUTPUTS = [
        OutPort("Output", "List[float]")
    ]
    NODETYPE = "Listifier"

    def __init__(self):
        super(ListifierNode, self).__init__()
        self.a = self.inputs[0]
        self.out = self.outputs[0]

    def setup(self) -> None:
        pass

    def execute(self) -> None:
        # Input is variable, therefore
        # a.value is a list of every input value
        self.out.setValue(self.a.value)
