# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2014 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file LICENSE, which
# you should have received as part of this distribution.
#

#: Noop sentinel value
NOOP = type('NoOp', (object,), {'__slots__': ()})()
_EOS = type('EndOfStream', (object,), {'__slots__': ()})
#: EOS (end of stream) sentinel value. Draft-8 only.
EOS = _EOS()
EOS_A = type('EndOfArrayStream', (_EOS,), {'__slots__': ()})()
EOS_O = type('EndOfObjectStream', (_EOS,), {'__slots__': ()})()
del _EOS

import warnings
from .version import __version__
# from .draft8 import Draft8Decoder, Draft8Encoder
from .draft9 import Draft9Decoder, Draft9Encoder
from .tools import inspect
from .tools.inspect import pprint
from .exceptions import DecodeError, EncodeError

__all__ = ['decode', 'encode', 'pprint', 'NOOP', 'DecodeError', 'EncodeError',
           '__version__']

# _draft8_decoder = Draft8Decoder
# _draft8_encoder = Draft8Encoder

_draft9_decoder = Draft9Decoder
_draft9_encoder = Draft9Encoder

warnings.simplefilter('once')
_DRAFT8_DEPRECATED = ('Draft-8 specification is too old and deprecated.'
                      ' Please upgrade your data to fit Draft-9 spec.')


def set_datatype_format(old_format=True):
    old_format_json = old_format
    inspect.output_old_format = old_format_json

def decode(data, allow_noop=False, spec='draft9'):
    """Decodes input stream of UBJSON data to Python object.

    :param data: `.read([size])`-able object or source string.
    :param allow_noop: Allow to emit :const:`~simpleubjson.NOOP` values for
                       unsized arrays and objects.
    :type allow_noop: bool
    :param spec: UBJSON specification. Supported Draft-8 and Draft-9
                 specifications by ``draft-8`` or ``draft-9`` keys.
    :type spec: str

    :return: Decoded Python object. See mapping table below.
    """

    return _draft9_decoder(data, allow_noop).decode_next()


def encode(data, output=None, default=None, old_format_json=True, spec='draft9'):
    """Encodes Python object to Universal Binary JSON data.

    :param data: Python object.
    :param output: `.write([data])`-able object. If omitted result would be
                   returned instead of written into.
    :param default: Callable object that would be used if there is no handlers
                    matched for Python data type.
                    Takes encodable value as single argument and must return
                    valid UBJSON encodable value.
    :param spec: UBJSON specification. Supported Draft-8 and Draft-9
                 specifications by ``draft-8`` or ``draft-9`` keys.
    :type spec: str

    :return: Encoded Python object. See mapping table below.
             If `output` param is specified, all data would be written into it
             by chunks and None will be returned.
    """
    current_encoder = _draft9_encoder(default)
    current_encoder.old_format_json = old_format_json
    res = current_encoder.encode_next(data)

    if output:
        output.write(res)
    else:
        return res
