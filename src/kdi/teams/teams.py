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

	async def start(self, ctx: lightbulb.SlashContext):
		self._state.reset()
		if check_flag(TEST_DATA_FLAG):
			self.load_test_data()
		if ctx.options["auto-core"]:
			self._state.add_core({ctx.user.username})
		await self._cores_message.create(ctx, self._state.cores)
		await self._players_message.create(ctx, self._state.players - self._state.cores)

	def load_test_data(self):
		for c in map(set, ["xy", "z"]):
			self._state.add_core(c)
		for p in map(set, ["a", "b", "cd", "e", "f", "ghi"]):
			self._state.add_player(p)

	def build_add_core_success_embed(self, core_names: KeySet):
		embed = hikari.Embed(
			color=self._color,
			description=f"Added new core: **{" / ".join(core_names)}**",
			title=":white_check_mark: Add Core: Success",
		)
		embed.set_footer(SELF_DESTRUCT_FOOTER)
		return embed

	def build_add_core_error_embed(self, core_names: KeySet):
		embed = hikari.Embed(
			color=self._color,
			description=f"**{" / ".join(core_names)}** overlaps with existing cores.",
			title=":stop_sign: Add Core: Failure",
		)
		embed.set_footer(SELF_DESTRUCT_FOOTER)
		return embed

	def build_remove_core_success_embed(self, core_names: KeySet):
		embed = hikari.Embed(
			color=self._color,
			description=f"**{" / ".join(core_names)}** is no longer a core.",
			title=":white_check_mark: Remove Core: Success",
		)
		embed.set_footer(SELF_DESTRUCT_FOOTER)
		return embed

	def build_remove_core_error_embed(self, core_names: KeySet):
		embed = hikari.Embed(
			color=self._color,
			description=f"**{" / ".join(core_names)}** is not currently a core.",
			title=":stop_sign: Remove Core: Failure",
		)
		embed.set_footer(SELF_DESTRUCT_FOOTER)
		return embed

	def is_trusted_user(self, user_id: hikari.Snowflakeish):
		return user_id in self._trusted_user_ids

	async def add_core(self, ctx: lightbulb.SlashContext):
		names = get_usernames_from_options(ctx.options)
		embed = self.build_add_core_success_embed(names)
		if self._state.add_core(names):
			await self._cores_message.update(self._state.cores)
		else:
			embed = self.build_add_core_error_embed(names)
		await ctx.respond(
			hikari.ResponseType.MESSAGE_CREATE,
			delete_after=SELF_DESTRUCT_TIME_SECS,
			embed=embed,
		)

	async def remove_core(self, ctx: lightbulb.SlashContext):
		names = get_usernames_from_options(ctx.options)
		embed = self.build_remove_core_success_embed(names)
		if self._state.remove_core(names):
			await self._cores_message.update(self._state.cores)
		else:
			embed = self.build_remove_core_error_embed(names)
		await ctx.respond(
			hikari.ResponseType.MESSAGE_CREATE,
			delete_after=SELF_DESTRUCT_TIME_SECS,
			embed=embed,
		)

	async def generate(self, ctx: lightbulb.SlashContext):
		teams = self._state.generate(ctx.options["max-size"])
		message = TeamsMessage()
		await ctx.respond(embed=message.build_embed(self._state.round_number, teams))

	async def check_players_interaction(self, interaction: hikari.ComponentInteraction):
		if not self._players_message.matches(interaction.message):
			return
		modified = False
		if interaction.custom_id == PLAYER_AVAILABLE_ID:
			modified |= self._state.add_player({interaction.user.username})
		elif interaction.custom_id == PLAYER_UNAVAILABLE_ID:
			modified |= self._state.remove_player({interaction.user.username})
		if modified:
			await self._cores_message.update(self._state.cores)
			await self._players_message.update(self._state.players - self._state.cores)
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
