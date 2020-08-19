from __future__ import annotations

import abc
import traceback
import typing

import services
from NeonOcean.S4.Main import Debug, Language, This
from NeonOcean.S4.Main.Tools import Exceptions, TextBuilder
from NeonOcean.S4.Main.UI import Dialogs, Notifications, SettingsShared as UISettingsShared
from sims4 import collections, localization
from ui import ui_dialog, ui_dialog_generic, ui_dialog_notification, ui_dialog_picker, ui_text_input

InvalidInputNotificationTitle = Language.String(This.Mod.Namespace + ".Setting_Dialogs.Invalid_Input_Notification.Title")  # type: Language.String
InvalidInputNotificationText = Language.String(This.Mod.Namespace + ".Setting_Dialogs.Invalid_Input_Notification.Text")  # type: Language.String

PresetConfirmDialogTitle = Language.String(This.Mod.Namespace + ".Setting_Dialogs.Preset_Confirm_Dialog.Title")  # type: Language.String
PresetConfirmDialogText = Language.String(This.Mod.Namespace + ".Setting_Dialogs.Preset_Confirm_Dialog.Text")  # type: Language.String
PresetConfirmDialogYesButton = Language.String(This.Mod.Namespace + ".Setting_Dialogs.Preset_Confirm_Dialog.Yes_Button", fallbackText = "Preset_Confirm_Dialog.Yes_Button")  # type: Language.String
PresetConfirmDialogNoButton = Language.String(This.Mod.Namespace + ".Setting_Dialogs.Preset_Confirm_Dialog.No_Button", fallbackText = "Preset_Confirm_Dialog.No_Button")  # type: Language.String

class DialogButton:
	def __init__ (self,
				  responseID: int,
				  sortOrder: int,
				  callback: typing.Callable[[ui_dialog.UiDialog], None],
				  text: localization.LocalizedString,
				  subText: localization.LocalizedString = None):
		"""
		:param responseID: The identifier used to determine which response the dialog was given.
		:type responseID: int

		:param sortOrder: A number used to sort button on the dialog.
		:type sortOrder: int

		:param callback: A function that will be called after this button was clicked, it should take the associated dialog as an argument.
		:type callback: typing.Callable[[], None]

		:param text: The localization string of the text shown on the button, you shouldn't make this callable.
		:type text: localization.LocalizedString

		:param subText: The localization string of the sub text shown on the button, you shouldn't make this callable.
		:type subText: localization.LocalizedString | None
		"""

		self.ResponseID = responseID  # type: int
		self.SortOrder = sortOrder  # type: int

		self.Callback = callback  # type: typing.Callable[[ui_dialog.UiDialog], None]

		self.Text = text  # type: localization.LocalizedString
		self.SubText = subText  # type: localization.LocalizedString

	Callback: typing.Callable

	def GenerateDialogResponse (self) -> ui_dialog.UiDialogResponse:
		buttonTextString = lambda *args, **kwargs: self.Text

		responseArguments = {
			"dialog_response_id": self.ResponseID,
			"sort_order": self.SortOrder,
			"text": buttonTextString
		}

		if self.SubText is not None:
			buttonSubTextString = lambda *args, **kwargs: self.SubText
			responseArguments["subtext"] = buttonSubTextString

		response = ui_dialog.UiDialogResponse(**responseArguments)

		return response

class ChoiceDialogButton(DialogButton):
	ChoiceButton = Language.String(This.Mod.Namespace + ".Setting_Dialogs.Choice_Button", fallbackText = "Choice_Button")  # type: Language.String

	def __init__ (self, selected: bool = False, *args, **kwargs):
		"""
		:param selected: Whether or not the button's text will have a selected look.
		:type selected: bool
		"""

		super().__init__(*args, **kwargs)

		self.Selected = selected  # type: bool

	def GenerateDialogResponse (self) -> ui_dialog.UiDialogResponse:
		if self.Selected:
			valueButtonStringTokens = ("&gt; ", self.Text, " &lt;")
		else:
			valueButtonStringTokens = ("", self.Text, "")

		if self.ChoiceButton.IdentifierIsRegistered():
			buttonTextString = self.ChoiceButton.GetCallableLocalizationString(*valueButtonStringTokens)
		else:
			buttonTextString = self.Text

		responseArguments = {
			"dialog_response_id": self.ResponseID,
			"sort_order": self.SortOrder,
			"text": buttonTextString
		}

		if self.SubText is not None:
			responseArguments["subtext"] = self.SubText

		response = ui_dialog.UiDialogResponse(**responseArguments)

		return response

class DialogRow:
	def __init__ (self,
				  optionID: int,
				  callback: typing.Callable[[ui_dialog.UiDialog], None],
				  text: localization.LocalizedString,
				  description: localization.LocalizedString = None,
				  icon = None):
		"""
		:param optionID: The identifier used to determine which response the dialog was given.
		:type optionID: int

		:param callback: A function that will be called after this row was clicked, it should take the associated dialog as an argument.
		:type callback: typing.Callable[[], None]

		:param text: The localization string of the text shown on the row, you shouldn't make this callable.
		:type text: localization.LocalizedString

		:param description: The localization string of the sub text shown on the row, you shouldn't make this callable.
		:type description: localization.LocalizedString | None

		:param icon: A key pointing to this row's icon resource.
		:type icon: resources.Key | None
		"""

		self.OptionID = optionID  # type: int

		self.Callback = callback  # type: typing.Callable[[ui_dialog.UiDialog], None]

		self.Text = text  # type: localization.LocalizedString
		self.Description = description  # type: localization.LocalizedString

		self.Icon = icon

	def GenerateRow (self) -> ui_dialog_picker.ObjectPickerRow:
		row = ui_dialog_picker.ObjectPickerRow(option_id = self.OptionID, name = self.Text, row_description = self.Description, icon = self.Icon)
		return row

class SettingDialogBase(abc.ABC):
	HostNamespace = This.Mod.Namespace
	HostName = This.Mod.Name

	def __init_subclass__ (cls, **kwargs):
		cls._OnInitializeSubclass()

	def ShowDialog (self,
					setting: UISettingsShared.SettingWrapper,
					returnCallback: typing.Callable[[], None] = None,
					**kwargs) -> None:

		if not isinstance(setting, UISettingsShared.SettingWrapper):
			raise Exceptions.IncorrectTypeException(setting, "setting", (UISettingsShared.SettingWrapper,))

		if not isinstance(returnCallback, typing.Callable) and returnCallback is not None:
			raise Exceptions.IncorrectTypeException(returnCallback, "returnCallback", ("Callable", None))

		if services.current_zone() is None:
			Debug.Log("Tried to show setting dialog before a zone was loaded\n" + str.join("", traceback.format_stack()), self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
			return

		self._ShowDialogInternal(setting, setting.Get(ignoreOverride = True), kwargs, returnCallback = returnCallback)

	@classmethod
	def _OnInitializeSubclass (cls) -> None:
		pass

	@abc.abstractmethod
	def _ShowDialogInternal (self,
							 setting: UISettingsShared.SettingWrapper,
							 currentValue: typing.Any,
							 showDialogArguments: typing.Dict[str, typing.Any],
							 returnCallback: typing.Callable[[], None] = None,
							 *args, **kwargs) -> None:

		pass

	@abc.abstractmethod
	def _CreateArguments (self,
						  setting: UISettingsShared.SettingWrapper,
						  currentValue: typing.Any,
						  showDialogArguments: typing.Dict[str, typing.Any],
						  *args, **kwargs) -> typing.Dict[str, typing.Any]:

		pass

	@abc.abstractmethod
	def _CreateDialog (self,
					   dialogArguments: dict,
					   *args, **kwargs) -> ui_dialog.UiDialog:

		pass

	@abc.abstractmethod
	def _OnDialogResponse (self,
						   dialog: ui_dialog.UiDialogBase,
						   *args, **kwargs) -> None:
		pass

class StandardDialog(SettingDialogBase):
	def __init__ (self):
		super().__init__()

	def _GetTitleText (self, setting: UISettingsShared.SettingWrapper) -> localization.LocalizedString:
		return setting.GetNameText()

	def _GetDescriptionText (self, setting: UISettingsShared.SettingWrapper) -> localization.LocalizedString:
		descriptionParts = self._GetDescriptionParts(setting)  # type: typing.List[typing.Union[localization.LocalizedString, str, int, float]]
		return TextBuilder.BuildText(descriptionParts)

	def _GetDescriptionParts (self, setting: UISettingsShared.SettingWrapper) -> typing.List[typing.Union[localization.LocalizedString, str, int, float]]:
		descriptionParts = list()  # type: typing.List[typing.Union[localization.LocalizedString, str, int, float]]
		descriptionParts.extend(self._GetDescriptionInformationParts(setting))
		descriptionParts.append("\n\n")
		descriptionParts.extend(self._GetDescriptionValuesParts(setting))

		documentationURL = self._GetDescriptionDocumentationURL(setting)  # type: typing.Optional[str]
		if documentationURL is not None:
			descriptionParts.append("\n\n")
			descriptionParts.extend(self._GetDescriptionDocumentationParts(setting))

		return descriptionParts

	def _GetDescriptionInformationParts (self, setting: UISettingsShared.SettingWrapper) -> typing.List[typing.Union[localization.LocalizedString, str, int, float]]:
		informationParts = [self._GetDescriptionSettingText(setting)]  # type: typing.List[typing.Union[localization.LocalizedString, str, int, float]]

		if setting.IsOverridden():
			informationParts.append("\n")
			informationParts.append(self._GetDescriptionPartsOverriddenText())

		return informationParts

	def _GetDescriptionValuesParts (self, setting: UISettingsShared.SettingWrapper) -> typing.List[typing.Union[localization.LocalizedString, str, int, float]]:
		valuesParts = list()  # type: typing.List[typing.Union[localization.LocalizedString, str, int, float]]

		defaultPart = self._GetDescriptionPartsDefaultText()  # type: localization.LocalizedString
		Language.AddTokens(defaultPart, self._GetDescriptionDefaultText(setting))
		valuesParts.append(defaultPart)

		if setting.IsOverridden():
			overriddenPart = self._GetDescriptionPartsOverriddenValueText()  # type: localization.LocalizedString
			overriddenPartTokens = (
				self._GetDescriptionOverrideValueText(setting),
				self._GetDescriptionOverrideReasonText(setting)
			)  # type: tuple

			Language.AddTokens(overriddenPart, *overriddenPartTokens)

			valuesParts.append("\n")
			valuesParts.append(overriddenPart)

		return valuesParts

	def _GetDescriptionDocumentationParts (self, setting: UISettingsShared.SettingWrapper) -> typing.List[typing.Union[localization.LocalizedString, str, int, float]]:
		return [] # Disabled the documentation parts because the links no longer work on some types of dialogs.
		#documentationURL = self._GetDescriptionDocumentationURL(setting)  # type: typing.Optional[str]

		#if documentationURL is None:
		#	documentationURL = "**"

		#documentationPart = self._GetDescriptionPartsDocumentationText()  # type: localization.LocalizedString
		#Language.AddTokens(documentationPart, documentationURL)
		#return [documentationPart]

	def _GetDescriptionSettingText (self, setting: UISettingsShared.SettingWrapper) -> localization.LocalizedString:
		return Language.CreateLocalizationString("**")

	def _GetDescriptionDefaultText (self, setting: UISettingsShared.SettingWrapper) -> localization.LocalizedString:
		return setting.GetDefaultText()

	def _GetDescriptionOverrideValueText (self, setting: UISettingsShared.SettingWrapper) -> localization.LocalizedString:
		return setting.GetOverrideValueText()

	def _GetDescriptionOverrideReasonText (self, setting: UISettingsShared.SettingWrapper) -> localization.LocalizedString:
		return setting.GetOverrideReasonText()

	def _GetDescriptionDocumentationURL (self, setting: UISettingsShared.SettingWrapper) -> typing.Optional[str]:
		return None

	def _GetDescriptionPartsOverriddenText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Dialogs.Description_Parts.Overridden")

	def _GetDescriptionPartsOverriddenValueText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Dialogs.Description_Parts.Overridden_Value")

	def _GetDescriptionPartsDefaultText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Dialogs.Description_Parts.Default")

	def _GetDescriptionPartsDocumentationText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Dialogs.Description_Parts.Documentation")

	def _GetAcceptButtonText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Dialogs.Apply_Button", fallbackText = "Apply_Button")

	def _GetCancelButtonText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Dialogs.Cancel_Button", fallbackText = "Cancel_Button")

	def _ShowDialogInternal (self,
							 setting: UISettingsShared.SettingWrapper,
							 currentValue: typing.Any,
							 showDialogArguments: typing.Dict[str, typing.Any],
							 returnCallback: typing.Callable[[], None] = None,
							 *args, **kwargs) -> None:

		acceptButtonCallback = self._CreateAcceptButtonCallback(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.Callable[[ui_dialog.UiDialogOkCancel], None]
		cancelButtonCallback = self._CreateCancelButtonCallback(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.Callable[[ui_dialog.UiDialogOkCancel], None]

		dialogButtons = self._CreateButtons(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.List[DialogButton]
		dialogArguments = self._CreateArguments(setting, currentValue, showDialogArguments, dialogButtons = dialogButtons)  # type: typing.Dict[str, typing.Any]
		dialog = self._CreateDialog(dialogArguments)  # type: ui_dialog.UiDialogOkCancel

		def DialogCallback (dialogReference: ui_dialog.UiDialogOkCancel):
			try:
				self._OnDialogResponse(dialogReference, dialogButtons = dialogButtons, acceptButtonCallback = acceptButtonCallback, cancelButtonCallback = cancelButtonCallback)
			except Exception as e:
				Debug.Log("Failed to run the callback for the setting dialog of '" + setting.Key + "'.", self.HostNamespace, Debug.LogLevels.Exception, group = self.HostNamespace, owner = __name__)
				raise e

		dialog.add_listener(DialogCallback)
		dialog.show_dialog()

	# noinspection PyUnusedLocal
	def _CreateAcceptButtonCallback (self,
									 setting: UISettingsShared.SettingWrapper,
									 currentValue: typing.Any,
									 showDialogArguments: typing.Dict[str, typing.Any],
									 returnCallback: typing.Callable[[], None] = None,
									 *args, **kwargs) -> typing.Callable[[ui_dialog.UiDialogOkCancel], None]:

		# noinspection PyUnusedLocal
		def AcceptButtonCallback (dialog: ui_dialog.UiDialogOkCancel) -> None:
			setting.Set(currentValue)

			if returnCallback is not None:
				returnCallback()

		return AcceptButtonCallback

	# noinspection PyUnusedLocal
	def _CreateCancelButtonCallback (self,
									 setting: UISettingsShared.SettingWrapper,
									 currentValue: typing.Any,
									 showDialogArguments: typing.Dict[str, typing.Any],
									 returnCallback: typing.Callable[[], None] = None,
									 *args, **kwargs) -> typing.Callable[[ui_dialog.UiDialogOkCancel], None]:

		# noinspection PyUnusedLocal
		def CancelButtonCallback (dialog: ui_dialog.UiDialogOkCancel) -> None:
			if returnCallback is not None:
				returnCallback()

		return CancelButtonCallback

	def _CreateButtons (self,
						setting: UISettingsShared.SettingWrapper,
						currentValue: typing.Any,
						showDialogArguments: typing.Dict[str, typing.Any],
						returnCallback: typing.Callable[[], None] = None,
						*args, **kwargs) -> typing.List[DialogButton]:

		buttons = list()
		return buttons

	def _CreateArguments (self,
						  setting: UISettingsShared.SettingWrapper,
						  currentValue: typing.Any,
						  showDialogArguments: typing.Dict[str, typing.Any],
						  *args, **kwargs) -> typing.Dict[str, typing.Any]:

		dialogArguments = dict()

		dialogOwner = showDialogArguments.get("owner")

		dialogButtons = kwargs["dialogButtons"]  # type: typing.List[DialogButton]
		dialogResponses = list()  # type: typing.List[ui_dialog.UiDialogResponse]

		for dialogButton in dialogButtons:  # type: DialogButton
			dialogResponses.append(dialogButton.GenerateDialogResponse())

		textString = self._GetDescriptionText(setting)  # type: localization.LocalizedString

		dialogArguments["owner"] = dialogOwner
		dialogArguments["title"] = Language.MakeLocalizationStringCallable(self._GetTitleText(setting))
		dialogArguments["text"] = Language.MakeLocalizationStringCallable(textString)
		dialogArguments["text_ok"] = Language.MakeLocalizationStringCallable(self._GetAcceptButtonText())
		dialogArguments["text_cancel"] = Language.MakeLocalizationStringCallable(self._GetCancelButtonText())
		dialogArguments["ui_responses"] = dialogResponses

		return dialogArguments

	def _CreateDialog (self,
					   dialogArguments: dict,
					   *args, **kwargs) -> ui_dialog.UiDialogOkCancel:

		if not "owner" in dialogArguments:
			dialogArguments["owner"] = None

		dialog = ui_dialog.UiDialogOkCancel.TunableFactory().default(**dialogArguments)  # type: ui_dialog.UiDialogOkCancel

		return dialog

	def _OnDialogResponse (self, dialog: ui_dialog.UiDialog, *args, **kwargs) -> None:
		dialogButtons = kwargs["dialogButtons"]  # type: typing.List[DialogButton]

		if dialog.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
			acceptButtonCallback = kwargs["acceptButtonCallback"]  # type: typing.Callable[[ui_dialog.UiDialog], None]

			acceptButtonCallback(dialog)

		if dialog.response == ui_dialog.ButtonType.DIALOG_RESPONSE_CANCEL:
			cancelButtonCallback = kwargs["cancelButtonCallback"]  # type: typing.Callable[[ui_dialog.UiDialog], None]

			cancelButtonCallback(dialog)

		for dialogButton in dialogButtons:  # type: DialogButton
			if dialog.response == dialogButton.ResponseID:
				dialogButton.Callback(dialog)

class InputDialog(StandardDialog):
	# noinspection PyUnusedLocal
	def _GetInputRestriction (self, setting: UISettingsShared.SettingWrapper) -> typing.Optional[localization.LocalizedString]:
		return None

	def _ShowInvalidInputNotification (self, inputString) -> None:
		ShowInvalidInputNotification(inputString, self.HostName)

	def _ShowDialogInternal (self,
							 setting: UISettingsShared.SettingWrapper,
							 currentValue: typing.Any,
							 showDialogArguments: typing.Dict[str, typing.Any],
							 returnCallback: typing.Callable[[], None] = None,
							 *args, **kwargs) -> None:

		acceptButtonCallback = self._CreateAcceptButtonCallback(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.Callable[[ui_dialog_generic.UiDialogTextInputOkCancel], None]
		cancelButtonCallback = self._CreateCancelButtonCallback(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.Callable[[ui_dialog_generic.UiDialogTextInputOkCancel], None]

		dialogButtons = self._CreateButtons(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.List[DialogButton]

		if "currentInput" in kwargs:
			dialogArguments = self._CreateArguments(setting, currentValue, showDialogArguments, dialogButtons = dialogButtons, currentInput = kwargs["currentInput"])  # type: typing.Dict[str, typing.Any]
		else:
			dialogArguments = self._CreateArguments(setting, currentValue, showDialogArguments, dialogButtons = dialogButtons)  # type: typing.Dict[str, typing.Any]

		dialog = self._CreateDialog(dialogArguments)  # type: ui_dialog_generic.UiDialogTextInputOkCancel

		def DialogCallback (dialogReference: ui_dialog_generic.UiDialogTextInputOkCancel):
			try:
				self._OnDialogResponse(dialogReference, dialogButtons = dialogButtons, acceptButtonCallback = acceptButtonCallback, cancelButtonCallback = cancelButtonCallback)
			except Exception as e:
				Debug.Log("Failed to run the callback for the setting dialog of '" + setting.Key + "'.", self.HostNamespace, Debug.LogLevels.Exception, group = self.HostNamespace, owner = __name__)
				raise e

		dialog.add_listener(DialogCallback)
		dialog.show_dialog()

	def _CreateAcceptButtonCallback (self,
									 setting: UISettingsShared.SettingWrapper,
									 currentValue: typing.Any,
									 showDialogArguments: typing.Dict[str, typing.Any],
									 returnCallback: typing.Callable[[], None] = None,
									 *args, **kwargs) -> typing.Callable[[ui_dialog_generic.UiDialogTextInputOkCancel], None]:

		# noinspection PyUnusedLocal
		def AcceptButtonCallback (dialog: ui_dialog_generic.UiDialogTextInputOkCancel) -> None:
			dialogInput = dialog.text_input_responses["Input"]  # type: str

			try:
				dialogInputValue = self._ParseValueString(dialogInput)
			except Exception:
				Debug.Log("User tried to change a setting with the text input of '" + dialogInput + "' but this input is invalid.", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
				self._ShowInvalidInputNotification(dialogInput)
				self._ShowDialogInternal(setting, currentValue, showDialogArguments, returnCallback = returnCallback, currentInput = dialogInput)
				return

			try:
				setting.Set(dialogInputValue)
			except Exception:
				Debug.Log("User tried to change a setting with the text input of '" + dialogInput + "' but this input is invalid.", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
				self._ShowInvalidInputNotification(dialogInput)
				self._ShowDialogInternal(setting, currentValue, showDialogArguments, returnCallback = returnCallback, currentInput = dialogInput)
				return

			if returnCallback is not None:
				returnCallback()

		return AcceptButtonCallback

	def _CreateButtons (self,
						setting: UISettingsShared.SettingWrapper,
						currentValue: typing.Any,
						showDialogArguments: typing.Dict[str, typing.Any],
						returnCallback: typing.Callable[[], None] = None,
						*args, **kwargs) -> typing.List[DialogButton]:

		buttons = super()._CreateButtons(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)
		return buttons

	def _CreateArguments (self,
						  setting: UISettingsShared.SettingWrapper,
						  currentValue: typing.Any,
						  showDialogArguments: typing.Dict[str, typing.Any],
						  *args, **kwargs) -> typing.Dict[str, typing.Any]:

		dialogArguments = super()._CreateArguments(setting, currentValue, showDialogArguments, *args, **kwargs)  # type: typing.Dict[str, typing.Any]

		textInputKey = "Input"  # type: str

		textInputLockedArguments = {
			"sort_order": 0,
		}

		textInput = ui_text_input.UiTextInput.TunableFactory(locked_args = textInputLockedArguments).default  # type: ui_text_input.UiTextInput

		if "currentInput" in kwargs:
			textInputInitialValue = Language.MakeLocalizationStringCallable(Language.CreateLocalizationString(kwargs["currentInput"]))
		else:
			textInputInitialValue = Language.MakeLocalizationStringCallable(Language.CreateLocalizationString(self._ValueToString(currentValue)))

		textInput.initial_value = textInputInitialValue

		textInput.restricted_characters = self._GetInputRestriction(setting)

		textInputs = collections.make_immutable_slots_class([textInputKey])
		textInputs = textInputs({
			textInputKey: textInput
		})

		dialogArguments["text_inputs"] = textInputs

		return dialogArguments

	def _CreateDialog (self,
					   dialogArguments: dict,
					   *args, **kwargs) -> ui_dialog_generic.UiDialogTextInputOkCancel:

		if not "owner" in dialogArguments:
			dialogArguments["owner"] = None

		dialog = ui_dialog_generic.UiDialogTextInputOkCancel.TunableFactory().default(**dialogArguments)  # type: ui_dialog_generic.UiDialogTextInputOkCancel

		return dialog

	def _ParseValueString (self, valueString: str) -> typing.Any:
		raise NotImplementedError()

	def _ValueToString (self, value: typing.Any) -> str:
		raise NotImplementedError()

class PresetDialog(StandardDialog):
	def __init__ (self):
		super().__init__()

		self.ShowCustomizeButton = True

	@property
	def ShowCustomizeButton (self) -> bool:
		return self._showCustomizeButton

	@ShowCustomizeButton.setter
	def ShowCustomizeButton (self, value: bool) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "ShowCustomizeButton", (bool,))

		self._showCustomizeButton = value

	def _GetAcceptButtonText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Dialogs.Back_Button", fallbackText = "Back_Button")

	def _GetCustomizeButtonText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Dialogs.Preset.Customize_Button", fallbackText = "Customize_Button")

	def _ShowDialogInternal (self,
							 setting: UISettingsShared.SettingWrapper,
							 currentValue: typing.Any,
							 showDialogArguments: typing.Dict[str, typing.Any],
							 returnCallback: typing.Callable[[], None] = None,
							 *args, **kwargs) -> None:

		acceptButtonCallback = self._CreateAcceptButtonCallback(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.Callable[[ui_dialog.UiDialogOk], None]

		dialogButtons = self._CreateButtons(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.List[DialogButton]
		dialogArguments = self._CreateArguments(setting, currentValue, showDialogArguments, dialogButtons = dialogButtons)  # type: typing.Dict[str, typing.Any]
		dialog = self._CreateDialog(dialogArguments)  # type: ui_dialog.UiDialogOk

		def DialogCallback (dialogReference: ui_dialog.UiDialogOk):
			try:
				self._OnDialogResponse(dialogReference, dialogButtons = dialogButtons, acceptButtonCallback = acceptButtonCallback)
			except Exception as e:
				Debug.Log("Failed to run the callback for the setting dialog of '" + setting.Key + "'.", self.HostNamespace, Debug.LogLevels.Exception, group = self.HostNamespace, owner = __name__)
				raise e

		dialog.add_listener(DialogCallback)
		dialog.show_dialog()

	# noinspection PyUnusedLocal
	def _CreateAcceptButtonCallback (self,
									 setting: UISettingsShared.SettingWrapper,
									 currentValue: typing.Any,
									 showDialogArguments: typing.Dict[str, typing.Any],
									 returnCallback: typing.Callable[[], None] = None,
									 *args, **kwargs) -> typing.Callable[[ui_dialog.UiDialogOk], None]:

		# noinspection PyUnusedLocal
		def AcceptButtonCallback (dialog: ui_dialog.UiDialogOk) -> None:
			if returnCallback is not None:
				returnCallback()

		return AcceptButtonCallback

	def _CreateCustomizeButton (self,
								setting: UISettingsShared.SettingWrapper,
								currentValue: typing.Any,
								showDialogArguments: typing.Dict[str, typing.Any],
								returnCallback: typing.Callable[[], None] = None,
								*args, **kwargs) -> DialogButton:

		customizeButtonCallback = self._CreateCustomizeButtonCallback(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)  # type: typing.Callable[[ui_dialog.UiDialog], None]
		return DialogButton(10200, -5, customizeButtonCallback, self._GetCustomizeButtonText())

	# noinspection PyUnusedLocal
	def _CreateCustomizeButtonCallback (self,
										setting: UISettingsShared.SettingWrapper,
										currentValue: typing.Any,
										showDialogArguments: typing.Dict[str, typing.Any],
										returnCallback: typing.Callable[[], None] = None,
										*args, **kwargs) -> typing.Callable[[ui_dialog.UiDialog], None]:

		# noinspection PyUnusedLocal
		def CustomizeButtonCallback (dialog: ui_dialog.UiDialog) -> None:
			pass

		return CustomizeButtonCallback

	def _CreateButtons (self,
						setting: UISettingsShared.SettingWrapper,
						currentValue: typing.Any,
						showDialogArguments: typing.Dict[str, typing.Any],
						returnCallback: typing.Callable[[], None] = None,
						*args, **kwargs) -> typing.List[DialogButton]:

		buttons = super()._CreateButtons(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)

		if self.ShowCustomizeButton:
			customizeButton = self._CreateCustomizeButton(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)
			buttons.append(customizeButton)

		return buttons

	def _CreateArguments (self,
						  setting: UISettingsShared.SettingWrapper,
						  currentValue: typing.Any,
						  showDialogArguments: typing.Dict[str, typing.Any],
						  *args, **kwargs) -> typing.Dict[str, typing.Any]:

		dialogArguments = dict()

		dialogOwner = showDialogArguments.get("owner")

		dialogButtons = kwargs["dialogButtons"]  # type: typing.List[DialogButton]

		dialogResponses = list()  # type: typing.List[ui_dialog.UiDialogResponse]

		for dialogButton in dialogButtons:  # type: DialogButton
			dialogResponses.append(dialogButton.GenerateDialogResponse())

		textString = self._GetDescriptionText(setting)  # type: localization.LocalizedString

		dialogArguments["owner"] = dialogOwner
		dialogArguments["title"] = Language.MakeLocalizationStringCallable(self._GetTitleText(setting))
		dialogArguments["text"] = Language.MakeLocalizationStringCallable(textString)
		dialogArguments["text_ok"] = Language.MakeLocalizationStringCallable(self._GetAcceptButtonText())
		dialogArguments["ui_responses"] = dialogResponses

		return dialogArguments

	def _CreateDialog (self,
					   dialogArguments: dict,
					   *args, **kwargs) -> ui_dialog.UiDialogOk:

		if not "owner" in dialogArguments:
			dialogArguments["owner"] = None

		dialog = ui_dialog.UiDialogOk.TunableFactory().default(**dialogArguments)  # type: ui_dialog.UiDialogOk

		return dialog

	def _OnDialogResponse (self, dialog: ui_dialog.UiDialog, *args, **kwargs) -> None:
		dialogButtons = kwargs["dialogButtons"]  # type: typing.List[DialogButton]

		if dialog.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
			acceptButtonCallback = kwargs["acceptButtonCallback"]  # type: typing.Callable[[ui_dialog.UiDialog], None]

			acceptButtonCallback(dialog)

		for dialogButton in dialogButtons:  # type: DialogButton
			if dialog.response == dialogButton.ResponseID:
				dialogButton.Callback(dialog)

class DictionaryDialog(StandardDialog):
	def __init__ (self):
		super().__init__()

	def _CreateAcceptButtonCallback (self,
									 setting: UISettingsShared.SettingWrapper,
									 currentValue: typing.Any,
									 showDialogArguments: typing.Dict[str, typing.Any],
									 returnCallback: typing.Callable[[], None] = None,
									 *args, **kwargs) -> typing.Callable[[ui_dialog.UiDialogOkCancel], None]:

		# noinspection PyUnusedLocal
		def AcceptButtonCallback (dialog: ui_dialog.UiDialogOkCancel) -> None:
			pass

		return AcceptButtonCallback

	def _CreateCancelButtonCallback (self,
									 setting: UISettingsShared.SettingWrapper,
									 currentValue: typing.Any,
									 showDialogArguments: typing.Dict[str, typing.Any],
									 returnCallback: typing.Callable[[], None] = None,
									 *args, **kwargs) -> typing.Callable[[ui_dialog.UiDialogOkCancel], None]:

		# noinspection PyUnusedLocal
		def CancelButtonCallback (dialog: ui_dialog.UiDialogOkCancel) -> None:
			setting.Set(currentValue)

			if returnCallback is not None:
				returnCallback()

		return CancelButtonCallback

	def _ShowDialogInternal (self,
							 setting: UISettingsShared.SettingWrapper,
							 currentValue: typing.Any,
							 showDialogArguments: typing.Dict[str, typing.Any],
							 returnCallback: typing.Callable[[], None] = None,
							 *args, **kwargs) -> None:

		acceptButtonCallback = self._CreateAcceptButtonCallback(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.Callable[[ui_dialog.UiDialogOkCancel], None]
		cancelButtonCallback = self._CreateCancelButtonCallback(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.Callable[[ui_dialog.UiDialogOkCancel], None]

		dialogButtons = self._CreateButtons(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.List[DialogButton]
		dialogRows = self._CreateRows(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.List[DialogRow]
		dialogArguments = self._CreateArguments(setting, currentValue, showDialogArguments, dialogButtons = dialogButtons)  # type: typing.Dict[str, typing.Any]
		dialog = self._CreateDialog(dialogArguments, dialogRows = dialogRows)  # type: ui_dialog_picker.UiObjectPicker

		def DialogCallback (dialogReference: ui_dialog_picker.UiObjectPicker):
			try:
				self._OnDialogResponse(dialogReference, dialogButtons = dialogButtons, dialogRows = dialogRows, acceptButtonCallback = acceptButtonCallback, cancelButtonCallback = cancelButtonCallback)
			except Exception as e:
				Debug.Log("Failed to run the callback for the setting dialog of '" + setting.Key + "'.", self.HostNamespace, Debug.LogLevels.Exception, group = self.HostNamespace, owner = __name__)
				raise e

		dialog.add_listener(DialogCallback)
		dialog.show_dialog()

	def _CreateRows (self,
					 setting: UISettingsShared.SettingWrapper,
					 currentValue: typing.Any,
					 showDialogArguments: typing.Dict[str, typing.Any],
					 returnCallback: typing.Callable[[], None] = None,
					 *args, **kwargs) -> typing.List[DialogRow]:

		rows = list()
		return rows

	def _CreateDialog (self,
					   dialogArguments: dict,
					   *args, **kwargs) -> ui_dialog_picker.UiObjectPicker:

		dialogOwner = dialogArguments.get("owner")

		if dialogOwner is None:
			dialogArguments["owner"] = services.get_active_sim().sim_info

		dialog = ui_dialog_picker.UiObjectPicker.TunableFactory().default(**dialogArguments)  # type: ui_dialog_picker.UiObjectPicker

		dialogRows = kwargs["dialogRows"]  # type: typing.List[DialogRow]

		for dialogRow in dialogRows:  # type: DialogRow
			dialog.add_row(dialogRow.GenerateRow())

		return dialog

	def _OnDialogResponse (self, dialog: ui_dialog_picker.UiObjectPicker, *args, **kwargs) -> None:
		dialogButtons = kwargs["dialogButtons"]  # type: typing.List[DialogButton]
		dialogRows = kwargs["dialogRows"]  # type: typing.List[DialogRow]

		if dialog.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
			resultRows = dialog.get_result_rows()  # type: typing.List[ui_dialog_picker.BasePickerRow]

			for resultRow in resultRows:  # type: ui_dialog_picker.BasePickerRow
				for dialogRow in dialogRows:  # type: DialogRow
					if dialogRow.OptionID == resultRow.option_id:
						dialogRow.Callback(dialog)

			acceptButtonCallback = kwargs["acceptButtonCallback"]  # type: typing.Callable[[ui_dialog.UiDialog], None]

			acceptButtonCallback(dialog)

		if dialog.response == ui_dialog.ButtonType.DIALOG_RESPONSE_CANCEL:
			cancelButtonCallback = kwargs["cancelButtonCallback"]  # type: typing.Callable[[ui_dialog.UiDialog], None]

			cancelButtonCallback(dialog)

		for dialogButton in dialogButtons:  # type: DialogButton
			if dialog.response == dialogButton.ResponseID:
				dialogButton.Callback(dialog)

def ShowInvalidInputNotification (inputString: str, modName: str) -> None:
	if services.current_zone() is None:
		Debug.Log("Tried to show setting dialog before a zone was loaded.\n" + str.join("", traceback.format_stack()), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
		return

	notificationArguments = {
		"title": InvalidInputNotificationTitle.GetCallableLocalizationString(modName),
		"text": InvalidInputNotificationText.GetCallableLocalizationString(inputString),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}

	Notifications.ShowNotification(queue = False, **notificationArguments)

def ShowPresetConfirmDialog (callback: typing.Callable[[ui_dialog.UiDialog], None]) -> None:
	if services.current_zone() is None:
		Debug.Log("Tried to show setting dialog before a zone was loaded.\n" + str.join("", traceback.format_stack()), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
		return

	dialogArguments = {
		"title": PresetConfirmDialogTitle.GetCallableLocalizationString(),
		"text": PresetConfirmDialogText.GetCallableLocalizationString(),
		"text_ok": PresetConfirmDialogYesButton.GetCallableLocalizationString(),
		"text_cancel": PresetConfirmDialogNoButton.GetCallableLocalizationString()
	}

	Dialogs.ShowOkCancelDialog(callback = callback, **dialogArguments)
