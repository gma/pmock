import unittest

import pmock


class SystemError(Exception):

    def __init__(self, msg):
        self.msg = msg


class Greeting:

    def __init__(self, system):
        self._system = system

    def message(self):
        try:
            (hours, seconds) = self._system.time()
            if hours < 12:
                return "Good morning"
            elif hours >= 12 and hours < 19:
                return "Good afternoon"
            else:
                return "Good evening"
        except SystemError, err:
            self._system.log("time problem: %s" % err.msg)
            return "Good day"


class GreetingTest(unittest.TestCase):

    def setUp(self):
        self.mock = pmock.Mock()
        self.greeting = Greeting(self.mock.proxy())

    def tearDown(self):
        self.mock.verify()

    def test_afternoon(self):
        self.mock.expect().method("time").will(pmock.return_value((12,10)))
        self.assertEqual(self.greeting.message(), "Good afternoon")

    def test_morning(self):
        self.mock.expect().method("time").will(pmock.return_value((6,50)))
        self.assertEqual(self.greeting.message(), "Good morning")

    def test_evening(self):
        self.mock.expect().method("time").will(pmock.return_value((19,50)))
        self.assertEqual(self.greeting.message(), "Good evening")

    def test_clock_failure(self):
        err_msg = "bzzz..malfunction"
        err = SystemError(err_msg)
        self.mock.expect().method("time").will(pmock.throw_exception(err))
        self.mock.expect().method("log").with(pmock.string_contains(err_msg))
        self.assertEqual(self.greeting.message(), "Good day")
        

if __name__ == "__main__":
    unittest.main()
    
        
                                                
