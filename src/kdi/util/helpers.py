from copy import deepcopy
from pathlib import Path
from random import shuffle
from sys import argv
from typing import Iterable, TypeVar

T = TypeVar("T")

Setlike = set[T] | frozenset[T]


TEST_DATA_FLAG = "--test-data"


def check_flag(flag: str):
	return flag in argv


def shuffled(x: Iterable[T]):
	y = list(deepcopy(x))
	shuffle(y)
	return y


def flatten_2d(x: Iterable[Iterable[T]]):
	return [item for iterable in x for item in iterable]


def get_cache_dir():
	project_root = Path(__file__).resolve().parent
	while (
		not (project_root / "pyproject.toml").exists()
		and project_root != project_root.parent
	):
		project_root = project_root.parent
	cache_dir = project_root / ".cache"
	cache_dir.mkdir(parents=True, exist_ok=True)
	return cache_dir


def clamp(x: int, lo: int, hi: int):
	return max(lo, min(x, hi))


def intersects(a: Setlike[T], b: Setlike[T]):
	return not a.isdisjoint(b)
