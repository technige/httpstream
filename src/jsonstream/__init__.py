#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2012 Nigel Small
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" Incremental JSON parser.
"""


from .exceptions import AwaitingData, EndOfStream, UnexpectedCharacter
from .tokeniser import Tokeniser
from .util import merged


# Token constants used for expectation management
VALUE           = 0x01
OPENING_BRACKET = 0x02
CLOSING_BRACKET = 0x04
OPENING_BRACE   = 0x08
CLOSING_BRACE   = 0x10
COMMA           = 0x20
COLON           = 0x40


class JSONStream(object):
    """ Streaming JSON decoder.
    """

    def __init__(self, source):
        self.tokeniser = Tokeniser()
        self.source = iter(source)
        self.path = []
        self._expectation = VALUE | OPENING_BRACKET | OPENING_BRACE

    def _assert_expecting(self, token, src):
        if not self._expectation & token:
            raise UnexpectedCharacter(src)

    def _in_array(self):
        return self.path and isinstance(self.path[-1], int)

    def _in_object(self):
        return self.path and not isinstance(self.path[-1], int)

    def _has_key(self):
        if self.path:
            top = self.path[-1]
            if top is None:
                return False
            elif isinstance(self.path[-1], int):
                return None
            else:
                return True
        else:
            return None

    def _next_value(self, src, value):
        self._assert_expecting(VALUE, src)
        if self._in_array():
            # array value
            out = tuple(self.path), value
            self.path[-1] += 1
            self._expectation = COMMA | CLOSING_BRACKET
        elif self._in_object():
            if self._has_key():
                # object value
                out = tuple(self.path), value
                self.path[-1] = None
                self._expectation = COMMA | CLOSING_BRACE
            else:
                # object key
                out = None
                self.path[-1] = value
                self._expectation = COLON
        else:
            # simple value
            out = tuple(self.path), value
        return out

    def _handle_comma(self, src):
        self._assert_expecting(COMMA, src)
        self._expectation = VALUE | OPENING_BRACKET | OPENING_BRACE

    def _handle_colon(self, src):
        self._assert_expecting(COLON, src)
        self._expectation = VALUE | OPENING_BRACKET | OPENING_BRACE

    def _open_array(self, src):
        self._assert_expecting(OPENING_BRACKET, src)
        self.path.append(0)
        self._expectation = (VALUE | OPENING_BRACKET | CLOSING_BRACKET |
                             OPENING_BRACE)

    def _close_array(self, src):
        self._assert_expecting(CLOSING_BRACKET, src)
        self.path.pop()
        if self._in_array():
            self.path[-1] += 1
            self._expectation = COMMA | CLOSING_BRACKET
        elif self._in_object():
            self.path[-1] = None
            self._expectation = COMMA | CLOSING_BRACE
        else:
            self._expectation = VALUE | OPENING_BRACKET | OPENING_BRACE

    def _open_object(self, src):
        self._assert_expecting(OPENING_BRACE, src)
        self.path.append(None)
        self._expectation = VALUE | CLOSING_BRACE

    def _close_object(self, src):
        self._assert_expecting(CLOSING_BRACE, src)
        self.path.pop()
        if self._in_array():
            self.path[-1] += 1
            self._expectation = COMMA | CLOSING_BRACKET
        elif self._in_object():
            self.path[-1] = None
            self._expectation = COMMA | CLOSING_BRACE
        else:
            self._expectation = VALUE | OPENING_BRACKET | OPENING_BRACE

    def __iter__(self):
        while True:
            try:
                try:
                    self.tokeniser.write(next(self.source))
                except StopIteration:
                    self.tokeniser.end()
                while True:
                    try:
                        src, value = self.tokeniser.read()
                        if src == ',':
                            self._handle_comma(src)
                        elif src == ':':
                            self._handle_colon(src)
                        elif src == '[':
                            self._open_array(src)
                        elif src == ']':
                            self._close_array(src)
                        elif src == '{':
                            self._open_object(src)
                        elif src == '}':
                            self._close_object(src)
                        else:
                            out = self._next_value(src, value)
                            if out:
                                yield out
                    except AwaitingData:
                        break
            except EndOfStream:
                break

