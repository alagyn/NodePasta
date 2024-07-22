from typing import Type

import imgui as im

from nodepasta.argtypes import NodeArg, EnumNodeArg
from nodepasta.argtypes import INT, FLOAT, ENUM


class ImArgHandler:

    @classmethod
    def render(cls, arg: NodeArg) -> bool:
        """
        Render an argument handler.
        Returns true if modified
        """
        raise NotImplementedError


class IntHandler(ImArgHandler):

    @classmethod
    def render(cls, arg: NodeArg) -> bool:
        if arg.value is None:
            arg.value = 0
        ref = im.IntRef(arg.value)
        im.SetNextItemWidth(50)
        if im.DragInt(arg.display, ref):
            arg.value = ref.val
            return True
        return False


class FloatHandler(ImArgHandler):

    @classmethod
    def render(cls, arg: NodeArg) -> bool:
        if arg.value is None:
            arg.value = 0.0
        ref = im.FloatRef(arg.value)
        im.SetNextItemWidth(50)
        if im.DragFloat(arg.display, ref):
            arg.value = ref.val
            return True
        return False


class EnumHandler(ImArgHandler):

    @classmethod
    def render(cls, arg: NodeArg) -> bool:
        if not isinstance(arg, EnumNodeArg):
            raise RuntimeError("Not an enum")
        im.SetNextItemWidth(100)
        out = False
        if im.BeginCombo(arg.display, arg.value):
            for x in arg.enums:
                if im.Selectable(x):
                    arg.value = x
                    out = True
            im.EndCombo()
        return out


def getDefaultArgHandlers() -> dict[str, Type[ImArgHandler]]:
    return {
        INT: IntHandler,
        FLOAT: FloatHandler,
        ENUM: EnumHandler
    }
