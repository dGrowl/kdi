from lightbulb.ext import tasks
import hikari
import lightbulb
import ongaku

from ..util import get_config_value

INTENTS = (
	hikari.Intents.ALL_UNPRIVILEGED
	| hikari.Intents.GUILD_MEMBERS
	| hikari.Intents.GUILD_MESSAGES
	| hikari.Intents.MESSAGE_CONTENT
)


class KDI(lightbulb.BotApp):
	_audio_password: str

	def __init__(self):
		super().__init__(
			token=get_config_value("bot", "token"),
			intents=INTENTS,
		)
		self._audio_password = get_config_value("relay", "audio_password")

	@property
	def audio_password(self):
		return self._audio_password


kdi = KDI()
tasks.load(kdi)

audio_client = ongaku.Client(kdi)
audio_client.create_session("hikari-session", password=kdi.audio_password)
