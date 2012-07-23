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


    def test_addPipe(self):
        """
        Should call the plumber's addPipe method
        """
        p = Plumber()
        called = []
        p.addPipe = lambda *a: called.append(a)
        
        c = Control(p)
        src = 'unix:'+self.mktemp()
        dst = 'unix:path='+self.mktemp()
        c.addPipe(src, dst)
        self.assertEqual(called, [(src, dst)], "Should have called addPipe on"
                         " the Plumber")