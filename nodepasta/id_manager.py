class IDManager:
    def __init__(self) -> None:
        self._nodeIDGen = -1
        self._portIDGen = -1
        self._linkIDGen = -1

    def reset(self):
        self._nodeIDGen = -1
        self._portIDGen = -1
        self._linkIDGen = -1

    def newNode(self) -> int:
        self._nodeIDGen += 1
        return self._nodeIDGen

    def newPort(self) -> int:
        self._portIDGen += 1
        return self._portIDGen

    def newLink(self) -> int:
        self._linkIDGen += 1
        return self._linkIDGen
