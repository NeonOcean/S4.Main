from __future__ import annotations

import typing
import math

from NeonOcean.S4.Main.Tools import Exceptions

def IsRealNumber (number: typing.Union[float, int]):
	if not isinstance(number, float) and not isinstance(number, int):
		raise Exceptions.IncorrectTypeException(number, "number", (float, int))

	if not math.isfinite(number):
		return False

	return True

def IsInteger (number: int):
	if not isinstance(number, int):
		raise Exceptions.IncorrectTypeException(number, "number", (int, ))

	if not math.isfinite(number):
		return False

	return True