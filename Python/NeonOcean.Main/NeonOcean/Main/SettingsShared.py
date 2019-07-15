import abc
import typing

class SettingBase(abc.ABC):
	IsSetting: bool

	Key: str
	Type: typing.Type
	Default: typing.Any

	Dialog: typing.Any

	def __init_subclass__ (cls, **kwargs):
		cls.OnInitializeSubclass()

	@classmethod
	def OnInitializeSubclass (cls) -> None:
		pass

	@classmethod
	@abc.abstractmethod
	def Setup (cls) -> None:
		raise NotImplementedError()

	@classmethod
	@abc.abstractmethod
	def IsSetup (cls) -> bool:
		raise NotImplementedError()

	@classmethod
	@abc.abstractmethod
	def Get (cls) -> typing.Any:
		raise NotImplementedError()

	@classmethod
	@abc.abstractmethod
	def Set (cls, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
		raise NotImplementedError()

	@classmethod
	def SetDefault (cls) -> None:
		pass

	@classmethod
	@abc.abstractmethod
	def Reset (cls) -> None:
		raise NotImplementedError()

	@classmethod
	@abc.abstractmethod
	def Verify (cls, value: typing.Any, lastChangeVersion = None) -> typing.Any:
		raise NotImplementedError()

	@classmethod
	@abc.abstractmethod
	def IsActive (cls) -> bool:
		raise NotImplementedError()

	@classmethod
	@abc.abstractmethod
	def GetName (cls) -> typing.Any:
		raise NotImplementedError()

	@classmethod
	@abc.abstractmethod
	def ShowDialog (cls) -> None:
		raise NotImplementedError()

class SettingBranchedBase:
	IsSetting: bool

	Key: str
	Type: typing.Type
	Default: typing.Any

	Dialog: typing.Any

	def __init_subclass__ (cls, **kwargs):
		cls.OnInitializeSubclass()

	@classmethod
	def OnInitializeSubclass (cls) -> None:
		pass

	@classmethod
	@abc.abstractmethod
	def Setup (cls) -> None:
		raise NotImplementedError()

	@classmethod
	@abc.abstractmethod
	def IsSetup (cls) -> bool:
		raise NotImplementedError()

	@classmethod
	@abc.abstractmethod
	def Get (cls, branch: str) -> typing.Any:
		raise NotImplementedError()

	@classmethod
	@abc.abstractmethod
	def Set (cls, branch: str, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
		raise NotImplementedError()

	@classmethod
	def SetDefault (cls) -> None:
		pass

	@classmethod
	@abc.abstractmethod
	def Reset (cls, branch: str = None) -> None:
		raise NotImplementedError()

	@classmethod
	@abc.abstractmethod
	def Verify (cls, value: typing.Any, lastChangeVersion = None) -> typing.Any:
		raise NotImplementedError()

	@classmethod
	@abc.abstractmethod
	def IsActive (cls) -> bool:
		raise NotImplementedError()

	@classmethod
	@abc.abstractmethod
	def GetName (cls) -> typing.Any:
		raise NotImplementedError()

	@classmethod
	@abc.abstractmethod
	def ShowDialog (cls, branch: str) -> None:
		raise NotImplementedError()