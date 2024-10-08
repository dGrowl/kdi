import hikari
import lightbulb

from ..bot import kdi
from ..util import get_config_value

CHANNEL_NOT_SET_RESPONSE = r":warning: You haven't set a channel to relay messages into. Use `/relay channel {id}` e.g. `/relay channel 0123456789`."

SET_CHANNEL_SUCCESS_RESPONSE = ":white_check_mark: Successfully set your relay channel."

UNTRUSTED_USER_RESPONSE = ":no_entry: Only trusted users can relay messages. Sorry!"


class RelayPlugin(lightbulb.Plugin):
	_trusted_user_ids: list[hikari.Snowflakeish]
	_user_channel: dict[hikari.Snowflakeish, hikari.Snowflakeish]

	def __init__(self):
		super().__init__("relay")
		self._trusted_user_ids = get_config_value("user", "trusted_ids")
		self._user_channel = {}

		kdi.subscribe(hikari.DMMessageCreateEvent, self.on_dm)

	def is_trusted_user(self, user_id: hikari.Snowflakeish):
		return user_id in self._trusted_user_ids

	async def send_message(self, event: hikari.DMMessageCreateEvent):
		if not event.content or event.content.startswith("/"):
			return
		if (channel_id := self._user_channel.get(event.author_id)) is not None:
			await kdi.rest.create_message(channel_id, event.content)
		else:
			await event.message.respond(
				CHANNEL_NOT_SET_RESPONSE, flags=hikari.MessageFlag.EPHEMERAL
			)

	async def on_dm(self, event: hikari.DMMessageCreateEvent):
		if not event.is_human:
			return
		if not self.is_trusted_user(event.author_id):
			await event.message.respond(
				UNTRUSTED_USER_RESPONSE, flags=hikari.MessageFlag.EPHEMERAL
			)
			return
		await self.send_message(event)

	async def set_channel(self, ctx: lightbulb.SlashContext):
		self._user_channel[ctx.user.id] = ctx.options["channel"].id
		await ctx.respond(
			SET_CHANNEL_SUCCESS_RESPONSE,
			flags=hikari.MessageFlag.EPHEMERAL,
		)


relay_plugin = RelayPlugin()


@lightbulb.Check
async def is_trusted_user(ctx: lightbulb.Context):
	success = relay_plugin.is_trusted_user(ctx.user.id)
	if not success:
		await ctx.respond(UNTRUSTED_USER_RESPONSE, flags=hikari.MessageFlag.EPHEMERAL)
	return success


@relay_plugin.command
@lightbulb.add_checks(lightbulb.human_only, is_trusted_user)
@lightbulb.command("relay", description="Allows you to send messages through the bot.")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def relay_group(_):
	pass


@relay_group.child
@lightbulb.option(
	"channel", "The relevant channel.", hikari.TextableGuildChannel, required=True
)
@lightbulb.command(
	"set-channel",
	description="Sets the channel the bot will send your messages into.",
	inherit_checks=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def set_channel_command(ctx: lightbulb.SlashContext):
	await relay_plugin.set_channel(ctx)
