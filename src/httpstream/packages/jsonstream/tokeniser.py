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

""" JSON tokeniser
"""


from string import whitespace
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

from .exceptions import AwaitingData, EndOfStream, UnexpectedCharacter


try:
    from builtins import chr as _chr
except ImportError:
    from __builtin__ import unichr as _chr


class Tokeniser(object):

    ESCAPE_SEQUENCES = {
        '"': u'"',
        '\\': u'\\',
        '/': u'/',
        'b': u'\b',
        'f': u'\f',
        'n': u'\n',
        'r': u'\r',
        't': u'\t',
    }

    def __init__(self):
        self.start()

    def _assert_writable(self):
        if not self._writable:
            raise IOError("Stream is not writable")

    def write(self, data):
        """Write raw JSON data to the decoder stream.
        """
        self._assert_writable()
        read_pos = self.data.tell()
        self.data.seek(self._write_pos)
        self.data.write(data)
        self._write_pos = self.data.tell()
        self.data.seek(read_pos)

    def start(self):
        self.data = StringIO()
        self._write_pos = 0
        self._writable = True

    def end(self):
        self._writable = False

    def _peek(self):
        """Return next available character without
        advancing pointer.
        """
        pos = self.data.tell()
        ch = self.data.read(1)
        self.data.seek(pos)
        if ch:
            return ch
        elif self._writable:
            raise AwaitingData()
        else:
            raise EndOfStream()

    def _read(self):
        """Read the next character.
        """
        ch = self.data.read(1)
        if ch:
            return ch
        elif self._writable:
            raise AwaitingData()
        else:
            raise EndOfStream()

    def _skip_whitespace(self):
        while True:
            pos = self.data.tell()
            ch = self.data.read(1)
            if ch == '':
                break
            if ch not in whitespace:
                self.data.seek(pos)
                break

    def _read_literal(self, literal):
        pos = self.data.tell()
        try:
            for expected in literal:
                actual = self._read()
                if actual != expected:
                    raise UnexpectedCharacter(actual)
        except AwaitingData:
            self.data.seek(pos)
            raise AwaitingData()
        return literal

    def _read_digit(self):
        pos = self.data.tell()
        try:
            digit = self._read()
            if digit not in "0123456789":
                self.data.seek(pos)
                raise UnexpectedCharacter(digit)
        except AwaitingData:
            self.data.seek(pos)
            raise AwaitingData()
        return digit

    def _read_string(self):
        pos = self.data.tell()
        src, value = [self._read_literal('"')], []
        try:
            while True:
                ch = self._read()
                src.append(ch)
                if ch == '\\':
                    ch = self._read()
                    src.append(ch)
                    if ch in self.ESCAPE_SEQUENCES:
                        value.append(self.ESCAPE_SEQUENCES[ch])
                    elif ch == 'u':
                        n = 0
                        for i in range(4):
                            ch = self._read()
                            src.append(ch)
                            n = 16 * n + int(ch, 16)
                        value.append(_chr(n))
                    else:
                        raise UnexpectedCharacter(ch)
                elif ch == '"':
                    break
                else:
                    value.append(ch)
        except AwaitingData:
            self.data.seek(pos)
            raise AwaitingData()
        return "".join(src), u"".join(value)

    def _read_number(self):
        pos = self.data.tell()
        src = []
        has_fractional_part = False
        try:
            # check for sign
            ch = self._peek()
            if ch == '-':
                src.append(self._read())
            # read integer part
            ch = self._read_digit()
            src.append(ch)
            if ch != '0':
                while True:
                    try:
                        src.append(self._read_digit())
                    except (UnexpectedCharacter, EndOfStream):
                        break
            try:
                ch = self._peek()
            except EndOfStream:
                pass
            # read fractional part
            if ch == '.':
                has_fractional_part = True
                src.append(self._read())
                while True:
                    try:
                        src.append(self._read_digit())
                    except (UnexpectedCharacter, EndOfStream):
                        break
        except AwaitingData:
            # number potentially incomplete: need to wait for
            # further data or end of stream
            self.data.seek(pos)
            raise AwaitingData()
        src = "".join(src)
        if has_fractional_part:
            return src, float(src)
        else:
            return src, int(src)

    def read(self):
        self._skip_whitespace()
        ch = self._peek()
        if ch in ',:[]{}':
            return self._read(), None
        elif ch == 'n':
            return self._read_literal('null'), None
        elif ch == 't':
            return self._read_literal('true'), True
        elif ch == 'f':
            return self._read_literal('false'), False
        elif ch == '"':
            return self._read_string()
        elif ch in '-0123456789':
            return self._read_number()
        else:
            raise UnexpectedCharacter(ch)
