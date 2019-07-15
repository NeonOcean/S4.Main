import typing

import services
import zone
from NeonOcean.Main import Debug, Director, Language, LoadingShared, This, Events, Mods
from NeonOcean.Main.Saving import Shared
from NeonOcean.Main.Tools import Exceptions, Patcher
from NeonOcean.Main.UI import Notifications
from protocolbuffers import FileSerialization_pb2
from server import client
from server_commands import persistence_commands
from sims4 import commands
from ui import ui_dialog_notification

class SaveHandler:
	Host = This.Mod

	FailureNotificationsTitle = Language.String(This.Mod.Namespace + ".System.Saving.Failure_Notifications.Title")  # type: Language.String
	FailureNotificationsLoadText = Language.String(This.Mod.Namespace + ".System.Saving.Failure_Notifications.Load_Text")  # type: Language.String
	FailureNotificationsSaveText = Language.String(This.Mod.Namespace + ".System.Saving.Failure_Notifications.Save_Text")  # type: Language.String
	FailureNotificationsUnloadText = Language.String(This.Mod.Namespace + ".System.Saving.Failure_Notifications.Unload_Text")  # type: Language.String

	WarningNotificationsTitle = Language.String(This.Mod.Namespace + ".System.Saving.Warning_Notifications.Title")  # type: Language.String
	WarningNotificationsMismatchText = Language.String(This.Mod.Namespace + ".System.Saving.Warning_Notifications.Mismatch_Text")  # type: Language.String

	_savingObjects = list()  # type: typing.List[Shared.SaveBase]
	_commitNextSave = False  # type: bool

	@classmethod
	def LoadAll (cls, saveSlotID: int) -> None:
		"""
		Load the file specified by the inputs for each saving object.
		:param saveSlotID: The save slot id of the game's loaded save file.
		:type saveSlotID: int
		"""

		Debug.Log("Loading %s saving object(s)." % len(cls._savingObjects), cls.Host.Namespace, Debug.LogLevels.Info, group = cls.Host.Namespace, owner = __name__)

		failedSavingIdentifiers = list()  # type: typing.List[str]
		mismatchSavingIdentifiers = list()  # type: typing.List[str]

		for savingObject in cls._savingObjects:  # type: Shared.SaveBase
			try:
				if not savingObject.Enabled:
					continue

				loadSuccessful = savingObject.Load(saveSlotID)  # type: bool
			except Exception:
				Debug.Log("Encountered an unhandled exception upon loading a saving object with the identifier '" + savingObject.Identifier + "'.", cls.Host.Namespace, Debug.LogLevels.Exception, group = cls.Host.Namespace, owner = __name__)
				loadSuccessful = False
				failedSavingIdentifiers.append(savingObject.Identifier)

			if not loadSuccessful:
				failedSavingIdentifiers.append(savingObject.Identifier)

			if loadSuccessful:
				if savingObject.DataGUID is None:
					continue

				gameSaveGUID = services.get_persistence_service().get_save_slot_proto_guid()  # type: int

				if savingObject.DataGUID != gameSaveGUID:
					mismatchSavingIdentifiers.append(savingObject.Identifier)

		if len(failedSavingIdentifiers) != 0:
			cls._ShowLoadFailureDialog(failedSavingIdentifiers)

		if len(mismatchSavingIdentifiers) != 0:
			cls._ShowMismatchWarningDialog(mismatchSavingIdentifiers)

		Debug.Log("Finished loading %s saving object(s) and encountered %s error(s)." % (len(cls._savingObjects), str(len(failedSavingIdentifiers))), cls.Host.Namespace, Debug.LogLevels.Info, group = cls.Host.Namespace, owner = __name__)

	@classmethod
	def SaveAll (cls, saveSlotID: int = None) -> None:
		"""
		Save every registered and enabled saving object's data to their active save files.

		:param saveSlotID: The save slot id this is suppose to saved to. If the slot id is None the current slot id will be used.
		:type saveSlotID: int | None
		"""

		commitNextSave = cls._commitNextSave  # type: bool
		cls._commitNextSave = False

		if commitNextSave:
			Debug.Log("Saving and committing %s saving object(s)." % len(cls._savingObjects), cls.Host.Namespace, Debug.LogLevels.Info, group = cls.Host.Namespace, owner = __name__)
		else:
			Debug.Log("Saving %s saving object(s)." % len(cls._savingObjects), cls.Host.Namespace, Debug.LogLevels.Info, group = cls.Host.Namespace, owner = __name__)

		if not isinstance(saveSlotID, int):
			raise Exceptions.IncorrectTypeException(saveSlotID, "saveSlotID", (int,))

		failedSavingIdentifiers = list()  # type: typing.List[str]

		for savingObject in cls._savingObjects:  # type: Shared.SaveBase
			try:
				if not savingObject.Enabled:
					continue

				if not savingObject.Loaded:
					Debug.Log("Went to save a saving object with the identifier '" + savingObject.Identifier + "' but it wasn't loaded.", cls.Host.Namespace, Debug.LogLevels.Warning, group = cls.Host.Namespace, owner = __name__)
					continue

				savingObject.Save(saveSlotID = saveSlotID, commitSave = commitNextSave)  # type: bool
			except Exception:
				Debug.Log("Encountered an unhandled exception upon saving a saving object with the identifier '" + savingObject.Identifier + "'.", cls.Host.Namespace, Debug.LogLevels.Exception, group = cls.Host.Namespace, owner = __name__)
				failedSavingIdentifiers.append(savingObject.Identifier)

		if len(failedSavingIdentifiers) != 0:
			cls._ShowSaveFailureDialog(failedSavingIdentifiers)

		Debug.Log("Finished saving %s saving object(s) and encountered %s error(s)." % (len(cls._savingObjects), str(len(failedSavingIdentifiers))), cls.Host.Namespace, Debug.LogLevels.Info, group = cls.Host.Namespace, owner = __name__)

	@classmethod
	def CommitNextSave (cls) -> None:
		"""
		Setup this handler to commit the next save. Save file commits should typically occur when the game does the same.
		"""

		cls._commitNextSave = True

	@classmethod
	def UnloadAll (cls) -> None:
		"""
		Unload every registered and loaded saving object.
		"""

		Debug.Log("Unloading %s saving object(s)." % len(cls._savingObjects), cls.Host.Namespace, Debug.LogLevels.Info, group = cls.Host.Namespace, owner = __name__)

		failedSavingIdentifiers = list()  # type: typing.List[str]

		for savingObject in cls._savingObjects:  # type: Shared.SaveBase
			try:
				if not savingObject.Loaded:
					continue

				savingObject.Unload()  # type: bool
			except Exception:
				Debug.Log("Encountered an unhandled exception upon unloading a saving object with the identifier '" + savingObject.Identifier + "'.", cls.Host.Namespace, Debug.LogLevels.Exception, group = cls.Host.Namespace, owner = __name__)
				failedSavingIdentifiers.append(savingObject.Identifier)

		if len(failedSavingIdentifiers) != 0:
			cls._ShowUnloadFailureDialog(failedSavingIdentifiers)

		Debug.Log("Finished unloading %s saving object(s) and encountered %s error(s)." % (len(cls._savingObjects), str(len(failedSavingIdentifiers))), cls.Host.Namespace, Debug.LogLevels.Info, group = cls.Host.Namespace, owner = __name__)
	
	@classmethod
	def UnloadWithHost (cls, host: Mods.Mod) -> None:
		"""
		Unload all registered and loaded saving objects with the specified host
		"""

		Debug.Log("Unloading all saving objects from the host '%s'" % host.Namespace, cls.Host.Namespace, Debug.LogLevels.Info, group = cls.Host.Namespace, owner = __name__)

		failedSavingIdentifiers = list()  # type: typing.List[str]

		for savingObject in cls._savingObjects:  # type: Shared.SaveBase
			try:
				if not savingObject.Host == host:
					continue

				if not savingObject.Loaded:
					continue

				savingObject.Unload()  # type: bool
			except Exception:
				Debug.Log("Encountered an unhandled exception upon unloading a saving object with the identifier '" + savingObject.Identifier + "'.", cls.Host.Namespace, Debug.LogLevels.Exception, group = cls.Host.Namespace, owner = __name__)
				failedSavingIdentifiers.append(savingObject.Identifier)

		if len(failedSavingIdentifiers) != 0:
			cls._ShowUnloadFailureDialog(failedSavingIdentifiers)

		Debug.Log("Finished unloading all saving object from the host '%s' and encountered %s error(s)." % (host.Namespace, str(len(failedSavingIdentifiers))), cls.Host.Namespace, Debug.LogLevels.Info, group = cls.Host.Namespace, owner = __name__)
	
	@classmethod
	def UnloadAllCompletely (cls) -> None:
		"""
		Unload every registered and loaded saving object in necessary and prepare it to load a different save file.
		"""

		for savingObject in cls._savingObjects:  # type: Shared.SaveBase
			try:
				savingObject.UnloadCompletely()
			except Exception:
				Debug.Log("Encountered an unhandled exception upon completely unloaded a saving object with the identifier '" + savingObject.Identifier + "'.", cls.Host.Namespace, Debug.LogLevels.Exception, group = cls.Host.Namespace, owner = __name__)

	@classmethod
	def RegisterSavingObject (cls, savingObject: Shared.SaveBase) -> None:
		if savingObject in cls._savingObjects:
			return

		cls._savingObjects.append(savingObject)

	@classmethod
	def UnregisterSavingObject (cls, savingObject: Shared.SaveBase) -> None:
		cls._savingObjects.remove(savingObject)

	@classmethod
	def _ShowLoadFailureDialog (cls, savingIdentifiers: typing.List[str]) -> None:
		identifiersText = "\n".join(savingIdentifiers)

		notificationArguments = {
			"title": cls.FailureNotificationsTitle.GetCallableLocalizationString(),
			"text": cls.FailureNotificationsLoadText.GetCallableLocalizationString(identifiersText),
			"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
			"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
		}  # type: typing.Dict[str, typing.Any]

		Notifications.ShowNotification(queue = True, **notificationArguments)

	@classmethod
	def _ShowSaveFailureDialog (cls, savingIdentifiers: typing.List[str]) -> None:
		identifiersText = "\n".join(savingIdentifiers)

		notificationArguments = {
			"title": cls.FailureNotificationsTitle.GetCallableLocalizationString(),
			"text": cls.FailureNotificationsSaveText.GetCallableLocalizationString(identifiersText),
			"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
			"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
		}  # type: typing.Dict[str, typing.Any]

		Notifications.ShowNotification(queue = True, **notificationArguments)

	@classmethod
	def _ShowUnloadFailureDialog (cls, savingIdentifiers: typing.List[str]) -> None:
		identifiersText = "\n".join(savingIdentifiers)

		notificationArguments = {
			"title": cls.FailureNotificationsTitle.GetCallableLocalizationString(),
			"text": cls.FailureNotificationsUnloadText.GetCallableLocalizationString(identifiersText),
			"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
			"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
		}  # type: typing.Dict[str, typing.Any]

		Notifications.ShowNotification(queue = True, **notificationArguments)

	@classmethod
	def _ShowMismatchWarningDialog (cls, savingIdentifiers: typing.List[str]) -> None:
		identifiersText = "\n".join(savingIdentifiers)

		notificationArguments = {
			"title": cls.WarningNotificationsTitle.GetCallableLocalizationString(),
			"text": cls.WarningNotificationsMismatchText.GetCallableLocalizationString(identifiersText),
			"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
			"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
		}  # type: typing.Dict[str, typing.Any]

		Notifications.ShowNotification(queue = True, **notificationArguments)

class _Announcer(Director.Announcer):
	Level = -10

	@classmethod
	def OnEnterMainMenu (cls) -> None:
		SaveHandler.UnloadAllCompletely()

	@classmethod
	def ZoneLoad (cls, zoneReference: zone.Zone) -> None:
		slotID = services.get_persistence_service().get_save_slot_proto_buff().slot_id  # type: int
		SaveHandler.LoadAll(slotID)

	@classmethod
	def ZoneSave (cls, zoneReference: zone.Zone, saveSlotData: typing.Optional[FileSerialization_pb2.SaveSlotData] = None) -> None:
		SaveHandler.SaveAll(saveSlotID = saveSlotData.slot_id)

	@classmethod
	def ZoneOnToreDown (cls, zoneReference: zone.Zone, clientReference: client.Client):
		SaveHandler.UnloadAll()

# noinspection SpellCheckingInspection, PyUnusedLocal
def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	Patcher.Patch(persistence_commands, "override_save_slot", _SaveOverrideSlot)
	commands.Command("persistence.override_save_slot", command_type = commands.CommandType.Live)(persistence_commands.override_save_slot)

	Patcher.Patch(persistence_commands, "save_to_new_slot", _SaveNewSlot)
	commands.Command("persistence.save_to_new_slot", command_type = commands.CommandType.Live)(persistence_commands.save_to_new_slot)

	Patcher.Patch(persistence_commands, "save_game_with_autosave", _SaveGameAuto)
	commands.Command("persistence.save_game_with_autosave", command_type = commands.CommandType.Live)(persistence_commands.save_game_with_autosave)

# noinspection PyUnusedLocal
def _OnStop (cause: LoadingShared.LoadingCauses) -> None:
	SaveHandler.UnloadAllCompletely()

def _OnModUnloaded (mod: Mods.Mod, exiting: bool) -> None:
	if exiting:
		return

	SaveHandler.UnloadWithHost(mod)

# noinspection PyUnusedLocal
def _SaveOverrideSlot (*args, **kwargs) -> None:
	# The game doesn't seem to actually use the override_save_slot and save_to_new_slot commands, which is annoying as it would be pretty useful otherwise.
	# We still patch the commands just in case.
	SaveHandler.CommitNextSave()

# noinspection PyUnusedLocal
def _SaveNewSlot (*args, **kwargs) -> None:
	SaveHandler.CommitNextSave()

# noinspection PyUnusedLocal
def _SaveGameAuto (*args, **kwargs) -> None:
	SaveHandler.CommitNextSave()

Events.RegisterOnModUnload(_OnModUnloaded, 0)