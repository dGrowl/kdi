class Team:
	_capacity: int
	_members: set[str]

	def __init__(self, capacity: int):
		if capacity <= 0:
			raise ValueError(capacity, "Team capacity must be positive")
		self._capacity = capacity
		self._members = set()

	def __str__(self):
		return str(self._members)

	def __repr__(self):
		return f"Team(capacity={self._capacity}, members={self._members})"

	@property
	def remaining_space(self):
		return self._capacity - len(self._members)

	@property
	def has_space(self):
		return self.remaining_space > 0

	def add_members(self, new_members: set[str]):
		future_members = self._members | new_members
		if len(future_members) > self._capacity:
			raise ValueError(
				"Team would exceed capacity after adding new members",
				self._members,
				new_members,
			)
		self._members = future_members
