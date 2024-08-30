import argparse
import logging
import os
import sys

from koa import exceptions
from koa import optmanager
from koa import VERSION
from koa.bot import KoaBot
from koa.options import Options


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(usage="%(prog)s [options]")
    parser.add_argument(
        "--version",
        action="store_true",
        help="show version number and exit"
    )
    parser.add_argument(
        "--set",
        type=str,
        dest="setopt",
        default=[],
        action="append",
        metavar="option[=value]",
        help="""
        Set a configuration value. When the value is omitted, boleans are
        set to true, strings and integers are set to None (if permitted),
        and sequences are emptied. Boolean values can be true, false or
        toggle. Sequences are set using multiple invocations to set for
        the same configuration parameter.
        """
    )
    return parser


def main() -> int | None:
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("discord").setLevel(logging.WARNING)

    options = Options()
    parser = make_parser()
    args = parser.parse_args()

    if args.version:
        print(VERSION)
        sys.exit(0)

    try:
        options.set(*args.setopt)
        optmanager.load_paths(
            options,
            os.path.join(options.confdir, "options.toml"),
            defer=True
        )

        bot = KoaBot(options)
        bot.run()
    except exceptions.OptionError as ex:
        print(f"{sys.argv[0]}: {ex}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
