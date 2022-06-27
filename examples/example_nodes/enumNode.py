from nodepasta.node import Node, InPort, OutPort
from nodepasta.argtypes import EnumNodeArg
from operator import lt, gt

_TYPE = '_TYPE'

class EnumNode(Node):
    _INPUTS = [
        InPort("A", "float"),
        InPort("B", "float")
    ]
    _OUTPUTS = [
        OutPort("Check", "bool")
    ]
    _ARGS = [
        EnumNodeArg(_TYPE, "Type", "<", ["<", ">"])
    ]
    NODETYPE = "Compare"

    def __init__(self):
        super().__init__()
        self._opType = self.args[_TYPE]
        self.op = None
        self.a = self.inputs[0]
        self.b = self.inputs[1]
        self.out = self.outputs[0]

    def setup(self) -> None:
        if self._opType == "<":
            self.op = lt
        else:
            self.op = gt

    def execute(self) -> None:
        if self.a.value is None or self.b.value is None:
            self.out.setValue(None)
        else:
            self.out.setValue(self.op(self.a.value, self.b.value))