"""
Python mock object framework, based on the jmock Java mock object
framework.

This module provides support for creating mock objects for use in unit
testing. The api is modelled on the jmock mock object framework.

Usage::

    import unittest
    import pmock

    class PowerStation(object):
        def start_up(self, reactor):
            try:
                reactor.activate('core')
            except Exception, err:
                reactor.shutdown()

    class PowerStationTestCase(unittest.TestCase):
        def testSuccessfulActivation(self):
            mock = pmock.Mock()
            mock.expect().method('activate').with(pmock.eq('core'))
            PowerStation().start_up(mock.proxy())
            mock.verify()
        def testProblematicActivation(self):
            mock = pmock.Mock()
            mock.expect().method('activate').with(pmock.eq('core')).will(
                pmock.throw_exception(RuntimeError('overheating')))
            mock.expect().method('shutdown')
            PowerStation().start_up(mock.proxy())
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
__version__ = "0.1"

import unittest


##############################################################################
# Exported classes and functions
##############################################################################

__all__ = ["Mock",
           "once", "at_least_once", "not_called",
           "eq", "same", "string_contains", "functor",
           "return_value", "raise_exception", "is_void"]


##############################################################################
# Mock objects framework
##############################################################################

class Error(AssertionError):

    def __init__(self, msg):
        AssertionError.__init__(self, msg)
        self.msg = msg

    def _mockers_str(cls, mockers):
        matchers_strs = [mocker.matchers_str() for mocker in mockers]
        return ", ".join(matchers_strs)

    _mockers_str = classmethod(_mockers_str)


class VerificationError(Error):
    """All the expectations have not been met."""
    
    def create_unsatisfied_error(cls, unsatisfied_mockers):
        msg = ("unsatisfied expectation(s): %s" %
               cls._mockers_str(unsatisfied_mockers))
        return VerificationError(msg)

    create_unsatisfied_error = classmethod(create_unsatisfied_error)


class MatchError(Error):
    """Method call unexpected or conflicts with expectations."""
    
    def create_conflict_error(cls, invocation, mocker):
        msg = ("call %s, conflicts with expectation: %s" %
               (invocation, mocker.matchers_str()))
        return MatchError(msg)

    create_conflict_error = classmethod(create_conflict_error)

    def create_unexpected_error(cls, invocation, unsatisfied_mockers):
        if len(unsatisfied_mockers) > 0:
            err_msg = ("unexpected call %s, expectation(s): %s" %
                       (invocation, cls._mockers_str(unsatisfied_mockers)))
        else:
            err_msg = ("unexpected call %s, no expectations remaining" %
                       invocation)
        return MatchError(err_msg)

    create_unexpected_error = classmethod(create_unexpected_error)


class DefinitionError(Error):
    """Expectation definition isn't valid."""

    def create_unregistered_label_error(cls, label):
        msg = "reference to undefined label: %s" % label
        return DefinitionError(msg)

    create_unregistered_label_error = classmethod(
        create_unregistered_label_error)

    def create_duplicate_label_error(cls, label, mocker):
        msg = ("label: %s is already defined by expectation: %s" %
               (label, mocker))
        return DefinitionError(msg)

    create_duplicate_label_error = classmethod(create_duplicate_label_error)


class AbstractArgumentsMatcher(object):

    def __init__(self, arg_constraints=(), kwarg_constraints={}):
        self._arg_constraints = arg_constraints
        self._kwarg_constraints = kwarg_constraints

    def __str__(self):
        if (len(self._arg_constraints) == 0 and
            len(self._kwarg_constraints) == 0):
            return self._no_explicit_constraints_str()
        else:
            arg_strs = [str(c) for c in self._arg_constraints]
            keywords = self._kwarg_constraints.keys()
            keywords.sort()
            for kw in keywords:
                constraint = self._kwarg_constraints[kw]
                arg_strs.append("%s=%s" % (kw, str(constraint)))
            return ", ".join(arg_strs)

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

    
class LeastArgumentsMatcher(AbstractArgumentsMatcher):

    def _no_explicit_constraints_str(self):
        return "..."

    def _matches_args(self, invocation):
        if len(self._arg_constraints) > len(invocation.args):
            return False
        return AbstractArgumentsMatcher._matches_args(self, invocation)


class AllArgumentsMatcher(AbstractArgumentsMatcher):

    def _no_explicit_constraints_str(self):
        return ""

    def _matches_args(self, invocation):
        if len(self._arg_constraints) != len(invocation.args):
            return False
        return AbstractArgumentsMatcher._matches_args(self, invocation)

    def _matches_kwargs(self, invocation):
        for invocation_kw in invocation.kwargs.iterkeys():
            if invocation_kw not in self._kwarg_constraints:
                return False
        return AbstractArgumentsMatcher._matches_kwargs(self, invocation)


class MethodMatcher(object):

    def __init__(self, name):
        self._name = name
        
    def __str__(self):
         return self._name

    def matches(self, invocation):
        return invocation.name == self._name


class InvocationLog(object):

    singleton = None
    
    def __init__(self):
        self._invocations = {}
        self._registered = {}

    def clear(self):
        self._invocations.clear()
        self._registered.clear()

    def invoked(self, label):
        self._invocations[label] = True

    def has_been_invoked(self, label):
        return self._invocations.has_key(label)
        
    def register(self, label, mocker):
        self._registered[label] = mocker

    def is_registered(self, label):
        return self._registered.has_key(label)

    def get_registered(self, label):
        return self._registered[label]
        
    def instance(cls):
        if cls.singleton is None:
            cls.singleton = InvocationLog()
        return cls.singleton

    instance = classmethod(instance)


class AfterLabelMatcher(object):

    def __init__(self, label, invocation_log):
        self._invocation_log = invocation_log
        self._label = label
        if not invocation_log.is_registered(label):
            raise DefinitionError.create_unregistered_label_error(label)
        
    def __str__(self):
         return "after(%s)" % repr(self._label)

    def matches(self):
        return self._invocation_log.has_been_invoked(self._label)


class InvocationMocker(object):
    
    def __init__(self, invocation_matcher):
        self._invocation_matcher = invocation_matcher
        self._method_matcher = None
        self._arguments_matcher = LeastArgumentsMatcher()
        self._action = is_void()
        self._label = None
        self._explicit_label = None
        self._label_matcher = None

    def is_satisfied(self):
        return self._invocation_matcher.is_satisfied()

    def invoke(self):
        InvocationLog.instance().invoked(self._label)
        self._invocation_matcher.invoke()
        return self._action.invoke()
    
    def is_void(self):
        """Method returns None."""
        self._action = is_void()
        return self
    
    def matchers_str(self):
        suffix = [""]
        if self._explicit_label:
            suffix.append("label(%s)" % repr(self._label))
        if self._label_matcher is not None:
            suffix.append(str(self._label_matcher))
        return "%s %s(%s)%s" % (self._invocation_matcher, self._method_matcher,
                                self._arguments_matcher, ".".join(suffix))
    
    def matches(self, invocation):
        return (self._invocation_matcher.matches() and
                self._method_matcher.matches(invocation) and
                self._arguments_matcher.matches(invocation) and
                (self._label_matcher is None or self._label_matcher.matches()))

    def _set_label(self, label, explicit):
        invocation_log = InvocationLog.instance()
        if explicit and invocation_log.is_registered(label):
            mocker = invocation_log.get_registered(label)
            raise DefinitionError.create_duplicate_label_error(
                label, mocker.matchers_str())
        self._label = label
        self._explicit_label = explicit
        invocation_log.register(label, self)
        
    def method(self, name):
        """Define method name."""
        self._set_label(name, False)
        self._method_matcher = MethodMatcher(name)
        return self

    def will(self, action):
        """Set action when method is called."""
        self._action = action
        return self
    
    def with(self, *arg_constraints, **kwarg_constraints):
        """Fully specify the method's arguments."""
        self._arguments_matcher = AllArgumentsMatcher(arg_constraints,
                                                      kwarg_constraints)
        return self

    def with_at_least(self, *arg_constraints, **kwarg_constraints):
        """Specify the method's minimum required arguments."""
        self._arguments_matcher = LeastArgumentsMatcher(arg_constraints,
                                                        kwarg_constraints)
        return self

    def no_args(self):
        """Method takes no arguments."""
        self._arguments_matcher = AllArgumentsMatcher()
        return self

    def label(self, label_str):
        """Define a label for use in other mock's L{after} method."""
        self._set_label(label_str, True)
        return self

    def after(self, label):
        """Expected to be called after the method with supplied label."""
        self._label_matcher = AfterLabelMatcher(label,
                                                InvocationLog.instance())
        return self


class MockInvocation(object):

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


class MockedMethod(object):

    def __init__(self, name, mock):
        self._name = name
        self._mock = mock

    def __call__(self, *args, **kwargs):
        return self._mock._method_invoked(
            MockInvocation(self._name, args, kwargs))


class Proxy(object):

    def __init__(self, mock):
        self._mock = mock

    def __getattr__(self, name):
        return MockedMethod(name, self._mock)


class InvokeConflictError(Exception):
    pass


class Mock(object):
    """Define a mock object's expectations and simple behaviour."""

    def __init__(self):
        self._mockers = []
        self._proxy = Proxy(self)

    def _unsatisfied_mockers(self):
        unsatisfied = []
        for mocker in self._mockers:
            if not mocker.is_satisfied():
                unsatisfied.append(mocker)
        return unsatisfied

    def _unmatched_method_invoked(self, invocation):
        unsatisfied_mockers = self._unsatisfied_mockers()
        raise MatchError.create_unexpected_error(invocation,
                                                 unsatisfied_mockers)
        
    def _method_invoked(self, invocation):
        matching_mocker = None
        for mocker in self._mockers:
            if mocker.matches(invocation):
                try:
                    return mocker.invoke()
                except InvokeConflictError:
                    raise MatchError.create_conflict_error(invocation, mocker)
        self._unmatched_method_invoked(invocation)

    def _add_mocker(self, mocker):
        self._mockers.insert(0, mocker)
        
    def expect(self, invocation_matcher):
        """Define a method that is expected to be called.

        @return: L{InvocationMocker}
        """
        if invocation_matcher is None:
            invocation_matcher = once()
        mocker = InvocationMocker(invocation_matcher)
        self._add_mocker(mocker)
        return mocker

    def stub(self):
        """Define a method that may or may not be called.

        @return: L{InvocationMocker}
        """
        mocker = InvocationMocker(StubInvocationMatcher())
        self._add_mocker(mocker)
        return mocker

    def proxy(self):
        """Return the mock object instance.""" 
        return self._proxy
    
    def verify(self):
        """Check that the mock object has been called as expected."""
        unsatisfied = self._unsatisfied_mockers()
        if len(unsatisfied) > 0:
            raise VerificationError.create_unsatisfied_error(unsatisfied)


class MockTestCase(unittest.TestCase):
    """Unit test base class to help reset ordering expectations."""
    
    def setUp(self):
        InvocationLog.instance().clear()


##############################################################################
# Mocked method actions
############################################################################## 

class ReturnValueAction(object):
    
    def __init__(self, value):
        self._value = value

    def invoke(self):
        return self._value


def return_value(value):
    """Action that returns the supplied value.    

    Convenience function for creating a L{ReturnValueAction} instance.
    """
    return ReturnValueAction(value)


def is_void():
    """Action that returns None.    

    Convenience function for creating a L{ReturnValueAction} instance.
    """
    return ReturnValueAction(None)


class RaiseExceptionAction(object):

    def __init__(self, exception):
        self._exception = exception

    def invoke(self):
        raise self._exception


def raise_exception(exception):
    """Action that raises the supplied exception.    

    Convenience function for creating a L{RaiseExceptionAction} instance.
    """
    return RaiseExceptionAction(exception)


##############################################################################
# Call match constraints
############################################################################## 

class AbstractInvocationMatcher(object):

    def __init__(self):
        self._invoked = False

    def invoke(self):
        self._invoked = True

    
class OnceInvocationMatcher(AbstractInvocationMatcher):

    def __str__(self):
        return "once"
    
    def is_satisfied(self):
        return self._invoked

    def matches(self):
        return not self._invoked


def once():
    """Method will be called only once.

    Convenience function for creating a L{OnceInvocationMatcher} instance.
    """
    return OnceInvocationMatcher()


class AtLeastOnceInvocationMatcher(AbstractInvocationMatcher):

    def __str__(self):
        return "at least once"

    def is_satisfied(self):
        return self._invoked

    def matches(self):
        return True


def at_least_once():
    """Method will be called at least once.

    Convenience function for creating a L{AtLeastOnceInvocationMatcher}
    instance.
    """
    return AtLeastOnceInvocationMatcher()


class NotCalledInvocationMatcher(AbstractInvocationMatcher):

    def __str__(self):
        return "not called"

    def invoke(self):
        AbstractInvocationMatcher.invoke(self)
        raise InvokeConflictError

    def is_satisfied(self):
        return not self._invoked
        
    def matches(self):
        return True


def not_called():
    """Method will not be called.

    Convenience function for creating a L{NotCalledInvocationMatcher} instance.
    """
    return NotCalledInvocationMatcher()


class StubInvocationMatcher(object):

    def invoke(self):
        pass

    def is_satisfied(self):
        return True
        
    def matches(self):
        return True


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
