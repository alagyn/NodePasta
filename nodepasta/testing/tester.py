from typing import Dict, Any

from nodepasta.node import Node, Link
from nodepasta.ports import InPort, OutPort
from nodepasta.id_manager import IDManager


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

        # Init first to setup the internal objects
        self._idManager = IDManager()
        self._node._init(self._idManager)

        self._inLinks: Dict[str, Link] = {}
        self._outLinks: Dict[str, Link] = {}

        for port in node.getInputPorts():
            newPort = OutPort(self._idManager.newPort(), port.port.copy(), Node())
            newLink = Link(self._idManager.newLink(), newPort, port)
            self._inLinks[port.port.name] = newLink
            port.setLink(newLink)

        for port in node.getOutputPorts():
            newPort = InPort(self._idManager.newPort(), port.port.copy(), Node())
            newLink = Link(self._idManager.newLink(), port, newPort)
            self._outLinks[port.port.name] = newLink
            port.setLink(newLink)

    def test(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set the node's inputs to the passed values then execute and return
        the node's outputs

        :inputs: A Dict of inPortName to value
        :return: A Dict of outPortName to value
        """
        for key, value in inputs.items():
            self._inLinks[key].value = value

        self._node.execute()

        out = {}

        for key, link in self._outLinks.items():
            out[key] = link.value

        return out
