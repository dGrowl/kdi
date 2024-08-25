from typing import Optional

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

	def test_errors_on_excessive_members(self):
		with pytest.raises(ValueError):
			Team(3, {"a", "b", "c", "d"})


class TestEquality:
	@pytest.mark.parametrize(
		("c", "members"),
		[
			(4, None),
			(3, {"a"}),
		],
	)
	def test_returns_true_on_match(self, c: int, members: Optional[set[str]]):
		assert Team(c, members) == Team(c, members)

	def test_returns_false_on_differing_capacities(self, members: set[str]):
		assert Team(3, members) != Team(4, members)

	def test_returns_false_on_differing_members(self, members: set[str]):
		c = 3
		assert Team(c, members) != Team(c, members | {"c"})


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
