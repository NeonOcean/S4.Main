from NeonOcean.S4.Main import Debug, LoadingShared, Resetting, This
from NeonOcean.S4.Main.Console import Command
from sims4 import commands

ResetCommand: Command.ConsoleCommand

def _Setup () -> None:
	global ResetCommand

	commandPrefix = This.Mod.Namespace.lower()  # type: str

	ResetCommand = Command.ConsoleCommand(_ShowDialog, commandPrefix + ".reset")

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	ResetCommand.RegisterCommand()

def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	ResetCommand.UnregisterCommand()

def _ShowDialog (_connection: int = None) -> None:
	try:
		Resetting.ShowResetDialog(This.Mod)
	except Exception as e:
		output = commands.CheatOutput(_connection)
		output("Failed to show reset dialog.")

		Debug.Log("Failed to show reset dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

_Setup()