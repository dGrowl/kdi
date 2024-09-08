from copy import deepcopy
from random import shuffle
from typing import Iterable, TypeVar
from sys import argv

T = TypeVar("T")


TEST_DATA_FLAG = "--test-data"


def check_flag(flag: str):
	return flag in argv


def shuffled(x: Iterable[T]):
	y = list(deepcopy(x))
	shuffle(y)
	return y


def flatten_2d(x: Iterable[Iterable[T]]):
	return [item for iterable in x for item in iterable]
