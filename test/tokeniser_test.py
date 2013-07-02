#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2012-2013 Nigel Small
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


from httpstream.jsonstream import (Tokeniser, AwaitingData, EndOfStream,
                                   UnexpectedCharacter)


def test_null():
    tokeniser = Tokeniser()
    tokeniser.write('null')
    tokeniser.end()
    assert tokeniser.read() == ('null', None)


def test_true():
    tokeniser = Tokeniser()
    tokeniser.write('true')
    tokeniser.end()
    assert tokeniser.read() == ('true', True)


def test_false():
    tokeniser = Tokeniser()
    tokeniser.write('false')
    tokeniser.end()
    assert tokeniser.read() == ('false', False)


def test_two_part_boolean_value():
    tokeniser = Tokeniser()
    tokeniser.write('fal')
    try:
        tokeniser.read()
    except AwaitingData:
        assert True
    else:
        assert False
    tokeniser.write('se')
    tokeniser.end()
    assert tokeniser.read() == ('false', False)


def test_broken_boolean_value():
    tokeniser = Tokeniser()
    tokeniser.write('fal')
    tokeniser.end()
    try:
        tokeniser.read()
    except EndOfStream:
        assert True
    else:
        assert False


def test_unknown_value():
    tokeniser = Tokeniser()
    tokeniser.write('xyz')
    tokeniser.end()
    try:
        tokeniser.read()
    except UnexpectedCharacter:
        assert True
    else:
        assert False


def test_misleading_value():
    tokeniser = Tokeniser()
    tokeniser.write('foo')
    tokeniser.end()
    try:
        tokeniser.read()
    except UnexpectedCharacter:
        assert True
    else:
        assert False


def test_string():
    tokeniser = Tokeniser()
    tokeniser.write('"foo"')
    tokeniser.end()
    assert tokeniser.read() == ('"foo"', u"foo")


def test_two_part_string_value():
    tokeniser = Tokeniser()
    tokeniser.write('"foo')
    try:
        tokeniser.read()
    except AwaitingData:
        assert True
    else:
        assert False
    tokeniser.write('bar"')
    tokeniser.end()
    assert tokeniser.read() == ('"foobar"', u"foobar")


def test_broken_string_value():
    tokeniser = Tokeniser()
    tokeniser.write('"foo')
    tokeniser.end()
    try:
        tokeniser.read()
    except EndOfStream:
        assert True
    else:
        assert False


def test_broken_string_value_with_trailing_escape():
    tokeniser = Tokeniser()
    tokeniser.write('"foo\\')
    tokeniser.end()
    try:
        tokeniser.read()
    except EndOfStream:
        assert True
    else:
        assert False


def test_broken_string_value_with_hanging_escape():
    tokeniser = Tokeniser()
    tokeniser.write('"foo\\')
    try:
        tokeniser.read()
    except AwaitingData:
        assert True
    else:
        assert False
    tokeniser.end()


def test_string_with_tab():
    tokeniser = Tokeniser()
    tokeniser.write('"foo\\tbar"')
    tokeniser.end()
    assert tokeniser.read() == ('"foo\\tbar"', u"foo\tbar")


def test_string_with_newline():
    tokeniser = Tokeniser()
    tokeniser.write('"foo\\nbar"')
    tokeniser.end()
    assert tokeniser.read() == ('"foo\\nbar"', u"foo\nbar")


def test_string_with_illegal_escape():
    tokeniser = Tokeniser()
    tokeniser.write('"foo\\xbar"')
    tokeniser.end()
    try:
        tokeniser.read()
    except UnexpectedCharacter:
        assert True
    else:
        assert False


def test_string_with_unicode_char():
    tokeniser = Tokeniser()
    tokeniser.write('"\\u00a3100"')
    tokeniser.end()
    assert tokeniser.read() == ('"\\u00a3100"', u"\xa3100")


def test_string_array():
    tokeniser = Tokeniser()
    tokeniser.write('["foo", "bar", "baz"]')
    tokeniser.end()
    assert tokeniser.read() == ('[', None)
    assert tokeniser.read() == ('"foo"', u"foo")
    assert tokeniser.read() == (',', None)
    assert tokeniser.read() == ('"bar"', u"bar")
    assert tokeniser.read() == (',', None)
    assert tokeniser.read() == ('"baz"', u"baz")
    assert tokeniser.read() == (']', None)


def test_int():
    tokeniser = Tokeniser()
    tokeniser.write('42')
    tokeniser.end()
    assert tokeniser.read() == ('42', 42)


def test_negative_int():
    tokeniser = Tokeniser()
    tokeniser.write('-42')
    tokeniser.end()
    assert tokeniser.read() == ('-42', -42)

def test_float():
    tokeniser = Tokeniser()
    tokeniser.write('3.14')
    tokeniser.end()
    assert tokeniser.read() == ('3.14', 3.14)


def test_negative_float():
    tokeniser = Tokeniser()
    tokeniser.write('-3.14')
    tokeniser.end()
    assert tokeniser.read() == ('-3.14', -3.14)


def test_int_comma_int():
    tokeniser = Tokeniser()
    tokeniser.write('42, 76')
    tokeniser.end()
    assert tokeniser.read() == ('42', 42)
    assert tokeniser.read() == (',', None)
    assert tokeniser.read() == ('76', 76)


def test_int_comma_string():
    tokeniser = Tokeniser()
    tokeniser.write('42, "meaning of life"')
    tokeniser.end()
    assert tokeniser.read() == ('42', 42)
    assert tokeniser.read() == (',', None)
    assert tokeniser.read() == ('"meaning of life"', "meaning of life")