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


from __future__ import unicode_literals

from httpstream.jsonstream import JSONStream


def _jsonstream(*lines):
    return list(JSONStream(iter(lines)))


def test_single_int_value():
    assert _jsonstream('42') == [
        ((), 42),
    ]


def test_single_float_value():
    assert _jsonstream('3.14') == [
        ((), 3.14),
    ]

def test_exponential_float_values():
    assert _jsonstream('3.14e10') == [
        ((), 3.14e10),
    ]
    assert _jsonstream('-3.14e10') == [
        ((), -3.14e10),
    ]
    assert _jsonstream('-3.14e+10') == [
        ((), -3.14e+10),
    ]
    assert _jsonstream('-3E-10') == [
        ((), -3E-10),
    ]


def test_single_string_value():
    assert _jsonstream('"foo"') == [
        ((), "foo"),
    ]


def test_array():
    assert _jsonstream('["foo", "bar"]') == [
        ((), []),
        ((0,), 'foo'),
        ((1,), 'bar'),
    ]


def test_array_in_two_parts():
    assert _jsonstream('["foo",',
                       ' "bar"]') == [
        ((), []),
        ((0,), 'foo'),
        ((1,), 'bar'),
    ]


def test_multipart_array_with_broken_tokens():
    assert _jsonstream('["foo',
                       '", "',
                       'bar"]') == [
        ((), []),
        ((0,), 'foo'),
        ((1,), 'bar'),
    ]


def test_nested_arrays():
    assert _jsonstream('["foo", ["bar", "baz"], 19]') == [
        ((), []),
        ((0,), 'foo'),
        ((1,), []),
        ((1, 0), 'bar'),
        ((1, 1), 'baz'),
        ((2,), 19),
    ]


def test_deeper_nested_arrays():
    assert _jsonstream('["foo", ["bar", [1, 1, 2, 3, 5, 8],',
                       ' [true, false], "baz"], 19]') == [
        ((), []),
        ((0,), 'foo'),
        ((1,), []),
        ((1, 0), 'bar'),
        ((1, 1), []),
        ((1, 1, 0), 1),
        ((1, 1, 1), 1),
        ((1, 1, 2), 2),
        ((1, 1, 3), 3),
        ((1, 1, 4), 5),
        ((1, 1, 5), 8),
        ((1, 2), []),
        ((1, 2, 0), True),
        ((1, 2, 1), False),
        ((1, 3), 'baz'),
        ((2,), 19),
    ]


def test_object():
    assert _jsonstream('{"foo": "milk", "bar": "juice"}') == [
        ((), {}),
        (('foo',), 'milk'),
        (('bar',), 'juice'),
    ]


def test_empty_array():
    assert _jsonstream('[]') == [
        ((), []),
    ]


def test_nested_empty_arrays():
    assert _jsonstream('[[],[]]') == [
        ((), []),
        ((0,), []),
        ((1,), []),
    ]


def test_empty_arrays_in_an_object():
    assert _jsonstream('{"foo":[],"bar":[]}') == [
        ((), {}),
        (("foo",), []),
        (("bar",), []),
    ]


def test_empty_object():
    assert _jsonstream('{}') == [
        ((), {}),
    ]


def test_nested_empty_objects():
    assert _jsonstream('{"foo":{},"bar":{}}') == [
        ((), {}),
        (("foo",), {}),
        (("bar",), {}),
    ]


def test_empty_objects_in_an_array():
    assert _jsonstream('[{},{}]') == [
        ((), []),
        ((0,), {}),
        ((1,), {}),
    ]
