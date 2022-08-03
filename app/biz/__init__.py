# coding=utf-8
import logging
import blinker

_signal = blinker.Namespace()
teko_msg_signal = _signal.signal('teko-msg')  # type: blinker.NamedSignal


def on_teko_msg(arg):
    """
    Decorator apply to teko-biz functions
    :param arg:
    :return:
    """
    if isinstance(arg, (str, bytes)):
        return teko_msg_signal.connect_via(arg)
    return teko_msg_signal.connect(arg)


__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)
