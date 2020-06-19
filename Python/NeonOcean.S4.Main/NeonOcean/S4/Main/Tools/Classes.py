from __future__ import annotations

import typing

class ClassProperty:
	def __init__ (self, getFunction: typing.Callable = None, documentationString: str = None):
		self._GetFunction = getFunction

		if documentationString is None and getFunction is not None:
			documentationString = self._GetFunction.__doc__

		self.__doc__ = documentationString

	def __get__ (self, instance: object, owner: typing.Type):
		return self._GetFunction(owner)
