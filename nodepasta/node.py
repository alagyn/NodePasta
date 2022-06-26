import abc
from abc import ABC
from typing import List, Dict, Optional, Iterator, Iterable

from nodepasta.errors import ExecutionError, NodeDefError
from nodepasta.utils import Vec
from nodepasta.argtypes import NodeArg


class LinkAddr:
    def __init__(self, outIdx: int, outVarIdx: int, inIdx: int, inVarIdx: int):
        self.outIdx: int = outIdx
        self.outVarIdx: int = outVarIdx
        self.inIdx: int = inIdx
        self.inVarIdx: int = inVarIdx

    def __str__(self) -> str:
        return f'({self.outIdx}.{self.outVarIdx} -> {self.inIdx}.{self.inVarIdx})'


class Link:
    def __init__(self, linkID: int, parent: 'Node', child: 'Node', linkAddr: LinkAddr):
        self.linkID = linkID
        self.addr = linkAddr
        self.parent = parent
        self.child = child
        self.value = None

    def __str__(self):
        return f'{self.parent} {self.addr} {self.child}'


class IOPort:
    def __init__(self, name: str, typeStr: str, variable=False, cnt=1):
        self.name = name
        self.typeStr = typeStr
        self.variable = variable
        self.cnt = cnt

    def addvarport(self):
        raise NotImplementedError

    def remvarport(self):
        raise NotImplementedError

    def addLink(self, link: Link):
        raise NotImplementedError

class InPort(IOPort):
    def __init__(self, name: str, typeStr: Optional[str] = None, allowAny: bool = False, variable=False, cnt=1):
        super().__init__(name, typeStr, variable, cnt)
        self.allowAny = allowAny
        if (typeStr is None or len(typeStr) == 0) and not allowAny:
            raise NodeDefError(f"InPort.init()", f"No Type defined and allowAny=False: {self}")

        if allowAny:
            self.typeStr = 'Any'

        self.links: List[Optional[Link]] = [None] * self.cnt
        self._listcache = None

    def resetValue(self):
        for link in self.links:
            if link is not None:
                link.value = None

        self._listcache = None

    @property
    def value(self) -> any:
        if self.variable:
            if self._listcache is None:
                self._listcache = [None] * self.cnt
                for idx, link in enumerate(self.links):
                    if link is not None:
                        self._listcache[idx] = link.value

            return self._listcache
        else:
            if self.links[0] is None:
                return None
            else:
                return self.links[0].value

    def __iter__(self) -> Iterator[Link]:
        return iter(self.links)

    def addLink(self, link: Link) -> Optional[Link]:
        if link.addr.inVarIdx > 0 and not self.variable:
            raise NodeDefError("InPort.addlink()",
                               f"{self} Cannot add link with idx {link.addr.inVarIdx}, port is not variable")
        try:
            out = self.links[link.addr.inVarIdx]
        except IndexError:
            out = None

        self.links[link.addr.inVarIdx] = link

        return out

    def remLink(self, link: Link):
        if link.addr.inVarIdx > 0 and not self.variable:
            raise NodeDefError("InPort.remLink()",
                               f"{self} Cannot rem link with idx {link.addr.inVarIdx}, port is not variable")
        self.links[link.addr.inVarIdx] = None

    def copy(self):
        return InPort(self.name, self.typeStr, self.allowAny, self.variable, self.cnt)

    def addvarport(self):
        self.cnt += 1
        self.links.append(None)

    def remvarport(self):
        if self.cnt <= 1:
            raise NodeDefError("InPort.remvarport()", "DEV: Cannot rem varport, cnt <= 1")
        self.cnt -= 1
        if self.links[-1] is not None:
            link = self.links[-1]
            link.parent.outputs[link.addr.outIdx].remLink(link)
            self.remLink(self.links[-1])

        self.links.pop()

    def __str__(self):
        return f'InPort({self.name}, type:{self.typeStr})'


class OutPort(IOPort):
    def __init__(self, name: str, typeStr: str, variable=False, cnt=1):
        super().__init__(name, typeStr, variable, cnt)
        # Var port -> links
        self.links: List[List[Link]] = [[]] * self.cnt
        self.value: any = None
        if self.variable:
            self.value = [None] * cnt

    def setValue(self, value: any, idx: int = 0):
        if not self.variable and idx > 0:
            raise ExecutionError("OutPort.setValue()",
                                 f"{self}: Cannot set value for idx {idx}, port is not variable")

        if self.variable:
            self.value[idx] = value
        else:
            self.value = value

        for link in self.links[idx]:
            link.value = value

    def addLink(self, link: Link):
        if link.addr.outVarIdx > 0 and not self.variable:
            raise NodeDefError("OutPort.addlink()",
                               f"{self} Cannot add link with idx {link.addr.outVarIdx}, port is not variable")
        self.links[link.addr.outVarIdx].append(link)

    def remLink(self, link: Link):
        if link.addr.outVarIdx > 0 and not self.variable:
            raise NodeDefError("OutPort.remlink()",
                               f"{self} Cannot rem link with idx {link.addr.outVarIdx}, port is not variable")
        self.links[link.addr.outVarIdx].remove(link)

    def addvarport(self):
        self.cnt += 1
        self.links.append([])
        self.value.append(None)

    def remvarport(self):
        # TOFIX
        pass

    def __iter__(self):
        return _OPortLinkIter(self)

    def copy(self):
        return OutPort(self.name, self.typeStr, self.variable, self.cnt)

    def __str__(self):
        return f'OutPort({self.name}, type: {self.typeStr})'


class _IPortLinkIter(Iterator[Link]):
    def __init__(self, portIter: Iterator[InPort]):
        self.portIter = portIter
        self.curPortIter = None

    def __next__(self) -> Link:
        if self.curPortIter is None:
            self.curPortIter = iter(next(self.portIter))

        while True:
            try:
                return next(self.curPortIter)
            except StopIteration:
                pass

            self.curPortIter = iter(next(self.portIter))


class _OPortLinkIter(Iterator[Link]):
    def __init__(self, port: OutPort):
        self.listIter = iter(port.links)
        self.curListIter = None

    def __next__(self) -> Link:
        if self.curListIter is None:
            self.curListIter = iter(next(self.listIter))

        while True:
            try:
                return next(self.curListIter)
            except StopIteration:
                pass

            self.curListIter = iter(next(self.listIter))


class _NodeLinkIter(Iterator[Link]):
    def __init__(self, portIter: Iterator[OutPort]):
        self._portIter = portIter
        self._curPIter = None

    def __next__(self) -> Link:
        if self._curPIter is None:
            self._curPIter = iter(next(self._portIter))

        while True:
            try:
                return next(self._curPIter)
            except StopIteration:
                pass

            self._curPIter = iter(next(self._portIter))


class _DataMap:
    def __init__(self):
        self._datamap = None

    def __getitem__(self, item):
        if self._datamap is None:
            raise ExecutionError("_DataMap.__getitem__()", "Node is not part of a NodeGraph, no datamap set")
        return self._datamap[item]

    def __setitem__(self, key, value):
        if self._datamap is None:
            raise ExecutionError("_DataMap.__setitem__()", "Node is not part of a NodeGraph, no datamap set")
        self._datamap[key] = value


NODE_ERR_CN = "__ERROR__"


class Node(ABC):
    _INPUTS: List[InPort] = []
    _OUTPUTS: List[OutPort] = []
    _ARGS: List[NodeArg] = []
    NODETYPE = NODE_ERR_CN

    def __init__(self, *, noneCapable: bool = True):
        self.nodeID = -1

        self._noneCapable = noneCapable

        self.args: Dict[str, NodeArg] = {x.name: x.copy() for x in self._ARGS}

        self.inputs = [x.copy() for x in self._INPUTS]
        self.outputs = [x.copy() for x in self._OUTPUTS]

        self.pos = Vec()

        self.datamap: _DataMap = _DataMap()

    def __iter__(self) -> Iterable[Link]:
        """
        Iterates over child links
        :return: An iterable over this node's child links
        """
        return _NodeLinkIter(iter(self.outputs))

    def incoming(self) -> Iterable[Link]:
        return _IPortLinkIter(iter(self.inputs))

    def resetPorts(self):
        for port in self.inputs:
            port.resetValue()

    @abc.abstractmethod
    def execute(self) -> None:
        raise NotImplementedError

    def unloadArgs(self) -> Dict[str, any]:
        return {x.name: x.getJSON() for x in self.args.values()}

    def loadArgs(self, args: Dict[str, any]) -> None:
        for key, val in args.items():
            try:
                self.args[key].loadJSON(val)
            except KeyError:
                raise NodeDefError("Node.loadArgs()",
                                   f"{self} Invalid Argument name {key}:{val}")

    @abc.abstractmethod
    def setup(self) -> None:
        """
        Resets internals and forces all arguments to take effect
        :return:
        """
        raise NotImplementedError

    def __str__(self):
        return f'{self.__class__.__name__}_{self.nodeID}'
