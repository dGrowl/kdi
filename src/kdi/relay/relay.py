from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import asyncio

import hikari
import lightbulb
import ongaku
import pyttsx3

from ..bot import audio_client, kdi
from ..util import get_cache_dir, get_config_value, log

CHANNEL_NOT_SET_RESPONSE = r":warning: You haven't set a channel to relay messages into. Use `/relay channel {id}` e.g. `/relay channel 0123456789`."

SET_CHANNEL_SUCCESS_RESPONSE = ":white_check_mark: Successfully set your relay channel."

UNTRUSTED_USER_RESPONSE = ":no_entry: Only trusted users can relay messages. Sorry!"

NON_GUILD_MESSAGE_RESPONSE = ":no_entry: This command can only be run in a guild."

NOT_CONNECTED_RESPONSE = ":warning: Not currently connected to a channel."

SUCCESSFUL_DISCONNECT_RESPONSE = ":white_check_mark: Successfully left the channel."

SUCCESSFUL_SPEAK_RESPONSE = ":white_check_mark: Successfully spoke message."


def SUCCESSFUL_CONNECT_RESPONSE(channel: str):
	return f":white_check_mark: Joined {channel}."


class TTSClient:
	_CACHE_FILE_NAME = "tts.mp3"
	_DEFAULT_RATE = 165
	_MAX_WORKERS = 1

	def __init__(self):
		self.engine = pyttsx3.init()
		self.engine.setProperty("rate", self._DEFAULT_RATE)
		self.executor = ThreadPoolExecutor(max_workers=self._MAX_WORKERS)
		self.out_path = (get_cache_dir() / self._CACHE_FILE_NAME).absolute().as_posix()
		self.load_config_voice()

	def load_config_voice(self):
		desired = get_config_value("relay", "voice")
		desired_lower = desired.lower()
		for available in self.engine.getProperty("voices"):
			if desired_lower in available.id.lower():
				self.engine.setProperty("voice", available.id)
				return
		log.warning(f"Failed to load specified voice '{desired}'. Available options:")
		for available in self.engine.getProperty("voices"):
			log.warning("\t* " + available.id)

	def save_sync(self, message: str):
		self.engine.save_to_file(message, self.out_path)
		self.engine.runAndWait()

	async def create_track(self, message: str):
		track_path = await self.render(message)
		load_result = await audio_client.rest.load_track(track_path)
		if load_result is None:
			raise FileNotFoundError(track_path)
		track: Optional[ongaku.Track] = None
		if isinstance(load_result, ongaku.Playlist):
			track = load_result.tracks[0]
		elif isinstance(load_result, ongaku.Track):
			track = load_result
		else:
			track = load_result[0]
		return track

	async def render(self, message: str):
		await asyncio.get_running_loop().run_in_executor(
			self.executor, self.save_sync, message
		)
		return self.out_path


class RelayPlugin(lightbulb.Plugin):
	_trusted_user_ids: list[hikari.Snowflakeish]
	_tts: TTSClient
	_user_channel: dict[hikari.Snowflakeish, hikari.Snowflakeish]

	def __init__(self):
		super().__init__("relay")
		self._trusted_user_ids = get_config_value("user", "trusted_ids")
		self._tts = TTSClient()
		self._user_channel = {}

		kdi.subscribe(hikari.DMMessageCreateEvent, self.on_dm)

	@staticmethod
	def _get_player(guild_id: hikari.Snowflakeish):
		try:
			return audio_client.fetch_player(guild_id)
		except Exception:
			return audio_client.create_player(guild_id)

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

	async def join(self, ctx: lightbulb.SlashContext):
		channel: hikari.GuildVoiceChannel = ctx.options["channel"]
		if ctx.guild_id is None or channel.name is None:
			return
		player = self._get_player(ctx.guild_id)

		await player.connect(channel, deaf=False)
		await ctx.respond(
			SUCCESSFUL_CONNECT_RESPONSE(channel.name),
			flags=hikari.MessageFlag.EPHEMERAL,
		)

	async def leave(self, ctx: lightbulb.SlashContext):
		if ctx.guild_id is None:
			return
		player = self._get_player(ctx.guild_id)
		if not player.connected:
			await ctx.respond(
				NOT_CONNECTED_RESPONSE,
				flags=hikari.MessageFlag.EPHEMERAL,
			)
			return
		await player.disconnect()
		await ctx.respond(
			SUCCESSFUL_DISCONNECT_RESPONSE,
			flags=hikari.MessageFlag.EPHEMERAL,
		)

	async def speak(self, ctx: lightbulb.SlashContext):
		if ctx.guild_id is None:
			return
		player = self._get_player(ctx.guild_id)
		if not player.connected:
			return

		message = ctx.options["message"]
		track = await self._tts.create_track(message)
		await player.play(track)
		await ctx.respond(
			SUCCESSFUL_SPEAK_RESPONSE,
			flags=hikari.MessageFlag.EPHEMERAL,
		)


relay_plugin = RelayPlugin()


@lightbulb.Check
async def is_trusted_user(ctx: lightbulb.Context):
	success = relay_plugin.is_trusted_user(ctx.user.id)
	if not success:
		await ctx.respond(UNTRUSTED_USER_RESPONSE, flags=hikari.MessageFlag.EPHEMERAL)
	return success


@lightbulb.Check
async def is_sent_from_guild(ctx: lightbulb.Context):
	if ctx.guild_id is None:
		await ctx.respond(
			NON_GUILD_MESSAGE_RESPONSE, flags=hikari.MessageFlag.EPHEMERAL
		)
		return False
	return True


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


@relay_group.child
@lightbulb.add_checks(is_sent_from_guild)
@lightbulb.option(
	"channel", "The relevant channel.", hikari.GuildVoiceChannel, required=True
)
@lightbulb.command(
	"join",
	description="Requests that the bot join a voice channel.",
	inherit_checks=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def join_command(ctx: lightbulb.SlashContext):
	await relay_plugin.join(ctx)


@relay_group.child
@lightbulb.add_checks(is_sent_from_guild)
@lightbulb.command(
	"leave",
	description="Requests that the bot leaves its current voice channel.",
	inherit_checks=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def leave_command(ctx: lightbulb.SlashContext):
	await relay_plugin.leave(ctx)


@relay_group.child
@lightbulb.add_checks(is_sent_from_guild)
@lightbulb.option(
	"message",
	"The message to speak.",
	str,
	required=True,
	min_length=1,
	max_length=1024,
)
@lightbulb.command(
	"speak",
	description="Sends TTS to the current voice channel.",
	inherit_checks=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def speak_command(ctx: lightbulb.SlashContext):
	await relay_plugin.speak(ctx)
