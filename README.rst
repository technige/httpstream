==========
HTTPStream
==========

HTTPStream is an HTTP client library for Python that is designed to allow
incremental receipt and handling of web content as opposed to full document
retrieval. Additionally, large JSON documents may be parsed incrementally and
recombined into a series of smaller objects and arrays as required.


Installation
============

HTTPStream is hosted on PyPI and so to install, simply use pip::

    pip install httpstream


No external dependencies are required, the entire package is self-contained.


Basic Usage
===========

HTTPStream is based around {{{Resource}}} objects which are defined by a URI
and may be accessed via methods such as {{{get}}} and {{{post}}}. A
{{{Resource}}} may be declared as follows::

    >>> from httpstream import Resource
    >>> res = Resource("http://example.com/")


Once defined, accessor methods can be used on a resource in much the same way
as the Python built-in method, {{{open}}}. These return file-like
{{{Response}}} objects which may be read in full or iterated through. To
consume the entire response, simply use the {{{read}}} method on the response::

    >>> print res.get().read()
    <!DOCTYPE html>
    <html>
      <head>
        <title>Example</title>
      </head>
      <body>
        <h1>Welcome</h1>
        <p>Lorem ipsum...</p>
      </body>
    </html>

