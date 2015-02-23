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

from httpstream import Authority


def test_can_parse_none_authority():
    auth = Authority(None)
    assert str(auth) == ""
    assert auth.string is None
    assert auth.user_info is None
    assert auth.host is None
    assert auth.port is None


def test_can_parse_empty_authority():
    auth = Authority("")
    assert str(auth) == ""
    assert auth.string == ""
    assert auth.user_info is None
    assert auth.host == ""
    assert auth.port is None


def test_can_parse_host_authority():
    auth = Authority("example.com")
    assert str(auth) == "example.com"
    assert auth.string == "example.com"
    assert auth.user_info is None
    assert auth.host == "example.com"
    assert auth.port is None


def test_can_parse_host_port_authority():
    auth = Authority("example.com:6789")
    assert str(auth) == "example.com:6789"
    assert auth.string == "example.com:6789"
    assert auth.user_info is None
    assert auth.host == "example.com"
    assert auth.port == 6789


def test_can_parse_user_host_authority():
    auth = Authority("bob@example.com")
    assert str(auth) == "bob@example.com"
    assert auth.string == "bob@example.com"
    assert auth.user_info == "bob"
    assert auth.host == "example.com"
    assert auth.port is None


def test_can_parse_email_user_host_authority():
    auth = Authority("bob@example.com@example.com")
    assert str(auth) == "bob%40example.com@example.com"
    assert auth.string == "bob%40example.com@example.com"
    assert auth.user_info == "bob@example.com"
    assert auth.host == "example.com"
    assert auth.port is None


def test_can_parse_full_authority():
    auth = Authority("bob@example.com:6789")
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


def test_authority_equality_when_none():
    auth = Authority(None)
    none = None
    assert auth == none


def test_authority_is_hashable():
    auth = Authority("alice@example.com:1234")
    hashed = hash(auth)
    assert hashed
