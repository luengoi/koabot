import asyncio
import logging

import discord
from discord.ext import commands

from koa import extmanager
from koa import optmanager
from koa.ext import log


logger = logging.getLogger(__name__)


def _get_intents(options: optmanager.OptManager) -> discord.Intents:
    """
    Return the configured gateway intents.
    """
    intents = discord.Intents.default()
    for intent in options.intents.options():
        if intent.is_set:
            setattr(intents, intent.name.rsplit(".", 1)[-1], intent.value)
    return intents


class KoaBot(commands.Bot):
    def __init__(self, options: optmanager.OptManager) -> None:
        super().__init__(command_prefix=options.command_prefix, intents=_get_intents(options))
        self.options = options
        self.extmanager = extmanager.ExtManager(self)

    def run(self) -> None:  # type: ignore
        async def runner():
            async with self:
                try:
                    await self.extmanager.add(log.Log())
                    await self.start(self.options.bot_token)
                except discord.PrivilegedIntentsRequired:
                    logger.critical(
                        "Privileged intents are not explicitly set in the developer portal."
                    )
                except discord.LoginFailure:
                    logger.critical("Invalid token.")
                except Exception:
                    logger.critical("Fatal error", exc_info=True)
                finally:
                    if not self.is_closed():
                        await self.close()

        try:
            asyncio.run(runner())
        except (KeyboardInterrupt, SystemExit):
            logger.info("Received termination signal.")
        finally:
            # TODO: Close tasks
            pass

    async def on_connect(self) -> None:
        logger.debug("Connected to gateway.")
