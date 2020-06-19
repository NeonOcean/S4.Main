from __future__ import annotations

import enum_lib
import typing

from sims4.tuning import tunable, tunable_base

class TunablePythonEnumEntry(tunable.Tunable):
	# noinspection SpellCheckingInspection
	TAGNAME = tunable_base.Tags.Enum
	LOADING_TAG_NAME = tunable_base.LoadingTags.Enum

	__slots__ = ('cache_key', 'EnumType', 'InvalidEnums')

	def __init__ (self, enumType: typing.Type[enum_lib.Enum], default: typing.Union[enum_lib.Enum, str], *args, invalidEnums: typing.Tuple[typing.Union[enum_lib.Enum, str], ...] = (), **kwargs):
		"""
		A python enum version of the game's tunable enum entry.
		"""

		if not isinstance(enumType, type) or not issubclass(enumType, enum_lib.Enum):
			raise tunable_base.MalformedTuningSchemaError('Must provide a python enum type to TunablePythonEnumEntry')

		if isinstance(default, enum_lib.Enum):
			default = default.name

		# noinspection PyTypeChecker
		self.EnumType = enumType  # type: typing.Type[enum_lib.Enum]
		self.InvalidEnums = invalidEnums  # type: typing.Tuple[typing.Union[enum_lib.EnumMeta, str], ...]

		super().__init__(tunable_type = str, default = default, *args, **kwargs)

		self.cache_key = "TunablePythonEnumEntry_{}_{}".format(enumType.__name__, self.default)

	def _export_default (self, value):
		if isinstance(value, self.EnumType):
			return value.name

		return super()._export_default(value)

	def export_desc (self):
		export_dict = super().export_desc()  # type: dict
		export_dict[tunable_base.Attributes.Type] = self.get_exported_type_name()

		if self.InvalidEnums:
			export_dict[tunable_base.Attributes.InvalidEnumEntries] = ','.join(self._export_default(invalidEnum) for invalidEnum in self.InvalidEnums)

		return export_dict

	def _convert_to_value (self, content):
		if content is None:
			return

		return self.EnumType[content]

class TunablePythonEnumSet(tunable.TunableSet):
	__slots__ = ('_enumType', 'AllowEmptySet')

	def __init__ (
			self,
			enumType: typing.Type[enum_lib.Enum],
			enumDefault: typing.Optional[enum_lib.Enum] = None,
			invalidEnums: typing.Tuple[typing.Union[enum_lib.Enum, str], ...] = (),
			defaultEnumList: typing.FrozenSet[enum_lib.Enum] = frozenset(),
			allowEmptySet: bool = False,
			**kwargs):

		"""
		A python enum version of the game's tunable enum set.
		"""

		if enumDefault is None:
			enumDefault = list(enumType.__members__.keys())[0]

		super().__init__(tunable = TunablePythonEnumEntry(enumType = enumType, default = enumDefault, invalidEnums = invalidEnums), **kwargs)

		self._enumType = enumType
		self.AllowEmptySet = allowEmptySet
		self._default = defaultEnumList

	def export_desc (self):
		export_dict = super().export_desc()  # type: typing.Dict

		if self._default:
			export_dict[tunable_base.Attributes.Default] = self._export_default(self.default)

		return export_dict

	def _export_default (self, value):
		return ','.join(e.name for e in value)

	def load_etree_node (self, node, source, expect_error):
		value = super().load_etree_node(node, source, expect_error)

		if not self.AllowEmptySet and len(value) <= 0:
			name = '<UNKNOWN ITEM>'  # type: str

			if node is not None:
				name = node.get(tunable.LoadingAttributes.Name, name)

			tunable.logger.error('Error parsing enum set for {}: No enums specified for {}', source, name)

		return value
