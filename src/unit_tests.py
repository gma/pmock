import unittest

import pmock
import testsupport


class VerificationErrorTest(testsupport.ErrorMsgAssertsMixin,
                            unittest.TestCase):

    def test_create_unsatisfied(self):
        class Mocker:
            def __str__(self): return "matchers"
        error = pmock.VerificationError.create_unsatisfied_error([Mocker()])
        self.assertUnsatisfiedMsg(error.msg, ["matchers"])


class MatchErrorTest(testsupport.ErrorMsgAssertsMixin, unittest.TestCase):

    def test_create_unexpected(self):
        class MockInvocation:
            def __str__(self): return "call"
        class Mocker:
            def __str__(self): return "matchers"
        error = pmock.MatchError.create_unexpected_error(MockInvocation(),
                                                         [Mocker()])
        self.assertUnexpectedCallMsg(error.msg, "call", ["matchers"])

    def test_create_conflict(self):
        class MockInvocation:
            def __str__(self): return "call"
        class Mocker:
            def __str__(self): return "matchers"
        error = pmock.MatchError.create_conflict_error(MockInvocation(),
                                                       Mocker())
        self.assertConflictedCallMsg(error.msg, "call", "matchers")


class ArgumentsMatcherTestMixin(object):

    def __init__(self, matcher_class):
        self.matcher_class = matcher_class
    
    def test_matches_arguments(self):
        arg1 = []
        args_matcher = self.matcher_class((pmock.same(arg1),), {})
        self.assert_(
            args_matcher.matches(pmock.Invocation("snake", (arg1,), {})))

    def test_matches_keyword_arguments(self):
        arg2 = []
        args_matcher = self.matcher_class((), {"food": pmock.same(arg2)})
        invocation = pmock.Invocation("snake", (), {"food": arg2})
        self.assert_(args_matcher.matches(invocation))

    def test_matches_both_types_of_arguments(self):
        arg1 = []
        arg2 = []
        args_matcher = self.matcher_class((pmock.same(arg1),),
                                          {"food": pmock.same(arg2)})
        invocation = pmock.Invocation("snake", (arg1,), {"food": arg2})
        self.assert_(args_matcher.matches(invocation))

    def test_insufficient_arguments(self):
        args_matcher = self.matcher_class((pmock.eq("slither"),), {})
        self.assert_(
            not args_matcher.matches(pmock.Invocation("snake", (), {})))

    def test_insufficient_keyword_arguments(self):
        args_matcher = self.matcher_class((), {"food": pmock.eq("goat")})
        self.assert_(
            not args_matcher.matches(pmock.Invocation("snake", (), {})))

    def test_unmatched_argument(self):
        class UnmatchedConstraint:
            def eval(self, invocation): return False
        args_matcher = self.matcher_class((UnmatchedConstraint(),), {})
        invocation = pmock.Invocation("snake", ("slither",), {})
        self.assert_(not args_matcher.matches(invocation))

    def test_unmatched_keyword_argument(self):
        class UnmatchedConstraint:
            def eval(self, invocation): return False
        args_matcher = self.matcher_class((), {"food": UnmatchedConstraint()})
        invocation = pmock.Invocation("snake", (), {"food": "goat"})
        self.assert_(not args_matcher.matches(invocation))


class AllArgumentsMatcherTest(ArgumentsMatcherTestMixin, unittest.TestCase):

    def __init__(self, *args):
        ArgumentsMatcherTestMixin.__init__(self, pmock.AllArgumentsMatcher)
        unittest.TestCase.__init__(self, *args)        

    def test_extra_arguments(self):
        args_matcher = pmock.AllArgumentsMatcher((pmock.eq("slither"),), {})
        self.assert_(not args_matcher.matches(
            pmock.Invocation("snake", ("slither", "hiss"), {})))

    def test_extra_keyword_arguments(self):
        args_matcher = pmock.AllArgumentsMatcher((),
                                                 {"food": pmock.eq("goat")})
        self.assert_(not args_matcher.matches(
            pmock.Invocation("snake", (), {"food": "goat", "colour": "red"})))

    def test_no_arguments(self):
        args_matcher = pmock.AllArgumentsMatcher()
        self.assert_(args_matcher.matches(pmock.Invocation("snake", (), {})))
        self.assert_(
            not args_matcher.matches(pmock.Invocation("snake", ("hiss",), {})))
        self.assert_(not args_matcher.matches(
            pmock.Invocation("snake", (), {"food": "goat"})))

    def test_str(self):
        matcher = pmock.AllArgumentsMatcher((pmock.eq("slither"),),
                                            {"food": pmock.eq("goat")})
        self.assertEqual(str(matcher),
                         "(pmock.eq('slither'), food=pmock.eq('goat'))")

    def test_empty_str(self):
        self.assertEqual(str(pmock.AllArgumentsMatcher()), "()")


class LeastArgumentsMatcherTest(ArgumentsMatcherTestMixin, unittest.TestCase):

    def __init__(self, *args):
        ArgumentsMatcherTestMixin.__init__(self, pmock.LeastArgumentsMatcher)
        unittest.TestCase.__init__(self, *args)        
    
    def test_extra_arguments(self):
        args_matcher = pmock.LeastArgumentsMatcher((pmock.eq("slither"),), {})
        self.assert_(args_matcher.matches(
            pmock.Invocation("snake", ("slither", "hiss"), {})))

    def test_extra_keyword_arguments(self):
        args_matcher = pmock.LeastArgumentsMatcher((),
                                                 {"food": pmock.eq("goat")})
        self.assert_(args_matcher.matches(
            pmock.Invocation("snake", (), {"food": "goat", "colour": "red"})))

    def test_any_arguments(self):
        args_matcher = pmock.LeastArgumentsMatcher()
        self.assert_(args_matcher.matches(pmock.Invocation("snake", (), {})))
        self.assert_(
            args_matcher.matches(pmock.Invocation("snake", ("hiss",), {})))
        self.assert_(args_matcher.matches(
            pmock.Invocation("snake", ("constrict",), {"food": "goat"})))

    def test_str(self):
        matcher = pmock.LeastArgumentsMatcher((pmock.eq("slither"),),
                                              {"food": pmock.eq("goat")})
        self.assertEqual(str(matcher),
                         "(pmock.eq('slither'), food=pmock.eq('goat'), ...)")

    def test_empty_str(self):
        self.assertEqual(str(pmock.LeastArgumentsMatcher()), "(...)")


class InvocationMockerTest(testsupport.ErrorMsgAssertsMixin,
                           unittest.TestCase):

    class MockMatcher:
        def __init__(self, matches):
            self._matches = matches
        def matches(self, invocation):
            self.matches_invocation = invocation
            return self._matches
        def invoked(self, invocation):
            self.invoked_invocation = invocation
    
    def test_matches(self):
        mocker = pmock.InvocationMocker(self.MockMatcher(True))
        self.assert_(mocker.matches(pmock.Invocation("duck", (), {})))

    def test_unmatched(self):
        mocker = pmock.InvocationMocker(self.MockMatcher(False))
        self.assert_(not mocker.matches(pmock.Invocation("duck", (), {})))

    def test_added_matcher_unmatched(self):
        mocker = pmock.InvocationMocker(self.MockMatcher(True))
        mocker.add_matcher(self.MockMatcher(False))
        self.assert_(not mocker.matches(pmock.Invocation("duck", (), {})))

    def test_matches_passes_invocation_to_matcher(self):
        matcher = self.MockMatcher(True)
        mocker = pmock.InvocationMocker(matcher)
        invocation = pmock.Invocation("duck", (), {})
        mocker.matches(invocation)
        self.assertEqual(matcher.matches_invocation, invocation)

    def test_no_action_returns_none(self):
        mocker = pmock.InvocationMocker(self.MockMatcher(True))
        self.assert_(mocker.invoke(pmock.Invocation("duck", (), {})) is None)

    def test_invoke_returns_actions_value(self):
        class MockAction:
            def invoke(self, invocation): return 'value'
        mocker = pmock.InvocationMocker(self.MockMatcher(True))
        mocker.set_action(MockAction())
        self.assert_(mocker.invoke(pmock.Invocation("duck", (), {})) ==
                     'value')

    # TODO: questionable functionality - why is it needed
    def test_mocker_remembers_it_has_been_invoked(self):
        mocker = pmock.InvocationMocker(self.MockMatcher(True))
        self.assert_(not mocker.has_been_invoked())
        mocker.invoke(pmock.Invocation("duck", (), {}))
        self.assert_(mocker.has_been_invoked())

    def test_invoke_passes_invocation_to_matcher(self):
        matcher1 = self.MockMatcher(True)
        matcher2 = self.MockMatcher(True)
        mocker = pmock.InvocationMocker(matcher1)
        mocker.add_matcher(matcher2)
        invocation = pmock.Invocation("duck", (), {})
        mocker.invoke(invocation)
        self.assertEqual(matcher1.invoked_invocation, invocation)
        self.assertEqual(matcher2.invoked_invocation, invocation)

    def test_verify(self):
        class MockInvocationMatcher:
            def verify(self): self.verified = True
            def is_satisfied(self): return True
        matcher = MockInvocationMatcher()
        mocker = pmock.InvocationMocker(matcher)
        mocker.verify()
        self.assert_(matcher.verified)
        
    def test_satisfaction(self):
        class MockInvocationMatcher:
            def __init__(self, satisfied): self.satisfied = satisfied
            def is_satisfied(self): return self.satisfied
        mocker1 = pmock.InvocationMocker(MockInvocationMatcher(True))
        self.assert_(mocker1.is_satisfied())
        mocker2 = pmock.InvocationMocker(MockInvocationMatcher(False))
        self.assert_(not mocker2.is_satisfied())

    def test_str(self):
        class MockMatcher:
            def __init__(self, str_str): self._str = str_str
            def __str__(self): return self._str
        MockAction = MockMatcher
        mocker = pmock.InvocationMocker(MockMatcher("invocation_matcher"))
        mocker.add_matcher(MockMatcher("added_matcher1"))
        mocker.add_matcher(MockMatcher("added_matcher2"))
        mocker.set_action(MockAction("action"))
        self.assertEqual(str(mocker),
                         "invocation_matcher added_matcher1added_matcher2, "
                         "action")

    def test_implicitly_labelled_str(self):
        class MockMatcher:
            def __init__(self, str_str): self._str = str_str
            def __str__(self): return self._str
        mocker = pmock.InvocationMocker(MockMatcher("invocation_matcher"))
        mocker.add_matcher(MockMatcher("added_matcher1"))
        self.assertEqual(str(mocker), "invocation_matcher added_matcher1")

    def test_explicitly_labelled_str(self):
        class MockMatcher:
            def __init__(self, str_str): self._str = str_str
            def __str__(self): return self._str
        MockAction = MockMatcher
        mocker = pmock.InvocationMocker(MockMatcher("invocation_matcher"))
        mocker.add_matcher(MockMatcher("added_matcher1"))
        mocker.set_action(MockAction("action"))
        mocker.set_label("quack")
        self.assertEqual(str(mocker),
                         "invocation_matcher added_matcher1, action [quack]")


class MatchBuilderTest(testsupport.ErrorMsgAssertsMixin,
                       unittest.TestCase):

    def setUp(self):
        class MockInvocationMocker:
            def __init__(self):
                self.added_matcher = None
                self.label = None
                self.action = None
            def add_matcher(self, matcher):
                self.added_matcher = matcher
            def set_label(self, label):
                self.label = label
            def set_action(self, action):
                self.action = action
        self.mocker = MockInvocationMocker()
        self.invocation_log = pmock.InvocationLog()
        self.builder = pmock.MatchBuilder(self.mocker, self.invocation_log)
        
    def test_add_with_matcher(self):
        self.assert_(self.builder.with(pmock.eq("egg")) is not None)
        self.assert_(isinstance(self.mocker.added_matcher,
                                pmock.AllArgumentsMatcher))
        self.assert_(self.mocker.added_matcher.matches(
            pmock.Invocation(None, ("egg",), {})))

    def test_add_with_at_least_matcher(self):
        self.assert_(self.builder.with_at_least(pmock.eq("egg")) is not None)
        self.assert_(isinstance(self.mocker.added_matcher,
                                pmock.LeastArgumentsMatcher))
        self.assert_(self.mocker.added_matcher.matches(
            pmock.Invocation(None, ("egg", "feather"), {})))

    def test_add_no_args_matcher(self):
        self.assert_(self.builder.no_args() is not None)
        self.assertEqual(self.mocker.added_matcher, pmock.NO_ARGS_MATCHER)

    def test_add_any_args_matcher(self):
        self.assert_(self.builder.any_args() is not None)
        self.assertEqual(self.mocker.added_matcher, pmock.ANY_ARGS_MATCHER)

    def test_set_will_action(self):
        class MockAction: pass
        action = MockAction()
        self.assert_(self.builder.will(action) is not None)
        self.assertEqual(self.mocker.action, action)

    def test_set_label(self):
        self.assert_(self.builder.label("poultry") is not None)
        self.assertEqual(self.mocker.label, "poultry")
        self.assertEqual(self.invocation_log.get_registered("poultry"),
                         self.mocker)

    def test_set_duplicate_label(self):
        self.builder.label("poultry")
        try:
            self.builder.label("poultry")
            self.fail("mocker with duplicate labels should raise")
        except pmock.DefinitionError, err:
            self.assertDuplicateLabelMsg(err.msg, "poultry", str(self.mocker))
        
    def test_add_after_ordering(self):
        self.builder.label("rooster")
        self.assert_(self.builder.after("rooster") is not None)
        self.assert_(isinstance(self.mocker.added_matcher,
                                pmock.AfterLabelMatcher))

    def test_add_after_other_named_mock_ordering(self):
        other_mock = pmock.Mock("coup")
        other_mock.expects(pmock.OnceInvocationMatcher()).method("rooster")
        self.assert_(self.builder.after("rooster", other_mock) is not None)
        self.assert_(isinstance(self.mocker.added_matcher,
                                pmock.AfterLabelMatcher))
        self.assertEqual(str(self.mocker.added_matcher),
                         ".after('rooster' on mock 'coup')")

    def test_add_after_other_unnamed_mock_ordering(self):
        other_mock = pmock.Mock()
        other_mock.expects(pmock.OnceInvocationMatcher()).method("rooster")
        self.assert_(self.builder.after("rooster", other_mock) is not None)
        self.assert_(isinstance(self.mocker.added_matcher,
                                pmock.AfterLabelMatcher))
        self.assertEqual(str(self.mocker.added_matcher),
                         ".after('rooster' on mock %s)" % str(other_mock))


class NameAndDirectArgsBuilderTest(unittest.TestCase):

    def setUp(self):
        class MockInvocationMocker:
            def __init__(self):
                self.added_matchers = []
            def add_matcher(self, matcher):
                self.added_matchers.append(matcher)
        self.mocker = MockInvocationMocker()
        self.invocation_log = pmock.InvocationLog()
        self.builder = pmock.NameAndDirectArgsBuilder(self.mocker,
                                                      self.invocation_log)

    def test_add_method_matcher(self):
        self.assert_(self.builder.method("chicken") is not None)
        self.assert_(isinstance(self.mocker.added_matchers[0],
                                pmock.MethodMatcher))
        self.assert_(self.mocker.added_matchers[0].matches(
            pmock.Invocation("chicken", (), {})))
        self.assertEqual(self.invocation_log.get_registered("chicken"),
                         self.mocker)

    def test_add_direct_method_matcher(self):
        self.assert_(self.builder.chicken() is not None)
        self.assert_(isinstance(self.mocker.added_matchers[0],
                                pmock.MethodMatcher))
        self.assert_(self.mocker.added_matchers[0].matches(
            pmock.Invocation("chicken", (), {})))
        self.assert_(self.mocker.added_matchers[1].matches(
            pmock.Invocation("chicken", (), {})))
        self.assertEqual(self.invocation_log.get_registered("chicken"),
                         self.mocker)

    def test_add_direct_method_and_arg_matcher(self):
        self.assert_(self.builder.chicken(pmock.eq("egg")) is not None)
        self.assert_(isinstance(self.mocker.added_matchers[0],
                                pmock.MethodMatcher))
        self.assert_(self.mocker.added_matchers[0].matches(
            pmock.Invocation("chicken", (), {})))
        self.assert_(self.mocker.added_matchers[1].matches(
            pmock.Invocation("chicken", ("egg",), {})))
        self.assertEqual(self.invocation_log.get_registered("chicken"),
                         self.mocker)


class MethodMatcherTest(unittest.TestCase):

    def setUp(self):
        self.method_matcher = pmock.MethodMatcher("horse")

    def test_matches(self):
        self.assert_(
            self.method_matcher.matches(pmock.Invocation("horse", (), {})))

    def test_unmatched(self):
        self.assert_(
            not self.method_matcher.matches(pmock.Invocation("ass", (), {})))
 
    def test_str(self):
        self.assertEqual(str(self.method_matcher), "horse")


class InvocationLogTest(unittest.TestCase):

    def setUp(self):
        self.invocation_log = pmock.InvocationLog()

    def test_not_registered(self):
        self.assert_(not self.invocation_log.is_registered("racoon"))

    def test_registered(self):
        mocker = pmock.InvocationMocker(pmock.OnceInvocationMatcher())
        self.invocation_log.register("racoon", mocker)
        self.assert_(self.invocation_log.is_registered("racoon"))
        self.assertEqual(self.invocation_log.get_registered("racoon"), mocker)


class AfterLabelMatcherTest(testsupport.ErrorMsgAssertsMixin,
                            unittest.TestCase):

    def setUp(self):
        self.invocation_log = pmock.InvocationLog()
        self.mocker = pmock.InvocationMocker(pmock.OnceInvocationMatcher())
        self.invocation_log.register("weasel", self.mocker)
        self.matcher = pmock.AfterLabelMatcher("weasel", self.invocation_log)
        self.invocation = pmock.Invocation("stoat", (), {})
        
    def test_uninvoked_doesnt_match(self):
        self.assert_(not self.matcher.matches(self.invocation))

    def test_invoked_matches(self):
        self.mocker.invoke(self.invocation)
        self.assert_(self.matcher.matches(self.invocation))

    def test_str(self):
        self.assertEqual(str(self.matcher), ".after('weasel')")


class AfterLabelMatcherAdditionalTest(testsupport.ErrorMsgAssertsMixin,
                                      unittest.TestCase):

    def test_unregistered_label(self):
        try:
            invocation_log = pmock.InvocationLog()
            matcher = pmock.AfterLabelMatcher("stoat", invocation_log)
            self.fail("should raise because label isn't registered")
        except pmock.DefinitionError, err:
            self.assertUndefinedLabelMsg(err.msg, "stoat")

    def test_str_with_additional_description(self):
        invocation_log = pmock.InvocationLog()
        mocker = pmock.InvocationMocker(pmock.OnceInvocationMatcher())
        invocation_log.register("weasel", mocker)
        matcher = pmock.AfterLabelMatcher("weasel", invocation_log, " extra")
        self.assertEqual(str(matcher), ".after('weasel' extra)")


class InvocationTest(unittest.TestCase):

    def test_no_args_str(self):
        self.assertEqual(str(pmock.Invocation("penguin", (), {})), "penguin()")

    def test_arg_str(self):
        self.assertEqual(str(pmock.Invocation("penguin", ("swim",), {})),
                         "penguin('swim')")

    def test_kwarg_str(self):
        self.assertEqual(
            str(pmock.Invocation("penguin", (), {"food": "fish"})),
            "penguin(food='fish')")

    def test_args_str(self):
        self.assertEqual(
            str(pmock.Invocation("penguin", ("swim", "waddle"),
                                 {"home": "iceberg", "food": "fish"})),
            "penguin('swim', 'waddle', food='fish', home='iceberg')")


class ProxyTest(unittest.TestCase):

    def test_invoke(self):
        class Mock:
            def invoke(self, invocation):
                self.invocation = invocation
        mock = Mock()
        proxy = pmock.Proxy(mock)
        proxy.camel("walk", desert="gobi")
        self.assertEqual(mock.invocation.name, "camel")
        self.assertEqual(mock.invocation.args, ("walk",))
        self.assertEqual(mock.invocation.kwargs, {"desert": "gobi"})        


class MockTest(testsupport.ErrorMsgAssertsMixin, unittest.TestCase):

    def test_one_to_one_proxy(self):
        mock = pmock.Mock()
        self.assert_(mock.proxy() is mock.proxy())

    def test_unmatched_invocation(self):
        mock = pmock.Mock()
        try:
            mock.invoke(pmock.Invocation("wolf", (), {}))
            fail("should have raised due to unexpected method call")
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(
                err.msg,
                str(pmock.Invocation("wolf", (), {})),
                [])

    def test_matching_invokable(self):
        class Invokable:
            def matches(self, invocation):
                self.matches_invocation = invocation
                return True
            def invoke(self, invocation):
                self.invoke_invocation = invocation
        invokable = Invokable()
        mock = pmock.Mock()
        mock.add_invokable(invokable)
        invocation = pmock.Invocation("wolf", (), {})
        mock.invoke(invocation)
        self.assertEqual(invokable.matches_invocation, invocation)
        self.assertEqual(invokable.invoke_invocation, invocation)
        
    def test_lifo_matching_order(self):
        class Invokable:
            current_attempt_number = 1
            def __init__(self, matches):
                self._matches = matches
                self.attempt_number = None
                self.invoked = False
            def matches(self, invocation):
                self.attempt_number = Invokable.current_attempt_number
                Invokable.current_attempt_number += 1
                return self._matches
            def invoke(self, invocation):
                self.invoked = True
        invokable1 = Invokable(False)
        invokable2 = Invokable(True)
        invokable3 = Invokable(False)
        mock = pmock.Mock()
        mock.add_invokable(invokable1)
        mock.add_invokable(invokable2)
        mock.add_invokable(invokable3)
        mock.invoke(pmock.Invocation("wolf", (), {}))
        self.assert_(invokable1.attempt_number is None)
        self.assert_(not invokable1.invoked)
        self.assertEqual(invokable2.attempt_number, 2)
        self.assert_(invokable2.invoked)
        self.assertEqual(invokable3.attempt_number, 1)
        self.assert_(not invokable3.invoked)

    def test_verify(self):
        class Invokable:
            def verify(self): self.verified = True
            def is_satisfied(self): return True
        invokable = Invokable()
        mock = pmock.Mock()
        mock.add_invokable(invokable)
        mock.verify()
        self.assert_(invokable.verified)
        
    def test_unsatisfied_invokable(self):
        class Invokable:
            def verify(self): pass
            def is_satisfied(self): return False
            def __str__(self): return "unsatisfied"
        mock = pmock.Mock()
        mock.add_invokable(Invokable())
        try:
            mock.verify()
            fail("should have raised due to unsatisfied invokable")
        except pmock.VerificationError, err:
            self.assertUnsatisfiedMsg(err.msg, ["unsatisfied"])

    def test_satisfied_invokable(self):
        class Invokable:
            def verify(self): pass
            def is_satisfied(self): return True
        mock = pmock.Mock()
        mock.add_invokable(Invokable())
        mock.verify()

    def test_conflicting_invokable(self):
        class Invokable:
            def matches(self, invocation): return True
            def invoke(self, invocation): raise pmock.InvokeConflictError
            def __str__(self): return "conflicted"
        mock = pmock.Mock()
        mock.add_invokable(Invokable())
        try:
            mock.invoke(pmock.Invocation("wolf", (), {}))
            fail("should have raised due to conflicting invokable")
        except pmock.MatchError, err:
            self.assertConflictedCallMsg(
                err.msg,
                str(pmock.Invocation("wolf", (), {})),
                "conflicted")

    def test_expects(self):
        mock = pmock.Mock()
        mock.expects(pmock.OnceInvocationMatcher()).method("foo")
        self.assert_(mock._invocation_log.is_registered("foo"))
        self.assertRaises(pmock.VerificationError, mock.verify)

    def test_stubs(self):
        mock = pmock.Mock()
        mock.stubs().method("foo")
        self.assert_(mock._invocation_log.is_registered("foo"))
        mock.verify()

    def test_unnamed(self):
        mock = pmock.Mock()
        self.assertEqual(mock.get_name(), None)

    def test_name(self):
        mock = pmock.Mock("white fang")
        self.assertEqual(mock.get_name(), "white fang")

    def test_invoke_directly(self):
        class Invokable:
            def matches(self, invocation):
                self.invocation = invocation
                return True
            def invoke(self, invocation): pass
        mock = pmock.Mock()
        invokable = Invokable()
        mock.add_invokable(invokable)
        mock.howl(under='moon')
        self.assert_(invokable.invocation.name, "howl")
        self.assert_(invokable.invocation.kwargs['under'], "moon")


##############################################################################
# Mocked method actions
############################################################################## 

class ReturnValueTest(unittest.TestCase):

    def setUp(self):
        self.action = pmock.ReturnValueAction("owl")
        
    def test_invoke(self):
        self.assertEqual(self.action.invoke(pmock.Invocation("hoot", (), {})),
                         "owl")

    def test_str(self):
        self.assertEqual(str(self.action), "returns 'owl'")


class RaiseExceptionAction(unittest.TestCase):

    def setUp(self):
        self.exception = RuntimeError("owl")
        self.action = pmock.RaiseExceptionAction(self.exception)
        
    def test_invoke(self):
        try:
            self.action.invoke(pmock.Invocation("hoot", (), {}))
            fail("expected exception to be raised")
        except RuntimeError, err:
            self.assertEqual(err, self.exception)

    def test_str(self):
        self.assertEqual(str(self.action), "raises %s" % self.exception)


##############################################################################
# Invocation matchers
############################################################################## 

class OnceInvocationMatcherTest(unittest.TestCase):

    def setUp(self):
        self.matcher = pmock.OnceInvocationMatcher()
        
    def test_uninvoked_matches(self):
        self.assert_(self.matcher.matches(pmock.Invocation("worm", (), {})))

    def test_invoked_doesnt_match(self):
        self.matcher.invoked(pmock.Invocation("worm", (), {}))
        self.assert_(
        not self.matcher.matches(pmock.Invocation("snake", (), {})))

    def test_uninvoked_is_unsatisfied(self):
        self.assert_(not self.matcher.is_satisfied())

    def test_invoked_is_satisfied(self):
        self.matcher.invoked(pmock.Invocation("worm", (), {}))
        self.assert_(self.matcher.is_satisfied())

    def test_str(self):
        self.assert_(str(self.matcher), "once")
        

class AtLeastOnceInvocationMatcherTest(unittest.TestCase):

    def setUp(self):
        self.matcher = pmock.AtLeastOnceInvocationMatcher()
        
    def test_uninvoked_matches(self):
        self.assert_(self.matcher.matches(pmock.Invocation("worm", (), {})))

    def test_invoked_matches(self):
        self.matcher.invoked(pmock.Invocation("worm", (), {}))
        self.assert_(self.matcher.matches(pmock.Invocation("snake", (), {})))

    def test_uninvoked_is_unsatisfied(self):
        self.assert_(not self.matcher.is_satisfied())

    def test_invoked_is_satisfied(self):
        self.matcher.invoked(pmock.Invocation("worm", (), {}))
        self.assert_(self.matcher.is_satisfied())

    def test_str(self):
        self.assert_(str(self.matcher), "at least once")


class NotCalledInvocationMatcherTest(unittest.TestCase):

    def setUp(self):
        self.matcher = pmock.NotCalledInvocationMatcher()
        
    def test_uninvoked_matches(self):
        self.assert_(self.matcher.matches(pmock.Invocation("worm", (), {})))

    def test_invoke_raises(self):
        self.assertRaises(pmock.InvokeConflictError,
                          self.matcher.invoked,
                          pmock.Invocation("worm", (), {}))

    def test_uninvoked_is_satisfied(self):
        self.assert_(self.matcher.is_satisfied())

    def test_invoked_is_unsatisfied(self):
        try:
            self.matcher.invoked(pmock.Invocation("worm", (), {}))
            fail()
        except pmock.InvokeConflictError:
            self.assert_(not self.matcher.is_satisfied())

    def test_str(self):
        self.assert_(str(self.matcher), "not called")


class StubInvocationMatcherTest(unittest.TestCase):

    def setUp(self):
        self.matcher = pmock.StubInvocationMatcher()
        
    def test_uninvoked_matches(self):
        self.assert_(self.matcher.matches(pmock.Invocation("worm", (), {})))

    def test_uninvoked_is_satisfied(self):
        self.assert_(self.matcher.is_satisfied())

    def test_invoked_is_satisfied(self):
        self.matcher.invoked(pmock.Invocation("worm", (), {}))
        self.assert_(self.matcher.is_satisfied())


##############################################################################
# Argument constraints
############################################################################## 

class EqConstraintTest(unittest.TestCase):

    def test_match(self):
        self.assert_(pmock.EqConstraint("mouse").eval("mouse"))

    def test_umatched(self):
        self.assert_(not pmock.EqConstraint("mouse").eval("rat"))
        
    def test_str(self):
        self.assertEqual(str(pmock.EqConstraint("mouse")),
                         "pmock.eq('mouse')")
        

class SameConstraintTest(unittest.TestCase):

    def test_match(self):
        mutable = ["mouse"]
        self.assert_(pmock.SameConstraint(mutable).eval(mutable))

    def test_umatched(self):
        self.assert_(not pmock.SameConstraint(["mouse"]).eval(["mouse"]))
        
    def test_str(self):
        self.assertEqual(str(pmock.SameConstraint(["mouse"])),
                         "pmock.same(['mouse'])")


class StringContainsConstraintTest(unittest.TestCase):

    def test_matches_same_string(self):
        self.assert_(pmock.StringContainsConstraint("mouse").eval("mouse"))
        
    def test_matches_substring(self):
        self.assert_(pmock.StringContainsConstraint("mo").eval("mouse"))
        self.assert_(pmock.StringContainsConstraint("ou").eval("mouse"))
        self.assert_(pmock.StringContainsConstraint("se").eval("mouse"))
        self.assert_(pmock.StringContainsConstraint("").eval("mouse"))
        
    def test_umatched(self):
        self.assert_(not pmock.StringContainsConstraint("mouse").eval("rat"))
        self.assert_(not pmock.StringContainsConstraint("mouse").eval(None))

    def test_str(self):
        self.assertEqual(str(pmock.StringContainsConstraint("mouse")),
                         "pmock.string_contains('mouse')")


class FunctorConstraintTest(unittest.TestCase):

    def test_matches(self):
        self.assert_(pmock.FunctorConstraint(lambda arg: True).eval("mouse"))
        
    def test_umatched(self):
        self.assert_(
            not pmock.FunctorConstraint(lambda arg: False).eval("mouse"))

    def test_str(self):
        lambda_ = lambda arg: False
        self.assertEqual(str(pmock.FunctorConstraint(lambda_)),
                         "pmock.functor(%s)" % repr(lambda_))


if __name__ == '__main__':
    unittest.main()
