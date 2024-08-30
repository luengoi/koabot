import re
import warnings
from dataclasses import dataclass
from dataclasses import fields
from dataclasses import is_dataclass
from typing import Any
from typing import ClassVar
from typing import Self

from koa import optmanager


class Event:
    """
    Base class for all events.
    """
    name: ClassVar[str]

    def args(self) -> list[Any]:
        return [getattr(self, f.name) for f in fields(self)]  # type: ignore[arg-type]

    def __new__(cls, *args, **kwargs) -> Self:
        if cls is Event:
            raise TypeError("Event may not be instantiated directly.")
        if not is_dataclass(cls):
            raise TypeError("Event subclass is not a dataclass.")
        return super().__new__(cls)

    def __init_subclass__(cls) -> None:
        if cls.__dict__.get("name", None) is None:
            # Normalize .name attribue. RunSomeActionEvent -> run_some_action
            name = re.sub("Event$", "", cls.__name__)
            cls.name = re.sub("(?!^)([A-Z]+)", r"_\1", name).lower()
        if other := all_events.get(cls.name, None) is not None:
            warnings.warn(
                f"Two conflicting event classes for {cls.name}: {cls} and {other}",
                RuntimeWarning
            )
        if not cls.name:
            return
        all_events[cls.name] = cls
        cls.__hash__ = object.__hash__
        cls.__eq__ = object.__eq__


all_events: dict[str, type[Event]] = {}


@dataclass
class ConfigureEvent(Event):
    """
    Event triggered when options change. The updated argument is a set
    of strings containing the keys of all the changed options.
    """
    options: optmanager.OptManager
    updated: set[str]


@dataclass
class DoneEvent(Event):
    """
    Event triggered when before the extension is removed.
    """


@dataclass
class ReadyEvent(Event):
    """
    Event triggered when the extension has been loaded and configured
    with the initial options from command-line or the configuration
    file.
    """
    options: optmanager.OptManager
