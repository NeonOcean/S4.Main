from __future__ import annotations

import os
import pathlib
import typing

import services
from NeonOcean.S4.Main import Debug, Language, Paths, This
from NeonOcean.S4.Main.Saving import Save
from NeonOcean.S4.Main.UI import Dialogs
from ui import ui_dialog, ui_dialog_picker

SelectSaveDialogTitle = Language.String(This.Mod.Namespace + ".Saving.Select_Save_Dialog.Title")  # type: Language.String
SelectSaveDialogText = Language.String(This.Mod.Namespace + ".Saving.Select_Save_Dialog.Text")  # type: Language.String
SelectSaveDialogDescriptionCurrentlyLoaded = Language.String(This.Mod.Namespace + ".Saving.Select_Save_Dialog.Description_Currently_Loaded", fallbackText = "Description_Currently_Loaded")  # type: Language.String
SelectSaveDialogDescriptionNormal = Language.String(This.Mod.Namespace + ".Saving.Select_Save_Dialog.Description_Normal", fallbackText = "Description_Normal")  # type: Language.String

SelectSaveDialogDescriptionMatchMatches = Language.String(This.Mod.Namespace + ".Saving.Select_Save_Dialog.Description_Match.Matches", fallbackText = "Description_Match.Matches")  # type: Language.String
SelectSaveDialogDescriptionMatchMismatchGUID = Language.String(This.Mod.Namespace + ".Saving.Select_Save_Dialog.Description_Match.Mismatch_GUID", fallbackText = "Description_Match.Mismatch_GUID")  # type: Language.String
SelectSaveDialogDescriptionMatchMismatchGameTick = Language.String(This.Mod.Namespace + ".Saving.Select_Save_Dialog.Description_Match.Mismatch_Game_Tick", fallbackText = "Description_Match.Mismatch_Game_Tick")  # type: Language.String
SelectSaveDialogDescriptionMatchUnknown = Language.String(This.Mod.Namespace + ".Saving.Select_Save_Dialog.Description_Match.Unknown", fallbackText = "Description_Match.Unknown")  # type: Language.String

def ShowSelectSaveDialog () -> None:
	gameSaveSlotID = str(services.get_persistence_service().get_save_slot_proto_buff().slot_id)  # type: str
	gameSaveGUID = str(services.get_persistence_service().get_save_slot_proto_guid())  # type: str

	dialogArguments = {
		"owner": services.get_active_sim().sim_info,
		"title": SelectSaveDialogTitle,
		"text": SelectSaveDialogText.GetCallableLocalizationString(*(gameSaveSlotID, gameSaveGUID))
	}

	dialogRows = list()

	options = { }  # type: typing.Dict[int, str]

	loadedSaveDirectoryPath = Save.GetLoadedDirectoryPath()  # type: typing.Optional[str]
	loadedSaveDirectoryPathObject = pathlib.Path(Save.GetLoadedDirectoryPath()) if loadedSaveDirectoryPath is not None else None  # type: typing.Optional[pathlib.Path]

	for saveDirectoryName in os.listdir(Paths.SavesPath):  # type: str
		saveDirectoryPath = os.path.join(Paths.SavesPath, saveDirectoryName)  # type: str

		if os.path.isdir(saveDirectoryPath):
			saveDirectoryPathObject = pathlib.Path(saveDirectoryPath)  # type: pathlib.Path

			currentOptionID = 50000 + len(options)
			options[currentOptionID] = saveDirectoryPath

			saveDirectoryMetaData = Save.GetSaveMetaData(saveDirectoryPath)  # type: typing.Optional[Save.ModSaveMetaData]

			rowDescriptionTokens = (SelectSaveDialogDescriptionMatchUnknown.GetLocalizationString(),)

			if saveDirectoryMetaData is not None:
				saveDirectoryMatchType = saveDirectoryMetaData.MatchesGameSave()  # type: Save.ModSaveMatchTypes

				if saveDirectoryMatchType in Save.ModSaveMatchTypes.Match:
					rowDescriptionTokens = (SelectSaveDialogDescriptionMatchMatches.GetLocalizationString(),)
				elif saveDirectoryMatchType in Save.ModSaveMatchTypes.MismatchedGUID:
					rowDescriptionTokens = (SelectSaveDialogDescriptionMatchMismatchGUID.GetLocalizationString(),)
				elif saveDirectoryMatchType in Save.ModSaveMatchTypes.MismatchedGameTick:
					rowDescriptionTokens = (SelectSaveDialogDescriptionMatchMismatchGameTick.GetLocalizationString(),)

			if loadedSaveDirectoryPathObject is not None:
				if loadedSaveDirectoryPathObject == saveDirectoryPathObject:
					rowDescription = SelectSaveDialogDescriptionCurrentlyLoaded.GetLocalizationString(*rowDescriptionTokens)
				else:
					rowDescription = SelectSaveDialogDescriptionNormal.GetLocalizationString(*rowDescriptionTokens)
			else:
				rowDescription = SelectSaveDialogDescriptionNormal.GetLocalizationString(*rowDescriptionTokens)

			if saveDirectoryMetaData is None:
				rowNameTokens = (saveDirectoryName,)
			else:
				rowNameTokens = (saveDirectoryName + " (" + saveDirectoryMetaData.Name + ")",)

			dialogRows.append(ui_dialog_picker.ObjectPickerRow(
				option_id = currentOptionID,
				name = Language.CreateLocalizationString(*rowNameTokens),
				row_description = rowDescription))

	def DialogCallback (dialogReference: ui_dialog_picker.UiObjectPicker) -> None:
		try:
			if dialogReference.response == ui_dialog.ButtonType.DIALOG_RESPONSE_CANCEL:
				return

			resultRows = dialogReference.picked_results  # type: typing.Tuple[int]

			if len(resultRows) == 0:
				return

			selectedSaveDirectory = options.get(resultRows[0])  # type: typing.Optional[str]

			if selectedSaveDirectory is None:
				return

			Save.Load(services.get_persistence_service().get_save_slot_proto_buff().slot_id, selectedSaveDirectory, changingSave = True)
		except Exception as e:
			Debug.Log("Failed to run the callback for the select save dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

	Dialogs.ShowObjectPickerDialog(DialogCallback, dialogRows, **dialogArguments)
