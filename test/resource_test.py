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

from httpstream import Resource, NetworkAddressError, SocketError, ResourceTemplate
from httpstream.packages.urimagic import URI, URITemplate


def test_bad_hostname_will_fail():
    resource = Resource("http://localtoast:6789")
    try:
        resource.get()
    except NetworkAddressError as err:
        assert True
        assert err.host_port == "localtoast:6789"
    else:
        assert False


def test_bad_port_will_fail():
    resource = Resource("http://localhost:6789")
    try:
        resource.get()
    except SocketError as err:
        assert True
        assert err.code == 111
        assert err.host_port == "localhost:6789"
    else:
        assert False


def test_can_get_simple_uri():
    resource = Resource("http://localhost:8080/person/")
    rs = resource.get()
    assert rs.status_code == 200


def test_can_get_substituted_uri():
    resource = ResourceTemplate("http://localhost:8080/person/{name}")
    rs = resource.expand(name="alice").get()
    assert rs.status_code == 200


# RESOURCE CREATION


def test_can_create_none_resource():
    resource = Resource(None)
    assert resource.uri == URI(None)
    assert not bool(resource)
    assert str(resource) == "<>"


def test_can_create_resource_from_string():
    resource = Resource("http://example.com/foo")
    assert resource.uri == URI("http://example.com/foo")
    assert bool(resource)
    assert str(resource) == "<http://example.com/foo>"


def test_can_create_resource_from_uri():
    uri = URI("http://example.com/foo")
    resource = Resource(uri)
    assert resource.uri == uri
    assert bool(resource)
    assert str(resource) == "<http://example.com/foo>"


# RESOURCE TEMPLATE CREATION


def test_can_create_none_resource_template():
    template = ResourceTemplate(None)
    assert template.uri_template == URITemplate(None)
    assert not bool(template)
    assert str(template) == "<>"


def test_can_create_resource_template_from_empty_string():
    template = ResourceTemplate("")
    assert template.uri_template == URITemplate("")
    assert not bool(template)
    assert str(template) == "<>"


def test_can_create_resource_template_from_string():
    template = ResourceTemplate("http://example.com/foo/{bar}")
    assert template.uri_template == URITemplate("http://example.com/foo/{bar}")
    assert bool(template)
    assert str(template) == "<http://example.com/foo/{bar}>"


def test_can_create_resource_template_from_none_uri_template():
    uri_template = URITemplate(None)
    template = ResourceTemplate(uri_template)
    assert template.uri_template == uri_template
    assert not bool(template)
    assert str(template) == "<>"


def test_can_create_resource_template_from_empty_uri_template():
    uri_template = URITemplate("")
    template = ResourceTemplate(uri_template)
    assert template.uri_template == uri_template
    assert not bool(template)
    assert str(template) == "<>"


def test_can_create_resource_template_from_uri_template():
    uri_template = URITemplate("http://example.com/foo/{bar}")
    template = ResourceTemplate(uri_template)
    assert template.uri_template == uri_template
    assert bool(template)
    assert str(template) == "<http://example.com/foo/{bar}>"
