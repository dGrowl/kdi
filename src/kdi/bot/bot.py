import hikari
import lightbulb

from ..util import get_config_value

INTENTS = (
	hikari.Intents.ALL_UNPRIVILEGED
	| hikari.Intents.GUILD_MEMBERS
	| hikari.Intents.GUILD_MESSAGES
	| hikari.Intents.MESSAGE_CONTENT
)


class KDI(lightbulb.BotApp):
	def __init__(self):
		super().__init__(
			token=get_config_value("bot", "token"),
			intents=INTENTS,
		)


kdi = KDI()
