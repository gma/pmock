import unittest

import pmock


class MockTestCase(unittest.TestCase):

    def assertUncalledMsg(self, msg, uncalled_strs):
        self.assertEqual(msg, "expected method(s) %s uncalled" %
                         ", ".join(uncalled_strs))

    def assertUnexpectedCallMsg(self, msg, call_str, expected_call_strs):
        if len(expected_call_strs) > 0:
            self.assertEqual(msg, "unexpected call %s, expected call(s) %s" %
                             (call_str, ", ".join(expected_call_strs)))
        else:
            self.assertEqual(msg, "unexpected call %s, no expected calls "
                             "remaining" % call_str)

    
class MockMethodTest(MockTestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expect().method("dog")
        
    def test_uncalled_method(self):
        try:
            self.mock.verify()
            self.fail()
        except pmock.VerificationError, err:
            self.assertUncalledMsg(err.msg, ["dog(...)"])

    def test_called_method(self):
        self.mock.proxy().dog()
        self.mock.verify()

    def test_called_method_with_extra_arg(self):
        self.mock.proxy().dog("bone")
        self.mock.verify()

    def test_call_wrong_method(self):
        try:
            self.mock.proxy().cat()
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "cat()", ["dog(...)"])

    def test_default_return_value(self):
        self.assertEqual(self.mock.proxy().dog(), None)

    def test_called_method_twice(self):
        self.mock.proxy().dog()
        try:
            self.mock.proxy().dog()
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "dog()", [])


class MockMethodWithArgTestMixin(object):

    def test_uncalled_method(self):
        try:
            self.mock.verify()
            self.fail()
        except pmock.VerificationError, err:
            self.assertUncalledMsg(err.msg, ["dog(pmock.eq('bone'))"])

    def test_method_with_correct_arg(self):
        self.mock.proxy().dog("bone")
        self.mock.verify()

    def test_call_method_with_incorrect_arg(self):
        try:
            self.mock.proxy().dog("carrot")
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "dog('carrot')",
                                         ["dog(pmock.eq('bone'))"])

    def test_call_method_with_insufficient_args(self):
        try:
            self.mock.proxy().dog()
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "dog()",
                                         ["dog(pmock.eq('bone'))"])

    def test_method_with_correct_arg_and_extras(self):
        self.mock.proxy().dog("bone", "biscuit")
        self.mock.verify()


class MockMethodWithArgTest(MockMethodWithArgTestMixin, MockTestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expect().method("dog").with(pmock.eq("bone"))

    def test_method_with_correct_arg_and_extras(self):
        try:
            self.mock.proxy().dog("bone", "biscuit")
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "dog('bone', 'biscuit')",
                                         ["dog(pmock.eq('bone'))"])


class MockMethodWithAtLeastArgTest(MockMethodWithArgTestMixin, MockTestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expect().method("dog").with_at_least(pmock.eq("bone"))

    def test_method_with_correct_arg_and_extras(self):
        self.mock.proxy().dog("bone", "biscuit")
        self.mock.verify()


class MockMethodWithArgsTest(MockTestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.toys = ["ball", "stick"]
        self.mock.expect().method("dog").with(pmock.eq("bone"),
                                              pmock.same(self.toys),
                                              pmock.string_contains("slipper"))

    def test_method_with_correct_args(self):
        self.mock.proxy().dog("bone", self.toys, "bob's slipper")
        self.mock.verify()

    def test_call_method_with_insufficient_args(self):
        try:
            self.mock.proxy().dog("bone", "biscuit")
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "dog('bone', 'biscuit')",
                              ["dog(pmock.eq('bone'), "
                               "pmock.same(['ball', 'stick']), "
                               "pmock.string_contains('slipper'))"])


class MockMethodWithArgTestMixin(object):
    
    def test_uncalled_method(self):
        try:
            self.mock.verify()
            self.fail()
        except pmock.VerificationError, err:
            self.assertUncalledMsg(err.msg, ["dog(food=pmock.eq('bone'))"])

    def test_method_with_correct_arg(self):
        self.mock.proxy().dog(food="bone")
        self.mock.verify()

    def test_call_method_with_incorrect_arg(self):
        try:
            self.mock.proxy().dog(food="ball")
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "dog(food='ball')",
                                         ["dog(food=pmock.eq('bone'))"])

    def test_call_method_with_missing_arg(self):
        try:
            self.mock.proxy().dog(toy="ball")
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "dog(toy='ball')",
                                         ["dog(food=pmock.eq('bone'))"])


class MockMethodWithKeywordArgTest(MockMethodWithArgTestMixin, MockTestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expect().method("dog").with(food=pmock.eq("bone"))

    def test_method_with_correct_arg_and_extra(self):
        try:
            self.mock.proxy().dog(toy="ball", food="bone")
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg,
                                         "dog(food='bone', toy='ball')",
                                         ["dog(food=pmock.eq('bone'))"])


class MockMethodWithAtLeastKeywordArgTest(MockMethodWithArgTestMixin,
                                          MockTestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expect().method("dog").with_at_least(food=pmock.eq("bone"))

    def test_method_with_correct_arg_and_extra(self):
        self.mock.proxy().dog(toy="ball", food="bone")
        self.mock.verify()


class MockMethodWillTest(MockTestCase):

    def test_method_will_return_value(self):
        self.mock = pmock.Mock()
        self.mock.expect().method("dog").will(pmock.return_value("bone"))
        self.assertEqual(self.mock.proxy().dog(), "bone")

    def test_method_is_void(self):
        self.mock = pmock.Mock()
        self.mock.expect().method("dog").is_void()
        self.assertEqual(self.mock.proxy().dog(), None)

    def test_method_will_throw_exception(self):
        self.mock = pmock.Mock()
        custom_err = RuntimeError()
        self.mock.expect().method("dog").will(pmock.
                                              throw_exception(custom_err))
        try:
            self.mock.proxy().dog()
            self.fail()
        except RuntimeError, err:
            self.assertEqual(err, custom_err)
            self.mock.verify()


class MockMultipleMethodsTest(MockTestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expect().method("cat")
        self.mock.expect().method("cat").with(pmock.eq("mouse"))

    def test_method_lifo_order(self):
         self.mock.proxy().cat("mouse")
         self.mock.proxy().cat()
         self.mock.verify()

    def test_uncalled_method(self):
        self.mock.proxy().cat()
        try:
            self.mock.verify()
            self.fail()
        except pmock.VerificationError, err:
            self.assertUncalledMsg(err.msg, ["cat(pmock.eq('mouse'))"])


class MockFifoExpectationTest(MockTestCase):

    # Currently expectations are matched in a LIFO manner which may be
    # surprising
    
    def test_method_lifo_order(self):
        self.mock = pmock.Mock()
        self.mock.expect().method("cat").with(pmock.eq("mouse"))
        self.mock.expect().method("cat")
        self.mock.proxy().cat(food="mouse")
        try:
            self.mock.proxy().cat()
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "cat()",
                                         ["cat(pmock.eq('mouse'))"])


class EqConstraintTest(MockTestCase):

    def test_match(self):
        self.assert_(pmock.eq("mouse").eval("mouse"))

    def test_umatched(self):
        self.assert_(not pmock.eq("mouse").eval("rat"))
        
    def test_str(self):
        self.assertEqual(str(pmock.eq("mouse")),
                         "pmock.eq('mouse')")


class SameConstraintTest(MockTestCase):

    def test_match(self):
        mutable = ["mouse"]
        self.assert_(pmock.same(mutable).eval(mutable))

    def test_umatched(self):
        self.assert_(not pmock.same(["mouse"]).eval(["mouse"]))
        
    def test_str(self):
        self.assertEqual(str(pmock.same(["mouse"])),
                         "pmock.same(['mouse'])")


class StringContainsConstraintTest(MockTestCase):

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


class FunctorConstraintTest(MockTestCase):

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

