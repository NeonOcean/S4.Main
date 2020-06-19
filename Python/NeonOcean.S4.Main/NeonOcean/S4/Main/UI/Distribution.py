from __future__ import annotations

import typing

from NeonOcean.S4.Main import Language, This, DistributionShared
from NeonOcean.S4.Main.UI import Dialogs, Generic, Resources as UIResources
from sims4 import localization, resources
from ui import ui_dialog, ui_dialog_picker

UpdatesListTitle = Language.String(This.Mod.Namespace + ".Distribution.Updates_List.Title")
UpdatesListText = Language.String(This.Mod.Namespace + ".Distribution.Updates_List.Text")
UpdatesListRowText = Language.String(This.Mod.Namespace + ".Distribution.Updates_List.Row_Text")
UpdatesListRowDescription = Language.String(This.Mod.Namespace + ".Distribution.Updates_List.Row_Description")
UpdatesListRowDescriptionReleaseType = Language.String(This.Mod.Namespace + ".Distribution.Updates_List.Row_Description.Release_Type")
UpdatesListRowDescriptionPreviewType = Language.String(This.Mod.Namespace + ".Distribution.Updates_List.Row_Description.Preview_Type")

def ShowUpdatesList (updatedMods: typing.List[DistributionShared.UpdateInformation]) -> None:
	dialogArguments = {
		"title": UpdatesListTitle.GetCallableLocalizationString(),
		"text": UpdatesListText.GetCallableLocalizationString()
	}

	options = { }  # type: typing.Dict[int, str]

	dialogRows = list()  # type: typing.List

	for updatedModIndex in range(len(updatedMods)):  # type: int
		updatedMod = updatedMods[updatedModIndex]  # type: DistributionShared.UpdateInformation

		optionID = 5000 + updatedModIndex  # type: int

		dialogRowArguments = {
			"option_id": optionID,
			"name": UpdatesListRowText.GetLocalizationString(updatedMod.ModName, updatedMod.ModAuthor),
			"icon": resources.ResourceKeyWrapper(UIResources.PickerDownloadIconKey)
		}

		if not updatedMod.IsPreview:
			descriptionTypeText = UpdatesListRowDescriptionReleaseType.GetLocalizationString()  # type: localization.LocalizedString
		else:
			descriptionTypeText = UpdatesListRowDescriptionPreviewType.GetLocalizationString()  # type: localization.LocalizedString

		dialogRowArguments["row_description"] = UpdatesListRowDescription.GetLocalizationString(descriptionTypeText, updatedMod.CurrentVersion, updatedMod.NewVersion, updatedMod.DownloadURL)
		dialogRows.append(ui_dialog_picker.ObjectPickerRow(**dialogRowArguments))

		options[optionID] = updatedMod.DownloadURL

	def OpenBrowserDialogCallback () -> None:
		ShowUpdatesList(updatedMods)

	def DialogCallback (dialogReference: ui_dialog_picker.UiObjectPicker) -> None:
		if dialogReference.response == ui_dialog.ButtonType.DIALOG_RESPONSE_CANCEL:
			return

		resultRows = dialogReference.picked_results  # type: typing.Tuple[int]

		if len(resultRows) == 0:
			return

		selectedModURL = options.get(resultRows[0])  # type: typing.Optional[str]

		if selectedModURL is None:
			return

		Generic.ShowOpenBrowserDialog(selectedModURL, returnCallback = OpenBrowserDialogCallback)

	Dialogs.ShowObjectPickerDialog(callback = DialogCallback, pickerRows = dialogRows, **dialogArguments)
