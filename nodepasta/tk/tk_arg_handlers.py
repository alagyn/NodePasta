import tkinter as tk
import abc
from nodepasta.argtypes import NodeArg, NodeArgValue


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
    """
    def __init__(self, var: tk.Variable):
        self.var = var

    def get(self) -> any:
        return self.var.get()

# String
class TKStringArgHandler(TKArgHandler):
    @classmethod
    def draw(cls, frame: tk.Frame, arg: NodeArg) -> NodeArgValue:
        tk.Label(frame, text=f'{arg.display}:').grid(row=0, column=0, sticky='nesw')
        var = tk.StringVar(value=arg.default if arg.default is not None else "")
        tk.Entry(frame, textvariable=var).grid(row=0, column=1, sticky='nesw')
        return TKVarArg(var)

# Int
class TKIntArgHandler(TKArgHandler):
    @classmethod
    def draw(cls, frame: tk.Frame, arg: NodeArg) -> NodeArgValue:
        tk.Label(frame, text=f'{arg.display}:').grid(row=0, column=0, sticky='nesw')
        var = tk.IntVar(value=arg.default if arg.default is not None else 0)
        tk.Spinbox(frame, textvariable=var, increment=1).grid(row=0, column=1, sticky='nesw')
        return TKVarArg(var)

# Bool
class TKBoolArgHandler(TKArgHandler):
    @classmethod
    def draw(cls, frame: tk.Frame, arg: NodeArg) -> NodeArgValue:
        var = tk.BooleanVar()
        tk.Checkbutton(frame, text=arg.display, variable=var)
        return TKVarArg(var)
