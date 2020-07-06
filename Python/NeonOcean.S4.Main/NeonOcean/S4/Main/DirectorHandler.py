from __future__ import annotations

import typing

import clock
import services
import zone
from NeonOcean.S4.Main import Director
from NeonOcean.S4.Main.Tools import Patcher, Types, Python
from sims4 import service_manager
from sims4.tuning import instance_manager

class _Announcement:
	def __init__ (self, targetObject: object, targetCallableName: str, announcementName: str, announcementCallWrapper: typing.Callable = None, limitErrors: bool = False):
		self.AnnouncementName = announcementName  # type: str
		self.AnnouncementCallWrapper = announcementCallWrapper  # type: typing.Optional[typing.Callable]
		self.LimitErrors = limitErrors  # type: bool

		def AnnouncementBeforePatch (*args, **kwargs) -> typing.Any:
			self._TriggerAnnouncement(self.AnnouncementName, True, *args, **kwargs)

		def AnnouncementAfterPatch (*args, **kwargs) -> typing.Any:
			self._TriggerAnnouncement(self.AnnouncementName, False, *args, **kwargs)

		Patcher.Patch(targetObject, targetCallableName, AnnouncementBeforePatch, patchType = Patcher.PatchTypes.Before, permanent = True)
		Patcher.Patch(targetObject, targetCallableName, AnnouncementAfterPatch, patchType = Patcher.PatchTypes.After, permanent = True)

	def _TriggerAnnouncement (self, announcementMethodName: str, preemptive: bool, *announcementArgs, **announcementKwargs) -> None:
		for announcer in Director.GetAllAnnouncers():  # type: typing.Type[Director.Announcer]
			readReportLockIdentifier = None  # type: typing.Optional[str]
			readReportLockReference = None  # type: typing.Any

			if self.LimitErrors:
				readReportLockIdentifier = __name__ + ":" + str(Python.GetLineNumber())  # type: str
				readReportLockReference = announcer

			try:
				if not announcer.Enabled:
					continue

				if not announcer.Host.IsLoaded() and not announcer.Reliable:
					continue

				if preemptive != announcer.Preemptive:
					continue

				announcementMethod = getattr(announcer, announcementMethodName)  # type: typing.Callable
			except Exception:
				from NeonOcean.S4.Main import Debug
				Debug.Log("Failed to read the announcer at '" + Types.GetFullName(announcer) + "' when triggering the announcement '" + announcementMethodName + "'.",
						  announcer.Host.Namespace, Debug.LogLevels.Exception, group = announcer.Host.Namespace, owner = __name__, lockIdentifier = readReportLockIdentifier, lockReference = readReportLockReference)

				return
			else:
				if readReportLockIdentifier is not None:
					from NeonOcean.S4.Main import Debug
					Debug.Unlock(readReportLockIdentifier, readReportLockReference)

			callReportLockIdentifier = None  # type: typing.Optional[str]
			callReportLockReference = None  # type: typing.Any

			if self.LimitErrors:
				callReportLockIdentifier = __name__ + ":" + str(Python.GetLineNumber())  # type: str
				callReportLockReference = announcer

			try:
				if self.AnnouncementCallWrapper is None:
					announcementMethod(*announcementArgs, **announcementKwargs)
				else:
					self.AnnouncementCallWrapper(announcementMethod, *announcementArgs, **announcementKwargs)
			except Exception:
				from NeonOcean.S4.Main import Debug
				Debug.Log("Failed to trigger the announcement '" + announcementMethodName + "' for '" + Types.GetFullName(announcer) + "'.", announcer.Host.Namespace, Debug.LogLevels.Exception, group = announcer.Host.Namespace, owner = __name__, lockIdentifier = callReportLockIdentifier, lockReference = callReportLockReference)
				return
			else:
				if callReportLockIdentifier is not None:
					from NeonOcean.S4.Main import Debug
					Debug.Unlock(callReportLockIdentifier, callReportLockReference)

# noinspection PyUnusedLocal
def _InstanceManagerOnStartWrapper (announcementMethod: typing.Callable, self, *args, **kwargs) -> None:
	announcementMethod(self)

# noinspection PyUnusedLocal
def _InstanceManagerOnStopWrapper (announcementMethod: typing.Callable, self, *args, **kwargs) -> None:
	announcementMethod(self)

# noinspection PyUnusedLocal
def _OnLoadingScreenAnimationFinishedWrapper (announcementMethod: typing.Callable, self, *args, **kwargs) -> None:
	announcementMethod(self)

# noinspection PyUnusedLocal
def _OnClientConnectWrapper (announcementMethod: typing.Callable, client, *args, **kwargs) -> None:
	announcementMethod(client)

# noinspection PyUnusedLocal
def _OnClientDisconnectWrapper (announcementMethod: typing.Callable, client, *args, **kwargs) -> None:
	announcementMethod(client)

# noinspection PyUnusedLocal
def _OnEnterMainMenuWrapper (announcementMethod: typing.Callable, *args, **kwargs) -> None:
	announcementMethod()

# noinspection PyUnusedLocal
def _ZoneLoadWrapper (announcementMethod: typing.Callable, self, *args, **kwargs) -> None:
	announcementMethod(self)

# noinspection PyUnusedLocal
def _ZoneSaveWrapper (announcementMethod: typing.Callable, self, save_slot_data = None, *args, **kwargs) -> None:
	announcementMethod(self, saveSlotData = save_slot_data)

# noinspection PyUnusedLocal
def _ZoneStartServicesWrapper (announcementMethod: typing.Callable, self, gameplay_zone_data, save_slot_data, *args, **kwargs) -> None:
	announcementMethod(self, gameplay_zone_data, save_slot_data)

# noinspection PyUnusedLocal
def _ZoneOnToreDownWrapper (announcementMethod: typing.Callable, self, client, *args, **kwargs) -> None:
	announcementMethod(self, client)

# noinspection PyUnusedLocal
def _ZoneUpdateWrapper (announcementMethod: typing.Callable, self, absolute_ticks, *args, **kwargs) -> None:
	announcementMethod(self, absolute_ticks)

# noinspection PyUnusedLocal
def _ServiceManagerOnZoneLoadWrapper (announcementMethod: typing.Callable, self, *args, **kwargs) -> None:
	announcementMethod(self)

# noinspection PyUnusedLocal
def _ServiceManagerOnZoneUnloadWrapper (announcementMethod: typing.Callable, self, *args, **kwargs) -> None:
	announcementMethod(self)

# noinspection PyUnusedLocal
def _GameClockTickGameClockWrapper (announcementMethod: typing.Callable, self, absolute_ticks, *args, **kwargs) -> None:
	announcementMethod(self, absolute_ticks)

_instanceManagerOnStart = _Announcement(instance_manager.InstanceManager, "on_start", Director.Announcer.InstanceManagerOnStart.__name__, announcementCallWrapper = _InstanceManagerOnStartWrapper)
_instanceManagerOnStop = _Announcement(instance_manager.InstanceManager, "on_stop", Director.Announcer.InstanceManagerOnStop.__name__, announcementCallWrapper = _InstanceManagerOnStopWrapper)
_onLoadingScreenAnimationFinished = _Announcement(zone.Zone, "on_loading_screen_animation_finished", Director.Announcer.OnLoadingScreenAnimationFinished.__name__, announcementCallWrapper = _OnLoadingScreenAnimationFinishedWrapper)
_onClientConnect = _Announcement(services, "on_client_connect", Director.Announcer.OnClientConnect.__name__, announcementCallWrapper = _OnClientConnectWrapper)
_onClientDisconnect = _Announcement(services, "on_client_disconnect", Director.Announcer.OnClientDisconnect.__name__, announcementCallWrapper = _OnClientDisconnectWrapper)
_onEnterMainMenu = _Announcement(services, "on_enter_main_menu", Director.Announcer.OnEnterMainMenu.__name__, announcementCallWrapper = _OnEnterMainMenuWrapper)
_zoneLoad = _Announcement(zone.Zone, "load_zone", Director.Announcer.ZoneLoad.__name__, announcementCallWrapper = _ZoneLoadWrapper)
_zoneSave = _Announcement(zone.Zone, "save_zone", Director.Announcer.ZoneSave.__name__, announcementCallWrapper = _ZoneSaveWrapper)
_zoneStartServices = _Announcement(zone.Zone, "start_services", Director.Announcer.ZoneStartServices.__name__, announcementCallWrapper = _ZoneStartServicesWrapper)
_zoneOnToreDown = _Announcement(zone.Zone, "on_teardown", Director.Announcer.ZoneOnToreDown.__name__, announcementCallWrapper = _ZoneOnToreDownWrapper)
_zoneUpdate = _Announcement(zone.Zone, "update", Director.Announcer.ZoneUpdate.__name__, announcementCallWrapper = _ZoneUpdateWrapper, limitErrors = True)
_serviceManagerOnZoneLoad = _Announcement(service_manager.ServiceManager, "on_zone_load", Director.Announcer.ServiceManagerOnZoneLoad.__name__, announcementCallWrapper = _ServiceManagerOnZoneLoadWrapper)
_serviceManagerOnZoneUnload = _Announcement(service_manager.ServiceManager, "on_zone_unload", Director.Announcer.ServiceManagerOnZoneUnload.__name__, announcementCallWrapper = _ServiceManagerOnZoneUnloadWrapper)
_gameClockTickGameClock = _Announcement(clock.GameClock, "tick_game_clock", Director.Announcer.GameClockTickGameClock.__name__, announcementCallWrapper = _GameClockTickGameClockWrapper, limitErrors = True)
