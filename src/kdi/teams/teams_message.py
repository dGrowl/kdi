import hikari
from random import choice

from ..util import get_config_value, shuffled
from .teams_state import Team


class TeamsMessage:
	_color: str
	_name_components: list[list[str]]
	_player_emojis: list[str]

	def __init__(self):
		self._color = get_config_value("bot", "color")
		self._name_components = get_config_value("teams", "team_name_components")
		self._player_emojis = get_config_value("teams", "player_emojis")

	def build_embed(self, i_round: int, teams: list[Team]):
		name_components = list(map(shuffled, self._name_components))
		embed = hikari.Embed(
			title=f":twisted_rightwards_arrows: Shuffled Teams (Round {i_round})",
			color=self._color,
			description="The teams for this round of play. Squad up and have fun!",
		)
		for t in teams:
			embed.add_field(
				":military_helmet: Team "
				+ " ".join(piece.pop() for piece in name_components),
				"\n".join(
					[f"{choice(self._player_emojis)} " + name for name in sorted(t)]
				),
			)
		return embed
