from __future__ import annotations

import types
import typing

from NeonOcean.S4.Main import Mods
from NeonOcean.S4.Main.Settings import Base as SettingsBase, Dialogs as SettingsDialogs, Types as SettingsTypes
from NeonOcean.S4.Main.Tools import Events

class CheckForUpdatesDefault(SettingsTypes.BooleanEnabledDisabledDialogSetting):
	IsSetting = True

	Key = "Check_For_Updates_Default"  # type: str
	Default = True

	@classmethod
	def Set (cls, value: bool, autoSave: bool = True, autoUpdate: bool = True) -> None:
		previousValue = cls.Get()  # type: bool
		super().Set(value, autoSave = autoSave, autoUpdate = autoUpdate)
		cls._ApplyDefault(previousValue, autoSave = autoSave, autoUpdate = autoUpdate)

	@classmethod
	def Reset (cls, autoSave: bool = True, autoUpdate: bool = True) -> None:
		previousValue = cls.Get()  # type: bool
		super().Reset(autoSave = autoSave, autoUpdate = autoUpdate)
		cls._ApplyDefault(previousValue, autoSave = autoSave, autoUpdate = autoUpdate)

	@classmethod
	def _ApplyDefault (cls, value: bool, autoSave: bool = True, autoUpdate: bool = True) -> None:
		updatesSetting = CheckForUpdates  # type: typing.Type[SettingsBase.Setting]

		if cls.IsSetup() and updatesSetting.IsSetup():
			updatesValue = updatesSetting.Get()  # type: typing.Dict[str, bool]
			updatesValueChanged = False  # type: bool

			for mod in Mods.GetAllMods():  # type: Mods.Mod
				if mod.Distribution.UpdatesController is None:
					continue

				if mod.Namespace not in updatesValue:
					updatesValue[mod.Namespace] = value
					updatesValueChanged = True

			if updatesValueChanged:
				updatesSetting.Set(updatesValue, autoSave = autoSave, autoUpdate = autoUpdate)

class CheckForUpdates(SettingsTypes.CheckForUpdatesDialogSetting):
	IsSetting = True  # type: bool

	Key = "Check_For_Updates"  # type: str
	Default = dict()  # type: bool

	DefaultSetting = CheckForUpdatesDefault

	class Dialog(SettingsTypes.CheckForUpdatesDialogSetting.Dialog):
		DefaultSetting = CheckForUpdatesDefault

	class ValueDialog(SettingsTypes.CheckForUpdatesDialogSetting.ValueDialog):
		DefaultSetting = CheckForUpdatesDefault

	@classmethod
	def _OnLoad (cls) -> None:
		defaultSetting = cls.DefaultSetting  # type: typing.Type[SettingsBase.Setting]

		currentValue = cls.Get()  # type: typing.Dict[str, bool]
		defaultValue = defaultSetting.Get()  # type: bool

		currentValueChanged = False  # type: bool

		for mod in Mods.GetAllMods():  # type: Mods.Mod
			if mod.Distribution.UpdatesController is None:
				continue

			if mod.Namespace not in currentValue:
				currentValue[mod.Namespace] = defaultValue
				currentValueChanged = True

		if currentValueChanged:
			cls.Set(currentValue)

class CheckForPreviewUpdatesDefault(SettingsTypes.BooleanEnabledDisabledDialogSetting):
	IsSetting = True

	Key = "Check_For_Preview_Updates_Default"  # type: str
	Default = False

	@classmethod
	def Set (cls, value: bool, autoSave: bool = True, autoUpdate: bool = True) -> None:
		previousValue = cls.Get()  # type: bool
		super().Set(value, autoSave = autoSave, autoUpdate = autoUpdate)
		cls._ApplyDefault(previousValue, autoSave = autoSave, autoUpdate = autoUpdate)

	@classmethod
	def Reset (cls, autoSave: bool = True, autoUpdate: bool = True) -> None:
		previousValue = cls.Get()  # type: bool
		super().Reset(autoSave = autoSave, autoUpdate = autoUpdate)
		cls._ApplyDefault(previousValue, autoSave = autoSave, autoUpdate = autoUpdate)

	@classmethod
	def _ApplyDefault (cls, value: bool, autoSave: bool = True, autoUpdate: bool = True) -> None:
		updatesSetting = CheckForPreviewUpdates  # type: typing.Type[SettingsBase.Setting]

		if cls.IsSetup() and updatesSetting.IsSetup():
			updatesValue = updatesSetting.Get()  # type: typing.Dict[str, bool]
			updatesValueChanged = False  # type: bool

			for mod in Mods.GetAllMods():  # type: Mods.Mod
				if mod.Distribution.UpdatesController is None:
					continue

				if mod.Namespace not in updatesValue:
					updatesValue[mod.Namespace] = value
					updatesValueChanged = True

			if updatesValueChanged:
				updatesSetting.Set(updatesValue, autoSave = autoSave, autoUpdate = autoUpdate)

class CheckForPreviewUpdates(SettingsTypes.CheckForUpdatesDialogSetting):
	IsSetting = True  # type: bool

	Key = "Check_For_Preview_Updates"  # type: str
	Default = dict()  # type: bool

	DefaultSetting = CheckForPreviewUpdatesDefault

	class Dialog(SettingsTypes.CheckForUpdatesDialogSetting.Dialog):
		DefaultSetting = CheckForPreviewUpdatesDefault

	class ValueDialog(SettingsTypes.CheckForUpdatesDialogSetting.ValueDialog):
		DefaultSetting = CheckForPreviewUpdatesDefault

	@classmethod
	def _OnLoad (cls) -> None:
		defaultSetting = cls.DefaultSetting  # type: typing.Type[SettingsBase.Setting]

		currentValue = cls.Get()  # type: typing.Dict[str, bool]
		defaultValue = defaultSetting.Get()  # type: bool

		currentValueChanged = False  # type: bool

		for mod in Mods.GetAllMods():  # type: Mods.Mod
			if mod.Distribution.UpdatesController is None:
				continue

			if mod.Namespace not in currentValue:
				currentValue[mod.Namespace] = defaultValue
				currentValueChanged = True

		if currentValueChanged:
			cls.Set(currentValue)

class ShowPromotions(SettingsTypes.BooleanYesNoDialogSetting):
	IsSetting = True  # type: bool

	Key = "Show_Promotions"  # type: str
	Default = True  # type: bool

def GetSettingsFilePath () -> str:
	return SettingsBase.SettingsFilePath

def GetAllSettings () -> typing.List[typing.Type[SettingsBase.Setting]]:
	return list(SettingsBase.AllSettings)

def Load () -> None:
	SettingsBase.Load()

def Save () -> None:
	SettingsBase.Save()

def Update () -> None:
	SettingsBase.Update()

def RegisterOnUpdateCallback (updateCallback: typing.Callable[[types.ModuleType, SettingsBase.UpdateEventArguments], None]) -> None:
	SettingsBase.RegisterOnUpdateCallback(updateCallback)

def UnregisterOnUpdateCallback (updateCallback: typing.Callable[[types.ModuleType, SettingsBase.UpdateEventArguments], None]) -> None:
	SettingsBase.UnregisterOnUpdateCallback(updateCallback)

def RegisterOnLoadCallback (loadCallback: typing.Callable[[types.ModuleType, Events.EventArguments], None]) -> None:
	SettingsBase.RegisterOnLoadCallback(loadCallback)

def UnregisterOnLoadCallback (loadCallback: typing.Callable[[types.ModuleType, Events.EventArguments], None]) -> None:
	SettingsBase.UnregisterOnLoadCallback(loadCallback)
