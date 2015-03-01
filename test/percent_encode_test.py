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

try:
    from collections import OrderedDict
except ImportError:
    from .util.ordereddict import OrderedDict

from httpstream import percent_encode


def test_can_percent_encode_none():
    encoded = percent_encode(None)
    assert encoded is None


def test_can_percent_encode_empty_string():
    encoded = percent_encode("")
    assert encoded == ""


def test_can_percent_encode_number():
    encoded = percent_encode(12)
    assert encoded == "12"


def test_can_percent_encode_string():
    encoded = percent_encode("foo")
    assert encoded == "foo"


def test_can_percent_encode_list():
    encoded = percent_encode(["knife&fork", "spoon"])
    assert encoded == "knife%26fork&spoon"


def test_can_percent_encode_dictionary():
    encoded = percent_encode(OrderedDict([("one", 1), ("two", 2)]))
    assert encoded == "one=1&two=2"


def test_can_percent_encode_reserved_chars():
    encoded = percent_encode("20% of $100 = $20")
    assert encoded == "20%25%20of%20%24100%20%3D%20%2420"


def test_can_percent_encode_extended_chars():
    encoded = percent_encode("/El Niño/")
    assert encoded == "%2FEl%20Ni%C3%B1o%2F"


def test_can_percent_encode_with_safe_chars():
    encoded = percent_encode("/El Niño/", safe="/|\\")
    assert encoded == "/El%20Ni%C3%B1o/"
