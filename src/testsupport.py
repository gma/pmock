import unittest


class ErrorMsgAssertsMixin:

    def assertUnsatisfiedMsg(self, msg, unsatisfied_strs):
        self.assertEqual(msg, "unsatisfied expectation(s): %s" %
                         ", ".join(unsatisfied_strs))

    def assertUnexpectedCallMsg(self, msg, call_str, expectation_strs):
        if len(expectation_strs) > 0:
            self.assertEqual(msg, "unexpected call %s, expectation(s): %s" %
                             (call_str, ", ".join(expectation_strs)))
        else:
            self.assertEqual(msg, "unexpected call %s, no expectations "
                             "remaining" % call_str)

    def assertConflictedCallMsg(self, msg, call_str, conflicted_str):
        self.assertEqual(msg, "call %s, conflicts with expectation: %s" %
                         (call_str, conflicted_str))
