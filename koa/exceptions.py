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


class ExtensionHalt(KoaException):
    """
    Exception that signals that no further extensions in the chain
    should process the event.
    """


class ExtManagerError(KoaException):
    """
    Class for errors related to the extension manager.
    """
