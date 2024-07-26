from dataclasses import dataclass

import hikari


@dataclass
class User:
	id: hikari.Snowflakeish
	name: str


class UserStore:
	_id_to_name: dict[hikari.Snowflakeish, User]
	_name_to_id: dict[str, User]

	def __init__(self):
		self._id_to_name = {}
		self._name_to_id = {}

	def clear(self):
		self._id_to_name.clear()
		self._name_to_id.clear()

	def get(self, id_or_name: hikari.Snowflakeish | str):
		if isinstance(id_or_name, str):
			return self._name_to_id.get(id_or_name)
		return self._id_to_name.get(id_or_name)

	def store(self, uid: hikari.Snowflakeish, name: str):
		if name not in self._name_to_id and uid not in self._id_to_name:
			self._id_to_name[uid] = self._name_to_id[name] = User(uid, name)


users = UserStore()
