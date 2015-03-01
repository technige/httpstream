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

from httpstream import Path, ParameterString, URI


def test_can_parse_none_path():
    path = Path(None)
    assert str(path) == ""
    assert path.string is None


def test_can_parse_empty_path():
    path = Path("")
    assert str(path) == ""
    assert path.string == ""


def test_can_parse_absolute_path():
    path = Path("/foo/bar")
    assert str(path) == "/foo/bar"
    assert path.string == "/foo/bar"


def test_can_parse_relative_path():
    path = Path("foo/bar")
    assert str(path) == "foo/bar"
    assert path.string == "foo/bar"


def test_can_parse_path_with_encoded_slash():
    path = Path("/foo/bar%2Fbaz")
    assert str(path) == "/foo/bar%2Fbaz"
    assert path.string == "/foo/bar%2Fbaz"


def test_path_equality():
    path1 = Path("/foo/bar")
    path2 = Path("/foo/bar")
    assert path1 == path2


def test_path_inequality():
    path1 = Path("/foo/bar")
    path2 = Path("/foo/bar/baz")
    assert path1 != path2


def test_path_equality_with_string_containing_space():
    path = Path("/foo bar")
    string = "/foo bar"
    assert path == string


def test_path_equality_with_string_containing_encoded_space():
    path = Path("/foo bar")
    string = "/foo%20bar"
    assert path == string


def test_path_equality_when_none():
    path = Path(None)
    none = None
    assert path == none


def test_path_is_hashable():
    path = Path("/foo/bar")
    hashed = hash(path)
    assert hashed


def test_path_has_no_segments_when_none():
    path = Path(None)
    segments = list(path.segments)
    assert segments == []


def test_path_is_iterable_as_segments():
    path = Path("/foo/bar")
    segments = list(path)
    assert segments == ["", "foo", "bar"]


def test_can_remove_dot_segments_pattern_1():
    path_in = Path("/a/b/c/./../../g")
    path_out = path_in.remove_dot_segments()
    assert path_out == "/a/g"


def test_can_remove_dot_segments_pattern_2():
    path_in = Path("mid/content=5/../6")
    path_out = path_in.remove_dot_segments()
    assert path_out == "mid/6"


def test_can_remove_dot_segments_when_single_dot():
    path_in = Path(".")
    path_out = path_in.remove_dot_segments()
    assert path_out == ""


def test_can_remove_dot_segments_when_double_dot():
    path_in = Path("..")
    path_out = path_in.remove_dot_segments()
    assert path_out == ""


def test_can_remove_dot_segments_when_starts_with_single_dot():
    path_in = Path("./a")
    path_out = path_in.remove_dot_segments()
    assert path_out == "a"


def test_can_remove_dot_segments_when_starts_with_double_dot():
    path_in = Path("../a")
    path_out = path_in.remove_dot_segments()
    assert path_out == "a"


def test_can_add_trailing_slash_to_path():
    path = Path("/foo/bar")
    path = path.with_trailing_slash()
    assert path.string == "/foo/bar/"


def test_wont_add_trailing_slash_to_path_that_already_has_one():
    path = Path("/foo/bar/")
    path = path.with_trailing_slash()
    assert path.string == "/foo/bar/"


def test_wont_add_trailing_slash_to_root_path():
    path = Path("/")
    path = path.with_trailing_slash()
    assert path.string == "/"


def test_can_add_trailing_slash_to_empty_path():
    path = Path("")
    path = path.with_trailing_slash()
    assert path.string == "/"


def test_cant_add_trailing_slash_to_none_path():
    path = Path(None)
    path = path.with_trailing_slash()
    assert path.string is None


def test_can_remove_trailing_slash_from_path():
    path = Path("/foo/bar/")
    path = path.without_trailing_slash()
    assert path.string == "/foo/bar"


def test_wont_remove_trailing_slash_if_none_exists():
    path = Path("/foo/bar")
    path = path.without_trailing_slash()
    assert path.string == "/foo/bar"


def test_will_remove_root_path_slash():
    path = Path("/")
    path = path.without_trailing_slash()
    assert path.string == ""


def test_cannot_remove_trailing_slash_from_empty_string():
    path = Path("")
    path = path.without_trailing_slash()
    assert path.string == ""


def test_cannot_remove_trailing_slash_from_none_path():
    path = Path(None)
    path = path.without_trailing_slash()
    assert path.string is None


def test_can_parse_none_parameter_string():
    path_segment = ParameterString(None, ";")
    assert str(path_segment) == ""
    assert path_segment.string is None


def test_can_parse_empty_parameter_string():
    path_segment = ParameterString("", ";")
    assert str(path_segment) == ""
    assert path_segment.string == ""


def test_parameter_string_equality():
    path_segment_1 = ParameterString("foo", ";")
    path_segment_2 = ParameterString("foo", ";")
    assert path_segment_1 == path_segment_2


def test_parameter_string_inequality():
    path_segment_1 = ParameterString("foo", ";")
    path_segment_2 = ParameterString("bar", ";")
    assert path_segment_1 != path_segment_2


def test_parameter_string_equality_when_none():
    path_segment = ParameterString(None, ";")
    none = None
    assert path_segment == none


def test_parameter_string_is_hashable():
    path_segment = ParameterString("foo", ";")
    hashed = hash(path_segment)
    assert hashed


def test_can_parse_parameter_string_with_params():
    uri = URI("http://example.com/foo/name;version=1.2/bar")
    path_segment = ParameterString(uri.path.segments[2], ";")
    assert str(path_segment) == "name;version=1.2"
    assert path_segment.string == "name;version=1.2"
    assert list(path_segment) == [("name", None), ("version", "1.2")]
    assert len(path_segment) == 2
    assert path_segment[0] == ("name", None)
    assert path_segment[1] == ("version", "1.2")
    assert path_segment.get("name") is None
    assert path_segment.get("version") == "1.2"
