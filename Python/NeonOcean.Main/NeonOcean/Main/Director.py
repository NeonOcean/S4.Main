import typing

import zone
from NeonOcean.Main import Debug, This, Mods
from NeonOcean.Main.Tools import Exceptions, Patcher, Types
from sims4.tuning import instance_manager

_announcer = list()  # type: typing.List[typing.Type[Announcer]]

class Announcer:
	Host = This.Mod  # type: Mods.Mod
	Enabled = True  # type: bool
	Reliable = False  # type: bool

	_level = 0  # type: float

	def __init_subclass__ (cls, **kwargs):
		SetupAnnouncer(cls)

	@classmethod
	def GetLevel (cls) -> float:
		return cls._level

	@classmethod
	def SetLevel (cls, value) -> None:
		cls._level = value
		_SortAnnouncer()

	@classmethod
	def OnInitializeSubclass (cls) -> None:
		pass

	@classmethod
	def OnInstanceManagerLoaded (cls, instanceManager: instance_manager.InstanceManager) -> None:
		pass

	@classmethod
	def OnLoadingScreenAnimationFinished (cls, zoneReference: zone.Zone) -> None:
		pass

def SetupAnnouncer (announcer: typing.Type[Announcer]) -> None:
	if not issubclass(announcer, Announcer):
		raise Exceptions.IncorrectTypeException(announcer, "announcer", (Announcer,))

	if announcer in _announcer:
		return

	_Register(announcer)

	_SortAnnouncer()
	OnInitializeSubclass()

def OnInitializeSubclass () -> None:
	for announcer in _announcer:  # type: typing.Type[Announcer]
		try:
			if not announcer.Enabled:
				continue

			if not announcer.Host.IsLoaded() and not announcer.Reliable:
				continue

			announcer.OnInitializeSubclass()
		except:
			Debug.Log("Failed to run 'OnInitializeSubclass' for '" + Types.GetFullName(announcer) + "'", announcer.Host.Namespace, Debug.LogLevels.Exception, group = announcer.Host.Namespace, owner = __name__)

@Patcher.Decorator(instance_manager.InstanceManager, "on_start", permanent = True)
def OnInstanceManagerLoaded (self: instance_manager.InstanceManager) -> None:
	for announcer in _announcer:  # type: typing.Type[Announcer]
		try:
			if not announcer.Enabled:
				continue

			if not announcer.Host.IsLoaded() and not announcer.Reliable:
				continue

			announcer.OnInstanceManagerLoaded(self)
		except:
			Debug.Log("Failed to run 'OnInstanceManagerLoaded' for '" + Types.GetFullName(announcer) + "'", announcer.Host.Namespace, Debug.LogLevels.Exception, group = announcer.Host.Namespace, owner = __name__)

@Patcher.Decorator(zone.Zone, "on_loading_screen_animation_finished", permanent = True)
def OnLoadingScreenAnimationFinished (self: zone.Zone) -> None:
	for announcer in _announcer:  # type: typing.Type[Announcer]
		try:
			if not announcer.Enabled:
				continue

			if not announcer.Host.IsLoaded() and not announcer.Reliable:
				continue

			announcer.OnLoadingScreenAnimationFinished(self)
		except:
			Debug.Log("Failed to run 'OnLoadingScreenAnimationFinished' for '" + Types.GetFullName(announcer) + "'", announcer.Host.Namespace, Debug.LogLevels.Exception, group = announcer.Host.Namespace, owner = __name__)

def _Register (announcer: typing.Type[Announcer]) -> None:
	if not announcer in _announcer:
		_announcer.append(announcer)

def _SortAnnouncer () -> None:
	global _announcer

	announcer = _announcer.copy()  # type: typing.List[typing.Type[Announcer]]

	sortedAnnouncer = list()

	for loopCount in range(len(announcer)):  # type: int
		targetIndex = None  # type: int

		for currentIndex in range(len(announcer)):
			if targetIndex is None:
				targetIndex = currentIndex
				continue

			if announcer[currentIndex].GetLevel() != announcer[targetIndex].GetLevel():
				if announcer[currentIndex].GetLevel() < announcer[targetIndex].GetLevel():
					targetIndex = currentIndex
					continue
			else:
				if announcer[currentIndex].__module__ < announcer[targetIndex].__module__:
					targetIndex = currentIndex
					continue

		sortedAnnouncer.append(announcer[targetIndex])
		announcer.pop(targetIndex)

		_announcer = sortedAnnouncer