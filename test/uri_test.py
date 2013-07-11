#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013, Nigel Small
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


from __future__ import print_function

from httpstream.uri import (percent_encode, percent_decode, Authority, Path,
                            Query, URI, URITemplate)
from collections import OrderedDict


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


def test_can_percent_encode_reserved_chars():
    encoded = percent_encode("20% of $100 = $20")
    assert encoded == "20%25%20of%20%24100%20%3D%20%2420"


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


def test_can_percent_decode_reserved_chars():
    decoded = percent_decode("20%25%20of%20%24100%20%3D%20%2420")
    assert decoded == "20% of $100 = $20"


# AUTHORITY


def test_can_parse_none_authority():
    auth = Authority(None)
    assert repr(auth) == "Authority(None)"
    assert str(auth) == ""
    assert auth.string is None
    assert auth.user_info is None
    assert auth.host is None
    assert auth.port is None


def test_can_parse_empty_authority():
    auth = Authority("")
    assert repr(auth) == "Authority('')"
    assert str(auth) == ""
    assert auth.string == ""
    assert auth.user_info is None
    assert auth.host == ""
    assert auth.port is None


def test_can_parse_host_authority():
    auth = Authority("example.com")
    assert repr(auth) == "Authority('example.com')"
    assert str(auth) == "example.com"
    assert auth.string == "example.com"
    assert auth.user_info is None
    assert auth.host == "example.com"
    assert auth.port is None


def test_can_parse_host_port_authority():
    auth = Authority("example.com:6789")
    assert repr(auth) == "Authority('example.com:6789')"
    assert str(auth) == "example.com:6789"
    assert auth.string == "example.com:6789"
    assert auth.user_info is None
    assert auth.host == "example.com"
    assert auth.port == 6789


def test_can_parse_user_host_authority():
    auth = Authority("bob@example.com")
    assert repr(auth) == "Authority('bob@example.com')"
    assert str(auth) == "bob@example.com"
    assert auth.string == "bob@example.com"
    assert auth.user_info == "bob"
    assert auth.host == "example.com"
    assert auth.port is None


def test_can_parse_email_user_host_authority():
    auth = Authority("bob@example.com@example.com")
    assert repr(auth) == "Authority('bob%40example.com@example.com')"
    assert str(auth) == "bob%40example.com@example.com"
    assert auth.string == "bob%40example.com@example.com"
    assert auth.user_info == "bob@example.com"
    assert auth.host == "example.com"
    assert auth.port is None


def test_can_parse_full_authority():
    auth = Authority("bob@example.com:6789")
    assert repr(auth) == "Authority('bob@example.com:6789')"
    assert str(auth) == "bob@example.com:6789"
    assert auth.string == "bob@example.com:6789"
    assert auth.user_info == "bob"
    assert auth.host == "example.com"
    assert auth.port == 6789


def test_authority_equality():
    auth1 = Authority("alice@example.com:1234")
    auth2 = Authority("alice@example.com:1234")
    assert auth1 == auth2


def test_authority_inequality():
    auth1 = Authority("alice@example.com:1234")
    auth2 = Authority("bob@example.org:5678")
    assert auth1 != auth2


# PATH


def test_can_parse_none_path():
    path = Path(None)
    assert repr(path) == "Path(None)"
    assert str(path) == ""
    assert path.string is None


def test_can_parse_empty_path():
    path = Path("")
    assert repr(path) == "Path('')"
    assert str(path) == ""
    assert path.string == ""


def test_can_parse_absolute_path():
    path = Path("/foo/bar")
    assert repr(path) == "Path('/foo/bar')"
    assert str(path) == "/foo/bar"
    assert path.string == "/foo/bar"


def test_can_parse_relative_path():
    path = Path("foo/bar")
    assert repr(path) == "Path('foo/bar')"
    assert str(path) == "foo/bar"
    assert path.string == "foo/bar"


def test_path_equality():
    path1 = Path("/foo/bar")
    path2 = Path("/foo/bar")
    assert path1 == path2


def test_path_equality():
    path1 = Path("/foo/bar")
    path2 = Path("/foo/bar/baz")
    assert path1 != path2


def test_can_remove_dot_segments_1():
    path_in = Path("/a/b/c/./../../g")
    path_out = path_in.remove_dot_segments()
    assert path_out == "/a/g"


def test_can_remove_dot_segments_2():
    path_in = Path("mid/content=5/../6")
    path_out = path_in.remove_dot_segments()
    assert path_out == "mid/6"


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


def test_cant_remove_trailing_slash_from_none_path():
    path = Path(None)
    path = path.without_trailing_slash()
    assert path.string is None


# QUERY


def test_can_parse_none_query():
    query = Query(None)
    assert repr(query) == "Query(None)"
    assert str(query) == ""
    assert query.string is None
    assert dict(query) == {}
    try:
        assert query["bacon"] == "yummy"
    except KeyError:
        assert True
    else:
        assert False


def test_can_parse_empty_query():
    query = Query("")
    assert repr(query) == "Query('')"
    assert str(query) == ""
    assert query.string == ""
    assert dict(query) == {}
    try:
        assert query["bacon"] == "yummy"
    except KeyError:
        assert True
    else:
        assert False


def test_can_parse_key_only_query():
    query = Query("foo")
    assert repr(query) == "Query('foo')"
    assert str(query) == "foo"
    assert query.string == "foo"
    assert dict(query) == {"foo": None}
    assert query["foo"] is None


def test_can_parse_key_value_query():
    query = Query("foo=bar")
    assert repr(query) == "Query('foo=bar')"
    assert str(query) == "foo=bar"
    assert query.string == "foo=bar"
    assert dict(query) == {"foo": "bar"}
    assert query["foo"] == "bar"


def test_can_parse_multi_key_value_query():
    query = Query("foo=bar&spam=eggs")
    assert repr(query) == "Query('foo=bar&spam=eggs')"
    assert str(query) == "foo=bar&spam=eggs"
    assert query.string == "foo=bar&spam=eggs"
    assert dict(query) == {"foo": "bar", "spam": "eggs"}
    assert query["foo"] == "bar"
    assert query["spam"] == "eggs"


def test_can_parse_mixed_query():
    query = Query("foo&spam=eggs")
    assert repr(query) == "Query('foo&spam=eggs')"
    assert str(query) == "foo&spam=eggs"
    assert query.string == "foo&spam=eggs"
    assert dict(query) == {"foo": None, "spam": "eggs"}
    assert query["foo"] is None
    assert query["spam"] == "eggs"
    try:
        assert query["bacon"] == "yummy"
    except KeyError:
        assert True
    else:
        assert False


def test_can_query_encode_dict():
    data = OrderedDict([("foo", "bar"), ("baz", None), ("big number", 712)])
    encoded = Query.encode(data)
    assert encoded == "foo=bar&baz&big%20number=712"


def test_can_query_encode_list():
    data = ["red", "orange", "yellow", "green", 97, False]
    encoded = Query.encode(data)
    assert encoded == "red&orange&yellow&green&97&False"


def test_query_equality():
    query1 = Query("foo=bar&spam=eggs")
    query2 = Query("foo=bar&spam=eggs")
    assert query1 == query2


def test_query_inequality():
    query1 = Query("foo=bar&spam=eggs")
    query2 = Query("foo=bar&spam=bacon")
    assert query1 != query2


# URI


def test_can_parse_none_uri():
    uri = URI(None)
    assert repr(uri) == "URI(None)"
    assert str(uri) == ""
    assert uri.string is None
    assert uri.scheme is None
    assert uri.hierarchical_part is None
    assert uri.query is None
    assert uri.fragment is None
    assert uri.authority is None
    assert uri.path is None
    assert uri.user_info is None
    assert uri.host is None
    assert uri.port is None
    

def test_can_parse_empty_string():
    uri = URI("")
    assert repr(uri) == "URI('')"
    assert str(uri) == ""
    assert uri.string == ""
    assert uri.scheme is None
    assert uri.hierarchical_part == ""
    assert uri.query is None
    assert uri.fragment is None
    assert uri.authority is None
    assert uri.path == ""
    assert uri.user_info is None
    assert uri.host is None
    assert uri.port is None


def test_can_parse_absolute_path():
    uri = URI("/foo/bar")
    assert repr(uri) == "URI('/foo/bar')"
    assert str(uri) == "/foo/bar"
    assert uri.string == "/foo/bar"
    assert uri.scheme is None
    assert uri.hierarchical_part == "/foo/bar"
    assert uri.query is None
    assert uri.fragment is None
    assert uri.authority is None
    assert uri.path == "/foo/bar"
    assert uri.user_info is None
    assert uri.host is None
    assert uri.port is None


def test_can_parse_relative_path():
    uri = URI("foo/bar")
    assert repr(uri) == "URI('foo/bar')"
    assert str(uri) == "foo/bar"
    assert uri.string == "foo/bar"
    assert uri.scheme is None
    assert uri.hierarchical_part == "foo/bar"
    assert uri.query is None
    assert uri.fragment is None
    assert uri.authority is None
    assert uri.path == "foo/bar"
    assert uri.user_info is None
    assert uri.host is None
    assert uri.port is None


def test_can_parse_only_query():
    uri = URI("?foo=bar")
    assert repr(uri) == "URI('?foo=bar')"
    assert str(uri) == "?foo=bar"
    assert uri.string == "?foo=bar"
    assert uri.scheme is None
    assert uri.hierarchical_part == ""
    assert uri.query == "foo=bar"
    assert dict(uri.query) == {"foo": "bar"}
    assert uri.fragment is None
    assert uri.authority is None
    assert uri.path == ""
    assert uri.user_info is None
    assert uri.host is None
    assert uri.port is None


def test_can_parse_only_fragment():
    uri = URI("#foo")
    assert repr(uri) == "URI('#foo')"
    assert str(uri) == "#foo"
    assert uri.string == "#foo"
    assert uri.scheme is None
    assert uri.hierarchical_part == ""
    assert uri.query is None
    assert uri.fragment == "foo"
    assert uri.authority is None
    assert uri.path == ""
    assert uri.user_info is None
    assert uri.host is None
    assert uri.port is None


def test_can_parse_uri_without_scheme():
    uri = URI("//example.com")
    assert repr(uri) == "URI('//example.com')"
    assert str(uri) == "//example.com"
    assert uri.string == "//example.com"
    assert uri.scheme is None
    assert uri.hierarchical_part == "//example.com"
    assert uri.query is None
    assert uri.fragment is None
    assert uri.authority == "example.com"
    assert uri.path == ""
    assert uri.user_info is None
    assert uri.host == "example.com"
    assert uri.port is None


def test_can_parse_simple_uri():
    uri = URI("foo://example.com")
    assert repr(uri) == "URI('foo://example.com')"
    assert str(uri) == "foo://example.com"
    assert uri.string == "foo://example.com"
    assert uri.scheme == "foo"
    assert uri.hierarchical_part == "//example.com"
    assert uri.query is None
    assert uri.fragment is None
    assert uri.authority == "example.com"
    assert uri.path == ""
    assert uri.user_info is None
    assert uri.host == "example.com"
    assert uri.port is None


def test_can_parse_uri_with_root_path():
    uri = URI("foo://example.com/")
    assert repr(uri) == "URI('foo://example.com/')"
    assert str(uri) == "foo://example.com/"
    assert uri.string == "foo://example.com/"
    assert uri.scheme == "foo"
    assert uri.hierarchical_part == "//example.com/"
    assert uri.query is None
    assert uri.fragment is None
    assert uri.authority == "example.com"
    assert uri.path == "/"
    assert uri.user_info is None
    assert uri.host == "example.com"
    assert uri.port is None


def test_can_parse_full_uri():
    uri = URI("foo://bob@somewhere@example.com:8042"
              "/over/there?name=ferret#nose")
    assert repr(uri) == ("URI('foo://bob%40somewhere@example.com:8042"
                         "/over/there?name=ferret#nose')")
    assert str(uri) ==\
        "foo://bob%40somewhere@example.com:8042/over/there?name=ferret#nose"
    assert len(uri) == (len("foo://bob%40somewhere@example.com:8042"
                            "/over/there?name=ferret#nose"))
    assert bool(uri) == True
    assert URI(uri) == \
        "foo://bob%40somewhere@example.com:8042/over/there?name=ferret#nose"
    assert uri.string == \
        "foo://bob%40somewhere@example.com:8042/over/there?name=ferret#nose"
    assert uri.scheme == "foo"
    assert uri.hierarchical_part == \
        "//bob%40somewhere@example.com:8042/over/there"
    assert uri.query == "name=ferret"
    assert dict(uri.query) == {"name": "ferret"}
    assert uri.query["name"] == "ferret"
    assert uri.fragment == "nose"
    assert uri.authority == "bob%40somewhere@example.com:8042"
    assert uri.path == "/over/there"
    assert uri.user_info == "bob@somewhere"
    assert uri.host == "example.com"
    assert uri.port == 8042
    assert uri.absolute_path_reference == "/over/there?name=ferret#nose"


def test_uri_equality():
    uri1 = URI("http://example.com/")
    uri2 = URI("http://example.com/")
    assert uri1 == uri2


def test_uri_inequality():
    uri1 = URI("http://example.com/")
    uri2 = URI("http://example.org/")
    assert uri1 != uri2


def _test_references(references):
    base = URI("http://a/b/c/d;p?q")
    for reference, target in references.items():
        print(reference, "->", target)
        uri = base.resolve(reference)
        assert uri == target


def test_can_resolve_normal_uri_references():
    _test_references({
        "g:h"    : "g:h",
        "g"      : "http://a/b/c/g",
        "./g"    : "http://a/b/c/g",
        "g/"     : "http://a/b/c/g/",
        "/g"     : "http://a/g",
        "//g"    : "http://g",
        "?y"     : "http://a/b/c/d;p?y",
        "g?y"    : "http://a/b/c/g?y",
        "#s"     : "http://a/b/c/d;p?q#s",
        "g#s"    : "http://a/b/c/g#s",
        "g?y#s"  : "http://a/b/c/g?y#s",
        ";x"     : "http://a/b/c/;x",
        "g;x"    : "http://a/b/c/g;x",
        "g;x?y#s": "http://a/b/c/g;x?y#s",
        ""       : "http://a/b/c/d;p?q",
        "."      : "http://a/b/c/",
        "./"     : "http://a/b/c/",
        ".."     : "http://a/b/",
        "../"    : "http://a/b/",
        "../g"   : "http://a/b/g",
        "../.."  : "http://a/",
        "../../" : "http://a/",
        "../../g": "http://a/g",
    })


def test_can_resolve_abnormal_uri_references():
    _test_references({
        "../../../g"    :  "http://a/g",
        "../../../../g" :  "http://a/g",
    })


def test_can_resolve_and_remove_dot_segments_correctly():
    _test_references({
        "/./g"          :  "http://a/g",
        "/../g"         :  "http://a/g",
        "g."            :  "http://a/b/c/g.",
        ".g"            :  "http://a/b/c/.g",
        "g.."           :  "http://a/b/c/g..",
        "..g"           :  "http://a/b/c/..g",
    })


def test_can_resolve_nonsensical_dot_segments_correctly():
    _test_references({
        "./../g"        :  "http://a/b/g",
        "./g/."         :  "http://a/b/c/g/",
        "g/./h"         :  "http://a/b/c/g/h",
        "g/../h"        :  "http://a/b/c/h",
        "g;x=1/./y"     :  "http://a/b/c/g;x=1/y",
        "g;x=1/../y"    :  "http://a/b/c/y",
    })


def test_can_resolve_and_handle_queries_and_fragments_correctly():
    _test_references({
        "g?y/./x"       :  "http://a/b/c/g?y/./x",
        "g?y/../x"      :  "http://a/b/c/g?y/../x",
        "g#s/./x"       :  "http://a/b/c/g#s/./x",
        "g#s/../x"      :  "http://a/b/c/g#s/../x",
    })


def test_can_resolve_with_strict_mode():
    base = URI("http://a/b/c/d;p?q")
    uri = base.resolve("http:g", strict=True)
    assert uri == "http:g"


def test_can_resolve_without_strict_mode():
    base = URI("http://a/b/c/d;p?q")
    uri = base.resolve("http:g", strict=False)
    assert uri == "http://a/b/c/g"


# URI TEMPLATE


def _test_expansions(expansions):
    variables = {
        "count": ("one", "two", "three"),
        "dom": ("example", "com"),
        "dub": "me/too",
        "hello": "Hello World!",
        "half": "50%",
        "var": "value",
        "who": "fred",
        "base": "http://example.com/home/",
        "path": "/foo/bar",
        "list": ("red", "green", "blue"),
        "keys": OrderedDict([("semi", ";"), ("dot", "."), ("comma", ",")]),
        "v": "6",
        "x": "1024",
        "y": "768",
        "empty": "",
        "empty_keys": dict([]),
        "undef": None,
    }
    for template, expansion in expansions.items():
        print(template, "->", expansion)
        uri_template = URITemplate(template)
        uri = uri_template.expand(**variables)
        assert uri == expansion


def test_can_expand_simple_strings():
    _test_expansions({
        "{var}": "value",
        "{hello}": "Hello%20World%21",
        "{half}": "50%25",
        "O{empty}X": "OX",
        "O{undef}X": "OX",
        "{x,y}": "1024,768",
        "{x,hello,y}": "1024,Hello%20World%21,768",
        "?{x,empty}": "?1024,",
        "?{x,undef}": "?1024",
        "?{undef,y}": "?768",
        "{var:3}": "val",
        "{var:30}": "value",
        "{list}": "red,green,blue",
        "{list*}": "red,green,blue",
        "{keys}": "semi,%3B,dot,.,comma,%2C",
        "{keys*}": "semi=%3B,dot=.,comma=%2C",
    })


def test_can_expand_reserved_strings():
    _test_expansions({
        "{+var}": "value",
        "{+hello}": "Hello%20World!",
        "{+half}": "50%25",
        "{base}index": "http%3A%2F%2Fexample.com%2Fhome%2Findex",
        "{+base}index": "http://example.com/home/index",
        "O{+empty}X": "OX",
        "O{+undef}X": "OX",
        "{+path}/here": "/foo/bar/here",
        "here?ref={+path}": "here?ref=/foo/bar",
        "up{+path}{var}/here": "up/foo/barvalue/here",
        "{+x,hello,y}": "1024,Hello%20World!,768",
        "{+path,x}/here": "/foo/bar,1024/here",
        "{+path:6}/here": "/foo/b/here",
        "{+list}": "red,green,blue",
        "{+list*}": "red,green,blue",
        "{+keys}": "semi,;,dot,.,comma,,",
        "{+keys*}": "semi=;,dot=.,comma=,",
    })


def test_can_expand_fragments():
    _test_expansions({
        "{#var}": "#value",
        "{#hello}": "#Hello%20World!",
        "{#half}": "#50%25",
        "foo{#empty}": "foo#",
        "foo{#undef}": "foo",
        "{#x,hello,y}": "#1024,Hello%20World!,768",
        "{#path,x}/here": "#/foo/bar,1024/here",
        "{#path:6}/here": "#/foo/b/here",
        "{#list}": "#red,green,blue",
        "{#list*}": "#red,green,blue",
        "{#keys}": "#semi,;,dot,.,comma,,",
        "{#keys*}": "#semi=;,dot=.,comma=,",
    })


def test_can_expand_labels():
    _test_expansions({
        "{.who}": ".fred",
        "{.who,who}": ".fred.fred",
        "{.half,who}": ".50%25.fred",
        "www{.dom*}": "www.example.com",
        "X{.var}": "X.value",
        "X{.empty}": "X.",
        "X{.undef}": "X",
        "X{.var:3}": "X.val",
        "X{.list}": "X.red,green,blue",
        "X{.list*}": "X.red.green.blue",
        "X{.keys}": "X.semi,%3B,dot,.,comma,%2C",
        "X{.keys*}": "X.semi=%3B.dot=..comma=%2C",
        "X{.empty_keys}": "X",
        "X{.empty_keys*}": "X",
    })


def test_can_expand_path_segments():
    _test_expansions({
        "{/who}": "/fred",
        "{/who,who}": "/fred/fred",
        "{/half,who}": "/50%25/fred",
        "{/who,dub}": "/fred/me%2Ftoo",
        "{/var}": "/value",
        "{/var,empty}": "/value/",
        "{/var,undef}": "/value",
        "{/var,x}/here": "/value/1024/here",
        "{/var:1,var}": "/v/value",
        "{/list}": "/red,green,blue",
        "{/list*}": "/red/green/blue",
        "{/list*,path:4}": "/red/green/blue/%2Ffoo",
        "{/keys}": "/semi,%3B,dot,.,comma,%2C",
        "{/keys*}": "/semi=%3B/dot=./comma=%2C",
    })


def test_can_expand_path_parameters():
    _test_expansions({
        "{;who}": ";who=fred",
        "{;half}": ";half=50%25",
        "{;empty}": ";empty",
        "{;v,empty,who}": ";v=6;empty;who=fred",
        "{;v,bar,who}": ";v=6;who=fred",
        "{;x,y}": ";x=1024;y=768",
        "{;x,y,empty}": ";x=1024;y=768;empty",
        "{;x,y,undef}": ";x=1024;y=768",
        "{;hello:5}": ";hello=Hello",
        "{;list}": ";list=red,green,blue",
        "{;list*}": ";list=red;list=green;list=blue",
        "{;keys}": ";keys=semi,%3B,dot,.,comma,%2C",
        "{;keys*}": ";semi=%3B;dot=.;comma=%2C",
    })


def test_can_expand_form_queries():
    _test_expansions({
        "{?who}": "?who=fred",
        "{?half}": "?half=50%25",
        "{?x,y}": "?x=1024&y=768",
        "{?x,y,empty}": "?x=1024&y=768&empty=",
        "{?x,y,undef}": "?x=1024&y=768",
        "{?var:3}": "?var=val",
        "{?list}": "?list=red,green,blue",
        "{?list*}": "?list=red&list=green&list=blue",
        "{?keys}": "?keys=semi,%3B,dot,.,comma,%2C",
        "{?keys*}": "?semi=%3B&dot=.&comma=%2C",
    })


def test_can_expand_form_query_continuations():
    _test_expansions({
        "{&who}": "&who=fred",
        "{&half}": "&half=50%25",
        "?fixed=yes{&x}": "?fixed=yes&x=1024",
        "{&x,y,empty}": "&x=1024&y=768&empty=",
        "{&x,y,undef}": "&x=1024&y=768",
        "{&var:3}": "&var=val",
        "{&list}": "&list=red,green,blue",
        "{&list*}": "&list=red&list=green&list=blue",
        "{&keys}": "&keys=semi,%3B,dot,.,comma,%2C",
        "{&keys*}": "&semi=%3B&dot=.&comma=%2C",
    })


def test_can_parse_none_uri_template():
    template = URITemplate(None)
    assert template.string is None


def test_can_parse_uri_template():
    template = URITemplate("http://example.com/data/{foo}")
    assert template.string == "http://example.com/data/{foo}"


def test_uri_template_equality():
    template1 = URITemplate("http://example.com/data/{foo}")
    template2 = URITemplate("http://example.com/data/{foo}")
    assert template1 == template2


def test_uri_template_inequality():
    template1 = URITemplate("http://example.com/data/{foo}")
    template2 = URITemplate("http://example.com/data/{foo}/{bar}")
    assert template1 != template2
