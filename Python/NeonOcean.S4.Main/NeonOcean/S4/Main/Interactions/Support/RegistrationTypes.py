from __future__ import annotations

import time
import typing

import services
import tag
import zone
from NeonOcean.S4.Main import Debug, Director, Mods, This
from NeonOcean.S4.Main.Tools import Exceptions, Python
from objects import definition, definition_manager, script_object
from sims4 import resources

RegistrationTagSetAttributeName = "NeonOceanRegistrationCachedTagSet"  # type: str

_computerTag = tag.Tag("Func_Computer")  # type: tag.Tag
_mailboxTag = tag.Tag("Func_Mailbox")  # type: tag.Tag
_singleBedTag = tag.Tag("Func_SingleBed")  # type: tag.Tag
_doubleBedTag = tag.Tag("Func_DoubleBed")  # type: tag.Tag
_toiletTag = tag.Tag("Func_Toilet")  # type: tag.Tag

class ObjectTypeOrganizer:
	Host = This.Mod  # type: Mods.Mod

	_typeDeterminers = dict()  # type: typing.Dict[str, typing.Callable]

	_objectsByType = dict()  # type: typing.Dict[str, typing.Set[typing.Type[script_object.ScriptObject]]]
	_objectTypesDetermined = False  # type: bool

	def __init_subclass__ (cls, *args, **kwargs):
		cls._typeDeterminers = dict()

		cls._objectsByType = dict()

	@classmethod
	def HasDeterminerForType (cls, typeIdentifier: str) -> bool:
		"""
		Whether or not the a determiner for this type exists.
		"""

		return typeIdentifier in cls._typeDeterminers

	@classmethod
	def RegisterTypeDeterminer (cls, typeIdentifier: str, typeDeterminer: typing.Callable) -> None:
		"""
		Register a method to determine the type of an object.
		:param typeIdentifier: The type identifier, used to signal to interactions what type of object it is.
		:type typeIdentifier: str
		:param typeDeterminer: A type determiner, this should take a object tuned class and return a boolean indicating whether or not it is of that type.
		:type typeDeterminer: typing.Callable
		"""

		if not isinstance(typeDeterminer, typing.Callable):
			raise Exceptions.IncorrectTypeException(typeDeterminer, "typeDeterminer", ("Callable",))

		if not isinstance(typeIdentifier, str):
			raise Exceptions.IncorrectTypeException(typeIdentifier, "typeIdentifier", (str,))

		cls._typeDeterminers[typeIdentifier] = typeDeterminer

	@classmethod
	def ObjectTypesDetermined (cls) -> bool:
		"""
		Whether or not the type of every object has been determined yet.
		"""

		return cls._objectTypesDetermined

	@classmethod
	def GetObjectsByType (cls) -> typing.Dict[str, typing.Set[typing.Type[script_object.ScriptObject]]]:
		"""
		Get a dictionary of object types connected to lists of every object that matches that type.
		"""

		if not cls._objectTypesDetermined:
			cls.DetermineAllObjectTypes()

		return dict(cls._objectsByType)

	@classmethod
	def DetermineAllObjectTypes (cls) -> None:
		operationStartTime = time.time()  # type: float

		cls._objectsByType = dict()  # type: typing.Dict[str, typing.Set[typing.Type[script_object.ScriptObject]]]

		# noinspection PyProtectedMember
		objectManager = services.get_instance_manager(resources.Types.OBJECT)  # type: definition_manager.DefinitionManager
		objectDefinitions = objectManager.loaded_definitions

		for typeIdentifier, typeDeterminer in cls._typeDeterminers.items():  # type: str, typing.Callable
			matchingObjects = set()  # type: typing.Set[typing.Type[script_object.ScriptObject]]

			for objectDefinition in objectDefinitions:  # type: typing.Any, definition.Definition
				matchingType = False  # type: bool

				try:
					matchingType = typeDeterminer(objectDefinition)
				except:
					Debug.Log("Type determiner failed to determine if an object definition matches the type identifier '" + typeIdentifier + "'.\nObject Definition ID:" + str(objectDefinition.id),
							  cls.Host.Namespace, Debug.LogLevels.Exception, group = cls.Host.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = typeDeterminer)

				if matchingType:
					matchingObjects.add(objectDefinition.cls)

			cls._objectsByType[typeIdentifier] = matchingObjects

		operationTime = time.time() - operationStartTime
		cls._objectTypesDetermined = True
		Debug.Log("Finished organizing all objects by type in %s seconds with %s type determiners and %s object definitions existing." % (operationTime, len(cls._typeDeterminers), len(objectDefinitions)), cls.Host.Namespace, Debug.LogLevels.Info, group = cls.Host.Namespace, owner = __name__)

class _Announcer(Director.Announcer):
	Host = This.Mod

	_priority = 4000  # type: int

	_zoneStartServicesTriggered = False  # type: bool

	@classmethod
	def ZoneStartServices(cls, zoneReference: zone.Zone, gameplayZoneData: typing.Any, saveSlotData: typing.Any) -> None:
		if not cls._zoneStartServicesTriggered and not ObjectTypeOrganizer.ObjectTypesDetermined():
			ObjectTypeOrganizer.DetermineAllObjectTypes()
			cls._zoneStartServicesTriggered = True

def _Setup () -> None:
	ObjectTypeOrganizer.RegisterTypeDeterminer("Everything", _EverythingDeterminer)
	ObjectTypeOrganizer.RegisterTypeDeterminer("Terrain", _TerrainDeterminer)
	ObjectTypeOrganizer.RegisterTypeDeterminer("Humans", _HumansDeterminer)
	ObjectTypeOrganizer.RegisterTypeDeterminer("HumanBabies", _HumanBabiesDeterminer)
	ObjectTypeOrganizer.RegisterTypeDeterminer("Dogs", _DogsDeterminer)
	ObjectTypeOrganizer.RegisterTypeDeterminer("SmallDogs", _SmallDogsDeterminer)
	ObjectTypeOrganizer.RegisterTypeDeterminer("Cats", _CatsDeterminer)
	ObjectTypeOrganizer.RegisterTypeDeterminer("Computers", _ComputerDeterminer)
	ObjectTypeOrganizer.RegisterTypeDeterminer("Mailboxes", _MailBoxDeterminer)
	ObjectTypeOrganizer.RegisterTypeDeterminer("SingleBeds", _SingleBedDeterminer)
	ObjectTypeOrganizer.RegisterTypeDeterminer("DoubleBeds", _DoubleBedDeterminer)
	ObjectTypeOrganizer.RegisterTypeDeterminer("Toilets", _ToiletDeterminer)
	ObjectTypeOrganizer.RegisterTypeDeterminer("ToiletStalls", _ToiletStallDeterminer)

def _GetOrCreateObjectDefinitionTagSet (objectDefinition: definition.Definition) -> typing.Set[tag.Tag]:
	objectDefinitionTags = getattr(objectDefinition, RegistrationTagSetAttributeName, None)  # type: typing.Optional[typing.Set[tag.Tag]]

	if objectDefinitionTags is None:
		objectDefinitionTags = set(objectDefinition.build_buy_tags)  # type: typing.Set[tag.Tag]

	return objectDefinitionTags

# noinspection PyUnusedLocal
def _EverythingDeterminer (objectDefinition: definition.Definition) -> bool:
	return True

# noinspection PyUnusedLocal
def _TerrainDeterminer (objectDefinition: definition.Definition) -> bool:
	return objectDefinition.cls.guid64 == 14982

# noinspection PyUnusedLocal
def _HumansDeterminer (objectDefinition: definition.Definition) -> bool:
	return objectDefinition.cls.guid64 == 14965

# noinspection PyUnusedLocal
def _HumanBabiesDeterminer (objectDefinition: definition.Definition) -> bool:
	return objectDefinition.cls.guid64 == 14826

# noinspection PyUnusedLocal
def _DogsDeterminer (objectDefinition: definition.Definition) -> bool:
	return objectDefinition.cls.guid64 == 120620

# noinspection PyUnusedLocal
def _SmallDogsDeterminer (objectDefinition: definition.Definition) -> bool:
	return objectDefinition.cls.guid64 == 174619

# noinspection PyUnusedLocal
def _CatsDeterminer (objectDefinition: definition.Definition) -> bool:
	return objectDefinition.cls.guid64 == 120621

# noinspection PyUnusedLocal
def _ComputerDeterminer (objectDefinition: definition.Definition) -> bool:
	objectDefinitionTags = _GetOrCreateObjectDefinitionTagSet(objectDefinition)  # type: typing.Set[tag.Tag]
	return _computerTag in objectDefinitionTags

def _MailBoxDeterminer (objectDefinition: definition.Definition) -> bool:
	objectDefinitionTags = _GetOrCreateObjectDefinitionTagSet(objectDefinition)  # type: typing.Set[tag.Tag]
	return _mailboxTag in objectDefinitionTags

def _SingleBedDeterminer (objectDefinition: definition.Definition) -> bool:
	objectDefinitionTags = _GetOrCreateObjectDefinitionTagSet(objectDefinition)  # type: typing.Set[tag.Tag]
	return _singleBedTag in objectDefinitionTags

def _DoubleBedDeterminer (objectDefinition: definition.Definition) -> bool:
	objectDefinitionTags = _GetOrCreateObjectDefinitionTagSet(objectDefinition)  # type: typing.Set[tag.Tag]
	return _doubleBedTag in objectDefinitionTags

def _ToiletDeterminer (objectDefinition: definition.Definition) -> bool:
	objectDefinitionTags = _GetOrCreateObjectDefinitionTagSet(objectDefinition)  # type: typing.Set[tag.Tag]

	if not _toiletTag in objectDefinitionTags:
		return False

	# noinspection PyProtectedMember
	objectInteractions = objectDefinition.cls._super_affordances

	invalidInteractions = {
		214054, # Toilet stall use sitting interaction
		214055,  # Toilet stall use standing interaction
		144848  # Toddler chair use interaction
	}

	for objectInteraction in objectInteractions:
		if getattr(objectInteraction, "guid64", 0) in invalidInteractions:
			return False

	return True

def _ToiletStallDeterminer (objectDefinition: definition.Definition) -> bool:
	objectDefinitionTags = _GetOrCreateObjectDefinitionTagSet(objectDefinition)  # type: typing.Set[tag.Tag]

	if not _toiletTag in objectDefinitionTags:
		return False

	# noinspection PyProtectedMember
	objectInteractions = objectDefinition.cls._super_affordances

	invalidInteractions = {
		14427,  # Toilet use sitting interaction
		14428,  # Toilet use standing interaction
		144848  # Toddler chair use interaction
	}

	for objectInteraction in objectInteractions:
		if getattr(objectInteraction, "guid64", 0) in invalidInteractions:
			return False

	return True

_Setup()
