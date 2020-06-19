from __future__ import annotations

import time
import typing

import services
import snippets
import zone
from NeonOcean.S4.Main import Debug, Director, This
from NeonOcean.S4.Main.Tools import Types

_scanningSnippets = dict()  # type: typing.Dict[str, typing.List[typing.Callable]]

class _Announcer(Director.Announcer):
	Host = This.Mod

	_priority = 5000

	_zoneLoadTriggered = False  # type: bool

	@classmethod
	def ZoneLoad (cls, zoneReference: zone.Zone) -> None:
		if not cls._zoneLoadTriggered:
			_ScanForAllSnippets()
			cls._zoneLoadTriggered = True

def SetupSnippetScanning (snippetType: str, callback: typing.Callable) -> None:
	"""
	Once all snippet tuning is loaded, we will look for any snippets with this type and report them as a list to the callback. The snippet type
	needs to be defined in the game's 'snippets' module or the callback will receive nothing.
	:param snippetType: The type of the snippet, this is a unique string used to identify a snippet's type. This needs to be defined in the
	game's 'snippets' module or the callback will receive nothing.
	:type snippetType: str
	:param callback: The callback that will be triggered once all snippet tuning has been loaded. This should take one parameter, a list
	of tuned snippet instances. If this callback is already registered to this snippet type nothing will happen.
	:type callback: typing.Callable
	"""

	snippetTypeCallbacks = _scanningSnippets.get(snippetType, None)  # type: typing.List[typing.Callable]

	if snippetTypeCallbacks is None:
		snippetTypeCallbacks = list()
		_scanningSnippets[snippetType] = snippetTypeCallbacks

	if callback in snippetTypeCallbacks:
		return

	snippetTypeCallbacks.append(callback)

def _ScanForAllSnippets () -> None:
	if services.snippet_manager is None:
		raise Exception("Cannot look for snippets, the manager is None.")

	if len(_scanningSnippets) == 0:
		return

	operationStartTime = time.time()  # type: float

	snippetsByType = dict()  # type: typing.Dict[str, typing.List[snippets.SnippetInstanceMetaclass]]

	for snippetID, snippet in services.snippet_manager().types.items():  # type: typing.Any, snippets.SnippetInstanceMetaclass
		if isinstance(snippet, snippets.SnippetInstanceMetaclass):
			snippetList = snippetsByType.get(snippet.snippet_type, None)  # type: typing.List[snippets.SnippetInstanceMetaclass]

			if snippetList is None:
				snippetList = list()
				snippetsByType[snippet.snippet_type] = snippetList

			snippetList.append(snippet)

	for snippetType, snippetCallbacks in _scanningSnippets.items():  # type: str, typing.List[typing.Callable]
		snippetList = snippetsByType.get(snippetType, None)

		if snippetList is None:
			snippetList = list()

		for snippetCallback in snippetCallbacks:  # type: typing.Callable
			try:
				snippetCallback(snippetList)
			except:
				Debug.Log("Failed to trigger snippet scan callback at '%s'." % Types.GetFullName(snippetCallback), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	operationTime = time.time() - operationStartTime
	Debug.Log("Finished scanning for %s types of snippet in %s seconds with %s snippets existing." % (len(_scanningSnippets), operationTime, len(services.snippet_manager().types)), This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)
