from __future__ import annotations

from NeonOcean.S4.Main import Information, DistributionShared

_distributionURL = "http://dist.mods.neonoceancreations.com"  # type: str

_updateDistributor: DistributionShared.UpdateDistributor
_promotionsDistributor: DistributionShared.PromotionDistributor

def _Setup () -> None:
	global _updateDistributor, _promotionsDistributor

	promotionsFileURL = _distributionURL + "/promotions/promotions.json"  # type: str

	_updateDistributor = DistributionShared.UpdateDistributor(Information.RootNamespace)
	_promotionsDistributor = DistributionShared.PromotionDistributor(Information.RootNamespace, promotionsFileURL, tickerDelay = 25)

_Setup()
