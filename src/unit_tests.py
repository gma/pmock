import unittest

import pmock
import testsupport


class VerificationErrorTest(unittest.TestCase):

    def test_create_error(self):
        class Mocker:
            def __str__(self): return "matchers"
        error = pmock.VerificationError.create_error("problem", Mocker())
        self.assertEqual(error.msg, "problem: matchers")


class MatchErrorTest(unittest.TestCase):

    class MockInvocation:
        def __str__(self): return "call"
    class Mock:
        def __init__(self, invokables_str): self._str = invokables_str
        def invokables_str(self): return self._str

    def test_empty_invokables(self):
        error = pmock.MatchError.create_error("msg",
                                              self.MockInvocation(),
                                              self.Mock(""))
        self.assertEqual(error.msg, "msg\ninvoked call")

    def test_non_empty_invokables(self):
        error = pmock.MatchError.create_error("msg",
                                              self.MockInvocation(),
                                              self.Mock("invokables"))
        self.assertEqual(error.msg, "msg\ninvoked call\nin:\ninvokables")


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


class InvocationMockerTest(unittest.TestCase):

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
            def __init__(self, raises, str_str):
                self.raises = raises
                self.str_str = str_str
                self.verified = False
            def __str__(self):
                return self.str_str
            def verify(self):
                self.verified = True
                if self.raises:
                    raise AssertionError("problem")
        matcher1 = MockInvocationMatcher(False, "one")
        matcher2 = MockInvocationMatcher(True, "two")
        matcher3 = MockInvocationMatcher(True, "three")
        mocker = pmock.InvocationMocker(matcher1)
        mocker.add_matcher(matcher2)
        mocker.add_matcher(matcher3)
        try:
            mocker.verify()
            self.fail("expected verify to raise")
        except pmock.VerificationError, err:
            self.assert_(matcher1.verified)
            self.assert_(matcher2.verified)
            self.assert_(not matcher3.verified)
            self.assertEqual(err.msg, "problem: %s" % mocker)
            
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
                         "invocation_matcher: added_matcher1added_matcher2, "
                         "action")

    def test_no_id_str(self):
        class MockMatcher:
            def __init__(self, str_str): self._str = str_str
            def __str__(self): return self._str
        mocker = pmock.InvocationMocker(MockMatcher("invocation_matcher"))
        mocker.add_matcher(MockMatcher("added_matcher1"))
        self.assertEqual(str(mocker), "invocation_matcher: added_matcher1")

    def test_id_str(self):
        class MockMatcher:
            def __init__(self, str_str): self._str = str_str
            def __str__(self): return self._str
        MockAction = MockMatcher
        mocker = pmock.InvocationMocker(MockMatcher("invocation_matcher"))
        mocker.add_matcher(MockMatcher("added_matcher1"))
        mocker.set_action(MockAction("action"))
        mocker.set_id("quack")
        self.assertEqual(str(mocker),
                         "invocation_matcher: added_matcher1, action [quack]")


class InvocationMockerBuilderTest(testsupport.ErrorMsgAssertsMixin,
                                  unittest.TestCase):

    class MockInvocationMocker:
        def __init__(self):
            self.added_matchers = []
            self.id = None
            self.action = None
        def add_matcher(self, matcher):
            self.added_matchers.append(matcher)
        def set_id(self, mocker_id):
            self.id = mocker_id
        def set_action(self, action):
            self.action = action
        def _get_only_added_matcher(self):
            if len(self.added_matchers) != 1:
                raise AssertionError('more than one matcher has been added')
            return self.added_matchers[0]
        added_matcher = property(_get_only_added_matcher)

    def setUp(self):
        self.mocker = self.MockInvocationMocker()
        self.builder_namespace = pmock.Mock()
        self.builder = pmock.InvocationMockerBuilder(self.mocker,
                                                     self.builder_namespace)

    def test_add_method_matcher(self):
        self.assert_(self.builder.method("chicken") is not None)
        self.assert_(isinstance(self.mocker.added_matcher,
                                pmock.MethodMatcher))
        self.assert_(self.mocker.added_matcher.matches(
            pmock.Invocation("chicken", (), {})))
        self.assertEqual(self.builder_namespace.lookup_id("chicken"),
                         self.builder)

    def test_add_direct_method_matcher(self):
        self.assert_(self.builder.chicken() is not None)
        self.assert_(isinstance(self.mocker.added_matchers[0],
                                pmock.MethodMatcher))
        self.assert_(self.mocker.added_matchers[0].matches(
            pmock.Invocation("chicken", (), {})))
        self.assert_(self.mocker.added_matchers[1].matches(
            pmock.Invocation("chicken", (), {})))
        self.assertEqual(self.builder_namespace.lookup_id("chicken"),
                         self.builder)

    def test_add_direct_method_and_arg_matcher(self):
        self.assert_(self.builder.chicken(pmock.eq("egg")) is not None)
        self.assert_(isinstance(self.mocker.added_matchers[0],
                                pmock.MethodMatcher))
        self.assert_(self.mocker.added_matchers[0].matches(
            pmock.Invocation("chicken", (), {})))
        self.assert_(self.mocker.added_matchers[1].matches(
            pmock.Invocation("chicken", ("egg",), {})))
        self.assertEqual(self.builder_namespace.lookup_id("chicken"),
                         self.builder)

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

    def test_set_id(self):
        self.assert_(self.builder.id("poultry") is not None)
        self.assertEqual(self.mocker.id, "poultry")
        self.assertEqual(self.builder_namespace.lookup_id("poultry"),
                         self.builder)

    def test_set_duplicate_id(self):
        self.builder.id("poultry")
        try:
            self.builder.id("poultry")
            self.fail("mocker with duplicate ids should raise")
        except pmock.DefinitionError, err:
            self.assertDuplicateIdMsg(err.msg, "poultry")
        
    def test_add_after_ordering(self):
        builder2 = pmock.InvocationMockerBuilder(self.MockInvocationMocker(),
                                                 self.builder_namespace)
        builder2.id("rooster")
        self.assert_(self.builder.after("rooster") is not None)
        self.assert_(isinstance(self.mocker.added_matcher,
                                pmock.InvokedAfterMatcher))

    def test_after_undefined_id(self):
        try:
            self.builder.after("rooster")
        except pmock.DefinitionError, err:
            self.assertUndefinedIdMsg(err.msg, "rooster")

    def test_add_after_other_named_mock_ordering(self):
        other_mock = pmock.Mock("coup")
        other_mock.expects(pmock.OnceInvocationMatcher()).method("rooster")
        self.assert_(self.builder.after("rooster", other_mock) is not None)
        self.assert_(isinstance(self.mocker.added_matcher,
                                pmock.InvokedAfterMatcher))
        self.assertEqual(str(self.mocker.added_matcher),
                         ".after('rooster' on mock 'coup')")

    def test_add_after_other_unnamed_mock_ordering(self):
        other_mock = pmock.Mock()
        other_mock.expects(pmock.OnceInvocationMatcher()).method("rooster")
        self.assert_(self.builder.after("rooster", other_mock) is not None)
        self.assert_(isinstance(self.mocker.added_matcher,
                                pmock.InvokedAfterMatcher))
        self.assertEqual(str(self.mocker.added_matcher),
                         ".after('rooster' on mock '%s')" % str(other_mock))

    def test_match(self):
        class CustomMatcher: pass
        custom_matcher = CustomMatcher()
        self.assert_(self.builder.match(custom_matcher) is not None)
        self.assertEqual(self.mocker.added_matcher, custom_matcher)


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


class InvokedAfterMatcherTest(unittest.TestCase):

    def setUp(self):
        self.invocation_recorder = pmock.InvokedRecorderMatcher()
        self.matcher = pmock.InvokedAfterMatcher(self.invocation_recorder,
                                                 "'weasel'")
        self.invocation = pmock.Invocation("stoat", (), {})
        
    def test_uninvoked_doesnt_match(self):
        self.assert_(not self.matcher.matches(self.invocation))

    def test_invoked_matches(self):
        self.invocation_recorder.invoked(self.invocation)
        self.assert_(self.matcher.matches(self.invocation))

    def test_str(self):
        self.assertEqual(str(self.matcher), ".after('weasel')")


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


class MockTest(unittest.TestCase):

    def test_one_to_one_proxy(self):
        mock = pmock.Mock()
        self.assert_(mock.proxy() is mock.proxy())

    def test_unmatched_invocation(self):
        mock = pmock.Mock()
        try:
            mock.invoke(pmock.Invocation("wolf", (), {}))
            self.fail("should have raised due to unexpected method call")
        except pmock.MatchError, err:
            self.assertEqual(err.msg,
                             "no match found\n"
                             "invoked wolf()")

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

    def test_lifo_verify_order(self):
        class Invokable:
            def __init__(self, raises):
                self.verified = False
                self.raises = raises
            def verify(self):
                self.verified = True
                if self.raises:
                    raise pmock.VerificationError("problem")
        invokable1 = Invokable(False)
        invokable2 = Invokable(True)
        invokable3 = Invokable(False)
        mock = pmock.Mock()
        mock.add_invokable(invokable3)
        mock.add_invokable(invokable2)
        mock.add_invokable(invokable1)
        try:
            mock.verify()
            self.fail("expected verify to raise")
        except pmock.VerificationError:
            self.assert_(invokable1.verified)
            self.assert_(invokable2.verified)
            self.assert_(not invokable3.verified)
        
    def test_invokables_str(self):
        class Invokable:
            def __init__(self, str_str): self._str = str_str
            def __str__(self): return self._str
        mock = pmock.Mock()
        self.assertEqual(mock.invokables_str(), "")
        mock.add_invokable(Invokable("howl"))
        self.assertEqual(mock.invokables_str(), "howl")
        mock.add_invokable(Invokable("bark"))
        self.assertEqual(mock.invokables_str(), "howl,\nbark")
        mock.add_invokable(Invokable("growl"))
        self.assertEqual(mock.invokables_str(), "howl,\nbark,\ngrowl")
        
    def test_expects(self):
        mock = pmock.Mock()
        mock.expects(pmock.OnceInvocationMatcher()).method("foo")
        self.assert_(mock.lookup_id("foo") is not None)
        self.assertRaises(pmock.VerificationError, mock.verify)

    def test_stubs(self):
        mock = pmock.Mock()
        mock.stubs().method("foo")
        self.assert_(mock.lookup_id("foo") is not None)
        mock.verify()

    def test_get_unnamed(self):
        mock = pmock.Mock()
        self.assertEqual(mock.get_name(), str(mock))

    def test_get_name(self):
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


class RegisterIdTest(testsupport.ErrorMsgAssertsMixin, unittest.TestCase):
    
    def setUp(self):
        class MockBuilder: pass
        self.builder = MockBuilder()
        self.mock = pmock.Mock()
        self.mock.register_unique_id("howler", self.builder)

    def test_register_unique_id(self):
        self.assertEqual(self.mock.lookup_id("howler"), self.builder)

    def test_register_duplicate_id(self):
        try:
            self.mock.register_unique_id("howler", self.builder)
        except pmock.DefinitionError, err:
            self.assertDuplicateIdMsg(err.msg, "howler")

    def test_lookup_unknown_id(self):
        self.assert_(self.mock.lookup_id("growler") is None)


class RegisterMethodNameTest(testsupport.ErrorMsgAssertsMixin,
                             unittest.TestCase):

    class MockBuilder: pass
    
    def setUp(self):
        self.builder = self.MockBuilder()
        self.mock = pmock.Mock()
        self.mock.register_method_name("wolf", self.builder)

    def test_register_method_name(self):
        self.assertEqual(self.mock.lookup_id("wolf"), self.builder)

    def test_register_method_again(self):
        another_builder = self.MockBuilder()
        self.mock.register_method_name("wolf", another_builder)
        self.assertEqual(self.mock.lookup_id("wolf"), another_builder)


class MockTestCaseTest(unittest.TestCase):

    def test_no_mocks_created(self):
        class Test(pmock.MockTestCase):
            def test_method(self):
                pass
        test = Test('test_method')
        result = unittest.TestResult()
        test.run(result)
        self.assert_(result.wasSuccessful())

    def test_created_mock(self):
        created_mocks = []
        class Test(pmock.MockTestCase):
            def test_method(self):
                created_mocks.append(self.mock())
        test = Test('test_method')
        result = unittest.TestResult()
        test.run(result)
        self.assert_(result.wasSuccessful(),
                     'errors %s, failures %s' % (result.errors,
                                                 result.failures))
        self.assert_(isinstance(created_mocks[0], pmock.Mock))

    def test_created_mocks_are_verified(self):
        class MockMatcher:
            def verify(self): self.is_verified = True
        matcher = MockMatcher()
        class Test(pmock.MockTestCase):
            def test_method(self):
                self.mock().expects(matcher)
        test = Test('test_method')
        test.run()
        self.assert_(matcher.is_verified)

    def test_raised_verify_is_failure(self):
        class MockMatcher:
            def verify(self): raise pmock.VerificationError('oops')
        matcher = MockMatcher()
        class Test(pmock.MockTestCase):
            def test_method(self):
                self.mock().expects(matcher)
        test = Test('test_method')
        result = unittest.TestResult()
        test.run(result)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(len(result.errors), 0)

    def test_auto_verify_independent_of_fixtures(self):
        fixtures = []
        class MockMatcher:
            def verify(self): self.is_verified = True
        matcher = MockMatcher()
        class Test(pmock.MockTestCase):
            def setUp(self):
                fixtures.append('setUp')
            def tearDown(self):
                fixtures.append('tearDown')
            def test_method(self):
                self.mock().expects(matcher)
        test = Test('test_method')
        result = unittest.TestResult()
        test.run()
        self.assert_(matcher.is_verified)
        self.assertEqual(fixtures, ['setUp', 'tearDown'])


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
            self.fail("expected exception to be raised")
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

    def test_verify_uninvoked(self):
        try:
            self.matcher.verify()
            self.fail("expected verify to raise")
        except AssertionError, err:
            self.assertEqual("expected method was not invoked", str(err))

    def test_verify_invoked(self):
        self.matcher.invoked(pmock.Invocation("worm", (), {}))
        self.matcher.verify()

    def test_uninvoked_str(self):
        self.assertEqual(str(self.matcher), "expected once")

    def test_invoked_str(self):
        self.matcher.invoked(pmock.Invocation("worm", (), {}))        
        self.assertEqual(str(self.matcher),
                         "expected once and has been invoked")


class AtLeastOnceInvocationMatcherTest(unittest.TestCase):

    def setUp(self):
        self.matcher = pmock.AtLeastOnceInvocationMatcher()
        
    def test_uninvoked_matches(self):
        self.assert_(self.matcher.matches(pmock.Invocation("worm", (), {})))

    def test_invoked_matches(self):
        self.matcher.invoked(pmock.Invocation("worm", (), {}))
        self.assert_(self.matcher.matches(pmock.Invocation("snake", (), {})))

    def test_verify_uninvoked(self):
        try:
            self.matcher.verify()
            self.fail("expected verify to raise")
        except AssertionError, err:
            self.assertEqual("expected method was not invoked", str(err))

    def test_verify_invoked(self):
        self.matcher.invoked(pmock.Invocation("worm", (), {}))
        self.matcher.verify()

    def test_uninvoked_str(self):
        self.assertEqual(str(self.matcher), "expected at least once")

    def test_invoked_str(self):
        self.matcher.invoked(pmock.Invocation("worm", (), {}))        
        self.assertEqual(str(self.matcher),
                         "expected at least once and has been invoked")


class NotCalledInvocationMatcherTest(unittest.TestCase):

    def setUp(self):
        self.matcher = pmock.NotCalledInvocationMatcher()
        
    def test_uninvoked_matches(self):
        self.assert_(self.matcher.matches(pmock.Invocation("worm", (), {})))

    def test_invoke_raises(self):
        try:
            self.matcher.invoked(pmock.Invocation("worm", (), {}))
            self.fail("expected exception to be raised")
        except AssertionError, err:
            self.assertEqual(str(err), "expected method to never be invoked")

    def test_verify_uninvoked(self):
        self.matcher.verify()

    def test_str(self):
        self.assertEqual(str(self.matcher), "expected not to be called")


class StubInvocationMatcherTest(unittest.TestCase):

    def setUp(self):
        self.matcher = pmock.StubInvocationMatcher()
        
    def test_uninvoked_matches(self):
        self.assert_(self.matcher.matches(pmock.Invocation("worm", (), {})))

    def test_verify_uninvoked(self):
        self.matcher.verify()

    def test_verify_invoked(self):
        self.matcher.invoked(pmock.Invocation("worm", (), {}))
        self.matcher.verify()

    def test_str(self):
        self.assertEqual(str(self.matcher), "stub")


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
