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

import json

from httpstream.jsonencoder import JSONEncoder


def test_can_encode_none():
    data = None
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert string == 'null'


def test_can_encode_true():
    data = True
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert string == 'true'


def test_can_encode_false():
    data = False
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert string == 'false'


def test_can_encode_positive_integer():
    data = 42
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert string == '42'


def test_can_encode_negative_integer():
    data = -42
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert string == '-42'


def test_can_encode_positive_float():
    data = 3.1415926
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert float(string) == data


def test_can_encode_negative_float():
    data = -3.1415926
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert float(string) == data


def test_can_encode_complex():
    data = 42 + 3.14j
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    # a bit of a roundabout check but works with python 2.6
    assert string.startswith("[")
    assert string.endswith("]")
    parts = tuple(map(float, string[1:-1].split(",")))
    assert parts[0] == 42.0
    assert parts[1] == 3.14


def test_can_encode_string():
    data = "hello, world"
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert string == '"hello, world"'


def test_can_encode_unicode_string():
    try:
        data = "hellö, wörld"
    except SyntaxError:
        assert True
    else:
        string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
        assert string == '"hell\\u00f6, w\\u00f6rld"'


def test_can_encode_dict():
    data = {"one": 1, "two": 2}
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert string in ('{"one":1,"two":2}', '{"two":2,"one":1}')


def test_can_encode_ordered_dict():
    try:
        from collections import OrderedDict
    except ImportError:
        from .util.ordereddict import OrderedDict
    data = OrderedDict([("one", 1), ("two", 2), ("three", 2), ("four", 2)])
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert string == '{"one":1,"two":2,"three":2,"four":2}'


def test_can_encode_list():
    data = [1, 2, "three"]
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert string == '[1,2,"three"]'


def test_can_encode_tuple():
    data = (1, 2, "three")
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert string == '[1,2,"three"]'


def test_can_encode_set():
    data = set([1, 2])
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert string in ('[1,2]', '[2,1]')


def test_can_encode_frozenset():
    data = frozenset([1, 2])
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert string in ('[1,2]', '[2,1]')


def test_can_encode_decimal():
    from decimal import Decimal
    data = Decimal("3.141592653589")
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert string == '"3.141592653589"'


def test_can_encode_date():
    from datetime import date
    data = date(2000, 3, 25)
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert string == '"2000-03-25"'


def test_can_encode_time():
    from datetime import time
    data = time(13, 9, 55)
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert string == '"13:09:55"'


def test_can_encode_datetime():
    from datetime import datetime
    data = datetime(2000, 3, 25, 13, 9, 55)
    string = json.dumps(data, cls=JSONEncoder, separators=(",", ":"))
    assert string == '"2000-03-25T13:09:55"'
