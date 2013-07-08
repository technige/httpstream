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


from collections import OrderedDict
import re


__all__ = ["percent_encode", "percent_decode", "Authority", "Path", "Query",
           "URI", "URITemplate"]

general_delimiters = frozenset(":/?#[]@")
subcomponent_delimiters = frozenset("!$&'()*+,;=")

reserved = general_delimiters | subcomponent_delimiters
unreserved = frozenset("-.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz~")


def percent_encode(data, safe=None):
    """ Percent encode data
    """
    if data is None:
        return None
    if safe:
        safe = unreserved | frozenset(safe)
    else:
        safe = unreserved
    chars = list(str(data))
    for i, char in enumerate(chars):
        if char == "%" or char not in safe:
            chars[i] = "%" + hex(ord(char))[2:].upper().zfill(2)
    return "".join(chars)


def percent_decode(data):
    """ Percent decode data
    """
    if data is None:
        return None
    bits = re.split("(%[0-9A-Fa-f]{2})", str(data))
    for i, bit in enumerate(bits):
        if bit.startswith("%"):
            bits[i] = chr(int(bit[1:], 16))
    return "".join(bits)


class _Part(object):

    def __init__(self):
        pass

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, repr(self.string))

    def __str__(self):
        return self.string or ""

    def __bool__(self):
        return bool(self.string)

    def __nonzero__(self):
        return bool(self.string)

    def __len__(self):
        return len(str(self))

    def __iter__(self):
        return iter(self.string)

    @property
    def string(self):
        raise NotImplementedError()


class Authority(_Part):
    """ A host name plus optional port and user information detail.

    authority := [ user_info "@" ] host [ ":" port ]
    """

    @classmethod
    def _cast(cls, obj):
        if obj is None:
            return None
        elif isinstance(obj, cls):
            return obj
        else:
            return cls(str(obj))

    def __init__(self, string):
        super(Authority, self).__init__()
        if string is None:
            self._user_info = None
            self._host = None
            self._port = None
        else:
            if ":" in string:
                string, self._port = string.rpartition(":")[0::2]
                self._port = int(self._port)
            else:
                self._port = None
            if "@" in string:
                self._user_info, self._host = map(percent_decode,
                                                  string.rpartition("@")[0::2])
            else:
                self._user_info, self._host = None, percent_decode(string)

    def __eq__(self, other):
        other = self._cast(other)
        return (self._user_info == other._user_info and
                self._host == other._host and
                self._port == other._port)

    def __ne__(self, other):
        other = self._cast(other)
        return (self._user_info != other._user_info or
                self._host != other._host or
                self._port != other._port)

    def __hash__(self):
        return hash(self.string)

    @property
    def string(self):
        if self._host is None:
            return None
        u = []
        if self._user_info is not None:
            u += [percent_encode(self._user_info), "@"]
        u += [self._host]
        if self._port is not None:
            u += [":", str(self._port)]
        return "".join(u)
        
    @property
    def user_info(self):
        return self._user_info
        
    @property
    def host(self):
        return self._host
        
    @property
    def port(self):
        return self._port

    @property
    def host_port(self):
        u = [self._host]
        if self._port is not None:
            u += [":", str(self._port)]
        return "".join(u)


class Path(_Part):

    @classmethod
    def _cast(cls, obj):
        if obj is None:
            return None
        elif isinstance(obj, cls):
            return obj
        else:
            return cls(str(obj))

    def __init__(self, string):
        super(Path, self).__init__()
        if string is None:
            self._path = None
        else:
            self._path = percent_decode(string)

    def __eq__(self, other):
        other = self._cast(other)
        return self._path == other._path

    def __ne__(self, other):
        other = self._cast(other)
        return self._path != other._path

    def __hash__(self):
        return hash(self.string)

    @property
    def string(self):
        if self._path is None:
            return None
        return percent_encode(self._path, "/")

    @property
    def segments(self):
        if self._path is None:
            return []
        else:
            return self._path.split("/")

    def __iter__(self):
        return iter(self.segments)

    def remove_dot_segments(self):
        """ Implementation of RFC3986, section 5.2.4
        """
        inp = self.string
        out = ""
        while inp:
            if inp.startswith("../"):
                inp = inp[3:]
            elif inp.startswith("./"):
                inp = inp[2:]
            elif inp.startswith("/./"):
                inp = inp[2:]
            elif inp == "/.":
                inp = "/"
            elif inp.startswith("/../"):
                inp = inp[3:]
                out = out.rpartition("/")[0]
            elif inp == "/..":
                inp = "/"
                out = out.rpartition("/")[0]
            elif inp in (".", ".."):
                inp = ""
            else:
                if inp.startswith("/"):
                    inp = inp[1:]
                    out += "/"
                seg, slash, inp = inp.partition("/")
                out += seg
                inp = slash + inp
        return Path(out)


class Query(_Part):

    @classmethod
    def _cast(cls, obj):
        if obj is None:
            return None
        elif isinstance(obj, cls):
            return obj
        else:
            return cls(str(obj))

    @classmethod
    def encode(cls, iterable):
        if iterable is None:
            return None
        bits = []
        if isinstance(iterable, dict):
            for key, value in iterable.items():
                if value is None:
                    bits.append(percent_encode(key))
                else:
                    bits.append(percent_encode(key) + "=" + percent_encode(value))
        else:
            for item in iterable:
                bits.append(percent_encode(item))
        return "&".join(bits)

    @classmethod
    def decode(cls, string):
        if string is None:
            return None
        data = OrderedDict()
        if string:
            bits = string.split("&")
            for bit in bits:
                if "=" in bit:
                    key, value = map(percent_decode, bit.partition("=")[0::2])
                else:
                    key, value = percent_decode(bit), None
                data[key] = value
        return data

    def __init__(self, string):
        super(Query, self).__init__()
        self._query = Query.decode(string)

    def __eq__(self, other):
        other = self._cast(other)
        return self._query == other._query

    def __ne__(self, other):
        other = self._cast(other)
        return self._query != other._query

    def __hash__(self):
        return hash(self.string)

    @property
    def string(self):
        return Query.encode(self._query)

    def __iter__(self):
        if self._query is None:
            return iter(())
        else:
            return iter(self._query.items())

    def __getitem__(self, key):
        if self._query is None:
            raise KeyError(key)
        else:
            return self._query[key]


class URI(_Part):
    """ Uniform Resource Identifier.

    
    http://bob@example.com:8080/data/report.html?date=2000-12-25#summary
    
    absolute_path_reference
        /data/report.html?date=2000-12-25#summary
    authority
        bob@example.com:8080
    fragment
        summary
    hierarchical_part
        //bob@example.com:8080/data/report.html
    host
        example.com
    path
        /data/report.html
    port
        8080
    query
        date=2000-12-25
    scheme
        http
    string
        http://bob@example.com:8080/data/report.html?date=2000-12-25#summary
    user_info
        bob
    """

    @classmethod
    def _cast(cls, obj):
        if obj is None:
            return None
        elif isinstance(obj, cls):
            return obj
        else:
            return cls(str(obj))

    def __init__(self, value):
        super(URI, self).__init__()
        if value is None:
            self._scheme = None
            self._authority = None
            self._path = None
            self._query = None
            self._fragment = None
        else:
            try:
                value = str(value.__uri__)
            except AttributeError:
                value = str(value)
            # scheme
            if ":" in value:
                self._scheme, value = value.partition(":")[0::2]
                self._scheme = percent_decode(self._scheme)
            else:
                self._scheme = None
            # fragment
            if "#" in value:
                value, self._fragment = value.partition("#")[0::2]
                self._fragment = percent_decode(self._fragment)
            else:
                self._fragment = None
            # query
            if "?" in value:
                value, self._query = value.partition("?")[0::2]
                self._query = Query(self._query)
            else:
                self._query = None
            # hierarchical part
            if value.startswith("//"):
                value = value[2:]
                slash = value.find("/")
                if slash >= 0:
                    self._authority = Authority(value[:slash])
                    self._path = Path(value[slash:])
                else:
                    self._authority = Authority(value)
                    self._path = Path("")
            else:
                self._authority = None
                self._path = Path(value)

    def __eq__(self, other):
        other = self._cast(other)
        return (self._scheme == other._scheme and
                self._authority == other._authority and
                self._path == other._path and
                self._query == other._query and
                self._fragment == other._fragment)

    def __ne__(self, other):
        other = self._cast(other)
        return (self._scheme != other._scheme or
                self._authority != other._authority or
                self._path != other._path or
                self._query != other._query or
                self._fragment != other._fragment)

    def __hash__(self):
        return hash(self.string)

    @property
    def __uri__(self):
        return self.string

    @property
    def string(self):
        """ The entire URI as a string or :py:const:`None` if undefined.
        """
        if self._path is None:
            return None
        u = []
        if self._scheme is not None:
            u += [percent_encode(self._scheme), ":"]
        if self._authority is not None:
            u += ["//", str(self._authority)]
        u += [str(self._path)]
        if self._query is not None:
            u += ["?", str(self._query)]
        if self._fragment is not None:
            u += ["#", percent_encode(self._fragment)]
        return "".join(u)

    @property
    def scheme(self):
        return self._scheme

    @property
    def authority(self):
        return self._authority

    @property
    def user_info(self):
        if self._authority is None:
            return None
        else:
            return self._authority.user_info

    @property
    def host(self):
        if self._authority is None:
            return None
        else:
            return self._authority.host
        
    @property
    def port(self):
        if self._authority is None:
            return None
        else:
            return self._authority.port

    @property
    def host_port(self):
        if self._authority is None:
            return None
        else:
            return self._authority.host_port

    @property
    def path(self):
        return self._path

    @property
    def query(self):
        return self._query

    @property
    def fragment(self):
        return self._fragment

    @property
    def hierarchical_part(self):
        if self._path is None:
            return None
        u = []
        if self._authority is not None:
            u += ["//", str(self._authority)]
        u += [str(self._path)]
        return "".join(u)

    @property
    def absolute_path_reference(self):
        if self._path is None:
            return None
        u = [str(self._path)]
        if self._query is not None:
            u += ["?", str(self._query)]
        if self._fragment is not None:
            u += ["#", percent_encode(self._fragment)]
        return "".join(u)

    def _merge_path(self, relative_path_reference):
        relative_path_reference = Path._cast(relative_path_reference)
        if self._authority is not None and not self._path:
            return Path("/" + str(relative_path_reference))
        else:
            if "/" in self._path.string:
                segments = self._path.segments
                segments[-1] = ""
                return Path("/".join(segments) + str(relative_path_reference))
            else:
                return relative_path_reference

    def resolve(self, reference, strict=True):
        """ Transform a reference relative to this URI to produce a full target
        URI.
        
        RFC3986, section 5.2.2 Transform References
        """
        if reference is None:
            return None
        reference = self._cast(reference)
        target = URI(None)
        if not strict and reference._scheme == self._scheme:
            reference_scheme = None
        else:
            reference_scheme = reference._scheme
        if reference_scheme is not None:
            target._scheme = reference_scheme
            target._authority = reference._authority
            target._path = reference._path.remove_dot_segments()
            target._query = reference._query
        else:
            if reference._authority is not None:
                target._authority = reference._authority
                target._path = reference._path.remove_dot_segments()
                target._query = reference._query
            else:
                if not reference.path:
                    target._path = self._path
                    if reference._query is not None:
                        target._query = reference._query
                    else:
                        target._query = self._query
                else:
                    if str(reference._path).startswith("/"):
                        target._path = reference._path.remove_dot_segments()
                    else:
                        target._path = self._merge_path(reference._path)
                        target._path = target._path.remove_dot_segments()
                    target._query = reference._query
                target._authority = self._authority
            target._scheme = self._scheme
        target._fragment = reference._fragment
        return target


class URITemplate(_Part):
    """A URI Template is a compact sequence of characters for describing a
    range of Uniform Resource Identifiers through variable expansion.
    
    This class exposes a full implementation of RFC6570.
    """

    @classmethod
    def _cast(cls, obj):
        if obj is None:
            return None
        elif isinstance(obj, cls):
            return obj
        else:
            return cls(str(obj))

    class _Expander(object):

        _operators = set("+#./;?&")

        def __init__(self, values):
            self.values = values

        def collect(self, *keys):
            """ Fetch a list of all values matching the keys supplied,
            returning (key, value) pairs for each.
            """
            items = []
            for key in keys:
                if key.endswith("*"):
                    key, explode = key[:-1], True
                else:
                    explode = False
                    if ":" in key:
                        key, max_length = key.partition(":")[0::2]
                        max_length = int(max_length)
                    else:
                        max_length = None
                value = self.values.get(key)
                if isinstance(value, dict):
                    if not value:
                        items.append((key, None))
                    elif explode:
                        items.extend((key, _) for _ in value.items())
                    else:
                        items.append((key, value))
                elif isinstance(value, (tuple, list)):
                    if explode:
                        items.extend((key, _) for _ in value)
                    else:
                        items.append((key, list(value)))
                elif max_length is not None:
                    items.append((key, value[:max_length]))
                else:
                    items.append((key, value))
            return [(key, value) for key, value in items if value is not None]

        def _expand(self, expression, safe=None, prefix="", separator=",",
                    with_keys=False, trim_empty_equals=False):
            items = self.collect(*expression.split(","))
            encode = lambda x: percent_encode(x, safe)
            for i, (key, value) in enumerate(items):
                if isinstance(value, tuple):
                    items[i] = "=".join(map(encode, value))
                else:
                    if isinstance(value, dict):
                        items[i] = ",".join(",".join(map(encode, item))
                                             for item in value.items())
                    elif isinstance(value, list):
                        items[i] = ",".join(map(encode, value))
                    else:
                        items[i] = encode(value)
                    if with_keys:
                        if items[i] or not trim_empty_equals:
                            items[i] = encode(key) + "=" + items[i]
                        else:
                            items[i] = encode(key)
            out = []
            for i, item in enumerate(items):
                out.append(prefix if i == 0 else separator)
                out.append(item)
            return "".join(out)

        def expand(self, expression):
            """ Dispatch to the correct expansion method.
            """
            if not expression:
                return ""
            if expression[0] in self._operators:
                operator, expression = expression[0], expression[1:]
                if operator == "+":
                    return self._expand(expression, reserved)
                elif operator == "#":
                    return self._expand(expression, reserved, prefix="#")
                elif operator == ".":
                    return self._expand(expression, prefix=".", separator=".")
                elif operator == "/":
                    return self._expand(expression, prefix="/", separator="/")
                elif operator == ";":
                    return self._expand(expression, prefix=";", separator=";",
                                        with_keys=True, trim_empty_equals=True)
                elif operator == "?":
                    return self._expand(expression, prefix="?", separator="&",
                                        with_keys=True)
                elif operator == "&":
                    return self._expand(expression, prefix="&", separator="&",
                                        with_keys=True)
            else:
                return self._expand(expression)

    _tokeniser = re.compile("(\{)([^{}]*)(\})")

    def __init__(self, template):
        super(URITemplate, self).__init__()
        self._template = template

    def __eq__(self, other):
        other = self._cast(other)
        return self._template == other._template

    def __ne__(self, other):
        other = self._cast(other)
        return self._template != other._template

    def __hash__(self):
        return hash(self.string)

    @property
    def string(self):
        if self._template is None:
            return None
        return self._template

    def expand(self, **values):
        """ Expand into a URI using the values supplied
        """
        if self._template is None:
            return None
        tokens = self._tokeniser.split(self._template)
        expander = URITemplate._Expander(values)
        out = []
        while tokens:
            token = tokens.pop(0)
            if token == "{":
                expression = tokens.pop(0)
                tokens.pop(0)
                out.append(expander.expand(expression))
            else:
                out.append(token)
        return URI("".join(out))
