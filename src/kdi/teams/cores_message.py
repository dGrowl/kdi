from collections import defaultdict
from itertools import product
from typing import DefaultDict, Optional

import hikari
import lightbulb

from ..util import get_config_value, shuffled
from .teams_state import Player


class CoresMessage:
	_assigned_names: DefaultDict[Player, str]
	_color: str
	_message: Optional[hikari.Message]
	_possible_names: list[str]

	def __init__(self):
		self._assigned_names = defaultdict(self.get_name)
		self._color = get_config_value("bot", "color")
		self._message = None
		name_components = get_config_value("teams", "core_name_components")
		self._possible_names = shuffled(
			[" ".join(sequence) for sequence in product(*name_components)]
		)

	def get_name(self):
		if self._possible_names:
			return self._possible_names.pop()
		return "Null"

	async def create(self, ctx: lightbulb.SlashContext, cores: set[Player]):
		response = await ctx.respond(embed=self.build_embed(cores))
		self._message = await response.message()

	async def update(self, cores: set[Player]):
		if self._message is None:
			return
		await self._message.edit(embed=self.build_embed(cores))

	def build_embed(self, cores: set[Player]):
		embed = hikari.Embed(
			title=":pilot: Cores",
			color=self._color,
			description="The leaders of the teams into which players will be shuffled.",
		)
		if cores:
			for c in cores:
				embed.add_field(
					":rosette: " + self._assigned_names[frozenset(c)],
					"\n".join(name for name in c),
				)
		else:
			embed.add_field("Active (0)", "But you can still play!")
		return embed
