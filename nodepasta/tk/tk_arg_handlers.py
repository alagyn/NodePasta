import tkinter as tk
from tkinter import ttk
import abc
from typing import Any

from nodepasta.argtypes import NodeArg, NodeArgValue, EnumNodeArg
from nodepasta.argtypes import STRING, INT, FLOAT, ENUM, BOOL


class TKArgHandler(abc.ABC):
    def __init__(self):
        pass

    @classmethod
    @abc.abstractmethod
    def draw(cls, frame: tk.Frame, arg: NodeArg) -> NodeArgValue:
        raise NotImplementedError


class TKVarArg(NodeArgValue):
    """
    Basic Arg Wrapper to get a value from a tk Variable
    Automatically updates the arg value when the TK variable is written to
    """

    def __init__(self, var: tk.Variable, arg: NodeArg):
        self.var = var
        self.var.trace_add('write', self._written)
        self.arg = arg

    def _written(self, _a, _b, _c):
        """
        Called when the variable is modified
        """
        try:
            self.arg.value = self.get()
        except tk.TclError:
            pass

    def get(self) -> Any:
        return self.var.get()

    def reload(self):
        self.var.set(self.arg.value)


# String
class TKStringArgHandler(TKArgHandler):
    @classmethod
    def draw(cls, frame: tk.Frame, arg: NodeArg) -> NodeArgValue:
        tk.Label(frame, text=f'{arg.display}:').grid(
            row=0, column=0, sticky='nesw')
        var = tk.StringVar(value=arg.value if arg.value is not None else "")
        tk.Entry(frame, textvariable=var).grid(row=0, column=1, sticky='nesw')
        return TKVarArg(var, arg)


# Int
class TKIntArgHandler(TKArgHandler):
    @classmethod
    def draw(cls, frame: tk.Frame, arg: NodeArg) -> NodeArgValue:
        # TODO force int
        tk.Label(frame, text=f'{arg.display}:').grid(
            row=0, column=0, sticky='nesw')
        var = tk.IntVar(value=int(arg.value) if arg.value is not None else 0)
        tk.Spinbox(frame, textvariable=var, increment=1,
                   width=5).grid(row=0, column=1, sticky='nesw')
        return TKVarArg(var, arg)


# Float
class TKFloatArgHandler(TKArgHandler):
    @classmethod
    def draw(cls, frame: tk.Frame, arg: NodeArg) -> NodeArgValue:
        tk.Label(frame, text=f"{arg.display}:").grid(
            row=0, column=0, sticky='nesw')
        var = tk.DoubleVar(value=float(arg.value)
                           if arg.value is not None else 0)
        tk.Spinbox(frame, textvariable=var, increment=1,
                   width=5).grid(row=0, column=1, sticky='nesw')
        return TKVarArg(var, arg)


# Bool
class TKBoolArgHandler(TKArgHandler):
    @classmethod
    def draw(cls, frame: tk.Frame, arg: NodeArg) -> NodeArgValue:
        var = tk.BooleanVar()
        tk.Checkbutton(frame, text=arg.display, variable=var)
        return TKVarArg(var, arg)


# Enum
class TKEnumArgHandler(TKArgHandler):
    @classmethod
    def draw(cls, frame: tk.Frame, arg: EnumNodeArg) -> NodeArgValue:
        tk.Label(frame, text=f"{arg.display}:").grid(
            row=0, column=0, sticky='nesw')
        var = tk.StringVar(value=arg.value if arg.value is not None else "")
        ttk.Combobox(frame, textvariable=var, values=arg.enums, state='readonly',
                     width=10
                     ).grid(row=0, column=1)
        return TKVarArg(var, arg)


# NotFound
class TKNotFoundHandler(TKArgHandler):
    @classmethod
    def draw(cls, frame: tk.Frame, arg: NodeArg) -> NodeArgValue:
        tk.Label(frame, text=f"Arg: {arg.display}, Type: {arg.argType}").grid(
            row=0, column=0, sticky='nesw')
        tk.Label(frame, text=f"Type Handler not found").grid(
            row=1, column=0, sticky='nesw')
        var = tk.Variable(value=arg.value)
        return TKVarArg(var, arg)


DEF_HANDLERS = {
    STRING: TKStringArgHandler,
    INT: TKIntArgHandler,
    FLOAT: TKFloatArgHandler,
    ENUM: TKEnumArgHandler,
    BOOL: TKBoolArgHandler
}
