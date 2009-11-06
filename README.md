README
======

pMock provides support for creating mock objects for use in unit testing.
The API is modelled on the jMock mock object framework. It was written by an
ex colleague of mine, Graham Carlyle, and the official version is [hosted on
SourceForge](http://pmock.sourceforge.net).

This github repo is not an official version and is not the new home for pMock.
It is simply the place where I'm maintaining and sharing my patches.

Installation
------------

I've not pushed this package to PyPI; you'll need to clone the git repository
and install it locally:

    $ git clone git://github.com/gma/pmock.git
    $ cd pmock
    $ sudo python setup.py install

Documentation
-------------

Check the SourceForge page for a brief
[overview](http://pmock.sourceforge.net/overview.html) and for the [full API
reference](http://pmock.sourceforge.net/api/index.html).

What are the patches?
---------------------

The version of pMock that is currently on SourceForge (version 0.3) doesn't
run under Python 2.6, as it defines a method called `with()`. In Python 2.6
`with` became a keyword.

So that I can continue using pMock with Python 2.6 I've renamed the `with()`
method to `taking()`. That's it, there are no other changes to the API. If
you're an existing user of pMock then you're unlikely to find that this change
will break your existing tests; it's really only used internally by pMock
itself.

To avoid future confusion over versions that Graham C (or others) might
release I've bumped the version number to 0.4-gma.
