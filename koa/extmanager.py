import contextlib
import inspect
import logging
import sys
import traceback
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from discord.ext import commands

from koa import events
from koa import exceptions


logger = logging.getLogger(__name__)


def cut_traceback(tb, func_name):
    tb_orig = tb
    for _, _, fname, _ in traceback.extract_tb(tb):
        tb = tb.tb_next
        if fname == func_name:
            break
    return tb or tb_orig


@contextlib.contextmanager
def safecall():
    try:
        yield
    except (exceptions.OptionError):
        raise
    except Exception:
        etype, value, tb = sys.exc_info()
        tb = cut_traceback(tb, "invoke_ext_sync")
        tb = cut_traceback(tb, "invoke_ext")
        assert etype
        assert value
        logger.error(
            f"Extension error: {value}",
            exc_info=(etype, value, tb)
        )


def _ext_name(ext) -> str:
    return getattr(ext, "name", ext.__class__.__name__.lower())


class Loader:
    """
    Class passed to the extensions on the LoadEvent. It allows extensions
    to register options.
    """

    def __init__(self, bot) -> None:
        self.bot = bot

    def add_option(
        self,
        name: str,
        typespec: type,
        default: Any,
        help: str,
        choices: Sequence[str] | None = None
    ) -> None:
        self.bot.options.add_option(name, typespec, default, help, choices)


@dataclass
class LoadEvent(events.Event):
    """
    Event triggered when the extension is loaded.
    """
    loader: Loader


class ExtManager:
    def __init__(self, bot) -> None:
        self.lookup = {}
        self.bot = bot
        self.bot.options.changed.connect(self._configure_all)

    def _configure_all(self, updated: set[str]) -> None:
        self.trigger_sync(events.ConfigureEvent(self.bot.options, updated))

    async def invoke_extension(self, ext, event: events.Event) -> None:
        if func := getattr(ext, event.name, None):
            if callable(func):
                res = func(*event.args())
                if res is not None and inspect.isawaitable(res):
                    await res
            else:
                raise exceptions.ExtManagerError(
                    f"Event handler method {event.name} ({ext}) not callable."
                )

    def invoke_extension_sync(self, ext, event: events.Event) -> None:
        if func := getattr(ext, event.name, None):
            if callable(func):
                func(*event.args())
            else:
                raise exceptions.ExtManagerError(
                    f"Event handler method {event.name} ({ext}) not callable."
                )

    async def trigger(self, event: events.Event) -> None:
        for ext in self.lookup.values():
            try:
                with safecall():
                    await self.invoke_extension(ext, event)
            except exceptions.ExtensionHalt:
                return

    def trigger_sync(self, event: events.Event) -> None:
        for ext in self.lookup.values():
            try:
                with safecall():
                    self.invoke_extension_sync(ext, event)
            except exceptions.ExtensionHalt:
                return

    def __contains__(self, ext) -> bool:
        return _ext_name(ext) in self.lookup

    async def clear(self) -> None:
        """
        Remove all extensions.
        """
        await self.trigger(events.DoneEvent())
        self.lookup = {}

    async def register(self, ext) -> Any:
        """
        Register an extension.
        """
        name = _ext_name(ext)
        if name in self.lookup:
            raise exceptions.ExtManagerError(f"Extension {name} already registered.")

        loader = Loader(self.bot)
        self.invoke_extension_sync(ext, LoadEvent(loader))
        self.lookup[name] = ext
        self.bot.options.process_deferred()

        if isinstance(ext, commands.Cog):
            await self.bot.add_cog(ext)

        self.invoke_extension_sync(ext, events.ReadyEvent(self.bot.options))
        return ext

    async def add(self, *ext) -> None:
        """
        Add extensions to the end of the chain.
        """
        for e in ext:
            await self.register(e)

    async def remove(self, ext) -> None:
        """
        Remove an extension from the chain.
        """
        name = _ext_name(ext)
        if name not in self.lookup:
            raise exceptions.ExtManagerError(f"No such extension: {name}")
        del self.lookup[name]
        await self.invoke_extension(ext, events.DoneEvent())
