import pytest

from koa import optmanager


class TD(optmanager.OptManager):
    def __init__(self) -> None:
        super().__init__()
        self.add_option("one", str, "done", "help")
        self.add_option("two", str, "dtwo", "help")


class TD2(TD):
    def __init__(self) -> None:
        super().__init__()
        self.add_option("three", str, "dthree", "help")
        self.add_option("four", str, "dfour", "help")
        self.add_option("one", str, "xone", "help")


def test_defaults() -> None:
    o = TD2()
    defaults = {
        "two": "dtwo",
        "three": "dthree",
        "four": "dfour",
    }

    for k, v in defaults.items():
        assert o.default(k) == v

    assert o.is_set("one")
    assert "xone" == o.one

    new_values = {
        "two": "xtwo",
        "three": "xthree",
        "four": "xfour"
    }
    o.update(**new_values)
    for k, v in new_values.items():
        assert o.is_set(k)
        assert v == getattr(o, k)
