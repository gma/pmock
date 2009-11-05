import unittest

import pmock
import testsupport


class MockMethodTest(unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expects(pmock.once()).method("dog")
        
    def test_uncalled_method(self):
        try:
            self.mock.verify()
            self.fail()
        except pmock.VerificationError:
            pass

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
        except pmock.MatchError:
            pass

    def test_default_return_value(self):
        self.assertEqual(self.mock.proxy().dog(), None)

    def test_called_method_twice(self):
        self.mock.proxy().dog()
        try:
            self.mock.proxy().dog()
            self.fail()
        except pmock.MatchError:
            pass


class MockMethodArgTestMixin(object):

    def test_uncalled_method(self):
        try:
            self.mock.verify()
            self.fail()
        except pmock.VerificationError:
            pass

    def test_method_with_correct_arg(self):
        self.mock.proxy().dog("bone")
        self.mock.verify()

    def test_call_method_with_incorrect_arg(self):
        try:
            self.mock.proxy().dog("carrot")
            self.fail()
        except pmock.MatchError:
            pass

    def test_call_method_with_insufficient_args(self):
        try:
            self.mock.proxy().dog()
            self.fail()
        except pmock.MatchError:
            pass

    def test_method_with_correct_arg_and_extras(self):
        self.mock.proxy().dog("bone", "biscuit")
        self.mock.verify()


class MockMethodWithArgTest(MockMethodArgTestMixin, unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expects(pmock.once()).method("dog").taking(pmock.eq("bone"))

    def test_method_with_correct_arg_and_extras(self):
        try:
            self.mock.proxy().dog("bone", "biscuit")
        except pmock.MatchError:
            pass


class MockMethodWithAtLeastArgTest(MockMethodArgTestMixin, unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expects(pmock.once()).method("dog").taking_at_least(
            pmock.eq("bone"))

    def test_method_with_correct_arg_and_extras(self):
        self.mock.proxy().dog("bone", "biscuit")
        self.mock.verify()


class MockMethodWithArgsTest(unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.toys = ["ball", "stick"]
        self.mock.expects(pmock.once()).method("dog").taking(
            pmock.eq("bone"),
            pmock.same(self.toys),
            pmock.string_contains("slipper"))

    def test_method_with_correct_args(self):
        self.mock.proxy().dog("bone", self.toys, "bob's slipper")
        self.mock.verify()

    def test_call_method_with_insufficient_args(self):
        try:
            self.mock.proxy().dog("bone", "biscuit")
            self.fail()
        except pmock.MatchError:
            pass


class MockMethodKeywordArgTestMixin(object):
    
    def test_uncalled_method(self):
        try:
            self.mock.verify()
            self.fail()
        except pmock.VerificationError:
            pass

    def test_method_with_correct_arg(self):
        self.mock.proxy().dog(food="bone")
        self.mock.verify()

    def test_call_method_with_incorrect_arg(self):
        try:
            self.mock.proxy().dog(food="ball")
            self.fail()
        except pmock.MatchError:
            pass

    def test_call_method_with_missing_arg(self):
        try:
            self.mock.proxy().dog(toy="ball")
            self.fail()
        except pmock.MatchError:
            pass


class MockMethodWithKeywordArgTest(MockMethodKeywordArgTestMixin,
                                   unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expects(pmock.once()).method("dog").taking(
            food=pmock.eq("bone"))

    def test_method_with_correct_arg_and_extra(self):
        try:
            self.mock.proxy().dog(toy="ball", food="bone")
        except pmock.MatchError:
            pass


class MockMethodWithAtLeastKeywordArgTest(MockMethodKeywordArgTestMixin,
                                          unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expects(pmock.once()).method("dog").taking_at_least(
            food=pmock.eq("bone"))

    def test_method_with_correct_arg_and_extra(self):
        self.mock.proxy().dog(toy="ball", food="bone")
        self.mock.verify()


class MockMethodWithNoArgsTestMixin(object):

    def test_method_with_no_args(self):
        self.mock.proxy().dog()
        self.mock.verify()

    def test_method_with_args(self):
        try:
            self.mock.proxy().dog("biscuit")
            self.fail()
        except pmock.MatchError:
            pass

    def test_method_with_kwargs(self):
        try:
            self.mock.proxy().dog(toy="ball")
            self.fail()
        except pmock.MatchError:
            pass


class MockMethodWithNoArgsTest(MockMethodWithNoArgsTestMixin,
                               unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expects(pmock.once()).method("dog").no_args()


class MockMethodWithAnyArgsTest(unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expects(pmock.once()).method("dog").any_args()

    def test_method_with_no_args(self):
        self.mock.proxy().dog()
        self.mock.verify()

    def test_method_with_args(self):
        self.mock.proxy().dog("biscuit")
        self.mock.verify()
        
    def test_method_with_kwargs(self):
        self.mock.proxy().dog(toy="ball")
        self.mock.verify()
        

class MockMethodWillTest(unittest.TestCase):

    def test_method_will_return_value(self):
        self.mock = pmock.Mock()
        self.mock.expects(pmock.once()).method("dog").will(
            pmock.return_value("bone"))
        self.assertEqual(self.mock.proxy().dog(), "bone")

    def test_method_will_raise_exception(self):
        self.mock = pmock.Mock()
        custom_err = RuntimeError()
        self.mock.expects(pmock.once()).method("dog").will(
            pmock.raise_exception(custom_err))
        try:
            self.mock.proxy().dog()
            self.fail()
        except RuntimeError, err:
            self.assert_(err is custom_err)
            self.mock.verify()


class MockDirectMethodWithNoArgsTest(MockMethodWithNoArgsTestMixin,
                                     unittest.TestCase):
    
    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expects(pmock.once()).dog()


class MockDirectMethodAdditionalTest(unittest.TestCase):

    def test_expectation(self):
        mock = pmock.Mock()
        mock.expects(pmock.once()).dog(
            pmock.eq("bone"), food=pmock.eq("biscuit")).will(
            pmock.return_value("bark"))
        self.assert_(mock.proxy().dog("bone", food="biscuit"), "bark")
            
    
class MockMultipleMethodsTest(unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expects(pmock.once()).method("cat")
        self.mock.expects(pmock.once()).method("cat").taking(pmock.eq("mouse"))

    def test_method_lifo_order(self):
         self.mock.proxy().cat("mouse")
         self.mock.proxy().cat()
         self.mock.verify()

    def test_uncalled_method(self):
        self.mock.proxy().cat()
        try:
            self.mock.verify()
            self.fail()
        except pmock.VerificationError:
            pass


class SpecialMethodsTest(pmock.MockTestCase):

    def test_expected_specials(self):
        class Test(pmock.MockTestCase):
            def test_method(self):
                self.special = self.mock()
                self.special.expects(pmock.once()).__cmp__(pmock.eq("guppy")).\
                    will(pmock.return_value(0))
                self.special.expects(pmock.once()).__call__(pmock.eq("blub"),
                                                            pmock.eq("blub"))
                self.special == "guppy"
                self.special("blub", "blub")
        test = Test('test_method')
        result = unittest.TestResult()
        test(result)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 0)

    def test_unexpected_specials(self):
        class Test(pmock.MockTestCase):
            def test_method(self):
                self.special = self.mock()
                self.special == "guppy"
        test = Test('test_method')
        result = unittest.TestResult()
        test(result)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(len(result.errors), 0)


class CallMockDirectlyTest(unittest.TestCase):

    def test_call_mock_rather_than_proxy(self):
        self.mock = pmock.Mock()
        self.mock.expects(pmock.once()).method("newt")
        self.mock.newt()
        self.mock.verify()


class FifoExpectationTest(unittest.TestCase):

    def test_method_fifo_order(self):
        self.mock = pmock.Mock()
        self.mock.expects(pmock.once()).method("cat").taking(pmock.eq("mouse"))
        self.mock.expects(pmock.once()).method("cat")
        self.mock.proxy().cat(food="mouse")
        try:
            self.mock.proxy().cat()
            self.fail()
        except pmock.MatchError:
            pass


class OnceTest(unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expects(pmock.once()).method("rabbit")

    def test_uncalled(self):
        try:
            self.mock.verify()
        except pmock.VerificationError:
            pass

    def test_call_once(self):
        self.mock.proxy().rabbit()
        self.mock.verify()

    def test_call_too_many(self):
        self.mock.proxy().rabbit()
        try:
            self.mock.proxy().rabbit()
            self.fail()
        except pmock.MatchError:
            pass


class AtLeastOnceTest(unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expects(pmock.at_least_once()).method("rabbit")

    def test_uncalled(self):
        try:
            self.mock.verify()
        except pmock.VerificationError:
            pass

    def test_call_once(self):
        self.mock.proxy().rabbit()
        self.mock.verify()

    def test_call_many(self):
        self.mock.proxy().rabbit()
        self.mock.proxy().rabbit()
        self.mock.proxy().rabbit()
        self.mock.proxy().rabbit()
        self.mock.verify()


class NeverTest(unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expects(pmock.never()).method("rabbit")

    def test_uncalled(self):
        self.mock.verify()

    def test_called(self):
        try:
            self.mock.proxy().rabbit()
            self.fail()
        except pmock.MatchError:
            pass


class OrderedCallsBasicTest(unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expects(pmock.once()).method("bull").id("bull call")
        self.mock.expects(pmock.once()).method("cow").after("bull call")

    def test_call_in_order(self):
        self.mock.proxy().bull()
        self.mock.proxy().cow()
        self.mock.verify()

    def test_call_out_of_order_doesnt_match(self):
        try:
            self.mock.proxy().cow()
            self.fail()
        except pmock.MatchError:
            pass
            

class OrderedCallsAcrossMocksTest(unittest.TestCase):

    def setUp(self):
        self.mock1 = pmock.Mock("field")
        self.mock2 = pmock.Mock()
        self.mock1.expects(pmock.once()).method("bull").id("bovine")
        self.mock2.expects(pmock.once()).method("cow").after("bovine",
                                                             self.mock1)

    def test_call_in_order(self):
        self.mock1.proxy().bull()
        self.mock2.proxy().cow()
        self.mock1.verify()
        self.mock2.verify()
        
    def test_call_out_of_order_doesnt_match(self):
        try:
            self.mock2.proxy().cow()
            self.fail()
        except pmock.MatchError:
            pass


class OrderedCallsAdditionalTest(testsupport.ErrorMsgAssertsMixin,
                                 unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()

    def test_method_name_as_id(self):
        self.mock.expects(pmock.once()).method("bull")
        self.mock.expects(pmock.once()).method("cow").after("bull")
        self.mock.proxy().bull()
        self.mock.proxy().cow()
        self.mock.verify()

    def test_method_name_as_id_binds_to_last_matching_expectation(self):
        self.mock.expects(pmock.once()).method("cow").taking(pmock.eq("moo"))
        self.mock.expects(pmock.once()).method("cow").taking(pmock.eq("mooo"))
        self.mock.expects(pmock.once()).method("bull").after("cow")
        self.mock.proxy().cow("mooo")
        self.mock.proxy().bull()
        self.mock.proxy().cow("moo")
        self.mock.verify()

    def test_after_undefined_id_raises(self):
        try:
            self.mock.expects(pmock.once()).method("cow").after("ox")
            self.fail()
        except pmock.DefinitionError, err:
            self.assertUndefinedIdMsg(err.msg, "ox")

    def test_disallow_duplicate_ids(self):
        self.mock.expects(pmock.once()).method("cow").id("bovine")
        try:
            self.mock.expects(pmock.once()).method("bull").id("bovine")
            self.fail()
        except pmock.DefinitionError, err:
            self.assertDuplicateIdMsg(err.msg, "bovine")

    def test_disallow_duplicating_id_of_existing_method(self):
        self.mock.expects(pmock.once()).method("cow")
        try:
            self.mock.expects(pmock.once()).method("bovine").id("cow")
            self.fail()
        except pmock.DefinitionError, err:
            self.assertDuplicateIdMsg(err.msg, "cow")


class StubTest(unittest.TestCase):

    def test_specified_like_expectations(self):
        mock = pmock.Mock()
        mock.stubs().method("fox")
        mock.stubs().method("fox").taking_at_least("sly")
        mock.stubs().method("fox").taking("sly", meal="chicken")
        mock.stubs().method("fox").will(pmock.return_value("trot"))
        self.assertEqual(mock.proxy().fox(), "trot")
        mock.fox("sly", meal="chicken")
        mock.fox("sly")
        mock.fox()

    def test_uninvoked_doesnt_raise_verify(self):
        mock = pmock.Mock()
        mock.stubs().method("fox")
        mock.verify()

    def test_expectation_can_use_for_ordering(self):
        mock = pmock.Mock()
        mock.stubs().method("fox")
        mock.expects(pmock.once()).method("farmer").after("fox")
        mock.fox()
        mock.farmer()

    def test_set_default_stub(self):
        mock = pmock.Mock()
        mock.set_default_stub(pmock.return_value("trot"))
        self.assertEqual(mock.fox(), "trot")


class ErrorMessageTest(unittest.TestCase):

    def test_expected_method_not_invoked(self):
        mock = pmock.Mock()
        mock.expects(pmock.once()).ant()
        try:
            mock.verify()
        except pmock.VerificationError, err:
            self.assertEqual(
                err.msg,
                "expected method was not invoked: expected once: ant()")

    def test_unmatched_method(self):
        mock = pmock.Mock()
        mock.stubs().mite(looks=pmock.eq("creepy"))
        mock.expects(pmock.once()).termite()
        mock.termite()
        try:
            mock.ant()
        except pmock.MatchError, err:
            self.assertEqual(err.msg,
                             "no match found\n"
                             "invoked ant()\n"
                             "in:\n"
                             "stub: mite(looks=pmock.eq('creepy')),\n"
                             "expected once and has been invoked: termite()")

    def test_conflicting_method(self):
        mock = pmock.Mock()
        mock.expects(pmock.never()).cockroach()
        try:
            mock.cockroach()
        except pmock.MatchError, err:
            self.assertEqual(err.msg,
                             "expected method to never be invoked\n"
                             "invoked cockroach()\n"
                             "in:\n"
                             "expected not to be called: cockroach()")


class MockTestCaseTest(unittest.TestCase):

    def test_verify_unsatisfied_expectation(self):
        class Test(pmock.MockTestCase):
            def test_method(self):
                mock = self.mock()
                mock.expects(pmock.once()).crow()
        test = Test('test_method')
        result = unittest.TestResult()
        test(result)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(len(result.errors), 0)
        traceback = result.failures[0][1]
        self.assert_(traceback.find('VerificationError') != -1)

    def test_verify_satisfied_expectation(self):
        class Test(pmock.MockTestCase):
            def test_method(self):
                mock = self.mock()
                mock.expects(pmock.once()).crow()
                mock.crow()
        test = Test('test_method')
        result = unittest.TestResult()
        test(result)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 0)

        
if __name__ == '__main__':
    unittest.main()
