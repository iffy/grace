from twisted.trial.unittest import TestCase
from twisted.protocols import amp, loopback
from twisted.internet.protocol import Factory

from grace.plumbing import Plumber
from grace.control import Server, AddPipe, RemovePipe, Switch, ServerFactory



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



class ServerFactoryTest(TestCase):


    def test_protocol(self):
        self.assertTrue(issubclass(ServerFactory, Factory))
        self.assertEqual(ServerFactory.protocol, Server)



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



class SingleCommandClient(amp.AMP):
    
        def __init__(self, cmd, *args, **kwargs):
            amp.AMP.__init__(self)
            self.cmd = cmd
            self.args = args
            self.kwargs = kwargs
            self.response = None


        def connectionMade(self):
            amp.AMP.connectionMade(self)
            d = self.callRemote(self.cmd, *self.args, **self.kwargs)
            return d.addCallback(self.gotResponse)


        def gotResponse(self, response):
            self.response = response
            self.transport.loseConnection()
            return response



class ClientTest(TestCase):


    timeout = 3


    def test_AddPipe(self):
        """
        You can add a pipe.
        """
        server = Server(FakePlumber())
        client = SingleCommandClient(AddPipe, src='foo', dst='bar')

        from twisted.protocols.loopback import loopbackAsync
        def check(response):
            self.assertEqual(server.plumber.called, [
                ('addPipe', 'foo', 'bar'),
            ])
        r = loopbackAsync(server, client)
        return r.addCallback(check)


    def test_RemovePipe(self):
        """
        You can remove a pipe.
        """
        server = Server(FakePlumber())
        client = SingleCommandClient(RemovePipe, src='foo')

        from twisted.protocols.loopback import loopbackAsync
        def check(response):
            self.assertEqual(server.plumber.called, [
                ('rmPipe', 'foo'),
            ])
        r = loopbackAsync(server, client)
        return r.addCallback(check)        


    def test_Switch(self):
        """
        You can switch forwarding
        """
        server = Server(FakePlumber())
        client = SingleCommandClient(Switch, src='foo', dst='bar')

        from twisted.protocols.loopback import loopbackAsync
        def check(response):
            self.assertEqual(server.plumber.called, [
                ('pipeCommand', 'foo', 'switch', ('bar',), {}),
            ])
        r = loopbackAsync(server, client)
        return r.addCallback(check) 

