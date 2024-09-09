from typing import Callable

import hikari
import lightbulb

from ..bot import kdi
from ..util import check_flag, get_config_value, TEST_DATA_FLAG
from .cores_message import CoresMessage
from .players_message import (
	PlayersMessage,
	PLAYER_AVAILABLE_ID,
	PLAYER_UNAVAILABLE_ID,
)
from .teams_message import TeamsMessage
from .teams_state import KeySet, TeamsState

UNTRUSTED_USER_RESPONSE = ":no_entry: Only trusted users can make teams. Sorry!"

SELF_DESTRUCT_FOOTER = "This message will self-destruct momentarily."

SELF_DESTRUCT_TIME_SECS = 6.0


def get_usernames_from_options(options: lightbulb.OptionsProxy):
	return {
		v.username
		for _, v in options.items()
		if isinstance(v, hikari.InteractionMember)
	}


class TeamsPlugin(lightbulb.Plugin):
	_color: str
	_cores_message: CoresMessage
	_players_message: PlayersMessage
	_state: TeamsState
	_trusted_user_ids: set[int]

	def __init__(self):
		super().__init__("teams")
		self._color = get_config_value("bot", "color")
		self._cores_message = CoresMessage()
		self._players_message = PlayersMessage()
		self._state = TeamsState()
		self._trusted_user_ids = get_config_value("user", "trusted_ids")

		kdi.subscribe(hikari.GuildMessageDeleteEvent, self.on_gm_delete)
		kdi.subscribe(hikari.InteractionCreateEvent, self.on_interaction)

	@property
	def cores(self):
		return self._state._cores

	@property
	def players(self):
		return self._state._players - self._state._cores

	def is_trusted_user(self, user_id: hikari.Snowflakeish):
		return user_id in self._trusted_user_ids

	async def start(self, ctx: lightbulb.SlashContext):
		self._state.reset()
		if check_flag(TEST_DATA_FLAG):
			self.load_test_data()
		if ctx.options["auto-core"]:
			self._state.add_core({ctx.user.username})
		await self._cores_message.create(ctx, self.cores)
		await self._players_message.create(ctx, self.players)

	def load_test_data(self):
		for c in map(set, ["xy", "z"]):
			self._state.add_core(c)
		for p in map(set, ["a", "b", "cd", "e", "f", "ghi"]):
			self._state.add_player(p)

	def build_embed(self, title: str, description: str, success: bool):
		status_icon = ":white_check_mark:" if success else ":stop_sign:"
		embed = hikari.Embed(
			color=self._color,
			description=description,
			title=f"{status_icon} {title}",
		)
		embed.set_footer(SELF_DESTRUCT_FOOTER)
		return embed

	async def handle_player_command(
		self,
		ctx: lightbulb.SlashContext,
		action: str,
		player_type: str,
		success_msg: str,
		error_msg: str,
		state_method: Callable[[KeySet], bool],
	):
		names = get_usernames_from_options(ctx.options)
		if state_method(names):
			embed = self.build_embed(
				f"{action} {player_type}: Success",
				f"**{' / '.join(names)}** {success_msg}",
				True,
			)
			await self._cores_message.update(self.cores)
			await self._players_message.update(self.players)
		else:
			embed = self.build_embed(
				f"{action} {player_type}: Failure",
				f"**{' / '.join(names)}** {error_msg}",
				False,
			)
		await ctx.respond(
			hikari.ResponseType.MESSAGE_CREATE,
			delete_after=SELF_DESTRUCT_TIME_SECS,
			embed=embed,
		)

	async def add_core(self, ctx: lightbulb.SlashContext):
		await self.handle_player_command(
			ctx,
			action="Add",
			player_type="Core",
			success_msg="has been added.",
			error_msg="overlaps with existing cores.",
			state_method=self._state.add_core,
		)

	async def remove_core(self, ctx: lightbulb.SlashContext):
		await self.handle_player_command(
			ctx,
			action="Remove",
			player_type="Core",
			success_msg="is no longer a core.",
			error_msg="is not currently a core.",
			state_method=self._state.remove_core,
		)

	async def add_player(self, ctx: lightbulb.SlashContext):
		await self.handle_player_command(
			ctx,
			action="Add",
			player_type="Player",
			success_msg="has been added.",
			error_msg="overlaps with existing players.",
			state_method=self._state.add_player,
		)

	async def remove_player(self, ctx: lightbulb.SlashContext):
		await self.handle_player_command(
			ctx,
			action="Remove",
			player_type="Player",
			success_msg="is no longer a playerset.",
			error_msg="is not currently a playerset.",
			state_method=self._state.remove_player,
		)

	async def generate(self, ctx: lightbulb.SlashContext):
		teams = self._state.generate(ctx.options["max-size"])
		message = TeamsMessage()
		await ctx.respond(embed=message.build_embed(self._state.round_number, teams))

	async def check_players_interaction(self, interaction: hikari.ComponentInteraction):
		if not self._players_message.matches(interaction.message):
			return
		modified = False
		player = {interaction.user.username}
		if interaction.custom_id == PLAYER_AVAILABLE_ID:
			modified |= self._state.add_player(player)
		elif interaction.custom_id == PLAYER_UNAVAILABLE_ID:
			modified |= self._state.remove_player(player)
		if modified:
			await self._cores_message.update(self.cores)
			await self._players_message.update(self.players)
		await interaction.create_initial_response(
			hikari.ResponseType.DEFERRED_MESSAGE_UPDATE
		)

	async def on_gm_delete(self, event: hikari.GuildMessageDeleteEvent):
		await self._cores_message.check_delete(event)
		await self._players_message.check_delete(event)

	async def on_interaction(self, event: hikari.InteractionCreateEvent):
		if (
			not isinstance(event.interaction, hikari.ComponentInteraction)
			or event.interaction.user.is_bot
		):
			return
		await self.check_players_interaction(event.interaction)


teams_plugin = TeamsPlugin()


@lightbulb.Check
async def is_trusted_user(ctx: lightbulb.Context):
	success = teams_plugin.is_trusted_user(ctx.user.id)
	if not success:
		await ctx.respond(UNTRUSTED_USER_RESPONSE, flags=hikari.MessageFlag.EPHEMERAL)
	return success


@teams_plugin.command
@lightbulb.add_checks(lightbulb.human_only, is_trusted_user)
@lightbulb.command(
	"teams", description="Allows you to generate randomized teams of players."
)
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def teams_group(_):
	pass


@teams_group.child
@lightbulb.option(
	"auto-core",
	description="Add the command executor to cores. (default=True)",
	type=bool,
	default=True,
)
@lightbulb.command(
	"start",
	description="Starts a new session of the teams system.",
	inherit_checks=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def start_command(ctx: lightbulb.SlashContext):
	await teams_plugin.start(ctx)


MAX_PLAYERS = 4

PLAYER_OPTIONS = [
	lightbulb.option(
		f"player-{i}",
		description=f"The {ordinal} player who will be in the core.",
		default=None,
		required=(i == 1),
		type=hikari.User,
	)
	for (i, ordinal) in zip(
		range(1, MAX_PLAYERS + 1),
		["first", "second", "third", "fourth"],
	)
]


def player_options(command: lightbulb.CommandLike):
	for o in PLAYER_OPTIONS:
		command = o(command)
	return command


@teams_group.child
@player_options
@lightbulb.command(
	"add-core",
	description="Adds a core to the teams system.",
	inherit_checks=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def add_core_command(ctx: lightbulb.SlashContext):
	await teams_plugin.add_core(ctx)


@teams_group.child
@player_options
@lightbulb.command(
	"remove-core",
	description="Removes a core from the teams system.",
	inherit_checks=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def remove_core_command(ctx: lightbulb.SlashContext):
	await teams_plugin.remove_core(ctx)


@teams_group.child
@player_options
@lightbulb.command(
	"add-player",
	description="Adds a playerset to the teams system.",
	inherit_checks=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def add_player_command(ctx: lightbulb.SlashContext):
	await teams_plugin.add_player(ctx)


@teams_group.child
@player_options
@lightbulb.command(
	"remove-player",
	description="Removes a playerset from the teams system.",
	inherit_checks=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def remove_player_command(ctx: lightbulb.SlashContext):
	await teams_plugin.remove_player(ctx)


@teams_group.child
@lightbulb.option(
	"max-size",
	description="The largest possible team size. (default=3)",
	type=int,
	default=3,
	min_value=2,
	max_value=4,
)
@lightbulb.command(
	"generate",
	description="Creates randomized teams based on the current cores/players.",
	inherit_checks=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def generate_command(ctx: lightbulb.SlashContext):
	await teams_plugin.generate(ctx)
