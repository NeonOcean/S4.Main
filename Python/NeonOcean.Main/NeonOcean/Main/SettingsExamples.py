"""
Below is a pre-made settings setup layered on top of the persistence system. You should feel free to reuse this in your own mod.
I employ this setup in my own mods, though the section below is only a blank version with no settings defined.
To make new settings, you should create classes that inherit the Setting class, make sure the IsSetting value is set to true and necessary values are filled
If you want to see more complex examples of this system in use, check out the settings module in Main or in my other mods.
"""

# noinspection SpellCheckingInspection
"""
import os
import typing

from NeonOcean.Main import This # Make sure this points to your own mod.
from NeonOcean.Main import Debug, Language, LoadingShared, SettingsShared
from NeonOcean.Main.Data import Persistence
from NeonOcean.Main.Tools import Version
from NeonOcean.Main.UI import Settings as SettingsUI
from sims4 import localization

SettingsPath = os.path.join(This.Mod.PersistentPath, "Settings.json")  # type: str

_settings = None  # type: Persistence.Persistent
_allSettings = list()  # type: typing.List[typing.Type[Setting]]

class Setting(SettingsShared.SettingBase):
	IsSetting = False  # type: bool
	
	# Make sure these three values exist in a setting, if they don't there will be an exception.
	# What you see below doesn't create the value in the class, it only serves as hints to IDEs like Pycharm that they should exist.
	Key: str
	Type: typing.Type
	Default: typing.Any
	
	Dialog: typing.Type[SettingsUI.SettingDialog]

	def __init_subclass__ (cls, **kwargs):		
		super().OnInitializeSubclass()

		if cls.IsSetting:
			cls.SetDefault()
			_allSettings.append(cls)

	@classmethod
	def Setup (cls) -> None:
		_Setup(cls.Key,
			  cls.Type,
			  cls.Default,
			  cls.Verify)

	@classmethod
	def isSetup (cls) -> bool:
		return _isSetup(cls.Key)

	@classmethod
	def Get (cls):
		# Get the value from the persitance system, if you so wish, you may even override this method to do something extra before the value sent out.
		# All requests to get the setting data should be funneled through here.
		
		return _Get(cls.Key)

	@classmethod
	def Set (cls, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
		# Set the value from the persitance system, if you so wish, you may even override this method to do something extra before the value is set.
		# All requests to set the setting data should be funneled through here.
	
		return _Set(cls.Key, value, autoSave = autoSave, autoUpdate = autoUpdate)

	@classmethod
	def Reset (cls) -> None:
		Reset(cls.Key)

	@classmethod
	def Verify (cls, value: typing.Any, lastChangeVersion: Version.Version = None) -> typing.Any:
		return value

	@classmethod
	def IsActive (cls) -> bool:
		return True

	@classmethod
	def ShowDialog (cls):
		if not hasattr(cls, "Dialog"):
			return

		if cls.Dialog is None:
			return

		cls.Dialog.ShowDialog(cls)

	@classmethod
	def GetName(cls) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".System.Settings.Values." + cls.Key + ".Name")

def GetAllSettings () -> typing.List[typing.Type[Setting]]:
	return _allSettings

# Many functions, such as the six below are just simple wrappers that settings call to manipulate the underlying persistence system, information on their 
# use is avaliable in the persistence module.

def Load () -> None:
	_settings.Load()

def Save () -> None:
	_settings.Save()

def Reset (key: str = None) -> None:
	_settings.Reset(key = key)

def Update () -> None:
	_settings.Update()

def RegisterUpdate (update: typing.Callable) -> None:
	_settings.RegisterUpdate(update)

def UnregisterUpdate (update: typing.Callable) -> None:
	_settings.UnregisterUpdate(update)

def _OnInitiate (cause: LoadingShared.LoadingCauses) -> None:
# _OnInitiate and _OnUnload are functions that are called by the Loading module in Main, if you do not use the loading system to load your mod you likely need to 
# relace these or this setting setup will not function.

	global _settings

	if cause:
		pass

	if _settings is None:
		_settings = Persistence.Persistent(SettingsPath, This.Mod.Version, hostNamespace = This.Mod.Namespace)

		for setting in _allSettings:
			setting.Setup()

	Load()

def _OnUnload (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	try:
		Save()
	except:
		Debug.Log("Failed to save settings.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _OnReset () -> None:
	Reset()

def _OnResetSettings () -> None:
	Reset()

def _Setup (key: str, valueType: type, default, verify: typing.Callable) -> None:
	_settings.Setup(key, valueType, default, verify)

def _isSetup (key: str) -> bool:
	return _settings.isSetup(key)

def _Get (key: str) -> typing.Any:
	# This function is used to get the value from the persistence system. It is marked as a protected function as it is not recommended to get a value directly
	# through this. You instead use the method in the setting its self instead.

	return _settings.Get(key)

def _Set (key: str, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
	# This function is used to set the value in the persistence system. It is marked as a protected function as it is not recommended to set a value directly
	# through this. You instead use the method in the setting its self instead.

	_settings.Set(key, value, autoSave = autoSave, autoUpdate = autoUpdate)
"""



# noinspection SpellCheckingInspection
"""
# This is an example of a simple boolean setting with no dialog system attached.
# It should work with the system above with no additional effort beyond copying and pasting them both into a Python file.

class BooleanSetting(Setting):
	# Its a good idea to use setting type bases like this one, you won't have to include duplicate functions or classes in every setting.
	# This also shows the function of the IsSetting value as it will allow you to create bases for settings without the system thinking the base is a setting.

	Type = bool

	@classmethod
	def Verify (cls, value: bool, lastChangeVersion: Version.Version = None) -> bool:	
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		if not isinstance(lastChangeVersion, Version.Version) and lastChangeVersion is not None:
			raise Exceptions.IncorrectTypeException(lastChangeVersion, "lastChangeVersion", (Version.Version, "None"))

		return value
	
class SimpleBooleanSetting(BooleanSetting):
	IsSetting = True  # type: bool

	Key = "Simple_Boolean_Setting"  # type: str
	Default = True  # type: bool
"""
