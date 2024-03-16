from typing import Type

import imgui as im

from nodepasta.argtypes import NodeArg, EnumNodeArg
from nodepasta.argtypes import INT, FLOAT, ENUM


class ImArgHandler:

    @classmethod
    def render(cls, arg: NodeArg):
        raise NotImplementedError


class IntHandler(ImArgHandler):

    @classmethod
    def render(cls, arg: NodeArg):
        ref = im.IntRef(arg.value)
        im.SetNextItemWidth(50)
        if im.DragInt(arg.display, ref):
            arg.value = ref.val


class FloatHandler(ImArgHandler):

    @classmethod
    def render(cls, arg: NodeArg):
        ref = im.FloatRef(arg.value)
        im.SetNextItemWidth(50)
        if im.DragFloat(arg.display, ref):
            arg.value = ref.val


class EnumHandler(ImArgHandler):

    @classmethod
    def render(cls, arg: NodeArg):
        if not isinstance(arg, EnumNodeArg):
            raise RuntimeError("Not an enum")
        im.SetNextItemWidth(100)
        if im.BeginCombo(arg.display, arg.value):
            for x in arg.enums:
                if im.Selectable(x):
                    arg.value = x

            im.EndCombo()


def getDefaultArgHandlers() -> dict[str, Type[ImArgHandler]]:
    return {
        INT: IntHandler,
        FLOAT: FloatHandler,
        ENUM: EnumHandler
    }
