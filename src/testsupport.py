class ErrorMsgAssertsMixin:

    def assertUndefinedLabelMsg(self, msg, label):
        self.assertEqual(msg, "reference to undefined label: %s" % label)

    def assertDuplicateLabelMsg(self, msg, label, mocker):
        self.assertEqual(msg,
                         "label: %s is already defined by: %s" %
                         (label, mocker))
