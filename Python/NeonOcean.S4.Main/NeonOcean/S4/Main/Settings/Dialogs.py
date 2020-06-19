from __future__ import annotations

import typing

from NeonOcean.S4.Main import Language, Mods, This, Websites
from NeonOcean.S4.Main.Abstract import Settings as AbstractSettings
from NeonOcean.S4.Main.UI import Resources as UIResources, Settings as UISettings, SettingsShared as UISettingsShared
from sims4 import localization, resources
from ui import ui_dialog

class BooleanDialog(UISettings.StandardDialog):
	HostNamespace = This.Mod.Namespace  # type: str
	HostName = This.Mod.Name  # type: str

	Values = [True, False]  # type: typing.List[bool]

	def _GetDescriptionSettingText (self, setting: UISettingsShared.SettingStandardWrapper) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Mod_Settings.Values." + setting.Key + ".Description")

	def _GetDescriptionDocumentationURL (self, setting: UISettingsShared.SettingStandardWrapper) -> typing.Optional[str]:
		return Websites.GetNODocumentationModSettingURL(setting.Setting, This.Mod)

	def _GetValueText (self, value: bool) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Boolean." + str(value), fallbackText = str(value))

	def _CreateButtons (self,
						setting: UISettingsShared.SettingStandardWrapper,
						currentValue: typing.Any,
						showDialogArguments: typing.Dict[str, typing.Any],
						returnCallback: typing.Callable[[], None] = None,
						*args, **kwargs):

		buttons = super()._CreateButtons(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)  # type: typing.List[UISettings.DialogButton]

		for valueIndex in range(len(self.Values)):  # type: int
			def CreateValueButtonCallback (value: typing.Any) -> typing.Callable:

				# noinspection PyUnusedLocal
				def ValueButtonCallback (dialog: ui_dialog.UiDialog) -> None:
					self._ShowDialogInternal(setting, value, showDialogArguments, returnCallback = returnCallback)

				return ValueButtonCallback

			valueButtonArguments = {
				"responseID": 50000 + valueIndex * -5,
				"sortOrder": -(500 + valueIndex * -5),
				"callback": CreateValueButtonCallback(self.Values[valueIndex]),
				"text": self._GetValueText(self.Values[valueIndex]),
			}

			if currentValue == self.Values[valueIndex]:
				valueButtonArguments["selected"] = True

			valueButton = UISettings.ChoiceDialogButton(**valueButtonArguments)
			buttons.append(valueButton)

		return buttons

class BooleanYesNoDialog(BooleanDialog):
	def _GetValueText (self, value: bool) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Boolean.Yes_No." + str(value), fallbackText = str(value))

class BooleanEnabledDisabledDialog(BooleanDialog):
	def _GetValueText (self, value: bool) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Boolean.Enabled_Disabled." + str(value), fallbackText = str(value))

class CheckForUpdatesPresetDialog(UISettings.PresetDialog):
	HostNamespace = This.Mod.Namespace  # type: str
	HostName = This.Mod.Name  # type: str

	DefaultSetting = None  # type: AbstractSettings.SettingAbstract

	def _GetDescriptionSettingText (self, setting: UISettingsShared.SettingStandardWrapper) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Mod_Settings.Values." + setting.Key + ".Preset_Description")

	def _GetDescriptionDocumentationURL (self, setting: UISettingsShared.SettingStandardWrapper) -> typing.Optional[str]:
		return Websites.GetNODocumentationModSettingURL(setting.Setting, This.Mod)

	def _GetAllModsEnabledButtonText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Check_For_Updates.All_Mods_Enabled", fallbackText = "All_Mods_Enabled")

	def _GetNoModsEnabledButtonText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Check_For_Updates.No_Mods_Enabled", fallbackText = "No_Mods_Enabled")

	# noinspection PyUnusedLocal
	def _CreateChangeAllButtonCallback (self,
										selectedModValue: bool,
										setting: typing.Any,
										currentValue: typing.Dict[str, bool],
										showDialogArguments: typing.Dict[str, typing.Any],
										returnCallback: typing.Callable[[], None] = None,
										*args, **kwargs) -> typing.Callable[[ui_dialog.UiDialog], None]:

		# noinspection PyUnusedLocal
		def ChangeAllButtonCallback (dialog: ui_dialog.UiDialog) -> None:

			# noinspection PyUnusedLocal
			def ChangeAllButtonConfirmCallback (confirmDialog: ui_dialog.UiDialog) -> None:
				if confirmDialog.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
					newValue = dict()

					for mod in Mods.GetAllMods():  # type: Mods.Mod
						newValue[mod.Namespace] = selectedModValue

					setting.Set(newValue)

					self._ShowDialogInternal(setting, newValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)
				elif confirmDialog.response == ui_dialog.ButtonType.DIALOG_RESPONSE_CANCEL:
					self._ShowDialogInternal(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)

			UISettings.ShowPresetConfirmDialog(ChangeAllButtonConfirmCallback)

		return ChangeAllButtonCallback

	def _CreateCustomizeButtonCallback (self,
										setting: typing.Any,
										currentValue: typing.Any,
										showDialogArguments: typing.Dict[str, typing.Any],
										returnCallback: typing.Callable[[], None] = None,
										*args, **kwargs) -> typing.Callable[[ui_dialog.UiDialog], None]:

		# noinspection PyUnusedLocal
		def CustomizeButtonCallback (dialog: ui_dialog.UiDialog) -> None:
			# noinspection PyUnusedLocal
			def CustomizeDialogReturnCallback () -> None:
				self.ShowDialog(setting, returnCallback = returnCallback)

			settingValueDialog = setting.Setting.ValueDialog()  # type: UISettings.SettingDialogBase
			settingValueDialog.ShowDialog(setting, returnCallback = CustomizeDialogReturnCallback)

		return CustomizeButtonCallback

	def _CreateButtons (self,
						setting: UISettingsShared.SettingStandardWrapper,
						currentValue: typing.Any,
						showDialogArguments: typing.Dict[str, typing.Any],
						returnCallback: typing.Callable[[], None] = None,
						*args, **kwargs) -> typing.List[UISettings.DialogButton]:

		buttons = super()._CreateButtons(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)  # type: typing.List[UISettings.DialogButton]

		defaultValue = self.DefaultSetting.Get()  # type: bool

		allModsEnabledSelected = True  # type: bool
		noModsEnabledSelected = True  # type: bool

		if len(currentValue) == 0:
			if defaultValue:
				noModsEnabledSelected = False
			else:
				allModsEnabledSelected = False
		else:
			for settingValue in currentValue.values():  # type: str
				if settingValue is False:
					allModsEnabledSelected = False
				elif settingValue is True:
					noModsEnabledSelected = False

			if allModsEnabledSelected and noModsEnabledSelected:
				noModsEnabledSelected = False

		allModsEnabledButtonArguments = {
			"responseID": 50000,
			"sortOrder": -500,
			"callback": self._CreateChangeAllButtonCallback(True, setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs),
			"text": self._GetAllModsEnabledButtonText(),
			"selected": allModsEnabledSelected
		}

		allModsEnabledButton = UISettings.ChoiceDialogButton(**allModsEnabledButtonArguments)
		buttons.append(allModsEnabledButton)

		noModsEnabledButtonArguments = {
			"responseID": 50005,
			"sortOrder": -495,
			"callback": self._CreateChangeAllButtonCallback(False, setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs),
			"text": self._GetNoModsEnabledButtonText(),
			"selected": noModsEnabledSelected
		}

		noModsEnabledButton = UISettings.ChoiceDialogButton(**noModsEnabledButtonArguments)
		buttons.append(noModsEnabledButton)

		return buttons

class CheckForUpdatesValueDialog(UISettings.DictionaryDialog):
	HostNamespace = This.Mod.Namespace  # type: str
	HostName = This.Mod.Name  # type: str

	DefaultSetting = None  # type: AbstractSettings.SettingAbstract

	def _GetDescriptionSettingText (self, setting: UISettingsShared.SettingStandardWrapper) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Mod_Settings.Values." + setting.Key + ".Description")

	def _GetDescriptionDefaultText (self, setting: UISettingsShared.SettingStandardWrapper) -> localization.LocalizedString:
		defaultSettingString = str(self.DefaultSetting.Get())  # type: str
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Boolean.Enabled_Disabled." + defaultSettingString, fallbackText = defaultSettingString)

	def _GetDescriptionDocumentationURL (self, setting: UISettingsShared.SettingStandardWrapper) -> typing.Optional[str]:
		return Websites.GetNODocumentationModSettingURL(setting.Setting, This.Mod)

	# noinspection PyUnusedLocal
	def _GetKeyText (self, setting: UISettingsShared.SettingStandardWrapper, mod: Mods.Mod, value: bool) -> localization.LocalizedString:
		keyTemplate = Language.String(This.Mod.Namespace + ".Mod_Settings.Values." + setting.Key + ".Key_Template")  # type: Language.String
		return keyTemplate.GetLocalizationString(mod.Name, mod.Author)

	# noinspection PyUnusedLocal
	def _GetValueText (self, setting: UISettingsShared.SettingStandardWrapper, mod: Mods.Mod, value: bool) -> localization.LocalizedString:
		valueTemplate = Language.String(This.Mod.Namespace + ".Mod_Settings.Values." + setting.Key + ".Value_Template")  # type: Language.String
		return valueTemplate.GetLocalizationString(
			Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Boolean.Enabled_Disabled." + str(value), fallbackText = str(value)),
			str(mod.Distribution.UpdatesFileURL)
		)

	def _GetEnabledButtonIconKey (self) -> str:
		return UIResources.PickerCheckIconKey

	def _GetDisabledButtonIconKey (self) -> str:
		return UIResources.PickerBlankIconKey

	def _CreateRows (self,
					 setting: UISettingsShared.SettingStandardWrapper,
					 currentValue: typing.Any,
					 showDialogArguments: typing.Dict[str, typing.Any],
					 returnCallback: typing.Callable[[], None] = None,
					 *args, **kwargs) -> typing.List[UISettings.DialogRow]:

		rows = super()._CreateRows(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)  # type: typing.List[UISettings.DialogRow]

		defaultValue = self.DefaultSetting.Get()  # type: bool

		allMods = Mods.GetAllMods()  # type: typing.List[Mods.Mod]
		for modIndex in range(len(allMods)):  # type: int
			if allMods[modIndex].Distribution.UpdatesController is None:
				continue

			if allMods[modIndex].Distribution.UpdatesFileURL is None:
				continue

			if allMods[modIndex].Distribution.DownloadURL is None:
				continue

			modEnabled = defaultValue  # type: bool

			if allMods[modIndex].Namespace in currentValue:
				modEnabled = currentValue[allMods[modIndex].Namespace]

			def CreateModButtonCallback (mod: Mods.Mod, lastValue: bool) -> typing.Callable:

				# noinspection PyUnusedLocal
				def ModButtonCallback (dialog: ui_dialog.UiDialog) -> None:
					if lastValue:
						currentValue[mod.Namespace] = False
						self._ShowDialogInternal(setting, currentValue, showDialogArguments, returnCallback = returnCallback)
					else:
						currentValue[mod.Namespace] = True
						self._ShowDialogInternal(setting, currentValue, showDialogArguments, returnCallback = returnCallback)

				return ModButtonCallback

			rowArguments = {
				"optionID": (50000 + modIndex + -1),
				"callback": CreateModButtonCallback(allMods[modIndex], modEnabled),
				"text": self._GetKeyText(setting, allMods[modIndex], modEnabled),
				"description": self._GetValueText(setting, allMods[modIndex], modEnabled),
				"icon": resources.ResourceKeyWrapper(self._GetEnabledButtonIconKey()) if modEnabled else resources.ResourceKeyWrapper(self._GetDisabledButtonIconKey())
			}

			rows.append(UISettings.DialogRow(**rowArguments))

		return rows
