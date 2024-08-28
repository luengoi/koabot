import os

from koa import optmanager


CONF_DIR = os.path.join(f"{os.environ.get("XDG_CONFIG_HOME", "~/.config")}", "koabot")


class Options(optmanager.OptManager):
    def __init__(self) -> None:
        super().__init__()

        self.add_option(
            "confdir",
            str,
            CONF_DIR,
            "Location of the configuration files."
        )
        self.add_option(
            "bot_token",
            str,
            "",
            "Discord bot authentication token."
        )
        self.add_option(
            "command_prefix",
            str,
            "!",
            "Prefix that the message must contain to have a command invoked."
        )
        self.add_option(
            "intents.guilds",
            bool,
            False,
            "Whether guild related events are enabled."
        )
        self.add_option(
            "intents.members",
            bool,
            False,
            "Whether guild member related events are enabled."
        )
        self.add_option(
            "intents.moderation",
            bool,
            False,
            "Whether guild moderation related events are enabled."
        )
        self.add_option(
            "intents.emojis_and_stickers",
            bool,
            False,
            "Whether guild emoji and sticker related events are enabled."
        )
        self.add_option(
            "intents.integrations",
            bool,
            False,
            "Whether guild integration related events are enabled."
        )
        self.add_option(
            "intents.webhooks",
            bool,
            False,
            "Whether guild webhook related events are enbaled."
        )
        self.add_option(
            "intents.invites",
            bool,
            False,
            "Whether guild invite related events are enabled."
        )
        self.add_option(
            "intents.voice_states",
            bool,
            False,
            "Whether guild voice state related events are enabled."
        )
        self.add_option(
            "intents.presences",
            bool,
            False,
            "Whether guild presence related events are enabled."
        )
        self.add_option(
            "intents.messages",
            bool,
            False,
            """
            Whether guild and direct message related events are enabled.
            This is a shortcut to set both intents.guild_messages and
            intents.dm_messages.
            """
        )
        self.add_option(
            "intents.guild_messages",
            bool,
            False,
            "Whether guild message related events are enabled."
        )
        self.add_option(
            "intents.dm_messages",
            bool,
            False,
            "Whether direct message related events are enabled."
        )
        self.add_option(
            "intents.reactions",
            bool,
            False,
            """
            Whether guild and direct message reaction related events are enabled.
            This is a shortcut to set both intents.guild_reactions and
            intents.dm_reactions.
            """
        )
        self.add_option(
            "intents.guild_reactions",
            bool,
            False,
            "Whether guild message reaction related events are enabled."
        )
        self.add_option(
            "intents.dm_reactions",
            bool,
            False,
            "Whether dm message reaction related events are enabled."
        )
        self.add_option(
            "intents.typing",
            bool,
            False,
            """
            Whether guild and direct message typing related events are enabled.
            This is a shortcut to set both intents.guild_typing and
            intents.dm_typing.
            """
        )
        self.add_option(
            "intents.guild_typing",
            bool,
            False,
            "Whether guild typing related events are enabled."
        )
        self.add_option(
            "intents.dm_typing",
            bool,
            False,
            "Whether direct message typing related events are enabled."
        )
        self.add_option(
            "intents.message_content",
            bool,
            False,
            """
            Whether message content, attachments, embeds and components will be
            available in messages which do not meet the following criteria:
            (1) The message was sent by the client,
            (2) The message was sent in direct messages,
            (3) The message mentions the client.
            This option requires opting in explicitly via the developer portal
            as well. Bots over 100 guilds will need to apply to Discord verification.
            """
        )
        self.add_option(
            "intents.guild_scheduled_events",
            bool,
            False,
            "Whether guild scheduled event related events are enabled."
        )
        self.add_option(
            "intents.auto_moderation",
            bool,
            False,
            """
            Whether auto moderation related events are enabled.
            This is a shortcut to set both intents.auto_moderation_configuration and
            intents.auto_moderation_execution.
            """
        )
        self.add_option(
            "intents.auto_moderation_configuration",
            bool,
            False,
            "Whether auto moderation configuration related events are enabled."
        )
        self.add_option(
            "intents.auto_moderation_execution",
            bool,
            False,
            "Whether auto moderation execution related events are enabled."
        )
        self.add_option(
            "intents.polls",
            bool,
            False,
            """
            Whether guild and direct messages poll related events are enabled.
            This is a shortcut to set both intents.guild_polls and intents.dm_polls.
            """
        )
        self.add_option(
            "intents.guild_polls",
            bool,
            False,
            "Whether guild poll related events are enabled."
        )
        self.add_option(
            "intents.dm_polls",
            bool,
            False,
            "Whether direct messages poll related events are enabled."
        )
