class ErrorMsgAssertsMixin:

    def assertUndefinedIdMsg(self, msg, label):
        self.assertEqual(msg, "reference to undefined id: %s" % label)

    def assertDuplicateIdMsg(self, msg, builder_id):
        self.assertEqual(msg, "id: %s is already defined" % builder_id)
