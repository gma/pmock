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
        class MockCall:
            def __str__(self): return "call"
        class Mocker:
            def matchers_str(self): return "matchers"
        error = pmock.MatchError.create_unexpected_error(MockCall(),
                                                         [Mocker()])
        self.assertUnexpectedCallMsg(error.msg, "call", ["matchers"])

    def test_create_conflict(self):
        class MockCall:
            def __str__(self): return "call"
        class Mocker:
            def matchers_str(self): return "matchers"
        error = pmock.MatchError.create_conflict_error(MockCall(), Mocker())
        self.assertConflictedCallMsg(error.msg, "call", "matchers")


class ArgumentsMatcherTestMixin(object):

    def __init__(self, matcher_class):
        self.matcher_class = matcher_class
    
    def test_matches_arguments(self):
        arg1 = []
        args_matcher = self.matcher_class((pmock.same(arg1),), {})
        self.assert_(
            args_matcher.matches(pmock.MockCall("snake", (arg1,), {})))

    def test_matches_keyword_arguments(self):
        arg2 = []
        args_matcher = self.matcher_class((), {"food": pmock.same(arg2)})
        call = pmock.MockCall("snake", (), {"food": arg2})
        self.assert_(args_matcher.matches(call))

    def test_matches_both_types_of_arguments(self):
        arg1 = []
        arg2 = []
        args_matcher = self.matcher_class((pmock.same(arg1),),
                                          {"food": pmock.same(arg2)})
        call = pmock.MockCall("snake", (arg1,), {"food": arg2})
        self.assert_(args_matcher.matches(call))

    def test_insufficient_arguments(self):
        args_matcher = self.matcher_class((pmock.eq("slither"),), {})
        self.assert_(
            not args_matcher.matches(pmock.MockCall("snake", (), {})))

    def test_insufficient_keyword_arguments(self):
        args_matcher = self.matcher_class((), {"food": pmock.eq("goat")})
        self.assert_(not args_matcher.matches(pmock.MockCall("snake", (), {})))

    def test_unmatched_argument(self):
        class UnmatchedConstraint:
            def eval(self, call): return False
        args_matcher = self.matcher_class((UnmatchedConstraint(),), {})
        call = pmock.MockCall("snake", ("slither",), {})
        self.assert_(not args_matcher.matches(call))

    def test_unmatched_keyword_argument(self):
        class UnmatchedConstraint:
            def eval(self, call): return False
        args_matcher = self.matcher_class((), {"food": UnmatchedConstraint()})
        call = pmock.MockCall("snake", (), {"food": "goat"})
        self.assert_(not args_matcher.matches(call))


class AllArgumentsMatcherTest(ArgumentsMatcherTestMixin, unittest.TestCase):

    def __init__(self, *args):
        ArgumentsMatcherTestMixin.__init__(self, pmock.AllArgumentsMatcher)
        unittest.TestCase.__init__(self, *args)        

    def test_extra_arguments(self):
        args_matcher = pmock.AllArgumentsMatcher((pmock.eq("slither"),), {})
        self.assert_(not args_matcher.matches(
            pmock.MockCall("snake", ("slither", "hiss"), {})))

    def test_extra_keyword_arguments(self):
        args_matcher = pmock.AllArgumentsMatcher((),
                                                 {"food": pmock.eq("goat")})
        self.assert_(not args_matcher.matches(
            pmock.MockCall("snake", (), {"food": "goat", "colour": "brown"})))

    def test_no_arguments(self):
        args_matcher = pmock.AllArgumentsMatcher()
        self.assert_(args_matcher.matches(pmock.MockCall("snake", (), {})))
        self.assert_(not args_matcher.matches(pmock.MockCall("snake",
                                                             ("hiss",),
                                                             {})))
        self.assert_(not args_matcher.matches(
            pmock.MockCall("snake", (), {"food": "goat"})))

    def test_str(self):
        self.assertEqual(str(pmock.AllArgumentsMatcher()), "")


class LeastArgumentsMatcherTest(ArgumentsMatcherTestMixin, unittest.TestCase):

    def __init__(self, *args):
        ArgumentsMatcherTestMixin.__init__(self, pmock.LeastArgumentsMatcher)
        unittest.TestCase.__init__(self, *args)        
    
    def test_extra_arguments(self):
        args_matcher = pmock.LeastArgumentsMatcher((pmock.eq("slither"),), {})
        self.assert_(args_matcher.matches(
            pmock.MockCall("snake", ("slither", "hiss"), {})))

    def test_extra_keyword_arguments(self):
        args_matcher = pmock.LeastArgumentsMatcher((),
                                                 {"food": pmock.eq("goat")})
        self.assert_(args_matcher.matches(
            pmock.MockCall("snake", (), {"food": "goat", "colour": "brown"})))

    def test_any_arguments(self):
        args_matcher = pmock.LeastArgumentsMatcher()
        self.assert_(args_matcher.matches(pmock.MockCall("snake", (), {})))
        self.assert_(args_matcher.matches(pmock.MockCall("snake",
                                                         ("hiss",),
                                                         {})))
        self.assert_(args_matcher.matches(pmock.MockCall("snake",
                                                         ("constrict",),
                                                         {"food": "goat"})))

    def test_str(self):
        self.assertEqual(str(pmock.LeastArgumentsMatcher()), "...")


class CallMockerTest(unittest.TestCase):

    def test_matches(self):
        class MockMatcher:
            def matches(self): return True
        mocker = pmock.CallMocker(MockMatcher())
        mocker.method("skunk").with(pmock.eq("spray"))
        self.assert_(mocker.matches(pmock.MockCall("skunk", ("spray",), {})))

    def test_matches_with_at_least(self):
        class MockMatcher:
            def matches(self): return True        
        mocker = pmock.CallMocker(MockMatcher())
        mocker.method("skunk").with_at_least(pmock.eq("spray"))
        self.assert_(
            mocker.matches(pmock.MockCall("skunk", ("spray", "forage"), {})))

    def test_matches_with_no_args(self):
        class MockMatcher:
            def matches(self): return True        
        mocker = pmock.CallMocker(MockMatcher())
        mocker.method("skunk").no_args()
        self.assert_(mocker.matches(pmock.MockCall("skunk", (), {})))
        self.assert_(
            not mocker.matches(pmock.MockCall("skunk", ("spray",), {})))
        self.assert_(
            not mocker.matches(pmock.MockCall("skunk", (), {"smell":"bad"})))

    def test_unmatched_call_matcher(self):
        class MockMatcher:
            def matches(self): return False
        mocker = pmock.CallMocker(MockMatcher())
        mocker.method("skunk").with(pmock.eq("spray"))
        self.assert_(
            not mocker.matches(pmock.MockCall("skunk", ("spray",), {})))

    def test_unmatched_method(self):
        class MockMatcher:
            def matches(self): return True
        mocker = pmock.CallMocker(MockMatcher())
        mocker.method("skunk").with(pmock.eq("spray"))
        self.assert_(
            not mocker.matches(pmock.MockCall("ferret", ("spray",), {})))

    def test_unmatched_args(self):
        class MockMatcher:
            def matches(self): return True
        mocker = pmock.CallMocker(MockMatcher())
        mocker.method("skunk").with(pmock.eq("spray"))
        self.assert_(
            not mocker.matches(pmock.MockCall("skunk", ("fly",), {})))

    def test_is_void(self):
        class MockCallMatcher:
            def invoke(self): pass
            def matches(self): return True
        mocker = pmock.CallMocker(MockCallMatcher())
        mocker.method("skunk").is_void()
        self.assert_(mocker.invoke() is None)
        
    def test_invocation(self):
        class MockInvocable:
            def __init__(self): self.invoked = False
            def invoke(self): self.invoked = True
        mock_call_matcher = MockInvocable()
        mock_action = MockInvocable()
        mocker = pmock.CallMocker(mock_call_matcher)
        mocker.will(mock_action)
        mocker.invoke()
        self.assert_(mock_call_matcher.invoked)
        self.assert_(mock_action.invoked)
        
    def test_matches_str(self):
        mocker = pmock.CallMocker(pmock.OnceMatcher())
        mocker.method("skunk")
        self.assertEqual(mocker.matchers_str(),
                         "%s %s(%s)" % (pmock.OnceMatcher(),
                                        "skunk",
                                        pmock.LeastArgumentsMatcher()))

    def test_satisfaction(self):
        class MockCallMatcher:
            def __init__(self, satisfied): self.satisfied = satisfied
            def is_satisfied(self): return self.satisfied
        mocker1 = pmock.CallMocker(MockCallMatcher(True))
        self.assert_(mocker1.is_satisfied())
        mocker2 = pmock.CallMocker(MockCallMatcher(False))
        self.assert_(not mocker2.is_satisfied())


class MethodMatcherTest(unittest.TestCase):

    def setUp(self):
        self.method_matcher = pmock.MethodMatcher("horse")

    def test_matches(self):
        self.assert_(
            self.method_matcher.matches(pmock.MockCall("horse", (), {})))

    def test_unmatched(self):
        self.assert_(
            not self.method_matcher.matches(pmock.MockCall("donkey", (), {})))
 
    def test_str(self):
        self.assertEqual(str(self.method_matcher), "horse")


class MockCallTest(unittest.TestCase):

    def test_no_args_str(self):
        self.assertEqual(str(pmock.MockCall("penguin", (), {})), "penguin()")

    def test_arg_str(self):
        self.assertEqual(str(pmock.MockCall("penguin", ("swim",), {})),
                         "penguin('swim')")

    def test_kwarg_str(self):
        self.assertEqual(str(pmock.MockCall("penguin", (), {"food": "fish"})),
                         "penguin(food='fish')")

    def test_args_str(self):
        self.assertEqual(
            str(pmock.MockCall("penguin", ("swim", "waddle"),
                               {"home": "iceberg", "food": "fish"})),
            "penguin('swim', 'waddle', food='fish', home='iceberg')")


class ProxyTest(unittest.TestCase):

    def test_method_call(self):
        class Mock:
            def method_called(self, call):
                self.call = call
        mock = Mock()
        proxy = pmock.Proxy(mock)
        proxy.camel("walk", desert="gobi")
        self.assertEqual(mock.call.name, "camel")
        self.assertEqual(mock.call.args, ("walk",))
        self.assertEqual(mock.call.kwargs, {"desert": "gobi"})        


class MockTest(testsupport.ErrorMsgAssertsMixin, unittest.TestCase):

    def test_one_to_one_proxy(self):
        mock = pmock.Mock()
        self.assert_(mock.proxy() is mock.proxy())

    def test_matching_mocker(self):
        class Mocker:
            def __init__(self): self.invoked = False
            def matches(self, call): return True
            def invoke(self): self.invoked = True
        mocker = Mocker()
        mock = pmock.Mock()
        mock.expect(mocker)
        mock.proxy().wolf()
        self.assert_(mocker.invoked)

    def test_unmatched_method(self):
        class Mocker:
            def matches(self, call): return False
            def is_satisfied(self): return False
            def matchers_str(self): return "unsatisfied"
        mock = pmock.Mock()
        mock.expect(Mocker())
        try:
            mock.proxy().wolf()
            fail("should have raised due to unexpected method call")
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg,
                                         str(pmock.MockCall("wolf", (), {})),
                                         ["unsatisfied"])

    def test_lifo_matching_order(self):
        class Mocker:
            attempt_number = 1
            def __init__(self, will_match):
                self.will_match = will_match
                self.match_attempt = None
                self.invoked = False
            def matches(self, call):
                self.match_attempt = Mocker.attempt_number
                Mocker.attempt_number += 1
                return self.will_match
            def invoke(self): self.invoked = True
        mocker1 = Mocker(False)
        mocker2 = Mocker(True)
        mocker3 = Mocker(False)
        mock = pmock.Mock()
        mock.expect(mocker1)
        mock.expect(mocker2)
        mock.expect(mocker3)
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
        mock.expect(Mocker())
        try:
            mock.verify()
            fail("should have raised due to unsatisfied mocker")
        except pmock.VerificationError, err:
            self.assertUnsatisfiedMsg(err.msg, ["unsatisfied"])

    def test_satisfied_mocker(self):
        class Mocker:
            def is_satisfied(self): return True
        mock = pmock.Mock()
        mock.expect(Mocker())
        mock.verify()

    def test_conflicting_mocker(self):
        class Mocker:
            def matches(self, call): return True
            def invoke(self): raise pmock.InvokeConflictError
            def matchers_str(self): return "conflicted"
        mock = pmock.Mock()
        mock.expect(Mocker())
        try:
            mock.proxy().wolf()
            fail("should have raised due to conflicting mocker")
        except pmock.MatchError, err:
            self.assertConflictedCallMsg(err.msg,
                                         str(pmock.MockCall("wolf", (), {})),
                                         "conflicted")


class OnceMatcherTest(unittest.TestCase):

    def setUp(self):
        self.matcher = pmock.OnceMatcher()
        
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


class AtLeastOnceMatcherTest(unittest.TestCase):

    def setUp(self):
        self.matcher = pmock.AtLeastOnceMatcher()
        
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


class NotCalledMatcherTest(unittest.TestCase):

    def setUp(self):
        self.matcher = pmock.NotCalledMatcher()
        
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


class EqConstraintTest(unittest.TestCase):

    def test_match(self):
        self.assert_(pmock.eq("mouse").eval("mouse"))

    def test_umatched(self):
        self.assert_(not pmock.eq("mouse").eval("rat"))
        
    def test_str(self):
        self.assertEqual(str(pmock.eq("mouse")),
                         "pmock.eq('mouse')")


class SameConstraintTest(unittest.TestCase):

    def test_match(self):
        mutable = ["mouse"]
        self.assert_(pmock.same(mutable).eval(mutable))

    def test_umatched(self):
        self.assert_(not pmock.same(["mouse"]).eval(["mouse"]))
        
    def test_str(self):
        self.assertEqual(str(pmock.same(["mouse"])),
                         "pmock.same(['mouse'])")


class StringContainsConstraintTest(unittest.TestCase):

    def test_matches_same_string(self):
        self.assert_(pmock.string_contains("mouse").eval("mouse"))
        
    def test_matches_substring(self):
        self.assert_(pmock.string_contains("mo").eval("mouse"))
        self.assert_(pmock.string_contains("ou").eval("mouse"))
        self.assert_(pmock.string_contains("se").eval("mouse"))
        self.assert_(pmock.string_contains("").eval("mouse"))
        
    def test_umatched(self):
        self.assert_(not pmock.string_contains("mouse").eval("rat"))
        self.assert_(not pmock.string_contains("mouse").eval(None))

    def test_str(self):
        self.assertEqual(str(pmock.string_contains("mouse")),
                         "pmock.string_contains('mouse')")


class FunctorConstraintTest(unittest.TestCase):

    def test_matches(self):
        self.assert_(pmock.functor(lambda arg: True).eval("mouse"))
        
    def test_umatched(self):
        self.assert_(not pmock.functor(lambda arg: False).eval("mouse"))

    def test_str(self):
        lambda_ = lambda arg: False
        self.assertEqual(str(pmock.functor(lambda_)),
                         "pmock.functor(%s)" % repr(lambda_))


if __name__ == '__main__':
    unittest.main()
