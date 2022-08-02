from nodepasta.node import Node, InPort

class OutputNode(Node):
    DESCRIPTION = "Prints out the input to the console"
    _INPUTS = [InPort("value", None, "The input" ,allowAny=True)]
    NODETYPE = "Output"

    def setup(self) -> None:
        pass

    def execute(self) -> None:
        print(self.inputs[0].value)
