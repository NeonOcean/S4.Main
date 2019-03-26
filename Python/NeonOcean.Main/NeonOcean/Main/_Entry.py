from NeonOcean.Main import Mods

def _Run () -> None:
	if not Mods.IsInstalled("NeonOcean.Order"):
		from NeonOcean.Main import Loading

		Loading.Load()

_Run()
