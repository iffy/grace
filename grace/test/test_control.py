from twisted.trial.unittest import TestCase
from twisted.protocols import amp, loopback
from twisted.internet.protocol import Factory
from twisted.internet import defer

from grace.plumbing import Plumber
from grace.control import Server, ServerFactory
from grace.control import AddPipe, RemovePipe, Switch, Stop, List, Wait



class FakePlumber(Plumber):


    def __init__(self, results=None):
        Plumber.__init__(self)
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


    def stop(self):
        self.called.append('stop')
        return self._results.get('stop', None)


    def ls(self):
        self.called.append('ls')
        return self._results.get('ls', None)



class ServerFactoryTest(TestCase):


    def test_protocol(self):
        self.assertTrue(issubclass(ServerFactory, Factory))
        self.assertEqual(ServerFactory.protocol, Server)


    def test_buildProtocol(self):
        """
        Should give the protocol a Plumber
        """
        plumber = object()
        factory = ServerFactory(plumber)
        proto = factory.buildProtocol('foo')
        self.assertEqual(proto.factory, factory)
        self.assertEqual(proto.plumber, plumber)



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


    def test_stop(self):
        """
        Stop should mirror plumber.stop
        """
        c = Server(FakePlumber())
        c.stop()
        self.assertEqual(c.plumber.called, ['stop'])


    def test_ls(self):
        """
        ls should call through to the plumber and return a dictionary ready
        for AMP
        """
        c = Server(FakePlumber({
            'ls': [
                ('foo', 'thing1', 0, True),
                ('bar', 'thing2', 1, False),
                ('bar', 'thing3', 12, True),
            ]
        }))
        r = c.ls()
        self.assertEqual(r['pipes'], [
            {
                'src': 'foo',
                'dst': 'thing1',
                'conns': 0,
                'active': True,
            },
            {
                'src': 'bar',
                'dst': 'thing2',
                'conns': 1,
                'active': False,
            },
            {
                'src': 'bar',
                'dst': 'thing3',
                'conns': 12,
                'active': True,
            },
        ])


    def test_wait(self):
        """
        Wait should wait
        """
        ret = defer.Deferred()
        c = Server(FakePlumber({
            'pipeCommand': ret,
        }))
        r = c.wait('foo')
        self.assertEqual(c.plumber.called, [
            ('pipeCommand', 'foo', 'wait', (), {}),
        ])
        self.assertFalse(r.called)
        ret.callback(None)        
        def check(response):
            self.assertEqual(response, {})
        return r.addCallback(check)



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


    def test_Stop(self):
        """
        You can stop the whole server.
        """
        server = Server(FakePlumber())
        client = SingleCommandClient(Stop)

        from twisted.protocols.loopback import loopbackAsync
        def check(response):
            self.assertEqual(server.plumber.called, ['stop'])
        r = loopbackAsync(server, client)
        return r.addCallback(check)


    def test_List(self):
        """
        You can get a listing
        """
        server = Server(FakePlumber({
            'ls': [
                ('foo', 'bar', 12, True),
            ]
        }))
        client = SingleCommandClient(List)

        from twisted.protocols.loopback import loopbackAsync
        def check(response):
            self.assertEqual(server.plumber.called, ['ls'])
            self.assertEqual(client.response, {
                'pipes': [
                    {
                        'src': 'foo',
                        'dst': 'bar',
                        'conns': 12,
                        'active': True,
                    },
                ]
            })
        r = loopbackAsync(server, client)
        return r.addCallback(check)


    def test_Wait(self):
        """
        You can wait for connections to settle.
        """
        wait_ret = defer.Deferred()
        server = Server(FakePlumber({
            'pipeCommand': wait_ret,
        }))
        client = SingleCommandClient(Wait, src='foo')
        
        from twisted.protocols.loopback import loopbackAsync
        def check(response):
            self.assertEqual(server.plumber.called, [
                ('pipeCommand', 'foo', 'wait', (), {}),
            ])
        r = loopbackAsync(server, client)
        self.assertFalse(r.called)
        wait_ret.callback(None)
        return r.addCallback(check)
        

