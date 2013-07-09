Working with URIs
=================


URIs
----

.. autoclass:: httpstream.uri.URI
    :members:
    :undoc-members:

.. autoclass:: httpstream.uri.Authority
    :members:
    :undoc-members:

.. autoclass:: httpstream.uri.Path
    :members:
    :undoc-members:

.. autoclass:: httpstream.uri.Query
    :members:
    :undoc-members:


Percent Encoding
----------------

Percent encoding is used within URI components to allow inclusion of certain
characters which are not within a permitted set.

.. autofunction:: httpstream.uri.percent_encode

.. autofunction:: httpstream.uri.percent_decode

.. seealso::
    `RFC 3986 § 2.1`_

.. _`RFC 3986 § 2.1`: http://tools.ietf.org/html/rfc3986#section-2.1

