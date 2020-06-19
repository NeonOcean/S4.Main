from __future__ import annotations

import abc
import codecs
import enum_lib
import json
import os
import random
import threading
import typing
from http import client
from urllib import request

import zone
from NeonOcean.S4.Main import Debug, Director, Language, LoadingShared, Mods, Paths, Settings, This
from NeonOcean.S4.Main.Tools import Exceptions, Parse, Timer, Version
from NeonOcean.S4.Main.UI import Notifications
from sims4 import collections
from ui import ui_dialog

_updateDistributors = list()  # type: typing.List[UpdateDistributor]
_promotionDistributors = list()  # type: typing.List[PromotionDistributor]

_updateDistributorTimers = list()  # type: typing.List[Timer.Timer]
_promotionDistributorTimers = list()  # type: typing.List[Timer.Timer]

class _Announcer(Director.Announcer):
	Host = This.Mod

	@classmethod
	def OnLoadingScreenAnimationFinished (cls, zoneReference: zone.Zone) -> None:
		for updateDistributor in _updateDistributors:  # type: UpdateDistributor
			# noinspection PyProtectedMember
			updateDistributorTimer = Timer.Timer(updateDistributor.TickerDelay, updateDistributor._Start)  # type: Timer.Timer
			updateDistributorTimer.start()
			_updateDistributorTimers.append(updateDistributorTimer)

		for promotionDistributor in _promotionDistributors:  # type: PromotionDistributor
			# noinspection PyProtectedMember
			promotionDistributorTimer = Timer.Timer(promotionDistributor.TickerDelay, promotionDistributor._Start)  # type: Timer.Timer
			promotionDistributorTimer.start()
			_promotionDistributorTimers.append(promotionDistributorTimer)

class FilterTypes(enum_lib.IntEnum):
	Whitelist = 0  # type: FilterTypes
	Blacklist = 1  # type: FilterTypes

class Distributor(abc.ABC):
	def __init__ (self, distributionIdentifier: str, tickerInterval: typing.Union[float, int] = 1800, tickerDelay: typing.Union[float, int] = 10):
		if not isinstance(distributionIdentifier, str):
			raise Exceptions.IncorrectTypeException(distributionIdentifier, "distributionIdentifier", (str,))

		if not isinstance(tickerInterval, (float, int)):
			raise Exceptions.IncorrectTypeException(tickerInterval, "tickerInterval", (float, int))

		if not isinstance(tickerDelay, (float, int)):
			raise Exceptions.IncorrectTypeException(tickerDelay, "tickerDelay", (float, int))

		self.DistributionIdentifier = distributionIdentifier  # type: str

		self.TickerInterval = tickerInterval  # type: typing.Union[float, int]
		self.TickerDelay = tickerDelay  # type: typing.Union[float, int]

		self._ticker = None  # type: typing.Optional[Timer.Timer]

	def CheckNow (self, restartTicker: bool = True) -> None:
		"""
		Check the distribution now.
		:param restartTicker: Whether or not we should restart the ticker after checking.
		:type restartTicker: bool
		:return:
		"""

		checkThread = threading.Thread(target = self._CheckDistribution)  # type: threading.Thread
		checkThread.setDaemon(True)
		checkThread.start()

		if restartTicker:
			self.RestartTicker()

	def RestartTicker (self) -> None:
		self.StopTicker()

		self._ticker = Timer.Timer(self.TickerInterval, self._CheckDistribution)
		self._ticker.start()

	def StopTicker (self) -> None:
		if self._ticker is not None:
			self._ticker.Stop()

	def _Start (self) -> None:
		if self._ticker is None:
			checkThread = threading.Thread(target = self._CheckDistribution)  # type: threading.Thread
			checkThread.setDaemon(True)
			checkThread.start()

			self.RestartTicker()

	@abc.abstractmethod
	def _CheckDistribution (self) -> None:
		...

class UpdateInformation:
	def __init__ (self, modNamespace: str, modName: str, modAuthor: str, currentVersion: str, newVersion: str, isPreview: bool, downloadURL: str):
		if not isinstance(modNamespace, str):
			raise Exceptions.IncorrectTypeException(modNamespace, "modNamespace", (str,))

		if not isinstance(modName, str):
			raise Exceptions.IncorrectTypeException(modName, "modName", (str,))

		if not isinstance(modAuthor, str):
			raise Exceptions.IncorrectTypeException(modAuthor, "modAuthor", (str,))

		if not isinstance(currentVersion, str):
			raise Exceptions.IncorrectTypeException(currentVersion, "currentVersion", (str,))

		if not isinstance(newVersion, str):
			raise Exceptions.IncorrectTypeException(newVersion, "newVersion", (str,))

		if not isinstance(isPreview, bool):
			raise Exceptions.IncorrectTypeException(isPreview, "isPreview", (bool,))

		if not isinstance(downloadURL, str):
			raise Exceptions.IncorrectTypeException(downloadURL, "downloadURL", (str,))

		self.ModNamespace = modNamespace  # type: str
		self.ModName = modName  # type: str
		self.ModAuthor = modAuthor  # type: str
		self.CurrentVersion = currentVersion  # type: str
		self.NewVersion = newVersion  # type: str
		self.IsPreview = isPreview  # type: bool
		self.DownloadURL = downloadURL  # type: str

	@classmethod
	def UpdateInformationListToHex (cls, updatedMods) -> str:
		updatedModsData = list()  # type: typing.List[typing.Dict[str, typing.Any]]

		for updatedMod in updatedMods:  # type: UpdateInformation
			updateData = {
				"ModNamespace": updatedMod.ModNamespace,
				"ModName": updatedMod.ModName,
				"ModAuthor": updatedMod.ModAuthor,
				"CurrentVersion": updatedMod.CurrentVersion,
				"NewVersion": updatedMod.NewVersion,
				"IsPreview": updatedMod.IsPreview,
				"DownloadURL": updatedMod.DownloadURL
			}

			updatedModsData.append(updateData)

		updatedModsString = json.encoder.JSONEncoder().encode(updatedModsData)  # type: str
		updatedModsHex = codecs.encode(bytearray(updatedModsString, "utf-8"), "hex").decode("utf-8")
		return updatedModsHex

	@classmethod
	def UpdateInformationListFromHex (cls, updatedModsHex: str):
		updatedModsString = codecs.decode(updatedModsHex, "hex").decode("utf-8")  # type: str
		updatedModsData = json.decoder.JSONDecoder().decode(updatedModsString)  # type: typing.List[typing.Dict[str, typing.Any]]

		updatedMods = list()  # type: typing.List[UpdateInformation]

		for updatedModData in updatedModsData:  # type: typing.Dict[str, typing.Any]
			modNamespace = updatedModData["ModNamespace"]  # type: str
			modName = updatedModData["ModName"]  # type: str
			modAuthor = updatedModData["ModAuthor"]  # type: str
			currentVersion = updatedModData["CurrentVersion"]  # type: str
			newVersion = updatedModData["NewVersion"]  # type: str
			isPreview = updatedModData["IsPreview"]  # type: bool
			downloadURL = updatedModData["DownloadURL"]  # type: str

			updatedMods.append(UpdateInformation(modNamespace, modName, modAuthor, currentVersion, newVersion, isPreview, downloadURL))

		return updatedMods

class UpdateDistributor(Distributor):
	"""
	Useful for checking for updates of various mods.
	"""

	UpdatesNotificationTitle = Language.String(This.Mod.Namespace + ".Distribution.Updates_Notification.Title")
	UpdatesNotificationText = Language.String(This.Mod.Namespace + ".Distribution.Updates_Notification.Text")
	UpdatesNotificationButton = Language.String(This.Mod.Namespace + ".Distribution.Updates_Notification.Button")

	_releaseKey = "Release"  # type: str
	_releaseDisplayKey = "ReleaseDisplay"  # type: str
	_previewKey = "Preview"  # type: str
	_previewDisplayKey = "PreviewDisplay"  # type: str

	def __init__ (self, distributionIdentifier: str, tickerInterval: float = 1800, tickerDelay: float = 10, connectionTimeout: typing.Union[float, int] = 10):
		"""
		:param distributionIdentifier: This distributor's identifier, the identifier used to determine if updates should be checked for a certain mod.
		This object will look for all mods with the same 'Distribution' value as this identifier.
		:type distributionIdentifier: str
		:param tickerInterval: The time in seconds between each time this will check for updates.
		:type tickerInterval: float
		:param tickerDelay: The time in seconds from the first time a zone is loaded to the first time this checks for an update.
		:type tickerDelay: float
		:param connectionTimeout: The amount of time in seconds we will try to read an updates file before giving up.
		:type connectionTimeout: float | int
		"""

		if not isinstance(connectionTimeout, (float, int)):
			raise Exceptions.IncorrectTypeException(connectionTimeout, "connectionTimeout", (float, int))

		super().__init__(distributionIdentifier, tickerInterval = tickerInterval, tickerDelay = tickerDelay)

		self.ConnectionTimeout = connectionTimeout  # type: typing.Union[float, int]

		self.ShownMods = set()  # type: typing.Set[str]

		_RegisterUpdateDistributor(self)

	def _GetUpdatesFileURLs (self) -> typing.Dict[str, typing.List[Mods.Mod]]:
		validMods = self._GetValidMods()  # type: typing.List[Mods.Mod]
		updatesFileGroups = dict()  # type: typing.Dict[str, typing.List[Mods.Mod]]

		for mod in validMods:  # type: Mods.Mod
			if mod.Distribution.UpdatesFileURL in updatesFileGroups:
				updatesFileGroups[mod.Distribution.UpdatesFileURL].append(mod)
			else:
				updatesFileGroups[mod.Distribution.UpdatesFileURL] = [mod]

		return updatesFileGroups

	def _GetReleaseURL (self, mod: Mods.Mod) -> str:
		return mod.Distribution.DownloadURL if mod.Distribution.DownloadURL is not None else ""

	def _GetPreviewURL (self, mod: Mods.Mod) -> str:
		return mod.Distribution.PreviewDownloadURL if mod.Distribution.PreviewDownloadURL is not None else self._GetReleaseURL(mod)

	def _GetValidMods (self) -> typing.List[Mods.Mod]:
		validMods = list()  # type: typing.List[Mods.Mod]

		for mod in Mods.GetAllMods():  # type: Mods.Mod
			if not mod.ReadInformation:
				continue

			if mod.Distribution.UpdatesController != self.DistributionIdentifier:
				continue

			if mod.Distribution.UpdatesFileURL is None:
				continue

			if mod.Distribution.DownloadURL is None:
				continue

			if not self._DistributeModUpdates(mod):
				continue

			validMods.append(mod)

		return validMods

	def _DistributeModUpdates (self, mod: Mods.Mod) -> bool:
		distributeUpdatesValues = Settings.CheckForUpdates.Get()  # type: typing.Dict[str, bool]
		distributeUpdatesDefault = Settings.CheckForUpdatesDefault.Get()  # type: bool
		return distributeUpdatesValues.get(mod.Namespace, distributeUpdatesDefault)

	def _DistributeModPreviewUpdates (self, mod: Mods.Mod) -> bool:
		distributePreviewUpdatesValues = Settings.CheckForPreviewUpdates.Get()  # type: typing.Dict[str, bool]
		distributePreviewUpdatesDefault = Settings.CheckForPreviewUpdatesDefault.Get()  # type: bool
		return distributePreviewUpdatesValues.get(mod.Namespace, distributePreviewUpdatesDefault)

	def _ShowedUpdateNotification (self, mod: Mods.Mod) -> bool:
		return mod.Namespace in self.ShownMods

	def _CheckDistribution (self) -> None:
		updatedMods = list()  # type: typing.List[UpdateInformation]

		for updatesFileURL, checkingMods in self._GetUpdatesFileURLs().items():  # type: str, typing.List[Mods.Mod]
			try:
				updatedMods.extend(self._CheckUpdates(updatesFileURL, checkingMods))  # type: typing.List[UpdateInformation]
			except Exception:
				Debug.Log("Failed to check for updates for distribution identifier '" + self.DistributionIdentifier + "'.\nUpdates File: " + updatesFileURL, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				continue

		if len(updatedMods) == 0:
			return

		self._ShowUpdatesNotification(updatedMods)

	def _CheckUpdates (self, updatesFileURL: str, checkingMods: typing.List[Mods.Mod]) -> typing.List[UpdateInformation]:
		updatedMods = list()  # type: typing.List[UpdateInformation]

		try:
			latestDictionary = self._ReadUpdatesFile(updatesFileURL)  # type: typing.Dict[str, dict]
		except Exception:
			Debug.Log("Failed to get mod versions.\nURL: " + updatesFileURL, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			return updatedMods

		for mod in checkingMods:  # type: Mods.Mod
			if mod in self.ShownMods:
				continue

			try:
				modVersions = latestDictionary.get(mod.Namespace)  # type: Version

				if modVersions is None:
					Debug.Log("Missing version data for '" + mod.Namespace + "'.\nURL: " + updatesFileURL, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
					continue

				releaseVersion = modVersions.get(self._releaseKey, Version.Version())  # type: Version.Version
				releaseVersionDisplay = modVersions.get(self._releaseDisplayKey, str(releaseVersion))  # type: str

				if self._DistributeModPreviewUpdates(mod):
					previewVersion = modVersions.get(self._previewKey, Version.Version())  # type: Version.Version
					previewVersionDisplay = modVersions.get(self._previewDisplayKey, str(previewVersion))  # type: str

					if previewVersion <= releaseVersion:
						if mod.Version < releaseVersion:
							updatedMods.append(UpdateInformation(mod.Namespace, mod.Name, mod.Author, mod.VersionDisplay,
																 releaseVersionDisplay, False, self._GetReleaseURL(mod)))
							continue
					else:
						if mod.Version < previewVersion:
							updatedMods.append(UpdateInformation(mod.Namespace, mod.Name, mod.Author, mod.VersionDisplay,
																 previewVersionDisplay, True, self._GetPreviewURL(mod)))
							continue
				else:
					if mod.Version < releaseVersion:
						updatedMods.append(UpdateInformation(mod.Namespace, mod.Name, mod.Author, mod.VersionDisplay,
															 releaseVersionDisplay, False, self._GetReleaseURL(mod)))
						continue
			except Exception:
				Debug.Log("Failed to get update information for '" + mod.Namespace + "'.\nURL: " + updatesFileURL, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

		return updatedMods

	def _ReadUpdatesFile (self, updatesFileURL: str) -> typing.Dict[str, dict]:
		with request.urlopen(updatesFileURL, timeout = self.ConnectionTimeout) as versionsFile:  # type: client.HTTPResponse
			versionsDictionaryString = versionsFile.read().decode("utf-8")  # type: str

		if not versionsDictionaryString or versionsDictionaryString.isspace():
			raise Exception("Latest versions file at '" + updatesFileURL + "' is empty or whitespace.")

		try:
			versionDictionary = json.JSONDecoder().decode(versionsDictionaryString)  # type: typing.Dict[str, typing.Dict[str, typing.Any]]

			if not isinstance(versionDictionary, dict):
				raise Exceptions.IncorrectTypeException(versionDictionary, "Root", (dict,))

			for modNamespace in list(versionDictionary.keys()):  # type: str
				if not isinstance(modNamespace, str):
					Debug.Log("Invalid type in distribution version data.\n" + Exceptions.GetIncorrectTypeExceptionText(modNamespace, "Root<Key>", (str,)), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
					versionDictionary.pop(modNamespace, None)
					continue

				modLatest = versionDictionary[modNamespace]  # type: dict

				if not isinstance(modLatest, dict):
					Debug.Log("Invalid type in distribution version data.\n" + Exceptions.GetIncorrectTypeExceptionText(modNamespace, "Root[%s]" % modNamespace, (str,)), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
					versionDictionary.pop(modNamespace, None)
					continue

				if self._releaseDisplayKey in modLatest:
					releaseVersionDisplayString = modLatest.get(self._releaseDisplayKey)  # type: str

					if not isinstance(releaseVersionDisplayString, str):
						Debug.Log("Invalid type in distribution version data.\n" + Exceptions.GetIncorrectTypeExceptionText(modNamespace, "Root[%s][%s]" % (modNamespace, self._releaseDisplayKey), (str,)), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
						modLatest.pop(self._releaseDisplayKey, None)

				if self._releaseKey in modLatest:
					releaseVersionString = modLatest.get(self._releaseKey)  # type: str

					if not isinstance(releaseVersionString, str):
						Debug.Log("Invalid type in distribution version data.\n" + Exceptions.GetIncorrectTypeExceptionText(modNamespace, "Root[%s][%s]" % (modNamespace, self._releaseKey), (str,)), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
						modLatest.pop(self._releaseKey, None)

					try:
						releaseVersion = Version.Version(releaseVersionString)  # type: Version.Version
						modLatest[self._releaseKey] = releaseVersion

						if not self._releaseDisplayKey in modLatest:
							modLatest[self._releaseDisplayKey] = str(releaseVersion)
					except:
						Debug.Log("Failed to convert a distribution version string to a version object.\n" + "Root[%s][%s]" % (modNamespace, self._releaseKey), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
						modLatest.pop(self._releaseKey, None)
				else:
					Debug.Log("Missing release version for '" + modNamespace + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

				if self._previewDisplayKey in modLatest:
					previewVersionDisplayString = modLatest.get(self._previewDisplayKey)  # type: str

					if not isinstance(previewVersionDisplayString, str):
						Debug.Log("Invalid type in distribution version data.\n" + Exceptions.GetIncorrectTypeExceptionText(modNamespace, "Root[%s][%s]" % (modNamespace, self._previewDisplayKey), (str,)), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
						modLatest.pop(self._previewDisplayKey, None)

				if self._previewKey in modLatest:
					previewVersionString = modLatest.get(self._previewKey)  # type: str

					if not isinstance(previewVersionString, str):
						Debug.Log("Invalid type in distribution version data.\n" + Exceptions.GetIncorrectTypeExceptionText(modNamespace, "Root[%s][%s]" % (modNamespace, self._previewKey), (str,)), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
						modLatest.pop(self._previewKey, None)

					try:
						previewVersion = Version.Version(previewVersionString)  # type: Version.Version
						modLatest[self._previewKey] = previewVersion

						if not self._previewDisplayKey in modLatest:
							modLatest[self._previewDisplayKey] = str(previewVersion)
					except:
						Debug.Log("Failed to convert a distribution version string to a version object.\n" + "Root[%s][%s]" % (modNamespace, self._previewKey), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
						modLatest.pop(self._previewKey, None)

		except Exception as e:
			raise Exception("Failed to decode latest version file at '" + updatesFileURL + "'.") from e

		return versionDictionary

	def _ShowUpdatesNotification (self, updatedMods: typing.List[UpdateInformation]) -> None:
		if len(updatedMods) == 0:
			return

		updatedModsHex = UpdateInformation.UpdateInformationListToHex(updatedMods)  # type: str

		responseCommand = collections.make_immutable_slots_class(("command", "arguments"))

		responseArguments = [
			collections.make_immutable_slots_class(("arg_value", "arg_type"))
		]

		responseArguments[0] = responseArguments[0]({
			"arg_value": updatedModsHex,
			"arg_type": ui_dialog.CommandArgType.ARG_TYPE_STRING
		})

		responseCommand = responseCommand({
			"command": This.Mod.Namespace.lower() + ".distribution.show_updates_list",
			"arguments": responseArguments
		})

		response = ui_dialog.UiDialogResponse(
			text = self.UpdatesNotificationButton.GetCallableLocalizationString(),
			ui_request = ui_dialog.UiDialogResponse.UiDialogUiRequest.SEND_COMMAND,
			response_command = responseCommand
		)

		updatedModsText = updatedMods[0].ModName  # type: str

		for updatedMod in updatedMods[1:]:  # type: UpdateInformation
			updatedModsText += "\n" + updatedMod.ModName

		notificationArguments = {
			"title": self.UpdatesNotificationTitle.GetCallableLocalizationString(),
			"text": self.UpdatesNotificationText.GetCallableLocalizationString(updatedModsText),

			"ui_responses": (response,)
		}

		Notifications.ShowNotification(queue = True, **notificationArguments)

		for updatedMod in updatedMods:  # type: UpdateInformation
			self.ShownMods.add(updatedMod.ModNamespace)

class PromotionDistributor(Distributor):
	"""
	For displaying promotional material, I highly recommend limiting the promotions you display to major events only. Showing too many promotions too frequently
	may cause players to want to disable promotional notifications.
	"""

	PromotionDefaultTitle = Language.String(This.Mod.Namespace + ".Distribution.Promotions.Default.Title")  # type: Language.String
	PromotionDefaultButton = Language.String(This.Mod.Namespace + ".Distribution.Promotions.Default.Button")  # type: Language.String

	_identifierKey = "Identifier"  # type: str

	class Promotion:
		_identifierKey = "Identifier"  # type: str
		_targetsKey = "Targets"  # type: str
		_targetsTypeKey = "TargetsType"  # type: str
		_modsKey = "Mods"  # type: str
		_modsTypeKey = "ModsType"  # type: str
		_ratingKey = "Rating"  # type: str
		_linkKey = "Link"  # type: str
		_s4TitleKey = "S4Title"  # type: str
		_s4TextKey = "S4Text"  # type: str
		_s4LinkButton = "S4LinkButton"  # type: str

		def __init__ (self, promotionDictionary: dict):
			self.Identifier = promotionDictionary[self._identifierKey]  # type: str

			self.Targets = promotionDictionary.get(self._targetsKey, list())  # type: list

			if not isinstance(self.Targets, list):
				Debug.Log("Expected type of 'list' for promotion target lists. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				self.Targets = list()

			targetIndex = 0  # type: int
			poppedTargets = 0  # type: int
			while targetIndex < len(self.Targets):
				if not isinstance(self.Targets[targetIndex], str):
					Debug.Log("Expected type of 'str' for a promotion target at the index of '" + str(targetIndex + poppedTargets) + "'. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
					self.Targets.pop(targetIndex)
					poppedTargets += 1

				targetIndex += 1

			targetsTypeString = promotionDictionary.get(self._targetsTypeKey, FilterTypes.Whitelist.name)  # type: str

			try:
				self.TargetsType = Parse.ParsePythonEnum(targetsTypeString, FilterTypes)  # type: FilterTypes
			except Exception:
				Debug.Log("Failed to parse target filter type from '" + targetsTypeString + "'. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				self.TargetsType = FilterTypes.Whitelist

			self.Mods = promotionDictionary.get(self._modsKey, list())  # type: list

			if not isinstance(self.Mods, list):
				Debug.Log("Expected type of 'list' for promotion mod lists. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				self.Mods = list()

			modIndex = 0  # type: int
			poppedMods = 0  # type: int
			while modIndex < len(self.Mods):
				if not isinstance(self.Mods[modIndex], str):
					Debug.Log("Expected type of 'str' for a promotion mod at the index of '" + str(modIndex + poppedMods) + "'. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
					self.Mods.pop(modIndex)
					poppedMods += 1

				modIndex += 1

			modsTypeString = promotionDictionary.get(self._modsTypeKey, FilterTypes.Whitelist.name)  # type: str

			try:
				self.ModsType = Parse.ParsePythonEnum(modsTypeString, FilterTypes)  # type: FilterTypes
			except Exception:
				Debug.Log("Failed to parse mod filter type from '" + modsTypeString + "'. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				self.ModsType = FilterTypes.Whitelist

			ratingString = promotionDictionary.get(self._ratingKey, Mods.Rating.Normal.name)  # type: str

			try:
				self.Rating = Parse.ParsePythonEnum(ratingString, Mods.Rating)  # type: Mods.Rating
			except Exception:
				Debug.Log("Failed to parse rating type from '" + ratingString + "'. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				self.Rating = Mods.Rating.Normal

			self.Link = promotionDictionary.get(self._linkKey)  # type: typing.Optional[str]

			if not isinstance(self.Link, str) and self.Link is not None:
				Debug.Log("Expected type of 'str' for a promotion link. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

			self.Title = promotionDictionary.get(self._s4TitleKey)  # type: typing.Optional[str]

			if not isinstance(self.Title, str) and self.Title is not None:
				Debug.Log("Expected type of 'str' for a promotion title. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

			self.Text = promotionDictionary.get(self._s4TextKey)  # type: typing.Optional[str]

			if not isinstance(self.Text, str) and self.Text is not None:
				Debug.Log("Expected type of 'str' for a promotion text. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

			self.LinkButton = promotionDictionary.get(self._s4LinkButton)  # type: typing.Optional[str]

			if not isinstance(self.LinkButton, str) and self.LinkButton is not None:
				Debug.Log("Expected type of 'str' for a promotion link button. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

		def CanShow (self, shownPromotions: typing.List[str]) -> bool:
			if self.Text is None:
				return False

			if self.TargetsType == FilterTypes.Whitelist:
				validGame = False  # type: bool

				for promotionTarget in self.Targets:  # type: str
					if promotionTarget.lower() == "s4":
						validGame = True

				if not validGame:
					return False
			else:
				for promotionTarget in self.Targets:  # type: str
					if promotionTarget.lower() == "s4":
						return False

			if self.ModsType == FilterTypes.Whitelist:
				validMods = True  # type: bool

				for promotionMod in self.Mods:  # type: str
					if not Mods.IsInstalled(promotionMod):
						validMods = False

				if not validMods:
					return False
			else:
				for promotionMod in self.Mods:  # type: str
					if Mods.IsInstalled(promotionMod):
						return False

			if self.Rating == Mods.Rating.NSFW:
				validRating = False

				for mod in Mods.GetAllMods():  # type: Mods.Mod
					if mod.Rating == Mods.Rating.NSFW:
						validRating = True

				if not validRating:
					return False

			identifierLower = self.Identifier.lower()  # type: str

			for shownPromotion in shownPromotions:  # type: str
				if identifierLower == shownPromotion.lower():
					return False

			return True

	def __init__ (self, distributionIdentifier: str, promotionsFileURL: str,
				  tickerInterval: float = 1800, tickerDelay: float = 10, connectionTimeout: typing.Union[float, int] = 10):
		"""
		:param distributionIdentifier: This distributor's identifier, the identifier used to separate persistent data made by this promotion distributor.
		:type distributionIdentifier: str
		:param promotionsFileURL: The url at which the update distributor object can find the promotion information file.
		:type promotionsFileURL: str
		:param tickerInterval: The time in seconds between each time this will check for new promotions.
		:type tickerInterval: float
		:param tickerDelay: The time in seconds from the first time a zone is loaded to the first time this checks for a promotion.
		:type tickerDelay: float
		:param connectionTimeout: The amount of time in seconds we will try to read a promotions file before giving up.
		:type connectionTimeout: float | int
		"""

		if not isinstance(connectionTimeout, (float, int)):
			raise Exceptions.IncorrectTypeException(connectionTimeout, "connectionTimeout", (float, int))

		super().__init__(distributionIdentifier, tickerInterval = tickerInterval, tickerDelay = tickerDelay)

		self.ConnectionTimeout = connectionTimeout

		self.ShowedPromotion = False  # type: bool
		self.ShownPromotions = list()  # type: typing.List[str]

		self._promotionsFileURL = promotionsFileURL  # type: str

		self._shownPromotionsFilePath = os.path.join(Paths.PersistentPath, "Distribution", self.DistributionIdentifier, "ShownPromotions.json")  # type: str

		self.LoadShownPromotions()

		_RegisterPromotionDistributor(self)

	@property
	def PromotionsFileURL (self) -> str:
		return self._promotionsFileURL

	@property
	def ShownPromotionsFilePath (self) -> str:
		return self._shownPromotionsFilePath

	def LoadShownPromotions (self) -> None:
		shownPromotionsFilePath = self.ShownPromotionsFilePath  # type: str

		if os.path.exists(shownPromotionsFilePath):
			try:
				with open(shownPromotionsFilePath) as shownPromotionsFile:
					shownPromotions = json.JSONDecoder().decode(shownPromotionsFile.read())

					if not isinstance(shownPromotions, list):
						raise Exceptions.IncorrectTypeException(shownPromotions, "Root", (list,))

					for shownPromotionIndex in range(len(shownPromotions)):  # type: int
						if not isinstance(shownPromotions[shownPromotionIndex], str):
							raise Exceptions.IncorrectTypeException(shownPromotions[shownPromotionIndex], "Root[%d]" % shownPromotionIndex, (str,))

					self.ShownPromotions = shownPromotions
			except Exception:
				Debug.Log("Failed to read shown promotions file.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

	def _CheckDistribution (self) -> None:
		if self.ShowedPromotion:
			return

		try:
			promotions = self._CheckPromotions(self.PromotionsFileURL)  # type: typing.List[PromotionDistributor.Promotion]

			if len(promotions) == 0:
				return

			chosenPromotion = self._ChoosePromotion(promotions)
		except Exception:
			Debug.Log("Failed to find a promotion.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			return

		try:
			self._ShowPromotion(chosenPromotion)
		except Exception:
			Debug.Log("Failed to show promotion notification for promotion '" + chosenPromotion.Identifier + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			return

	def _CheckPromotions (self, promotionsFileURL: str) -> typing.List[Promotion]:
		validPromotions = list()  # type: typing.List[PromotionDistributor.Promotion]

		if not self._DistributePromotions():
			return validPromotions

		try:
			promotionsList = self._ReadPromotionsFile(promotionsFileURL)  # type: typing.List[dict]
		except Exception:
			Debug.Log("Failed to get promotions.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			return validPromotions

		for promotionDictionary in promotionsList:  # type: typing.Dict
			promotion = self.Promotion(promotionDictionary)  # type: PromotionDistributor.Promotion

			if promotion.CanShow(self.ShownPromotions):
				validPromotions.append(promotion)

		return validPromotions

	def _DistributePromotions (self) -> bool:
		return Settings.ShowPromotions.Get()  # type: bool

	def _ChoosePromotion (self, promotions: typing.List[Promotion]) -> Promotion:
		return random.choice(promotions)

	def _ReadPromotionsFile (self, promotionsFileURL: str) -> typing.List[dict]:
		with request.urlopen(promotionsFileURL, timeout = self.ConnectionTimeout) as promotionsFile:  # type: client.HTTPResponse
			promotionsListString = promotionsFile.read().decode("utf-8")  # type: str

		if not promotionsListString or promotionsListString.isspace():
			raise Exception("Promotions file at '" + promotionsFileURL + "' is empty or whitespace.")

		try:
			promotionsList = json.JSONDecoder().decode(promotionsListString)  # type: typing.List[dict]

			if not isinstance(promotionsList, list):
				raise Exceptions.IncorrectTypeException(promotionsList, "Root", (list,))

			for promotionIndex in range(len(promotionsList)):
				if not isinstance(promotionsList[promotionIndex], dict):
					Debug.Log("Invalid type in distribution promotion data.\n" + Exceptions.GetIncorrectTypeExceptionText(promotionsList[promotionIndex], "Root[%s]" % promotionIndex, (str,)), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
					promotionsList.pop(promotionIndex)
					continue

				if not self._identifierKey in promotionsList[promotionIndex]:
					Debug.Log("Missing distribution promotion dictionary entry '%s' in 'Root[%s]'." % (self._identifierKey, promotionIndex), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
					promotionsList.pop(promotionIndex)
					continue

				if not isinstance(promotionsList[promotionIndex][self._identifierKey], str):
					Debug.Log("Invalid type in distribution promotion data.\n" + Exceptions.GetIncorrectTypeExceptionText(promotionsList[promotionIndex][self._identifierKey], "Root[%d][%s]" % (promotionIndex, self._identifierKey), (str,)), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
					promotionsList.pop(promotionIndex)
					continue

				promotionIndex += 1
		except Exception as e:
			raise Exception("Failed to decode promotions file at '" + promotionsFileURL + "'.") from e

		return promotionsList

	def _ShowPromotion (self, promotion: Promotion) -> None:
		notificationArguments = {
			"text": lambda *args, **kwargs: Language.CreateLocalizationString(promotion.Text)
		}

		if promotion.Link is not None:
			if promotion.LinkButton is not None:
				linkResponseText = lambda *args, **kwargs: Language.CreateLocalizationString(promotion.LinkButton)
			else:
				linkResponseText = self.PromotionDefaultButton.GetCallableLocalizationString()

			linkResponseCommand = collections.make_immutable_slots_class(("command", "arguments"))

			linkResponseArguments = [
				collections.make_immutable_slots_class(("arg_value", "arg_type"))
			]

			linkResponseArguments[0] = linkResponseArguments[0]({
				"arg_value": codecs.encode(bytearray(promotion.Link, "utf-8"), "hex").decode("utf-8"),
				"arg_type": ui_dialog.CommandArgType.ARG_TYPE_STRING
			})

			linkResponseCommand = linkResponseCommand({
				"command": This.Mod.Namespace.lower() + ".distribution.show_url",
				"arguments": linkResponseArguments
			})

			linkResponse = ui_dialog.UiDialogResponse(
				text = linkResponseText,
				ui_request = ui_dialog.UiDialogResponse.UiDialogUiRequest.SEND_COMMAND,
				response_command = linkResponseCommand
			)

			notificationArguments["ui_responses"] = (linkResponse,)

		if promotion.Title is not None:
			notificationArguments["title"] = lambda *args, **kwargs: Language.CreateLocalizationString(promotion.Title)
		else:
			notificationArguments["title"] = self.PromotionDefaultTitle.GetCallableLocalizationString()

		Notifications.ShowNotification(queue = True, **notificationArguments)

		self.ShowedPromotion = True
		self.ShownPromotions.append(promotion.Identifier)

		try:
			shownPromotionsFilePath = self.ShownPromotionsFilePath  # type: str
			shownPromotionsDirectory = os.path.dirname(self.ShownPromotionsFilePath)  # type: str

			if not os.path.exists(shownPromotionsDirectory):
				os.makedirs(shownPromotionsDirectory)

			with open(shownPromotionsFilePath, "w+") as shownPromotionsFile:
				shownPromotionsFile.write(json.JSONEncoder(indent = "\t").encode(self.ShownPromotions))
		except Exception:
			Debug.Log("Failed to write shown promotions to a file.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _RegisterUpdateDistributor (updateDistributor: UpdateDistributor) -> None:
	for existingUpdateDistributor in _updateDistributors:  # type: UpdateDistributor
		if existingUpdateDistributor.DistributionIdentifier == updateDistributor.DistributionIdentifier:
			Debug.Log("Multiple update distributors with the identifier '" + updateDistributor.DistributionIdentifier + "' exist, this might cause problems.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

	_updateDistributors.append(updateDistributor)

def _RegisterPromotionDistributor (promotionDistributor: PromotionDistributor) -> None:
	for existingPromotionDistributor in _promotionDistributors:  # type: PromotionDistributor
		if existingPromotionDistributor.DistributionIdentifier == promotionDistributor.DistributionIdentifier:
			Debug.Log("Multiple promotion distributors with the identifier '" + promotionDistributor.DistributionIdentifier + "' exist, this might cause problems.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

	_promotionDistributors.append(promotionDistributor)

def _OnUnload (cause: LoadingShared.UnloadingCauses) -> None:
	global _updateDistributorTimers, _promotionDistributorTimers

	if cause:
		pass

	for updateDistributorTimer in _updateDistributorTimers:  # type: Timer.Timer
		updateDistributorTimer.Stop()

	for promotionDistributorTimer in _promotionDistributorTimers:  # type: Timer.Timer
		promotionDistributorTimer.Stop()

	_updateDistributorTimers = list()
	_promotionDistributorTimers = list()
