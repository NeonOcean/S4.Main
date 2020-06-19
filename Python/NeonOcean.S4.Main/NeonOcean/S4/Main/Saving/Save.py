from __future__ import annotations

import datetime
import enum_lib
import json
import os
import pathlib
import re
import shutil
import typing
import uuid

import services
from NeonOcean.S4.Main import Debug, Language, Mods, Paths, Saving, This
from NeonOcean.S4.Main.Saving import SaveShared
from NeonOcean.S4.Main.Tools import Exceptions, FileSystem
from NeonOcean.S4.Main.UI import Notifications
from ui import ui_dialog_notification

FailureNotificationsTitle = Language.String(This.Mod.Namespace + ".Saving.Failure_Notifications.Title")  # type: Language.String

FailureNotificationsLoadText = Language.String(This.Mod.Namespace + ".Saving.Failure_Notifications.Load_Text")  # type: Language.String
FailureNotificationsSaveText = Language.String(This.Mod.Namespace + ".Saving.Failure_Notifications.Save_Text")  # type: Language.String
FailureNotificationsCommitText = Language.String(This.Mod.Namespace + ".Saving.Failure_Notifications.Commit_Text")  # type: Language.String

FailureNotificationsModLoadText = Language.String(This.Mod.Namespace + ".Saving.Failure_Notifications.Mod_Load_Text")  # type: Language.String
FailureNotificationsModSaveText = Language.String(This.Mod.Namespace + ".Saving.Failure_Notifications.Mod_Save_Text")  # type: Language.String
FailureNotificationsModUnloadText = Language.String(This.Mod.Namespace + ".Saving.Failure_Notifications.Mod_Unload_Text")  # type: Language.String

WarningNotificationsTitle = Language.String(This.Mod.Namespace + ".Saving.Warning_Notifications.Title")  # type: Language.String
WarningNotificationsMismatchGUIDText = Language.String(This.Mod.Namespace + ".Saving.Warning_Notifications.Mismatch_GUID_Text")  # type: Language.String
WarningNotificationsMismatchGameTickText = Language.String(This.Mod.Namespace + ".Saving.Warning_Notifications.Mismatch_Game_Tick_Text")  # type: Language.String

_registeredSavingObjects = list()  # type: typing.List[Saving.SaveBase]
_maximumBackups = 5  # type: int

_loadedSlotID = None  # type: typing.Optional[int]
_loadedDirectoryPath = None  # type: typing.Optional[str]

_activeSlotID = None  # type: typing.Optional[int]

class ModSaveMatchTypes(enum_lib.IntFlag):
	"""
	Types to show how well a game save matches mod save folders based on their meta data.
	Match - Based on the mod save's meta data, it appears to be matching.
	MismatchedGUID - The guid of the game save and the mod saves do not match, this means they are for completely different save games.
	MismatchedGameTick - The guid must match but the game tick does not match. This would be true if the mod saves pair with a later or earlier save of the same game.
	"""

	Match = 1  # type: ModSaveMatchTypes
	MismatchedGUID = 2  # type: ModSaveMatchTypes
	MismatchedGameTick = 4  # type: ModSaveMatchTypes

class ModSaveMetaData:
	def __init__ (self, saveDirectoryPath: str, name: str, guid: int, gameTick: int):
		if not isinstance(saveDirectoryPath, str):
			raise Exceptions.IncorrectTypeException(saveDirectoryPath, "saveDirectoryPath", (str,))

		if not isinstance(name, str):
			raise Exceptions.IncorrectTypeException(name, "name", (str,))

		if not isinstance(guid, int):
			raise Exceptions.IncorrectTypeException(guid, "guid", (int,))

		if not isinstance(gameTick, int):
			raise Exceptions.IncorrectTypeException(gameTick, "gameTick", (int,))

		self.SaveDirectoryPath = saveDirectoryPath  # type: str
		self.Name = name  # type: str
		self.GUID = guid  # type: int
		self.GameTick = gameTick  # type: int

	def MatchesGameSave (self) -> ModSaveMatchTypes:
		"""
		Get whether or not the mod save data matches the loaded game data.
		:return: A mod slot match type, check the class for details for the meaning of each value.
		:rtype: ModSaveMatchTypes
		"""

		GameGUID = services.get_persistence_service().get_save_slot_proto_guid()  # type: int
		GameGameTick = services.get_persistence_service().get_save_slot_proto_buff().gameplay_data.world_game_time

		if self.GUID != GameGUID:
			return ModSaveMatchTypes.MismatchedGUID

		if self.GameTick != GameGameTick:
			return ModSaveMatchTypes.MismatchedGameTick

		return ModSaveMatchTypes.Match

def RegisterSavingObject (savingObject: Saving.SaveBase) -> None:
	"""
	Register a saving object to be handled here.
	"""

	global _registeredSavingObjects

	if not isinstance(savingObject, Saving.SaveBase):
		raise Exceptions.IncorrectTypeException(savingObject, "savingObject", (Saving.SaveBase,))

	if savingObject in _registeredSavingObjects:
		return

	_registeredSavingObjects.append(savingObject)

def UnregisterSavingObject (savingObject: Saving.SaveBase) -> None:
	_registeredSavingObjects.remove(savingObject)

def GetLoadedSlotID () -> typing.Optional[int]:
	"""
	Get the loaded slot id, the slot id that the loaded mod data was first gotten from or last saved to. This will be None if nothing is loaded.
	"""

	return _loadedSlotID

def GetLoadedDirectoryPath () -> typing.Optional[str]:
	"""
	Get the loaded directory path, the directory that the loaded mod data was first gotten from or last saved to. This will be None if nothing is loaded.
	"""

	return _loadedDirectoryPath

def GetActiveSlotID () -> typing.Optional[int]:
	"""
	Get the active slot id, the slot id that the data is temporarily being saved to and loaded from between zone changes. This will be None if nothing is loaded.
	"""

	return _activeSlotID

def Load (loadSlotID: int, loadingDirectoryPath: typing.Optional[str] = None, changingSave: bool = False) -> None:
	"""
	Load the specified slot in every registered and enabled saving object.
	:param loadSlotID: The save slot id of the game's loaded save file. This must be greater than or equal to 0.
	:type loadSlotID: int
	:param loadingDirectoryPath: This parameter allows you to load a specific directory. If this is not None, we will copy this directory into the slot's active path to load it.
	Anything already existing at the activated path will be lost unless the path is pointing to the activated path.
	activated instead.
	:type loadingDirectoryPath: str | None
	:param changingSave: Whether or not we are switching to another save.
	:type changingSave: bool
	"""

	global _loadedSlotID, _loadedDirectoryPath

	if not isinstance(loadSlotID, int):
		raise Exceptions.IncorrectTypeException(loadSlotID, "loadSlotID", (int,))

	if loadSlotID < 0:
		raise Exception("loadSlotID values must be greater than or equal to 0.")

	if not isinstance(loadingDirectoryPath, str) and loadingDirectoryPath is not None:
		raise Exceptions.IncorrectTypeException(loadingDirectoryPath, "loadingDirectoryPath", (str, None))

	if not isinstance(changingSave, bool):
		raise Exceptions.IncorrectTypeException(changingSave, "changingSave", (bool,))

	if loadingDirectoryPath is not None:
		Debug.Log("Loading the directory '" + Paths.StripUserDataPath(loadingDirectoryPath) + "' in save slot %s for %s saving object(s)." % (loadSlotID, len(_registeredSavingObjects)), This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)
	else:
		Debug.Log("Loading save slot %s for %s saving object(s)." % (loadSlotID, len(_registeredSavingObjects)), This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

	loadingFailure = False  # type: bool

	failedSavingIdentifiers = list()  # type: typing.List[str]
	mismatchGUIDSavingIdentifiers = list()  # type: typing.List[str]
	mismatchGameTickSavingIdentifiers = list()  # type: typing.List[str]

	if _loadedSlotID is None or _loadedDirectoryPath is None:
		changingSave = True

	if loadingDirectoryPath is not None:
		changingSave = True

		try:
			ActivateDirectoryToSlot(loadingDirectoryPath, loadSlotID)
		except:
			Debug.Log("Failed to activate the directory at %s in save slot %s" % (Paths.StripUserDataPath(loadingDirectoryPath), loadSlotID), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			loadingFailure = True
	else:
		loadingDirectoryPath = GetModSaveDirectoryPath(loadSlotID)  # type: str

		if _activeSlotID != loadSlotID:
			try:
				ActivateDirectoryToSlot(loadingDirectoryPath, loadSlotID)
			except:
				Debug.Log("Failed to activate save slot %s" % (loadSlotID,), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
				loadingFailure = True

	loadingActiveDirectoryPath = GetModSaveActiveDirectoryPath(loadSlotID)  # type: str

	modSaveMetaDataFileName = GetModSaveMetaDataFileName()  # type: str

	for savingObject in _registeredSavingObjects:  # type: Saving.SaveBase
		try:
			if not savingObject.Enabled:
				continue

			savingObjectFileName = savingObject.GetSaveFileName()  # type: str

			if savingObjectFileName == modSaveMetaDataFileName:
				Debug.Log("Had to skip a saving object with the identifier '" + savingObject.Identifier + "' because its file name was '" + modSaveMetaDataFileName + "' which conflicts with an important file.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
				continue

			loadingFilePath = os.path.abspath(os.path.join(loadingActiveDirectoryPath, savingObject.GetSaveFileName()))  # type: str

			modLoadSuccessful = savingObject.Load(loadingFilePath)  # type: bool
		except Exception:
			Debug.Log("Encountered an unhandled exception upon loading a saving object with the identifier '" + savingObject.Identifier + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			modLoadSuccessful = False

		if not modLoadSuccessful:
			failedSavingIdentifiers.append(savingObject.Identifier)

		if modLoadSuccessful:
			savingObjectGUID = savingObject.DataGUID  # type: typing.Optional[int]

			if savingObjectGUID is not None:
				gameSaveGUID = services.get_persistence_service().get_save_slot_proto_guid()  # type: int

				if savingObjectGUID != gameSaveGUID:
					mismatchGUIDSavingIdentifiers.append(savingObject.Identifier)
					continue

			savingObjectGameTick = savingObject.DataGameTick  # type: typing.Optional[int]

			if savingObjectGameTick is not None:
				gameplaySaveSlotData = services.get_persistence_service().get_save_slot_proto_buff().gameplay_data

				if savingObjectGameTick != gameplaySaveSlotData.world_game_time:
					mismatchGameTickSavingIdentifiers.append(savingObject.Identifier)
					continue

	if changingSave:
		_loadedSlotID = loadSlotID
		_loadedDirectoryPath = loadingDirectoryPath

	if loadingFailure:
		_ShowLoadFailureDialog()

	if len(failedSavingIdentifiers) != 0:
		_ShowModLoadFailureDialog(failedSavingIdentifiers)

	if len(mismatchGUIDSavingIdentifiers) != 0:
		_ShowMismatchGUIDWarningDialog(mismatchGUIDSavingIdentifiers)

	if len(mismatchGameTickSavingIdentifiers) != 0:
		_ShowMismatchGameTickWarningDialog(mismatchGameTickSavingIdentifiers)

	Debug.Log("Finished loading %s saving object(s) with %s failing." % (len(_registeredSavingObjects), str(len(failedSavingIdentifiers))), This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

def Save (saveSlotID: int, commitSave: bool = False) -> None:
	"""
	Save every registered and enabled saving object's data to their active save files.
	:param saveSlotID: The save slot id this is suppose to saved to. This must be greater than or equal to 0.
	:type saveSlotID: int
	:param commitSave: If this function should commit the save file, to actually save the game not just write it to a temporary file. Save file
	commits should typically occur when the game does the same.
	:type commitSave: bool
	"""

	global _activeSlotID

	if saveSlotID is None:
		saveSlotID = services.get_persistence_service().get_save_slot_proto_buff().slot_id  # type: int

	if not isinstance(saveSlotID, int):
		raise Exceptions.IncorrectTypeException(saveSlotID, "saveSlotID", (int,))

	if saveSlotID < 0:
		raise Exception("saveSlotID values must be greater than or equal to 0.")

	if not isinstance(commitSave, bool):
		raise Exceptions.IncorrectTypeException(commitSave, "commitSave", (bool,))

	if commitSave:
		Debug.Log("Saving and committing %s saving object(s) to save slot %s." % (len(_registeredSavingObjects), saveSlotID), This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)
	else:
		Debug.Log("Saving %s saving object(s) to save slot %s" % (len(_registeredSavingObjects), saveSlotID), This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

	savingFailure = False  # type: bool
	failedSavingIdentifiers = list()  # type: typing.List[str]

	try:
		if _activeSlotID != saveSlotID:
			DeactivateActiveSlot()
	except:
		Debug.Log("Failed to deactivate the active save directory.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
		savingFailure = True

	_activeSlotID = saveSlotID

	savingDirectoryPath = GetModSaveActiveDirectoryPath(saveSlotID)  # type: str

	modSaveMetaDataFileName = GetModSaveMetaDataFileName()  # type: str

	for savingObject in _registeredSavingObjects:  # type: Saving.SaveBase
		try:
			if not savingObject.Enabled:
				continue

			if not savingObject.Loaded:
				Debug.Log("Went to save a saving object with the identifier '" + savingObject.Identifier + "' but it wasn't loaded.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				continue

			savingObjectFileName = savingObject.GetSaveFileName()  # type: str

			if savingObjectFileName == modSaveMetaDataFileName:
				Debug.Log("Had to skip a saving object with the identifier '" + savingObject.Identifier + "' because its file name was '" + modSaveMetaDataFileName + "' which conflicts with an important file.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
				continue

			savingFilePath = os.path.abspath(os.path.join(savingDirectoryPath, savingObject.GetSaveFileName()))  # type: str

			modSaveSuccessful = savingObject.Save(savingFilePath)  # type: bool
		except Exception:
			Debug.Log("Encountered an unhandled exception upon saving a saving object with the identifier '" + savingObject.Identifier + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			modSaveSuccessful = False  # type: bool

		if not modSaveSuccessful:
			failedSavingIdentifiers.append(savingObject.Identifier)

	try:
		_CreateSaveMetaDataFile(savingDirectoryPath)
	except:
		Debug.Log("Failed to write a save meta file into the slot %s" % saveSlotID, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	if commitSave:
		Commit(savingDirectoryPath, saveSlotID)

	if savingFailure:
		_ShowSaveFailureDialog()

	if len(failedSavingIdentifiers) != 0:
		_ShowModSaveFailureDialog(failedSavingIdentifiers)

	Debug.Log("Finished saving %s saving object(s) with %s failing." % (len(_registeredSavingObjects), str(len(failedSavingIdentifiers))), This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

def Commit (sourceDirectoryPath: str, commitSlotID: int) -> None:
	"""
	Copy the active directory in this slot to its actual save directory and backup old save directories. If the active directory doesn't exist nothing will happen.
	:param sourceDirectoryPath: The path of the mod save folder that will be copied to the slot.
	:type sourceDirectoryPath: str
	:param commitSlotID: The save slot id suppose to be committed. This must be greater than or equal to 0.
	:type commitSlotID: int
	"""

	global _loadedSlotID, _loadedDirectoryPath

	if not isinstance(sourceDirectoryPath, str):
		raise Exceptions.IncorrectTypeException(sourceDirectoryPath, "sourceDirectoryPath", (str,))

	if not isinstance(commitSlotID, int):
		raise Exceptions.IncorrectTypeException(commitSlotID, "commitSlotID", (int,))

	if commitSlotID < 0:
		raise Exception("commitSlotID values must be greater than or equal to 0.")

	Debug.Log("Committing the directory '%s' to the slot %s." % (Paths.StripUserDataPath(sourceDirectoryPath), commitSlotID), This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

	committingDirectoryPath = GetModSaveDirectoryPath(commitSlotID)  # type: str
	currentTimestamp = datetime.datetime.now().timestamp()  # type: float

	try:
		_ShiftBackupDirectories(commitSlotID)

		if os.path.exists(sourceDirectoryPath):
			shutil.copytree(sourceDirectoryPath, committingDirectoryPath)
			os.utime(committingDirectoryPath, (currentTimestamp, currentTimestamp))
		else:
			Debug.Log("The commit source directory at '%s' does not exist." % Paths.StripUserDataPath(sourceDirectoryPath), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
	except:
		Debug.Log("Failed to commit to save slot '" + str(commitSlotID) + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
		_ShowCommitFailureDialog()
		return

	_loadedSlotID = commitSlotID
	_loadedDirectoryPath = committingDirectoryPath

	Debug.Log("Finished committing to save slot %s." % commitSlotID, This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

def DoOverrideBackupCommit (slotID: int) -> None:
	"""
	Override backup commits should happen when the game overrides an existing save file, but only when the save file being overwritten has a different GUID.
	Anytime the game does this it always creates an entirely new save file from the save data existing in the overriding slot before the current game is written to
	the save slot. I'm not sure why the game does this, but this function exists prevent mod save backup files from not matching their game backup file due to this
	scenario.

	:param slotID: The save slot id suppose to be worked on. This must be greater than or equal to 0.
	:type slotID: int
	"""

	if not isinstance(slotID, int):
		raise Exceptions.IncorrectTypeException(slotID, "slotID", (int,))

	if slotID < 0:
		raise Exception("slotID values must be greater than or equal to 0.")

	Debug.Log("Doing an override backup commit for save slot %s." % slotID, This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

	saveDirectoryPath = GetModSaveDirectoryPath(slotID)  # type: str

	try:
		if not os.path.exists(saveDirectoryPath):
			_ShiftBackupDirectories(slotID)
			return

		saveTemporaryDirectoryParentPath = os.path.join(Paths.TemporaryPath, "Saves", str(uuid.uuid4()))  # type: str
		saveTemporaryDirectoryPath = os.path.join(saveTemporaryDirectoryParentPath, os.path.split(saveDirectoryPath)[1])  # type: str

		if not os.path.exists(saveTemporaryDirectoryParentPath):
			os.makedirs(saveTemporaryDirectoryParentPath)

		shutil.copytree(saveDirectoryPath, saveTemporaryDirectoryPath)

		_ShiftBackupDirectories(slotID)

		_MoveDirectory(saveTemporaryDirectoryPath, saveDirectoryPath)

		FileSystem.RemoveDirectoryTree(saveTemporaryDirectoryParentPath, directoryRemovalRequired = True)
		FileSystem.CloseDirectory(Paths.TemporaryPath, ignoreErrors = True)
	except:
		Debug.Log("Failed to do an override backup commit for save slot %s" % slotID, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
		return

	Debug.Log("Finished doing an override backup commit for save slot %s." % slotID, This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

def UnloadAll () -> None:
	"""
	Unload every registered and loaded saving object.
	"""

	Debug.Log("Unloading %s saving object(s)." % len(_registeredSavingObjects), This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

	failedSavingIdentifiers = list()  # type: typing.List[str]

	for savingObject in _registeredSavingObjects:  # type: Saving.SaveBase
		try:
			if not savingObject.Loaded:
				continue

			savingObject.Unload()  # type: bool
		except Exception:
			Debug.Log("Encountered an unhandled exception upon unloading a saving object with the identifier '" + savingObject.Identifier + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			failedSavingIdentifiers.append(savingObject.Identifier)

	if len(failedSavingIdentifiers) != 0:
		_ShowModUnloadFailureDialog(failedSavingIdentifiers)

	Debug.Log("Finished unloading %s saving object(s) with %s failing." % (len(_registeredSavingObjects), str(len(failedSavingIdentifiers))), This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

def UnloadWithHost (host: Mods.Mod) -> None:
	"""
	Unload all registered and loaded saving objects with the specified host
	"""

	if not isinstance(host, Mods.Mod):
		raise Exceptions.IncorrectTypeException(host, "host", (Mods.Mod,))

	Debug.Log("Unloading all saving objects from the host '%s'" % host.Namespace, This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

	failedSavingIdentifiers = list()  # type: typing.List[str]

	for savingObject in _registeredSavingObjects:  # type: Saving.SaveBase
		try:
			if not savingObject.Host == host:
				continue

			if not savingObject.Loaded:
				continue

			savingObject.Unload()  # type: bool
		except Exception:
			Debug.Log("Encountered an unhandled exception upon unloading a saving object with the identifier '" + savingObject.Identifier + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			failedSavingIdentifiers.append(savingObject.Identifier)

	if len(failedSavingIdentifiers) != 0:
		_ShowModUnloadFailureDialog(failedSavingIdentifiers)

	Debug.Log("Finished unloading all saving object from the host '%s' and encountered %s error(s)." % (host.Namespace, str(len(failedSavingIdentifiers))), This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

def PrepareForSaveChange () -> None:
	"""
	Prepare this module to load a different save file.
	"""

	global _loadedSlotID, _loadedDirectoryPath

	try:
		DeactivateActiveSlot()
	except:
		Debug.Log("Failed to deactivate the active save directory.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	_loadedSlotID = None
	_loadedDirectoryPath = None

def GetSaveMetaData (saveDirectoryPath: str) -> typing.Optional[ModSaveMetaData]:
	"""
	Get a meta data object for this mod save directory.
	:return: The meta data of this mod save directory or None if there was an error reading it or the meta data file doesn't exist.
	:rtype: typing.Optional[ModSaveMetaData]
	"""

	if not isinstance(saveDirectoryPath, str):
		raise Exceptions.IncorrectTypeException(saveDirectoryPath, "saveDirectoryPath", (str,))

	metaDataFilePath = os.path.join(saveDirectoryPath, GetModSaveMetaDataFileName())  # type: str

	if not os.path.exists(metaDataFilePath):
		return None

	try:
		with open(metaDataFilePath) as metaDataFile:
			metaData = json.JSONDecoder().decode(metaDataFile.read())  # type: typing.Dict[str, typing.Any]

		if not isinstance(metaData, dict):
			raise Exceptions.IncorrectTypeException(metaData, "Root", (dict,))

		name = metaData["Name"]  # type: str
		guid = metaData["GUID"]  # type: int
		gameTick = metaData["GameTick"]  # type: int

		if not isinstance(name, str):
			raise Exceptions.IncorrectTypeException(name, "Root[Name]", (str,))

		if not isinstance(guid, int):
			raise Exceptions.IncorrectTypeException(guid, "Root[GUID]", (int,))

		if not isinstance(gameTick, int):
			raise Exceptions.IncorrectTypeException(gameTick, "Root[GameTick]", (int,))

		return ModSaveMetaData(saveDirectoryPath, name, guid, gameTick)
	except:
		return None

def ActivateSaveSlot (slotID: int) -> None:
	"""
	Copy the mod save folder in the specified save slot to its active path where it will be available to be loaded. If a permanent mod saves folder with the specified
	slot id doesn't exist nothing will be copied. If any saves folder is already active it will be deactivated before activating the new folder.

	:param slotID: The targeted slot id. This must be greater than or equal to 0.
	:type slotID: int
	"""

	global _activeSlotID

	if not isinstance(slotID, int):
		raise Exceptions.IncorrectTypeException(slotID, "slotID", (int,))

	if slotID < 0:
		raise Exception("slotID values must be greater than or equal to 0.")

	DeactivateActiveSlot()

	saveDirectoryPath = GetModSaveDirectoryPath(slotID)  # type: str
	activeDirectoryPath = GetModSaveActiveDirectoryPath(slotID)  # type: str
	activeDirectoryParentPath = os.path.dirname(activeDirectoryPath)  # type: str

	if pathlib.Path(saveDirectoryPath) == pathlib.Path(activeDirectoryPath):
		return

	if not os.path.exists(saveDirectoryPath):
		return

	if not os.path.exists(activeDirectoryParentPath):
		os.makedirs(activeDirectoryParentPath)

	if os.path.exists(activeDirectoryPath):
		FileSystem.RemoveDirectoryTree(activeDirectoryPath, directoryRemovalRequired = True)

	shutil.copytree(saveDirectoryPath, activeDirectoryPath)

	_activeSlotID = slotID

def ActivateDirectoryToSlot (activatingDirectoryPath: str, slotID: int) -> None:
	"""
	Copy the specified directory to the specified slot id's active path where it will be available to be loaded. If the activating directory doesnt exist nothing will be
	copied. If any saves folder is already active it will be deactivated before activating the new folder.

	:param activatingDirectoryPath: The path of the directory that will be activated.
	:type activatingDirectoryPath: str
	:param slotID: The slot id the directory will be activated to. This must be greater than or equal to 0.
	:type slotID: int
	"""

	global _activeSlotID

	if not isinstance(slotID, int):
		raise Exceptions.IncorrectTypeException(slotID, "slotID", (int,))

	if slotID < 0:
		raise Exception("slotID values must be greater than or equal to 0.")

	DeactivateActiveSlot()

	activeDirectoryPath = GetModSaveActiveDirectoryPath(slotID)  # type: str
	activeDirectoryParentPath = os.path.dirname(activeDirectoryPath)  # type: str

	if pathlib.Path(activatingDirectoryPath) == pathlib.Path(activeDirectoryPath):
		return

	if not os.path.exists(activatingDirectoryPath):
		return

	if not os.path.exists(activeDirectoryParentPath):
		os.makedirs(activeDirectoryParentPath)

	if os.path.exists(activeDirectoryPath):
		FileSystem.RemoveDirectoryTree(activeDirectoryPath, directoryRemovalRequired = True)

	shutil.copytree(activatingDirectoryPath, activeDirectoryPath)

	_activeSlotID = slotID

def DeactivateActiveSlot () -> None:
	"""
	Deactivate the currently active mod save slot. Nothing will happen if no mod save slot is active.
	"""

	global _activeSlotID

	activeSlotID = _activeSlotID  # type: typing.Optional[int]

	if activeSlotID is not None:
		activeDirectoryPath = GetModSaveActiveDirectoryPath(activeSlotID)  # type: str

		if os.path.exists(activeDirectoryPath):
			FileSystem.RemoveDirectoryTree(activeDirectoryPath, directoryRemovalRequired = True)

	_activeSlotID = None

def GetModSaveDirectoryPath (slotID: int) -> str:
	"""
	Get the mod save directory, the latest mod save directory for this slot.
	Saving objects that don't use these directories shouldn't use the built in handler as it moves save files by moving the entire directory.
	:param slotID: The slot id of the targeted mod saves folder. This must be greater than or equal to 0.
	:type slotID: int
	"""

	if not isinstance(slotID, int):
		raise Exceptions.IncorrectTypeException(slotID, "slotID", (int,))

	if slotID < 0:
		raise Exception("slotID values must be greater than or equal to 0.")

	return os.path.join(Paths.SavesPath, "Slot_" + SaveShared.GetSlotIDString(slotID) + "_NO")

def GetModSaveActiveDirectoryPath (slotID: int) -> str:
	"""
	Get the mod save active directory, the file that is saved to and loaded from anytime the zone changes. This will only exist when the game is running.
	Saving objects that don't use these directories shouldn't use the built in handler as it moves save files by moving the entire directory.
	:param slotID: The slot id of the targeted mod saves folder. This must be greater than or equal to 0.
	:type slotID: int
	"""

	if not isinstance(slotID, int):
		raise Exceptions.IncorrectTypeException(slotID, "slotID", (int,))

	if slotID < 0:
		raise Exception("slotID values must be greater than or equal to 0.")

	return os.path.join(Paths.SavesPath, "Slot_" + SaveShared.GetSlotIDString(slotID) + "_NO_Active")

def GetModSaveBackupDirectoryPath (slotID: int, backupIndex: int) -> str:
	"""
	Get a mod save backup directory. All backup directories should correspond with a game's backup save file.
	Saving objects that don't use these directories shouldn't use the built in handler as it moves save files by moving the entire directory.
	:param slotID: The slot id of the targeted mod saves folder. This must be greater than or equal to 0.
	:type slotID: int
	:param backupIndex: The index of the target backup mod saves folder. The game's save backup files go up to the index of 4 and mod save folders do the same.
	:type backupIndex: int
	"""

	if not isinstance(slotID, int):
		raise Exceptions.IncorrectTypeException(slotID, "slotID", (int,))

	if slotID < 0:
		raise Exception("slotID values must be greater than or equal to 0.")

	if not isinstance(backupIndex, int):
		raise Exceptions.IncorrectTypeException(backupIndex, "backupIndex", (int,))

	if backupIndex < 0 or backupIndex > 5:
		raise Exception("backupIndex values must be between 0 and 5.")

	return os.path.join(Paths.SavesPath, "Slot_" + SaveShared.GetSlotIDString(slotID) + "_NO.ver" + str(backupIndex))

def GetModSaveMetaDataFileName () -> str:
	"""
	Get the file name of every mod save meta data file.
	"""

	return "Meta_Data.json"

def IsSaveDirectory (saveDirectory: str) -> bool:
	"""
	Get whether or not the specified save directory is a one that could be saved to or loaded from by this module.
	:param saveDirectory: The name or the path of a potential save directory.
	:type saveDirectory: str
	"""

	saveDirectory = os.path.basename(saveDirectory)

	saveDirectoryMatch = re.match("^Slot_[0-9|A-F]{8}_NO$", saveDirectory, re.IGNORECASE)

	if saveDirectoryMatch is None:
		return False

	return True

def GetSaveDirectorySlot (saveDirectory: str) -> typing.Optional[int]:
	"""
	Get the slot of the specified save directory. This must be a valid save directory, use the IsSaveDirectory function.
	:param saveDirectory: The name or the path of a save directory.
	:type saveDirectory: str
	:return: The slot of the specified save directory or None if the save directory is invalid.
	:rtype: int | None
	"""

	saveDirectory = os.path.basename(saveDirectory)

	saveDirectoryMatch = re.match("^(Slot_)([0-9|A-F]{8})(_NO)$", saveDirectory, re.IGNORECASE)

	if saveDirectoryMatch is None:
		return None

	saveDirectorySlotID = int(saveDirectoryMatch.groups()[1], 16)  # type: int

	return saveDirectorySlotID

def _ShiftBackupDirectories (slotID: int) -> None:
	"""
	Shift the backup directories in this slot to follow the game's save backups. After this is called, the most recent save directory will have been either moved to the
	backup or deleted. If the maximum amount of backup save directories exist, the oldest backup will be deleted.
	:param slotID: The slot id of the targeted save directories.
	:type slotID: int
	"""

	_VerifyBackupDirectories(slotID)

	saveDirectoryPath = GetModSaveDirectoryPath(slotID)  # type: str

	if _maximumBackups <= 0:
		if os.path.exists(saveDirectoryPath):
			FileSystem.RemoveDirectoryTree(saveDirectoryPath, directoryRemovalRequired = True)

		return

	for backupIndex in reversed(range(_maximumBackups)):  # type: int
		currentBackupDirectoryPath = GetModSaveBackupDirectoryPath(slotID, backupIndex)  # type: str

		if not os.path.exists(currentBackupDirectoryPath):
			continue

		if backupIndex == _maximumBackups - 1:
			FileSystem.RemoveDirectoryTree(currentBackupDirectoryPath, directoryRemovalRequired = True)
			continue

		nextBackupDirectoryPath = GetModSaveBackupDirectoryPath(slotID, backupIndex + 1)  # type: str
		nextBackupDirectoryParentPath = os.path.dirname(nextBackupDirectoryPath)  # type: str

		if os.path.exists(nextBackupDirectoryPath):
			FileSystem.RemoveDirectoryTree(nextBackupDirectoryPath, directoryRemovalRequired = True)

		if not os.path.exists(nextBackupDirectoryParentPath):
			os.makedirs(nextBackupDirectoryParentPath)

		_MoveDirectory(currentBackupDirectoryPath, nextBackupDirectoryPath)

	if os.path.exists(saveDirectoryPath):
		firstBackupDirectoryPath = GetModSaveBackupDirectoryPath(slotID, 0)  # type: str
		firstBackupDirectoryParentPath = os.path.dirname(firstBackupDirectoryPath)  # type: str

		assert not os.path.exists(firstBackupDirectoryPath)

		if not os.path.exists(firstBackupDirectoryParentPath):
			os.makedirs(firstBackupDirectoryParentPath)

		_MoveDirectory(saveDirectoryPath, firstBackupDirectoryPath)

	saveDirectoryParentPath = os.path.dirname(saveDirectoryPath)  # type: str
	FileSystem.CloseDirectory(saveDirectoryParentPath, ignoreErrors = True)

def _VerifyBackupDirectories (slotID: int) -> None:
	"""
	Verify that all existing backups have an attached game backup file that still exists. If the game backup save doesn't exist, the corresponding backup
	will be deleted.
	:param slotID: The slot id of the targeted save file.
	:type slotID: int
	"""

	for backupIndex in range(_maximumBackups):  # type: int
		gameBackupFilePath = SaveShared.GetGameSaveBackupFilePath(slotID, backupIndex)  # type: str
		backupDirectoryPath = GetModSaveBackupDirectoryPath(slotID, backupIndex)  # type: str
		backupDirectoryParentPath = os.path.dirname(backupDirectoryPath)  # type: str

		if not os.path.exists(gameBackupFilePath) and os.path.exists(backupDirectoryPath):
			FileSystem.RemoveDirectoryTree(backupDirectoryPath, directoryRemovalRequired = True)
			FileSystem.CloseDirectory(backupDirectoryParentPath, ignoreErrors = True)

def _CreateSaveMetaDataFile (metaDataDirectoryPath: str) -> None:
	metaDataFilePath = os.path.join(metaDataDirectoryPath, GetModSaveMetaDataFileName())  # type: str

	name = services.get_persistence_service().get_save_slot_proto_buff().slot_name  # type: str
	guid = services.get_persistence_service().get_save_slot_proto_guid()  # type: int
	gameTick = services.get_persistence_service().get_save_slot_proto_buff().gameplay_data.world_game_time  # type: int

	metaData = {
		"Name": name,
		"GUID": guid,
		"GameTick": gameTick
	}

	if not os.path.exists(metaDataDirectoryPath):
		os.makedirs(metaDataDirectoryPath)

	with open(metaDataFilePath, "w+") as metaDataFile:
		metaDataFile.write(json.JSONEncoder(indent = "\t").encode(metaData))

def _MoveDirectory (currentDirectoryPath: str, targetDirectoryPath: str) -> None:
	if not os.path.exists(currentDirectoryPath):
		return

	if os.path.isfile(currentDirectoryPath):
		return

	currentDirectoryModifiedTime = os.path.getmtime(currentDirectoryPath)  # type: float
	currentDirectoryAccessedTime = os.path.getatime(currentDirectoryPath)  # type: float

	if not os.path.exists(targetDirectoryPath):
		os.makedirs(targetDirectoryPath)
		shutil.copystat(currentDirectoryPath, targetDirectoryPath)

	for currentFileName in os.listdir(currentDirectoryPath):  # type: str
		currentFilePath = os.path.join(currentDirectoryPath, currentFileName)  # type: str
		targetFilePath = os.path.join(targetDirectoryPath, currentFileName)  # type: str

		if os.path.isfile(currentFilePath):
			if os.path.exists(targetFilePath):
				os.remove(targetFilePath)

			os.rename(currentFilePath, targetFilePath)
		else:
			_MoveDirectory(currentFilePath, targetFilePath)

	os.utime(targetDirectoryPath, (currentDirectoryAccessedTime, currentDirectoryModifiedTime))
	FileSystem.CloseDirectory(currentDirectoryPath, ignoreErrors = True)

def _ShowLoadFailureDialog () -> None:
	notificationArguments = {
		"title": FailureNotificationsTitle.GetCallableLocalizationString(),
		"text": FailureNotificationsLoadText.GetCallableLocalizationString(),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}  # type: typing.Dict[str, typing.Any]

	Notifications.ShowNotification(queue = True, **notificationArguments)

def _ShowSaveFailureDialog () -> None:
	notificationArguments = {
		"title": FailureNotificationsTitle.GetCallableLocalizationString(),
		"text": FailureNotificationsSaveText.GetCallableLocalizationString(),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}  # type: typing.Dict[str, typing.Any]

	Notifications.ShowNotification(queue = True, **notificationArguments)

def _ShowCommitFailureDialog () -> None:
	notificationArguments = {
		"title": FailureNotificationsTitle.GetCallableLocalizationString(),
		"text": FailureNotificationsCommitText.GetCallableLocalizationString(),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}  # type: typing.Dict[str, typing.Any]

	Notifications.ShowNotification(queue = True, **notificationArguments)

def _ShowModLoadFailureDialog (savingIdentifiers: typing.List[str]) -> None:
	identifiersText = "\n".join(savingIdentifiers)

	notificationArguments = {
		"title": FailureNotificationsTitle.GetCallableLocalizationString(),
		"text": FailureNotificationsModLoadText.GetCallableLocalizationString(identifiersText),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}  # type: typing.Dict[str, typing.Any]

	Notifications.ShowNotification(queue = True, **notificationArguments)

def _ShowModSaveFailureDialog (savingIdentifiers: typing.List[str]) -> None:
	identifiersText = "\n".join(savingIdentifiers)

	notificationArguments = {
		"title": FailureNotificationsTitle.GetCallableLocalizationString(),
		"text": FailureNotificationsModSaveText.GetCallableLocalizationString(identifiersText),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}  # type: typing.Dict[str, typing.Any]

	Notifications.ShowNotification(queue = True, **notificationArguments)

def _ShowModUnloadFailureDialog (savingIdentifiers: typing.List[str]) -> None:
	identifiersText = "\n".join(savingIdentifiers)

	notificationArguments = {
		"title": FailureNotificationsTitle.GetCallableLocalizationString(),
		"text": FailureNotificationsModUnloadText.GetCallableLocalizationString(identifiersText),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}  # type: typing.Dict[str, typing.Any]

	Notifications.ShowNotification(queue = True, **notificationArguments)

def _ShowMismatchGUIDWarningDialog (savingIdentifiers: typing.List[str]) -> None:
	identifiersText = "\n".join(savingIdentifiers)

	notificationArguments = {
		"title": WarningNotificationsTitle.GetCallableLocalizationString(),
		"text": WarningNotificationsMismatchGUIDText.GetCallableLocalizationString(identifiersText),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}  # type: typing.Dict[str, typing.Any]

	Notifications.ShowNotification(queue = True, **notificationArguments)

def _ShowMismatchGameTickWarningDialog (savingIdentifiers: typing.List[str]) -> None:
	identifiersText = "\n".join(savingIdentifiers)

	notificationArguments = {
		"title": WarningNotificationsTitle.GetCallableLocalizationString(),
		"text": WarningNotificationsMismatchGameTickText.GetCallableLocalizationString(identifiersText),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}  # type: typing.Dict[str, typing.Any]

	Notifications.ShowNotification(queue = True, **notificationArguments)
