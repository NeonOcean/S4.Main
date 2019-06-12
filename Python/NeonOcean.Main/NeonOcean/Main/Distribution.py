from NeonOcean.Main import Information, Mods, Websites
from NeonOcean.Main.Tools import Distribution

_distributionURL = "http://dist.mods.neonoceancreations.com"  # type: str

_updateDistributor = None  # type: Distribution.UpdateDistributor
_promotionsDistributor = None  # type: Distribution.PromotionDistributor

def _Setup () -> None:
	global _updateDistributor, _promotionsDistributor

	updatesFileURL = _distributionURL + "/mods/latest.json"  # type: str
	promotionsFileURL = _distributionURL + "/promotions/promotions.json"  # type: str

	_updateDistributor = Distribution.UpdateDistributor(Information.RootNamespace, updatesFileURL, _GetModReleaseURL, previewURLCallback = _GetModPreviewURL, tickerDelay = 15)
	_promotionsDistributor = Distribution.PromotionDistributor(Information.RootNamespace, promotionsFileURL, tickerDelay = 20)

def _GetModReleaseURL (mod: Mods.Mod) -> str:
	return Websites.GetNOMainModURL(mod)

def _GetModPreviewURL (mod: Mods.Mod) -> str:
	return Websites.GetNOSupportModPreviewPostsURL(mod)

_Setup()
