from typing import List, Dict, Any, Union

from nodepasta.node import Node, Link
from nodepasta.ports import IOPort, InPort, OutPort
from nodepasta.errors import NodeDefError


class DummyLink:
    def __init__(self, port: IOPort) -> None:
        self.port = port
        port.setLink(self)  # type: ignore
        self.value = None

    def setValue(self, value: Any):
        self.value = value

    def getValue(self) -> Any:
        return self.value


class DummyVarLink:
    def __init__(self, port: IOPort) -> None:
        if not port.port.variable:
            raise NodeDefError("DummyVarLink.init()", "Port not variable")

        self.dummyLinks: List[DummyLink] = []

        for varport in port.getPorts():
            dl = DummyLink(varport)
            self.dummyLinks.append(dl)

    def setValue(self, value: List[Any]):
        if len(value) != len(self.dummyLinks):
            raise NodeDefError("DummyVarLink.setValue()",
                               f"Expected {len(self.dummyLinks)} values, got {len(value)}")

        for dl, val in zip(self.dummyLinks, value):
            dl.setValue(val)

    def getValue(self) -> List[Any]:
        return [x.getValue() for x in self.dummyLinks]


def makeDummyLink(port: IOPort) -> Union[DummyLink, DummyVarLink]:
    if port.port.variable:
        return DummyVarLink(port)
    return DummyLink(port)


class Tester:
    """
    Test Utility for testing input and output of nodes
    """

    def __init__(self, node: Node):
        """
        Create a tester
        :node: The node to test
        """

        self._node = node

        self._inLinks: Dict[str, Union[DummyLink, DummyVarLink]] = {
            port.port.name: makeDummyLink(port) for port in node.getInputPorts()
        }
        self._outLinks: Dict[str, Union[DummyLink, DummyVarLink]] = {
            port.port.name: makeDummyLink(port) for port in node.getOutputPorts()
        }

    def test(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set the node's inputs to the passed values then execute and return
        the node's outputs

        :inputs: A Dict of inPortName to value
        :return: A Dict of outPortName to value
        """
        for key, value in inputs.items():
            self._inLinks[key].setValue(value)

        self._node.execute()

        out = {}

        for key, link in self._outLinks.items():
            out[key] = link.getValue()

        return out
