import hikari
import lightbulb

from ..bot import kdi
from ..util import get_config_value
from .cores_message import CoresMessage
from .players_message import (
	PlayersMessage,
	PLAYER_AVAILABLE_ID,
	PLAYER_UNAVAILABLE_ID,
)
from .teams_state import TeamsState

UNTRUSTED_USER_RESPONSE = ":no_entry: Only trusted users can make teams. Sorry!"


class TeamsPlugin(lightbulb.Plugin):
	_cores_message: CoresMessage
	_players_message: PlayersMessage
	_state: TeamsState
	_trusted_user_ids: set[int]

	def __init__(self):
		super().__init__("teams")
		self._cores_message = CoresMessage()
		self._players_message = PlayersMessage()
		self._state = TeamsState()
		self._trusted_user_ids = get_config_value("user", "trusted_ids")

		kdi.subscribe(hikari.GuildMessageDeleteEvent, self.on_gm_delete)
		kdi.subscribe(hikari.InteractionCreateEvent, self.on_interaction)

	async def start(self, ctx: lightbulb.SlashContext):
		user = ctx.user
		if user.is_bot:
			return
		if user.id not in self._trusted_user_ids:
			await ctx.respond(
				UNTRUSTED_USER_RESPONSE, flags=hikari.MessageFlag.EPHEMERAL
			)
			return
		self._state.reset()
		self._state.add_player({user.username}, True)
		await self._cores_message.create(ctx, self._state.cores)
		await self._players_message.create(ctx)

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
			await self._players_message.update(self._state.players)
		await interaction.create_initial_response(
			hikari.ResponseType.DEFERRED_MESSAGE_UPDATE
		)

	async def on_gm_delete(self, event: hikari.GuildMessageDeleteEvent):
		await self._players_message.check_delete(event)

	async def on_interaction(self, event: hikari.InteractionCreateEvent):
		if (
			not isinstance(event.interaction, hikari.ComponentInteraction)
			or event.interaction.user.is_bot
		):
			return
		await self.check_players_interaction(event.interaction)


teams_plugin = TeamsPlugin()


@teams_plugin.command
@lightbulb.command(
	"teams", description="Allows you to generate randomized teams of players"
)
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def teams_group(_: lightbulb.SlashContext):
	pass


@teams_group.child
@lightbulb.command("start", description="Starts a new session of the teams system")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def start(ctx: lightbulb.SlashContext):
	await teams_plugin.start(ctx)
