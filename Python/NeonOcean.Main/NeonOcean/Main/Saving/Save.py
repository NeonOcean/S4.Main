import copy
import datetime
import json
import os
import shutil
import time
import typing

import services
from NeonOcean.Main import Debug, Events, Mods, Paths, S4
from NeonOcean.Main.Saving import SaveHandler, Shared
from NeonOcean.Main.Tools import Exceptions, FileSystem

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

class Save(Shared.SaveBase):
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

		self._host = host  # type: Mods.Mod
		self._identifier = identifier  # type: str

		self._loaded = False  # type: bool

		self._sourceSlotID = None  # type: typing.Optional[int]
		self._activeSlotId = None  # type: typing.Optional[int]

		self._saveData = dict()  # type: typing.Dict[str, typing.Any]
		self._saveSectionsData = dict()  # type: typing.Dict[str, typing.Any]

		super().__init__()

		Events.RegisterOnModUnload(self._OnHostUnload)
		self.RegisterSavingObject()

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
	def SourceSlotID (self) -> typing.Optional[int]:
		"""
		The slot idd that the loaded data was first taken from or last committed to. This will be None if no data is loaded.
		"""

		return self._sourceSlotID

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
		The namespace of the host that the loaded save was written by, None will be returned if no data is loaded, the data does not have this attribute or the data
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
		The version of the host that the loaded save was written by, None will be returned if no data is loaded, the data does not have this attribute or the data
		is invalid.
		"""

		if not self.Loaded:
			return None

		dataHostVersion = self._saveData.get("HostVersion", None)

		if not isinstance(dataHostVersion, str):
			return None

		return dataHostVersion

	@property
	def DataS4Version (self) -> typing.Optional[str]:
		"""
		The version of the game from which the loaded save was written, None will be returned if no data is loaded, the data does not have this attribute or the data
		is invalid.
		"""

		if not self.Loaded:
			return None

		dataS4Version = self._saveData.get("S4Version", None)

		if not isinstance(dataS4Version, str):
			return None

		return dataS4Version

	@property
	def DataWriteTime (self) -> typing.Optional[str]:
		"""
		The version of the game from which the loaded save was written, None will be returned if no data is loaded, the data does not have this attribute or the data
		is invalid.
		"""

		if not self.Loaded:
			return None

		dataWriteTime = self._saveData.get("WriteTime", None)

		if not isinstance(dataWriteTime, str):
			return None

		return dataWriteTime

	def RegisterSavingObject (self) -> None:
		"""
		Register this saving object to a list where it can be handled.
		:return:
		"""

		SaveHandler.SaveHandler.RegisterSavingObject(self)

	def UnregisterSavingObject (self) -> None:
		"""
		Unregister this saving object from its handling list.
		:return:
		"""

		SaveHandler.SaveHandler.UnregisterSavingObject(self)

	def Load (self, loadSlotID: int) -> bool:
		"""
		Load the saved data file specified by the slot id. If any data is already loaded, it will be unloaded first.

		:param loadSlotID: The save slot id of the game's loaded save file.
		:type loadSlotID: int
		:return: This method will return False if an error occurred. Otherwise this method will return True if it behaved as expected.
		:rtype: bool
		"""

		if not isinstance(loadSlotID, int):
			raise Exceptions.IncorrectTypeException(loadSlotID, "loadSlotID", (int,))

		operationInformation = "Save Identifier: %s | Source Slot ID: %s | Target Slot ID: %s" % (self.Identifier, str(self.SourceSlotID), str(loadSlotID))
		operationStartTime = time.time()  # type: float

		Debug.Log("Load operation starting in a saving object.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)

		if not self.Enabled:
			Debug.Log("Triggered load operation in a disabled saving object.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)

		if self.Loaded:
			self.Unload()

		try:
			loadSuccessful = self._LoadInternal(loadSlotID)
		except Exception:
			operationTime = time.time() - operationStartTime  # type: float
			Debug.Log("Load operation in a saving object aborted, falling back to the default. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)
			self.LoadDefault(loadSlotID)
			return False

		operationTime = time.time() - operationStartTime  # type: float

		if loadSuccessful:
			Debug.Log("Load operation in a saving object finished without issue. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)
		else:
			Debug.Log("Load operation in a saving object at least partially failed. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)

		return loadSuccessful

	def LoadDefault (self, loadSlotID: int) -> None:
		"""
		Load the saving object as default. The sections will not be notified as they are expected to already have default values when nothing is
		loaded. If any data is already loaded it will be unloaded first.

		:param loadSlotID: The save slot id of the game's loaded save file.
		:type loadSlotID: int
		"""

		if not isinstance(loadSlotID, int):
			raise Exceptions.IncorrectTypeException(loadSlotID, "slotID", (int,))

		operationInformation = "Save Identifier: %s | Target Slot ID: %s" % (self.Identifier, str(loadSlotID))
		operationStartTime = time.time()  # type: float

		Debug.Log("Load default operation starting in a saving object.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)

		if not self.Enabled:
			Debug.Log("Triggered load default operation in a disabled saving object.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)

		if self.Loaded:
			self.Unload()

		if self._sourceSlotID is None:
			self._sourceSlotID = loadSlotID

		self._loaded = True

		operationTime = time.time() - operationStartTime  # type: float
		Debug.Log("Load default operation in a saving object finished without issue. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)

	def Save (self, saveSlotID: int, commitSave: bool = False) -> bool:
		"""
		Write the loaded data to the active save file.

		This saving object must have save data loaded or this method will raise an exception.

		:param saveSlotID: The save slot id this operation is suppose to write to.
		:type saveSlotID: int
		:param commitSave: Whether or not the save should be committed as a permanent save file.
		:type commitSave: bool
		:return: This method will return False if an error in saving any section occurred. Otherwise this method will return True if it behaved as expected.
		:rtype: bool
		"""

		if not isinstance(saveSlotID, int):
			raise Exceptions.IncorrectTypeException(saveSlotID, "saveSlotID", (int,))

		operationInformation = "Save Identifier: %s | Source Slot ID: %s | Target Slot ID: %s" % (self.Identifier, str(self.SourceSlotID), str(saveSlotID))
		operationStartTime = time.time()  # type: float

		Debug.Log("Save operation starting in a saving object.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)

		if not self.Enabled:
			Debug.Log("Triggered save operation in a disabled saving object.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)

		try:
			saveSuccessful = self._SaveInternal(saveSlotID, commitSave = commitSave)
		except:
			operationTime = time.time() - operationStartTime  # type: float
			Debug.Log("Save operation in a saving object aborted. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)
			return False

		operationTime = time.time() - operationStartTime  # type: float

		if saveSuccessful:
			Debug.Log("Save operation in a saving object finished without issue. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)
		else:
			Debug.Log("Save operation in a saving object at least partially failed. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)

		return saveSuccessful

	def Commit (self, activeFilePath: str, commitSlotID: int) -> bool:
		"""
		Commit an active save file to become a permanent save, this should typically occur when the game does the same. If the source save file does not exist, nothing
		will happen.
		
		:param activeFilePath: The path of the active file that will be copied to the permanent save.
		:type activeFilePath: str
		:param commitSlotID: The save slot id the commit is suppose to be saved to.
		:type commitSlotID: int
		:return: This method will return False if an error in saving any section occurred. Otherwise this method will return True if it behaved as expected.
		:rtype: bool
		"""

		if not isinstance(activeFilePath, str):
			raise Exceptions.IncorrectTypeException(activeFilePath, "activeFilePath", (str,))

		if not isinstance(commitSlotID, int):
			raise Exceptions.IncorrectTypeException(commitSlotID, "commitSlotID", (int, "None"))

		operationInformation = "Save Identifier: %s | Source Slot ID: %s | Target Slot ID: %s" % (self.Identifier, str(self.SourceSlotID), str(commitSlotID))
		operationStartTime = time.time()  # type: float

		Debug.Log("Commit active save operation starting in a saving object.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)

		if not self.Enabled:
			Debug.Log("Triggered commit active save operation in a disabled saving object.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)

		self.ShiftBackupFiles(commitSlotID)

		commitSaveFilePath = self.GetSaveFilePath(commitSlotID)  # type: str
		commitSaveFileDirectoryPath = os.path.dirname(commitSaveFilePath)  # type: str

		if not os.path.exists(activeFilePath):
			operationTime = time.time() - operationStartTime  # type: float
			Debug.Log("Commit active save operation aborted because the target active file does not exists. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)
			return False

		if not os.path.exists(commitSaveFileDirectoryPath):
			os.makedirs(commitSaveFileDirectoryPath)

		shutil.copy(activeFilePath, commitSaveFilePath)

		operationTime = time.time() - operationStartTime  # type: float
		Debug.Log("Commit active save operation in a saving object finished without issue. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)

		return True

	def Unload (self) -> None:
		"""
		Unload any save data stored in this object and notify any attached sections to reset.
		"""

		if not self.Loaded:
			return

		operationInformation = "Save Identifier: %s | Source Slot ID: %s" % (self.Identifier, self.SourceSlotID)
		operationStartTime = time.time()  # type: float

		Debug.Log("Unload operation starting in a saving object.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)

		for sectionHandler in self.Sections:  # type: Shared.SectionBase
			sectionHandler.Reset()

		self._saveData = dict()
		self._saveSectionsData = dict()

		self._loaded = False

		operationTime = time.time() - operationStartTime  # type: float
		Debug.Log("Unload operation in a saving object finished without issue. (Operation took " + str(operationTime) + " seconds)\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Info, group = self.Host.Namespace, owner = __name__)

	def UnloadCompletely (self) -> None:
		"""
		Unload this saving object completely. This should be called when you need the saving object to be ready to load a save in a different slot.
		"""

		if self.Loaded:
			self.Unload()

		self.DeactivateActiveSaveFile()

		self._sourceSlotID = None

	def ActivateSaveFile (self, slotID: int) -> None:
		"""
		Copy the specified permanent save file to its active file path, making the save file ready to be loaded. If a permanent save file with the specified
		slot id and GUID doesn't exist, nothing will be copied. If any save file is already active it will be deactivated before activating the new file.

		:param slotID: The slot id of the targeted save file.
		:type slotID: int
		:return:
		"""

		if not isinstance(slotID, int):
			raise Exceptions.IncorrectTypeException(slotID, "slotID", (int,))

		self.DeactivateActiveSaveFile()

		saveFilePath = self.GetSaveFilePath(slotID)  # type: str
		saveActiveFilePath = self.GetSaveActiveFilePath(slotID)  # type: str
		saveActiveDirectoryPath = os.path.dirname(saveActiveFilePath)  # type: str

		if not os.path.exists(saveFilePath):
			return

		if not os.path.exists(saveActiveDirectoryPath):
			os.makedirs(saveActiveDirectoryPath)

		shutil.copy(saveFilePath, saveActiveFilePath)

		self._activeSlotId = slotID

	def DeactivateActiveSaveFile (self) -> None:
		"""
		Deactivate the currently active save file. Nothing will happen if no save file is active.
		:return:
		"""

		activeSlotID = self._activeSlotId  # type: typing.Optional[int]

		if activeSlotID is not None:
			saveActiveFilePath = self.GetSaveActiveFilePath(activeSlotID)  # type: str

			if os.path.exists(saveActiveFilePath):
				os.remove(saveActiveFilePath)

			FileSystem.CloseDirectory(os.path.dirname(saveActiveFilePath))

		self._activeSlotId = None

	def ShiftBackupFiles (self, slotID: int) -> None:
		"""
		Shift the specified backup files to follow the game's save backups. After this is called, the most recent save file will have been either moved to the backup
		or deleted. If the maximum amount of backup save files exist the oldest backup will be deleted.

		This saving object must have save data loaded or this method will raise an exception.
		:param slotID: The slot id of the targeted save file.
		:type slotID: int
		"""

		if not isinstance(slotID, int):
			raise Exceptions.IncorrectTypeException(slotID, "slotID", (int,))

		self.VerifyBackupFiles(slotID)

		if self.MaximumBackups <= 0:
			saveFilePath = self.GetSaveFilePath(slotID)  # type: str

			if os.path.exists(saveFilePath):
				os.remove(saveFilePath)

			return

		for backupIndex in reversed(range(self.MaximumBackups)):  # type: int
			currentBackupFilePath = self.GetSaveBackupFilePath(slotID, backupIndex)  # type: str

			if not os.path.exists(currentBackupFilePath):
				continue

			if backupIndex == self.MaximumBackups - 1:
				os.remove(currentBackupFilePath)
				continue

			nextBackupFilePath = self.GetSaveBackupFilePath(slotID, backupIndex + 1)  # type: str
			nextBackupDirectoryPath = os.path.dirname(nextBackupFilePath)  # type: str

			if os.path.exists(nextBackupFilePath):
				os.remove(nextBackupFilePath)

			if not os.path.exists(nextBackupDirectoryPath):
				os.makedirs(nextBackupDirectoryPath)

			os.rename(currentBackupFilePath, nextBackupFilePath)

		saveFilePath = self.GetSaveFilePath(slotID)  # type: str

		if os.path.exists(saveFilePath):
			firstBackupFilePath = self.GetSaveBackupFilePath(slotID, 0)  # type: str
			firstBackupDirectoryPath = os.path.dirname(firstBackupFilePath)  # type: str

			assert not os.path.exists(firstBackupFilePath)

			if not os.path.exists(firstBackupDirectoryPath):
				os.makedirs(firstBackupDirectoryPath)

			os.rename(saveFilePath, firstBackupFilePath)

		for backupIndex in reversed(range(self.MaximumBackups)):  # type: int
			currentBackupDirectoryPath = self.GetSaveBackupDirectoryPath(slotID, backupIndex)  # type: str
			FileSystem.CloseDirectory(currentBackupDirectoryPath)

		saveDirectoryPath = os.path.dirname(saveFilePath)  # type: str
		FileSystem.CloseDirectory(saveDirectoryPath)

	def VerifyBackupFiles (self, slotID: int) -> None:
		"""
		Verify that all existing backups have an attached game backup file that still exists. If the game backup save doesn't exist the corresponding backup
		will be deleted.

		This saving object must have save data loaded or this method will raise an exception.
		:param slotID: The slot id of the targeted save file.
		:type slotID: int
		"""

		if not isinstance(slotID, int):
			raise Exceptions.IncorrectTypeException(slotID, "slotID", (int,))

		for backupIndex in range(self.MaximumBackups):  # type: int
			gameBackupFilePath = self.GetGameSaveBackupFilePath(slotID, backupIndex)  # type: str
			backupFilePath = self.GetSaveBackupFilePath(slotID, backupIndex)  # type: str
			backupDirectoryPath = os.path.dirname(backupFilePath)  # type: str

			if not os.path.exists(gameBackupFilePath) and os.path.exists(backupFilePath):
				os.remove(backupFilePath)
				FileSystem.CloseDirectory(backupDirectoryPath)

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

	def GetGameSaveFilePath (self, slotID: int) -> str:
		gameSaveFileName = self.GetGameSaveFileName(slotID)
		return os.path.join(Paths.SavesPath, gameSaveFileName)

	def GetGameSaveBackupFilePath (self, slotID: int, backupIndex: int) -> str:
		gameSaveBackupFileName = self.GetGameSaveFileName(slotID) + ".ver" + str(backupIndex)
		return os.path.join(Paths.SavesPath, gameSaveBackupFileName)

	def GetGameSaveFileName (self, slotID: int) -> str:
		return "Slot_" + self.GetSlotIDString(slotID) + ".save"

	def GetSaveDirectoryPath (self, slotID: int) -> str:
		saveDirectoryName = self.GetSaveDirectoryName(slotID)  # type: str
		return os.path.join(Paths.SavesPath, saveDirectoryName)

	def GetSaveActiveDirectoryPath (self, slotID: int) -> str:
		saveActiveDirectoryName = self.GetSaveActiveDirectoryName(slotID)  # type: str
		return os.path.join(Paths.SavesPath, saveActiveDirectoryName)

	def GetSaveBackupDirectoryPath (self, slotID: int, backupIndex: int) -> str:
		saveDirectoryName = self.GetSaveBackupDirectoryName(slotID, backupIndex)  # type: str
		return os.path.join(Paths.SavesPath, saveDirectoryName)

	def GetSaveDirectoryName (self, slotID: int) -> str:
		return "Slot_" + self.GetSlotIDString(slotID) + "_NO"

	def GetSaveActiveDirectoryName (self, slotID: int) -> str:
		return self.GetSaveDirectoryName(slotID) + "_Active"

	def GetSaveBackupDirectoryName (self, slotID: int, backupIndex: int) -> str:
		return "Slot_" + self.GetSlotIDString(slotID) + "_NO.ver" + str(backupIndex)

	def GetSaveFilePath (self, slotID: int) -> str:
		saveFileName = self.GetSaveFileName()  # type: str
		saveDirectoryPath = self.GetSaveDirectoryPath(slotID)  # type: str
		return os.path.join(saveDirectoryPath, saveFileName)

	def GetSaveActiveFilePath (self, slotID: int) -> str:
		saveFileName = self.GetSaveFileName()
		saveActiveDirectoryPath = self.GetSaveActiveDirectoryPath(slotID)  # type: str
		return os.path.join(saveActiveDirectoryPath, saveFileName)

	def GetSaveBackupFilePath (self, slotID: int, backupIndex: int) -> str:
		saveFileName = self.GetSaveFileName()  # type: str
		saveDirectoryPath = self.GetSaveBackupDirectoryPath(slotID, backupIndex)  # type: str
		return os.path.join(saveDirectoryPath, saveFileName)

	def GetSaveFileName (self) -> str:
		return self.Identifier + ".json"  # type: str

	@staticmethod
	def GetSlotIDString (slotID: int) -> str:
		if not isinstance(slotID, int):
			raise Exceptions.IncorrectTypeException(slotID, "slotID", (int,))

		if slotID < 0:
			raise ValueError("Slot id cannot be less than zero.")

		slotIDHex = "{:x}".format(slotID)  # type: str
		return ("0" * (8 - len(slotIDHex))) + slotIDHex

	def _LoadInternal (self, loadSlotID: int) -> bool:
		if loadSlotID != self._activeSlotId:
			self.ActivateSaveFile(loadSlotID)

		saveFilePath = self.GetSaveActiveFilePath(loadSlotID)

		if not os.path.exists(saveFilePath):
			self.LoadDefault(loadSlotID)
			return True

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

		return self._LoadSetValue(loadSlotID, saveData)

	def _LoadSetValue (self, loadSlotID: int, saveData: dict) -> bool:
		operationInformation = "Save Identifier: %s | Target Slot ID: %s" % (self.Identifier, str(loadSlotID))
		operationSuccess = True  # type: bool

		saveSectionsData = saveData.get("Sections")

		if not isinstance(saveSectionsData, dict):
			raise Exceptions.IncorrectTypeException(saveSectionsData, "Root[Sections]", (dict,), "The sections value for the save file is not a dictionary.")

		if self._sourceSlotID is None:
			self._sourceSlotID = loadSlotID

		self._loaded = True

		self._saveData = saveData
		self._saveSectionsData = saveSectionsData

		for sectionHandler in self.Sections:  # type: Shared.SectionBase
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
			Debug.Log("The loaded data's GUID '" + str(saveDataGUID) + "' does not match the game's save GUID '" + str(gameSaveGUID) + "'\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Warning, group = self.Host.Namespace, owner = __name__)

		return operationSuccess

	def _SaveInternal (self, saveSlotID: int, commitSave: bool = False) -> bool:
		success, saveData = self._SaveGetData(saveSlotID)  # type: bool, dict

		try:
			saveDataString = json.JSONEncoder(indent = "\t", sort_keys = True).encode(saveData)  # type: str
		except Exception as e:
			raise Exception("Failed to encode save data with Python's json encoder.") from e

		if self._activeSlotId != saveSlotID:
			self.DeactivateActiveSaveFile()

		self._activeSlotId = saveSlotID

		saveFilePath = self.GetSaveActiveFilePath(saveSlotID)  # type: str
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

		if commitSave:
			commitSuccessful = self.Commit(saveFilePath, saveSlotID)  # type: bool
			self._sourceSlotID = saveSlotID

			if not commitSuccessful:
				return False

		return success

	def _SaveGetData (self, saveSlotID: int) -> typing.Tuple[bool, dict]:
		operationInformation = "Save Identifier: %s | Source Slot ID: %s | Target Slot ID: %s" % (self.Identifier, str(self.SourceSlotID), str(saveSlotID))
		operationSuccess = True  # type: bool

		sectionsSaveData = dict()  # type: typing.Dict[str, typing.Any]

		for sectionHandler in self.Sections:  # type: Shared.SectionBase
			try:
				sectionSuccess, sectionsSaveData[sectionHandler.Identifier] = sectionHandler.Save()  # type: bool

				if not sectionSuccess:
					operationSuccess = False
			except Exception:
				Debug.Log("Failed to get section data for the section '" + sectionHandler.Identifier + "'.\n" + operationInformation, self.Host.Namespace, Debug.LogLevels.Exception, group = self.Host.Namespace, owner = __name__)
				operationSuccess = False
				continue

		saveData = {
			"GUID": services.get_persistence_service().get_save_slot_proto_guid(),
			"HostNamespace": self.Host.Namespace,
			"HostVersion": str(self.Host.Version),
			"S4Version": str(S4.GameVersion),
			"WriteTime": datetime.datetime.now().isoformat(),
			"Sections": sectionsSaveData
		}

		return operationSuccess, saveData

	# noinspection PyUnusedLocal
	def _OnHostUnload (self, mod: Mods.Mod, exiting: bool) -> None:
		if self.Loaded:
			self.Unload()
