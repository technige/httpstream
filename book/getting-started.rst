Getting Started
===============

The easiest way to get started with HTTPStream is via one of its simple wrapper methods, such as
:func:`get <httpstream.get>` or :func:`post <httpstream.post>`. These methods allow you to perform
an HTTP action against a particular URI, returning a full :class:`Response <httpstream.Response>`
object.

    >>> from httpstream import get
    >>> response = get("http://nigelsmall.com/time")
    >>> response.content
    '2014-12-25T09:10:11'
    >>> response.content_type
    'text/plain'

A ``post`` is similar to a ``get`` but it can also accept a ``body``. This payload can be supplied
as plain text or as a dictionary and will be sent as ``text/plain`` or ``application/json``
accordingly.

All the available direct methods are listed below:

.. autofunction:: httpstream.get

.. autofunction:: httpstream.put

.. autofunction:: httpstream.patch

.. autofunction:: httpstream.post

.. autofunction:: httpstream.delete

.. autofunction:: httpstream.head


Requests & Responses
--------------------

HTTPStream defines four types of response objects. A standard ``Response`` is
generated on receipt of a 2xx status code and a ``ClientError`` and
``ServerError`` may be raised on receipt of 4xx and 5xx statuses respectively.
The fourth response type is ``Redirection`` which is generally consumed
internally but may also be returned under certain circumstances, such as when
the maximum number of redirections have been followed for a given request.

Response objects are file-like and as such may be ``read`` or iterated through
The ``iter_lines`` and ``iter_json`` methods may be used to step through
known types of content. The response object itself may also be iterated
directly and an appropriate type of iterator is selected depending on the
type of content available. The code below shows how to print each line of
textual content as it is received::

    >>> for line in response.get():
    ...     print(line)


.. autoclass:: httpstream.Request
    :members:

.. autoclass:: httpstream.Response
    :members:

.. autoclass:: httpstream.Redirection
    :show-inheritance:
    :members:

.. autoclass:: httpstream.ClientError
    :show-inheritance:
    :members:

.. autoclass:: httpstream.ServerError
    :show-inheritance:
    :members:


Errors
------

.. autoexception:: httpstream.NetworkAddressError
    :members:
    :undoc-members:

.. autoexception:: httpstream.SocketError
    :members:
    :undoc-members:

.. autoexception:: httpstream.RedirectionError
    :members:
    :undoc-members:
