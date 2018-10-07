"""pMock: Python mock object framework.

pMock provides support for creating mock objects for use in unit testing.
The api is modelled on the jmock mock object framework.
"""

classifiers = """\
Development Status :: 3 - Alpha
Intended Audience :: Developers
License :: OSI Approved :: Python Software Foundation License
Programming Language :: Python :: 2 :: Only
Topic :: Software Development :: Libraries :: Python Modules
Topic :: Software Development :: Testing
Operating System :: OS Independent
"""

from distutils.core import setup

doclines = __doc__.split("\n")

setup (
    name = "pmock",
    version = "0.4-gma",
    maintainer="Graham Carlyle",
    maintainer_email="grahamcarlyle@users.sourceforge.net",
    license="Same terms as Python",
    platforms = ["any"],
    url = "http://pmock.sf.net",
    description = doclines[0],
    classifiers = filter(None, classifiers.split("\n")),
    long_description = "\n".join(doclines[2:]),
    package_dir = {"": "src"},
    py_modules = ["pmock"]
    )
