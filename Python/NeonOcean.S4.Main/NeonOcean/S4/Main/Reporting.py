import os
import typing
import zipfile

from NeonOcean.S4.Main import LoadingShared, Paths
from NeonOcean.S4.Main.Tools import Exceptions

_reportFileCollectors = set()  # type: typing.Set[typing.Callable[[], typing.List[str]]]

def PrepareReportFiles (reportFilePath: str) -> None:
	"""
	Gather up the files needed for players to report errors to mod creators. This will create a zip file that players can easily send out without effort.
	:param reportFilePath: The file path that the report will be created. This should be the full file path including the extension.
	:type reportFilePath: str
	"""

	reportDirectoryPath = os.path.dirname(reportFilePath)  # type: str

	if not os.path.exists(reportDirectoryPath):
		os.makedirs(reportDirectoryPath)

	if os.path.exists(reportFilePath):
		os.remove(reportFilePath)

	with zipfile.ZipFile(reportFilePath, "w") as reportFile:
		for reportFileCollector in _reportFileCollectors:  # type: typing.Callable[[], typing.List[str]]
			addingFilePaths = reportFileCollector()  # type: typing.List[str]
			addingFilePaths = set(os.path.normpath(addingFilePath) for addingFilePath in addingFilePaths)  # type: typing.Set[str]

			for addingFilePath in addingFilePaths:  # type: str
				addingFileRelativePath = os.path.relpath(addingFilePath, Paths.UserDataPath)  # type: str

				reportFile.write(addingFilePath, addingFileRelativePath)

def RegisterReportFileCollector (reportFileCollector: typing.Callable[[], typing.List[str]]) -> None:
	"""
	Register a report file collector.
	:param reportFileCollector: This should be a callable object that takes no parameters and returns a list of file paths that should be added to the report.
	A single collector may only be registered once. All files to be added to the report should be within the Sims 4 user data folder.
	:type reportFileCollector: typing.Callable[[], typing.List[str]]
	:return:
	"""

	if not isinstance(reportFileCollector, typing.Callable):
		raise Exceptions.IncorrectTypeException(reportFileCollector, "reportFileCollector", ("Callable",))

	_reportFileCollectors.add(reportFileCollector)

def UnregisterReportFileCollector (reportFileCollector: typing.Callable[[], typing.List[str]]) -> None:
	"""
	Unregister a report file collector. If the collector is not registered nothing will happen.
	"""

	if not isinstance(reportFileCollector, typing.Callable):
		raise Exceptions.IncorrectTypeException(reportFileCollector, "reportFileCollector", ("Callable",))

	try:
		_reportFileCollectors.remove(reportFileCollector)
	except KeyError:
		pass

# noinspection PyUnusedLocal
def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	RegisterReportFileCollector(_LastExceptionCollector)

# noinspection PyUnusedLocal
def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	UnregisterReportFileCollector(_LastExceptionCollector)

def _LastExceptionCollector () -> typing.List[str]:
	lastExceptionFilePaths = list()  # type: typing.List[str]

	for lastExceptionFileName in os.listdir(Paths.UserDataPath):
		lastExceptionFileNameLower = lastExceptionFileName.lower()  # type: str

		# noinspection SpellCheckingInspection
		if not (lastExceptionFileNameLower.startswith("lastexception") or lastExceptionFileNameLower.startswith("lastuiexception")) or not lastExceptionFileNameLower.endswith(".txt"):
			continue

		lastExceptionFilePath = os.path.join(Paths.UserDataPath, lastExceptionFileName)

		if not os.path.isfile(lastExceptionFilePath):
			continue

		lastExceptionFilePaths.append(lastExceptionFilePath)

	return lastExceptionFilePaths