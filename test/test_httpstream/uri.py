
from unittest import TestCase

from httpstream import URI


class URIConstructionTestCase(TestCase):

    def test_can_parse_uri_with_port(self):
        uri = URI("http://localhost:7474/db/data/")
        assert uri.scheme == "http"
        assert uri.netloc == "localhost:7474"
        assert uri.path == "/db/data/"
        assert uri.params == ""
        assert uri.query == ""
        assert uri.fragment == ""
        assert uri.username is None
        assert uri.password is None
        assert uri.hostname == "localhost"
        assert uri.port == 7474
        assert uri.base == "http://localhost:7474"
        assert uri.reference == "/db/data/"

    def test_can_parse_uri_without_port(self):
        uri = URI("http://localhost/db/data/")
        assert uri.scheme == "http"
        assert uri.netloc == "localhost"
        assert uri.path == "/db/data/"
        assert uri.params == ""
        assert uri.query == ""
        assert uri.fragment == ""
        assert uri.username is None
        assert uri.password is None
        assert uri.hostname == "localhost"
        assert uri.port is None
        assert uri.base == "http://localhost"
        assert uri.reference == "/db/data/"

    def test_can_parse_uri_without_path(self):
        uri = URI("http://localhost")
        assert uri.scheme == "http"
        assert uri.netloc == "localhost"
        assert uri.path == ""
        assert uri.params == ""
        assert uri.query == ""
        assert uri.fragment == ""
        assert uri.username is None
        assert uri.password is None
        assert uri.hostname == "localhost"
        assert uri.port is None
        assert uri.base == "http://localhost"
        assert uri.reference == ""


class URIJoinTestCase(TestCase):

    def test_can_join_with_trailing_slash(self):
        uri = URI("http://localhost:7474/")
        joined = URI.join(uri, "db", "data")
        assert joined == "http://localhost:7474/db/data"

    def test_can_join_without_trailing_slash(self):
        uri = URI("http://localhost:7474")
        joined = URI.join(uri, "db", "data")
        assert joined == "http://localhost:7474/db/data"

    def test_can_join_and_append_trailing_slash(self):
        uri = URI("http://localhost:7474/")
        joined = URI.join(uri, "db", "data", trailing_slash=True)
        assert joined == "http://localhost:7474/db/data/"

    def test_braces_will_be_encoded(self):
        uri = URI("http://localhost:7474/foo/")
        joined = URI.join(uri, "{bar}")
        assert joined == "http://localhost:7474/foo/%7Bbar%7D"

    def test_braces_can_be_unencoded(self):
        uri = URI("http://localhost:7474/foo/")
        joined = URI.join(uri, "{bar}", safe="{}")
        assert joined == "http://localhost:7474/foo/{bar}"


class URIFormatTestCase(TestCase):

    def test_can_format_uri(self):
        uri = URI("http://localhost:7474/foo/{bar}")
        formatted = uri.format(bar="spoon")
        assert formatted == "http://localhost:7474/foo/spoon"

    def test_can_format_uri_with_encoding(self):
        uri = URI("http://localhost:7474/foo/{bar}")
        formatted = uri.format(bar="knife & fork & spoon")
        assert formatted == "http://localhost:7474/foo/" \
                            "knife%20%26%20fork%20%26%20spoon"
