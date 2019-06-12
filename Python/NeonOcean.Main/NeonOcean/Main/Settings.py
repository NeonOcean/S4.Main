import os
import typing

from NeonOcean.Main import Debug, Language, LoadingShared, Mods, SettingsShared, This, Websites
from NeonOcean.Main.Data import Persistence
from NeonOcean.Main.Tools import Exceptions, Version
from NeonOcean.Main.UI import Settings as SettingsUI
from sims4 import localization, resources
from ui import ui_dialog

SettingsPath = os.path.join(This.Mod.PersistentPath, "Settings.json")  # type: str

_settings = None  # type: Persistence.Persistent
_allSettings = list()  # type: typing.List[typing.Type[Setting]]

class Setting(SettingsShared.SettingBase):
	IsSetting = False  # type: bool

	Key: str
	Type: typing.Type
	Default: typing.Any

	Dialog: typing.Type[SettingsUI.SettingDialog]

	def __init_subclass__ (cls, **kwargs):
		super().OnInitializeSubclass()

		if cls.IsSetting:
			cls.SetDefault()
			_allSettings.append(cls)

	@classmethod
	def Setup (cls) -> None:
		_Setup(cls.Key,
			   cls.Type,
			   cls.Default,
			   cls.Verify)

	@classmethod
	def isSetup (cls) -> bool:
		return _isSetup(cls.Key)

	@classmethod
	def Get (cls):
		return _Get(cls.Key)

	@classmethod
	def Set (cls, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
		return _Set(cls.Key, value, autoSave = autoSave, autoUpdate = autoUpdate)

	@classmethod
	def Reset (cls) -> None:
		Reset(cls.Key)

	@classmethod
	def Verify (cls, value: typing.Any, lastChangeVersion: Version.Version = None) -> typing.Any:
		return value

	@classmethod
	def IsActive (cls) -> bool:
		return True

	@classmethod
	def ShowDialog (cls):
		if not hasattr(cls, "Dialog"):
			return

		if cls.Dialog is None:
			return

		cls.Dialog.ShowDialog(cls)

	@classmethod
	def GetName (cls) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".System.Settings.Values." + cls.Key + ".Name")

class BooleanSetting(Setting):
	Type = bool

	@classmethod
	def Verify (cls, value: bool, lastChangeVersion: Version.Version = None) -> bool:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		if not isinstance(lastChangeVersion, Version.Version) and lastChangeVersion is not None:
			raise Exceptions.IncorrectTypeException(lastChangeVersion, "lastChangeVersion", (Version.Version, "None"))

		return value

class BooleanDialogSetting(BooleanSetting):
	class Dialog(SettingsUI.StandardDialog):
		HostNamespace = This.Mod.Namespace  # type: str
		HostName = This.Mod.Name  # type: str

		Values = [False, True]  # type: typing.List[bool]

		@classmethod
		def GetTitleText (cls, setting: typing.Type[SettingsShared.SettingBase]) -> localization.LocalizedString:
			return setting.GetName()

		@classmethod
		def GetDescriptionText (cls, setting: typing.Type[SettingsShared.SettingBase]) -> localization.LocalizedString:
			return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".System.Settings.Values." + setting.Key + ".Description")

		@classmethod
		def GetDefaultText (cls, setting: typing.Type[SettingsShared.SettingBase]) -> localization.LocalizedString:
			return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".System.Settings.Boolean." + str(setting.Default))

		@classmethod
		def GetDocumentationURL (cls, setting: typing.Type[SettingsShared.SettingBase]) -> typing.Optional[str]:
			return Websites.GetNODocumentationSettingURL(setting, This.Mod)

		@classmethod
		def _CreateButtons (cls,
							setting: typing.Type[SettingsShared.SettingBase],
							currentValue: typing.Any,
							showDialogArguments: typing.Dict[str, typing.Any],
							returnCallback: typing.Callable[[], None] = None,
							*args, **kwargs):

			buttons = super()._CreateButtons(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)  # type: typing.List[SettingsUI.DialogButton]

			for valueIndex in range(len(cls.Values)):  # type: int
				def CreateValueButtonCallback (value: typing.Any) -> typing.Callable:

					# noinspection PyUnusedLocal
					def ValueButtonCallback (dialog: ui_dialog.UiDialog) -> None:
						cls._ShowDialogInternal(setting, value, showDialogArguments, returnCallback = returnCallback)

					return ValueButtonCallback

				valueButtonArguments = {
					"responseID": 50000 + valueIndex + -1,
					"sortOrder": -(500 + valueIndex + -1),
					"callback": CreateValueButtonCallback(cls.Values[valueIndex]),
					"text": Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".System.Settings.Boolean." + str(cls.Values[valueIndex])),
				}

				if currentValue == cls.Values[valueIndex]:
					valueButtonArguments["selected"] = True

				valueButton = SettingsUI.ChoiceDialogButton(**valueButtonArguments)
				buttons.append(valueButton)

			return buttons

class CheckUpdatesSetting(Setting):
	Type = dict

	@classmethod
	def Verify (cls, value: dict, lastChangeVersion: Version.Version = None) -> dict:
		if not isinstance(value, dict):
			raise Exceptions.IncorrectTypeException(value, "value", (dict,))

		if not isinstance(lastChangeVersion, Version.Version) and lastChangeVersion is not None:
			raise Exceptions.IncorrectTypeException(lastChangeVersion, "lastChangeVersion", (Version.Version, "None"))

		for valueKey, valueValue in value.items():  # type: str, bool
			if not isinstance(valueKey, str):
				raise Exceptions.IncorrectTypeException(valueKey, "value[Key]", (str,))

			if not isinstance(valueValue, bool):
				raise Exceptions.IncorrectTypeException(valueValue, "value[%s]" % valueKey, (str,))

		return value

class CheckUpdatesDialogSetting(CheckUpdatesSetting):
	class Dialog(SettingsUI.PresetDialog):
		HostNamespace = This.Mod.Namespace  # type: str
		HostName = This.Mod.Name  # type: str

		DefaultSetting = None  # type: Setting

		AllModsEnabledButton = Language.String(This.Mod.Namespace + ".System.Setting_Dialogs.Check_Updates.All_Mods_Enabled_Button")  # type: Language.String
		NoModsEnabledButton = Language.String(This.Mod.Namespace + ".System.Setting_Dialogs.Check_Updates.No_Mods_Enabled_Button")  # type: Language.String

		@classmethod
		def GetTitleText (cls, setting: typing.Type[SettingsShared.SettingBase]) -> localization.LocalizedString:
			return setting.GetName()

		@classmethod
		def GetDescriptionText (cls, setting: typing.Type[SettingsShared.SettingBase]) -> localization.LocalizedString:
			return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".System.Settings.Values." + setting.Key + ".Preset_Description")

		@classmethod
		def GetDocumentationURL (cls, setting: typing.Type[SettingsShared.SettingBase]) -> typing.Optional[str]:
			return Websites.GetNODocumentationSettingURL(setting, This.Mod)

		@classmethod
		def _CreateCustomizeButtonCallback (cls,
											setting: typing.Any,
											currentValue: typing.Any,
											showDialogArguments: typing.Dict[str, typing.Any],
											returnCallback: typing.Callable[[], None] = None,
											*args, **kwargs) -> typing.Callable[[ui_dialog.UiDialog], None]:

			# noinspection PyUnusedLocal
			def CustomizeButtonCallback (dialog: ui_dialog.UiDialog) -> None:
				# noinspection PyUnusedLocal
				def CustomizeDialogReturnCallback () -> None:
					cls.ShowDialog(setting, returnCallback = returnCallback)

				setting.DictionaryDialog.ShowDialog(setting, returnCallback = CustomizeDialogReturnCallback)

			return CustomizeButtonCallback

		@classmethod
		def _CreateButtons (cls,
							setting: typing.Type[SettingsShared.SettingBase],
							currentValue: typing.Any,
							showDialogArguments: typing.Dict[str, typing.Any],
							returnCallback: typing.Callable[[], None] = None,
							*args, **kwargs) -> typing.List[SettingsUI.DialogButton]:

			buttons = super()._CreateButtons(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)  # type: typing.List[SettingsUI.DialogButton]

			allModsEnabledSelected = True  # type: bool
			noModsEnabledSelected = True  # type: bool

			for settingValue in currentValue.values():  # type: str
				if settingValue is False:
					allModsEnabledSelected = False
				elif settingValue is True:
					noModsEnabledSelected = False

			if allModsEnabledSelected and noModsEnabledSelected:
				noModsEnabledSelected = False

			# noinspection PyUnusedLocal
			def NoModsEnabledButtonCallback (dialog: ui_dialog.UiDialog) -> None:

				# noinspection PyUnusedLocal
				def NoModsEnabledButtonConfirmCallback (confirmDialog: ui_dialog.UiDialog) -> None:
					if confirmDialog.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
						newValue = dict()

						for mod in Mods.GetAllMods():  # type: Mods.Mod
							newValue[mod.Namespace] = False

						setting.Set(newValue)

						cls._ShowDialogInternal(setting, newValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)
					elif confirmDialog.response == ui_dialog.ButtonType.DIALOG_RESPONSE_CANCEL:
						cls._ShowDialogInternal(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)

				SettingsUI.ShowPresetConfirmDialog(NoModsEnabledButtonConfirmCallback)

			noModsEnabledButtonArguments = {
				"responseID": 50000,
				"sortOrder": -500,
				"callback": NoModsEnabledButtonCallback,
				"text": cls.NoModsEnabledButton.GetLocalizationString(),
				"selected": noModsEnabledSelected
			}

			noModsEnabledButton = SettingsUI.ChoiceDialogButton(**noModsEnabledButtonArguments)
			buttons.append(noModsEnabledButton)

			# noinspection PyUnusedLocal
			def AllModsEnabledButtonCallback (dialog: ui_dialog.UiDialog) -> None:

				# noinspection PyUnusedLocal
				def AllModsEnabledButtonConfirmCallback (confirmDialog: ui_dialog.UiDialog) -> None:
					if confirmDialog.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
						newValue = dict()

						for mod in Mods.GetAllMods():  # type: Mods.Mod
							newValue[mod.Namespace] = True

						setting.Set(newValue)

						cls._ShowDialogInternal(setting, newValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)
					elif confirmDialog.response == ui_dialog.ButtonType.DIALOG_RESPONSE_CANCEL:
						cls._ShowDialogInternal(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)

				SettingsUI.ShowPresetConfirmDialog(AllModsEnabledButtonConfirmCallback)

			allModsEnabledButtonArguments = {
				"responseID": 50001,
				"sortOrder": -501,
				"callback": AllModsEnabledButtonCallback,
				"text": cls.AllModsEnabledButton.GetLocalizationString(),
				"selected": allModsEnabledSelected
			}

			allModsEnabledButton = SettingsUI.ChoiceDialogButton(**allModsEnabledButtonArguments)
			buttons.append(allModsEnabledButton)

			return buttons

	class DictionaryDialog(SettingsUI.DictionaryDialog):
		HostNamespace = This.Mod.Namespace  # type: str
		HostName = This.Mod.Name  # type: str

		DefaultSetting = None  # type: Setting

		# noinspection SpellCheckingInspection
		EnabledIcon = resources.ResourceKeyWrapper("00B2D882:00000000:0F152249F46001EA")
		# noinspection SpellCheckingInspection
		DisabledIcon = resources.ResourceKeyWrapper("00B2D882:00000000:A4DB6EBAE174821B")

		@classmethod
		def GetTitleText (cls, setting: typing.Type[SettingsShared.SettingBase]) -> localization.LocalizedString:
			return setting.GetName()

		@classmethod
		def GetDescriptionText (cls, setting: typing.Type[SettingsShared.SettingBase]) -> localization.LocalizedString:
			return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".System.Settings.Values." + setting.Key + ".Description")

		@classmethod
		def GetDefaultText (cls, setting: typing.Type[SettingsShared.SettingBase]) -> localization.LocalizedString:
			return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".System.Settings.Boolean." + str(cls.DefaultSetting.Get()))

		@classmethod
		def GetDocumentationURL (cls, setting: typing.Type[SettingsShared.SettingBase]) -> typing.Optional[str]:
			return Websites.GetNODocumentationSettingURL(setting, This.Mod)

		@classmethod
		def GetKeyText (cls, setting: typing.Type[SettingsShared.SettingBase], mod: Mods.Mod) -> localization.LocalizedString:
			keyTemplate = Language.String(This.Mod.Namespace + ".System.Settings.Values." + setting.Key + ".Key_Template")  # type: Language.String
			return keyTemplate.GetLocalizationString(mod.Name, mod.Author)

		@classmethod
		def _CreateRows (cls,
						 setting: typing.Type[SettingsShared.SettingBase],
						 currentValue: typing.Any,
						 showDialogArguments: typing.Dict[str, typing.Any],
						 returnCallback: typing.Callable[[], None] = None,
						 *args, **kwargs) -> typing.List[SettingsUI.DialogRow]:

			rows = super()._CreateRows(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)  # type: typing.List[SettingsUI.DialogRow]

			defaultValue = cls.DefaultSetting.Get()  # type: bool

			allMods = Mods.GetAllMods()  # type: typing.List[Mods.Mod]
			for modIndex in range(len(allMods)):  # type: int
				if allMods[modIndex].Distribution is None:
					continue

				modEnabled = defaultValue  # type: bool

				if allMods[modIndex].Namespace in currentValue:
					modEnabled = currentValue[allMods[modIndex].Namespace]

				def CreateModButtonCallback (mod: Mods.Mod, lastValue: bool) -> typing.Callable:

					# noinspection PyUnusedLocal
					def ModButtonCallback (dialog: ui_dialog.UiDialog) -> None:
						if lastValue:
							currentValue[mod.Namespace] = False
							cls._ShowDialogInternal(setting, currentValue, showDialogArguments, returnCallback = returnCallback)
						else:
							currentValue[mod.Namespace] = True
							cls._ShowDialogInternal(setting, currentValue, showDialogArguments, returnCallback = returnCallback)

					return ModButtonCallback

				rowArguments = {
					"optionID": (50000 + modIndex + -1),
					"callback": CreateModButtonCallback(allMods[modIndex], modEnabled),
					"text": cls.GetKeyText(setting, allMods[modIndex]),
					"description": Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".System.Settings.Boolean." + str(modEnabled)),
					"icon": cls.EnabledIcon if modEnabled else cls.DisabledIcon
				}

				rows.append(SettingsUI.DialogRow(**rowArguments))

			return rows

class CheckForUpdatesDefault(BooleanDialogSetting):
	IsSetting = True

	Key = "Check_For_Updates_Default"  # type: str
	Default = True

	@classmethod
	def Set (cls, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
		settingIsSetup = cls.isSetup()  # type: bool
		updatesSettingIsSetup = CheckUpdatesSetting.isSetup()  # type: bool

		currentValue = None  # type: bool
		checkUpdatesDictionary = None  # type: typing.Dict[str, bool]

		if settingIsSetup and updatesSettingIsSetup:
			currentValue = cls.Get()  # type: bool
			checkUpdatesDictionary = CheckForUpdates.Get()  # type: typing.Dict[str, bool]

		super().Set(value, autoSave = autoSave, autoUpdate = autoUpdate)

		if settingIsSetup and updatesSettingIsSetup:
			if not currentValue and value:
				for mod in Mods.GetAllMods():  # type: Mods.Mod
					if mod.Namespace not in checkUpdatesDictionary:
						checkUpdatesDictionary[mod.Namespace] = False
			elif currentValue and not value:
				for mod in Mods.GetAllMods():  # type: Mods.Mod
					if mod.Namespace not in checkUpdatesDictionary:
						checkUpdatesDictionary[mod.Namespace] = True

		CheckForUpdates.Set(checkUpdatesDictionary, autoSave = autoSave, autoUpdate = autoUpdate)

class CheckForUpdates(CheckUpdatesDialogSetting):
	IsSetting = True  # type: bool

	Key = "Check_For_Updates"  # type: str
	Default = dict()  # type: bool

	class Dialog(CheckUpdatesDialogSetting.Dialog):
		DefaultSetting = CheckForUpdatesDefault

	class DictionaryDialog(CheckUpdatesDialogSetting.DictionaryDialog):
		DefaultSetting = CheckForUpdatesDefault

class CheckForPreviewUpdatesDefault(BooleanDialogSetting):
	IsSetting = True

	Key = "Check_For_Preview_Updates_Default"  # type: str
	Default = False

	@classmethod
	def Set (cls, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
		settingIsSetup = cls.isSetup()  # type: bool
		checkPreviewUpdatesSettingIsSetup = CheckForPreviewUpdates.isSetup()  # type: bool

		currentValue = None  # type: bool
		checkPreviewUpdatesDictionary = None  # type: typing.Dict[str, bool]

		if settingIsSetup and checkPreviewUpdatesSettingIsSetup:
			currentValue = cls.Get()  # type: bool
			checkPreviewUpdatesDictionary = CheckForPreviewUpdates.Get()  # type: typing.Dict[str, bool]

		super().Set(value, autoSave = autoSave, autoUpdate = autoUpdate)

		if settingIsSetup and checkPreviewUpdatesSettingIsSetup:
			if not currentValue and value:
				for mod in Mods.GetAllMods():  # type: Mods.Mod
					if mod.Namespace not in checkPreviewUpdatesDictionary:
						checkPreviewUpdatesDictionary[mod.Namespace] = False
			elif currentValue and not value:
				for mod in Mods.GetAllMods():  # type: Mods.Mod
					if mod.Namespace not in checkPreviewUpdatesDictionary:
						checkPreviewUpdatesDictionary[mod.Namespace] = True

			CheckForPreviewUpdates.Set(checkPreviewUpdatesDictionary, autoSave = autoSave, autoUpdate = autoUpdate)

class CheckForPreviewUpdates(CheckUpdatesDialogSetting):
	IsSetting = True  # type: bool

	Key = "Check_For_Preview_Updates"  # type: str
	Default = dict()  # type: bool

	class Dialog(CheckUpdatesDialogSetting.Dialog):
		DefaultSetting = CheckForPreviewUpdatesDefault

	class DictionaryDialog(CheckUpdatesDialogSetting.DictionaryDialog):
		DefaultSetting = CheckForPreviewUpdatesDefault

class ShowPromotions(BooleanDialogSetting):
	IsSetting = True  # type: bool

	Key = "Show_Promotions"  # type: str
	Default = True  # type: bool

def GetAllSettings () -> typing.List[typing.Type[Setting]]:
	return list(_allSettings)

def Load () -> None:
	_settings.Load()

def Save () -> None:
	_settings.Save()

def Reset (key: str = None) -> None:
	_settings.Reset(key = key)

def Update () -> None:
	_settings.Update()

def RegisterUpdate (update: typing.Callable) -> None:
	_settings.RegisterUpdate(update)

def UnregisterUpdate (update: typing.Callable) -> None:
	_settings.UnregisterUpdate(update)

def _OnInitiate (cause: LoadingShared.LoadingCauses) -> None:
	global _settings

	if cause:
		pass

	if _settings is None:
		_settings = Persistence.Persistent(SettingsPath, This.Mod.Version, hostNamespace = This.Mod.Namespace)

		for setting in _allSettings:
			setting.Setup()

	Load()

def _OnUnload (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	try:
		Save()
	except:
		Debug.Log("Failed to save settings.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _OnReset () -> None:
	Reset()

def _OnResetSettings () -> None:
	Reset()

def _Setup (key: str, valueType: type, default, verify: typing.Callable) -> None:
	_settings.Setup(key, valueType, default, verify)

def _isSetup (key: str) -> bool:
	return _settings.isSetup(key)

def _Get (key: str) -> typing.Any:
	return _settings.Get(key)

def _Set (key: str, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
	_settings.Set(key, value, autoSave = autoSave, autoUpdate = autoUpdate)
