#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2012-2015, Nigel Small
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

from httpstream import percent_decode


def test_can_percent_decode_none():
    decoded = percent_decode(None)
    assert decoded is None


def test_can_percent_decode_empty_string():
    decoded = percent_decode("")
    assert decoded == ""


def test_can_percent_decode_number():
    decoded = percent_decode(12)
    assert decoded == "12"


def test_can_percent_decode_string():
    decoded = percent_decode("foo")
    assert decoded == "foo"


def test_can_percent_decode_plus_to_space():
    decoded = percent_decode("one+two%20three+four")
    assert decoded == "one two three four"


def test_can_percent_decode_reserved_chars():
    decoded = percent_decode("20%25%20of%20%24100%20%3D%20%2420")
    assert decoded == "20% of $100 = $20"


def test_can_percent_decode_extended_chars():
    decoded = percent_decode("El%20Ni%C3%B1o")
    assert decoded == "El Niño"


def test_percent_decoding_partial_extended_chars_will_fail():
    try:
        percent_decode("El%20Ni%C3")
    except UnicodeDecodeError:
        assert True
    else:
        assert False
