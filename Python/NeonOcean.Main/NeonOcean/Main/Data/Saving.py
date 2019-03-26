import collections
import json
import os
import shutil

import services
from NeonOcean.Main import Debug, Paths, This
from NeonOcean.Main.Tools import Exceptions, Types

def GetSlotIDString (slotID: int) -> str:
	if not isinstance(slotID, int):
		raise Exceptions.IncorrectTypeException(slotID, "slotID", (int,))

	if slotID < 0:
		raise ValueError("Slot id cannot be less than zero.")

	digits = len(str(slotID))  # type: int
	return ("0" * (8 - digits)) + str(slotID)

def _BackupSave (saveFilePath: str) -> None:
	if os.path.exists(saveFilePath):
		saveFileBackup0Path = saveFilePath + ".ver0"  # type: str

		if os.path.exists(saveFileBackup0Path):
			saveFileBackup1Path = saveFilePath + ".ver1"  # type: str

			if os.path.exists(saveFileBackup1Path):
				try:
					shutil.rmtree(saveFileBackup1Path)
				except:
					pass  # todo log / handle

			try:
				shutil.move(saveFileBackup0Path, saveFileBackup1Path)
			except:
				pass  # todo log / handle

		try:
			shutil.move(saveFilePath, saveFileBackup0Path)
		except:
			pass  # todo log / handle

class Saving:
	def __init__ (self, fileName: str):
		if not isinstance(fileName, str):
			raise Exceptions.IncorrectTypeException(fileName, "fileName", (str,))

		self.FileName = fileName

		self._file = dict()
		self._loadCallbacks = dict()
		self._saveCallbacks = dict()

	def Load (self):
		saveSlotID = services.get_persistence_service().get_save_slot_proto_buff().slot_id  # type: int
		saveGUID = services.get_persistence_service().get_save_slot_proto_guid()  # type: int
		saveFilePath = Paths.SavesPath + "Slot_" + GetSlotIDString(saveSlotID) + "_(" + str(saveGUID) + ")_" + self.FileName + ".json"  # type: str

		try:
			with open(saveFilePath, mode = "r") as saveFile:
				saveFileData = json.JSONDecoder().decode(saveFile.read())  # type: dict #todo check format

			if not isinstance(saveFileData, dict):
				raise TypeError("Cannot convert file to dictionary.")
		except Exception as e:
			Debug.Log("Failed to read '" + Paths.StripUserDataPath(saveFilePath) + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
			saveFileData = dict()

		for section in list(saveFileData.keys()):  # type: str
			saveFileData.pop(section, None)  # todo fix changing size while iterating
			Debug.Log("Section keys must be '" + Types.GetFullName(str) + "' not '" + Types.GetFullName(section) + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

		self._file = saveFileData

		for section, callback in self._loadCallbacks.items():  # type: str, collections.Callable
			sectionData = self._file.get(section)
			callback(sectionData)

	def Save (self):
		saveSlotID = services.get_persistence_service().get_save_slot_proto_buff().slot_id  # type: int
		saveGUID = services.get_persistence_service().get_save_slot_proto_guid()  # type: int
		saveFilePath = Paths.SavesPath + "Slot_" + GetSlotIDString(saveSlotID) + "_(" + str(saveGUID) + ")_" + self.FileName + ".json"  # type: str

		_BackupSave(saveFilePath)

		saveDictionary = dict()

		for section, callback in self._saveCallbacks.items():  # type: str, collections.Callable
			saveDictionary[section] = callback()

		with open(saveFilePath, mode = "w+") as saveFile:
			saveFile.write(json.JSONEncoder(indent = 4).encode(saveDictionary))

	def GetFileSection (self, section: str) -> None:
		pass

	def RegisterLoadCallback (self, section: str, callback: collections.Callable) -> None:
		if not isinstance(section, str):
			raise Exceptions.IncorrectTypeException(section, "section", (str,))

		if not isinstance(callback, collections.Callable):
			raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

		if section in self._loadCallbacks:
			raise Exception("Load callback for section '" + section + "' is already registered.")

		self._loadCallbacks[section] = callback

	def UnregisterLoadCallback (self, section: str) -> None:
		if not isinstance(section, str):
			raise Exceptions.IncorrectTypeException(section, "section", (str,))

		if section in self._loadCallbacks:
			self._loadCallbacks.pop(section)

	def RegisterSaveCallback (self, section: str, callback: collections.Callable) -> None:
		if not isinstance(section, str):
			raise Exceptions.IncorrectTypeException(section, "section", (str,))

		if not isinstance(callback, collections.Callable):
			raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

		if section in self._saveCallbacks:
			raise Exception("Save callback for section '" + section + "' is already registered.")

		self._saveCallbacks[section] = callback

	def UnregisterSaveCallback (self, section: str) -> None:
		if not isinstance(section, str):
			raise Exceptions.IncorrectTypeException(section, "section", (str,))

		if section in self._saveCallbacks:
			self._saveCallbacks.pop(section)
