"""
Python mock object framework, providing support for creating mock
objects for use in unit testing.

The api is modelled on the jmock mock object framework.

Usage::

    import pmock
    import unittest

    class PowerStation(object):
        def start_up(self, reactor):
            try:
                reactor.activate('core')
            except Exception, err:
                reactor.shutdown()

    class PowerStationTestCase(unittest.TestCase):
        def test_successful_activation(self):
            mock = pmock.Mock()
            mock.expects(pmock.once()).activate(pmock.eq('core'))
            PowerStation().start_up(mock)
            mock.verify()
        def test_problematic_activation(self):
            mock = pmock.Mock()
            mock.expects(pmock.once()).activate(pmock.eq('core')).will(
                pmock.throw_exception(RuntimeError('overheating')))
            mock.expects(pmock.once()).shutdown()
            PowerStation().start_up(mock)
            mock.verify()

    if __name__ == '__main__':
        unittest.main()

Further information is available in the bundled documentation, and from
http://pmock.sourceforge.net/

Copyright (c) 2004, Graham Carlyle

This module is free software, and you may redistribute it and/or modify
it under the terms of the GNU GPL.
"""

__author__ = "Graham Carlyle"
__email__ = "grahamcarlyle at users dot sourceforge dot net"
__version__ = "0.3"


##############################################################################
# Exported classes and functions
##############################################################################

__all__ = ["Mock",
           "once", "at_least_once", "never",
           "eq", "same", "string_contains", "functor",
           "return_value", "raise_exception"]


##############################################################################
# Mock objects framework
##############################################################################

class Error(AssertionError):

    def __init__(self, msg):
        AssertionError.__init__(self, msg)
        self.msg = msg

    def _mockers_str(cls, mockers):
        mockers_strs = [str(mocker) for mocker in mockers]
        return ", ".join(mockers_strs)

    _mockers_str = classmethod(_mockers_str)


class VerificationError(Error):
    """An expectation have failed verification."""
    
    def create_error(cls, msg, verified_invokable):
        err_msg = "%s: %s" % (msg, verified_invokable)
        return VerificationError(err_msg)

    create_error = classmethod(create_error)


class MatchError(Error):
    """Method call unexpected."""
    
    def create_error(cls, msg, invocation, mock):
        err_msg = "%s\ninvoked %s" % (msg, invocation)
        invokables_str = mock.invokables_str()
        if invokables_str != "":
            err_msg += "\nin:\n" + invokables_str
        return MatchError(err_msg)

    create_error = classmethod(create_error)
    

class DefinitionError(Error):
    """Expectation definition isn't valid."""

    def create_unregistered_label_error(cls, label):
        msg = "reference to undefined label: %s" % label
        return DefinitionError(msg)

    create_unregistered_label_error = classmethod(
        create_unregistered_label_error)

    def create_duplicate_label_error(cls, label, mocker):
        msg = ("label: %s is already defined by: %s" % (label, mocker))
        return DefinitionError(msg)

    create_duplicate_label_error = classmethod(create_duplicate_label_error)


class AbstractArgumentsMatcher(object):

    def __init__(self, arg_constraints=(), kwarg_constraints={}):
        self._arg_constraints = arg_constraints
        self._kwarg_constraints = kwarg_constraints

    def _arg_strs(self):
        arg_strs = [str(c) for c in self._arg_constraints]
        keywords = self._kwarg_constraints.keys()
        keywords.sort()
        for kw in keywords:
            constraint = self._kwarg_constraints[kw]
            arg_strs.append("%s=%s" % (kw, str(constraint)))
        return arg_strs

    def _matches_args(self, invocation):
        for i, constraint in enumerate(self._arg_constraints):
            if not constraint.eval(invocation.args[i]):
                return False
        return True

    def _matches_kwargs(self, invocation):
        for kw, constraint in self._kwarg_constraints.iteritems():
            if (not invocation.kwargs.has_key(kw) or
                not constraint.eval(invocation.kwargs[kw])):
                return False
        return True

    def matches(self, invocation):
        return (self._matches_args(invocation) and
                self._matches_kwargs(invocation))

    def invoked(self, invocation):
        pass

    def verify(self):
        pass


class LeastArgumentsMatcher(AbstractArgumentsMatcher):

    def __str__(self):
        arg_strs = AbstractArgumentsMatcher._arg_strs(self)
        arg_strs.append("...")
        return "(%s)" % ", ".join(arg_strs)

    def _matches_args(self, invocation):
        if len(self._arg_constraints) > len(invocation.args):
            return False
        return AbstractArgumentsMatcher._matches_args(self, invocation)


ANY_ARGS_MATCHER = LeastArgumentsMatcher()


class AllArgumentsMatcher(AbstractArgumentsMatcher):

    def __str__(self):
        return "(%s)" % ", ".join(AbstractArgumentsMatcher._arg_strs(self))
        
    def _matches_args(self, invocation):
        if len(self._arg_constraints) != len(invocation.args):
            return False
        return AbstractArgumentsMatcher._matches_args(self, invocation)

    def _matches_kwargs(self, invocation):
        for invocation_kw in invocation.kwargs.iterkeys():
            if invocation_kw not in self._kwarg_constraints:
                return False
        return AbstractArgumentsMatcher._matches_kwargs(self, invocation)


NO_ARGS_MATCHER = AllArgumentsMatcher()


class MethodMatcher(object):

    def __init__(self, name):
        self._name = name

    def __str__(self):
         return self._name

    def matches(self, invocation):
        return invocation.name == self._name

    def invoked(self, invocation):
        pass

    def verify(self):
        pass


class InvocationLog(object):

    def __init__(self):
        self._registered = {}

    def register(self, label, mocker):
        self._registered[label] = mocker

    def is_registered(self, label):
        return self._registered.has_key(label)

    def get_registered(self, label):
        return self._registered[label]


# TODO refactor to use a matcher to determine if a invoker has been called
class AfterLabelMatcher(object):

    def __init__(self, label, invocation_log, description=None):
        self._invocation_log = invocation_log
        self._label = label
        self._description = description
        if not invocation_log.is_registered(label):
            raise DefinitionError.create_unregistered_label_error(label)
        
    def __str__(self):
        if self._description is None:
            suffix = ""
        else:
            suffix = self._description
        return ".after(%s%s)" % (repr(self._label), suffix)

    def matches(self, invocation):
        mocker = self._invocation_log.get_registered(self._label)
        return mocker.has_been_invoked()

    def invoked(self, invocation):
        pass

    def verify(self):
        pass


class InvocationMocker(object):
    
    def __init__(self, invocation_matcher):
        self._matchers = []
        self._invocation_matcher = invocation_matcher
        self._matchers.append(invocation_matcher)
        self._action = None
        self._label = None
        self._has_been_invoked = False

    def __str__(self):
        strs = ["%s: " % str(self._invocation_matcher)]
        for matcher in self._matchers[1:]:
            strs.append(str(matcher))
        if self._action is not None:
            strs.append(", %s" % self._action)
        if self._label is not None:
            strs.append(" [%s]" % self._label)
        return "".join(strs)

    def add_matcher(self, matcher):
        self._matchers.append(matcher)

    def set_action(self, action):
        self._action = action

    def invoke(self, invocation):
        self._has_been_invoked = True
        for matcher in self._matchers:
            matcher.invoked(invocation)
        if self._action is not None:
            return self._action.invoke(invocation)

    def has_been_invoked(self):
        return self._has_been_invoked
    
    def matches(self, invocation):
        for matcher in self._matchers:
            if not matcher.matches(invocation):
                return False
        return True

    def set_label(self, label):
        self._label = label

    def verify(self):
        try:
            for matcher in self._matchers:
                matcher.verify()
        except AssertionError, err:
            raise VerificationError.create_error(str(err), self)

    
class InvocationMockerBuilder(object):

    def __init__(self, mocker, invocation_log):
        self._mocker = mocker
        self._invocation_log = invocation_log


class MatchBuilder(InvocationMockerBuilder):
    
    def with(self, *arg_constraints, **kwarg_constraints):
        """Fully specify the method's arguments."""
        self._mocker.add_matcher(AllArgumentsMatcher(arg_constraints,
                                                     kwarg_constraints))
        return self

    def with_at_least(self, *arg_constraints, **kwarg_constraints):
        """Specify the method's minimum required arguments."""
        self._mocker.add_matcher(LeastArgumentsMatcher(arg_constraints,
                                                       kwarg_constraints))
        return self

    def any_args(self):
        """Method takes any arguments."""
        self._mocker.add_matcher(ANY_ARGS_MATCHER)
        return self

    def no_args(self):
        """Method takes no arguments."""
        self._mocker.add_matcher(NO_ARGS_MATCHER)
        return self

    def will(self, action):
        """Set action when method is called."""
        self._mocker.set_action(action)
        return self

    def label(self, label_str):
        """Define a label for use in other mock's L{after} method."""
        if self._invocation_log.is_registered(label_str):
            raise DefinitionError.create_duplicate_label_error(
                label_str, str(self._invocation_log.get_registered(label_str)))
        self._mocker.set_label(label_str)
        self._invocation_log.register(label_str, self._mocker)
        return self

    def after(self, label_str, other_mock=None):
        """Expected to be called after the method with supplied label."""
        if other_mock is None:
            matcher = AfterLabelMatcher(label_str, self._invocation_log)
        else:
            if other_mock.get_name() is not None:
                description = repr(other_mock.get_name())
            else:
                description = str(other_mock)
            matcher = AfterLabelMatcher(label_str, other_mock._invocation_log,
                                        " on mock %s" % description)
        self._mocker.add_matcher(matcher)
        return self


class NameAndDirectArgsBuilder(InvocationMockerBuilder):

    def __call__(self, *arg_constraints, **kwarg_constraints):
        self._mocker.add_matcher(AllArgumentsMatcher(arg_constraints,
                                                     kwarg_constraints))
        return MatchBuilder(self._mocker, self._invocation_log)

    def __getattr__(self, name):
        """Define method name directly."""
        self._mocker.add_matcher(MethodMatcher(name))
        self._invocation_log.register(name, self._mocker)
        return self

    def method(self, name):
        """Define method name."""
        self._mocker.add_matcher(MethodMatcher(name))
        self._invocation_log.register(name, self._mocker)
        return MatchBuilder(self._mocker, self._invocation_log)


class Invocation(object):

    def __init__(self, name, args, kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        arg_strs = [repr(arg) for arg in self.args]
        keywords = self.kwargs.keys()
        keywords.sort()
        for kw in keywords:
            arg_strs.append("%s=%s" % (kw, repr(self.kwargs[kw])))
        return "%s(%s)" % (self.name, ", ".join(arg_strs))


class BoundMethod(object):

    def __init__(self, name, mock):
        self._name = name
        self._mock = mock

    def __call__(self, *args, **kwargs):
        return self._mock.invoke(Invocation(self._name, args, kwargs))


class Proxy(object):
    """A proxy for a mock object."""
    
    def __init__(self, mock):
        self._mock = mock

    def __getattr__(self, attr_name):
        return BoundMethod(attr_name, self._mock)


class Mock(object):
    """A mock object."""

    def __init__(self, name=None):
        self._name = name
        self._invokables = []
        self._proxy = Proxy(self)
        self._invocation_log = InvocationLog()

    def __getattr__(self, attr_name):
        return BoundMethod(attr_name, self)

    def get_name(self):
        return self._name

    def _get_match_order_invokables(self):
        return self._invokables[::-1] # LIFO

    def invoke(self, invocation):
        try:
            matching_invokable = None
            for invokable in self._get_match_order_invokables():
                if invokable.matches(invocation):
                    return invokable.invoke(invocation)
            # TODO replace with default stub
            raise AssertionError("no match found")
        except AssertionError, err:
            raise MatchError.create_error(str(err), invocation, self)

    def add_invokable(self, invokable):
        self._invokables.append(invokable)

    def invokables_str(self):
        invokable_strs = [str(invokable) for invokable in self._invokables]
        return ",\n".join(invokable_strs)

    def expects(self, invocation_matcher):
        """Define an expectation for a method.

        @return: L{InvocationMocker}
        """
        mocker = InvocationMocker(invocation_matcher)
        self.add_invokable(mocker)
        return NameAndDirectArgsBuilder(mocker, self._invocation_log)

    def stubs(self):
        """Define a method that may or may not be called.

        @return: L{InvocationMocker}
        """
        mocker = InvocationMocker(_STUB_MATCHER_INSTANCE)
        self.add_invokable(mocker)
        return NameAndDirectArgsBuilder(mocker, self._invocation_log)

    def proxy(self):
        """Return a proxy to the mock object.

        Proxies only have the mocked methods which may be useful if the
        mock's builder methods are in the way.
        """ 
        return self._proxy
    
    def verify(self):
        """Check that the mock object has been called as expected."""
        for invokable in self._get_match_order_invokables():
            invokable.verify()


##############################################################################
# Mocked method actions
############################################################################## 

class ReturnValueAction(object):
    
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return "returns %s" % repr(self._value)

    def invoke(self, invocation):
        return self._value


def return_value(value):
    """Action that returns the supplied value.    

    Convenience function for creating a L{ReturnValueAction} instance.
    """
    return ReturnValueAction(value)


class RaiseExceptionAction(object):

    def __init__(self, exception):
        self._exception = exception

    def __str__(self):
        return "raises %s" % self._exception

    def invoke(self, invocation):
        raise self._exception


def raise_exception(exception):
    """Action that raises the supplied exception.    

    Convenience function for creating a L{RaiseExceptionAction} instance.
    """
    return RaiseExceptionAction(exception)


##############################################################################
# Invocation matchers
############################################################################## 

class InvokedRecorderMatcher(object):

    def __init__(self):
        self._invoked = False

    def has_been_invoked(self):
        return self._invoked
    
    def matches(self, invocation):
        return True

    def invoked(self, invocation):
        self._invoked = True

    def verify(self):
        pass

    
class OnceInvocationMatcher(InvokedRecorderMatcher):

    def __str__(self):
        if self.has_been_invoked():
            return "expected once and has been invoked"
        else:
            return "expected once"
    
    def matches(self, invocation):
        return not self.has_been_invoked()

    def verify(self):
        if not self.has_been_invoked():
            raise AssertionError("expected method was not invoked")


def once():
    """Method will be called only once.

    Convenience function for creating a L{OnceInvocationMatcher} instance.
    """
    return OnceInvocationMatcher()


class AtLeastOnceInvocationMatcher(InvokedRecorderMatcher):

    def __str__(self):
        if self.has_been_invoked():
            return "expected at least once and has been invoked"
        else:
            return "expected at least once"

    def matches(self, invocation):
        return True

    def verify(self):
        if not self.has_been_invoked():
            raise AssertionError("expected method was not invoked")


def at_least_once():
    """Method will be called at least once.

    Convenience function for creating a L{AtLeastOnceInvocationMatcher}
    instance.
    """
    return AtLeastOnceInvocationMatcher()


class NotCalledInvocationMatcher(object):

    def __str__(self):
        return "expected not to be called"

    def invoked(self, invocation):
        raise AssertionError("expected method to never be invoked")

    def matches(self, invocation):
        return True

    def verify(self):
        pass


_NOT_CALLED_MATCHER_INSTANCE = NotCalledInvocationMatcher()


def never():
    """Method will not be called.

    Convenience function for getting a L{NotCalledInvocationMatcher} instance.
    """
    return _NOT_CALLED_MATCHER_INSTANCE


class StubInvocationMatcher(object):

    def __str__(self):
        return "stub"
    
    def invoked(self, invocation):
        pass

    def matches(self, invocation):
        return True

    def verify(self):
        pass


_STUB_MATCHER_INSTANCE = StubInvocationMatcher()


##############################################################################
# Argument constraints
############################################################################## 

class EqConstraint(object):

    def __init__(self, expected):
        self._expected = expected

    def __repr__(self):
        return "%s.eq(%s)" % (__name__, repr(self._expected))

    def eval(self, arg):
        return self._expected == arg


def eq(expected):
    """Argument will be equal to supplied value.

    Convenience function for creating a L{EqConstraint} instance.
    """
    return EqConstraint(expected)


class SameConstraint(object):

    def __init__(self, expected):
        self._expected = expected

    def __repr__(self):
        return "%s.same(%s)" % (__name__, repr(self._expected))

    def eval(self, arg):
        return self._expected is arg


def same(expected):
    """Argument will be the same as the supplied reference.

    Convenience function for creating a L{SameConstraint} instance.
    """
    return SameConstraint(expected)


class StringContainsConstraint(object):

    def __init__(self, expected):
        self._expected = expected

    def __repr__(self):
        return "%s.string_contains(%s)" % (__name__, repr(self._expected))

    def eval(self, arg):
        return (arg is not None) and (arg.find(self._expected) != -1)


def string_contains(expected):
    """Argument contains the supplied substring.

    Convenience function for creating a L{StringContainsConstraint} instance.
    """
    return StringContainsConstraint(expected)


class FunctorConstraint(object):

    def __init__(self, boolean_functor):
        self._boolean_functor = boolean_functor

    def __repr__(self):
        return "%s.functor(%s)" % (__name__, repr(self._boolean_functor))

    def eval(self, arg):
        return self._boolean_functor(arg)


def functor(boolean_functor):
    """Supplied unary function evaluates to True when called with argument.

    Convenience function for creating a L{FunctorConstraint} instance.
    """
    return FunctorConstraint(boolean_functor)
