from typing import List
import abc

STRING = '__str'
INT = "__int"
FLOAT = "__flt"
ENUM = "__enum"
BOOL = "__bool"

class NodeArg:
    def __init__(self, name: str, argType: str, display: str=None, value: any = None):
        self.name = name
        self.argType = argType
        self.value = value
        self.display = self.name if display is None else display

    def copy(self) -> 'NodeArg':
        return NodeArg(self.name, self.argType, self.display, self.value)

    def getJSON(self) -> any:
        return self.value

    def loadJSON(self, value: any):
        self.value = value


class EnumNodeArg(NodeArg):
    def __init__(self, name: str, default: str, values: List[str]):
        super().__init__(name, ENUM, default)
        self.values = values


class NodeArgValue(abc.ABC):
    @abc.abstractmethod
    def get(self) -> any:
        raise NotImplementedError
