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


from httpstream import Resource, RedirectionError
from httpstream.jsonstream import assembled, grouped


LOREM_IPSUM = """\
Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu
fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
culpa qui officia deserunt mollit anim id est laborum.
"""

OBJECT = {"one": 1, "two": 2, "three": 3}

PEOPLE = {
    "alice": {
        "name": "Alice Allison",
        "age": 34,
        "favourite_colours": ["purple", "red"]
    },
    "bob": {
        "name": "Bob Robertson",
        "age": 66,
        "favourite_colours": ["blue", "green"]
    },
    "carol": {
        "name": "Carol Carlsson",
        "age": 50,
        "favourite_colours": []
    }
}


def test_can_get_simple_text_resource():
    resource = Resource("http://localhost:8080/hello")
    response = resource.get()
    assert response.is_text
    content = response.read().decode(response.encoding)
    assert content == "hello, world"


def test_can_put_simple_text_resource():
    resource = Resource("http://localhost:8080/hello")
    response = resource.put("fred")
    assert response.is_text
    content = response.read().decode("utf-8")
    assert content == "hello, fred"


def test_can_post_simple_text_resource():
    resource = Resource("http://localhost:8080/hello")
    response = resource.post("fred")
    assert response.is_text
    content = response.read().decode(response.encoding)
    assert content == "hello, world and fred"


def test_can_delete_simple_text_resource():
    resource = Resource("http://localhost:8080/hello")
    response = resource.delete()
    assert response.is_text
    content = response.read().decode(response.encoding)
    assert content == "goodbye, cruel world"


def test_can_send_header():
    resource = Resource("http://localhost:8080/hello")
    response = resource.put("fred", headers={"X-Upper-Case": True})
    assert response.is_text
    content = response.read().decode(response.encoding)
    assert content == "HELLO, FRED"


def test_can_get_multi_line_text_resource():
    resource = Resource("http://localhost:8080/lorem_ipsum")
    expected_lines = LOREM_IPSUM.splitlines()
    with resource.get() as response:
        assert response.is_text
        for line in response:
            assert line == expected_lines.pop(0)


def test_can_get_big_resource_with_small_chunk_size():
    resource = Resource("http://localhost:8080/lorem_ipsum")
    expected_lines = LOREM_IPSUM.splitlines()
    with resource.get() as response:
        response.chunk_size = 10
        assert response.is_text
        for line in response:
            assert line == expected_lines.pop(0)


def test_can_get_simple_json_resource():
    resource = Resource("http://localhost:8080/object")
    with resource.get() as response:
        assert response.is_json
        assert assembled(response) == OBJECT


def test_can_get_multi_object_json_resource():
    resource = Resource("http://localhost:8080/person/")
    with resource.get() as response:
        assert response.is_json
        for (name,), person in grouped(response):
            assert assembled(person) == PEOPLE[name]


def test_can_use_resource_with_template_uri():
    resource = Resource("http://localhost:8080/person/{name}")
    for name in PEOPLE.keys():
        with resource.get(fields={"name": name}) as response:
            assert response.is_json
            assert assembled(response) == PEOPLE[name]


def test_infinity_is_detected():
    resource = Resource("http://localhost:8080/infinity")
    try:
        resource.get()
    except RedirectionError:
        assert True
    else:
        assert False


def test_can_set_product_in_user_agent():
    test_product = ("FooBar", "1.2.3")
    resource = Resource("http://localhost:8080/user_agent")
    with resource.get(product=test_product) as response:
        assert response.is_text
        bits = response.read().split()
        received_product = tuple(bits[0].split("/"))
        assert received_product == test_product
