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

        self._inputMap: Dict[str, int] = {}
        self._outputMap: Dict[int, str] = {}

        self._outLinks: Dict[str, Link] = {}

        for idx, port in enumerate(node.inputs):
            self._inputMap[port.port.name] = idx

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

        for key in inputs.keys():
            if key not in self._inputMap:
                raise RuntimeError(f"Invalid Input Key: {key}")

        for key, value in inputs.items():
            port = self._node.inputs[self._inputMap[key]]
            # If not var port, make a single new port
            # with a single value
            if not port.port.variable:
                newPort = OutPort(self._idManager.newPort(), port.port.copy(), Node())
                newLink = Link(self._idManager.newLink(), newPort, port)
                port.setLink(newLink)
                newLink.value = value
            # else attempt to iterate over the value
            else:
                # set the num of var ports to the num of values
                port.setVarPorts(len(value))
                for x, varPort in zip(value, port.getPorts()):
                    newPort = OutPort(self._idManager.newPort(), port.port.copy(), Node())
                    newLink = Link(self._idManager.newLink(), newPort, varPort)
                    varPort.setLink(newLink)
                    newLink.value = x

        self._node.execute()

        out = {}

        for key, link in self._outLinks.items():
            out[key] = link.value

        return out
