#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2014, Nigel Small
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

from httpstream import Query


def test_can_parse_none_query():
    query = Query(None)
    assert str(query) == ""
    assert query.string is None
    assert dict(query) == {}
    assert len(query) == 0
    assert not query.__bool__()
    assert not query.__nonzero__()


def test_can_parse_empty_query():
    query = Query("")
    assert str(query) == ""
    assert query.string == ""
    assert dict(query) == {}
    assert len(query) == 0
    assert not query.__bool__()
    assert not query.__nonzero__()


def test_can_parse_key_only_query():
    query = Query("foo")
    assert str(query) == "foo"
    assert query.string == "foo"
    assert dict(query) == {"foo": None}
    assert query.get("foo") is None
    assert len(query) == 1
    assert query.__bool__()
    assert query.__nonzero__()


def test_can_parse_key_value_query():
    query = Query("foo=bar")
    assert str(query) == "foo=bar"
    assert query.string == "foo=bar"
    assert dict(query) == {"foo": "bar"}
    assert query.get("foo") == "bar"
    assert len(query) == 1
    assert query.__bool__()
    assert query.__nonzero__()


def test_can_parse_multi_key_value_query():
    query = Query("foo=bar&spam=eggs")
    assert str(query) == "foo=bar&spam=eggs"
    assert query.string == "foo=bar&spam=eggs"
    assert dict(query) == {"foo": "bar", "spam": "eggs"}
    assert query.get("foo") == "bar"
    assert query.get("spam") == "eggs"


def test_can_parse_mixed_query():
    query = Query("foo&spam=eggs")
    assert str(query) == "foo&spam=eggs"
    assert query.string == "foo&spam=eggs"
    assert dict(query) == {"foo": None, "spam": "eggs"}
    assert query.get("foo") is None
    assert query.get("spam") == "eggs"


def test_query_equality():
    query1 = Query("foo=bar&spam=eggs")
    query2 = Query("foo=bar&spam=eggs")
    assert query1 == query2


def test_query_inequality():
    query1 = Query("foo=bar&spam=eggs")
    query2 = Query("foo=bar&spam=bacon")
    assert query1 != query2


def test_query_equality_when_none():
    query = Query(None)
    none = None
    assert query == none


def test_query_is_hashable():
    query = Query("foo=bar&spam=eggs")
    hashed = hash(query)
    assert hashed


def test_getting_non_existent_query_parameters_causes_key_error():
    query = Query("foo=bar&spam=eggs")
    try:
        query.get("bacon")
    except KeyError:
        assert True
    else:
        assert False


def test_getting_all_non_existent_query_parameters_causes_key_error():
    query = Query("foo=bar&spam=eggs")
    try:
        query.get_all("bacon")
    except KeyError:
        assert True
    else:
        assert False


def test_can_get_nth_parameter():
    query = Query("foo=bar&foo=baz&foo=qux&spam=eggs")
    assert query.get("foo", 0) == "bar"
    assert query.get("foo", 1) == "baz"
    assert query.get("foo", 2) == "qux"
    try:
        query.get("foo", 3)
    except IndexError:
        assert True
    else:
        assert False


def test_can_get_all_parameters_with_name():
    query = Query("foo=bar&foo=baz&foo=qux&spam=eggs")
    values = query.get_all("foo")
    assert values == ["bar", "baz", "qux"]


def test_can_get_query_item():
    query = Query("one=eins&two=zwei&three=drei&four=vier&five=fünf")
    bit = query[2]
    assert bit == ("three", "drei")


def test_can_get_query_slice():
    query = Query("one=eins&two=zwei&three=drei&four=vier&five=fünf")
    bits = query[1:3]
    assert bits.string == "two=zwei&three=drei"


def test_can_check_parameter_exists():
    query = Query("one=eins&two=zwei&three=drei&four=vier&five=fünf")
    assert ("two", "zwei") in query
    assert ("nine", "neun") not in query


def test_old_slicing_method():
    query = Query("one=eins&two=zwei&three=drei&four=vier&five=fünf")
    bits = query.__getslice__(1, 3)
    assert bits.string == "two=zwei&three=drei"


def test_passing_a_slice_through_getitem():
    query = Query("one=eins&two=zwei&three=drei&four=vier&five=fünf")
    bits = query.__getitem__(slice(1, 3))
    assert bits.string == "two=zwei&three=drei"
