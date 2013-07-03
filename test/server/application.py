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


@get('/infinity')
def infinity():
    redirect("/infinity")


@get('/user_agent')
def user_agent():
    return request.headers.get("User-Agent")


if __name__ == "__main__":
    run(host='localhost', port=8080)
