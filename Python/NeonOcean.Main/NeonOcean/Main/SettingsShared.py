import typing

class SettingBase:
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
	def Setup (cls) -> None:
		raise NotImplementedError()

	@classmethod
	def isSetup (cls) -> bool:
		raise NotImplementedError()

	@classmethod
	def Get (cls) -> typing.Any:
		raise NotImplementedError()

	@classmethod
	def Set (cls, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
		raise NotImplementedError()

	@classmethod
	def SetDefault (cls) -> None:
		pass

	@classmethod
	def Reset (cls) -> None:
		raise NotImplementedError()

	@classmethod
	def Verify (cls, value: typing.Any, lastChangeVersion = None) -> typing.Any:
		raise NotImplementedError()

	@classmethod
	def IsActive (cls) -> bool:
		raise NotImplementedError()

	@classmethod
	def GetName (cls) -> typing.Any:
		raise NotImplementedError()

	@classmethod
	def ShowDialog (cls) -> None:
		raise NotImplementedError()
