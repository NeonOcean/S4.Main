from __future__ import annotations

import os
import pathlib
import typing

from NeonOcean.S4.Main.Tools import Exceptions

def RemoveDirectoryTree (directoryPath: typing.Union[str, pathlib.Path], fileRemovalRequired: bool = True, directoryRemovalRequired: bool = True) -> None:
	"""
	Remove a directory completely along with all subdirectories. If it doesn't exist nothing will happen.
	:param directoryPath: The path of the directory to removed.
	:type directoryPath: str
	:param fileRemovalRequired: Whether or not it is ok to silently leave behind files we couldn't delete. Files and their directories may be
	left behind by this operation if true. Inaccessible directories will be ignored if this is true as we couldn't remove files are undetectable.
	:type fileRemovalRequired: bool
	:param directoryRemovalRequired:  Whether or not it is ok to silently leave behind directory we couldn't delete. Directories that we failed
	delete will remain but should be empty of any files. This function may be forced leave some directories in existence for the sake of
	files we can't delete.
	:type directoryRemovalRequired: bool
	"""

	if not isinstance(directoryPath, str) and not isinstance(directoryPath, pathlib.Path):
		raise Exceptions.IncorrectTypeException(directoryPath, "directoryPath", (str, pathlib.Path))

	if isinstance(directoryPath, pathlib.Path):
		directoryPath = str(directoryPath)

	if not isinstance(fileRemovalRequired, bool):
		raise Exceptions.IncorrectTypeException(fileRemovalRequired, "fileRemovalRequired", (bool,))

	if not isinstance(directoryRemovalRequired, bool):
		raise Exceptions.IncorrectTypeException(directoryRemovalRequired, "directoryRemovalRequired", (bool,))

	try:
		if not os.path.exists(directoryPath):
			return

		if os.path.isfile(directoryPath):
			return

		deletingFileNames = os.listdir(directoryPath)  # type: typing.List[str]
	except Exception if fileRemovalRequired else Exceptions.DummyException:
		return

	clearedDirectory = True  # type: bool

	for deletingName in deletingFileNames:  # type: str
		deletingPath = os.path.join(directoryPath, deletingName)  # type: str

		try:
			deletingIsFile = os.path.isfile(deletingPath)  # type: bool
		except Exception if fileRemovalRequired else Exceptions.DummyException:
			continue

		if deletingIsFile:
			try:
				os.remove(deletingPath)
			except Exception if fileRemovalRequired else Exceptions.DummyException:
				continue
		else:
			RemoveDirectoryTree(deletingPath, fileRemovalRequired = fileRemovalRequired, directoryRemovalRequired = directoryRemovalRequired)

		try:
			if os.path.exists(deletingPath):
				clearedDirectory = False
		except Exception if \
				(fileRemovalRequired if deletingIsFile else directoryRemovalRequired) \
				else Exceptions.DummyException:
			continue

	if clearedDirectory:
		try:
			os.rmdir(directoryPath)
		except Exception if directoryRemovalRequired else Exceptions.DummyException:
			return

def CloseDirectory (directoryPath: typing.Union[str, pathlib.Path], ignoreErrors: bool = False) -> None:
	"""
	If the specified directory exists and is empty it will be deleted.
	:param directoryPath: The path of the directory to closed.
	:type directoryPath: str
	:param ignoreErrors: Whether or not to ignore errors encountered while removing the directory.
	:type ignoreErrors: bool
	"""

	if not isinstance(directoryPath, str) and not isinstance(directoryPath, pathlib.Path):
		raise Exceptions.IncorrectTypeException(directoryPath, "directoryPath", (str, pathlib.Path))

	if isinstance(directoryPath, pathlib.Path):
		directoryPath = str(directoryPath)

	try:
		if not os.path.exists(directoryPath):
			return

		if os.path.isfile(directoryPath):
			return

		directoryContents = os.listdir(directoryPath)  # type: typing.List[str]
	except Exception if not ignoreErrors else Exceptions.DummyException:
		return

	if len(directoryContents) == 0:
		try:
			os.rmdir(directoryPath)
		except Exception if not ignoreErrors else Exceptions.DummyException:
			return
