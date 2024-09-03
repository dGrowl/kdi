from typing import Optional, Union

from ..util import Key, KeySet


class Team:
	_capacity: int
	_members: set[Key]

	def __init__(self, capacity: int, members: Optional[set[Key]] = None):
		if capacity <= 0:
			raise ValueError(capacity, "Capacity must be positive")
		if members is not None and len(members) > capacity:
			raise ValueError(capacity, "Member count must not exceed capacity")
		self._capacity = capacity
		self._members = set() if members is None else members.copy()

	def __eq__(self, other: object):
		if isinstance(other, Team):
			return self.__dict__ == other.__dict__
		return False

	def __contains__(self, name: str):
		return name in self._members

	def __iter__(self):
		for name in self._members:
			yield name

	def __str__(self):
		return str(self._members)

	def __repr__(self):
		return f"Team(capacity={self._capacity}, members={self._members})"

	def __and__(self, other: Union["Team", KeySet]):
		if isinstance(other, (set, frozenset)):
			return self._members & other
		return self._members & other._members

	def __or__(self, other: Union["Team", KeySet]):
		if isinstance(other, (set, frozenset)):
			return self._members | other
		return self._members | other._members

	@property
	def remaining_space(self):
		return self._capacity - len(self._members)

	@property
	def has_space(self):
		return self.remaining_space > 0

	@property
	def members(self):
		return frozenset(self._members)

	def add_members(self, new_members: KeySet):
		future_members = self._members | new_members
		if len(future_members) > self._capacity:
			raise ValueError(
				"Team would exceed capacity after adding new members",
				self._members,
				new_members,
			)
		self._members = future_members
