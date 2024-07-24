import re

import hikari

from ..bot import kdi
from ..util import get_config_value

CHANNEL_NOT_SET_RESPONSE = r":warning: You haven't set a channel to relay messages into. Use `/relay channel {id}` e.g. `/relay channel 0123456789`."

SET_CHANNEL_SUCCESS_RESPONSE = ":white_check_mark: Successfully set your relay channel."

UNRECOGNIZED_COMMAND_RESPONSE = "Sorry, I didn't recognize that command. :thinking:"

UNTRUSTED_USER_RESPONSE = ":no_entry: Only trusted users can relay messages. Sorry!"


class RelayPlugin:
	_trusted_user_ids: list[hikari.Snowflakeish]
	_user_channel: dict[hikari.Snowflakeish, hikari.Snowflakeish]

	def __init__(self):
		self._trusted_user_ids = get_config_value("user", "trusted_ids")
		self._user_channel = {}

		kdi.subscribe(hikari.DMMessageCreateEvent, self.handle_dm)

	@property
	def user_channel(self):
		return self._user_channel

	def set_channel(
		self, user_id: hikari.Snowflakeish, channel_id: hikari.Snowflakeish
	):
		self._user_channel[user_id] = channel_id

	async def send_help(self, event: hikari.DMMessageCreateEvent):
		await event.message.respond(UNRECOGNIZED_COMMAND_RESPONSE)

	async def relay_message(self, event: hikari.DMMessageCreateEvent):
		if not event.content:
			return
		if channel_id := self._user_channel.get(event.author_id):
			await kdi.rest.create_message(channel_id, event.content)
		else:
			await event.message.respond(CHANNEL_NOT_SET_RESPONSE)

	async def handle_dm(self, event: hikari.DMMessageCreateEvent):
		if not event.content or not event.is_human:
			return
		if event.author_id not in self._trusted_user_ids:
			await event.message.respond(UNTRUSTED_USER_RESPONSE)
			return
		if event.content.startswith("/relay"):
			if match := re.fullmatch(r"/relay channel (\d+)", event.content):
				self.set_channel(event.author_id, int(match.group(1)))
				await event.message.respond(SET_CHANNEL_SUCCESS_RESPONSE)
			else:
				await self.send_help(event)
		else:
			await self.relay_message(event)
