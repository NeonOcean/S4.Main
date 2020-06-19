from NeonOcean.S4.Main import Debug, LoadingShared, This, Websites
from NeonOcean.S4.Main.Console import Command
from NeonOcean.S4.Main.UI import Generic
from sims4 import commands

AboutModCommand: Command.ConsoleCommand
DocumentationCommand: Command.ConsoleCommand
VisitModPageCommand: Command.ConsoleCommand

def _Setup () -> None:
	global AboutModCommand, DocumentationCommand, VisitModPageCommand

	commandPrefix = This.Mod.Namespace.lower() + ".standard"  # type: str

	AboutModCommand = Command.ConsoleCommand(_AboutMod, commandPrefix + ".about_mod")
	DocumentationCommand = Command.ConsoleCommand(_Documentation, commandPrefix + ".documentation")
	VisitModPageCommand = Command.ConsoleCommand(_VisitModPage, commandPrefix + ".visit_mod_page")

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	AboutModCommand.RegisterCommand()
	DocumentationCommand.RegisterCommand()
	VisitModPageCommand.RegisterCommand()

def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	AboutModCommand.UnregisterCommand()
	DocumentationCommand.UnregisterCommand()
	VisitModPageCommand.UnregisterCommand()

def _AboutMod (_connection: int = None) -> None:
	try:
		Generic.ShowAboutModDialog(This.Mod)
	except:
		output = commands.CheatOutput(_connection)
		output("Failed to show the about mod dialog.")

		Debug.Log("Failed to show the about mod dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

def _Documentation (_connection: int = None) -> None:
	try:
		Generic.ShowOpenBrowserDialog(Websites.GetNODocumentationModURL(This.Mod))
	except:
		output = commands.CheatOutput(_connection)
		output("ailed to show mod documentation with the open browser dialog.")

		Debug.Log("Failed to show mod documentation with the open browser dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

def _VisitModPage (_connection: int = None) -> None:
	try:
		Generic.ShowOpenBrowserDialog(Websites.GetNOMainModURL(This.Mod))
	except:
		output = commands.CheatOutput(_connection)
		output("Failed to show the mod page with the open browser dialog.")

		Debug.Log("Failed to show the mod page with the open browser dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

_Setup()
