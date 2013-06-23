
try:
    from urllib.parse import quote, quote_plus, unquote, urlparse, urlunparse
except ImportError:
    from urllib import quote, quote_plus, unquote
    from urlparse import urlparse, urlunparse


class URI(object):

    @staticmethod
    def _pack_query_param(key, value):
        if value is None:
            return quote(key, safe="")
        else:
            return quote(key, safe="") + "=" + quote(value, safe="")

    @staticmethod
    def _unpack_query_param(item):
        if "=" in item:
            return map(item.partition("=")[0::2], unquote)
        else:
            return unquote(item), None

    @classmethod
    def join(cls, *parts, **kwargs):
        if len(parts) >= 2:
            parts = list(str(part) for part in parts)
            plus = kwargs.get("plus", False)
            safe = kwargs.get("safe", "")
            for i, part in enumerate(parts):
                if i == 0:
                    parts[i] = parts[i].rstrip("/")
                elif plus:
                    parts[i] = quote_plus(parts[i], safe=safe)
                else:
                    parts[i] = quote(parts[i], safe=safe)
        if kwargs.get("trailing_slash"):
            return URI("/".join(parts) + "/")
        else:
            return URI("/".join(parts))

    def __init__(self, uri):
        try:
            parsed = urlparse(str(uri.__uri__))
        except AttributeError:
            parsed = urlparse(str(uri))
        self.scheme = parsed.scheme
        self.netloc = parsed.netloc
        self.path = parsed.path
        self.params = parsed.params
        self.query = parsed.query
        self.fragment = parsed.fragment
        self.username = parsed.username
        self.password = parsed.password
        self.hostname = parsed.hostname
        self.port = parsed.port

    def __hash__(self):
        return hash(self.__uri__)

    def __repr__(self):
        return repr(self.__uri__)

    def __str__(self):
        return str(self.__uri__)

    def __eq__(self, other):
        return URI(self).__uri__ == URI(other).__uri__

    def __ne__(self, other):
        return URI(self).__uri__ != URI(other).__uri__

    def __len__(self):
        return len(str(self.__uri__))

    @property
    def __uri__(self):
        return urlunparse((self.scheme, self.netloc, self.path,
                           self.params, self.query, self.fragment))

    @property
    def query(self):
        return "&".join(
            self._pack_query_param(key, value)
            for key, value in self._query.items()
        )

    @query.setter
    def query(self, value):
        if isinstance(value, dict):
            self._query = value
        elif value:
            self._query = dict(
                self._unpack_query_param(item)
                for item in str(value).split("&")
            )
        else:
            self._query = {}

    @property
    def base(self):
        return "{0}://{1}".format(self.scheme, self.netloc)

    @property
    def reference(self):
        ref = [self.path]
        if self.query:
            ref.append("?")
            ref.append(self.query)
        if self.fragment:
            ref.append("#")
            ref.append(self.fragment)
        return "".join(ref)

    def format(self, *args, **kwargs):
        return URI(self.__uri__.format(
            *[quote(arg, safe="") for arg in args],
            **dict(
                (key, quote(value, safe=""))
                for key, value in kwargs.items()
            )
        ))
