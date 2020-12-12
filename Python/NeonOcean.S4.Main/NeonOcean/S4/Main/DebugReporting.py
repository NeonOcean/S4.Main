import typing
from NeonOcean.S4.Main import LoadingShared, Reporting, Debug

def _DebugLogCollector () -> typing.List[str]:
	return Debug.ActiveLogger().GetLogFilesToBeReported()

# noinspection PyUnusedLocal
def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	Reporting.RegisterReportFileCollector(_DebugLogCollector)

# noinspection PyUnusedLocal
def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	Reporting.UnregisterReportFileCollector(_DebugLogCollector)