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


class VerificationError(Error):
    pass


class MatchError(Error):
    pass


class AnyArgumentsMatcher(object):

    def __str__(self):
        return "..."

    def matches(self, call):
        return True


class AbstractArgumentsMatcher(object):

    def __init__(self, arg_constraints=(), kwarg_constraints={}):
        self._arg_constraints = arg_constraints
        self._kwarg_constraints = kwarg_constraints
        keywords = self._kwarg_constraints.keys()
        keywords.sort()
        self._sorted_keywords = keywords

    def __str__(self):
        if (len(self._arg_constraints) == 0 and
            len(self._kwarg_constraints) == 0):
            return "..."
        else:
            arg_strs = [str(c) for c in self._arg_constraints]
            for kw in self._sorted_keywords:
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
            if not constraint.eval(call.kwargs[kw]):
                return False
        return True

    def matches(self, call):
        return (self._matches_args(call) and
                self._matches_kwargs(call))

    
class LeastArgumentsMatcher(AbstractArgumentsMatcher):
    
    def _matches_args(self, call):
        if len(self._arg_constraints) > len(call.args):
            return False
        return AbstractArgumentsMatcher._matches_args(self, call)

    def _matches_kwargs(self, call):
        missing_kwargs = []
        for kw in self._kwarg_constraints.keys():
            if kw not in call.kwargs.keys():
                missing_kwargs.append(kw)
        if len(missing_kwargs) > 0:
            return False
        return AbstractArgumentsMatcher._matches_kwargs(self, call)


class AllArgumentsMatcher(AbstractArgumentsMatcher):

    def _matches_args(self, call):
        if len(self._arg_constraints) != len(call.args):
            return False
        return AbstractArgumentsMatcher._matches_args(self, call)

    def _matches_kwargs(self, call) :
        call_keys = call.kwargs.keys()
        call_keys.sort()
        if self._sorted_keywords != call_keys:
            return False
        return AbstractArgumentsMatcher._matches_kwargs(self, call)


class MethodMatcher(object):

    def __init__(self, name):
        self._name = name
        
    def __str__(self):
         return self._name

    def matches(self, call):
        return call.name == self._name


class CallMocker(object):

    def __init__(self):
        self._method_matcher = None
        self._arguments_matcher = AnyArgumentsMatcher()
        self._action = is_void()

    def invoke_action(self):
        return self._action.invoke()
    
    def is_void(self):
        self._action = is_void()
        return self
    
    def method_str(self):
        return "%s(%s)" % (self._method_matcher, self._arguments_matcher)
    
    def matches(self, call):
        return (self._method_matcher.matches(call) and
                self._arguments_matcher.matches(call))

    def method(self, name):
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


class MockCall(object):

    def __init__(self, name, args, kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        arg_strs = [repr(arg) for arg in self.args]
        for kw, arg in self.kwargs.iteritems():
            arg_strs.append("%s=%s" % (kw, repr(arg)))
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


class Mock(object):

    def __init__(self):
        self._expected_calls = []
        self._proxy = Proxy(self)

    def _expected_calls_str(self):
        uncalled_strs = [call_mocker.method_str()
                         for call_mocker in self._expected_calls]
        return ", ".join(uncalled_strs)
        
    def method_called(self, call):
        matching_mocker = None
        for call_mocker in self._expected_calls:
            if call_mocker.matches(call):
                self._expected_calls.remove(call_mocker)
                return call_mocker.invoke_action()
        else:
            if len(self._expected_calls) > 0:
                err_msg = ("unexpected call %s, expected call(s) %s" %
                           (call, self._expected_calls_str()))
            else:
                err_msg = ("unexpected call %s, no expected calls remaining" %
                           call)
            raise MatchError(err_msg)

    def expect(self):
        call_mocker = CallMocker()
        self._expected_calls.insert(0, call_mocker)
        return call_mocker

    def proxy(self):
        return self._proxy
    
    def verify(self):
        if len(self._expected_calls) > 0:
            raise VerificationError("expected method(s) %s uncalled" %
                                    self._expected_calls_str())


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
