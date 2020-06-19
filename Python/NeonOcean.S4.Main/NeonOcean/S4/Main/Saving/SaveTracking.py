from __future__ import annotations

import typing

import zone
from NeonOcean.S4.Main import Director, Language, This
from NeonOcean.S4.Main.Saving import Save, SaveShared
from NeonOcean.S4.Main.UI import Notifications

SavingFirstTimeNotificationTitle = Language.String(This.Mod.Namespace + ".Saving.Saving_First_Time_Notifications.Title")  # type: Language.String
SavingFirstTimeNotificationText = Language.String(This.Mod.Namespace + ".Saving.Saving_First_Time_Notifications.Text")  # type: Language.String

_savingObject: SaveShared.Save

class _Announcer(Director.Announcer):
	Host = This.Mod

	@classmethod
	def ZoneLoad (cls, zoneReference: zone.Zone) -> None:
		if not GetSavingObject().LoadedFileExisted:
			_ShowSavingFirstTimeNotification()

def GetSavingObject () -> SaveShared.Save:
	return _savingObject

def _Setup () -> None:
	global _savingObject

	_savingObject = SaveShared.Save(This.Mod, This.Mod.Namespace.replace(".", "_") + "_Save_Tracking")
	Save.RegisterSavingObject(_savingObject)

def _ShowSavingFirstTimeNotification () -> None:
	notificationArguments = {
		"title": SavingFirstTimeNotificationTitle.GetCallableLocalizationString(),
		"text": SavingFirstTimeNotificationText.GetCallableLocalizationString(),
	}  # type: typing.Dict[str, typing.Any]

	Notifications.ShowNotification(queue = True, **notificationArguments)

_Setup()
