from typing import Collection, Optional

import hikari
import lightbulb

from ..bot import kdi
from ..util import get_config_value, KeySet
from .teams_state import Player


PLAYER_AVAILABLE_ID = "PLAYER_AVAILABLE"

PLAYER_UNAVAILABLE_ID = "PLAYER_UNAVAILABLE"

PLAYERS_EMBED_DESCRIPTION = "Use the **__buttons__** below to set your availability! Check that you appear on the list when you're active."

PLAYERS_EMBED_NO_PLAYERS_LIST = "Nobody at the moment :("

PLAYERS_EMBED_TITLE = ":video_game: Players"

ACTION_ROW = kdi.rest.build_message_action_row()
ACTION_ROW.add_interactive_button(
	hikari.ButtonStyle.PRIMARY,
	PLAYER_AVAILABLE_ID,
	emoji="\N{SALUTING FACE}",
	label="Ready!",
)
ACTION_ROW.add_interactive_button(
	hikari.ButtonStyle.SECONDARY,
	PLAYER_UNAVAILABLE_ID,
	emoji="\N{SLEEPING FACE}",
	label="Done for now.",
)


def format_players(players: Collection[KeySet]):
	return sorted([" / ".join(sorted(p)) for p in players])


class PlayersMessage:
	_color: str
	_message: Optional[hikari.Message]

	def __init__(self):
		self._color = get_config_value("bot", "color")
		self._message = None

	def matches(self, message: hikari.Message) -> bool:
		return self._message is not None and self._message.id == message.id

	def build_embed(self, players: Collection[KeySet] = []):
		n_players = sum(len(p) for p in players)
		names = format_players(players)
		return hikari.Embed(
			title=PLAYERS_EMBED_TITLE,
			color=self._color,
			description=PLAYERS_EMBED_DESCRIPTION,
		).add_field(
			f"Active ({n_players})",
			"\n".join(names) if players else PLAYERS_EMBED_NO_PLAYERS_LIST,
		)

	async def create(self, ctx: lightbulb.SlashContext, players: set[Player]):
		response = await ctx.respond(
			embed=self.build_embed(players), component=ACTION_ROW
		)
		self._message = await response.message()

	async def update(self, players: set[Player]):
		if self._message is None:
			return
		await self._message.edit(embed=self.build_embed(players))

	async def check_delete(self, event: hikari.GuildMessageDeleteEvent):
		if self._message and self._message.id == event.message_id:
			self._message = None
