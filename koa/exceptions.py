class KoaException(Exception):
    """
    Base class for custom exceptions.
    """
    def __init__(self, message: str | None = None) -> None:
        super().__init__(message)


class OptionError(KoaException):
    """
    Class for errors related to options.
    """
