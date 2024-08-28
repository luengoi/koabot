import contextlib
import copy
import os
import tomllib
import typing
import weakref
from collections.abc import Callable
from collections.abc import Generator
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

import blinker

from koa import exceptions


class _Option:
    def __init__(
        self,
        name: str,
        typespec: type,
        default: Any,
        help: str,
        choices: Sequence[Any] | None
    ) -> None:
        _Option.assert_type(name, default, typespec)
        self.name = name
        self.typespec = typespec
        self._default = default
        self._value = default
        self._is_set = False
        self.help = help
        self.choices = choices

    @property
    def default(self) -> Any:
        return copy.deepcopy(self._default)

    @property
    def value(self) -> Any:
        return copy.deepcopy(self._value)

    @value.setter
    def value(self, value: Any) -> None:
        _Option.assert_type(self.name, value, self.typespec)
        self._is_set = True
        self._value = value

    @property
    def is_set(self) -> bool:
        return self._is_set

    def reset(self) -> None:
        self._is_set = False
        self.value = self._default

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _Option):
            return NotImplemented
        return (
            self.name == other.name
            and self.typespec == other.typespec
            and self.value == other.value
        )

    def __deepcopy__(self, _) -> "_Option":
        opt = _Option(self.name, self.typespec, self.default, self.help, self.choices)
        if self.is_set:
            opt.value = self.value
        return opt

    @classmethod
    def assert_type(cls: type["_Option"], name: str, value: Any, typespec: type) -> None:
        ex = TypeError(f"Expected {typespec} for {name}, but got {type(value)}")
        origin = typing.get_origin(typespec)

        if origin is Union:
            for typ in typing.get_args(typespec):
                try:
                    cls.assert_type(name, value, typ)
                except TypeError:
                    pass
                else:
                    return
            raise ex
        elif origin is Tuple:
            types = typing.get_args(typespec)
            if not isinstance(value, (tuple, list)):
                raise ex
            if len(types) != len(value):
                raise ex
            for i, (val, typ) in enumerate(zip(value, types)):
                cls.assert_type(f"{name}[{i}]", val, typ)
        elif typespec is Any:
            return
        elif not isinstance(value, typespec):
            if typespec is float and isinstance(value, int):
                return
            raise ex


@dataclass
class _OptionSpec:
    """
    Class for options that have not been added yet and therefore, can't be
    processed. Instead of raising an error, we can defer them for later
    processing.
    """
    values: list[str]


class OptManager:
    """
    Manages the program options.

    Whenever options are updated, the `options.changed` signal is
    triggered.
    """
    def __init__(self) -> None:
        self.changed = blinker.signal("options.changed")
        self.errored = blinker.signal("options.errored")
        self.deferred: dict[str, Any] = {}
        self._subscriptions: list[tuple[weakref.ref[Callable[["OptManager", set[str]], None]], set[str]]] = []
        # _options should be the last attribute set - after that, we raise
        # an exception for attribute assignment to unknown options.
        self._options: dict[str, _Option] = {}

    def add_option[T](
        self,
        name: str,
        typespec: type[T],
        default: T,
        help: str,
        choices: Sequence[T] | None = None
    ) -> None:
        self._options[name] = _Option(name, typespec, default, help, choices)
        self.changed.send({name})

    @contextlib.contextmanager
    def rollback(self, updated: set[str], reraise: bool = False) -> Generator[None, "OptManager", None]:
        """
        Creates a context that rolls back the changes if any handler
        in the chain raises an `OptionError`.

        If `reraise` is true, the exception is forwarded. Otherwise it
        will be silenced.
        """
        old = copy.deepcopy(self._options)
        try:
            yield
        except exceptions.OptionError as ex:
            self.errored.send(ex)
            self.__dict__["_options"] = old
            self.changed.send(updated)
            if reraise:
                raise ex

    def subscribe(self, func: Callable[["OptManager", set[str]], None], *options: str) -> None:
        """
        Subscribe a callable to the `options.changed` signal for a specified
        list of options. This method accepts a wildcard at the end of the
        string, which is useful to subscribe to all options of a specific
        namespace (e.g: "intents.*" will subscribe to all options that start
        with "intents.")

        The event will be automatically unsubscribed if the callable goes out
        of scope.
        """
        def func_weakref() -> weakref.ReferenceType:
            if hasattr(func, "__self__"):
                return typing.cast(weakref.ReferenceType, weakref.WeakMethod(func))
            else:
                return weakref.ref(func)

        subscribed_options: set[str] = set()
        for option in options:
            if option.endswith("*"):
                if matched := [o for o in self._options if o.startswith(option[:-1])]:
                    subscribed_options.update(matched)
                else:
                    raise exceptions.OptionError(f"No options matching: {option}")
            else:
                if option not in self._options:
                    raise exceptions.OptionError(f"No such option: {option}")
                subscribed_options.add(option)

        self._subscriptions.append((func_weakref(), subscribed_options))

    def update_known(self, **options: Any) -> dict[str, Any]:
        """
        Update and set all known options.

        Returns a dictionary of unknown options.
        """
        known, unknown = {}, {}
        for option, value in options.items():
            if option in self._options:
                known[option] = value
            else:
                unknown[option] = value

        if updated := set(known):
            with self.rollback(updated, reraise=True):
                for option, value in known.items():
                    self._options[option].value = value
                self.changed.send(updated)

        return unknown

    def update(self, **options: Any) -> None:
        """
        Update and set all known options.
        """
        if unknown := self.update_known(**options):
            raise exceptions.OptionError(f"No such option(s): {", ".join(unknown)}")

    def update_deferred(self, **options: Any) -> None:
        """
        Update and set all known options. Unknown options will be
        deferred for later processing.
        """
        if unknown := self.update_known(**options):
            self.deferred.update(unknown)

    def set(self, *specs: str, defer: bool = False) -> None:
        """
        Process a list of option specifications, in the format "option=value"
        and set the values of the known options.

        Unknown options can be deferred for later processing by setting
        `defer` to True.
        """
        unprocessed: dict[str, list[str]] = {}
        for spec in specs:
            if "=" in spec:
                option, value = spec.split("=", maxsplit=1)
                unprocessed.setdefault(option, []).append(value)
            else:
                unprocessed.setdefault(spec, [])

        processed: dict[str, Any] = {}
        for name in list(unprocessed):
            if name in self._options:
                processed[name] = self._parse_setval(self._options[name], unprocessed.pop(name))

        if defer:
            self.deferred.update(
                { key: _OptionSpec(value) for key, value in unprocessed.items() }
            )
        elif unprocessed:
            raise exceptions.OptionError(f"Unknown option(s): {", ".join(unprocessed)}")

        self.update(**processed)

    def _parse_setval(self, option: _Option, values: list[str]) -> Any:
        """
        Parses the value from the option specification supplied to the
        set method.
        """
        if option.typespec is Sequence[str]:
            return values
        if len(values) > 1:
            raise exceptions.OptionError(f"Received multiple values for {option.name}: {values}")

        value_str = values[0] if values else None
        if option.typespec in (str, Optional[str]):
            if option.typespec is str and value_str is None:
                raise exceptions.OptionError(f"Configuration is required: {option.name}")
            return value_str
        elif option.typespec in (int, Optional[int]):
            if value_str:
                try:
                    return int(value_str)
                except ValueError:
                    raise exceptions.OptionError(f"Not an integer: {option.name}")
            elif option.typespec is int:
                raise exceptions.OptionError(f"Configuration is required: {option.name}")
            return None
        elif option.typespec is bool:
            if not value_str or value_str == "true":
                return True
            elif value_str == "false":
                return False
            raise exceptions.OptionError("Boolean must be true, false or have the value omitted.")
        raise NotImplementedError(f"Unsupported configuration type: {option.typespec}")

    def process_deferred(self) -> None:
        """
        Process options that were deferred in previous calls to set or
        update, and have since been added.
        """
        update: dict[str, Any] = {}
        for name, value in self.deferred.items():
            if name in self._options:
                if isinstance(value, _OptionSpec):
                    value = self._parse_setval(self._options[name], value.values)
                update[name] = value

        self.update(**update)
        for key in update:
            del self.deferred[key]

    def bind(self, instance: Any, attr: str, option: str) -> Callable[["OptManager", Set[str]], None]:
        """
        Binds the specified attribute to changes of the specified option.

        Returns a callable that contains the subscription to the option
        changes. When the callable goes out of scope, the binding will
        be removed.
        """
        def subscription(optmanager: OptManager, updated: set[str]) -> None:
            if option in updated:
                setattr(instance, attr, getattr(optmanager, attr))

        self.subscribe(subscription, option)
        return subscription

    def default(self, option: str) -> Any:
        """
        Return the default value of the specified option, if exists.
        """
        if option in self._options:
            return self._options[option].default
        else:
            raise exceptions.OptionError(f"No such option: {option}")

    def is_set(self, option: str) -> bool:
        """
        Return whether or not the specified option has been set.
        """
        if option in self._options:
            return self._options[option].default
        else:
            raise exceptions.OptionError(f"No such option: {option}")

    def __deepcopy__(self, memodict=None) -> "OptManager":
        cp = OptManager()
        cp.__dict__["_options"] = copy.deepcopy(self._options, memodict)
        return cp

    __copy__ = __deepcopy__

    def __getattr__(self, attr: str) -> Any:
        if attr in self._options:
            return self._options[attr].value

        namespace = {
            o.removeprefix(f"{attr}.") for o in self._options if o.startswith(f"{attr}.")
        }
        if namespace:
            return OptNamespace(attr, self, namespace)
        raise exceptions.OptionError(f"No such configuration: {attr}")

    def __contains__(self, key: str) -> bool:
        return key in self._options


@dataclass
class OptNamespace:
    _prefix: str
    _manager: OptManager
    _options: set[str]

    def __setattr__(self, attr: str, value: Any) -> None:
        if "_options" not in self.__dict__:
            super().__setattr__(attr, value)
        else:
            setattr(self._manager, f"{self._prefix}.{attr}", value)

    def __getattr__(self, attr: str) -> Any:
        return getattr(self._manager, f"{self._prefix}.{attr}")

    def options(self) -> Generator[_Option, None, None]:
        return (self._manager._options[f"{self._prefix}.{opt}"] for opt in self._options)


def flatten_options(toml: dict[str, Any]) -> dict[str, Any]:
    options = {}
    for key, val in toml.items():
        if isinstance(val, dict):
            options.update({ f"{key}.{k}": v for (k, v) in flatten_options(val).items() })
        elif isinstance(val, str):
            options[key] = os.path.expandvars(val)
        else:
            options[key] = val
    return options


def parse(text: str) -> dict[str, Any]:
    if not text:
        return {}
    try:
        toml = tomllib.loads(text)
        options = flatten_options(toml)
    except tomllib.TOMLDecodeError as ex:
        raise exceptions.OptionError(f"Error parsing configuration: {ex}")
    return options


def load(options: OptManager, text: str, defer: bool = False) -> None:
    """
    Load options from text, overwriting parameters that are already set.
    """
    parsed = parse(text)
    if defer:
        options.update_deferred(**parsed)
    else:
        options.update(**parsed)


def load_paths(options: OptManager, *paths: Path | str) -> None:
    """
    Load paths in order. Paths that don't exist will be ignored.
    """
    for path in paths:
        path = Path(path).expanduser()
        if path.exists() and path.is_file():
            with path.open(encoding="utf-8") as f:
                try:
                    text = f.read()
                except UnicodeDecodeError as ex:
                    raise exceptions.OptionError(f"Error reading {path}: {ex}")
            try:
                load(options, text)
            except exceptions.OptionError as ex:
                raise exceptions.OptionError(f"Error reading {path}: {ex}")
