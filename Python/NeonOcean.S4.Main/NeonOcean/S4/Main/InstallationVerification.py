import functools
import typing

import zone
from sims4 import localization, log
from ui import ui_dialog_notification

mainMissingModFileNotificationTitleID = 4215308301  # type: int  # Can't use Language.py since we can't trust it to not throw an exception.
mainMissingModFileNotificationTextID = 3037040933  # type: int

modMissingScriptFilesNotificationTitleID = 2729143438  # type: int
modMissingScriptFilesNotificationTextID = 979387582  # type: int

def _Setup () -> None:
	originalOnLoadingScreenAnimationFinished = zone.Zone.on_loading_screen_animation_finished

	@functools.wraps(originalOnLoadingScreenAnimationFinished)
	def onLoadingScreenAnimationFinished (*args, **kwargs) -> None:
		_ShowNecessaryBadInstallationDialogs()

		originalOnLoadingScreenAnimationFinished(*args, **kwargs)

	zone.Zone.on_loading_screen_animation_finished = onLoadingScreenAnimationFinished

def _MainMissingModFile () -> bool:
	try:
		from NeonOcean.S4.Main import Mods, ThisNamespace
		if Mods.IsInstalled(ThisNamespace.Namespace):
			return False
		else:
			return True
	except:
		return True

def _GetModsMissingScriptFiles () -> list:
	modsMissingScriptFiles = list()  # type: list

	from NeonOcean.S4.Main import Mods

	for mod in Mods.GetAllMods():  # type: Mods.Mod
		for modScriptPath in mod.ScriptPathsIncludingMissing:  # type: str
			if not modScriptPath in mod.ScriptPaths:
				modsMissingScriptFiles.append(mod)
				break

	return modsMissingScriptFiles

def _ShowNecessaryBadInstallationDialogs () -> None:
	try:
		showingMainMissingModFileDialog = _MainMissingModFile()  # type: bool
	except Exception as e:
		log.exception("NeonOcean", "Failed to check if we need to show the main missing mod file dialog.", exc = e, owner = __name__)
		return

	if showingMainMissingModFileDialog:
		try:
			_ShowMainMissingModFileDialog()
		except Exception as e:
			log.exception("NeonOcean", "Failed to show the main missing mod file dialog.", exc = e, owner = __name__)

		return

	try:
		modsMissingScriptFiles = _GetModsMissingScriptFiles()  # type: typing.Optional[list]

		if modsMissingScriptFiles is None:
			pass

	except Exception as e:
		log.exception("NeonOcean", "Failed to check if we need to show the mod script path missing dialog.", exc = e, owner = __name__)
		return

	if len(modsMissingScriptFiles) != 0:
		try:
			_ShowModMissingScriptFilesNotification(modsMissingScriptFiles)
		except Exception as e:
			log.exception("NeonOcean", "Failed to show the mod script path missing notification.", exc = e, owner = __name__)

		return

def _GetDialogLocalizationString (key: int, *tokens) -> typing.Callable[[], localization.LocalizedString]:
	localizationString = localization.LocalizedString()
	localizationString.hash = key
	# noinspection PyUnresolvedReferences
	localization.create_tokens(localizationString.tokens, *tokens)
	return lambda *args, **kwargs: localizationString

def _ShowMainMissingModFileDialog () -> None:
	notificationTitle = _GetDialogLocalizationString(mainMissingModFileNotificationTitleID)
	notificationText = _GetDialogLocalizationString(mainMissingModFileNotificationTextID)

	notificationArguments = {
		"owner": None,
		"title": notificationTitle,
		"text": notificationText,
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}

	notification = ui_dialog_notification.UiDialogNotification.TunableFactory().default(**notificationArguments)
	notification.show_dialog()

def _ShowModMissingScriptFilesNotification (modsMissingScriptFiles: list) -> None:
	modMissingScriptFilesByAuthor = dict()  # type: typing.Dict[str, list]

	for mod in modsMissingScriptFiles:
		modsAuthor = mod.Author.lower()  # type: str

		if modsAuthor in modMissingScriptFilesByAuthor:
			modMissingScriptFilesByAuthor[modsAuthor].append(mod)
		else:
			modMissingScriptFilesByAuthor[modsAuthor] = [mod]

	missingScriptFileMods = ""  # type: str

	for modList in modMissingScriptFilesByAuthor.values():
		if len(modList) == 0:
			continue

		if missingScriptFileMods != "":
			missingScriptFileMods += "\n"

		missingScriptFileMods += modList[0].Author + ":\n"

		for mod in modList:
			missingScriptFileMods += "%s - v%s\n" % (mod.Name, mod.Version)

	notificationTitle = _GetDialogLocalizationString(modMissingScriptFilesNotificationTitleID)
	notificationText = _GetDialogLocalizationString(modMissingScriptFilesNotificationTextID, missingScriptFileMods)

	notificationArguments = {
		"owner": None,
		"title": notificationTitle,
		"text": notificationText,
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}

	notification = ui_dialog_notification.UiDialogNotification.TunableFactory().default(**notificationArguments)
	notification.show_dialog()

_Setup()
