from twisted.trial.unittest import TestCase
from twisted.protocols import amp, loopback

from grace.plumbing import Plumber
from grace.control import Control



class ControlTest(TestCase):


    def test_AMP(self):
        """
        Should be an AMP factory
        """
        self.assertTrue(issubclass(Control, amp.AMP))


    def test_init(self):
        """
        Should accept a Plumber
        """
        p = Plumber()
        c = Control(p)
        self.assertEqual(c.plumber, p)


    def assertCallsThrough(self, method, plumber_method, *args, **kwargs):
        """
        Assert that calling the L{Control}'s C{method} method will result
        in a call on the C{plumber_method} with the given arguments.
        """
        p = Plumber()
        called = []
        def fake(*a, **kw):
            called.append((a, kw))
            return 'result'
        setattr(p, plumber_method, fake)
        
        c = Control(p)
        r = getattr(c, method)(*args, **kwargs)
        self.assertEqual(called, [(args, kwargs)], "Calling Control.%s with "
                         "%r and %r should have resulted in a call to "
                         "Plumber.%s with the same args and kwargs" % (
                            method, args, kwargs, plumber_method
                         ))


    def test_addPipe(self):
        self.assertCallsThrough('addPipe', 'addPipe', 'foo', 'bar')


    def test_rmPipe(self):
        self.assertCallsThrough('rmPipe', 'rmPipe', 'foo', 'bar')