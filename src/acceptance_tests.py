import unittest

import pmock
import testsupport


class MockMethodTest(testsupport.ErrorMsgAssertsMixin, unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expect(pmock.once()).method("dog")
        
    def test_uncalled_method(self):
        try:
            self.mock.verify()
            self.fail()
        except pmock.VerificationError, err:
            self.assertUnsatisfiedMsg(err.msg, ["once dog(...)"])

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
            self.assertUnexpectedCallMsg(err.msg, "cat()", ["once dog(...)"])

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
            self.assertUnsatisfiedMsg(err.msg, ["once dog(pmock.eq('bone'))"])

    def test_method_with_correct_arg(self):
        self.mock.proxy().dog("bone")
        self.mock.verify()

    def test_call_method_with_incorrect_arg(self):
        try:
            self.mock.proxy().dog("carrot")
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "dog('carrot')",
                                         ["once dog(pmock.eq('bone'))"])

    def test_call_method_with_insufficient_args(self):
        try:
            self.mock.proxy().dog()
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "dog()",
                                         ["once dog(pmock.eq('bone'))"])

    def test_method_with_correct_arg_and_extras(self):
        self.mock.proxy().dog("bone", "biscuit")
        self.mock.verify()


class MockMethodWithArgTest(MockMethodWithArgTestMixin,
                            testsupport.ErrorMsgAssertsMixin,
                            unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expect(pmock.once()).method("dog").with(pmock.eq("bone"))

    def test_method_with_correct_arg_and_extras(self):
        try:
            self.mock.proxy().dog("bone", "biscuit")
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "dog('bone', 'biscuit')",
                                         ["once dog(pmock.eq('bone'))"])


class MockMethodWithAtLeastArgTest(MockMethodWithArgTestMixin,
                                   testsupport.ErrorMsgAssertsMixin,
                                   unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expect(pmock.once()).method("dog").with_at_least(
            pmock.eq("bone"))

    def test_method_with_correct_arg_and_extras(self):
        self.mock.proxy().dog("bone", "biscuit")
        self.mock.verify()


class MockMethodWithArgsTest(testsupport.ErrorMsgAssertsMixin,
                             unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.toys = ["ball", "stick"]
        self.mock.expect(pmock.once()).method("dog").with(
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
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "dog('bone', 'biscuit')",
                              ["once dog(pmock.eq('bone'), "
                               "pmock.same(['ball', 'stick']), "
                               "pmock.string_contains('slipper'))"])


class MockMethodWithKeywordArgTestMixin(object):
    
    def test_uncalled_method(self):
        try:
            self.mock.verify()
            self.fail()
        except pmock.VerificationError, err:
            self.assertUnsatisfiedMsg(err.msg,
                                      ["once dog(food=pmock.eq('bone'))"])

    def test_method_with_correct_arg(self):
        self.mock.proxy().dog(food="bone")
        self.mock.verify()

    def test_call_method_with_incorrect_arg(self):
        try:
            self.mock.proxy().dog(food="ball")
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "dog(food='ball')",
                                         ["once dog(food=pmock.eq('bone'))"])

    def test_call_method_with_missing_arg(self):
        try:
            self.mock.proxy().dog(toy="ball")
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "dog(toy='ball')",
                                         ["once dog(food=pmock.eq('bone'))"])


class MockMethodWithKeywordArgTest(MockMethodWithKeywordArgTestMixin,
                                   testsupport.ErrorMsgAssertsMixin,
                                   unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expect(pmock.once()).method("dog").with(
            food=pmock.eq("bone"))

    def test_method_with_correct_arg_and_extra(self):
        try:
            self.mock.proxy().dog(toy="ball", food="bone")
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg,
                                         "dog(food='bone', toy='ball')",
                                         ["once dog(food=pmock.eq('bone'))"])


class MockMethodWithAtLeastKeywordArgTest(MockMethodWithKeywordArgTestMixin,
                                          testsupport.ErrorMsgAssertsMixin,
                                          unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expect(pmock.once()).method("dog").with_at_least(
            food=pmock.eq("bone"))

    def test_method_with_correct_arg_and_extra(self):
        self.mock.proxy().dog(toy="ball", food="bone")
        self.mock.verify()


class MockMethodWithNoArgsTest(testsupport.ErrorMsgAssertsMixin,
                               unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expect(pmock.once()).method("dog").no_args()

    def test_method_with_no_args(self):
        self.mock.proxy().dog()
        self.mock.verify()

    def test_method_with_args(self):
        try:
            self.mock.proxy().dog("biscuit")
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "dog('biscuit')",
                                         ["once dog()"])

    def test_method_with_kwargs(self):
        try:
            self.mock.proxy().dog(toy="ball")
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "dog(toy='ball')",
                                         ["once dog()"])


class MockMethodWillTest(testsupport.ErrorMsgAssertsMixin, unittest.TestCase):

    def test_method_will_return_value(self):
        self.mock = pmock.Mock()
        self.mock.expect(pmock.once()).method("dog").will(
            pmock.return_value("bone"))
        self.assertEqual(self.mock.proxy().dog(), "bone")

    def test_method_is_void(self):
        self.mock = pmock.Mock()
        self.mock.expect(pmock.once()).method("dog").is_void()
        self.assertEqual(self.mock.proxy().dog(), None)

    def test_method_will_raise_exception(self):
        self.mock = pmock.Mock()
        custom_err = RuntimeError()
        self.mock.expect(pmock.once()).method("dog").will(
            pmock.raise_exception(custom_err))
        try:
            self.mock.proxy().dog()
            self.fail()
        except RuntimeError, err:
            self.assert_(err is custom_err)
            self.mock.verify()


class MockMultipleMethodsTest(testsupport.ErrorMsgAssertsMixin,
                              unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expect(pmock.once()).method("cat")
        self.mock.expect(pmock.once()).method("cat").with(pmock.eq("mouse"))

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
            self.assertUnsatisfiedMsg(err.msg, ["once cat(pmock.eq('mouse'))"])


class FifoExpectationTest(testsupport.ErrorMsgAssertsMixin,
                          unittest.TestCase):

    # Currently expectations are matched in a LIFO manner which may be
    # surprising
    
    def test_method_fifo_order(self):
        self.mock = pmock.Mock()
        self.mock.expect(pmock.once()).method("cat").with(pmock.eq("mouse"))
        self.mock.expect(pmock.once()).method("cat")
        self.mock.proxy().cat(food="mouse")
        try:
            self.mock.proxy().cat()
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "cat()",
                                         ["once cat(pmock.eq('mouse'))"])


class OnceCallTest(testsupport.ErrorMsgAssertsMixin, unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expect(pmock.once()).method("rabbit")

    def test_uncalled(self):
        try:
            self.mock.verify()
        except pmock.VerificationError, err:
            self.assertUnsatisfiedMsg(err.msg, ["once rabbit(...)"])

    def test_call_once(self):
        self.mock.proxy().rabbit()
        self.mock.verify()

    def test_call_too_many(self):
        self.mock.proxy().rabbit()
        try:
            self.mock.proxy().rabbit()
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "rabbit()", [])


class AtLeastOnceCallTest(testsupport.ErrorMsgAssertsMixin,
                          unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expect(pmock.at_least_once()).method("rabbit")

    def test_uncalled(self):
        try:
            self.mock.verify()
        except pmock.VerificationError, err:
            self.assertUnsatisfiedMsg(err.msg, ["at least once rabbit(...)"])

    def test_call_once(self):
        self.mock.proxy().rabbit()
        self.mock.verify()

    def test_call_many(self):
        self.mock.proxy().rabbit()
        self.mock.proxy().rabbit()
        self.mock.proxy().rabbit()
        self.mock.proxy().rabbit()
        self.mock.verify()


class NotCalledCallTest(testsupport.ErrorMsgAssertsMixin, unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.mock.expect(pmock.not_called()).method("rabbit")

    def test_uncalled(self):
        self.mock.verify()

    def test_called(self):
        try:
            self.mock.proxy().rabbit()
            self.fail()
        except pmock.MatchError, err:
            self.assertConflictedCallMsg(err.msg, "rabbit()",
                                         "not called rabbit(...)")


class OrderedCallsBasicTest(testsupport.ErrorMsgAssertsMixin,
                            pmock.MockTestCase):

    def setUp(self):
        pmock.MockTestCase.setUp(self)
        self.mock = pmock.Mock()
        self.mock.expect(pmock.once()).method("bull").label("bull call")
        self.mock.expect(pmock.once()).method("cow").after("bull call")

    def test_call_in_order(self):
        self.mock.proxy().bull()
        self.mock.proxy().cow()
        self.mock.verify()

    def test_call_out_of_order_doesnt_match(self):
        try:
            self.mock.proxy().cow()
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "cow()",
                                         ["once cow(...).after('bull call')",
                                          "once bull(...).label('bull call')"])
            

class OrderedCallsAcrossMocksTest(testsupport.ErrorMsgAssertsMixin,
                                  pmock.MockTestCase):

    def setUp(self):
        pmock.MockTestCase.setUp(self)
        self.mock1 = pmock.Mock()
        self.mock2 = pmock.Mock()
        self.mock1.expect(pmock.once()).method("bull").label("bull call")
        self.mock2.expect(pmock.once()).method("cow").after("bull call")

    def test_call_in_order(self):
        self.mock1.proxy().bull()
        self.mock2.proxy().cow()
        self.mock1.verify()
        self.mock2.verify()
        
    def test_call_out_of_order_doesnt_match(self):
        try:
            self.mock2.proxy().cow()
            self.fail()
        except pmock.MatchError, err:
            self.assertUnexpectedCallMsg(err.msg, "cow()",
                                         ["once cow(...).after('bull call')"])


class OrderedCallsAdditionalTest(testsupport.ErrorMsgAssertsMixin,
                                 pmock.MockTestCase):

    def setUp(self):
        self.mock = pmock.Mock()

    def test_method_name_as_label(self):
        self.mock.expect(pmock.once()).method("bull")
        self.mock.expect(pmock.once()).method("cow").after("bull")
        self.mock.proxy().bull()
        self.mock.proxy().cow()
        self.mock.verify()

    def test_method_name_as_label_binds_to_last_matching_expectation(self):
        self.mock.expect(pmock.once()).method("cow").with(pmock.eq("moo"))
        self.mock.expect(pmock.once()).method("cow").with(pmock.eq("mooo"))
        self.mock.expect(pmock.once()).method("bull").after("cow")
        self.mock.proxy().cow("mooo")
        self.mock.proxy().bull()
        self.mock.proxy().cow("moo")
        self.mock.verify()

    def test_after_undefined_label_raises(self):
        try:
            self.mock.expect(pmock.once()).method("cow").after("ox")
            self.fail()
        except pmock.DefinitionError, err:
            self.assertUndefinedLabelMsg(err.msg, "ox")

    def test_disallow_duplicate_labels(self):
        self.mock.expect(pmock.once()).method("cow").label("bovine")
        try:
            self.mock.expect(pmock.once()).method("bull").label("bovine")
            self.fail()
        except pmock.DefinitionError, err:
            self.assertDuplicateLabelMsg(err.msg, "bovine",
                                         "once cow(...).label('bovine')")

    def test_disallow_duplicating_label_of_existing_method(self):
        self.mock.expect(pmock.once()).method("cow")
        try:
            self.mock.expect(pmock.once()).method("bovine").label("cow")
            self.fail()
        except pmock.DefinitionError, err:
            self.assertDuplicateLabelMsg(err.msg, "cow", "once cow(...)")


class StubTest(unittest.TestCase):

    def test_specified_like_expectations(self):
        mock = pmock.Mock()
        mock.stub().method("fox")
        mock.stub().method("fox").with_at_least("sly")
        mock.stub().method("fox").with("sly", meal="chicken")
        mock.stub().method("fox").will(pmock.return_value("trot"))
        self.assertEqual(mock.proxy().fox(), "trot")
        mock.proxy().fox("sly", meal="chicken")
        mock.proxy().fox("sly")
        mock.proxy().fox()

    def test_uninvoked_doesnt_raise_verify(self):
        mock = pmock.Mock()
        mock.stub().method("fox")
        mock.verify()

    def test_expectation_can_use_for_ordering(self):
        mock = pmock.Mock()
        mock.stub().method("fox")
        mock.expect(pmock.once()).method("farmer").after("fox")
        mock.proxy().fox()
        mock.proxy().farmer()


if __name__ == '__main__':
    unittest.main()
