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

from httpstream import URI, URITemplate


def test_expansion_with_no_variables():
    uri_template = URITemplate("{}")
    uri = uri_template.expand()
    assert uri == URI("")


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


def test_empty_expansion():
    _test_expansions({
        None: None,
        "": "",
    })


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
    uri = template.expand()
    assert uri.string is None


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


def test_uri_template_equality_with_string():
    template = URITemplate("http://example.com/data/{foo}")
    string = "http://example.com/data/{foo}"
    assert template == string


def test_uri_template_equality_when_none():
    template = URITemplate(None)
    none = None
    assert template == none


def test_uri_template_is_hashable():
    template = URITemplate("http://example.com/data/{foo}")
    hashed = hash(template)
    assert hashed
