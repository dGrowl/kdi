from typing import Iterable, TypeVar
from copy import deepcopy
from random import shuffle

T = TypeVar("T")


def shuffled(x: Iterable[T]):
	y = list(deepcopy(x))
	shuffle(y)
	return y
