from functools import lru_cache
from typing import Optional
import re


class Command:
	_module: str
	_action: Optional[str]
	_args: Optional[list[str]]

	def __init__(
		self,
		module: str,
		action: Optional[str] = None,
		args: Optional[list[str]] = None,
	):
		self._module = module
		self._action = action
		self._args = args

	def __eq__(self, other: object):
		if not isinstance(other, Command):
			return NotImplemented
		return (
			self._module == other._module
			and self._action == other._action
			and self._args == other._args
		)

	@classmethod
	@lru_cache(32)
	def from_string(cls, s: str):
		match = re.fullmatch(r"\/(\w+)( +[^\s]+)?(.+)?", s)
		if match is None:
			return None
		components = [g if g is None else g.strip() for g in match.groups()]
		if components[2] is not None:
			components[2] = re.split(r" +", components[2])
		return cls(components[0], components[1], components[2])

	@property
	def module(self):
		return self._module

	@property
	def action(self):
		return self._action

	@property
	def args(self):
		return self._args
