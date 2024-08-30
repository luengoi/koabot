import logging
import sys
from typing import IO

from colorama import Fore
from colorama import Style
from discord.ext import commands

from koa import extmanager
from koa.options import Options
from koa.utils import vt_codes


LOG_LEVELS = [
    "debug",
    "info",
    "warn",
    "error",
]

LOG_COLORS = {
    logging.DEBUG: Fore.LIGHTBLACK_EX,
    logging.WARN: Fore.YELLOW,
    logging.ERROR: Fore.RED
}


class Log(commands.Cog):
    def __init__(self, out: IO[str] | None = None) -> None:
        self.handler = KoaLogHandler(out)
        self.handler.install()

    def load(self, loader: extmanager.Loader) -> None:
        loader.add_option(
            "log.level",
            str,
            "info",
            "The logging level.",
            choices=LOG_LEVELS
        )
        self.handler.setLevel(logging.INFO)

    def configure(self, options: Options, updated: set[str]) -> None:
        if "log.level" in updated:
            self.handler.setLevel(options.log.level.upper())


class KoaLogHandler(logging.Handler):
    def __init__(self, out: IO[str] | None = None) -> None:
        super().__init__()
        self.file: IO[str] = out or sys.stdout
        self.formatter = KoaFormatter(vt_codes.is_supported(self.file))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            print(self.format(record), file=self.file)
        except OSError:
            # Can't print, exit immediately
            sys.exit(1)

    def install(self) -> None:
        logging.getLogger().addHandler(self)

    def remove(self) -> None:
        logging.getLogger().removeHandler(self)


class KoaFormatter(logging.Formatter):
    default_time_format = "%H:%M:%S"
    default_msec_format = "%s.%03d"

    def __init__(self, colorize: bool) -> None:
        super().__init__()
        self.colorize = colorize

    @property
    def time(self) -> str:
        return "[%s]" if not self.colorize else f"[{Fore.LIGHTBLACK_EX}%s{Fore.RESET}]"

    def format(self, record: logging.LogRecord) -> str:
        time = self.formatTime(record)
        message = record.getMessage()
        if record.exc_info:
            message = f"{message}\n{self.formatException(record.exc_info)}"
        if self.colorize:
            message = f"{LOG_COLORS.get(record.levelno, "")}{message}{Style.RESET_ALL}"
        return f"{time} {message}"
