from __future__ import annotations

import copy
import json
import typing

from NeonOcean.S4.Main import Debug, Saving
from NeonOcean.S4.Main.Tools import Exceptions, Types

class SectionStandard(Saving.SectionBase):
	def __init__ (self, identifier: str, savingObject: Saving.SaveAbstract):
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
		operationInformation = "Save Identifier: %s | Section Identifier: %s" % (self.SavingObject.Identifier, self.Identifier,)
		operationSuccessful = True  # type: bool

		if not isinstance(sectionData, dict):
			Debug.Log("Incorrect type in section data.\n" + Exceptions.GetIncorrectTypeExceptionText(sectionData, "SectionData", (dict,)) + "\n" + operationInformation, self.SavingObject.Host.Namespace, Debug.LogLevels.Warning, group = self.SavingObject.Host.Namespace, owner = __name__)
			sectionData = dict()
			operationSuccessful = False

		for valueKey in list(sectionData.keys()):  # type: str
			if not isinstance(valueKey, str):
				Debug.Log("Incorrect type in section data.\n" + Exceptions.GetIncorrectTypeExceptionText(sectionData, "SectionData<Key>", (str,)) + "\n" + operationInformation, self.SavingObject.Host.Namespace, Debug.LogLevels.Warning, group = self.SavingObject.Host.Namespace, owner = __name__)
				sectionData.pop(valueKey, None)
				operationSuccessful = False
				continue

		self._loadedData = sectionData

		callbackSuccessful = self._ActivateLoadCallbacks()  # type: bool

		if not callbackSuccessful:
			return False

		return operationSuccessful

	def Save (self) -> typing.Tuple[bool, dict]:
		callbackSuccessful = self._ActivateSaveCallbacks()  # type: bool
		return callbackSuccessful, self._loadedData

	def Reset (self) -> None:
		self._loadedData = dict()
		self._ActivateResetCallbacks()

	def GetValue (self, key: str, default: typing.Any = None) -> typing.Any:
		"""
		Gets the value of the section data specified by the key and branch. The value returned will be a deep copy of what is stored, modifying it should never change
		anything unless you set it with the set function. The default value will not be copied if it is returned however, only the value in storage.

		:param key: The name of the section data, is case sensitive.
		:type key: str
		:param default: The value returned if no value under the branch and key exists.
		:return: The value in storage or the default argument.
		"""

		if not isinstance(key, str):
			raise Exceptions.IncorrectTypeException(key, "key", (str,))

		if not key in self._loadedData:
			return default

		return copy.deepcopy(self._loadedData[key])

	def SetValue (self, key: str, value) -> None:
		"""
		Set the value of the section data specified by the key and branch. The value is deep copied before being but into storage, modifying the value after setting
		it will not change the stored version. All values must be able to be encoded by python's json modules.

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

		self._loadedData[key] = value

	def RegisterLoadCallback (self, callback: typing.Callable) -> None:
		"""
		Register a callback to be called after the data has been loaded.
		:param callback: The callback, this should take a single argument, the section object.
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
		:param callback: The callback, this should take a single argument, the section object.
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
		:param callback: The callback, this should take a single argument, the section object.
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
		operationInformation = "Save Identifier: %s | Section Identifier: %s" % (self.SavingObject.Identifier, self.Identifier,)
		operationSuccessful = True  # type: bool

		for loadCallback in self._loadCallbacks:  # type: typing.Callable[[Saving.SectionBase], bool]
			try:
				callbackSuccess = loadCallback(self)  # type: bool

				if not callbackSuccess:
					operationSuccessful = False
			except:
				Debug.Log("Failed to activate load callback at '" + Types.GetFullName(loadCallback) + "'.\n" + operationInformation, self.SavingObject.Host.Namespace, Debug.LogLevels.Exception, group = self.SavingObject.Host.Namespace, owner = __name__)
				operationSuccessful = False

		return operationSuccessful

	def _ActivateSaveCallbacks (self) -> bool:
		operationInformation = "Save Identifier: %s | Section Identifier: %s" % (self.SavingObject.Identifier, self.Identifier,)
		operationSuccessful = True  # type: bool

		for saveCallback in self._saveCallbacks:  # type: typing.Callable[[Saving.SectionBase], bool]
			try:
				callbackSuccess = saveCallback(self)  # type: bool

				if not callbackSuccess:
					operationSuccessful = False
			except:
				Debug.Log("Failed to activate save callback at '" + Types.GetFullName(saveCallback) + "'.\n" + operationInformation, self.SavingObject.Host.Namespace, Debug.LogLevels.Exception, group = self.SavingObject.Host.Namespace, owner = __name__)
				operationSuccessful = False

		return operationSuccessful

	def _ActivateResetCallbacks (self) -> bool:
		operationInformation = "Save Identifier: %s | Section Identifier: %s" % (self.SavingObject.Identifier, self.Identifier,)
		operationSuccessful = True  # type: bool

		for resetCallback in self._resetCallbacks:  # type: typing.Callable[[Saving.SectionBase], bool]
			try:
				callbackSuccess = resetCallback(self)  # type: bool

				if not callbackSuccess:
					operationSuccessful = False
			except:
				Debug.Log("Failed to activate reset callback at '" + Types.GetFullName(resetCallback) + "'.\n" + operationInformation, self.SavingObject.Host.Namespace, Debug.LogLevels.Exception, group = self.SavingObject.Host.Namespace, owner = __name__)
				operationSuccessful = False

		return operationSuccessful
