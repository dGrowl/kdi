from pytest_mock import MockerFixture
import pytest

from kdi.util import Command, get_config_value


@pytest.fixture(autouse=True)
def clear_config_file_data(mocker: MockerFixture):
	mocker.patch("kdi.util.config.config_file_data", None)


@pytest.fixture
def mock_config_file(mocker: MockerFixture):
	mocker.patch(
		"kdi.util.config.read_config_file",
		return_value={"section": {"a": "first", "b": "second"}},
	)


class TestConfig:
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


@pytest.fixture
def module():
	return "etl"


@pytest.fixture
def action():
	return "transform"


@pytest.fixture
def arg():
	return "data.txt"


@pytest.fixture
def args():
	return ["-O3", "--verbose", "data.txt"]


class TestCommand:
	def test_module(self, module: str):
		assert Command.from_string(f"/{module}") == Command(module)

	def test_action(self, module: str, action: str):
		assert Command.from_string(f"/{module} {action}") == Command(module, action)

	def test_one_arg(self, module: str, action: str, arg: str):
		assert Command.from_string(f"/{module} {action} {arg}") == Command(
			module, action, [arg]
		)

	def test_multiple_args(self, module: str, action: str, args: list[str]):
		assert Command.from_string(f"/{module} {action} {" ".join(args)}") == Command(
			module, action, args
		)

	@pytest.mark.parametrize("command", ["", "    ", "/", "hello, kdi"])
	def test_non_command(self, command: str):
		assert Command.from_string(command) is None

	def test_extra_spaces(self, module: str, action: str, args: list[str]):
		assert Command.from_string(
			f"/{module}    {action}     {" ".join(args)}    "
		) == Command(module, action, args)

	def test_special_characters(self):
		module = "he_llo"
		action = "!)#*(_|}{<>938)"
		args = ["aH|{}<:L(8", "zdL+_!#-=SJ)", r"$?<\>:}{})(*!#&)"]
		assert Command.from_string(f"/{module} {action} {" ".join(args)}") == Command(
			module, action, args
		)
