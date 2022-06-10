class NodeGraphError(Exception):
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return self.msg


class NodeTypeError(NodeGraphError):
    def __init__(self, msg: str):
        super().__init__(msg)


class NodeDefError(NodeGraphError):
    def __init__(self, msg: str):
        super().__init__(f'NodeDefinitionError: {msg}')


class ExecutionError(NodeGraphError):
    def __init__(self, msg: str):
        super().__init__(f'ExecutionError: {msg}')