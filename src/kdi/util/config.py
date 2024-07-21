from pathlib import Path
from typing import Any
import tomllib as toml

from .logger import log


class Config:
	_data: dict[str, Any]
	_table_key: str
	_required_keys: set[str]

	def __init__(self, table_key: str, required_keys: set[str]):
		self._data = {}
		self._table_key = table_key
		self._required_keys = required_keys

	def load(self):
		self._data = get_config_table(self._table_key)

		missing_keys = self._required_keys - set(self._data.keys())
		if missing_keys:
			log.critical(f"Config table missing required keys: {sorted(missing_keys)}")
			exit(1)

	def get(self, key: str):
		if not self._data:
			self.load()
		return self._data[key]


CONFIG_FILE_NAME = "config.toml"


def get_config_path():
	p = Path(__file__).parents[3] / "config" / CONFIG_FILE_NAME
	return p.absolute().as_posix()


def read_config_file():
	with open(get_config_path(), "rb") as config_file:
		return toml.load(config_file)


config_file_data = None


def load_config():
	global config_file_data
	config_file_data = read_config_file()


def get_config_table(table_key: str) -> dict[str, Any]:
	if config_file_data is None:
		load_config()
	if config_file_data is None:
		log.critical(f"Failed to load config file ({get_config_path()})")
		exit(1)
	if table_key not in config_file_data:
		log.critical(
			f"Config file ({get_config_path()}) missing table key: '{table_key}'"
		)
		exit(1)
	return config_file_data[table_key]
