import pytest

from kdi.store import User, UserStore


@pytest.fixture
def name():
	return "friend"


@pytest.fixture
def uid():
	return 1


@pytest.fixture
def multiple_users():
	return [(123, "user1"), (456, "user2"), (789, "user3")]


@pytest.fixture
def user_store():
	return UserStore()


class TestUsers:
	def test_get_id(self, user_store: UserStore, uid: int, name: str):
		user_store.store(uid, name)
		assert user_store.get(uid) == User(uid, name)

	def test_get_name(self, user_store: UserStore, uid: int, name: str):
		user_store.store(uid, name)
		assert user_store.get(name) == User(uid, name)

	def test_store_multiple(
		self, user_store: UserStore, multiple_users: list[tuple[int, str]]
	):
		for uid, name in multiple_users:
			user_store.store(uid, name)
		for uid, name in multiple_users:
			assert user_store.get(uid) == user_store.get(name) == User(uid, name)

	def test_clear(self, user_store: UserStore, multiple_users: list[tuple[int, str]]):
		for uid, name in multiple_users:
			user_store.store(uid, name)
		user_store.clear()
		for uid, name in multiple_users:
			assert user_store.get(uid) is None
			assert user_store.get(name) is None

	def test_store_ignores_duplicate_id(
		self, user_store: UserStore, uid: int, name: str
	):
		user_store.store(uid, name)
		other_name = "enemy"
		user_store.store(uid, other_name)
		assert user_store.get(other_name) is None

	def test_store_ignores_duplicate_name(
		self, user_store: UserStore, uid: int, name: str
	):
		user_store.store(uid, name)
		other_id = 2
		user_store.store(other_id, name)
		assert user_store.get(other_id) is None

	@pytest.mark.parametrize("key", [uid, name])
	def test_get_nonexistent_user(self, user_store: UserStore, key: int | str):
		assert user_store.get(key) is None
