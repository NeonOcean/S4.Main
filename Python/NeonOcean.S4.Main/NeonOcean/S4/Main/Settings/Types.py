from __future__ import annotations

import typing

from NeonOcean.S4.Main import Language, Mods, This
from NeonOcean.S4.Main.Settings import Base as SettingsBase, Dialogs as SettingsDialogs
from NeonOcean.S4.Main.Tools import Exceptions, Version
from sims4 import localization

class BooleanSetting (SettingsBase.Setting):
	Type = bool

	@classmethod
	def Verify (cls, value: bool, lastChangeVersion: Version.Version = None) -> bool:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		if not isinstance(lastChangeVersion, Version.Version) and lastChangeVersion is not None:
			raise Exceptions.IncorrectTypeException(lastChangeVersion, "lastChangeVersion", (Version.Version, "None"))

		return value

	@classmethod
	def GetValueText (cls, value: typing.Any) -> localization.LocalizedString:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		valueString = str(value)  # type: str
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Boolean." + valueString, fallbackText = valueString)

class BooleanDialogSetting (BooleanSetting):
	Dialog = SettingsDialogs.BooleanDialog

class BooleanEnabledDisabledSetting (BooleanSetting):
	@classmethod
	def GetValueText (cls, value: typing.Any) -> localization.LocalizedString:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		valueString = str(value)  # type: str
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Boolean.Enabled_Disabled." + valueString, fallbackText = valueString)

class BooleanEnabledDisabledDialogSetting(BooleanEnabledDisabledSetting):
	Dialog = SettingsDialogs.BooleanEnabledDisabledDialog

class BooleanYesNoSetting (BooleanSetting):
	@classmethod
	def GetValueText (cls, value: typing.Any) -> localization.LocalizedString:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		valueString = str(value)  # type: str
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Boolean.Yes_No." + valueString, fallbackText = valueString)

class BooleanYesNoDialogSetting(BooleanYesNoSetting):
	Dialog = SettingsDialogs.BooleanYesNoDialog

class CheckForUpdatesSetting(SettingsBase.Setting):
	Type = dict

	DefaultSetting: typing.Type[SettingsBase.Setting]

	AllModsEnabledText = Language.String(This.Mod.Namespace + ".Settings.Types.Check_For_Updates.All_Mods_Enabled", fallbackText = "Check_For_Updates.All_Mods_Enabled")  # type: Language.String
	NoModsEnabledText = Language.String(This.Mod.Namespace + ".Settings.Types.Check_For_Updates.No_Mods_Enabled", fallbackText = "Check_For_Updates.No_Mods_Enabled")  # type: Language.String
	CustomizedText = Language.String(This.Mod.Namespace + ".Settings.Types.Check_For_Updates.Customized", fallbackText = "Check_For_Updates.Customized")  # type: Language.String

	@classmethod
	def Verify (cls, value: dict, lastChangeVersion: Version.Version = None) -> dict:
		if not isinstance(value, dict):
			raise Exceptions.IncorrectTypeException(value, "value", (dict,))

		if not isinstance(lastChangeVersion, Version.Version) and lastChangeVersion is not None:
			raise Exceptions.IncorrectTypeException(lastChangeVersion, "lastChangeVersion", (Version.Version, "None"))

		for valueKey, valueValue in value.items():  # type: str, bool
			if not isinstance(valueKey, str):
				raise Exceptions.IncorrectTypeException(valueKey, "value<Key>", (str,))

			if not isinstance(valueValue, bool):
				raise Exceptions.IncorrectTypeException(valueValue, "value[%s]" % valueKey, (str,))

		return value

	@classmethod
	def GetValueText (cls, value: typing.Any) -> localization.LocalizedString:
		if not isinstance(value, dict):
			raise Exceptions.IncorrectTypeException(value, "value", (dict,))

		for valueKey, valueValue in value.items():  # type: str, bool
			if not isinstance(valueKey, str):
				raise Exceptions.IncorrectTypeException(valueKey, "value<Key>", (str,))

			if not isinstance(valueValue, bool):
				raise Exceptions.IncorrectTypeException(valueValue, "value[%s]" % valueKey, (str,))

		value = cls.Get()  # type: dict
		defaultSettingValue = cls.DefaultSetting.Get()  # type: bool

		if len(value) == 0:
			if defaultSettingValue:
				return cls.AllModsEnabledText.GetLocalizationString()
			else:
				return cls.NoModsEnabledText.GetLocalizationString()

		allModsEnabled = True  # type: bool
		noModsEnabled = True  # type: bool

		for settingValue in value.values():  # type: str
			if settingValue is False:
				allModsEnabled = False
			elif settingValue is True:
				noModsEnabled = False

		if allModsEnabled and noModsEnabled:
			noModsEnabled = False

		if allModsEnabled:
			return cls.AllModsEnabledText.GetLocalizationString()
		elif noModsEnabled:
			return cls.NoModsEnabledText.GetLocalizationString()
		else:
			return cls.CustomizedText.GetLocalizationString()

	@classmethod
	def _OnLoad (cls) -> None:
		currentValue = cls.Get()  # type: typing.Dict[str, bool]
		defaultValue = cls.DefaultSetting.Get()  # type: bool

		currentValueChanged = False  # type: bool

		for mod in Mods.GetAllMods():  # type: Mods.Mod
			if mod.Distribution.UpdatesController is None:
				continue

			if mod.Namespace not in currentValue:
				currentValue[mod.Namespace] = defaultValue
				currentValueChanged = True

		if currentValueChanged:
			cls.Set(currentValue)

class CheckForUpdatesDialogSetting(CheckForUpdatesSetting):
	Dialog = SettingsDialogs.CheckForUpdatesPresetDialog
	ValueDialog = SettingsDialogs.CheckForUpdatesValueDialog
