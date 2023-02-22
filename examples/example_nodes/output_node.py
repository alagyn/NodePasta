from nodepasta.node import Node, Port
from nodepasta.argtypes import ANY


class OutputNode(Node):
    DESCRIPTION = "Prints out the input to the console"
    _INPUTS = [Port("value", ANY, "The input")]
    NODETYPE = "Output"

    def init(self) -> None:
        pass

    def setup(self) -> None:
        pass

    def execute(self) -> None:
        print(self.inputs[0].value())
