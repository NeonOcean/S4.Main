from __future__ import annotations

import typing

import services
from NeonOcean.S4.Main.Saving import SectionBranched
from NeonOcean.S4.Main.Tools import Sims as ToolsSims
from sims import sim, sim_info

class SectionSims(SectionBranched.SectionBranched):
	@property
	def NameKey (self) -> str:
		return "--Name"

	def Save (self) -> typing.Tuple[bool, dict]:
		callbackSuccessful = self._ActivateSaveCallbacks()  # type: bool

		for branchKey, branchDictionary in self._loadedData.items():
			try:
				branchSimID = int(branchKey)  # type: int
				branchSim = services.sim_info_manager().get(branchSimID)  # type: sim.Sim
				branchSimInfo = branchSim.sim_info  # type: sim_info.SimInfo

				branchDictionary[self.NameKey] = ToolsSims.GetFullName(branchSimInfo)
			except:
				continue

		return callbackSuccessful, self._loadedData

	def Set (self, branch: str, key: str, value) -> None:
		"""
		Set the value of the section data specified by the key and branch. The value is deep copied before being but into storage, modifying the value after setting
		it will not change the stored version. All values must be able to be encoded by python's json modules.

		You may not set to the key '--Name' or an exception will be raised.

		:param branch: The name of the branch to set the value to.
		:type branch: str
		:param key: The name of the section data, is case sensitive.
		:type key: str
		:param value: The value the section data will be changing to. This must be able to be encoded by python's json modules.
		:rtype: None
		"""

		if key == self.NameKey:
			raise ValueError("The parameter 'key' may not have the value '" + self.NameKey + "'.")

		super().Set(branch, key, value)

	def SetAllBranches (self, key: str, value) -> None:
		"""
		Set the value of the section data specified by the key in all branches. The value is deep copied before being but into storage, modifying the value after
		setting it will not change the stored version. All values must be able to be encoded by python's json modules.

		You may not set to the key '--Name' or an exception will be raised.

		:param key: The name of the section data, is case sensitive.
		:type key: str
		:param value: The value the section data will be changing to. This must be able to be encoded by python's json modules.
		:rtype: None
		"""

		if key == self.NameKey:
			raise ValueError("The parameter 'key' may not have the value '" + self.NameKey + "'.")

		super().SetAllBranches(key, value)
