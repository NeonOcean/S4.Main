import typing

import services
import zone
from NeonOcean.Main import Director, This
from NeonOcean.Main.Tools import Exceptions
from sims import sim
from ui import ui_dialog, ui_dialog_generic, ui_dialog_picker

_queue = list()  # type: typing.List[ui_dialog.UiDialogBase]

class _Announcer(Director.Announcer):
	Host = This.Mod

	@classmethod
	def OnLoadingScreenAnimationFinished (cls, zoneReference: zone.Zone) -> None:
		global _queue

		from NeonOcean.Main import Debug

		for dialog in _queue:  # type: ui_dialog.UiDialogBase
			try:
				dialog.show_dialog()
			except:
				Debug.Log("Failed to show a queued dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

		_queue = list()

def ShowOkDialog (callback: typing.Callable = None, queue: bool = True, **dialogArguments) -> None:
	"""
	:param callback: Called after the dialog gets a response from the user. This will never be called it the dialog has no responses.
	 				 The callback function will receive one argument; a reference to the dialog.
	:type callback: typing.Callable
	:param queue: When true and the UI dialog service is not running the dialog will be put in queue until it is. Otherwise the dialog will be ignored.
				  The ui dialog service will only run while a zone is loaded.
	:type queue: bool
	"""

	if not isinstance(callback, typing.Callable) and callback is not None:
		raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

	if not isinstance(queue, bool):
		raise Exceptions.IncorrectTypeException(queue, "queue", (bool,))

	if not "owner" in dialogArguments:
		dialogArguments["owner"] = None

	dialog = ui_dialog.UiDialogOk.TunableFactory().default(**dialogArguments)  # type: ui_dialog.UiDialogOk

	if callback is not None:
		dialog.add_listener(callback)

	if services.current_zone() is not None:
		dialog.show_dialog()
	else:
		if queue:
			_queue.append(dialog)

def ShowOkCancelDialog (callback: typing.Callable = None, queue: bool = True, **dialogArguments) -> None:
	"""
	:param callback: Called after the dialog gets a response from the user. This will never be called it the dialog has no responses.
	 				 The callback function will receive one argument; a reference to the dialog.
	:type callback: typing.Callable
	:param queue: When true and the UI dialog service is not running the dialog will be put in queue until it is. Otherwise the dialog will be ignored.
				  The ui dialog service will only run while a zone is loaded.
	:type queue: bool
	"""

	if not isinstance(callback, typing.Callable) and callback is not None:
		raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

	if not isinstance(queue, bool):
		raise Exceptions.IncorrectTypeException(queue, "queue", (bool,))

	if not "owner" in dialogArguments:
		dialogArguments["owner"] = None

	dialog = ui_dialog.UiDialogOkCancel.TunableFactory().default(**dialogArguments)  # type: ui_dialog.UiDialogOkCancel

	if callback is not None:
		dialog.add_listener(callback)

	if services.current_zone() is not None:
		dialog.show_dialog()
	else:
		if queue:
			_queue.append(dialog)

def ShowOkInputDialog (callback: typing.Callable = None, queue: bool = True, **dialogArguments) -> None:
	"""
	:param callback: Called after the dialog gets a response from the user. This will never be called it the dialog has no responses.
	 				 The callback function will receive one argument; a reference to the dialog.
	:type callback: typing.Callable
	:param queue: When true and the UI dialog service is not running the dialog will be put in queue until it is. Otherwise the dialog will be ignored.
				  The ui dialog service will only run while a zone is loaded.
	:type queue: bool
	"""

	if not isinstance(callback, typing.Callable) and callback is not None:
		raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

	if not isinstance(queue, bool):
		raise Exceptions.IncorrectTypeException(queue, "queue", (bool,))

	if not "owner" in dialogArguments:
		dialogArguments["owner"] = None

	dialog = ui_dialog_generic.UiDialogTextInputOk.TunableFactory().default(**dialogArguments)  # type: ui_dialog_generic.UiDialogTextInputOk

	if callback is not None:
		dialog.add_listener(callback)

	if services.current_zone() is not None:
		dialog.show_dialog()
	else:
		if queue:
			_queue.append(dialog)

def ShowOkCancelInputDialog (callback: typing.Callable = None, queue: bool = True, **dialogArguments) -> None:
	"""
	:param callback: Called after the dialog gets a response from the user. This will never be called it the dialog has no responses.
	 				 The callback function will receive one argument; a reference to the dialog.
	:type callback: typing.Callable
	:param queue: When true and the UI dialog service is not running the dialog will be put in queue until it is. Otherwise the dialog will be ignored.
				  The ui dialog service will only run while a zone is loaded.
	:type queue: bool
	"""

	if not isinstance(callback, typing.Callable) and callback is not None:
		raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

	if not isinstance(queue, bool):
		raise Exceptions.IncorrectTypeException(queue, "queue", (bool,))

	if not "owner" in dialogArguments:
		dialogArguments["owner"] = None

	dialog = ui_dialog_generic.UiDialogTextInputOkCancel.TunableFactory().default(**dialogArguments)  # type: ui_dialog_generic.UiDialogTextInputOkCancel

	if callback is not None:
		dialog.add_listener(callback)

	if services.current_zone() is not None:
		dialog.show_dialog()
	else:
		if queue:
			_queue.append(dialog)

def ShowObjectPickerDialog (callback: typing.Callable = None, pickerRows: list = None, **dialogArguments) -> None:
	"""
	:param callback: Called after the dialog gets a response from the user. This will never be called it the dialog has no responses.
	 				 The callback function will receive one argument; a reference to the dialog.
	:type callback: typing.Callable

	:param pickerRows: A list of picker row objects sent to the dialog.
	:type pickerRows: list
	"""

	if not isinstance(callback, typing.Callable) and callback is not None:
		raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

	if not "owner" in dialogArguments:
		activeSim = services.get_active_sim()  # type: sim.Sim

		if activeSim is None:
			raise Exception("Cannot find active sim, object picker dialogs cannot be opened without a sim tied to them through the 'owner' value.")

		dialogArguments["owner"] = activeSim.sim_info

	dialog = ui_dialog_picker.UiObjectPicker.TunableFactory().default(**dialogArguments)  # type: ui_dialog_picker.UiObjectPicker

	if pickerRows is not None:
		for pickerRow in pickerRows:
			dialog.add_row(pickerRow)

	if callback is not None:
		dialog.add_listener(callback)

	dialog.show_dialog()

