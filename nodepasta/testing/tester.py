from typing import List, Dict

from nodepasta.node import Node, InPort, OutPort, Link, LinkAddr, IOPort


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

        def _linkup(portList: List[IOPort], linkDict: Dict[str, List[Link]], portDict: Dict[str, IOPort]):
            for portIdx, port in enumerate(portList):
                links = []
                for varportIdx, _ in enumerate(port.links):
                    addr = LinkAddr(0, 0, portIdx, varportIdx)
                    # noinspection PyTypeChecker
                    link = Link(0, None, node, addr)
                    port.addLink(link)
                    links.append(link)
                if port.name in linkDict:
                    raise RuntimeError(
                        f"Cannot Test node, two ports have the same name {port}, {port.name}")
                linkDict[port.name] = links
                portDict[port.name] = port

        self._toNode: Dict[str, List[Link]] = {}
        self._fromNode: Dict[str, List[Link]] = {}

        self._inPortLookup: Dict[str, InPort] = {}
        self._outPortLookup: Dict[str, OutPort] = {}

        _linkup(node.inputs, self._toNode, self._inPortLookup)
        _linkup(node.outputs, self._fromNode, self._outPortLookup)

    def test(self, inputs: Dict[str, any]) -> Dict[str, any]:
        """
        Set the node's inputs to the passed values then execute and return
        the node's outputs

        :inputs: A Dict of inPortName to value
        :return: A Dict of outPortName to value
        """
        for key, value in inputs.items():
            if self._inPortLookup[key].variable:
                for link, x in zip(self._toNode[key], value):
                    link.value = x
            else:
                self._toNode[key][0].value = value

        self._node.execute()

        out = {}

        for key, linkList in self._fromNode.items():
            if self._outPortLookup[key].variable:
                outlist = []
                for link in linkList:
                    outlist.append(link.value)
                out[key] = outlist
            else:
                out[key] = linkList[0].value

        return out
