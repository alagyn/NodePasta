class NodeGraphError(Exception):
    """
    Nodepasta Base Exception
    """

    def __init__(self, loc: str, msg: str):
        self.msg = msg
        self.loc = loc

    def __str__(self):
        return self.msg


class NodeTypeError(NodeGraphError):
    """
    Error caused by a bad node type
    """

    def __init__(self, loc: str, msg: str):
        super().__init__(loc, msg)


class NodeDefError(NodeGraphError):
    """
    Error caused by invalid node setup
    """

    def __init__(self, loc: str, msg: str):
        super().__init__(loc, f'NodeDefinitionError: {msg}')


class ExecutionError(NodeGraphError):
    """
    Error caused by other errors during execution
    """

    def __init__(self, loc: str, msg: str):
        super().__init__(loc, f'ExecutionError: {msg}')
