'''
Python mock object framework, based on the jmock Java mock object
framework.

This module provides support for creating mock objects for use in unit
testing. The api is modelled on the jmock mock object framework.

Simple usage:

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
'''

__author__ = "Graham Carlyle"
__email__ = "grahamcarlyle at users dot sourceforge dot net"
__version__ = "0.1"

import unittest


##############################################################################
# Exported classes and functions
##############################################################################
__all__ = []


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

    def create_unsatisfied_error(cls, unsatisfied_mockers):
        msg = ("unsatisfied expectation(s): %s" %
               cls._mockers_str(unsatisfied_mockers))
        return VerificationError(msg)

    create_unsatisfied_error = classmethod(create_unsatisfied_error)


class MatchError(Error):

    def create_conflict_error(cls, call, mocker):
        msg = ("call %s, conflicts with expectation: %s" %
               (call, mocker.matchers_str()))
        return MatchError(msg)

    create_conflict_error = classmethod(create_conflict_error)

    def create_unexpected_error(cls, call, unsatisfied_mockers):
        if len(unsatisfied_mockers) > 0:
            err_msg = ("unexpected call %s, expectation(s): %s" %
                       (call, cls._mockers_str(unsatisfied_mockers)))
        else:
            err_msg = ("unexpected call %s, no expectations remaining" %
                       call)
        return MatchError(err_msg)

    create_unexpected_error = classmethod(create_unexpected_error)


class DefinitionError(Error):

    def create_unregistered_label_error(cls, label):
        msg = ("reference to undefined label: %s" % label)
        return DefinitionError(msg)

    create_unregistered_label_error = classmethod(
        create_unregistered_label_error)


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

    def _matches_args(self, call):
        for i, constraint in enumerate(self._arg_constraints):
            if not constraint.eval(call.args[i]):
                return False
        return True

    def _matches_kwargs(self, call):
        for kw, constraint in self._kwarg_constraints.iteritems():
            if (not call.kwargs.has_key(kw) or
                not constraint.eval(call.kwargs[kw])):
                return False
        return True

    def matches(self, call):
        return (self._matches_args(call) and
                self._matches_kwargs(call))

    
class LeastArgumentsMatcher(AbstractArgumentsMatcher):

    def _no_explicit_constraints_str(self):
        return "..."

    def _matches_args(self, call):
        if len(self._arg_constraints) > len(call.args):
            return False
        return AbstractArgumentsMatcher._matches_args(self, call)


class AllArgumentsMatcher(AbstractArgumentsMatcher):

    def _no_explicit_constraints_str(self):
        return ""

    def _matches_args(self, call):
        if len(self._arg_constraints) != len(call.args):
            return False
        return AbstractArgumentsMatcher._matches_args(self, call)

    def _matches_kwargs(self, call):
        for call_kw in call.kwargs.iterkeys():
            if call_kw not in self._kwarg_constraints:
                return False
        return AbstractArgumentsMatcher._matches_kwargs(self, call)


class MethodMatcher(object):

    def __init__(self, name):
        self._name = name
        
    def __str__(self):
         return self._name

    def matches(self, call):
        return call.name == self._name


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
        
    def register(self, label):
        self._registered[label] = True

    def is_registered(self, label):
        return self._registered.has_key(label)
        
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


class CallMocker(object):
    
    def __init__(self, call_matcher):
        self._call_matcher = call_matcher
        self._method_matcher = None
        self._arguments_matcher = LeastArgumentsMatcher()
        self._action = is_void()
        self._label = None
        self._explicit_label = None
        self._label_matcher = None

    def is_satisfied(self):
        return self._call_matcher.is_satisfied()

    def invoke(self):
        InvocationLog.instance().invoked(self._label)
        self._call_matcher.invoke()
        return self._action.invoke()
    
    def is_void(self):
        self._action = is_void()
        return self
    
    def matchers_str(self):
        suffix = [""]
        if self._explicit_label:
            suffix.append("label(%s)" % repr(self._label))
        if self._label_matcher is not None:
            suffix.append(str(self._label_matcher))
        return "%s %s(%s)%s" % (self._call_matcher, self._method_matcher,
                                self._arguments_matcher, ".".join(suffix))
    
    def matches(self, call):
        return (self._call_matcher.matches() and
                self._method_matcher.matches(call) and
                self._arguments_matcher.matches(call) and
                (self._label_matcher is None or self._label_matcher.matches()))

    def _set_label(self, label, explicit):
        self._label = label
        self._explicit_label = explicit
        InvocationLog.instance().register(label)
        
    def method(self, name):
        self._set_label(name, False)
        self._method_matcher = MethodMatcher(name)
        return self

    def will(self, action):
        self._action = action
        return self
    
    def with(self, *arg_constraints, **kwarg_constraints):
        self._arguments_matcher = AllArgumentsMatcher(arg_constraints,
                                                      kwarg_constraints)
        return self

    def with_at_least(self, *arg_constraints, **kwarg_constraints):
        self._arguments_matcher = LeastArgumentsMatcher(arg_constraints,
                                                        kwarg_constraints)
        return self

    def no_args(self):
        self._arguments_matcher = AllArgumentsMatcher()

    def label(self, label_str):
        self._set_label(label_str, True)
        return self

    def after(self, label):
        self._label_matcher = AfterLabelMatcher(label,
                                                InvocationLog.instance())
        return self


class MockCall(object):

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
        return self._mock.method_called(MockCall(self._name, args, kwargs))


class Proxy(object):

    def __init__(self, mock):
        self._mock = mock

    def __getattr__(self, name):
        return MockedMethod(name, self._mock)


class InvokeConflictError(Exception):
    pass


class Mock(object):

    def __init__(self):
        self._expected_mockers = []
        self._proxy = Proxy(self)

    def _unsatisfied_mockers(self):
        unsatisfied = []
        for mocker in self._expected_mockers:
            if not mocker.is_satisfied():
                unsatisfied.append(mocker)
        return unsatisfied

    def _unmatched_method_called(self, call):
        unsatisfied_mockers = self._unsatisfied_mockers()
        raise MatchError.create_unexpected_error(call, unsatisfied_mockers)
        
    def method_called(self, call):
        matching_mocker = None
        for mocker in self._expected_mockers:
            if mocker.matches(call):
                try:
                    return mocker.invoke()
                except InvokeConflictError:
                    raise MatchError.create_conflict_error(call, mocker)
        self._unmatched_method_called(call)

    def expect(self, mocker=None):
        if mocker is None:
            mocker = once()
        self._expected_mockers.insert(0, mocker)
        return mocker

    def proxy(self):
        return self._proxy
    
    def verify(self):
        unsatisfied = self._unsatisfied_mockers()
        if len(unsatisfied) > 0:
            raise VerificationError.create_unsatisfied_error(unsatisfied)


class MockTestCase(unittest.TestCase):

    def setUp(self):
        InvocationLog.instance().clear()


##############################################################################
# Mocked method actions
############################################################################## 

class return_value(object):

    def __init__(self, value):
        self._value = value

    def invoke(self):
        return self._value


def is_void():
    return return_value(None)


class throw_exception(object):

    def __init__(self, exception):
        self._exception = exception

    def invoke(self):
        raise self._exception


##############################################################################
# Call match constraints
############################################################################## 

class CallMatcher(object):

    def __init__(self):
        self._invoked = False

    def invoke(self):
        self._invoked = True

    
class OnceMatcher(CallMatcher):

    def __str__(self):
        return "once"
    
    def is_satisfied(self):
        return self._invoked

    def matches(self):
        return not self._invoked


def once():
    return CallMocker(OnceMatcher())


class AtLeastOnceMatcher(CallMatcher):

    def __str__(self):
        return "at least once"

    def is_satisfied(self):
        return self._invoked

    def matches(self):
        return True


def at_least_once():
    return CallMocker(AtLeastOnceMatcher())


class NotCalledMatcher(CallMatcher):

    def __str__(self):
        return "not called"

    def invoke(self):
        CallMatcher.invoke(self)
        raise InvokeConflictError

    def is_satisfied(self):
        return not self._invoked
        
    def matches(self):
        return True


def not_called():
    return CallMocker(NotCalledMatcher())


##############################################################################
# Argument constraints
############################################################################## 

class eq(object):

    def __init__(self, expected):
        self._expected = expected

    def __repr__(self):
        return "%s.eq(%s)" % (__name__, repr(self._expected))

    def eval(self, arg):
        return self._expected == arg


class same(object):

    def __init__(self, expected):
        self._expected = expected

    def __repr__(self):
        return "%s.same(%s)" % (__name__, repr(self._expected))

    def eval(self, arg):
        return self._expected is arg


class string_contains(object):

    def __init__(self, expected):
        self._expected = expected

    def __repr__(self):
        return "%s.string_contains(%s)" % (__name__, repr(self._expected))

    def eval(self, arg):
        return (arg is not None) and (arg.find(self._expected) != -1)


class functor(object):

    def __init__(self, boolean_functor):
        self._boolean_functor = boolean_functor

    def __repr__(self):
        return "%s.functor(%s)" % (__name__, repr(self._boolean_functor))

    def eval(self, arg):
        return self._boolean_functor(arg)

