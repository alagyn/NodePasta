from typing import List, Dict, Iterator, Iterable, Any, Optional, Sequence, Hashable

from nodepasta.errors import ExecutionError, NodeDefError
from nodepasta.utils import Vec
from nodepasta.argtypes import NodeArg, ANY
from nodepasta.ports import Port, InPort, OutPort, Link, makeInputPort, makeOutputPort
from nodepasta.id_manager import IDManager


class _DataMap:
    def __init__(self):
        self._datamap = None

    def __contains__(self, item: Hashable) -> bool:
        if self._datamap is None:
            raise ExecutionError("_DataMap.__contains__()",
                                 "Node is not part of a NodeGraph, no datamap set")
        return item in self._datamap

    def __getitem__(self, item) -> Any:
        if self._datamap is None:
            raise ExecutionError("_DataMap.__getitem__()",
                                 "Node is not part of a NodeGraph, no datamap set")
        return self._datamap[item]

    def __setitem__(self, key, value) -> None:
        if self._datamap is None:
            raise ExecutionError("_DataMap.__setitem__()",
                                 "Node is not part of a NodeGraph, no datamap set")
        self._datamap[key] = value


NODE_ERR_CN = "__ERROR__"


class _ILinkIter(Iterator[Link]):
    def __init__(self, node: 'Node') -> None:
        super().__init__()
        self._portIter: Iterator[InPort] = iter(node.getInputPorts())

    def __next__(self) -> Link:
        x = None
        while x is None:
            x = next(self._portIter).link
        return x


class _OLinkIter(Iterator[Link]):
    def __init__(self, node: 'Node') -> None:
        super().__init__()
        self._listIter: Iterator[OutPort] = iter(node.outputs)
        self._curPortIter: Optional[Iterator[Link]] = None

    def __next__(self) -> Link:
        if self._curPortIter is None:
            self._curPortIter = iter(next(self._listIter))

        while True:
            try:
                return next(self._curPortIter)
            except StopIteration:
                pass

            self._curPortIter = iter(next(self._listIter))


class Node:
    _INPUTS: List[Port] = []
    _OUTPUTS: List[Port] = []
    _ARGS: List[NodeArg] = []
    NODETYPE = NODE_ERR_CN

    DESCRIPTION: str = "No Description Provided"

    _DOC_CACHE = None

    def _init(self, idManager: IDManager, inVarports: Optional[List[int]] = None, outVarPorts: Optional[List[int]] = None):
        self.nodeID = -1

        self.args: Dict[str, NodeArg] = {x.name: x.copy() for x in self._ARGS}

        self.pos = Vec()
        self.datamap: _DataMap = _DataMap()

        if inVarports is None:
            inVarports = [1 for _ in range(len(self._INPUTS))]

        if outVarPorts is None:
            outVarPorts = [1 for _ in range(len(self._OUTPUTS))]

        self.inputs: List[InPort] = []
        for v, x in zip(inVarports, self._INPUTS):
            port = makeInputPort(idManager, x, self)
            port.setVarPorts(v)
            self.inputs.append(port)

        self.outputs: List[OutPort] = []
        for v, x in zip(outVarPorts, self._OUTPUTS):
            port = makeOutputPort(idManager, x, self)
            port.setVarPorts(v)
            self.outputs.append(port)

    def getInputPorts(self) -> Sequence[InPort]:
        out = []
        for x in self.inputs:
            out.extend(x.getPorts())
        return out

    def getOutputPorts(self) -> Sequence[OutPort]:
        out = []
        for x in self.outputs:
            out.extend(x.getPorts())
        return out

    def __iter__(self) -> Iterator[Link]:
        """
        Iterates over child links
        :return: An iterable over this node's child links
        """
        return _OLinkIter(self)

    def incoming(self) -> Iterable[Link]:
        return _ILinkIter(self)

    def resetPorts(self):
        for link in self.incoming():
            link.value = None

    def execute(self) -> None:
        # This is what gets overidden by clients
        raise NotImplementedError

    def unloadArgs(self) -> Dict[str, Any]:
        return {x.name: x.getJSON() for x in self.args.values()}

    def loadArgs(self, args: Dict[str, Any]) -> None:
        for key, val in args.items():
            try:
                self.args[key].loadJSON(val)
            except KeyError:
                raise NodeDefError("Node.loadArgs()",
                                   f"{self} Invalid Argument name {key}:{val}")

    def init(self) -> None:
        """
        Override for logic that needs to run once at startup
        Storing data in the datamap that other nodes need to setup
        should happen here, but make no assumptions about the 
        order that nodes are initialized. Only check for stored values
        in setup()
        """
        raise NotImplementedError

    def setup(self) -> None:
        """
        Resets internals and forces all arguments to take effect.
        Override and use to clear internal state. Will only be called
        after every node has had init() called, so the datamap can be read
        """
        raise NotImplementedError

    def __str__(self):
        return f'{self.__class__.__name__}_{self.nodeID}'

    def docs(self) -> str:
        if self._DOC_CACHE is None:
            self._DOC_CACHE = f'{self.NODETYPE}\n' \
                              f'-----------------------------------------------\n' \
                              f'{self.DESCRIPTION}\n'

            if len(self._ARGS) > 0:
                self._DOC_CACHE += "\nOptions:\n"
                for arg in self._ARGS:
                    self._DOC_CACHE += f' - {arg.display} [{arg.argType}]: {arg.descr}\n\n'

            if len(self._INPUTS) > 0:
                self._DOC_CACHE += "\nInputs:\n"
                for port in self._INPUTS:
                    self._DOC_CACHE += f' - {port.name} [{port.typeStr}]: {port.descr}\n\n'

            if len(self._OUTPUTS) > 0:
                self._DOC_CACHE += "\nOutputs:\n"
                for port in self._OUTPUTS:
                    self._DOC_CACHE += f' - {port.name} [{port.typeStr}]: {port.descr}\n\n'

        return self._DOC_CACHE
