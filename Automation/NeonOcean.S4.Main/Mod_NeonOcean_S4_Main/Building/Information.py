from Mod_NeonOcean_S4_Main import Mod
from Mod_NeonOcean_S4_Main.Tools import Information

def BuildInformation () -> bool:
	if not Information.CanBuildInformation():
		return True

	Information.BuildInformation(Mod.GetCurrentMod().InformationSourceFilePath, Mod.GetCurrentMod().InformationBuildFilePath)

	return True
