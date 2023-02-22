from nodepasta.node import Node, Port
from nodepasta.argtypes import EnumNodeArg, FLOAT, BOOL

from operator import lt, gt

_TYPE = '_TYPE'


class EnumNode(Node):
    DESCRIPTION = "Compares two float values (A [operation] B)"
    _INPUTS = [
        Port("A", FLOAT, "The first value"),
        Port("B", FLOAT, "The second value")
    ]
    _OUTPUTS = [
        Port("Check", BOOL, "The output of the comparison")
    ]
    _ARGS = [
        EnumNodeArg(_TYPE, "Type", "The comparison operator to use", "<", ["<", ">"])
    ]
    NODETYPE = "Compare"

    def init(self) -> None:
        self._opType = self.args[_TYPE]

    def setup(self) -> None:
        self._opType = self.args[_TYPE].value
        self.op = lt
        self.a = self.inputs[0]
        self.b = self.inputs[1]
        self.out = self.outputs[0]

        if self._opType == "<":
            self.op = lt
        else:
            self.op = gt

    def execute(self) -> None:
        if self.a.value() is None or self.b.value() is None:
            self.out.value(None)
        else:
            self.out.value(self.op(self.a.value(), self.b.value()))
