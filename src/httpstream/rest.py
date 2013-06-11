
from .http import Request
from .uri import URI


class Resource(object):

    def __init__(self, uri):
        self.__uri__ = URI(uri)

    def get(self):
        return Request("GET", self.__uri__).stream()

    def put(self, body):
        return Request("PUT", self.__uri__, body).stream()

    def post(self, body):
        return Request("POST", self.__uri__, body).stream()

    def delete(self):
        return Request("DELETE", self.__uri__).stream()
