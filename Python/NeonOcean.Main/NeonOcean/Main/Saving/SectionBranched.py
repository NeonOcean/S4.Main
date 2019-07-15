import typing
import copy
import json

from NeonOcean.Main import Debug
from NeonOcean.Main.Saving import Shared
from NeonOcean.Main.Tools import Exceptions, Types

class SectionBranched(Shared.SectionBase):
	def __init__ (self, identifier: str, savingObject: Shared.SaveAbstract):
		self._identifier = identifier  # type: str

		self._loadedData = dict()  # type: typing.Dict[str, typing.Dict[str, typing.Any]]

		self._loadCallbacks = list()  # type: typing.List[typing.Callable]
		self._saveCallbacks = list()  # type: typing.List[typing.Callable]
		self._resetCallbacks = list()  # type: typing.List[typing.Callable]

		super().__init__(savingObject)

	@property
	def Identifier (self) -> str:
		return self._identifier

	def Load (self, sectionData: dict) -> bool:
		operationInformation = "Save Identifier: %s | Section Identifier: %s | Source Slot ID: %s" % (self.SavingObject.Identifier, self.Identifier, str(self.SavingObject.SourceSlotID))
		operationSuccessful = True  # type: bool

		if not isinstance(sectionData, dict):
			Debug.Log("Incorrect type in section data.\n" + Exceptions.GetIncorrectTypeExceptionText(sectionData, "SectionData", (dict,)) + "\n" + operationInformation, self.SavingObject.Host.Namespace, Debug.LogLevels.Warning, group = self.SavingObject.Host.Namespace, owner = __name__)
			sectionData = dict()
			operationSuccessful = False

		for branchKey in list(sectionData.keys()):  # type: str, dict
			if not isinstance(branchKey, str):
				Debug.Log("Incorrect type in section data.\n" + Exceptions.GetIncorrectTypeExceptionText(sectionData, "SectionData<Key>", (str,)) + "\n" + operationInformation, self.SavingObject.Host.Namespace, Debug.LogLevels.Warning, group = self.SavingObject.Host.Namespace, owner = __name__)
				sectionData.pop(branchKey, None)
				operationSuccessful = False
				continue

			branchDictionary = sectionData[branchKey]  # type: dict

			if not isinstance(branchDictionary, dict):
				Debug.Log("Incorrect type in section data.\n" + Exceptions.GetIncorrectTypeExceptionText(sectionData, "SectionData[%s]" % branchKey, (str,)) + "\n" + operationInformation, self.SavingObject.Host.Namespace, Debug.LogLevels.Warning, group = self.SavingObject.Host.Namespace, owner = __name__)
				sectionData.pop(branchKey, None)
				operationSuccessful = False
				continue

			for valueKey in list(branchDictionary.keys()):  # type: str
				if not isinstance(valueKey, str):
					Debug.Log("Incorrect type in section data.\n" + Exceptions.GetIncorrectTypeExceptionText(sectionData, "SectionData[%s]<Key>" % branchKey, (str,)) + "\n" + operationInformation, self.SavingObject.Host.Namespace, Debug.LogLevels.Warning, group = self.SavingObject.Host.Namespace, owner = __name__)
					branchDictionary.pop(valueKey, None)
					operationSuccessful = False
					continue

		self._loadedData = sectionData

		callbackFailure = self._ActivateLoadCallbacks()  # type: bool

		if not callbackFailure:
			return False

		return operationSuccessful

	def Save (self) -> typing.Tuple[bool, dict]:
		callbackFailure = self._ActivateSaveCallbacks()  # type: bool
		return callbackFailure, self._loadedData

	def Reset (self) -> None:
		self._loadedData = dict()
		self._ActivateResetCallbacks()

	def GetValue (self, branch: str, key: str, default: typing.Any = None) -> typing.Any:
		"""
		Gets the value of the section data specified by the key and branch. The value returned will be a deep copy of what is stored, modifying it should never change
		anything unless you set it with the set function. The default value will not be copied if it is returned however, only the value in storage.

		:param branch: The name of the branch to get the value from.
		:type branch: str
		:param key: The name of the section data, is case sensitive.
		:type key: str
		:param default: The value returned if no value under the branch and key exists.
		:return: The value in storage or the default argument.
		"""

		if not branch in self._loadedData:
			return default

		if not key in self._loadedData[branch]:
			return default

		return copy.deepcopy(self._loadedData[branch][key])

	def GetAllValues (self, key: str) -> typing.Dict[str, typing.Any]:
		"""
		Gets a dictionary of every branch's value for the section data specified by the key. The value returned will be a deep copy of what is stored, modifying it
		should never change anything unless you set it with the set function.

		:param key: The name of the section data, is case sensitive.
		:type key: str
		"""

		allValues = dict()  # type: typing.Dict[str, typing.Any]

		for branchKey, branchDictionary in self._loadedData.items():  # type: str, dict
			if key in branchDictionary:
				allValues[branchKey] = copy.deepcopy(branchDictionary[key])

		return allValues

	def Set (self, branch: str, key: str, value) -> None:
		"""
		Set the value of the section data specified by the key and branch. The value is deep copied before being but into storage, modifying the value after setting
		it will not change the stored version. All values must be able to be encoded by python's json modules.

		:param branch: The name of the branch to set the value to.
		:type branch: str
		:param key: The name of the section data, is case sensitive.
		:type key: str
		:param value: The value the section data will be changing to. This must be able to be encoded by python's json modules.
		:rtype: None
		"""

		if not isinstance(branch, str):
			raise Exceptions.IncorrectTypeException(branch, "branch", (str,))

		if not isinstance(key, str):
			raise Exceptions.IncorrectTypeException(key, "key", (str,))

		copiedValue = copy.deepcopy(value)
		
		try:
			json.dumps(copiedValue)
		except Exception as e:
			raise Exception("Target value cannot be encoded. Branch: " + branch + " Key: " + key + ".") from e

		if not branch in self._loadedData:
			self._loadedData[branch] = dict()

		branchDictionary = self._loadedData[branch]  # type: dict
		assert isinstance(branchDictionary, dict)
		branchDictionary[key] = value

	def SetAllBranches (self, key: str, value) -> None:
		"""
		Set the value of the section data specified by the key in all branches. The value is deep copied before being but into storage, modifying the value after
		setting it will not change the stored version. All values must be able to be encoded by python's json modules.

		:param key: The name of the section data, is case sensitive.
		:type key: str
		:param value: The value the section data will be changing to. This must be able to be encoded by python's json modules.
		:rtype: None
		"""

		if not isinstance(key, str):
			raise Exceptions.IncorrectTypeException(key, "key", (str,))

		copiedValue = copy.deepcopy(value)

		try:
			json.dumps(copiedValue)
		except Exception as e:
			raise Exception("Target value cannot be encoded. Key: " + key + ".") from e

		for branchDictionary in self._loadedData.values():  # type: str, dict
			assert isinstance(branchDictionary, dict)
			branchDictionary[key] = copiedValue

	def RegisterLoadCallback (self, callback: typing.Callable) -> None:
		"""
		Register a callback to be called after the data has been loaded.
		:param callback: The callback should take a single argument, the section object, and return a boolean indicating whether or not it was completely successful.
		:type callback: typing.Callable
		"""

		if callback in self._loadCallbacks:
			return

		self._loadCallbacks.append(callback)

	def UnregisterLoadCallback (self, callback: typing.Callable) -> None:
		"""
		Unregister a load callback.
		"""

		if callback in self._loadCallbacks:
			self._loadCallbacks.remove(callback)

	def RegisterSaveCallback (self, callback: typing.Callable) -> None:
		"""
		Register a callback to be called before the data is sent off to be saved.
		:param callback: The callback should take a single argument, the section object, and return a boolean indicating whether or not it was completely successful.
		:type callback: typing.Callable
		"""

		if callback in self._saveCallbacks:
			return

		self._saveCallbacks.append(callback)

	def UnregisterSaveCallback (self, callback: typing.Callable) -> None:
		"""
		Unregister a save callback.
		"""

		if callback in self._saveCallbacks:
			self._saveCallbacks.remove(callback)

	def RegisterResetCallback (self, callback: typing.Callable) -> None:
		"""
		Register a callback to be called after the section is reset.
		:param callback: The callback should take a single argument, the section object, and return a boolean indicating whether or not it was completely successful.
		:type callback: typing.Callable
		"""

		if callback in self._resetCallbacks:
			return

		self._resetCallbacks.append(callback)

	def UnregisterResetCallback (self, callback: typing.Callable) -> None:
		"""
		Unregister a save callback.
		"""

		if callback in self._resetCallbacks:
			self._resetCallbacks.remove(callback)

	def _ActivateLoadCallbacks (self) -> bool:
		operationInformation = "Save Identifier: %s | Section Identifier: %s | Source Slot ID: %s" % (self.SavingObject.Identifier, self.Identifier, str(self.SavingObject.SourceSlotID))
		operationSuccessful = True  # type: bool

		for loadCallback in self._loadCallbacks:  # type: typing.Callable[[], Shared.SectionBase]
			try:
				callbackSuccess = loadCallback(self)  # type: bool

				if not callbackSuccess:
					operationSuccessful = False
			except:
				Debug.Log("Failed to activate load callback at '" + Types.GetFullName(loadCallback) + "'.\n" + operationInformation, self.SavingObject.Host.Namespace, Debug.LogLevels.Exception, group = self.SavingObject.Host.Namespace, owner = __name__)
				operationSuccessful = False

		return operationSuccessful

	def _ActivateSaveCallbacks (self) -> bool:
		operationInformation = "Save Identifier: %s | Section Identifier: %s | Source Slot ID: %s" % (self.SavingObject.Identifier, self.Identifier, str(self.SavingObject.SourceSlotID))
		operationSuccessful = True  # type: bool

		for saveCallback in self._saveCallbacks:  # type: typing.Callable[[], Shared.SectionBase]
			try:
				callbackSuccess = saveCallback(self)  # type: bool

				if not callbackSuccess:
					operationSuccessful = False
			except:
				Debug.Log("Failed to activate save callback at '" + Types.GetFullName(saveCallback) + "'.\n" + operationInformation, self.SavingObject.Host.Namespace, Debug.LogLevels.Exception, group = self.SavingObject.Host.Namespace, owner = __name__)
				operationSuccessful = False

		return operationSuccessful

	def _ActivateResetCallbacks (self) -> bool:
		operationInformation = "Save Identifier: %s | Section Identifier: %s | Source Slot ID: %s" % (self.SavingObject.Identifier, self.Identifier, str(self.SavingObject.SourceSlotID))
		operationSuccessful = True  # type: bool

		for resetCallback in self._resetCallbacks:  # type: typing.Callable[[], Shared.SectionBase]
			try:
				callbackSuccess = resetCallback(self)  # type: bool

				if not callbackSuccess:
					operationSuccessful = False
			except:
				Debug.Log("Failed to activate reset callback at '" + Types.GetFullName(resetCallback) + "'.\n" + operationInformation, self.SavingObject.Host.Namespace, Debug.LogLevels.Exception, group = self.SavingObject.Host.Namespace, owner = __name__)
				operationSuccessful = False

		return operationSuccessful
