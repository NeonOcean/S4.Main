from __future__ import annotations

from NeonOcean.S4.Main.Tools import Exceptions
from sims import sim_info

def GetFullName (simInfo: sim_info.SimInfo) -> str:
	"""
	Get this sim's full name. The full name method within the sim info class doesn't seem to actually do anything.
	"""

	if not isinstance(simInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(simInfo, "simInfo", (sim_info.SimInfo,))

	# noinspection PyPropertyAccess
	simFirstName = simInfo.first_name
	# noinspection PyPropertyAccess
	simLastName = simInfo.last_name

	if not simFirstName:
		return simLastName if simLastName else ""
	else:
		return simFirstName + " " + simLastName if simLastName else simFirstName

def HasTraitByID (simInfo: sim_info.SimInfo, traitID: int) -> bool:
	if not isinstance(simInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(simInfo, "simInfo", (sim_info.SimInfo,))

	if not isinstance(traitID, int):
		raise Exceptions.IncorrectTypeException(traitID, "traitID", (int,))

	for simTrait in simInfo.get_traits():
		if hasattr(simTrait, "guid64"):

			if simTrait.guid64 == traitID:
				return True

	return False
