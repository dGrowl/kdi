from typing import Iterable

from pytest_mock import MockerFixture
import pytest

from kdi.util import flatten_2d, get_config_value, shuffled


class TestConfig:
	@pytest.fixture(autouse=True)
	def clear_config_file_data(self, mocker: MockerFixture):
		mocker.patch("kdi.util.config.config_file_data", None)

	@pytest.fixture
	def mock_config_file(self, mocker: MockerFixture):
		mocker.patch(
			"kdi.util.config.read_config_file",
			return_value={"section": {"a": "first", "b": "second"}},
		)

	def test_loads_keys(self, mock_config_file: None):
		assert get_config_value("section", "a") == "first"
		assert get_config_value("section", "b") == "second"

	def test_reads_file_once(self, mocker: MockerFixture, mock_config_file: None):
		import kdi.util.config

		config_loader = mocker.spy(kdi.util.config, "load_config")
		config_loader.assert_not_called()
		get_config_value("section", "a")
		config_loader.assert_called_once()
		get_config_value("section", "b")
		config_loader.assert_called_once()

	def test_missing_table_key(self):
		with pytest.raises(SystemExit):
			get_config_value("section_two", "a")

	def test_missing_key(self):
		with pytest.raises(SystemExit):
			get_config_value("section", "c")


class TestShuffled:
	def test_copies_object(self):
		x = [1, 2, 3, 4]
		y = shuffled(x)
		assert id(x) != id(y)

	def test_copies_subobjects(self):
		x = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
		y = shuffled(x)
		for a, b in zip(x, y):
			assert id(a) != id(b)


class TestFlatten2d:
	@pytest.mark.parametrize(
		("x", "y"),
		[
			([[1], [2, 3]], [1, 2, 3]),
			([(1, 2), (3, 4)], [1, 2, 3, 4]),
		],
	)
	def test_ordered(self, x: Iterable[Iterable[int]], y: Iterable[int]):
		assert flatten_2d(x) == y

	@pytest.mark.parametrize(
		("x", "y"),
		[
			([{1}, {2, 3}], [1, 2, 3]),
			({(1, 2), (3, 4, 5)}, [1, 2, 3, 4, 5]),
			([(1, 2), {3, 4}, [5]], [1, 2, 3, 4, 5]),
		],
	)
	def test_unordered(self, x: Iterable[Iterable[int]], y: Iterable[int]):
		assert sorted(flatten_2d(x)) == y
