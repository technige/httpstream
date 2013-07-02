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


from httpstream import Resource, NetworkAddressError, SocketError


def test_bad_hostname_will_fail():
    resource = Resource("http://localtoast:6789")
    try:
        resource.get()
    except NetworkAddressError as err:
        assert True
        assert err.netloc == "localtoast:6789"
    else:
        assert False


def test_bad_port_will_fail():
    resource = Resource("http://localhost:6789")
    try:
        resource.get()
    except SocketError as err:
        assert True
        assert err.code == 111
        assert err.netloc == "localhost:6789"
    else:
        assert False


def test_can_get_simple_uri():
    ddg = Resource("http://duckduckgo.com")
    rs = ddg.get()
    assert rs.status_code == 200


def test_can_get_substituted_uri():
    ddg = Resource("https://api.duckduckgo.com/?q={q}&format=json")
    rs = ddg.get(q="neo4j")
    for key, value in rs:
        print(key, value)
    assert rs.status_code == 200
