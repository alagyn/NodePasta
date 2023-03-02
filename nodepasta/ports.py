from typing import Any, Optional, Iterator, List, Sequence, TYPE_CHECKING

from nodepasta.argtypes import ANY
from nodepasta.errors import NodeDefError, ExecutionError
from nodepasta.id_manager import IDManager

if TYPE_CHECKING:
    from nodepasta.node import Node


class Link:
    def __init__(self, linkID: int, pPort: 'IOPort', cPort: 'IOPort'):
        self.linkID = linkID
        self.pPort = pPort
        self.cPort = cPort
        self.value = None

    def __str__(self):
        return f'Link {self.pPort} -> {self.cPort}'

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Link):
            return False

        return self.linkID == __o.linkID


class Port:
    def __init__(self, name: str, typeStr: str, descr: str, variable=False) -> None:
        self.name = name
        self.typeStr = typeStr
        self.descr = descr
        self.variable = variable


class IOPort:
    def __init__(self, portID: int, port: Port, node: 'Node'):
        self.portID = portID
        self.node = node

        self.port = port
        self.allowAny = port.typeStr == ANY

    def setLink(self, link: Link) -> Optional[Link]:
        raise NotImplementedError

    def remLink(self, link: Link):
        raise NotImplementedError

    def getPorts(self) -> Sequence['IOPort']:
        raise NotImplementedError

    def setVarPorts(self, num: int):
        raise NotImplementedError

    def addVarPort(self) -> 'IOPort':
        raise NotImplementedError

    def remVarPort(self):
        raise NotImplementedError

    def __str__(self):
        return f'InPort(type:{self.port.typeStr})'

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, InPort):
            return False

        return __o.portID == self.portID


class InPort(IOPort):
    def __init__(self, portID: int, port: Port, node: 'Node'):
        super().__init__(portID, port, node)

        self.link: Optional[Link] = None

    def value(self) -> Any:
        if self.link is not None:
            return self.link.value

    def setLink(self, link: Link):
        if link.cPort != self:
            raise NodeDefError("InPort.setLink", "Cannot set link, unequals port ID")
        x = self.link
        self.link = link
        return x

    def remLink(self, link: Link):
        if self.link == link:
            self.link = None
        else:
            raise NodeDefError("InPort.remLink", "Cannot remove link, unequal link ID")

    def getPorts(self) -> Sequence['IOPort']:
        return [self]

    def setVarPorts(self, num: int):
        if num != 1:
            raise NodeDefError("InPort.setVarPorts()",
                               "Cannot set varports num != 1, port not variable")

    def addVarPort(self) -> 'IOPort':
        raise NodeDefError('InPort.addVarPort()', 'Cannot add var port, port is not variable')

    def remVarPort(self):
        raise NodeDefError('InPort.remVarPort()', 'Cannot rem var port, port is not variable')

    def __str__(self):
        return f'InPort(type: {self.port.typeStr})'


class OutPort(IOPort):
    def __init__(self, portID: int, port: Port, node: 'Node'):
        super().__init__(portID, port, node)
        self.links: List[Link] = []

    def value(self, v: Any):
        for link in self.links:
            link.value = v

    def setLink(self, link: Link) -> Optional[Link]:
        self.links.append(link)

    def addLink(self, link: Link):
        self.links.append(link)

    def getPorts(self) -> Sequence['IOPort']:
        return [self]

    def remLink(self, link: Link):
        try:
            self.links.remove(link)
        except ValueError:
            raise NodeDefError("OutPort.remLink()", "Cannot remove link, link not found") from None

    def setVarPorts(self, num: int):
        if num != 1:
            raise NodeDefError("OutPort.setVarPorts()", "Cannot set varports, port not variable")

    def addVarPort(self) -> 'IOPort':
        raise NodeDefError('OutPort.addVarPort()', 'Cannot add var port, port is not variable')

    def remVarPort(self):
        raise NodeDefError('OutPort.remVarPort()', 'Cannot rem var port, port is not variable')

    def __iter__(self) -> Iterator[Link]:
        return iter(self.links)

    def __str__(self):
        return f'OutPort(type: {self.port.typeStr})'


class _VarInPort(InPort):
    def __init__(self, idManager: IDManager, port: Port, node: 'Node'):
        super().__init__(-1, port, node)
        self.ports: List[InPort] = []
        self.idManager = idManager

    # Set Link is not implemented, should never be setting a link on a parent VarPort

    def setVarPorts(self, num: int):
        self.ports = [InPort(self.idManager.newPort(), self.port, self.node) for _ in range(num)]

    def getPorts(self) -> Sequence['IOPort']:
        return self.ports

    def value(self) -> List[Any]:
        out = [None for _ in range(len(self.ports))]
        for idx, port in enumerate(self.ports):
            out[idx] = port.value()
        return out

    def addVarPort(self) -> IOPort:
        out = InPort(self.idManager.newPort(), self.port, self.node)
        self.ports.append(out)
        return out

    def remVarPort(self):
        if len(self.ports) <= 1:
            raise NodeDefError("_VarInPort.remVarPort()", "DEV: Cannot rem varport, cnt <= 1")

        port = self.ports.pop()
        link = port.link
        if link is not None:
            port.remLink(link)
            link.pPort.remLink(link)


class _VarOutPort(OutPort):
    def __init__(self, idManager: IDManager, port: Port, node: 'Node'):
        super().__init__(-1, port, node)
        self.ports: List[OutPort] = []
        self.idManager = idManager

    def setVarPorts(self, num: int):
        self.ports = [OutPort(self.idManager.newPort(), self.port, self.node) for _ in range(num)]

    def getPorts(self) -> Sequence['IOPort']:
        return self.ports

    def value(self, v: Any):
        if len(v) != len(self.ports):
            raise ExecutionError(
                "_VarOutPort.value()", f"Invalid number of values len(varports) != len(value), expected {len(self.ports)} got {len(v)}")

        for port, value in zip(self.ports, v):
            port.value(value)

    def addVarPort(self) -> IOPort:
        out = OutPort(self.idManager.newPort(), self.port, self.node)
        self.ports.append(out)
        return out

    def remVarPort(self):
        if len(self.ports) <= 1:
            raise NodeDefError('_VarOutPort.remVarPort()', "DEV: Cannot rem varport, cnt <= 1")

        port = self.ports.pop()
        for link in port.links:
            link.cPort.remLink(link)


def makeInputPort(idManager: IDManager, port: Port, node: 'Node') -> InPort:
    if port.variable:
        return _VarInPort(idManager, port, node)

    return InPort(idManager.newPort(), port, node)


def makeOutputPort(idManager: IDManager, port: Port, node: 'Node') -> OutPort:
    if port.variable:
        return _VarOutPort(idManager, port, node)

    return OutPort(idManager.newPort(), port, node)
