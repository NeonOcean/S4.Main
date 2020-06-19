from __future__ import annotations

import abc
import copy
import json
import os
import typing

from NeonOcean.S4.Main import Debug, Paths, This
from NeonOcean.S4.Main.Saving import SectionBranched
from NeonOcean.S4.Main.Tools import Events, Exceptions, Types, Version

class PersistentBranched(abc.ABC):
	"""
	A persistence class that allows you to have multiple values for all registered persistent data. This is an incomplete class, you would need to implement the
	load and save functions.
	"""

	class Value:
		def __init__ (self, values: typing.Dict[str, typing.Any], valueType: type, default, verify: typing.Callable):
			"""
			Used for storage of persistent data.
			"""

			self.Values = values  # type: typing.Dict[str, typing.Any]
			self.ValueType = valueType  # type: type
			self.Default = default  # type: typing.Any
			self.Verify = verify  # type: typing.Callable

		def IsSet (self, branch: str) -> bool:
			return branch in self.Values

		def Save (self) -> typing.Dict[str, typing.Any]:
			return copy.deepcopy(self.Values)

		def Get (self, branch: str) -> typing.Any:
			if not branch in self.Values:
				return copy.deepcopy(self.Default)

			return copy.deepcopy(self.Values[branch])

		def GetAllBranches (self) -> typing.Dict[str, typing.Any]:
			return copy.deepcopy(self.Values)

		def GetAllBranchIdentifiers (self) -> typing.Set[str]:
			return set(self.Values.keys())

		def Set (self, branch: str, value: typing.Any, version: Version.Version, verify: bool = True) -> None:
			if verify:
				copiedValue = copy.deepcopy(self.Verify(value, version))  # type: typing.Any
			else:
				copiedValue = copy.deepcopy(value)  # type: typing.Any

			self.Values[branch] = copiedValue

		def SetAllBranches (self, value: typing.Any, version: Version.Version, verify: bool = True) -> None:
			if verify:
				copiedValue = copy.deepcopy(self.Verify(value, version))  # type: typing.Any
			else:
				copiedValue = copy.deepcopy(value)  # type: typing.Any

			for branch in self.Values.keys():  # type: str
				self.Values[branch] = copiedValue

		def Reset (self, branch: str = None) -> None:
			if branch is None:
				self.Values = dict()
			else:
				self.Values.pop(branch, None)

	def __init__ (self, currentVersion: Version.Version, hostNamespace: str = This.Mod.Namespace):
		"""
		:param currentVersion: The current version of what ever will be controlling this persistence object.
							   This value can allow you to correct outdated persistent data.
		:type currentVersion: Version.Version
		:param hostNamespace: Errors made by this persistent object will show up under this namespace.
		:type hostNamespace: str
		"""

		if not isinstance(currentVersion, Version.Version):
			raise Exceptions.IncorrectTypeException(currentVersion, "currentVersion", (Version.Version,))

		if not isinstance(hostNamespace, str):
			raise Exceptions.IncorrectTypeException(hostNamespace, "hostNamespace", (str,))

		self.CurrentVersion = currentVersion  # type: Version.Version
		self.HostNamespace = hostNamespace  # type: str

		self.OnUpdate = Events.EventHandler()  # type: Events.EventHandler  # An event that is triggered to notify listeners of a changed value.
		self.OnLoad = Events.EventHandler()  # type: Events.EventHandler  # An event that is triggered when new data is loaded.

		self._loadedData = dict()  # type: typing.Dict[str, typing.Any]
		self._loadedLastVersion = None  # type: typing.Optional[Version.Version]

		self._storage = dict()  # type: typing.Dict[str, PersistentBranched.Value]
		self._managedBranches = list()  # type: typing.List[str]

		self._updateStorage = list()  # type: list

	@property
	def LoadedLastVersion (self) -> typing.Optional[Version.Version]:
		"""
		The last version the loaded data was loaded in.
		:return:
		"""

		if self._loadedLastVersion is None:
			return None

		return Version.Version(str(self._loadedLastVersion))

	@abc.abstractmethod
	def Load (self, *args, **kwargs) -> typing.Any:
		raise NotImplementedError()

	@abc.abstractmethod
	def Save (self, *args, **kwargs) -> typing.Any:
		raise NotImplementedError()

	def Setup (self, key: str, valueType: type, default, verify: typing.Callable) -> None:
		"""
		Setup persistent data for this persistence object. All persistent data must be setup before it can be used. Persistent data can be loaded before being
		setup but will remain dormant until setup. Persistent data also cannot be setup twice, an exception will be raised if this is tried.

		:param key: The name of the persistent data to be setup. This will be used to get and set the value in the future and is case sensitive.
		:type key: str

		:param valueType: The persistent data's value type, i.e. str, bool, float. The value of this persistent data should never be anything other than this type.
		:type valueType: type

		:param default: The persistent data's default value. Needs to be of the type specified in the valueType parameter.

		:param verify: This is called when changing or loading a value to verify that is correct and still valid.
					   Verify functions need to take two parameters: the value being verified and the version the value was set.
					   The first parameter will always be of the type specified in the 'valueType'. The value will often not be the current value of the persistent data.
					   The second parameter will be the version this value was set. The type of this parameter will be NeonOcean.S4.Main.Tools.Version.Version
					   Verify functions should also return the input or a corrected value.
					   If the value cannot be corrected the verify function should raise an exception, the persistent data may then revert to its default if necessary.
		:type verify: typing.Callable

		:rtype: None
		"""

		if not isinstance(key, str):
			raise Exceptions.IncorrectTypeException(key, "key", (str,))

		if self.IsSetup(key):
			raise Exception("Persistent data '" + key + "' is already setup.")

		if not isinstance(valueType, type):
			raise Exceptions.IncorrectTypeException(valueType, "valueType", (type,))

		if not isinstance(default, valueType):
			raise Exceptions.IncorrectTypeException(default, "default", (valueType,))

		if not isinstance(verify, typing.Callable):
			raise Exceptions.IncorrectTypeException(verify, "verify", ("Callable",))

		try:
			verifiedDefault = verify(default)
		except Exception as e:
			raise ValueError("Failed to verify default value for persistent data '" + key + "'.") from e

		if verifiedDefault != default:
			Debug.Log("Verification of default value for persistent data '" + key + "' changed it.", self.HostNamespace, level = Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)

		version = self.LoadedLastVersion

		if version is None:
			version = self.CurrentVersion

		values = dict()  # type: typing.Dict[str, typing.Any]

		for branchKey in list(self._loadedData.keys()):  # type: str
			branchValues = self._loadedData[branchKey]  # type: typing.Dict[str, typing.Any]

			if key in branchValues:
				try:
					values[branchKey] = verify(branchValues[key], version)
				except Exception:
					Debug.Log("Verify callback found fault with the value that was stored for persistent data '" + key + "'.", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)

		valueStorage = self.Value(values, valueType, default, verify)  # type: PersistentBranched.Value
		self._storage[key] = valueStorage

	def IsSetup (self, key: str) -> bool:
		"""
		Returns true if the persistent data specified by the key is setup.

		:param key: The name of the persistent data, is case sensitive.
		:type key: str
		:rtype: bool
		"""

		return key in self._storage

	def Get (self, branch: str, key: str):
		"""
		Gets the value of the persistent data specified by the key and branch. The value returned will be a deep copy of what is stored, modifying it should never change
		anything unless you set it with the set function.

		:param branch: The name of the branch to get the value from.
		:type branch: str
		:param key: The name of the persistent data, is case sensitive.
		:type key: str
		:return: The return object will always be of the type specified for the target persistent data during setup.
		"""

		if not isinstance(branch, str):
			raise Exceptions.IncorrectTypeException(branch, "branch", (str,))

		if not isinstance(key, str):
			raise Exceptions.IncorrectTypeException(key, "key", (str,))

		if not self.IsSetup(key):
			raise Exception("Persistent data '" + key + "' is not setup.")

		return self._storage[key].Get(branch)

	def GetAllBranches (self, key: str) -> typing.Dict[str, typing.Any]:
		"""
		Gets a dictionary of every branch's value for the persistent data specified by the key. The value returned will be a deep copy of what is stored, modifying it
		should never change anything unless you set it with the set function.

		:param key: The name of the persistent data, is case sensitive.
		:type key: str
		"""

		if not isinstance(key, str):
			raise Exceptions.IncorrectTypeException(key, "key", (str,))

		if not self.IsSetup(key):
			raise Exception("Persistent data '" + key + "' is not setup.")

		return self._storage[key].GetAllBranches()

	def GetAllBranchIdentifiers (self, key: str) -> typing.Set[str]:
		"""
		Gets a set of every branch's identifier for the persistent data specified by the key.
		"""

		if not isinstance(key, str):
			raise Exceptions.IncorrectTypeException(key, "key", (str,))

		if not self.IsSetup(key):
			raise Exception("Persistent data '" + key + "' is not setup.")

		return self._storage[key].GetAllBranchIdentifiers()

	def Set (self, branch: str, key: str, value, autoSave: bool = True, autoUpdate: bool = True) -> None:
		"""
		Set the value of the persistent data specified by the key and branch. The value is deep copied before being but into storage, modifying the value after setting
		it will not change the stored version.

		:param branch: The name of the branch to set the value to.
		:type branch: str
		:param key: The name of the persistent data, is case sensitive.
		:type key: str
		:param value: The value the persistent data will be changing to. This must be of the type specified for the target persistent data during setup.
		:param autoSave: Whether or not to automatically save the persistent data after changing the value.
		 				 This can allow you to change multiple values at once without saving each time.
		:type autoSave: bool
		:param autoUpdate: Whether or not to automatically update callbacks to the fact that a value has changed.
						   This can allow you to change multiple values at once without calling update callbacks each time.
		:type autoUpdate: bool
		:rtype: None
		"""

		if not isinstance(branch, str):
			raise Exceptions.IncorrectTypeException(branch, "branch", (str,))

		if not isinstance(key, str):
			raise Exceptions.IncorrectTypeException(key, "key", (str,))

		if not self.IsSetup(key):
			raise Exception("Persistent data '" + key + "' is not setup.")

		valueStorage = self._storage[key]

		if not isinstance(value, valueStorage.ValueType):
			raise Exceptions.IncorrectTypeException(value, "value", (valueStorage.ValueType,))

		if not isinstance(autoSave, bool):
			raise Exceptions.IncorrectTypeException(autoSave, "autoSave", (bool,))

		if not isinstance(autoUpdate, bool):
			raise Exceptions.IncorrectTypeException(autoUpdate, "autoUpdate", (bool,))

		valueStorage.Set(branch, value, self.CurrentVersion)

		if autoSave:
			self.Save()

		if autoUpdate:
			self.Update()

	def SetAllBranches (self, key: str, value, autoSave: bool = True, autoUpdate: bool = True) -> None:
		"""
		Set the value of the persistent data specified by the key in all branches. The value is deep copied before being but into storage, modifying the value after
		setting it will not change the stored version.

		:param key: The name of the persistent data, is case sensitive.
		:type key: str
		:param value: The value the persistent data will be changing to. This must be of the type specified for the target persistent data during setup.
		:param autoSave: Whether or not to automatically save the persistent data after changing the value.
		 				 This can allow you to change multiple values at once without saving each time.
		:type autoSave: bool
		:param autoUpdate: Whether or not to automatically update callbacks to the fact that a value has changed.
						   This can allow you to change multiple values at once without calling update callbacks each time.
		:type autoUpdate: bool
		:rtype: None
		"""

		if not isinstance(key, str):
			raise Exceptions.IncorrectTypeException(key, "key", (str,))

		if not self.IsSetup(key):
			raise Exception("Persistent data '" + key + "' is not setup.")

		valueStorage = self._storage[key]

		if not isinstance(value, valueStorage.ValueType):
			raise Exceptions.IncorrectTypeException(value, "value", (valueStorage.ValueType,))

		if not isinstance(autoSave, bool):
			raise Exceptions.IncorrectTypeException(autoSave, "autoSave", (bool,))

		if not isinstance(autoUpdate, bool):
			raise Exceptions.IncorrectTypeException(autoUpdate, "autoUpdate", (bool,))

		valueStorage.SetAllBranches(value, self.CurrentVersion)

		if autoSave:
			self.Save()

		if autoUpdate:
			self.Update()

	def ValueIsSet (self, branch: str, key: str) -> bool:
		"""
		Get whether or not this key has a value set for this branch, an exception will be raised it the key has not been setup.

		:param branch: The name of the branch to set the value to.
		:type branch: str
		:param key: The name of the persistent data, is case sensitive.
		:type key: str
		:return: True if the value has been set, False if not.
		:rtype: bool
		"""

		if not self.IsSetup(key):
			raise Exception("Persistent data '" + key + "' is not setup.")

		valueStorage = self._storage[key]  # type: PersistentBranched.Value
		return valueStorage.IsSet(branch)

	def Reset (self, branch: str = None, key: str = None, autoSave: bool = True, autoUpdate: bool = True) -> None:
		"""
		Resets persistent data to its default value.

		:param branch: The name of the branch containing the value to reset. If the branch is none, the target value will be reset in all branches.
		:type branch: str
		:param key: The name of the persistent data, is case sensitive. If the key is none, all values will be reset.
		:type key: str
		:param autoSave: Whether or not to automatically save the persistent data after resetting the values.
		:type autoSave: bool
		:param autoUpdate: Whether or not to automatically notify callbacks to the fact that the values have been reset.
		:type autoUpdate: bool
		:rtype: None
		"""

		if not isinstance(branch, str) and branch is not None:
			raise Exceptions.IncorrectTypeException(branch, "branch", (str,))

		if not isinstance(key, str) and key is not None:
			raise Exceptions.IncorrectTypeException(key, "key", (str,))

		if key is None:
			for valueStorage in self._storage.values():  # type: str, PersistentBranched.Value
				valueStorage.Reset(branch)
		else:
			if not self.IsSetup(key):
				raise Exception("Persistent data '" + key + "' is not setup.")

			valueStorage = self._storage[key]  # type: PersistentBranched.Value
			valueStorage.Reset(branch)

		if autoSave:
			self.Save()

		if autoUpdate:
			self.Update()

	def Update (self) -> None:
		"""
		Triggers the 'OnUpdate' event.
		This should be called after any persistent data change where you elected not to allow for auto-updating.

		:rtype: None
		"""

		self._InvokeOnUpdateEvent()

	def _LoadSetData (self, persistentDataBranches: dict, lastVersion: typing.Optional[Version.Version] = None) -> bool:
		"""
		:param persistentDataBranches: The persistent data branches to be loaded.
		:type persistentDataBranches: dict
		:param lastVersion: The last version this data was saved successfully in.
		:type lastVersion: Version.Version
		:return: True if this completed without incident, False if not.
		:rtype: bool
		"""

		operationSuccess = True  # type: bool

		changed = False  # type: bool

		for persistentBranchKey in list(persistentDataBranches.keys()):  # type: str
			persistentBranchValues = persistentDataBranches[persistentBranchKey]  # type: typing.Dict[str, typing.Any]

			if not isinstance(persistentBranchKey, str):
				persistentDataBranches.pop(persistentBranchKey, None)
				Debug.Log("Invalid type in persistent data.\n" + Exceptions.GetIncorrectTypeExceptionText(persistentBranchKey, "PersistentDataBranches<Key>", (str,)), self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
				changed = True
				operationSuccess = False
				continue

			if not isinstance(persistentBranchValues, dict):
				persistentDataBranches.pop(persistentBranchKey, None)
				Debug.Log("Invalid type in persistent data.\n" + Exceptions.GetIncorrectTypeExceptionText(persistentBranchValues, "PersistentDataBranches[%s]" % persistentBranchKey, (dict,)), self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
				changed = True
				operationSuccess = False
				continue

			for persistentKey in list(persistentBranchValues.keys()):  # type: str
				persistentValue = persistentBranchValues[persistentKey]  # type: typing.Any

				if not isinstance(persistentKey, str):
					persistentBranchValues.pop(persistentKey, None)
					Debug.Log("Invalid type in persistent data.\n" + Exceptions.GetIncorrectTypeExceptionText(persistentKey, "PersistentDataBranches[%s]<Key>" % persistentBranchKey, (str,)), self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
					changed = True
					operationSuccess = False
					continue

				if not persistentKey in self._storage:
					continue

				valueStorage = self._storage[persistentKey]  # type: PersistentBranched.Value

				if not isinstance(persistentValue, valueStorage.ValueType):
					Debug.Log("Invalid type in persistent data.\n" + Exceptions.GetIncorrectTypeExceptionText(persistentKey, "PersistentDataBranches[%s][%s]" % (persistentBranchKey, persistentKey), (str,)), self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
					persistentBranchValues.pop(persistentKey, None)
					changed = True
					operationSuccess = False
					continue

				try:
					valueStorage.Set(persistentBranchKey, persistentValue, lastVersion)
				except Exception:
					Debug.Log("Cannot set value '" + str(persistentValue) + "' for persistent data '" + persistentKey + "'.", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
					persistentBranchValues.pop(persistentKey, None)
					changed = True
					operationSuccess = False
					continue

		self._loadedData = persistentDataBranches
		self._loadedLastVersion = lastVersion

		if changed:
			self.Save()

		self.Update()

		return operationSuccess

	def _SaveGetData (self) -> typing.Tuple[bool, dict]:
		"""
		:return: The first value indicates if this method completed without incident. The second is the save data.
		:rtype: typing.Tuple[bool, dict]
		"""

		operationSuccess = True  # type: bool

		persistentData = copy.deepcopy(self._loadedData)  # type: typing.Dict[str, typing.Any]

		for persistentKey, persistentValueStorage in self._storage.items():  # type: str, PersistentBranched.Value
			try:
				for branchKey, branchValue in persistentValueStorage.Save().items():  # type: str, typing.Any
					if branchKey not in persistentData:
						persistentData[branchKey] = dict()

					persistentData[branchKey][persistentKey] = branchValue
			except Exception:
				Debug.Log("Failed to save value of '" + persistentKey + "'. This entry may be reset the next time this persistent data is loaded.", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
				persistentData.pop(persistentKey, None)
				operationSuccess = False

		return operationSuccess, persistentData

	def _InvokeOnUpdateEvent (self) -> Events.EventArguments:
		eventArguments = Events.EventArguments()  # type: Events.EventArguments

		for updateCallback in self.OnUpdate:  # type: typing.Callable[[PersistentBranched, Events.EventArguments], None]
			try:
				updateCallback(self, eventArguments)
			except:
				Debug.Log("Failed to run the 'OnUpdate' callback '" + Types.GetFullName(updateCallback) + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

		return eventArguments

	def _InvokeOnLoadEvent (self) -> Events.EventArguments:
		eventArguments = Events.EventArguments()  # type: Events.EventArguments

		for loadCallback in self.OnLoad:  # type: typing.Callable[[PersistentBranched, Events.EventArguments], None]
			try:
				loadCallback(self, eventArguments)
			except:
				Debug.Log("Failed to run the 'OnLoad' callback '" + Types.GetFullName(loadCallback) + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

		return eventArguments

class PersistentBranchedDirect(PersistentBranched):
	"""
	A class for handling persistent data. This version will allow you to directly input the persistent data container when using the load method, and get the persistent
	data container as the return value when using the save method.
	"""

	_branchesKey = "Branches"
	_lastVersionKey = "LastVersion"

	def Load (self, persistentDataContainer: dict) -> bool:
		"""
		Load persistent data from a persistent data container.
		:param persistentDataContainer: The persistent data container dictionary.
		:type persistentDataContainer: dict
		:return: True if this completed without incident, False if not.
		:rtype: bool
		"""

		operationSuccess = True  # type: bool

		if not isinstance(persistentDataContainer, dict):
			raise Exceptions.IncorrectTypeException(persistentDataContainer, "persistentDataContainer", (dict,))

		persistentDataBranches = persistentDataContainer.get(self._branchesKey, dict())  # type: typing.Dict[str, typing.Dict[str, typing.Any]]

		if not isinstance(persistentDataBranches, dict):
			Debug.Log("Invalid type in persistent data container.\n" + Exceptions.GetIncorrectTypeExceptionText(persistentDataBranches, "PersistentDataContainer[%s]" % self._branchesKey, (dict,)), self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
			persistentDataBranches = dict()
			operationSuccess = False

		lastVersionString = persistentDataContainer.get(self._lastVersionKey)  # type:

		if lastVersionString is None:
			lastVersion = None
		else:
			if not isinstance(lastVersionString, str):
				Debug.Log("Invalid type in persistent data container.\n" + Exceptions.GetIncorrectTypeExceptionText(lastVersionString, "PersistentDataContainer[%s]" % self._lastVersionKey, (dict,)), self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
				lastVersion = None
				operationSuccess = False
			else:
				try:
					lastVersion = Version.Version(lastVersionString)
				except Exception:
					Debug.Log("Cannot convert persistent data's last version value '" + lastVersionString + "' to a version number object", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
					lastVersion = None
					operationSuccess = False

		self.Reset(autoSave = False, autoUpdate = False)
		setDataSuccess = self._LoadSetData(persistentDataBranches, lastVersion = lastVersion)  # type: bool

		self._InvokeOnLoadEvent()

		if not setDataSuccess:
			return False

		return operationSuccess

	def Save (self) -> typing.Tuple[bool, dict]:
		"""
		Creates and returns a persistent data container with the current data.
		:return: The first value indicates if this method completed without incident. The second is the save data.
		:rtype: typing.Tuple[bool, dict]
		"""

		getDataSuccess, persistentDataBranches = self._SaveGetData()  # type: bool, dict

		persistentDataContainer = {
			self._branchesKey: persistentDataBranches,
			self._lastVersionKey: str(self.CurrentVersion)
		}  # type: dict

		return getDataSuccess, persistentDataContainer

class PersistentBranchedJson(PersistentBranchedDirect):
	"""
	A class for handling persistent data. This version will allow you to directly input the persistent data as a json string when using the load method, and get the string
	as the return value when using the save method.
	"""

	def Load (self, persistentDataContainerString: str, *args) -> bool:
		"""
		Load persistent data from the file path specified when initiating this object, if it exists.
		:param persistentDataContainerString: The persistent data container dictionary as a json encoded string.
		:type persistentDataContainerString: str
		:return: True if this completed without incident, False if not.
		:rtype: bool
		"""

		operationSuccess = True  # type: bool

		if not isinstance(persistentDataContainerString, str):
			raise Exceptions.IncorrectTypeException(persistentDataContainerString, "persistentDataContainerString", (str,))

		try:
			persistentDataContainer = json.JSONDecoder().decode(persistentDataContainerString)
		except Exception:
			Debug.Log("Could not decode the persistent data container string.", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
			persistentDataContainer = { }
			operationSuccess = False

		if not isinstance(persistentDataContainer, dict):
			Debug.Log("Could not convert persistent data container string to a dictionary.", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
			persistentDataContainer = { }
			operationSuccess = False

		loadSuccessful = super().Load(persistentDataContainer)  # type: bool

		if not loadSuccessful:
			return False

		return operationSuccess

	def Save (self) -> typing.Tuple[bool, str]:
		"""
		Encodes the persistent data container to a json string. This method can handle cases in which any persistent data's key or value cannot be encoded.

		:return: The first value indicates if this method completed without incident. The second is the save data.
		:rtype: typing.Tuple[bool, dict]
		"""

		operationSuccess = True  # type: bool

		saveSuccess, persistentDataContainer = super().Save()  # type: bool, dict

		persistentDataBranches = persistentDataContainer[self._branchesKey]  # type: typing.Dict[str, typing.Dict[str, typing.Any]]
		persistentDataBranchesValuesString = ""  # type: str

		for branchKey, branchValue in persistentDataBranches.items():  # type: str, dict
			branchInformation = "Branch: " + branchKey
			persistentDataValuesString = ""

			for persistentKey, persistentValue in branchValue.items():  # type: str, typing.Any
				keyInformation = "Key: " + persistentKey  # type: str

				try:
					assert isinstance(persistentKey, str)
					persistentKeyString = json.JSONEncoder(indent = "\t").encode(persistentKey)  # type: str
					assert "\n" not in persistentKeyString and "\r" not in persistentKeyString
				except Exception:
					Debug.Log("Failed to encode a persistence key to a json string.\n" + branchInformation + "\n" + keyInformation, self.HostNamespace, Debug.LogLevels.Exception, group = self.HostNamespace, owner = __name__)
					operationSuccess = False
					continue

				valueInformation = "Value Type: " + Types.GetFullName(persistentKey) + "\nValue Value: " + persistentKey  # type: str

				try:
					persistentValueString = json.JSONEncoder(indent = "\t").encode(persistentValue)  # type: str
				except Exception:
					Debug.Log("Failed to encode a persistence value to a json string.\n" + branchInformation + "\n" + keyInformation + "\n" + valueInformation, self.HostNamespace, Debug.LogLevels.Exception, group = self.HostNamespace, owner = __name__)
					operationSuccess = False
					continue

				persistentValueString = persistentValueString.replace("\n", "\n\t\t\t")

				if persistentDataValuesString != "":
					persistentDataValuesString += ",\n"

				persistentDataValuesString += "\t\t\t" + persistentKeyString + ": " + persistentValueString

			if persistentDataBranchesValuesString != "":
				persistentDataBranchesValuesString += ",\n"

			persistentDataBranchesValuesString += "\t\t\"" + branchKey + "\": {"

			if persistentDataBranchesValuesString != "":
				persistentDataBranchesValuesString += "\n" + persistentDataValuesString + "\n\t\t}"
			else:
				persistentDataBranchesValuesString += "}"

		persistentDataBranchesString = "\t\"" + self._branchesKey + "\": {"  # type: str

		if persistentDataBranchesString != "":
			persistentDataBranchesString += "\n" + persistentDataBranchesValuesString + "\n\t}"
		else:
			persistentDataBranchesString += "}"

		lastVersion = persistentDataContainer[self._lastVersionKey]  # type: str

		try:
			lastVersionString = json.JSONEncoder(indent = "\t").encode(lastVersion)  # type: str
		except Exception as e:
			raise Exception("Failed to encode a persistence last version to a json string.") from e

		lastVersionString = "\t\"" + self._lastVersionKey + "\": " + lastVersionString  # type: str

		persistentDataContainerString = "{\n" + persistentDataBranchesString + ",\n" + lastVersionString + "\n}"  # type: str

		if not saveSuccess:
			return False, persistentDataContainerString

		return operationSuccess, persistentDataContainerString

class PersistentBranchedFile(PersistentBranchedJson):
	"""
	A class for handling persistent data. This version will read and write the data to a file through the load and save methods.
	"""

	def __init__ (self, filePath: str, currentVersion: Version.Version, hostNamespace: str = This.Mod.Namespace):
		"""
		:param filePath: The file path this persistence object will be written to and read from.
		:type filePath: str
		:param currentVersion: The current version of what ever will be controlling this persistence object.
							   This value can allow you to correct outdated persistent data.
		:type currentVersion: Version.Version
		:param hostNamespace: Errors made by this persistent object will show up under this namespace.
		:type hostNamespace: str
		"""

		if not isinstance(filePath, str):
			raise Exceptions.IncorrectTypeException(filePath, "path", (str,))

		super().__init__(currentVersion, hostNamespace = hostNamespace)

		self.FilePath = filePath  # type: str

	def Load (self, *args) -> bool:
		"""
		Load persistent data from the file path specified when initiating this object, if it exists.

		:return: True if this completed without incident, False if not.
		:rtype: bool
		"""

		operationSuccess = True  # type: bool

		persistentDataContainerString = "{}"  # type: str

		if os.path.exists(self.FilePath):
			try:
				with open(self.FilePath) as persistentFile:
					persistentDataContainerString = persistentFile.read()
			except Exception:
				Debug.Log("Failed to read from '" + Paths.StripUserDataPath(self.FilePath) + "'.", self.HostNamespace, Debug.LogLevels.Error, group = self.HostNamespace, owner = __name__)
				operationSuccess = False

		loadSuccessful = super().Load(persistentDataContainerString)  # type: bool

		if not loadSuccessful:
			return False

		return operationSuccess

	def Save (self) -> bool:
		"""
		Saves the currently stored persistent data to the file path specified when initiating this object.
		If the directory the save file is in doesn't exist one will be created.

		:return: True if this completed without incident, False if not.
		:rtype: bool
		"""

		operationSuccess = True  # type: bool

		saveSuccessful, persistentDataContainerString = super().Save()  # type: bool, str

		try:
			if not os.path.exists(os.path.dirname(self.FilePath)):
				os.makedirs(os.path.dirname(self.FilePath))

			with open(self.FilePath, mode = "w+") as persistentFile:
				persistentFile.write(persistentDataContainerString)
		except Exception:
			Debug.Log("Failed to write to '" + Paths.StripUserDataPath(self.FilePath) + "'.", self.HostNamespace, Debug.LogLevels.Error, group = self.HostNamespace, owner = __name__)
			operationSuccess = False

		if not saveSuccessful:
			return False

		return operationSuccess

class PersistentBranchedSection(PersistentBranchedDirect):
	"""
	A class for writing branched persistent data to a branched saving section.
	"""

	def __init__ (self, linkedSection: SectionBranched.SectionBranched, sectionKey: str, currentVersion: Version.Version, hostNamespace: str = This.Mod.Namespace):
		"""
		:param linkedSection: The section this persistence object is linked to, this must be a branched section.
		:type linkedSection: SectionBranched.SectionBranched
		:param sectionKey: The key the persistent data is saved to and loaded from in the section data.
		:type sectionKey: str
		:param currentVersion: The current version of what ever will be controlling this persistence object.
							   This value can allow you to correct outdated persistent data.
		:type currentVersion: Version.Version
		:param hostNamespace: Errors made by this persistent object will show up under this namespace.
		:type hostNamespace: str
		"""

		self._linkedSection = linkedSection
		self._sectionKey = sectionKey

		self._linkedSection.RegisterLoadCallback(self._SectionLoadCallback)
		self._linkedSection.RegisterSaveCallback(self._SectionSaveCallback)
		self._linkedSection.RegisterResetCallback(self._SectionResetCallback)

		super().__init__(currentVersion, hostNamespace = hostNamespace)

	@property
	def LinkedSection (self) -> SectionBranched.SectionBranched:
		return self._linkedSection

	@property
	def SectionKey (self) -> str:
		return self._sectionKey

	def _SectionLoadCallback (self, section: SectionBranched.SectionBranched) -> bool:
		persistentDataContainer = {
			self._branchesKey: section.GetAllValues(self.SectionKey),
			self._lastVersionKey: section.SavingObject.DataHostVersion
		}  # type: dict

		loadSuccessful = self.Load(persistentDataContainer = persistentDataContainer)  # type: bool
		return loadSuccessful

	def _SectionSaveCallback (self, section: SectionBranched.SectionBranched) -> bool:
		saveSuccessful, persistentDataContainer = self.Save()  # type: bool, dict

		for branchKey, branchValue in persistentDataContainer[self._branchesKey].items():
			section.Set(branchKey, self.SectionKey, branchValue)

		return saveSuccessful

	def _SectionResetCallback (self, section: SectionBranched.SectionBranched) -> bool:
		persistentDataContainer = {
			self._branchesKey: section.GetAllValues(self.SectionKey),
			self._lastVersionKey: section.SavingObject.DataHostVersion
		}

		loadSuccessful = self.Load(persistentDataContainer = persistentDataContainer)  # type: bool
		return loadSuccessful
