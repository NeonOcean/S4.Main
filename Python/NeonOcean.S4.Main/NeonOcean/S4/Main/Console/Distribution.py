import codecs
import typing

from NeonOcean.S4.Main import Debug, DistributionShared as ToolsDistribution, LoadingShared, This
from NeonOcean.S4.Main.Console import Command
from NeonOcean.S4.Main.Tools import Exceptions
from NeonOcean.S4.Main.UI import Distribution as UIDistribution, Generic

ShowUpdatesListCommand: Command.ConsoleCommand
ShowURLCommand: Command.ConsoleCommand

def _Setup () -> None:
	global ShowUpdatesListCommand, ShowURLCommand

	commandPrefix = This.Mod.Namespace.lower() + ".distribution"

	ShowURLCommand = Command.ConsoleCommand(_ShowURL, commandPrefix + ".show_url")
	ShowUpdatesListCommand = Command.ConsoleCommand(_ShowUpdatesList, commandPrefix + ".show_updates_list")

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	ShowURLCommand.RegisterCommand()
	ShowUpdatesListCommand.RegisterCommand()

def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	ShowURLCommand.UnregisterCommand()
	ShowUpdatesListCommand.UnregisterCommand()

def _ShowURL (urlHex: str, _connection: int = None) -> None:
	try:
		if not isinstance(urlHex, str):
			raise Exceptions.IncorrectTypeException(urlHex, "urlHex", (str,))
	except Exception as e:
		Debug.Log("Incorrect types for command.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		return

	try:
		url = codecs.decode(urlHex, "hex").decode("utf-8")
		Generic.ShowOpenBrowserDialog(url)
	except Exception as e:
		Debug.Log("Failed to show distribution url.\nURL hex '" + str(urlHex) + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		return

def _ShowUpdatesList (updatedModsHex: str, _connection: int = None) -> None:
	try:
		updatedMods = ToolsDistribution.UpdateInformation.UpdateInformationListFromHex(updatedModsHex)  # type: typing.List[ToolsDistribution.UpdateInformation]
	except Exception as e:
		Debug.Log("Failed to decode the inputted update mods data.\nInputted Hex: " + updatedModsHex, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		return

	try:
		UIDistribution.ShowUpdatesList(updatedMods)
	except Exception as e:
		Debug.Log("Failed to the show updates list dialog.\nInputted Hex: " + updatedModsHex, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		return

_Setup()
