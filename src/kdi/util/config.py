from pathlib import Path
import tomllib as toml

from .logger import log


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


def get_config_value(table_key: str, key: str):
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
	table = config_file_data[table_key]
	if key not in table:
		log.critical(f"Config table '{table_key}' missing required key: '{key}'")
		exit(1)
	return table[key]
