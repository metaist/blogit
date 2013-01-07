#!/usr/bin/python
# coding: utf-8

"""Utilities for manipulating dictionaries."""

__author__ = 'The Metaist'
__copyright__ = 'Copyright 2013, Metaist'
__email__ = 'metaist@metaist.com'
__license__ = 'MIT'
__maintainer__ = 'The Metaist'
__status__ = 'Prototype'
__version_info__ = ('0', '0', '1')
__version__ = '.'.join(__version_info__)


def interpolate(dct, nesting=1):
    """Return a dictionary whose values are interpolated using itself.

    >>> expected = {'a': 'this', 'b': 'this works'}
    >>> interpolate({'a': 'this', 'b': '{a} works'}) == expected
    True
    """
    result = dct
    for _ in range(nesting):
        for key, val in result.items():
            if type(val) is str:
                result[key] = val.format(**result)  # pylint: disable=W0142
    return result


class Namespace(object):
    """A namespace of key / value pairs."""

    def update(self, other=None, **kwargs):
        """Updates this Namespace using a dict, object, or key/values.

        If both a dictionary and keywords are given, keywords win:
        >>> ns = Namespace({'a': 1}, a=2)
        >>> ns.a == 2
        True

        Using an object:
        >>> class OtherObject(object): pass
        >>> x = OtherObject()
        >>> x.a = 1
        >>> ns = Namespace(x)
        >>> ns.a == 1
        True
        """
        if type(other) is dict:
            self.__dict__.update(other)
        elif other and isinstance(other, object):
            self.__dict__.update(other.__dict__)

        if kwargs:
            self.__dict__.update(kwargs)

        return self

    def keys(self):
        """Returns a list of keys in this namespace.

        >>> Namespace(a=1).keys() == ['a']
        True
        """
        return self.__dict__.keys()

    def values(self):
        """Returns a list of values in this namespace.

        >>> Namespace(a=1).values() == [1]
        True
        """
        return self.__dict__.values()

    def items(self):
        """Returns a list of tuples in this namespace.

        >>> Namespace(a=1).items() == [('a', 1)]
        True
        """
        return self.__dict__.items()

    def __init__(self, other=None, **kwargs):
        """Construct a Namespace from a dict, object, or key/values."""
        self.update(other, **kwargs)

    def __repr__(self):
        """Return string representation of this namespace.

        >>> repr(Namespace(f='test'))
        "Namespace({'f': 'test'})"
        """
        return '{0.__class__.__name__}({0.__dict__!r})'.format(self)

    def __len__(self):
        """Return number of attributes defined in this namespace.

        >>> len(Namespace(a=1, b=2)) == 2
        True
        """
        return len(self.__dict__)

    def __contains__(self, item):
        """Return True if an key is in the Namespace.

        >>> ns = Namespace(a=1)
        >>> 'a' in ns
        True
        >>> 'x' in ns
        False
        """
        return item in self.__dict__

    def __getattr__(self, name):
        """Return None when the value does not exist.

        >>> ns = Namespace(a=1)
        >>> ns.x is None
        True
        """
        return None  # since this is always called when the attr doesn't exist

    def __getitem__(self, key):
        """Return the value of an attribute when accessed as a sequence.

        >>> ns = Namespace(a=1)
        >>> ns['a'] == 1 and ns['x'] is None
        True
        """
        result = None
        if key in self.__dict__:
            result = self.__dict__[key]
        return result

    def __setitem__(self, key, value):
        """Set the value of an attribute using brackets.

        >>> ns = Namespace(a=0)
        >>> ns['a'] = 1
        >>> ns.a == 1
        True
        """
        self.__dict__[key] = value

    def __delitem__(self, key):
        """Delete the attribute from the namespace.

        >>> ns = Namespace(a=1)
        >>> ns.a == 1
        True
        >>> del ns['a']
        >>> ns.a is None
        True
        """
        del self.__dict__[key]

    def __iter__(self):
        """Return an iterator for this namespace.

        >>> [v for k, v in Namespace(a=1)] == [1]
        True
        """
        return self.__dict__.iteritems()

    def __eq__(self, other):
        """Returns True if the namespaces have the same dictionary."""
        return type(other) == Namespace and self.__dict__ == other.__dict__

    def _combine(self, other, selfish=True, offspring=True):
        """Utility method for combining Namespaces with other objects."""
        result = self
        dct = dict()

        if selfish:  # self-first
            dct.update(self.__dict__)

        # add other object
        if type(other) is dict:
            dct.update(other)
        elif other and isinstance(other, object):
            dct.update(other.__dict__)

        if not selfish:  # self-last
            dct.update(self.__dict__)

        if offspring:  # create new object
            result = Namespace(dct)
        else:  # modify self
            self.__dict__.update(dct)

        return result

    def __add__(self, other):
        """Return a new Namespace combining this Namespace with another object.

        >>> ns1 = Namespace(a=1, b=2)
        >>> ns2 = Namespace(a=3, c=4)
        >>> ns1 + ns2 == Namespace(a=3, b=2, c=4)
        True
        >>> ns2 + ns1 == Namespace(a=1, b=2, c=4)
        True
        """
        return self._combine(other, selfish=True, offspring=True)

    def __radd__(self, other):
        """Return a new Namespace combining another object with this Namespace.

        >>> expected = Namespace(a=1, b=2)
        >>> {'a': 1} + Namespace(b=2) == expected
        True
        >>> Namespace(a=1) + {'b': 2} == expected
        True

        Add an object (its attributes) to an existing namespace:
        >>> class OtherObject(object): pass
        >>> x = OtherObject()
        >>> x.foo = 'bar'
        >>> Namespace(a=1) + x == Namespace(a=1, foo='bar')
        True
        >>> x.foo = 'baz'
        >>> x + Namespace(b=2) == Namespace(b=2, foo='baz')
        True
        """
        return self._combine(other, selfish=False, offspring=True)

    def __iadd__(self, other):
        """Return this Namespace after adding another object.

        >>> ns = Namespace(a=1)
        >>> ns += {'a': 2}
        >>> ns.a == 2
        True
        """
        return self._combine(other, selfish=True, offspring=False)
