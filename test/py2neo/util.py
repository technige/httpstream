
try:
    from urllib.parse import quote as _quote
except ImportError:
    from urllib import quote as _quote


def compact(obj):
    """ Return a copy of an object with all :py:const:`None` values removed.
    """
    if isinstance(obj, dict):
        return dict((key, value) for key, value in obj.items() if value is not None)
    else:
        return obj.__class__(value for value in obj if value is not None)


def flatten(*values):
    for value in values:
        if hasattr(value, "__iter__"):
            for val in value:
                yield val
        else:
            yield value


has_all = lambda iterable, items: all(item in iterable for item in items)


def quote(string, safe='/'):
    """ Quote a string for use in URIs.
    """
    try:
        return _quote(string, safe.encode("utf-8"))
    except UnicodeEncodeError:
        return string
