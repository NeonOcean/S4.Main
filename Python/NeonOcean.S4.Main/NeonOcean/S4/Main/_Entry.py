from __future__ import annotations

from NeonOcean.S4.Main import Mods

def _Run () -> None:
	if not Mods.IsInstalled("NeonOcean.Order") and not Mods.IsInstalled("NeonOcean.S4.Order"):
		from NeonOcean.S4.Main import Loading

		Loading.LoadAll()

_Run()