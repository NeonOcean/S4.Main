from __future__ import annotations

import copy
import json
import os
import time
import typing

import services
from NeonOcean.S4.Main import Debug, Mods, Paths, S4, Saving
from NeonOcean.S4.Main.Tools import Exceptions

"""
Game Systems Notes

Save GUID notes:
Save GUIDs are random numbers given to save files, they seem to be unique to each save and its lineage. The value is given to a save when it is first created and will 
follow it around forever, even if it is saved to a different slot.

Save backup notes:
The game's save backup files will always shift up a number even if there is no backup file poised to take its place. Backup files with the extension '.save.ver4' will
be deleted upon the next time the slot is saved to. There can be as many as 5 backup files and the first backup file will have the extension '.save.ver0'.
When overriding a save, if the a save file already exists in that slot, and the GUID of the new save is different from the existing one, the game will write the save
twice, this will create an extra backup.

The information above has not been tested to be true for Mac computers.
"""

class Save(Saving.SaveBase):
	MaximumBackups = 5  # type: int

	def __init__ (self, host: Mods.Mod, identifier: str):
		"""
		:param host: The host mod of this saving object. Debug logs made by this saving object will have the host's namespace attached.
		:type host: Mods.Mod
		:param identifier: This save object's identifier. This value is used the name the files that the data is saved and loaded to, this needs to be unique.
		:type identifier: str
		"""

		if not isinstance(host, Mods.Mod):
			raise Exceptions.IncorrectTypeException(host, "host", (Mods.Mod,))

		if not isinstance(identifier, str):
			raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

		super().__init__()

		self._host = host  # type: Mods.Mod
		self._identifier = identifier  # type: str

		self._loaded = False  # type: bool

		self._loadedDefault = None  # type: typing.Optional[bool]
		self._loadedFileExisted = None  # type: typing.Optional[bool]
		self._currentFilePath = None  # type: typing.Optional[str]

		self._sourceSlotID = None  # type: typing.Optional[int]

		self._saveData = dict()  # type: typing.Dict[str, typing.Any]
		self._saveSectionsData = dict()  # type: typing.Dict[str, typing.Any]

	@property
	def Host (self) -> Mods.Mod:
		return self._host

	@property
	def Identifier (self) -> str:
		return self._identifier

	@property
	def Enabled (self) -> bool:
		"""
		Whether or not this saving object should be loaded or saved.
		"""

		return self.Host.IsLoaded()

	@property
	def Loaded (self) -> bool:
		return self._loaded

	@property
	def LoadedDefault (self) -> typing.Optional[bool]:
		"""
		Whether or not this saving object has fallen back to the default when loading. This would be false if the file didn't exist or wasn't loadable.
		This value will be none if no data is loaded.
		"""

		return self._loadedDefault

	@property
	def LoadedFileExisted (self) -> typing.Optional[bool]:
		"""
		Whether or not this saving object's loaded file actually existed when it told to load it.
		This value will be none if no data is loaded or the load default method was used directly.
		"""

		return self._loadedFileExisted

	@property
	def CurrentFilePath (self) -> typing.Optional[str]:
		"""
		The file that this saving object last loaded from or saved to.
		This value will be none if no data is loaded.
		"""

		return self._currentFilePath

	@property
	def DataGUID (self) -> typing.Optional[int]:
		"""
		The game's save GUID from when the loaded data was saved. None will be returned if no data is loaded, the data does not have this attribute or the data is invalid.
		"""

		if not self.Loaded:
			return None

		dataGUID = self._saveData.get("GUID", None)

		if not isinstance(dataGUID, int):
			return None

		return dataGUID

	@property
	def DataHostNamespace (self) -> typing.Optional[str]:
		"""
		The namespace of the host that the loaded save was written by. None will be returned if no data is loaded, the data does not have this attribute or the data
		is invalid.
		"""

		if not self.Loaded:
			return None

		dataHostNamespace = self._saveData.get("HostNamespace", None)

		if not isinstance(dataHostNamespace, str):
			return None

		return dataHostNamespace

	@property
	def DataHostVersion (self) -> typing.Optional[str]:
		"""
		The version of the host that the loaded save was written by. None will be returned if no data is loaded, the data does not have this attribute or the data
		is invalid.
		"""

		if not self.Loaded:
			return None

		dataHostVersion = self._saveData.get("HostVersion", None)

		if not isinstance(dataHostVersion, str):
			return None

		return dataHostVersion

	@property
	def DataGameVersion (self) -> typing.Optional[str]:
		"""
		The version of the game from which the loaded save was written. None will be returned if no data is loaded, the data does not have this attribute or the data
		is invalid.
		"""

		if not self.Loaded:
			return None

		dataGameVersion = self._saveData.get("GameVersion", None)

		if not isinstance(dataGameVersion, str):
			return None

		return dataGameVersion

	@property
	def DataGameTick (self) -> typing.Optional[int]:
		"""
		The game tick the loaded data was saved on. None will be returned if no data is loaded, the data does not have this attribute or the data is invalid.
		"""

		if not self.Loaded:
			return None

		dataGameTick = self._saveData.get("GameTick", None)

		if not isinstance(dataGameTick, int):
			return None

		return dataGameTick

	def Load (self, saveFilePath: str) -> bool:
		"""
		Load a save file. If any data is already loaded it will be unloaded first.

		:param saveFilePath: The path of the save file to be loaded. If this doesn't exist the method 'LoadDefault' will be used instead.
		:type saveFilePath: str
		:return: This method will return False if an error occurred. Otherwise this method will return True if it behaved as expected.
		:rtype: bool
		"""

		if not isinstance(saveFilePath, str):
			raise Exceptions.IncorrectTypeException(saveFilePath, "saveFilePath", (str,))

		operationInformation = "Save Identifier: %s" % (self.Identifier,)
		operationStartTime = time.time()  # type: float

		Debug.Log("Load operation starting in a saving object.\nTarget File: %s\n" % Paths.StripUserDataPath(saveFilePath) + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)

		if not self.Enabled:
			Debug.Log("Triggered load operation in a disabled saving object.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)

		if self.Loaded:
			self.Unload()

		if not os.path.exists(saveFilePath):
			self.LoadDefault()
			loadSuccessful = True

			self._loadedFileExisted = False
			self._currentFilePath = saveFilePath
		else:
			try:
				loadSuccessful = self._LoadInternal(saveFilePath)

				self._loadedFileExisted = True
				self._currentFilePath = saveFilePath

			except Exception:
				operationTime = time.time() - operationStartTime  # type: float
				Debug.Log("Load operation in a saving object aborted, falling back to the default. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)
				self.LoadDefault()

				self._loadedFileExisted = True
				self._currentFilePath = saveFilePath

				return False

		operationTime = time.time() - operationStartTime  # type: float

		if loadSuccessful:
			Debug.Log("Load operation in a saving object finished without issue. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)
		else:
			Debug.Log("Load operation in a saving object at least partially failed. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)

		return loadSuccessful

	def LoadDefault (self) -> None:
		"""
		Load the saving object as default. The sections will not be notified as they are expected to already have default values when nothing is loaded.
		If any data is already loaded it will be unloaded first.
		"""

		operationInformation = "Save Identifier: %s" % (self.Identifier,)
		operationStartTime = time.time()  # type: float

		Debug.Log("Load default operation starting in a saving object.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)

		if not self.Enabled:
			Debug.Log("Triggered load default operation in a disabled saving object.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)

		if self.Loaded:
			self.Unload()

		self._LoadDefaultInternal()

		self._loadedDefault = True

		operationTime = time.time() - operationStartTime  # type: float
		Debug.Log("Load default operation in a saving object finished without issue. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace,
				  owner = __name__)

	def Save (self, saveFilePath: str) -> bool:
		"""
		Write the loaded data to the active save file.

		This saving object must have save data loaded or this method will raise an exception.

		:param saveFilePath: The path to save the data to.
		:type saveFilePath: str
		:return: This method will return False if an error in saving any section occurred. Otherwise this method will return True if it behaved as expected.
		:rtype: bool
		"""

		if not isinstance(saveFilePath, str):
			raise Exceptions.IncorrectTypeException(saveFilePath, "saveFilePath", (str,))

		operationInformation = "Save Identifier: %s" % (self.Identifier,)
		operationStartTime = time.time()  # type: float

		Debug.Log("Save operation starting in a saving object.\nTarget File: %s\n" % Paths.StripUserDataPath(saveFilePath) + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)

		if not self.Enabled:
			Debug.Log("Triggered save operation in a disabled saving object.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)

		try:
			saveSuccessful = self._SaveInternal(saveFilePath)
			self._currentFilePath = saveFilePath
		except:
			self._currentFilePath = saveFilePath
			operationTime = time.time() - operationStartTime  # type: float
			Debug.Log("Save operation in a saving object aborted. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)
			return False

		operationTime = time.time() - operationStartTime  # type: float

		if saveSuccessful:
			Debug.Log("Save operation in a saving object finished without issue. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)
		else:
			Debug.Log("Save operation in a saving object at least partially failed. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)

		return saveSuccessful

	def Unload (self) -> None:
		"""
		Unload any save data stored in this object and notify any attached sections to reset.
		"""

		if not self.Loaded:
			return

		operationInformation = "Save Identifier: %s" % (self.Identifier,)
		operationStartTime = time.time()  # type: float

		Debug.Log("Unload operation starting in a saving object.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)

		for sectionHandler in self.Sections:  # type: Saving.SectionBase
			sectionHandler.Reset()

		self._saveData = dict()
		self._saveSectionsData = dict()

		self._loaded = False

		self._loadedDefault = None
		self._loadedFileExisted = None
		self._currentFilePath = None

		operationTime = time.time() - operationStartTime  # type: float
		Debug.Log("Unload operation in a saving object finished without issue. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)

	def GetSectionData (self, sectionIdentifier: str) -> typing.Optional[typing.Any]:
		"""
		Get the section data from the loaded save. Any returned data will not be verified by a section handler to be accurate, the value will also be deep copied before
		being passed on.

		:param sectionIdentifier: The section's identifier.
		:type sectionIdentifier: str
		:return: The section's data or None
		"""

		if not self.Loaded:
			return None

		sectionData = self._saveSectionsData.get(sectionIdentifier)

		if sectionData is None:
			return sectionData

		return copy.deepcopy(self._saveSectionsData.get(sectionIdentifier))

	def GetSaveFileName (self) -> str:
		"""
		Get the save file name for this saving object. This could be overridden to change the name, extension or to place the file in a subdirectory of the mod
		save folder.
		"""

		return self.Identifier + ".json"  # type: str

	def _LoadInternal (self, saveFilePath: str) -> bool:
		try:
			with open(saveFilePath) as saveFile:
				saveDataString = saveFile.read()
		except Exception as e:
			raise Exception("Failed to read the target save file's text.") from e

		try:
			saveData = json.JSONDecoder().decode(saveDataString)  # type: typing.Dict[str, typing.Any]
		except Exception as e:
			raise Exception("Failed to the target decode save data.") from e

		if not isinstance(saveData, dict):
			raise Exceptions.IncorrectTypeException(saveData, "Root", (dict,), "The save file's root is not a dictionary.")

		return self._LoadSetValue(saveData)

	def _LoadSetValue (self, saveData: dict) -> bool:
		operationInformation = "Save Identifier: %s" % (self.Identifier,)
		operationSuccess = True  # type: bool

		saveSectionsData = saveData.get("Sections")

		if not isinstance(saveSectionsData, dict):
			raise Exceptions.IncorrectTypeException(saveSectionsData, "Root[Sections]", (dict,), "The sections value for the save file is not a dictionary.")

		self._saveData = saveData
		self._saveSectionsData = saveSectionsData

		self._loaded = True

		for sectionHandler in self.Sections:  # type: Saving.SectionBase
			try:
				sectionData = self.GetSectionData(sectionHandler.Identifier)  # type: typing.Any

				if sectionData is None:
					continue

				sectionSuccess = sectionHandler.Load(sectionData)  # type: bool

				if not sectionSuccess:
					operationSuccess = False
			except Exception:
				Debug.Log("Failed to load data to a section helper with the identifier '" + sectionHandler.Identifier + "'\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)
				operationSuccess = False
				continue

		saveDataGUID = self.DataGUID  # type: typing.Optional[int]
		gameSaveGUID = services.get_persistence_service().get_save_slot_proto_guid()  # type: int

		if saveDataGUID is None or saveDataGUID != gameSaveGUID:
			Debug.Log("The loaded data's GUID '" + str(saveDataGUID) + "' does not match the game's saved GUID '" + str(gameSaveGUID) + "'\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)

		saveDataGameTick = self.DataGameTick  # type: typing.Optional[int]
		gameSaveGameTick = services.get_persistence_service().get_save_slot_proto_buff().gameplay_data.world_game_time  # type: int

		if saveDataGameTick is None or saveDataGameTick != gameSaveGameTick:
			Debug.Log("The loaded data's game tick '" + str(saveDataGameTick) + "' does not match the game's saved game tick '" + str(gameSaveGameTick) + "'\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)

		return operationSuccess

	def _LoadDefaultInternal (self) -> None:
		self._loaded = True

	def _SaveInternal (self, saveFilePath: str) -> bool:
		success, saveData = self._SaveGetData()  # type: bool, dict

		try:
			saveDataString = json.JSONEncoder(indent = "\t", sort_keys = True).encode(saveData)  # type: str
		except Exception as e:
			raise Exception("Failed to encode save data with Python's json encoder.") from e

		saveFileDirectoryPath = os.path.dirname(saveFilePath)  # type: str

		try:
			if not os.path.exists(saveFileDirectoryPath):
				os.makedirs(saveFileDirectoryPath)
		except Exception as e:
			raise Exception("Failed to create a save file's directory.") from e

		try:
			with open(saveFilePath, "w+") as saveFile:
				saveFile.write(saveDataString)
		except Exception as e:
			raise Exception("Failed to write the save data to the save file.") from e

		return success

	def _SaveGetData (self) -> typing.Tuple[bool, dict]:
		operationInformation = "Save Identifier: %s" % (self.Identifier,)
		operationSuccess = True  # type: bool

		sectionsSaveData = dict()  # type: typing.Dict[str, typing.Any]

		for sectionHandler in self.Sections:  # type: Saving.SectionBase
			try:
				sectionSuccess, sectionsSaveData[sectionHandler.Identifier] = sectionHandler.Save()  # type: bool

				if not sectionSuccess:
					operationSuccess = False
			except Exception:
				Debug.Log("Failed to get section data for the section '" + sectionHandler.Identifier + "'.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Exception, group = self.Host.Namespace, owner = __name__)
				operationSuccess = False
				continue

		gameplaySaveSlotData = services.get_persistence_service().get_save_slot_proto_buff().gameplay_data

		saveData = {
			"GUID": services.get_persistence_service().get_save_slot_proto_guid(),
			"HostNamespace": self.Host.Namespace,
			"HostVersion": str(self.Host.Version),
			"GameVersion": str(S4.GameVersion),
			"GameTick": gameplaySaveSlotData.world_game_time,
			"Sections": sectionsSaveData
		}

		return operationSuccess, saveData

def GetSlotIDString (slotID: int) -> str:
	if not isinstance(slotID, int):
		raise Exceptions.IncorrectTypeException(slotID, "slotID", (int,))

	if slotID < 0:
		raise ValueError("Slot id cannot be less than zero.")

	slotIDHex = "{:x}".format(slotID)  # type: str
	return ("0" * (8 - len(slotIDHex))) + slotIDHex

def GetGameSaveFilePath (slotID: int) -> str:
	if not isinstance(slotID, int):
		raise Exceptions.IncorrectTypeException(slotID, "slotID", (int,))

	return os.path.join(Paths.SavesPath, "Slot_" + GetSlotIDString(slotID) + ".save")

def GetGameSaveBackupFilePath (slotID: int, backupIndex: int) -> str:
	if not isinstance(slotID, int):
		raise Exceptions.IncorrectTypeException(slotID, "slotID", (int,))

	if not isinstance(backupIndex, int):
		raise Exceptions.IncorrectTypeException(backupIndex, "backupIndex", (int,))

	return os.path.join(Paths.SavesPath, "Slot_" + GetSlotIDString(slotID) + ".save.ver" + str(backupIndex))
