from NeonOcean.S4.Main import Debug, LoadingShared, This
from NeonOcean.S4.Main.Console import Command
from NeonOcean.S4.Main.Saving import SelectSave
from sims4 import commands

SelectSaveCommand: Command.ConsoleCommand

def _Setup () -> None:
	global SelectSaveCommand

	commandPrefix = This.Mod.Namespace.lower()

	SelectSaveCommand = Command.ConsoleCommand(_ShowSelectSaveDialog, commandPrefix + ".debug.show_select_save_dialog")

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	SelectSaveCommand.RegisterCommand()

def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	SelectSaveCommand.UnregisterCommand()

def _ShowSelectSaveDialog (_connection: int = None) -> None:
	try:
		SelectSave.ShowSelectSaveDialog()
	except Exception as e:
		output = commands.CheatOutput(_connection)
		output("Failed to show the select save dialog.")

		Debug.Log("Failed to show the select save dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

_Setup()
