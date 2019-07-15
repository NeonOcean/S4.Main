import os

from NeonOcean.Main import Paths
from NeonOcean.Main.Tools import Version

def _GetGameVersion () -> Version.Version:
	try:
		with open(os.path.join(Paths.UserDataPath, "GameVersion.txt"), "rb") as versionFile:
			return Version.Version(versionFile.read()[4:].decode("utf-8"))
	except Exception:
		return Version.Version("0.0.0.0")

GameVersion = _GetGameVersion()  # type: Version.Version
