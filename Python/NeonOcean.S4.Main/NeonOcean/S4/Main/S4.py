from __future__ import annotations

import os

from NeonOcean.S4.Main import Paths
from NeonOcean.S4.Main.Tools import Version

def _GetGameVersion () -> Version.Version:
	try:
		with open(os.path.join(Paths.UserDataPath, "GameVersion.txt"), "rb") as versionFile:
			return Version.Version(versionFile.read()[4:].decode("utf-8"), translate = True)
	except Exception:
		return Version.Version()

GameVersion = _GetGameVersion()  # type: Version.Version
