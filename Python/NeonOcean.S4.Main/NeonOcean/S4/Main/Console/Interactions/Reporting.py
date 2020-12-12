import os
import typing

from NeonOcean.S4.Main import Debug, LoadingShared, Reporting, This, Language, Paths
from NeonOcean.S4.Main.UI import Dialogs
from NeonOcean.S4.Main.Console import Command
from sims4 import commands
from ui import ui_dialog

ShowPrepareReportLocationDialogCommand: Command.ConsoleCommand

PrepareReportLocationDialogTitle = Language.String(This.Mod.Namespace + ".Reporting.Dialogs.Prepare_Report_Location.Title", fallbackText = "Prepare_Report_Location.Title")  # type: Language.String
PrepareReportLocationDialogText = Language.String(This.Mod.Namespace + ".Reporting.Dialogs.Prepare_Report_Location.Text")  # type: Language.String
PrepareReportLocationDialogCancelButton = Language.String(This.Mod.Namespace + ".Reporting.Dialogs.Prepare_Report_Location.Cancel_Button", fallbackText = "Cancel_Button")  # type: Language.String
PrepareReportLocationDialogDesktopButton = Language.String(This.Mod.Namespace + ".Reporting.Dialogs.Prepare_Report_Location.Desktop_Button", fallbackText = "Desktop_Button")  # type: Language.String
PrepareReportLocationDialogGameUserDataButton = Language.String(This.Mod.Namespace + ".Reporting.Dialogs.Prepare_Report_Location.Game_User_Data_Button", fallbackText = "Game_User_Data_Button")  # type: Language.String

ReportCreatedDialogTitle = Language.String(This.Mod.Namespace + ".Reporting.Dialogs.Report_Created.Title", fallbackText = "Report_Created.Title")  # type: Language.String
ReportCreatedDialogText = Language.String(This.Mod.Namespace + ".Reporting.Dialogs.Report_Created.Text", fallbackText = "Report_Created.Text")  # type: Language.String
ReportCreatedDialogButton = Language.String(This.Mod.Namespace + ".Reporting.Dialogs.Report_Created.Button", fallbackText = "Report_Created.Button")  # type: Language.String

def _Setup () -> None:
	global ShowPrepareReportLocationDialogCommand

	commandPrefix = This.Mod.Namespace.lower() + ".reporting"  # type: str

	ShowPrepareReportLocationDialogCommand = Command.ConsoleCommand(_ShowPrepareReportLocationDialog, commandPrefix + ".show_prepare_report_location_dialog")

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	ShowPrepareReportLocationDialogCommand.RegisterCommand()

def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	ShowPrepareReportLocationDialogCommand.UnregisterCommand()

def _ShowPrepareReportLocationDialog (_connection: int = None) -> None:
	try:
		reportFileName = "NeonOcean Sims 4 Bug Report.zip"  # type: str

		dialogResponses = list()  # type: typing.List[ui_dialog.UiDialogResponse]

		gameUserDataDirectoryPath = Paths.UserDataPath  # type: str
		gameUserDataReportFilePath = os.path.join(gameUserDataDirectoryPath, reportFileName)  # type: str
		gameUserDataReportResponseID = 1  # type: int

		if os.path.exists(gameUserDataDirectoryPath):
			gameUserDataResponseArguments = {
				"dialog_response_id": gameUserDataReportResponseID,
				"sort_order": -2,
				"text": PrepareReportLocationDialogGameUserDataButton.GetCallableLocalizationString()
			}

			dialogResponses.append(ui_dialog.UiDialogResponse(**gameUserDataResponseArguments))
		else:
			raise Exception("The game's user data path does not exist.")


		desktopDirectoryPath = os.path.expanduser("~/Desktop")  # type: str
		desktopReportFilePath = os.path.join(desktopDirectoryPath, reportFileName)  # type: str
		desktopReportResponseID = 2  # type: int

		if os.path.exists(desktopDirectoryPath):
			desktopResponseArguments = {
				"dialog_response_id": desktopReportResponseID,
				"sort_order": -2,
				"text": PrepareReportLocationDialogDesktopButton.GetCallableLocalizationString()
			}

			dialogResponses.append(ui_dialog.UiDialogResponse(**desktopResponseArguments))


		dialogArguments = {
			"title": PrepareReportLocationDialogTitle.GetCallableLocalizationString(),
			"text": PrepareReportLocationDialogText.GetCallableLocalizationString(),
			"text_ok": PrepareReportLocationDialogCancelButton.GetCallableLocalizationString(),
			"ui_responses": dialogResponses
		}

		def dialogCallback (closedDialog: ui_dialog.UiDialog) -> None:
			try:
				if closedDialog.response == gameUserDataReportResponseID:
					Reporting.PrepareReportFiles(gameUserDataReportFilePath)
					_ShowReportCreatedDialog()
				elif closedDialog.response == desktopReportResponseID:
					Reporting.PrepareReportFiles(desktopReportFilePath)
					_ShowReportCreatedDialog()
			except:
				commands.CheatOutput(_connection)("Failed to run the callback for the prepare report location dialog.")

				Debug.Log("Failed to run the callback for the prepare report location dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

		Dialogs.ShowOkDialog(
			callback = dialogCallback,
			queue = False,
			**dialogArguments
		)
	except:
		commands.CheatOutput(_connection)("Failed to show the prepare report location dialog.")
		Debug.Log("Failed to show the prepare report location dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

def _ShowReportCreatedDialog () -> None:
	dialogArguments = {
		"title": ReportCreatedDialogTitle.GetCallableLocalizationString(),
		"text": ReportCreatedDialogText.GetCallableLocalizationString(),
		"text_ok": ReportCreatedDialogButton.GetCallableLocalizationString(),
	}

	Dialogs.ShowOkDialog(
		queue = False,
		**dialogArguments
	)

_Setup()