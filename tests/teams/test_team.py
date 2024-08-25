import pytest

from kdi.teams.team import Team


@pytest.fixture
def members():
	return {"a", "b"}


class TestInit:
	@pytest.mark.parametrize("c", [0, -3])
	def test_errors_on_nonpositive_capacity(self, c: int):
		with pytest.raises(ValueError):
			Team(c)


class TestRemainingSpace:
	def test_calculates_accurately(self, members: set[str]):
		t = Team(3)
		t.add_members(members)
		assert t.remaining_space == 1


class TestHasSpace:
	def test_returns_true_when_not_full(self, members: set[str]):
		t = Team(4)
		t.add_members(members)
		assert t.has_space

	def test_returns_false_when_full(self, members: set[str]):
		t = Team(2)
		t.add_members(members)
		assert not t.has_space


class TestAddMembers:
	def test_sets_members(self, members: set[str]):
		t = Team(3)
		t.add_members(members)
		assert t._members == members

	def test_errors_on_too_many_members(self):
		t = Team(3)
		with pytest.raises(ValueError):
			t.add_members({"a", "b", "c", "d"})
