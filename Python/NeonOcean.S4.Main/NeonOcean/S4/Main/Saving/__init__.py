from __future__ import annotations

import abc
import typing

from NeonOcean.S4.Main import Debug, Mods
from NeonOcean.S4.Main.Tools import Exceptions

class SectionAbstract(abc.ABC):
	@property
	@abc.abstractmethod
	def Identifier (self) -> str: ...

	@property
	@abc.abstractmethod
	def SavingObject (self): ...

	@abc.abstractmethod
	def Load (self, sectionData: typing.Any) -> bool: ...

	@abc.abstractmethod
	def Save (self) -> typing.Tuple[bool, typing.Any]: ...

	@abc.abstractmethod
	def Reset (self) -> None: ...

class SaveAbstract(abc.ABC):
	@property
	@abc.abstractmethod
	def Host (self) -> Mods.Mod: ...

	@property
	@abc.abstractmethod
	def Identifier (self) -> str: ...

	@property
	@abc.abstractmethod
	def Sections (self) -> list: ...

	@property
	@abc.abstractmethod
	def Enabled (self) -> bool: ...

	@property
	@abc.abstractmethod
	def Loaded (self) -> bool: ...

	@property
	@abc.abstractmethod
	def DataGUID (self) -> typing.Optional[int]: ...

	@property
	@abc.abstractmethod
	def DataHostNamespace (self) -> typing.Optional[str]: ...

	@property
	@abc.abstractmethod
	def DataHostVersion (self) -> typing.Optional[str]: ...

	@property
	@abc.abstractmethod
	def DataGameVersion (self) -> typing.Optional[str]: ...

	@property
	@abc.abstractmethod
	def DataGameTick (self) -> typing.Optional[int]: ...

	@abc.abstractmethod
	def RegisterSection (self, sectionHandler) -> None: ...

	@abc.abstractmethod
	def UnregisterSection (self, sectionHandler) -> None: ...

	@abc.abstractmethod
	def Load (self, saveFilePath: str) -> bool: ...

	@abc.abstractmethod
	def LoadDefault (self) -> None: ...

	@abc.abstractmethod
	def Save (self, saveFilePath: str) -> bool: ...

	@abc.abstractmethod
	def Unload (self) -> None: ...

	@abc.abstractmethod
	def GetSectionData (self, sectionIdentifier: str) -> typing.Optional[typing.Any]: ...

	@abc.abstractmethod
	def GetSaveFileName (self) -> str: ...

class SectionBase(SectionAbstract, abc.ABC):
	def __init__ (self, savingObject: SaveAbstract):
		if not isinstance(savingObject, SaveAbstract):
			raise Exceptions.IncorrectTypeException(savingObject, "savingObject", (SaveAbstract,))

		self._savingObject = savingObject  # type: SaveAbstract

	@property
	def SavingObject (self) -> SaveAbstract:
		return self._savingObject

class SaveBase(SaveAbstract, abc.ABC):
	def __init__ (self):
		self._sections = list()  # type: typing.List[SectionAbstract]

	@property
	def Sections (self) -> typing.List[SectionAbstract]:
		return list(self._sections)

	def RegisterSection (self, sectionHandler: SectionBase) -> None:
		"""
		Attach a section handler to this saving object. Saves are typically divided into sections dealing with different data, such as data specific to zones
		or specific to sims.
		:param sectionHandler: A section handler to be attached, save section data is passed to the handler for more meaningful management than this class
		can provide alone.
		"""

		if not isinstance(sectionHandler, SectionAbstract):
			raise Exceptions.IncorrectTypeException(sectionHandler, "sectionHandler", (SectionAbstract,))

		operationInformation = "Save Identifier: %s" % self.Identifier

		for currentSectionHandler in self._sections:  # type: SectionAbstract
			if currentSectionHandler.Identifier == sectionHandler.Identifier:
				Debug.Log("Multiple section handlers with the identifier '" + sectionHandler.Identifier + "'.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)

		self._sections.append(sectionHandler)

	def UnregisterSection (self, sectionHandler: SectionAbstract) -> None:
		"""
		Detach a section handler from this saving object.
		:param sectionHandler: A section handler to be detached.
		"""

		self._sections.remove(sectionHandler)
