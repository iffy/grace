from twisted.trial.unittest import TestCase
from twisted.protocols import amp, loopback

from grace.plumbing import Plumber
from grace.control import Server, Client



class FakePlumber(Plumber):


    def __init__(self, results=None):
        self.called = []
        self._results = results or {}


    def addPipe(self, src, dst):
        self.called.append(('addPipe', src, dst))
        return self._results.get('addPipe', None)


    def rmPipe(self, src):
        self.called.append(('rmPipe', src))
        return self._results.get('rmPipe', None)


    def pipeCommand(self, key, cmd, *args, **kwargs):
        self.called.append(('pipeCommand', key, cmd, args, kwargs))
        return self._results.get('pipeCommand', None)



class ServerTest(TestCase):


    def test_AMP(self):
        """
        Should be an AMP factory
        """
        self.assertTrue(issubclass(Server, amp.AMP))


    def test_init(self):
        """
        Should accept a Plumber
        """
        p = Plumber()
        c = Server(p)
        self.assertEqual(c.plumber, p)


    def test_addPipe(self):
        """
        addPipe should mirror plumber.addPipe
        """
        c = Server(FakePlumber())
        c.addPipe('foo', 'bar')
        self.assertEqual(c.plumber.called, [
            ('addPipe', 'foo', 'bar'),
        ])


    def test_rmPipe(self):
        """
        rmPipe should mirror plumber.rmPipe
        """
        c = Server(FakePlumber())
        c.rmPipe('foo')
        self.assertEqual(c.plumber.called, [
            ('rmPipe', 'foo'),
        ])


    def test_switch(self):
        """
        Switching should switch a Pipe's destination.
        """
        c = Server(FakePlumber())
        c.switch('foo', 'dst2')
        self.assertEqual(c.plumber.called, [
            ('pipeCommand', 'foo', 'switch', ('dst2',), {}),
        ])


