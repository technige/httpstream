
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


class URI(object):

    @classmethod
    def join(cls, *parts):
        parts = list(parts)
        for i, part in enumerate(parts):
            if i > 0:
                parts[i] = str(parts[i]).lstrip("/")
            if i < len(parts) - 1:
                parts[i] = str(parts[i]).rstrip("/")
        return "/".join(parts)

    def __init__(self, uri):
        try:
            self.__uri__ = str(uri.__uri__)
        except AttributeError:
            self.__uri__ = str(uri)
        parsed = urlparse(self.__uri__)
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
        return "<{0}>".format(self.__uri__)

    def __str__(self):
        return self.__uri__

    def __eq__(self, other):
        return URI(self).__uri__ == URI(other).__uri__

    def __ne__(self, other):
        return URI(self).__uri__ != URI(other).__uri__

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
