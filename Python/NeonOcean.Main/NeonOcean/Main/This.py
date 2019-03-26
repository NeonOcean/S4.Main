from NeonOcean.Main import Mods

try:
	Mod = Mods.Main  # type: Mods.Mod
except Exception as e:
	raise Exception("Cannot find self in mod list.") from e
