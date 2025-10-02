from abc import abstractmethod


class TPError(Exception):
    '''Error results from text processor'''

    # enumerations for error code
    # 0 is reserved for success
    TPE_TEXT_TOO_LONG = 1
    @abstractmethod
    def error_code(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError


class TextLengthError(TPError):
    def __init__(self, limit: int):
        self.limit = limit
        super().__init__()

    def error_code(self) -> int:
        return self.TPE_TEXT_TOO_LONG

    def __str__(self) -> str:
        return 'Length of the input text exceeded limitation: limit({})'.format(self.limit)
