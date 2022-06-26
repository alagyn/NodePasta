from nodepasta.node import Node, InPort

class OutputNode(Node):
    _INPUTS = [InPort("value", allowAny=True)]
    NODETYPE = "Output"

    def setup(self) -> None:
        pass

    def execute(self) -> None:
        print(self.inputs[0].value)
