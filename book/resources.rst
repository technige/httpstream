Resources
=========

A resource is an entity that exists on a distributed system, such as the World
Wide Web, and is identified by a URI. Commonly associated with the REST
architectural style, web resources are objects upon which HTTP methods like
GET and POST can be actioned.

HTTPStream is built around a core :class:`Resource <httpstream.Resource>`
class that embodies the concept of the web resource and instances can be
constructed by simply using the URI by which they are uniquely identified::

    >>> from httpstream import Resource
    >>> resource = Resource("http://example.com/foo/bar")

Although the ``Resource`` class can be used directly, applications may
alternatively either inherit from or wrap this class to provide more meaningful
naming::

    from httpstream import Resource

    class InheritedMailbox(Resource):

        def __init__(self, uri):
            Resource.__init__(self, uri)

        def deliver(self, message):
            self.post(message)

    class WrappedMailbox(object):

        def __init__(self, uri):
            self._resource = Resource(uri)

        def deliver(self, message):
            self._resource.post(message)

For simple HTTP access, resources can of course be created and used in an
immediate inline context::

    >>> from httpstream import Resource
    >>> results = Resource("https://api.duckduckgo.com/?q=neo4j&format=json").get().content

Methods such as :py:func:`get <httpstream.Resource.get>` return a
file-like :py:class:`Response <httpstream.Response>` object. The response
content can be either iterated through or retrieved at once::

    resource = Resource("http://example.com/")

    # print each line of the response in turn
    with resource.get() as response:
        for line in response:
            print line

    # print the entire response content at once
    with resource.get() as response:
        print response.content


.. autoclass:: httpstream.Resource
    :members: get, put, post, delete, head, resolve
