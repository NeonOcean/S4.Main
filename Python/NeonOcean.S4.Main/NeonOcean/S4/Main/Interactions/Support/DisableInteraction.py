from __future__ import annotations

import typing

from NeonOcean.S4.Main.Tools import Exceptions
from event_testing import results, test_base

class DisabledInteractionTest(test_base.BaseTest):
	def __init__ (self, *args, reasonToolTip: typing.Optional[typing.Callable] = None, **kwargs):
		"""
		A test that disables an interaction when added.
		:param args: The regular arguments of the test.
		:type args: tuple
		:param reasonToolTip: A callable object that will return a localized string explaining why the interaction cannot be used. This can be none to indicate
		there is no reason. If there is a reason tooltip, the interaction will appear grayed out. If there is no tooltip, the interaction will not appear at all.
		:type reasonToolTip: typing.Optional[typing.Callable]
		:param kwargs: The regular keyword arguments of the test.
		:type kwargs: dict
		"""

		if not isinstance(reasonToolTip, typing.Callable) and reasonToolTip is not None:
			raise Exceptions.IncorrectTypeException(reasonToolTip, "reasonToolTip", ("Callable", None))

		super().__init__(*args, **kwargs)

		self.ReasonToolTip = reasonToolTip  # type: typing.Optional[typing.Callable]

	# noinspection SpellCheckingInspection
	def __call__ (self):
		return results.TestResult(False, tooltip = self.ReasonToolTip)

	def get_expected_args (self) -> dict:
		return dict()