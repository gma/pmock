import unittest

import pmock
import testsupport


class VerificationErrorTest(testsupport.ErrorMsgAssertsMixin,
                            unittest.TestCase):

    def test_create_unsatisfied(self):
        class Mocker:
            def matchers_str(self): return "matchers"
        error = pmock.VerificationError.create_unsatisfied_error([Mocker()])
        self.assertUnsatisfiedMsg(error.msg, ["matchers"])


class MatchErrorTest(testsupport.ErrorMsgAssertsMixin, unittest.TestCase):

    def test_create_unexpected(self):
        class MockInvocation:
            def __str__(self): return "call"
        class Mocker:
            def matchers_str(self): return "matchers"
        error = pmock.MatchError.create_unexpected_error(MockInvocation(),
                                                         [Mocker()])
        self.assertUnexpectedCallMsg(error.msg, "call", ["matchers"])

    def test_create_conflict(self):
        class MockInvocation:
            def __str__(self): return "call"
        class Mocker:
            def matchers_str(self): return "matchers"
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
            args_matcher.matches(pmock.MockInvocation("snake", (arg1,), {})))

    def test_matches_keyword_arguments(self):
        arg2 = []
        args_matcher = self.matcher_class((), {"food": pmock.same(arg2)})
        invocation = pmock.MockInvocation("snake", (), {"food": arg2})
        self.assert_(args_matcher.matches(invocation))

    def test_matches_both_types_of_arguments(self):
        arg1 = []
        arg2 = []
        args_matcher = self.matcher_class((pmock.same(arg1),),
                                          {"food": pmock.same(arg2)})
        invocation = pmock.MockInvocation("snake", (arg1,), {"food": arg2})
        self.assert_(args_matcher.matches(invocation))

    def test_insufficient_arguments(self):
        args_matcher = self.matcher_class((pmock.eq("slither"),), {})
        self.assert_(
            not args_matcher.matches(pmock.MockInvocation("snake", (), {})))

    def test_insufficient_keyword_arguments(self):
        args_matcher = self.matcher_class((), {"food": pmock.eq("goat")})
        self.assert_(not args_matcher.matches(
            pmock.MockInvocation("snake", (), {})))

    def test_unmatched_argument(self):
        class UnmatchedConstraint:
            def eval(self, invocation): return False
        args_matcher = self.matcher_class((UnmatchedConstraint(),), {})
        invocation = pmock.MockInvocation("snake", ("slither",), {})
        self.assert_(not args_matcher.matches(invocation))

    def test_unmatched_keyword_argument(self):
        class UnmatchedConstraint:
            def eval(self, invocation): return False
        args_matcher = self.matcher_class((), {"food": UnmatchedConstraint()})
        invocation = pmock.MockInvocation("snake", (), {"food": "goat"})
        self.assert_(not args_matcher.matches(invocation))


class AllArgumentsMatcherTest(ArgumentsMatcherTestMixin, unittest.TestCase):

    def __init__(self, *args):
        ArgumentsMatcherTestMixin.__init__(self, pmock.AllArgumentsMatcher)
        unittest.TestCase.__init__(self, *args)        

    def test_extra_arguments(self):
        args_matcher = pmock.AllArgumentsMatcher((pmock.eq("slither"),), {})
        self.assert_(not args_matcher.matches(
            pmock.MockInvocation("snake", ("slither", "hiss"), {})))

    def test_extra_keyword_arguments(self):
        args_matcher = pmock.AllArgumentsMatcher((),
                                                 {"food": pmock.eq("goat")})
        self.assert_(not args_matcher.matches(
            pmock.MockInvocation("snake", (),
                                 {"food": "goat", "colour": "brown"})))

    def test_no_arguments(self):
        args_matcher = pmock.AllArgumentsMatcher()
        self.assert_(args_matcher.matches(
            pmock.MockInvocation("snake", (), {})))
        self.assert_(not args_matcher.matches(
            pmock.MockInvocation("snake", ("hiss",), {})))
        self.assert_(not args_matcher.matches(
            pmock.MockInvocation("snake", (), {"food": "goat"})))

    def test_str(self):
        self.assertEqual(str(pmock.AllArgumentsMatcher()), "")


class LeastArgumentsMatcherTest(ArgumentsMatcherTestMixin, unittest.TestCase):

    def __init__(self, *args):
        ArgumentsMatcherTestMixin.__init__(self, pmock.LeastArgumentsMatcher)
        unittest.TestCase.__init__(self, *args)        
    
    def test_extra_arguments(self):
        args_matcher = pmock.LeastArgumentsMatcher((pmock.eq("slither"),), {})
        self.assert_(args_matcher.matches(
            pmock.MockInvocation("snake", ("slither", "hiss"), {})))

    def test_extra_keyword_arguments(self):
        args_matcher = pmock.LeastArgumentsMatcher((),
                                                 {"food": pmock.eq("goat")})
        self.assert_(args_matcher.matches(
            pmock.MockInvocation("snake", (),
                                 {"food": "goat", "colour": "brown"})))

    def test_any_arguments(self):
        args_matcher = pmock.LeastArgumentsMatcher()
        self.assert_(args_matcher.matches(
            pmock.MockInvocation("snake", (), {})))
        self.assert_(args_matcher.matches(
            pmock.MockInvocation("snake", ("hiss",), {})))
        self.assert_(args_matcher.matches(
            pmock.MockInvocation("snake", ("constrict",), {"food": "goat"})))

    def test_str(self):
        self.assertEqual(str(pmock.LeastArgumentsMatcher()), "...")


class InvocationMockerTest(testsupport.ErrorMsgAssertsMixin,
                           unittest.TestCase):

    def test_matches(self):
        class MockInvocationMatcher:
            def matches(self): return True
        mocker = pmock.InvocationMocker(MockInvocationMatcher())
        mocker.method("skunk").with(pmock.eq("spray"))
        self.assert_(mocker.matches(
            pmock.MockInvocation("skunk", ("spray",), {})))

    def test_matches_with_at_least(self):
        class MockInvocationMatcher:
            def matches(self): return True        
        mocker = pmock.InvocationMocker(MockInvocationMatcher())
        mocker.method("skunk").with_at_least(pmock.eq("spray"))
        self.assert_(mocker.matches(
            pmock.MockInvocation("skunk", ("spray", "forage"), {})))

    def test_matches_with_no_args(self):
        class MockInvocationMatcher:
            def matches(self): return True        
        mocker = pmock.InvocationMocker(MockInvocationMatcher())
        mocker.method("skunk").no_args()
        self.assert_(mocker.matches(pmock.MockInvocation("skunk", (), {})))
        self.assert_(
            not mocker.matches(pmock.MockInvocation("skunk", ("spray",), {})))
        self.assert_(not mocker.matches(
            pmock.MockInvocation("skunk", (), {"smell":"bad"})))

    def test_unmatched_invocation_matcher(self):
        class MockInvocationMatcher:
            def matches(self): return False
        mocker = pmock.InvocationMocker(MockInvocationMatcher())
        mocker.method("skunk").with(pmock.eq("spray"))
        self.assert_(
            not mocker.matches(pmock.MockInvocation("skunk", ("spray",), {})))

    def test_unmatched_method(self):
        class MockInvocationMatcher:
            def matches(self): return True
        mocker = pmock.InvocationMocker(MockInvocationMatcher())
        mocker.method("skunk").with(pmock.eq("spray"))
        self.assert_(
            not mocker.matches(pmock.MockInvocation("ferret", ("spray",), {})))

    def test_unmatched_args(self):
        class MockInvocationMatcher:
            def matches(self): return True
        mocker = pmock.InvocationMocker(MockInvocationMatcher())
        mocker.method("skunk").with(pmock.eq("spray"))
        self.assert_(
            not mocker.matches(pmock.MockInvocation("skunk", ("fly",), {})))

    def test_is_void(self):
        class MockInvocationMatcher:
            def invoke(self): pass
            def matches(self): return True
        mocker = pmock.InvocationMocker(MockInvocationMatcher())
        mocker.method("skunk").is_void()
        self.assert_(mocker.invoke() is None)
        
    def test_invocation(self):
        class MockInvocable:
            def __init__(self): self.invoked = False
            def invoke(self): self.invoked = True
        mock_invocation_matcher = MockInvocable()
        mock_action = MockInvocable()
        mocker = pmock.InvocationMocker(mock_invocation_matcher)
        mocker.will(mock_action)
        mocker.invoke()
        self.assert_(mock_invocation_matcher.invoked)
        self.assert_(mock_action.invoked)
        
    def test_str(self):
        mocker = pmock.InvocationMocker(pmock.OnceInvocationMatcher())
        mocker.method("skunk")
        self.assertEqual(mocker.matchers_str(),
                         "%s skunk(%s)" % (pmock.OnceInvocationMatcher(),
                                           pmock.LeastArgumentsMatcher()))

    def test_labelled_str(self):
        pmock.InvocationLog.instance().clear()
        mocker = pmock.InvocationMocker(pmock.OnceInvocationMatcher())
        mocker.method("skunk").label("smelly")
        self.assertEqual(mocker.matchers_str(),
                         "%s skunk(%s).label('smelly')" %
                         (pmock.OnceInvocationMatcher(),
                          pmock.LeastArgumentsMatcher()))

    def test_after_str(self):
        invocation_log = pmock.InvocationLog.instance()
        invocation_log.clear()
        invocation_log.register("smelly", pmock.InvocationMocker(
            pmock.OnceInvocationMatcher()))
        mocker = pmock.InvocationMocker(pmock.OnceInvocationMatcher())
        mocker.method("skunk").after("smelly")
        self.assertEqual(mocker.matchers_str(),
                         "%s skunk(%s).%s" %
                         (pmock.OnceInvocationMatcher(),
                          pmock.LeastArgumentsMatcher(),
                          pmock.AfterLabelMatcher("smelly", invocation_log)))

    def test_satisfaction(self):
        class MockInvocationMatcher:
            def __init__(self, satisfied): self.satisfied = satisfied
            def is_satisfied(self): return self.satisfied
        mocker1 = pmock.InvocationMocker(MockInvocationMatcher(True))
        self.assert_(mocker1.is_satisfied())
        mocker2 = pmock.InvocationMocker(MockInvocationMatcher(False))
        self.assert_(not mocker2.is_satisfied())

    def test_invoking_makes_after_match(self):
        pmock.InvocationLog.instance().clear()
        mocker1 = pmock.InvocationMocker(
            pmock.OnceInvocationMatcher()).method("skunk").label("skunk call")
        mocker2 = pmock.InvocationMocker(
            pmock.OnceInvocationMatcher()).method("smell").after("skunk call")
        self.assert_(not mocker2.matches(
            pmock.MockInvocation("smell", (), {})))
        mocker1.invoke()
        self.assert_(mocker2.matches(pmock.MockInvocation("smell", (), {})))

    def test_duplicate_label_raises(self):
        pmock.InvocationLog.instance().clear()
        mocker1 = pmock.InvocationMocker(
            pmock.OnceInvocationMatcher()).method("skunk").label("skunk1")
        try:
            mocker2 = pmock.InvocationMocker(
                pmock.OnceInvocationMatcher()).method("skunk").label("skunk1")
            self.fail("creating mocker with duplicate label should raise")
        except pmock.DefinitionError, err:
            self.assertDuplicateLabelMsg(err.msg, "skunk1",
                                         "once skunk(...).label('skunk1')")


class MethodMatcherTest(unittest.TestCase):

    def setUp(self):
        self.method_matcher = pmock.MethodMatcher("horse")

    def test_matches(self):
        self.assert_(
            self.method_matcher.matches(pmock.MockInvocation("horse", (), {})))

    def test_unmatched(self):
        self.assert_(not self.method_matcher.matches(
            pmock.MockInvocation("donkey", (), {})))
 
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

    def test_has_not_been_invoked(self):
        self.assert_(not self.invocation_log.has_been_invoked("racoon"))

    def test_has_been_invoked(self):
        self.invocation_log.invoked("racoon")
        self.assert_(self.invocation_log.has_been_invoked("racoon"))

    def test_reset(self):
        self.invocation_log.register("racoon", pmock.InvocationMocker(
            pmock.OnceInvocationMatcher()))
        self.invocation_log.invoked("racoon")
        self.invocation_log.clear()
        self.assert_(not self.invocation_log.has_been_invoked("racoon"))
        self.assert_(not self.invocation_log.is_registered("racoon"))

    def test_singleton(self):
        self.assert_(pmock.InvocationLog.instance() is
                     pmock.InvocationLog.instance())


class AfterLabelMatcherTest(testsupport.ErrorMsgAssertsMixin,
                            unittest.TestCase):

    def setUp(self):
        self.invocation_log = pmock.InvocationLog()
        mocker = pmock.InvocationMocker(pmock.OnceInvocationMatcher())
        self.invocation_log.register("weasel", mocker)
        self.matcher = pmock.AfterLabelMatcher("weasel", self.invocation_log)
        
    def test_uninvoked_doesnt_match(self):
        self.assert_(not self.matcher.matches())

    def test_invoked_matches(self):
        self.invocation_log.invoked("weasel")
        self.assert_(self.matcher.matches())

    def test_str(self):
        self.assertEqual(str(self.matcher), "after('weasel')")

    def test_unregistered_label(self):
        try:
            self.matcher = pmock.AfterLabelMatcher("stoat",
                                                   self.invocation_log)
            self.fail("should raise because label isn't registered")
        except pmock.DefinitionError, err:
            self.assertUndefinedLabelMsg(err.msg, "stoat")


class MockInvocationTest(unittest.TestCase):

    def test_no_args_str(self):
        self.assertEqual(str(pmock.MockInvocation("penguin", (), {})),
                         "penguin()")

    def test_arg_str(self):
        self.assertEqual(str(pmock.MockInvocation("penguin", ("swim",), {})),
                         "penguin('swim')")

    def test_kwarg_str(self):
        self.assertEqual(str(pmock.MockInvocation("penguin", (),
                                                  {"food": "fish"})),
                         "penguin(food='fish')")

    def test_args_str(self):
        self.assertEqual(
            str(pmock.MockInvocation("penguin", ("swim", "waddle"),
                                     {"home": "iceberg", "food": "fish"})),
            "penguin('swim', 'waddle', food='fish', home='iceberg')")


class ProxyTest(unittest.TestCase):

    def test_method_invocation(self):
        class Mock:
            def _method_invoked(self, invocation):
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

    def test_matching_mocker(self):
        class Mocker:
            def __init__(self): self.invoked = False
            def matches(self, invocation): return True
            def invoke(self): self.invoked = True
        mocker = Mocker()
        mock = pmock.Mock()
        mock._add_mocker(mocker)
        mock.proxy().wolf()
        self.assert_(mocker.invoked)

    def test_unmatched_method(self):
        class Mocker:
            def matches(self, invocation): return False
            def is_satisfied(self): return False
            def matchers_str(self): return "unsatisfied"
        mock = pmock.Mock()
        mock._add_mocker(Mocker())
        try:
            mock.proxy().wolf()
            fail("should have raised due to unexpected method call")
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(
                err.msg,
                str(pmock.MockInvocation("wolf", (), {})),
                ["unsatisfied"])

    def test_lifo_matching_order(self):
        class Mocker:
            attempt_number = 1
            def __init__(self, will_match):
                self.will_match = will_match
                self.match_attempt = None
                self.invoked = False
            def matches(self, invocation):
                self.match_attempt = Mocker.attempt_number
                Mocker.attempt_number += 1
                return self.will_match
            def invoke(self): self.invoked = True
        mocker1 = Mocker(False)
        mocker2 = Mocker(True)
        mocker3 = Mocker(False)
        mock = pmock.Mock()
        mock._add_mocker(mocker1)
        mock._add_mocker(mocker2)
        mock._add_mocker(mocker3)
        mock.proxy().wolf()
        self.assert_(mocker1.match_attempt is None)
        self.assert_(not mocker1.invoked)
        self.assertEqual(mocker2.match_attempt, 2)
        self.assert_(mocker2.invoked)
        self.assertEqual(mocker3.match_attempt, 1)
        self.assert_(not mocker3.invoked)

    def test_unsatisfied_mocker(self):
        class Mocker:
            def is_satisfied(self): return False
            def matchers_str(self): return "unsatisfied"
        mock = pmock.Mock()
        mock._add_mocker(Mocker())
        try:
            mock.verify()
            fail("should have raised due to unsatisfied mocker")
        except pmock.VerificationError, err:
            self.assertUnsatisfiedMsg(err.msg, ["unsatisfied"])

    def test_satisfied_mocker(self):
        class Mocker:
            def is_satisfied(self): return True
        mock = pmock.Mock()
        mock._add_mocker(Mocker())
        mock.verify()

    def test_conflicting_mocker(self):
        class Mocker:
            def matches(self, invocation): return True
            def invoke(self): raise pmock.InvokeConflictError
            def matchers_str(self): return "conflicted"
        mock = pmock.Mock()
        mock._add_mocker(Mocker())
        try:
            mock.proxy().wolf()
            fail("should have raised due to conflicting mocker")
        except pmock.MatchError, err:
            self.assertConflictedCallMsg(
                err.msg,
                str(pmock.MockInvocation("wolf", (), {})),
                "conflicted")

    def test_expect(self):
        mock = pmock.Mock()
        mock.expect(pmock.OnceInvocationMatcher()).method("foo")
        self.assertRaises(pmock.VerificationError, mock.verify)

    def test_stub(self):
        mock = pmock.Mock()
        mock.stub().method("foo")
        mock.verify()


class MockTestCaseTest(unittest.TestCase):

    def test_mock_test_case_clears_invocation_log(self):
        class MockTest(pmock.MockTestCase):
            def test_dummy(self): pass
        test = MockTest("test_dummy")
        pmock.InvocationLog.instance().invoked("bat")
        test.run()
        self.assert_(
            not pmock.InvocationLog.instance().has_been_invoked("bat"))

    def test_normal_test_case_doesnt_clear_invocation_log(self):
        class MockTest(unittest.TestCase):
            def test_dummy(self): pass
        test = MockTest("test_dummy")
        pmock.InvocationLog.instance().invoked("bat")
        test.run()
        self.assert_(pmock.InvocationLog.instance().has_been_invoked("bat"))


class ReturnValueTest(unittest.TestCase):

    def test_invoke(self):
        self.assertEqual(pmock.ReturnValueAction("owl").invoke(), "owl")


class RaiseExceptionAction(unittest.TestCase):

    def test_invoke(self):
        exception = RuntimeError("owl")
        try:
            pmock.RaiseExceptionAction(exception).invoke()
            fail("expected exception to be raised")
        except RuntimeError, err:
            self.assertEqual(err, exception)


class OnceInvocationMatcherTest(unittest.TestCase):

    def setUp(self):
        self.matcher = pmock.OnceInvocationMatcher()
        
    def test_uninvoked_matches(self):
        self.assert_(self.matcher.matches())

    def test_invoked_doesnt_match(self):
        self.matcher.invoke()
        self.assert_(not self.matcher.matches())

    def test_uninvoked_is_unsatisfied(self):
        self.assert_(not self.matcher.is_satisfied())

    def test_invoked_is_satisfied(self):
        self.matcher.invoke()
        self.assert_(self.matcher.is_satisfied())


class AtLeastOnceInvocationMatcherTest(unittest.TestCase):

    def setUp(self):
        self.matcher = pmock.AtLeastOnceInvocationMatcher()
        
    def test_uninvoked_matches(self):
        self.assert_(self.matcher.matches())

    def test_invoked_matches(self):
        self.matcher.invoke()
        self.assert_(self.matcher.matches())

    def test_uninvoked_is_unsatisfied(self):
        self.assert_(not self.matcher.is_satisfied())

    def test_invoked_is_satisfied(self):
        self.matcher.invoke()
        self.assert_(self.matcher.is_satisfied())


class NotCalledInvocationMatcherTest(unittest.TestCase):

    def setUp(self):
        self.matcher = pmock.NotCalledInvocationMatcher()
        
    def test_uninvoked_matches(self):
        self.assert_(self.matcher.matches())

    def test_invoke_raises(self):
        self.assertRaises(pmock.InvokeConflictError, self.matcher.invoke)

    def test_uninvoked_is_satisfied(self):
        self.assert_(self.matcher.is_satisfied())

    def test_invoked_is_unsatisfied(self):
        try:
            self.matcher.invoke()
            fail()
        except pmock.InvokeConflictError:
            self.assert_(not self.matcher.is_satisfied())


class StubInvocationMatcherTest(unittest.TestCase):

    def setUp(self):
        self.matcher = pmock.StubInvocationMatcher()
        
    def test_uninvoked_matches(self):
        self.assert_(self.matcher.matches())

    def test_uninvoked_is_satisfied(self):
        self.assert_(self.matcher.is_satisfied())

    def test_invoked_is_satisfied(self):
        self.matcher.invoke()
        self.assert_(self.matcher.is_satisfied())


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
