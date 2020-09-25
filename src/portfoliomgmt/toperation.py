import enum


class TOperation(str, enum.Enum):

    BEAR = "BEAR"
    BULL = "BULL"

    def __str__(self):
        return self.value
