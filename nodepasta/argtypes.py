from typing import List, Any
import abc

STRING = 'String'
INT = "Int"
FLOAT = "Float"
ENUM = "Enum"
BOOL = "Bool"
ANY = "ANY"


class NodeArg:
    def __init__(self, name: str, argType: str, display: str, descr: str, value: Any = None):
        self.descr = descr
        self.name = name
        self.argType = argType
        self.value = value
        self.display = self.name if display is None else display

    def copy(self) -> 'NodeArg':
        return NodeArg(self.name, self.argType, self.display, self.descr, self.value)

    def getJSON(self) -> Any:
        return self.value

    def loadJSON(self, value: Any):
        self.value = value

    def __str__(self) -> str:
        return f'NodeArg Name: "{self.name}", Type: "{self.argType}",  Val: "{self.value}"'


class EnumNodeArg(NodeArg):
    def __init__(self, name: str, display: str, descr: str, value: str, enums: List[str]):
        super().__init__(name, ENUM, display, descr, value)
        self.enums = enums

    def copy(self) -> 'NodeArg':
        return EnumNodeArg(self.name, self.display, self.descr, self.value, self.enums)


class NodeArgValue(abc.ABC):
    @abc.abstractmethod
    def get(self) -> Any:
        raise NotImplementedError
