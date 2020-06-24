from __future__ import annotations

import datetime
import os
import typing

import services
import zone
from NeonOcean.S4.Main import Debug, Director, LoadingEvents, LoadingShared, This
from NeonOcean.S4.Main.Saving import Save, SaveShared
from NeonOcean.S4.Main.Tools import Patcher
from server import client
from server_commands import persistence_commands
from sims4 import commands

_commitNextSave = False  # type: bool

class _AnnouncerPreemptive(Director.Announcer):
	Host = This.Mod
	Preemptive = True

	_priority = 50

	@classmethod
	def OnEnterMainMenu (cls) -> None:
		Save.PrepareForSaveChange()

	@classmethod
	def ZoneOnToreDown (cls, zoneReference: zone.Zone, clientReference: client.Client):
		Save.UnloadAll()

class _Announcer(Director.Announcer):
	Host = This.Mod

	_priority = 50

	@classmethod
	def ZoneLoad (cls, zoneReference: zone.Zone) -> None:
		slotID = services.get_persistence_service().get_save_slot_proto_buff().slot_id  # type: int
		Save.Load(slotID)

	@classmethod
	def ZoneSave (cls, zoneReference: zone.Zone, saveSlotData: typing.Optional[typing.Any] = None) -> None:
		global _commitNextSave
		commitSave = _commitNextSave  # type: bool
		_commitNextSave = False

		if saveSlotData is None:
			return

		doOverrideBackupCommit = False  # type: bool

		try:
			if commitSave:
				gameSaveFilePath = SaveShared.GetGameSaveFilePath(saveSlotData.slot_id)  # type: str

				loadedSlotID = Save.GetLoadedSlotID()  # type: typing.Optional[int]

				if loadedSlotID is not None:
					overridingSave = loadedSlotID != saveSlotData.slot_id and os.path.exists(gameSaveFilePath)  # type: bool

					if overridingSave:
						gameSaveModifiedTime = datetime.datetime.fromtimestamp(os.path.getmtime(gameSaveFilePath))  # type: datetime.datetime
						overrideBackupMargin = datetime.timedelta(seconds = 3)

						if datetime.datetime.now() - overrideBackupMargin <= gameSaveModifiedTime:
							doOverrideBackupCommit = True
		except:
			Debug.Log("Failed to check if an override backup commit occurred.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

		if doOverrideBackupCommit:
			Save.DoOverrideBackupCommit(saveSlotData.slot_id)

		Save.Save(saveSlotID = saveSlotData.slot_id, commitSave = commitSave)

def _Setup () -> None:
	LoadingEvents.ModUnloadedEvent += _OnModUnloaded

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
	Save.PrepareForSaveChange()

def _GetSlotIDString (slotID: int) -> str:
	if slotID < 0:
		raise ValueError("Slot id cannot be less than zero.")

	slotIDHex = "{:x}".format(slotID)  # type: str
	return ("0" * (8 - len(slotIDHex))) + slotIDHex

# noinspection PyUnusedLocal
def _OnModUnloaded (owner: typing.Any, eventArguments: typing.Optional[LoadingEvents.ModUnloadedEventArguments]) -> None:
	if eventArguments.Exiting:
		return

	Save.UnloadWithHost(eventArguments.Mod)

# noinspection PyUnusedLocal
def _SaveOverrideSlot (*args, **kwargs) -> None:
	# The game doesn't seem to actually use the override_save_slot and save_to_new_slot commands, which is annoying as it would be pretty useful otherwise.
	# We still patch the commands just in case.

	global _commitNextSave
	_commitNextSave = True

# noinspection PyUnusedLocal
def _SaveNewSlot (*args, **kwargs) -> None:
	global _commitNextSave
	_commitNextSave = True

# noinspection PyUnusedLocal
def _SaveGameAuto (*args, **kwargs) -> None:
	global _commitNextSave
	_commitNextSave = True

_Setup()
