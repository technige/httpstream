#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2012-2014 Nigel Small
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

from jsonstream import assembled, grouped

from httpstream import http, Resource, ResourceTemplate, RedirectionError
from httpstream.numbers import *


LOREM_IPSUM = """\
Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu
fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
culpa qui officia deserunt mollit anim id est laborum.
"""

WAR_AND_PEACE = u"""\
Так говорила в июле 1805 года известная Анна Павловна Шерер, фрейлина и
приближенная императрицы Марии Феодоровны, встречая важного и чиновного князя
Василия, первого приехавшего на ее вечер. Анна Павловна кашляла несколько дней,
у нее был грипп, как она говорила (грипп был тогда новое слово, употреблявшееся
только редкими).
"""

GENESIS = u"""\
א  בְּרֵאשִׁית, בָּרָא אֱלֹהִים, אֵת הַשָּׁמַיִם, וְאֵת הָאָרֶץ.
ב  וְהָאָרֶץ, הָיְתָה תֹהוּ וָבֹהוּ, וְחֹשֶׁךְ, עַל-פְּנֵי תְהוֹם; וְרוּחַ אֱלֹהִים, מְרַחֶפֶת עַל-פְּנֵי הַמָּיִם.
ג  וַיֹּאמֶר אֱלֹהִים, יְהִי אוֹר; וַיְהִי-אוֹר.
ד  וַיַּרְא אֱלֹהִים אֶת-הָאוֹר, כִּי-טוֹב; וַיַּבְדֵּל אֱלֹהִים, בֵּין הָאוֹר וּבֵין הַחֹשֶׁךְ.
ה  וַיִּקְרָא אֱלֹהִים לָאוֹר יוֹם, וְלַחֹשֶׁךְ קָרָא לָיְלָה; וַיְהִי-עֶרֶב וַיְהִי-בֹקֶר, יוֹם אֶחָד.  {פ}
ו  וַיֹּאמֶר אֱלֹהִים, יְהִי רָקִיעַ בְּתוֹךְ הַמָּיִם, וִיהִי מַבְדִּיל, בֵּין מַיִם לָמָיִם.
ז  וַיַּעַשׂ אֱלֹהִים, אֶת-הָרָקִיעַ, וַיַּבְדֵּל בֵּין הַמַּיִם אֲשֶׁר מִתַּחַת לָרָקִיעַ, וּבֵין הַמַּיִם אֲשֶׁר מֵעַל לָרָקִיעַ; וַיְהִי-כֵן.
ח  וַיִּקְרָא אֱלֹהִים לָרָקִיעַ, שָׁמָיִם; וַיְהִי-עֶרֶב וַיְהִי-בֹקֶר, יוֹם שֵׁנִי.  {פ}
ט  וַיֹּאמֶר אֱלֹהִים, יִקָּווּ הַמַּיִם מִתַּחַת הַשָּׁמַיִם אֶל-מָקוֹם אֶחָד, וְתֵרָאֶה, הַיַּבָּשָׁה; וַיְהִי-כֵן.
י  וַיִּקְרָא אֱלֹהִים לַיַּבָּשָׁה אֶרֶץ, וּלְמִקְוֵה הַמַּיִם קָרָא יַמִּים; וַיַּרְא אֱלֹהִים, כִּי-טוֹב.
יא  וַיֹּאמֶר אֱלֹהִים, תַּדְשֵׁא הָאָרֶץ דֶּשֶׁא עֵשֶׂב מַזְרִיעַ זֶרַע, עֵץ פְּרִי עֹשֶׂה פְּרִי לְמִינוֹ, אֲשֶׁר זַרְעוֹ-בוֹ עַל-הָאָרֶץ; וַיְהִי-כֵן.
יב  וַתּוֹצֵא הָאָרֶץ דֶּשֶׁא עֵשֶׂב מַזְרִיעַ זֶרַע, לְמִינֵהוּ, וְעֵץ עֹשֶׂה-פְּרִי אֲשֶׁר זַרְעוֹ-בוֹ, לְמִינֵהוּ; וַיַּרְא אֱלֹהִים, כִּי-טוֹב.
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


def test_can_set_default_encoding():
    assert http.default_encoding == "ISO-8859-1"
    http.default_encoding = "UTF-8"
    assert http.default_encoding == "UTF-8"


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
        response.chunk_size = 37
        assert response.is_text
        for line in response:
            assert line == expected_lines.pop(0)


def test_can_get_multi_line_cyrillic_text_resource():
    resource = Resource("http://localhost:8080/war_and_peace")
    expected_lines = WAR_AND_PEACE.splitlines()
    with resource.get() as response:
        response.chunk_size = 37
        assert response.is_text
        for line in response:
            assert line == expected_lines.pop(0)


def test_can_get_multi_line_hebrew_text_resource():
    resource = Resource("http://localhost:8080/genesis")
    expected_lines = GENESIS.splitlines()
    with resource.get() as response:
        response.chunk_size = 37
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


def test_can_get_block_json_resource():
    resource = Resource("http://localhost:8080/object")
    with resource.get() as response:
        assert response.is_json
        assert response.json == OBJECT


def test_can_use_resource_with_template_uri():
    resource_tmpl = ResourceTemplate("http://localhost:8080/person/{name}")
    for name in PEOPLE.keys():
        with resource_tmpl.expand(name=name).get() as response:
            assert response.is_json
            assert assembled(response) == PEOPLE[name]


def test_can_follow_simple_redirect():
    resource = Resource("http://localhost:8080/old")
    with resource.get() as response:
        assert response.status_code == OK
        assert response.uri == "http://localhost:8080/new"


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
        bits = response.read().decode(response.encoding).split()
        received_product = tuple(bits[0].split("/"))
        assert received_product == test_product


def test_cannot_use_unknown_scheme():
    resource = Resource("xxxx://www.example.com/")
    try:
        resource.get()
    except ValueError:
        assert True
    else:
        assert False


def test_can_get_remote_resource():
    try:
        Resource("http://www.timeapi.org/utc/now").get()
    except:
        pass
