import hikari

from ..util import get_config_value

INTENTS = (
	hikari.Intents.ALL_UNPRIVILEGED
	| hikari.Intents.GUILD_MEMBERS
	| hikari.Intents.GUILD_MESSAGES
	| hikari.Intents.MESSAGE_CONTENT
)


def build_bot():
	return hikari.GatewayBot(
		token=get_config_value("bot", "token"),
		intents=INTENTS,
	)


kdi = build_bot()
