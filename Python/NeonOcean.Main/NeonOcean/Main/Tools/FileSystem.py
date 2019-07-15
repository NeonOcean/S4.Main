import pathlib
import typing
import os

from NeonOcean.Main.Tools import Exceptions

def CloseDirectory (directoryPath: typing.Union[str, pathlib.Path]) -> None:
	"""
	If the specified directory exists and is empty it will be deleted.
	:return:
	"""

	if not isinstance(directoryPath, str) and not isinstance(directoryPath, pathlib.Path):
		raise Exceptions.IncorrectTypeException(directoryPath, "directoryPath", (str, pathlib.Path))

	if isinstance(directoryPath, pathlib.Path):
		directoryPath = str(directoryPath)

	if not os.path.exists(directoryPath):
		return

	if os.path.isfile(directoryPath):
		return

	directoryContents = os.listdir(directoryPath)  # type: typing.List[str]

	if len(directoryContents) == 0:
		os.rmdir(directoryPath)


