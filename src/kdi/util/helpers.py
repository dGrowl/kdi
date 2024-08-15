from copy import deepcopy
from random import shuffle
from typing import Iterable, TypeVar

T = TypeVar("T")


def shuffled(x: Iterable[T]):
	y = list(deepcopy(x))
	shuffle(y)
	return y


def flatten_2d(x: Iterable[Iterable[T]]):
	return [item for iterable in x for item in iterable]
