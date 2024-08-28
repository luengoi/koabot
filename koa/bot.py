import asyncio

import discord
from discord.ext import commands

from koa import optmanager


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

    def run(self) -> None:  # type: ignore
        async def runner():
            async with self:
                try:
                    await self.start(self.options.bot_token)
                except discord.PrivilegedIntentsRequired:
                    pass
                finally:
                    if not self.is_closed():
                        await self.close()

        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            pass
        finally:
            # TODO: Close tasks
            pass
