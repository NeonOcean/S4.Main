from __future__ import annotations

import abc
import copy
import typing

from NeonOcean.S4.Main import Debug, DebugShared, This
from NeonOcean.S4.Main.Tools import Exceptions, Types, Version

class SavableException(Exception):
	def __init__ (self, failedAttribute: str, objectType: str):
		if not isinstance(failedAttribute, str):
			raise Exceptions.IncorrectTypeException(failedAttribute, "failedAttribute", (str,))

		if not isinstance(objectType, str):
			raise Exceptions.IncorrectTypeException(objectType, "objectType", (str,))

		self.FailedAttribute = failedAttribute  # type: str
		self.ObjectType = objectType  # type: str

		super().__init__(*(failedAttribute, objectType))

	def __str__ (self):
		return "Failed to complete a savable operation for the attribute '" + self.FailedAttribute + "' in an object of the type '" + self.ObjectType + "'."

class AttributeHandlerBase(abc.ABC):
	def __init__ (self,
				  savingKey: str,
				  attributeName: str,
				  requiredSuccess: bool = True,
				  requiredAttribute: bool = False,
				  skipSaveTest: typing.Optional[typing.Callable] = None,
				  updater: typing.Optional[typing.Callable] = None):
		"""
		The base object for savable attribute handlers.
		:param savingKey: The dictionary key the targeted attribute will be save to and loaded from.
		:type savingKey: str
		:param attributeName: The name of the target attribute.
		:type attributeName: str
		:param requiredSuccess: Whether or not the attribute needs to be successfully loaded and saved. Exceptions raised when loading or saving will not be
		caught if True.
		:type requiredSuccess: bool
		:param requiredAttribute: Whether or not this attribute's save data needs to exist. Exceptions will be raised if the attribute's save data is not
		found when loading.
		:param skipSaveTest: A callable object used to determine if this attribute doesn't need to be saved. This should take no parameters and return
		true or false. This must be None if the 'requiredAttribute' parameter is true.
		:type skipSaveTest: typing.Optional[typing.Callable]
		:param: updater: A callable object that will be used to bring old data from previous versions up to date. This should take the loading data dictionary
		and the last version as its two parameters. The last version can be None instead of a version object if no last version was specified.
		This parameter may be None if no updates are necessary for this attribute.
		:type updater: typing.Optional[typing.Callable]
		"""

		if not isinstance(savingKey, str):
			raise Exceptions.IncorrectTypeException(savingKey, "savingKey", (str,))

		if not isinstance(attributeName, str):
			raise Exceptions.IncorrectTypeException(attributeName, "attributeName", (str,))

		if not isinstance(requiredSuccess, bool):
			raise Exceptions.IncorrectTypeException(requiredSuccess, "requiredSuccess", (bool,))

		if not isinstance(requiredAttribute, bool):
			raise Exceptions.IncorrectTypeException(requiredAttribute, "requiredAttribute", (bool,))

		if not isinstance(updater, typing.Callable) and updater is not None:
			raise Exceptions.IncorrectTypeException(updater, "updater", ("Callable", None))

		if not isinstance(skipSaveTest, typing.Callable) and skipSaveTest is not None:
			raise Exceptions.IncorrectTypeException(skipSaveTest, "skipSaveTest", ("Callable", None))

		if requiredAttribute and skipSaveTest is not None:
			raise ValueError("Required attributes cannot have a skip save test.")

		self._savingKey = savingKey  # type: str
		self._attributeName = attributeName  # type: str
		self._requiredSuccess = requiredSuccess  # type: bool
		self._requiredAttribute = requiredAttribute  # type: bool
		self._skipTest = skipSaveTest  # type: typing.Optional[typing.Callable]
		self._updater = updater  # type: typing.Optional[typing.Callable]

	@property
	def AttributeName (self) -> str:
		"""
		The name of the target attribute.
		"""

		return self._attributeName

	@property
	def SavingKey (self) -> str:
		"""
		The dictionary key the targeted attribute will be save to and loaded from.
		"""

		return self._savingKey

	def LoadAttribute (self, loadingObject: typing.Any, data: dict, lastVersion: typing.Optional[Version.Version] = None) -> bool:
		"""
		Load this handler's attribute.
		:param loadingObject: The object to apply the attribute data to. This object must inherit from the savable extension.
		:type loadingObject: SavableExtension
		:param data: The raw data that the attribute is being loaded from.
		:type data: dict
		:param lastVersion: The mod version in which this data was last saved.
		:type lastVersion: typing.Optional[Version.Version]
		:return: Whether or not we finished handling the attribute without issue.
		:rtype: bool
		"""

		if not isinstance(loadingObject, SavableExtension):
			raise Exceptions.IncorrectTypeException(loadingObject, "loadingObject", (SavableExtension,))

		if not isinstance(data, dict):
			raise Exceptions.IncorrectTypeException(data, "data", (dict,))

		if not isinstance(lastVersion, Version.Version) and lastVersion is not None:
			raise Exceptions.IncorrectTypeException(lastVersion, "lastVersion", (Version.Version, None))

		operationInformation = loadingObject.SavableOperationInformation  # type: str

		try:
			try:
				if self._updater is not None:
					self._updater(data, lastVersion)
			except SavableException:
				raise
			except Exception as e:
				raise SavableException(self._attributeName, Types.GetFullName(loadingObject)) from e
		except Exception as e:
			if self._requiredSuccess:
				raise
			else:
				Debug.Log("Load operation in a savable object failed to update the saved data for the attribute '" + self._attributeName + "'.\n" + DebugShared.FormatException(e) + "\n" + operationInformation, loadingObject.HostNamespace, Debug.LogLevels.Warning, group = loadingObject.HostNamespace, owner = __name__)
				return False

		try:
			try:
				return self._LoadAttributeInternal(loadingObject, data, lastVersion)
			except SavableException:
				raise
			except Exception as e:
				raise SavableException(self._attributeName, Types.GetFullName(loadingObject)) from e
		except Exception as e:
			if self._requiredSuccess:
				raise
			else:
				Debug.Log("Load operation in a savable object failed to load the attribute '" + self._attributeName + "'.\n" + DebugShared.FormatException(e) + "\n" + operationInformation, loadingObject.HostNamespace, Debug.LogLevels.Warning, group = loadingObject.HostNamespace, owner = __name__)
				self.ResetAttribute(loadingObject)
				return False

	def SaveAttribute (self, savingObject: typing.Any, data: dict) -> bool:
		"""
		Save this handler's attribute.
		:param savingObject: The object to take the attribute data from. This object must inherit from the savable extension.
		:type savingObject: typing.Any
		:param data: The raw data being that the attribute is being saved to.
		:type data: dict
		:return: Whether or not we finished handling the attribute without issue.
		:rtype: bool
		"""

		if not isinstance(savingObject, SavableExtension):
			raise Exceptions.IncorrectTypeException(savingObject, "savingObject", (SavableExtension,))

		if not isinstance(data, dict):
			raise Exceptions.IncorrectTypeException(data, "data", (dict,))

		operationInformation = savingObject.SavableOperationInformation  # type: str

		try:
			try:
				if self._skipTest is not None:
					if self._skipTest():
						return True
			except SavableException:
				raise
			except Exception as e:
				raise SavableException(self._attributeName, Types.GetFullName(savingObject)) from e
		except Exception as e:
			if self._requiredSuccess:
				raise
			else:
				Debug.Log("Save operation in a savable object failed to run skip test for the attribute '" + self._attributeName + "'.\n" + DebugShared.FormatException(e) + "\n" + operationInformation, savingObject.HostNamespace, Debug.LogLevels.Warning, group = savingObject.HostNamespace, owner = __name__)
				return False

		try:
			try:
				return self._SaveAttributeInternal(savingObject, data)
			except SavableException:
				raise
			except Exception as e:
				raise SavableException(self._attributeName, Types.GetFullName(savingObject)) from e
		except Exception as e:
			if self._requiredSuccess:
				raise
			else:
				Debug.Log("Save operation in a savable object failed to save the attribute '" + self._attributeName + "'.\n" + DebugShared.FormatException(e) + "\n" + operationInformation, savingObject.HostNamespace, Debug.LogLevels.Warning, group = savingObject.HostNamespace, owner = __name__)
				return False

	def ResetAttribute (self, resettingObject: typing.Any) -> bool:
		"""
		Reset this handler's attribute
		:param resettingObject: The object who's attribute needs to be reset. This object must inherit from the savable extension.
		:type resettingObject: typing.Any
		:return: Whether or not we finished handling the attribute without issue.
		:rtype: bool
		"""

		if not isinstance(resettingObject, SavableExtension):
			raise Exceptions.IncorrectTypeException(resettingObject, "resettingObject", (SavableExtension,))

		try:
			return self._ResetAttributeInternal(resettingObject)
		except SavableException:
			raise
		except Exception as e:
			raise SavableException(self._attributeName, Types.GetFullName(resettingObject)) from e

	@abc.abstractmethod
	def _LoadAttributeInternal (self, loadingObject: typing.Any, data: dict, lastVersion: typing.Optional[Version.Version]) -> bool:
		...

	@abc.abstractmethod
	def _SaveAttributeInternal (self, savingObject: typing.Any, data: dict) -> bool:
		...

	@abc.abstractmethod
	def _ResetAttributeInternal (self, resettingObject: typing.Any) -> bool:
		...

class SavableExtension:
	HostNamespace = This.Mod.Namespace  # type: str

	def __init__ (self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self._savables = list()  # type: typing.List[AttributeHandlerBase]

	@property
	def SavableOperationInformation (self) -> str:
		return "%s" % (self.__class__.__name__,)

	def RegisterSavableAttribute (self, attributeHandler: AttributeHandlerBase):
		"""
		Register a savable attribute of this object.
		:param attributeHandler: A object used to save, load, and reset the attribute in question.
		:type attributeHandler: AttributeHandlerBase
		"""

		if not isinstance(attributeHandler, AttributeHandlerBase):
			raise Exceptions.IncorrectTypeException(attributeHandler, "attributeHandler", (AttributeHandlerBase,))

		self._savables.append(attributeHandler)

	def LoadFromDictionary (self, data: dict, lastVersion: typing.Optional[Version.Version] = None) -> bool:
		if not isinstance(data, dict):
			raise Exceptions.IncorrectTypeException(data, "data", (dict,))

		self._OnLoading()
		loadSuccessful = self._LoadFromDictionaryInternal(data, lastVersion = lastVersion)  # type: bool
		self._OnLoaded()

		return loadSuccessful

	def SaveToDictionary (self) -> typing.Tuple[bool, dict]:
		self._OnSaving()
		saveSuccessful, data = self._SaveToDictionaryInternal()  # type: bool, dict
		self._OnSaved()

		return saveSuccessful, data

	def Reset (self) -> bool:
		self._OnResetting()
		resetSuccessful = self._ResetInternal()  # type: bool
		self._OnResetted()

		return resetSuccessful

	def _LoadFromDictionaryInternal (self, data: dict, lastVersion: typing.Optional[Version.Version]) -> bool:
		operationSuccessful = True  # type: bool

		if not self.Reset():
			raise Exception("Failed to reset a savable object in preparation for loading it.\n" + self.SavableOperationInformation)

		for savableAttribute in self._savables:  # type: AttributeHandlerBase
			if not savableAttribute.LoadAttribute(self, data, lastVersion = lastVersion):
				operationSuccessful = False

		return operationSuccessful

	def _OnLoading (self) -> None:
		pass

	def _OnLoaded (self) -> None:
		pass

	def _SaveToDictionaryInternal (self) -> typing.Tuple[bool, dict]:
		operationSuccessful = True  # type: bool

		data = dict()  # type: dict

		for savableAttribute in self._savables:  # type: AttributeHandlerBase
			if not savableAttribute.SaveAttribute(self, data):
				operationSuccessful = False

		return operationSuccessful, data

	def _OnSaving (self) -> None:
		pass

	def _OnSaved (self) -> None:
		pass

	def _ResetInternal (self) -> bool:
		operationSuccessful = True  # type: bool

		for savableAttribute in self._savables:  # type: AttributeHandlerBase
			if not savableAttribute.ResetAttribute(self):
				operationSuccessful = False

		return operationSuccessful

	def _OnResetting (self) -> None:
		pass

	def _OnResetted (self) -> None:
		pass

class StandardAttributeHandler(AttributeHandlerBase):
	def __init__ (self,
				  savingKey: str,
				  attributeName: str,
				  default: typing.Any,
				  requiredSuccess: bool = True,
				  requiredAttribute: bool = False,
				  skipSaveTest: typing.Optional[typing.Callable] = None,
				  updater: typing.Optional[typing.Callable] = None,
				  encoder: typing.Optional[typing.Callable] = None,
				  decoder: typing.Optional[typing.Callable] = None,
				  typeVerifier: typing.Callable[[typing.Any], None] = None):
		"""
		A standard attribute handler for an attribute.
		:param savingKey: The dictionary key the targeted attribute will be save to and loaded from.
		:type savingKey: str
		:param attributeName: The name of the target attribute.
		:type attributeName: str
		:param default: The default value for this attribute. Defaults should be capable of being copied as to prevent the default value from being changed.
		:type default: typing.Any
		:param requiredSuccess: Whether or not the attribute needs to be successfully loaded and saved. Exceptions raised when loading or saving will not be
		caught if True.
		:type requiredSuccess: bool
		:param requiredAttribute: Whether or not this attribute's save data needs to exist. Exceptions will be raised if the attribute's save data is not
		found when loading.
		:param skipSaveTest: A callable object used to determine if this attribute doesn't need to be saved. This should take no parameters and return
		true or false. This must be None if the 'requiredAttribute' parameter is true.
		:type skipSaveTest: typing.Optional[typing.Callable]
		:param: updater: A callable object that will be used to bring old data from previous versions up to date. This should take the loading data
		dictionary and the last version as its two parameters. The last version can be None instead of a version object if no last version was specified.
		This parameter may be None if no updates are necessary for this attribute.
		:type updater: typing.Optional[typing.Callable]
		:param: encoder: A callable object used to encode the attribute's value. This should take the attribute's value and output an object that
		can be saved without additional effort. This should be left as None if no conversion is necessary. If this parameter is none, then the decoder parameter
		must also be none.
		:type encoder: typing.Optional[typing.Callable]
		:param: decoder: A callable object used to decode saved data. This should take a previously saved value and output a valid value for this attribute.
		This should be left as None if no conversion is necessary. If this parameter is none, then the encoder parameter must also be none.
		:type decoder: typing.Optional[typing.Callable]
		:param typeVerifier: An optional type verifier, this should be a callable object that takes a value and raises an exception if it's invalid.
		If this attribute uses an encoder and decoder, the input will have been decoded first.
		:type typeVerifier: typing.Callable[[typing.Any], None]
		"""

		super().__init__(savingKey, attributeName, requiredSuccess = requiredSuccess, requiredAttribute = requiredAttribute, skipSaveTest = skipSaveTest, updater = updater)

		if not isinstance(encoder, typing.Callable) and encoder is not None:
			raise Exceptions.IncorrectTypeException(encoder, "encoder", ("Callable", None))

		if not isinstance(decoder, typing.Callable) and decoder is not None:
			raise Exceptions.IncorrectTypeException(decoder, "decoder", ("Callable", None))

		if encoder is None and decoder is not None:
			raise ValueError("The decoder is a callable object but the encoder is not. The 'encoder' and 'decoder' parameters must be both callable or both None.")

		if encoder is not None and decoder is None:
			raise ValueError("The encoder is a callable object but the decoder is not. The 'encoder' and 'decoder' parameters must be both callable or both None.")

		if not isinstance(typeVerifier, typing.Callable) and typeVerifier is not None:
			raise Exceptions.IncorrectTypeException(typeVerifier, "typeVerifier", ("Callable", None))

		default = copy.deepcopy(default)  # type: typing.Any

		try:
			if typeVerifier is not None:
				typeVerifier(default)
		except Exception as e:
			raise ValueError("Savable attribute " + attributeName + " has a default value that does not pass the type verifier check.") from e

		self.Default = default  # type: typing.Any

		self.Encoder = encoder  # type: typing.Optional[typing.Callable[[typing.Any], None]]
		self.Decoder = decoder  # type: typing.Optional[typing.Callable[[typing.Any], None]]
		self.TypeVerifier = typeVerifier  # type: typing.Optional[typing.Callable[[typing.Any], None]]

	def GetAttributeValue (self, targetObject: typing.Any) -> typing.Any:
		"""
		Get the value of the handling attribute from this target object.
		"""

		try:
			return getattr(targetObject, self.AttributeName)
		except AttributeError:
			return copy.deepcopy(self.Default)

	def _LoadAttributeInternal (self, loadingObject: typing.Any, data: dict, lastVersion: typing.Optional[Version.Version]) -> bool:
		attributeName = self._attributeName  # type: str

		if not self._requiredAttribute:
			try:
				attributeValue = data[self._savingKey]  # type: typing.Optional[dict]
			except KeyError:
				return True
		else:
			attributeValue = data[self._savingKey]  # type: typing.Optional[dict]

		if self.Decoder is not None:
			attributeValue = self.Decoder(attributeValue)

		if self.TypeVerifier is not None:
			self.TypeVerifier(attributeValue)

		setattr(loadingObject, attributeName, attributeValue)
		return True

	def _SaveAttributeInternal (self, savingObject: typing.Any, data: dict) -> bool:
		try:
			attributeValue = getattr(savingObject, self.AttributeName)
		except AttributeError:
			attributeValue = copy.deepcopy(self.Default)

		if self.Encoder is not None:
			data[self._savingKey] = self.Encoder(attributeValue)
		else:
			data[self._savingKey] = attributeValue

		return True

	def _ResetAttributeInternal (self, resettingObject: typing.Any) -> bool:
		copiedDefault = self.Default
		attributeName = self._attributeName  # type: str

		setattr(resettingObject, attributeName, copiedDefault)
		return True

class StaticSavableAttributeHandler(AttributeHandlerBase):
	"""
	An attribute handler for savable objects that should reused through every load and reset.
	"""

	def _LoadAttributeInternal (self, loadingObject: typing.Any, data: dict, lastVersion: typing.Optional[Version.Version]) -> bool:
		attributeName = self._attributeName  # type: str

		if not self._requiredAttribute:
			try:
				attributeData = data[self._savingKey]  # type: typing.Optional[dict]
			except KeyError:
				return True
		else:
			attributeData = data[self._savingKey]  # type: typing.Optional[dict]

		if not isinstance(attributeData, dict):
			raise Exceptions.IncorrectTypeException(attributeData, "data[%s]" % attributeName, (dict,))

		attributeValue = getattr(loadingObject, attributeName)

		if not isinstance(attributeValue, SavableExtension) and attributeValue is not None:
			raise Exceptions.IncorrectTypeException(attributeValue, "loadingObject." + attributeName, (SavableExtension, None))

		return attributeValue.LoadFromDictionary(attributeData)

	def _SaveAttributeInternal (self, savingObject: typing.Any, data: dict) -> bool:
		operationSuccessful = True  # type: bool
		attributeName = self._attributeName  # type: str

		attributeValue = getattr(savingObject, attributeName)

		if not isinstance(attributeValue, SavableExtension) and attributeValue is not None:
			raise Exceptions.IncorrectTypeException(attributeValue, "savingObject." + attributeName, (SavableExtension, None))

		attributeOperationSuccessful, attributeData = attributeValue.SaveToDictionary()  # type: bool, dict
		data[self._savingKey] = attributeData

		if not attributeOperationSuccessful:
			operationSuccessful = False

		return operationSuccessful

	def _ResetAttributeInternal (self, resettingObject: typing.Any) -> bool:
		attributeName = self._attributeName  # type: str

		attributeValue = getattr(resettingObject, attributeName)

		if not isinstance(attributeValue, SavableExtension) and attributeValue is not None:
			raise Exceptions.IncorrectTypeException(attributeValue, "resettingObject." + attributeName, (SavableExtension, None))

		return attributeValue.Reset()

class DynamicSavableAttributeHandler(AttributeHandlerBase):
	def __init__ (self,
				  savingKey: str,
				  attributeName: str,
				  savableCreator: typing.Callable,
				  defaultCreator: typing.Callable,
				  requiredSuccess: bool = True,
				  requiredAttribute: bool = False,
				  skipSaveTest: typing.Optional[typing.Callable] = None,
				  updater: typing.Optional[typing.Callable] = None,
				  nullable: bool = False,
				  multiType: bool = False,
				  typeFetcher: typing.Optional[typing.Callable[[typing.Any], str]] = None,
				  typeSavingKey: typing.Optional[str] = None):

		"""
		An attribute handler for savable objects that should be replaced through every load and reset.
		:param savingKey: The dictionary key the targeted attribute will be save to and loaded from.
		:type savingKey: str
		:param attributeName: The name of the target attribute.
		:type attributeName: str
		:param savableCreator: A function used to create this attribute when necessary. Normally, the function should take no arguments and return an object
		that inherits from the savable extension or None. The required parameters of the function may change when the 'multiType' parameter is true.
		:type savableCreator: typing.Callable[[], SavableExtension]
		:param defaultCreator: A function used to create this attribute's default value when resetting. The function should take no arguments
		and return an object that inherits from the savable extension or None.
		:type defaultCreator: typing.Callable[[], typing.Optional[SavableExtension]]
		:param requiredSuccess: Whether or not the attribute needs to be successfully loaded and saved. Exceptions raised when loading or saving will not be
		caught if True.
		:type requiredSuccess: bool
		:param requiredAttribute: Whether or not this attribute's save data needs to exist. Exceptions will be raised if the attribute's save data is not
		found when loading.
		:param skipSaveTest: A callable object used to determine if this attribute doesn't need to be saved. This should take no parameters and return
		true or false. This must be None if the 'requiredAttribute' parameter is true.
		:type skipSaveTest: typing.Optional[typing.Callable]
		:param: updater: A callable object used to bring old data from previous versions up to date. This should take the loading data
		dictionary and the last version as its two parameters. The last version can be None instead of a version object if no last version was specified.
		This parameter may be None if no updates are necessary for this attribute.
		:type updater: typing.Optional[typing.Callable]
		:param nullable: Whether or not it is acceptable for this attribute to be None instead of a savable object.
		:type nullable: bool
		:param multiType: Whether or not this attribute can be more than one type of savable object. If this is True, the savable creator
		must take an additional parameter, a string identifier indicating the type of object to be created.
		:type multiType: bool
		:param typeFetcher: A function used when saving to determine the type of object. The function should take one argument, the value of
		the attribute, and return a string denoting the input's type. This parameter cannot be None if the parameter 'multiType' is True.
		This function will not be called if the attribute is None.
		:type typeFetcher: typing.Optional[typing.Callable[[typing.Any], str]]
		:param typeSavingKey: The dictionary key the targeted attribute's type string will be save to and loaded from. This parameter
		cannot be None if the parameter 'multiType' is True.
		:type typeSavingKey: str
		"""

		if not isinstance(savableCreator, typing.Callable):
			raise Exceptions.IncorrectTypeException(savableCreator, "savableCreator", ("Callable",))

		if not isinstance(defaultCreator, typing.Callable):
			raise Exceptions.IncorrectTypeException(defaultCreator, "defaultCreator", ("Callable",))

		if not isinstance(nullable, bool):
			raise Exceptions.IncorrectTypeException(nullable, "nullable", (bool,))

		if not isinstance(multiType, bool):
			raise Exceptions.IncorrectTypeException(multiType, "multiType", (bool,))

		if not isinstance(typeFetcher, typing.Callable) and typeFetcher is not None:
			raise Exceptions.IncorrectTypeException(typeFetcher, "typeFetcher", ("Callable", None))

		if not isinstance(typeSavingKey, str) and typeSavingKey is not None:
			raise Exceptions.IncorrectTypeException(typeSavingKey, "typeSavingKey", (str, None))

		if multiType and (typeFetcher is None or typeSavingKey is None):
			raise ValueError("The parameters 'typeFetcher' and 'typeSavingKey' cannot be None if the parameter 'multiType' is True.")

		super().__init__(savingKey, attributeName, requiredSuccess = requiredSuccess, requiredAttribute = requiredAttribute, skipSaveTest = skipSaveTest, updater = updater)

		self._savableCreator = savableCreator  # type: typing.Callable
		self._defaultCreator = defaultCreator  # type: typing.Callable
		self._nullable = nullable  # type: bool

		self._multiType = multiType  # type: bool
		self._typeFetcher = typeFetcher  # type: typing.Optional[typing.Callable[[typing.Any], str]]
		self._typeSavingKey = typeSavingKey  # type: typing.Optional[str]

	def _LoadAttributeInternal (self, loadingObject: typing.Any, data: dict, lastVersion: typing.Optional[Version.Version]) -> bool:
		operationSuccessful = True  # type: bool
		attributeName = self._attributeName  # type: str

		if not self._requiredAttribute:
			try:
				attributeData = data[self._savingKey]  # type: typing.Optional[dict]
			except KeyError:
				return True
		else:
			attributeData = data[self._savingKey]  # type: typing.Optional[dict]

		if self._nullable:
			if not isinstance(attributeData, dict) and attributeData is not None:
				raise Exceptions.IncorrectTypeException(attributeData, "data[%s]" % attributeName, (dict, None))
		else:
			if not isinstance(attributeData, dict):
				raise Exceptions.IncorrectTypeException(attributeData, "data[%s]" % attributeName, (dict,))

		if attributeData is None:
			setattr(loadingObject, attributeName, None)
		else:
			if self._multiType:
				attributeTypeIdentifier = data[self._typeSavingKey]  # type: str

				if not isinstance(attributeTypeIdentifier, str):
					raise Exceptions.IncorrectTypeException(attributeTypeIdentifier, "data[%s]" % self._typeSavingKey, (str,))

				attributeValue = self._savableCreator(attributeTypeIdentifier)  # type: SavableExtension
			else:
				attributeValue = self._savableCreator()  # type: SavableExtension

			if not isinstance(attributeValue, SavableExtension):
				raise Exceptions.IncorrectReturnTypeException(attributeData, "savableCreator", (SavableExtension,))

			if not attributeValue.LoadFromDictionary(attributeData, lastVersion = lastVersion):
				operationSuccessful = False

			setattr(loadingObject, attributeName, attributeValue)

		return operationSuccessful

	def _SaveAttributeInternal (self, savingObject: typing.Any, data: dict) -> bool:
		operationSuccessful = True  # type: bool
		attributeName = self._attributeName  # type: str

		attributeValue = getattr(savingObject, attributeName)  # type: typing.Optional[SavableExtension]

		if self._nullable:
			if not isinstance(attributeValue, SavableExtension) and attributeValue is not None:
				raise Exceptions.IncorrectTypeException(attributeValue, "savingObject." + attributeName, (SavableExtension, None))
		else:
			if not isinstance(attributeValue, SavableExtension):
				raise Exceptions.IncorrectTypeException(attributeValue, "savingObject." + attributeName, (SavableExtension,))

		if attributeValue is None:
			data[self._savingKey] = None
		else:
			attributeOperationSuccessful, attributeData = attributeValue.SaveToDictionary()  # type: bool, dict

			if not attributeOperationSuccessful:
				operationSuccessful = False

			if self._multiType:
				attributeTypeIdentifier = self._typeFetcher(attributeValue)  # type: str

				if not isinstance(attributeTypeIdentifier, str):
					raise Exceptions.IncorrectReturnTypeException(attributeTypeIdentifier, "typeFetcher", (str,))

				data[self._typeSavingKey] = attributeTypeIdentifier

			data[self._savingKey] = attributeData

		return operationSuccessful

	def _ResetAttributeInternal (self, resettingObject: typing.Any) -> bool:
		attributeDefault = self._defaultCreator()
		attributeName = self._attributeName  # type: str

		if self._nullable:
			if not isinstance(attributeDefault, SavableExtension) and attributeDefault is not None:
				raise Exceptions.IncorrectReturnTypeException(attributeDefault, "defaultCreator", (SavableExtension, None))
		else:
			if not isinstance(attributeDefault, SavableExtension):
				raise Exceptions.IncorrectReturnTypeException(attributeDefault, "defaultCreator", (SavableExtension,))

		setattr(resettingObject, attributeName, attributeDefault)

		return True

class ListedSavableAttributeHandler(DynamicSavableAttributeHandler):
	def __init__ (self,
				  savingKey: str,
				  attributeName: str,
				  savableCreator: typing.Callable,
				  defaultCreator: typing.Callable,
				  requiredSuccess: bool = True,
				  requiredAttribute: bool = False,
				  requiredEntrySuccess: bool = True,
				  skipSaveTest: typing.Optional[typing.Callable] = None,
				  skipEntrySaveTest: typing.Optional[typing.Callable] = None,
				  updater: typing.Optional[typing.Callable] = None,
				  nullable: bool = False,
				  entriesNullable: bool = False,
				  multiType: bool = False,
				  typeFetcher: typing.Optional[typing.Callable[[typing.Any], str]] = None):

		"""
		An attribute handler for lists of savable objects.
		:param savingKey: The dictionary key the targeted attribute will be save to and loaded from.
		:type savingKey: str
		:param attributeName: The name of the target attribute.
		:type attributeName: str
		:param savableCreator: A function used to create this attribute's entries when necessary. The function should take no arguments and return
		an object that inherits from the savable extension or None.
		:type savableCreator: typing.Callable[[], SavableExtension]
		:param defaultCreator: A function used to create this attribute's default value when resetting. The function should take no arguments
		and return a list or None.
		:type defaultCreator: typing.Callable[[], list]
		:param requiredSuccess: The attribute will need to be successfully loaded and saved else the entire load or save operation will
		fall through. Exceptions raised when loading or saving will not be caught if True.
		:type requiredSuccess: bool
		:param requiredAttribute: A required attribute needs its save data to exist or the entire load operation will fall through.
		:type requiredAttribute: bool
		:param requiredEntrySuccess: If true, all list entries must load or save successfully or the entire load operation will fall through. Failures
		while loading and saving an entry would be caught as normal if the 'requiredSuccess' parameter is false.
		:type requiredEntrySuccess: bool
		:param skipSaveTest: A callable object used to determine if this attribute doesn't need to be saved. This should take no parameters and return
		true or false. This must be None if the 'requiredAttribute' parameter is true.
		:type skipSaveTest: typing.Optional[typing.Callable]
		:param skipEntrySaveTest: A callable object used to determine if an item of the saving list doesnt need doesn't need to be saved. This should
		take one parameter, the item being tested, and return true or false.
		:type skipEntrySaveTest: typing.Optional[typing.Callable]
		:param: updater: A callable object used to bring old data from previous versions up to date. This should take the loading data dictionary
		and the last version as its two parameters. The last version can be None instead of a version object if no last version was specified.
		This parameter may be None if no updates are necessary for this attribute.
		:type updater: typing.Optional[typing.Callable]
		:param nullable: Whether or not it is acceptable for this attribute to be None instead of a list.
		:type nullable: bool
		:param entriesNullable: Whether or not it is acceptable for an entry in this list to by None instead of a savable object.
		:type entriesNullable: bool
		:param multiType: Whether or not an entry of this attribute can be more than one type of savable object. If this is True, the savable creator
		must take an additional parameter, a string identifier indicating the type of object to be created.
		:type multiType: bool
		:param typeFetcher: A function used when saving to determine the type of object. The function should take one argument, an entry of
		the attribute, and return a string denoting the input's type. This parameter cannot be None if the parameter 'multiType' is True.
		This function will not be called if the attribute entry is None.
		:type typeFetcher: typing.Optional[typing.Callable[[typing.Any], str]]
		"""

		if not isinstance(entriesNullable, bool):
			raise Exceptions.IncorrectTypeException(entriesNullable, "entriesNullable", (bool,))

		super().__init__(savingKey, attributeName, savableCreator, defaultCreator, requiredSuccess = requiredSuccess, requiredAttribute = requiredAttribute, skipSaveTest = skipSaveTest, updater = updater, nullable = nullable, multiType = multiType, typeFetcher = typeFetcher, typeSavingKey = "Type")

		self._dataSavingKey = "Data"  # type: str

		self._requiredEntrySuccess = requiredEntrySuccess  # type: bool
		self._entriesNullable = entriesNullable  # type: bool
		self._skipEntrySaveTest = skipEntrySaveTest  # type: typing.Optional[typing.Callable]

	def _LoadAttributeInternal (self, loadingObject: typing.Any, data: dict, lastVersion: typing.Optional[Version.Version]) -> bool:
		operationSuccessful = True  # type: bool
		operationInformation = loadingObject.SavableOperationInformation  # type: str
		attributeName = self._attributeName  # type: str

		if not self._requiredAttribute:
			try:
				attributeListData = data[self._savingKey]  # type: typing.Optional[list]
			except KeyError:
				return True
		else:
			attributeListData = data[self._savingKey]  # type: typing.Optional[list]

		if self._nullable:
			if not isinstance(attributeListData, list) and attributeListData is not None:
				raise Exceptions.IncorrectTypeException(attributeListData, "data[%s]" % attributeName, (list, None))
		else:
			if not isinstance(attributeListData, list):
				raise Exceptions.IncorrectTypeException(attributeListData, "data[%s]" % attributeName, (list,))

		if attributeListData is None:
			setattr(loadingObject, attributeName, None)
		else:
			attributeValue = list()  # type: typing.List[typing.Optional[SavableExtension]]

			for entryDataIndex in range(len(attributeListData)):  # type: int
				try:
					entryContainerData = attributeListData[entryDataIndex]  # type: dict

					if not isinstance(entryContainerData, dict):
						raise Exceptions.IncorrectTypeException(entryContainerData, "data[%s][%s]" % (attributeName, entryDataIndex), (dict,))

					entryData = entryContainerData[self._dataSavingKey]  # type: typing.Optional[dict]

					if self._nullable:
						if not isinstance(entryData, dict) and entryData is not None:
							raise Exceptions.IncorrectTypeException(entryData, "data[%s][%s][%s]" % (attributeName, entryDataIndex, self._dataSavingKey), (dict, None))
					else:
						if not isinstance(entryData, dict):
							raise Exceptions.IncorrectTypeException(entryData, "data[%s][%s][%s]" % (attributeName, entryDataIndex, self._dataSavingKey), (dict,))

					if entryData is None:
						attributeValue.append(None)
					else:
						if self._multiType:
							entryTypeIdentifier = entryContainerData[self._typeSavingKey]  # type: str

							if not isinstance(entryTypeIdentifier, str):
								raise Exceptions.IncorrectTypeException(entryTypeIdentifier, "data[%s][%s][%s]" % (attributeName, entryDataIndex, self._typeSavingKey), (str,))

							entryValue = self._savableCreator(entryTypeIdentifier)  # type: SavableExtension
						else:
							entryValue = self._savableCreator()  # type: SavableExtension

						if not isinstance(entryValue, SavableExtension):
							raise Exceptions.IncorrectReturnTypeException(entryValue, "savableCreator", (SavableExtension,))

						if not entryValue.LoadFromDictionary(entryData, lastVersion = lastVersion):
							operationSuccessful = False

						attributeValue.append(entryValue)
				except Exception as e:
					if self._requiredEntrySuccess:
						raise
					else:
						Debug.Log("Load operation in a savable object failed to load entry %s of the savable list attribute '%s'.\n%s" % (entryDataIndex, self._attributeName, operationInformation), loadingObject.HostNamespace, Debug.LogLevels.Warning, group = loadingObject.HostNamespace, owner = __name__)
						operationSuccessful = False

			setattr(loadingObject, attributeName, attributeValue)

		return operationSuccessful

	def _SaveAttributeInternal (self, savingObject: typing.Any, data: dict) -> bool:
		operationSuccessful = True  # type: bool
		operationInformation = savingObject.SavableOperationInformation  # type: str
		attributeName = self._attributeName  # type: str

		attributeValue = getattr(savingObject, attributeName)  # type: typing.Optional[list]

		if self._nullable:
			if not isinstance(attributeValue, list) and attributeValue is not None:
				raise Exceptions.IncorrectTypeException(attributeValue, "savingObject." + attributeName, (list, None))
		else:
			if not isinstance(attributeValue, list):
				raise Exceptions.IncorrectTypeException(attributeValue, "savingObject." + attributeName, (list,))

		if attributeValue is None:
			data[self._savingKey] = None
		else:
			attributeData = list()  # type: typing.List[typing.Optional[dict]]

			for entryIndex in range(len(attributeValue)):  # type: int
				try:
					entryValue = attributeValue[entryIndex]  # type: typing.Optional[SavableExtension]

					if self._skipEntrySaveTest is not None:
						if self._skipEntrySaveTest(entryValue):
							continue

					if self._nullable:
						if not isinstance(entryValue, SavableExtension) and entryValue is not None:
							raise Exceptions.IncorrectTypeException(entryValue, "savingObject.%s[%s]" % (attributeName, entryIndex), (SavableExtension, None))
					else:
						if not isinstance(entryValue, SavableExtension):
							raise Exceptions.IncorrectTypeException(entryValue, "savingObject.%s[%s]" % (attributeName, entryIndex), (SavableExtension,))

					if entryValue is None:
						attributeData.append(None)
					else:
						entryContainerData = dict()  # type: dict
						entryOperationSuccessful, entryData = entryValue.SaveToDictionary()  # type: bool, dict

						if not entryOperationSuccessful:
							operationSuccessful = False

						if self._multiType:
							entryTypeIdentifier = self._typeFetcher(entryValue)  # type: str

							if not isinstance(entryTypeIdentifier, str):
								raise Exceptions.IncorrectReturnTypeException(entryTypeIdentifier, "typeFetcher", (str,))

							entryContainerData[self._typeSavingKey] = entryTypeIdentifier

						entryContainerData[self._dataSavingKey] = entryData
						attributeData.append(entryContainerData)
				except Exception as e:
					if self._requiredEntrySuccess:
						raise
					else:
						Debug.Log("Save operation in a savable object failed to save entry %s of the savable list attribute '%s'.\n%s" % (entryIndex, self._attributeName, operationInformation), savingObject.HostNamespace, Debug.LogLevels.Warning, group = savingObject.HostNamespace, owner = __name__)
						operationSuccessful = False


			data[self._savingKey] = attributeData

		return operationSuccessful

	def _ResetAttributeInternal (self, resettingObject: typing.Any) -> bool:
		attributeDefault = self._defaultCreator()
		attributeName = self._attributeName  # type: str

		if self._nullable:
			if not isinstance(attributeDefault, list) and attributeDefault is not None:
				raise Exceptions.IncorrectReturnTypeException(attributeDefault, "defaultCreator", (list, None))
		else:
			if not isinstance(attributeDefault, list):
				raise Exceptions.IncorrectReturnTypeException(attributeDefault, "defaultCreator", (list,))

		setattr(resettingObject, attributeName, attributeDefault)

		return True
