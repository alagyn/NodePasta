from typing import List, Dict
import abc

STRING = '__str'
INT = "__int"
FLOAT = "__flt"
ENUM = "__enum"
BOOL = "__bool"

class NodeArg:
    def __init__(self, name: str, argType: str, display: str=None, default: any = None):
        self.name = name
        self.argType = argType
        self.default = default
        self.display = self.name if display is None else display

class EnumNodeArg(NodeArg):
    def __init__(self, name: str, default: str, values: List[str]):
        super().__init__(name, ENUM, default)
        self.values = values


class NodeArgValue(abc.ABC):
    @abc.abstractmethod
    def get(self) -> any:
        raise NotImplementedError
