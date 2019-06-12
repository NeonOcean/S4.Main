import codecs
import json
import os
import random
import threading
import typing
from http import client
from urllib import request

import enum
import zone
from NeonOcean.Main import Debug, Director, Language, Mods, Paths, Settings, This
from NeonOcean.Main.Tools import Exceptions, Parse, Timer, Version
from NeonOcean.Main.UI import Notifications
from sims4 import collections
from ui import ui_dialog

_updateDistributors = list()  # type: typing.List[UpdateDistributor]
_promotionDistributors = list()  # type: typing.List[PromotionDistributor]

class _Announcer(Director.Announcer):
	Host = This.Mod

	@classmethod
	def OnLoadingScreenAnimationFinished (cls, zoneReference: zone.Zone) -> None:
		for updateDistributor in _updateDistributors:  # type: UpdateDistributor
			Timer.Timer(updateDistributor.TickerDelay, updateDistributor._Start).start()  # type: Timer.Timer

		for promotionDistributor in _promotionDistributors:  # type: PromotionDistributor
			Timer.Timer(promotionDistributor.TickerDelay, promotionDistributor._Start).start()  # type: Timer.Timer

class _FilterTypes(enum.Int):
	Whitelist = 0  # type: _FilterTypes
	Blacklist = 1  # type: _FilterTypes

class _Promotion:
	def __init__ (self, promotionDictionary: dict):
		self.Identifier = promotionDictionary["Identifier"]  # type: str

		self.Targets = promotionDictionary.get("Targets", list())  # type: list

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

		targetsTypeString = promotionDictionary.get("TargetsType", _FilterTypes.Whitelist.name)  # type: str

		try:
			self.TargetsType = Parse.ParseEnum(targetsTypeString, _FilterTypes)  # type: _FilterTypes
		except:
			Debug.Log("Failed to parse target filter type from '" + targetsTypeString + "'. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			self.TargetsType = _FilterTypes.Whitelist

		self.Mods = promotionDictionary.get("Mods", list())  # type: list

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

		modsTypeString = promotionDictionary.get("ModsType", _FilterTypes.Whitelist.name)  # type: str

		try:
			self.ModsType = Parse.ParseEnum(modsTypeString, _FilterTypes)  # type: _FilterTypes
		except:
			Debug.Log("Failed to parse mod filter type from '" + modsTypeString + "'. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			self.ModsType = _FilterTypes.Whitelist

		ratingString = promotionDictionary.get("Rating", Mods.Rating.Normal.name)  # type: str

		try:
			self.Rating = Parse.ParseEnum(ratingString, Mods.Rating)  # type: Mods.Rating
		except:
			Debug.Log("Failed to parse rating type from '" + ratingString + "'. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			self.Rating = Mods.Rating.Normal

		self.Link = promotionDictionary.get("Link")  # type: typing.Optional[str]

		if not isinstance(self.Link, str) and self.Link is not None:
			Debug.Log("Expected type of 'str' for a promotion link. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

		self.Title = promotionDictionary.get("S4Title")  # type: typing.Optional[str]

		if not isinstance(self.Title, str) and self.Title is not None:
			Debug.Log("Expected type of 'str' for a promotion title. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

		self.Text = promotionDictionary.get("S4Text")  # type: typing.Optional[str]

		if not isinstance(self.Text, str) and self.Text is not None:
			Debug.Log("Expected type of 'str' for a promotion text. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

		self.LinkButton = promotionDictionary.get("S4LinkButton")  # type: typing.Optional[str]

		if not isinstance(self.LinkButton, str) and self.LinkButton is not None:
			Debug.Log("Expected type of 'str' for a promotion link button. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

	def CanShow (self, shownPromotions: typing.List[str]) -> bool:
		if self.Text is None:
			return False

		if self.TargetsType == _FilterTypes.Whitelist:
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

		if self.ModsType == _FilterTypes.Whitelist:
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

class _Distributor:
	def __init__ (self, distributionIdentifier: str, tickerInterval: float = 1800, tickerDelay: float = 10):
		self.DistributionIdentifier = distributionIdentifier  # type: str

		self.TickerInterval = tickerInterval  # type: int
		self.TickerDelay = tickerDelay  # type: int

		self._ticker = None  # type: Timer.Timer

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

	def _CheckDistribution (self) -> None:
		pass

class UpdateDistributor(_Distributor):
	"""
	Useful for checking for updates of various mods.
	"""

	UpdateNotificationTitle = Language.String(This.Mod.Namespace + ".System.Distribution.Update_Notification.Title")
	UpdateNotificationReleaseText = Language.String(This.Mod.Namespace + ".System.Distribution.Update_Notification.Release_Text")
	UpdateNotificationPreviewText = Language.String(This.Mod.Namespace + ".System.Distribution.Update_Notification.Preview_Text")
	UpdateNotificationButton = Language.String(This.Mod.Namespace + ".System.Distribution.Update_Notification.Button")

	def __init__ (self, distributionIdentifier: str, updatesFileURL: str, releaseURLCallback: typing.Callable[[Mods.Mod], str], previewURLCallback: typing.Optional[typing.Callable[[Mods.Mod], str]] = None,
				  tickerInterval: float = 1800, tickerDelay: float = 10):
		"""
		:param distributionIdentifier: This distributor's identifier, the identifier used to determine if updates should be checked for a certain mod.
		This object will look for all mods with the same 'Distribution' value as this identifier.
		:type distributionIdentifier: str
		:param updatesFileURL: The url at which the update distributor object can find the update information file.
		:type updatesFileURL: str
		:param releaseURLCallback: A callback that needs to output a string leading to a URL where the user can download the mod's new release version
		when given the mod's reference object.
		:type releaseURLCallback: typing.Callable[[Mods.Mod], str]
		:param previewURLCallback: A callback that needs to output a string leading to a URL where the user can download the mod's new preview version
		when given the mod's reference object. If this value is None the release URL callback will be used instead.
		:type previewURLCallback: typing.Optional[typing.Callable[[Mods.Mod], str]]
		:param tickerInterval: The time in seconds between each time this will check for updates.
		:type tickerInterval: float
		:param tickerDelay: The time in seconds from the first time a zone is loaded to the first time this checks for an update.
		:type tickerDelay: float
		"""

		super().__init__(distributionIdentifier, tickerInterval = tickerInterval, tickerDelay = tickerDelay)

		self.UpdatesFileURL = updatesFileURL  # type: str

		self.ReleaseURLCallback = releaseURLCallback  # type: typing.Callable[[Mods.Mod], str]
		self.PreviewURLCallback = previewURLCallback  # type: typing.Optional[typing.Callable[[Mods.Mod], str]]

		self._shownReleaseVersions = dict()  # type: typing.Dict[Mods.Mod, typing.List[Version.Version]]
		self._shownPreviewVersions = dict()  # type: typing.Dict[Mods.Mod, typing.List[Version.Version]]

		_RegisterUpdateDistributor(self)

	def _CheckDistribution (self) -> None:
		try:
			self._CheckUpdates()
		except:
			Debug.Log("Failed to check for updates for distribution identifier '" + self.DistributionIdentifier + "''.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

	def _CheckUpdates (self) -> None:
		previewAvailableMods = list()  # type: typing.List[typing.Tuple[Mods.Mod, Version.Version]]
		releaseAvailableMods = list()  # type: typing.List[typing.Tuple[Mods.Mod, Version.Version]]

		distributeUpdatesValues = Settings.CheckForUpdates.Get()  # type: typing.Dict[str, bool]
		distributePreviewUpdatesValues = Settings.CheckForPreviewUpdates.Get()  # type: typing.Dict[str, bool]

		modsToCheck = False  # type: bool

		for mod in Mods.GetAllMods():  # type: Mods.Mod
			if not mod.ReadInformation:
				continue

			if mod.Distribution is None:
				continue

			if mod.Distribution != self.DistributionIdentifier:
				continue

			distributeUpdates = distributeUpdatesValues.get(mod.Namespace, Settings.CheckForUpdates.Default)  # type: bool

			if distributeUpdates:
				modsToCheck = True

		if not modsToCheck:
			return

		try:
			latestDictionary = self._ReadVersionFile(self.UpdatesFileURL)  # type: typing.Dict[str, typing.Dict[str, Version.Version]]
		except:
			Debug.Log("Failed to get mod versions.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			return

		for mod in Mods.GetAllMods():  # type: Mods.Mod
			if not mod.ReadInformation:
				continue

			if mod.Distribution != self.DistributionIdentifier:
				continue

			distributeUpdates = distributeUpdatesValues.get(mod.Namespace, Settings.CheckForUpdates.Default)  # type: bool
			distributePreviewUpdates = distributePreviewUpdatesValues.get(mod.Namespace, Settings.CheckForPreviewUpdates.Default)  # type: bool

			if not distributeUpdates:
				continue

			modShownReleaseVersions = self._shownReleaseVersions.get(mod)  # type: list

			if modShownReleaseVersions is None:
				modShownReleaseVersions = list()
				self._shownReleaseVersions[mod] = modShownReleaseVersions

			modShownPreviewVersions = self._shownPreviewVersions.get(mod)  # type: list

			if modShownPreviewVersions is None:
				modShownPreviewVersions = list()
				self._shownPreviewVersions[mod] = modShownPreviewVersions

			try:
				modVersions = latestDictionary.get(mod.Namespace)  # type: Version

				if modVersions is None:
					Debug.Log("Missing version data for '" + mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
					continue

				releaseVersion = modVersions.get("Release")  # type: Version.Version

				if releaseVersion is None:
					Debug.Log("Missing release version for '" + mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
					releaseVersion = Version.Version("0.0.0.0")

				if distributePreviewUpdates:
					previewVersion = modVersions.get("Preview")  # type: Version.Version

					if previewVersion is None:
						previewVersion = Version.Version("0.0.0.0")

					if previewVersion <= releaseVersion:
						if not releaseVersion in modShownReleaseVersions:
							if mod.Version < releaseVersion:
								releaseAvailableMods.append((mod, releaseVersion))
								continue
					else:
						if not previewVersion in modShownPreviewVersions:
							if mod.Version < previewVersion:
								previewAvailableMods.append((mod, previewVersion))
								continue
				else:
					if not releaseVersion in modShownReleaseVersions:
						if mod.Version < releaseVersion:
							releaseAvailableMods.append((mod, releaseVersion))
							continue

			except:
				Debug.Log("Failed to get update information for '" + mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

		for releaseTuple in releaseAvailableMods:  # type: typing.Tuple[Mods.Mod, Version.Version]
			try:
				self._ShowUpdate(releaseTuple[0], releaseTuple[1], False)
			except:
				Debug.Log("Failed to show release update notification for '" + releaseTuple[0].Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

		for previewTuple in previewAvailableMods:  # type: typing.Tuple[Mods.Mod, Version.Version]
			try:
				self._ShowUpdate(previewTuple[0], previewTuple[1], True)
			except:
				Debug.Log("Failed to show release update notification for '" + previewTuple[0].Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

	def _ReadVersionFile (self, versionsFileURL: str) -> typing.Dict[str, typing.Dict[str, Version.Version]]:
		with request.urlopen(versionsFileURL) as versionsFile:  # type: client.HTTPResponse
			versionsDictionaryString = versionsFile.read().decode("utf-8")  # type: str

		if not versionsDictionaryString or versionsDictionaryString.isspace():
			raise Exception("Latest versions file at '" + versionsFileURL + "' is empty or whitespace.")

		try:
			versionDictionary = json.JSONDecoder().decode(versionsDictionaryString)  # type: typing.Dict[str, typing.Dict[str, typing.Any]]

			if not isinstance(versionDictionary, dict):
				raise Exceptions.IncorrectTypeException(versionDictionary, "Root", (dict,))

			for mod, modLatest in versionDictionary.items():  # type: str, typing.Dict[str, typing.Any]
				if not isinstance(mod, str):
					raise Exceptions.IncorrectTypeException(mod, "Root[Key]", (str,))

				if not isinstance(modLatest, dict):
					raise Exceptions.IncorrectTypeException(mod, "Root[%s]" % mod, (dict,))

				if "Release" in modLatest:
					modLatest["Release"] = Version.Version(modLatest["Release"])

				if "Preview" in modLatest:
					modLatest["Preview"] = Version.Version(modLatest["Preview"])
		except Exception as e:
			raise Exception("Failed to decode latest version file at '" + versionsFileURL + "'.") from e

		return versionDictionary

	def _ShowUpdate (self, mod: Mods.Mod, version: Version.Version, isPreview: bool) -> None:
		if isPreview:
			if self.PreviewURLCallback is not None:
				updateURL = self.PreviewURLCallback(mod)  # type: str
			else:
				updateURL = self.ReleaseURLCallback(mod)  # type: str
		else:
			updateURL = self.ReleaseURLCallback(mod)  # type: str

		showUpdateResponseCommand = collections.make_immutable_slots_class(("command", "arguments"))

		showUpdateResponseArguments = [
			collections.make_immutable_slots_class(("arg_value", "arg_type"))
		]

		showUpdateResponseArguments[0] = showUpdateResponseArguments[0]({
			"arg_value": codecs.encode(bytearray(updateURL, "utf-8"), "hex").decode("utf-8"),
			"arg_type": ui_dialog.CommandArgType.ARG_TYPE_STRING
		})

		showUpdateResponseCommand = showUpdateResponseCommand({
			"command": This.Mod.Namespace.lower() + ".distribution.show_url",
			"arguments": showUpdateResponseArguments
		})

		showUpdateResponse = ui_dialog.UiDialogResponse(
			text = self.UpdateNotificationButton.GetCallableLocalizationString(),
			ui_request = ui_dialog.UiDialogResponse.UiDialogUiRequest.SEND_COMMAND,
			response_command = showUpdateResponseCommand
		)

		if isPreview:
			notificationArguments = {
				"title": self.UpdateNotificationTitle.GetCallableLocalizationString(mod.Author + " - " + mod.Name),
				"text": self.UpdateNotificationPreviewText.GetCallableLocalizationString(str(version)),

				"ui_responses": (showUpdateResponse,)
			}
		else:
			notificationArguments = {
				"title": self.UpdateNotificationTitle.GetCallableLocalizationString(mod.Author + " - " + mod.Name),
				"text": self.UpdateNotificationReleaseText.GetCallableLocalizationString(str(version)),

				"ui_responses": (showUpdateResponse,)
			}

		Notifications.ShowNotification(queue = True, **notificationArguments)

		if isPreview:
			modShownPreviewVersions = self._shownPreviewVersions.get(mod)  # type: list

			if modShownPreviewVersions is None:
				modShownPreviewVersions = list()
				self._shownPreviewVersions[mod] = modShownPreviewVersions

			if not version in modShownPreviewVersions:
				modShownPreviewVersions.append(version)
		else:
			modShownReleaseVersions = self._shownReleaseVersions.get(mod)  # type: list

			if modShownReleaseVersions is None:
				modShownReleaseVersions = list()
				self._shownReleaseVersions[mod] = modShownReleaseVersions

			if not version in modShownReleaseVersions:
				modShownReleaseVersions.append(version)

class PromotionDistributor(_Distributor):
	"""
	For displaying promotional material, I highly recommend limiting the promotions you display to major events only. Showing too many promotions too frequently
	may cause players to want to disable promotional notifications.
	"""

	PromotionDefaultTitle = Language.String(This.Mod.Namespace + ".System.Distribution.Promotions.Default.Title")
	PromotionDefaultButton = Language.String(This.Mod.Namespace + ".System.Distribution.Promotions.Default.Button")

	def __init__ (self, distributionIdentifier: str, promotionsFileURL: str, tickerInterval: float = 1800, tickerDelay: float = 10):
		"""
		:param distributionIdentifier: This distributor's identifier, the identifier used to separate persistent data made by this promotion distributor.
		:type distributionIdentifier: str
		:param promotionsFileURL: The url at which the update distributor object can find the promotion information file.
		:type promotionsFileURL: str
		:param tickerInterval: The time in seconds between each time this will check for new promotions.
		:type tickerInterval: float
		:param tickerDelay: The time in seconds from the first time a zone is loaded to the first time this checks for a promotion.
		:type tickerDelay: float
		"""

		super().__init__(distributionIdentifier, tickerInterval = tickerInterval, tickerDelay = tickerDelay)

		self.PromotionsFileURL = promotionsFileURL  # type: str

		self._showedPromotion = False  # type: bool

		self._shownPromotionsFilePath = os.path.join(Paths.PersistentPath, "Distribution", distributionIdentifier, "ShownPromotions.json")  # type: str
		self._shownPromotions = list()  # type: typing.List[str]

		if os.path.exists(self._shownPromotionsFilePath):
			try:
				with open(self._shownPromotionsFilePath) as shownPromotionsFile:
					shownPromotions = json.JSONDecoder().decode(shownPromotionsFile.read())

					if not isinstance(shownPromotions, list):
						raise Exceptions.IncorrectTypeException(shownPromotions, "Root", (list,))

					for shownPromotionIndex in range(len(shownPromotions)):  # type: int
						if not isinstance(shownPromotions[shownPromotionIndex], str):
							raise Exceptions.IncorrectTypeException(shownPromotions[shownPromotionIndex], "Root[%d]" % shownPromotionIndex, (str,))

					self._shownPromotions = shownPromotions
			except:
				Debug.Log("Failed to read shown promotions file.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

		_RegisterPromotionDistributor(self)

	def _CheckDistribution (self) -> None:
		try:
			if not self._showedPromotion:
				self._CheckPromotions()
		except:
			Debug.Log("Failed to check for promotions.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

	def _CheckPromotions (self) -> None:
		showPromotions = Settings.ShowPromotions.Get()  # type: bool

		if not showPromotions:
			return

		try:
			promotionsList = self._ReadPromotionsFile(self.PromotionsFileURL)  # type: typing.List[dict]
		except:
			Debug.Log("Failed to get promotions.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			return

		validPromotions = list()  # type: typing.List[_Promotion]

		for promotionDictionary in promotionsList:  # type: typing.Dict
			promotion = _Promotion(promotionDictionary)  # type: _Promotion

			if promotion.CanShow(self._shownPromotions):
				validPromotions.append(promotion)

		if len(validPromotions) == 0:
			return

		chosenPromotion = random.choice(validPromotions)  # type: _Promotion

		try:
			self._ShowPromotion(chosenPromotion)
		except:
			Debug.Log("Failed to show promotion notification for promotion '" + chosenPromotion.Identifier + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			return

		self._showedPromotion = True
		self._shownPromotions.append(chosenPromotion.Identifier)

		try:
			shownPromotionsDirectory = os.path.dirname(self._shownPromotionsFilePath)  # type: str

			if not os.path.exists(shownPromotionsDirectory):
				os.makedirs(shownPromotionsDirectory)

			with open(self._shownPromotionsFilePath, "w+") as shownPromotionsFile:
				shownPromotionsFile.write(json.JSONEncoder(indent = "\t").encode(self._shownPromotions))
		except:
			Debug.Log("Failed to write shown promotions to a file.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			return

	def _ReadPromotionsFile (self, promotionsFileURL: str) -> typing.List[dict]:
		with request.urlopen(promotionsFileURL) as promotionsFile:  # type: client.HTTPResponse
			promotionsListString = promotionsFile.read().decode("utf-8")  # type: str

		if not promotionsListString or promotionsListString.isspace():
			raise Exception("Promotions file at '" + promotionsFileURL + "' is empty or whitespace.")

		try:
			promotionsList = json.JSONDecoder().decode(promotionsListString)  # type: typing.List[dict]

			if not isinstance(promotionsList, list):
				raise Exceptions.IncorrectTypeException(promotionsList, "Root", (list,))

			for promotionIndex in range(len(promotionsList)):
				if not isinstance(promotionsList[promotionIndex], dict):
					raise Exceptions.IncorrectTypeException(promotionsList[promotionIndex], "Root[%d]" % promotionIndex, (dict,))

				if not "Identifier" in promotionsList[promotionIndex]:
					raise Exception("Missing dictionary entry 'Identifier' in 'Root[%d]'." % promotionIndex)

				if not isinstance(promotionsList[promotionIndex]["Identifier"], str):
					raise Exceptions.IncorrectTypeException(promotionsList[promotionIndex]["Identifier"], "Root[%d][Identifier]" % promotionIndex, (str,))

				promotionIndex += 1
		except Exception as e:
			raise Exception("Failed to decode promotions file at '" + promotionsFileURL + "'.") from e

		return promotionsList

	def _ShowPromotion (self, promotion: _Promotion) -> None:
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

def _RegisterUpdateDistributor (updateDistributor: UpdateDistributor) -> None:
	for existingUpdateDistributor in _updateDistributors:  # type: UpdateDistributor
		if existingUpdateDistributor.DistributionIdentifier == updateDistributor.DistributionIdentifier:
			Debug.Log("Multiple update distributors with the identifier '" + updateDistributor.DistributionIdentifier + "' exist, its might cause problems.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

	_updateDistributors.append(updateDistributor)

def _RegisterPromotionDistributor (promotionDistributor: PromotionDistributor) -> None:
	for existingPromotionDistributor in _promotionDistributors:  # type: PromotionDistributor
		if existingPromotionDistributor.DistributionIdentifier == promotionDistributor.DistributionIdentifier:
			Debug.Log("Multiple promotion distributors with the identifier '" + promotionDistributor.DistributionIdentifier + "' exist, its might cause problems.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

	_promotionDistributors.append(promotionDistributor)