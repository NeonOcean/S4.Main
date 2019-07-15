import webbrowser

from NeonOcean.Main import Debug, Language, This, Mods
from NeonOcean.Main.UI import Dialogs
from ui import ui_dialog

OpenBrowserDialogText = Language.String(This.Mod.Namespace + ".System.Generic_Dialogs.Open_Browser_Dialog.Text")  # type: Language.String
OpenBrowserDialogYesButton = Language.String(This.Mod.Namespace + ".System.Generic_Dialogs.Open_Browser_Dialog.Yes_Button")  # type: Language.String
OpenBrowserDialogNoButton = Language.String(This.Mod.Namespace + ".System.Generic_Dialogs.Open_Browser_Dialog.No_Button")  # type: Language.String

AboutModDialogTitle = Language.String(This.Mod.Namespace + ".System.Generic_Dialogs.About_Mod_Dialog.Title")  # type: Language.String
AboutModDialogText = Language.String(This.Mod.Namespace + ".System.Generic_Dialogs.About_Mod_Dialog.Text")  # type: Language.String
AboutModDialogOkButton = Language.String(This.Mod.Namespace + ".System.Generic_Dialogs.About_Mod_Dialog.Ok_Button")  # type: Language.String

def ShowOpenBrowserDialog (url: str) -> None:
	dialogArguments = {
		"text": OpenBrowserDialogText.GetCallableLocalizationString(),
		"text_ok": OpenBrowserDialogYesButton.GetCallableLocalizationString(),
		"text_cancel": OpenBrowserDialogNoButton.GetCallableLocalizationString()
	}

	def DialogCallback (dialogReference: ui_dialog.UiDialogOkCancel) -> None:
		try:
			if dialogReference.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
				webbrowser.open(url, new = 2)
		except Exception:
			Debug.Log("Failed to run the callback for the open browser dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	Dialogs.ShowOkCancelDialog(callback = DialogCallback, queue = False, **dialogArguments)

def ShowAboutModDialog (mod: Mods.Mod) -> None:
	dialogArguments = {
		"title": AboutModDialogTitle.GetCallableLocalizationString(),
		"text": AboutModDialogText.GetCallableLocalizationString(mod.Name, mod.Author, str(mod.Version)),
		"text_ok": AboutModDialogOkButton.GetCallableLocalizationString(),
	}

	Dialogs.ShowOkDialog(queue = False, **dialogArguments)