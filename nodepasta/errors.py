class NodeGraphError(Exception):
    def __init__(self, loc:str, msg: str):
        self.msg = msg
        self.loc = loc

    def __str__(self):
        return self.msg


class NodeTypeError(NodeGraphError):
    def __init__(self, loc:str, msg: str):
        super().__init__(loc, msg)


class NodeDefError(NodeGraphError):
    def __init__(self, loc: str, msg: str):
        super().__init__(loc, f'NodeDefinitionError: {msg}')


class ExecutionError(NodeGraphError):
    def __init__(self, loc: str, msg: str):
        super().__init__(loc, f'ExecutionError: {msg}')
