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


import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from bottle import get, put, post, delete, request, run, redirect, abort


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


@get('/hello')
def get_hello():
    return "hello, world"


@put('/hello')
def put_hello():
    name = request.body.read().decode("utf-8")
    message = "hello, " + name
    if request.headers.get("X-Upper-Case"):
        return message.upper()
    else:
        return message


@post('/hello')
def post_hello():
    name = request.body.read().decode("utf-8")
    return "hello, world and " + name


@delete('/hello')
def delete_hello():
    return "goodbye, cruel world"


@get('/lorem_ipsum')
def lorem_ipsum():
    return LOREM_IPSUM


@get('/war_and_peace')
def war_and_peace():
    return WAR_AND_PEACE


@get('/genesis')
def genesis():
    return GENESIS


@get('/object')
def object_():
    return OBJECT


@get('/person/')
@get('/person/<name>')
def person(name=None):
    if name:
        try:
            return PEOPLE[name]
        except KeyError:
            abort(404)
    else:
        return PEOPLE


@get('/old')
def old():
    redirect("/new")


@get('/new')
def new():
    return "You arrived!"


@get('/infinity')
def infinity():
    redirect("/infinity")


@get('/user_agent')
def user_agent():
    return request.headers.get("User-Agent")


if __name__ == "__main__":
    run(host='localhost', port=8080)
