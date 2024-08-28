"""
Koa: Versatile extensible Discord bot.

Talk to your bot like an AI assistant by enabling the 'assistant' extension.
"""

__all__ = [
    "VERSION",
    "__version__"
]


def _version() -> str:
    """
    Returns the KoaBot version from multiple methods.

    Currently, only static versioning is available.
    """
    return "0.0.1.dev"


VERSION = __version__ = _version()
