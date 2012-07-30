from twisted.trial.unittest import TestCase
from twisted.internet import reactor, defer, task, endpoints
from twisted.python import log


from grace.test.util import YippyYuckFactory, ClientFactory
from grace.pipe import Pipe
        


class PipeTest(TestCase):


    timeout = 1


    @defer.inlineCallbacks
    def startServer(self, endpoint, expected_data):
        """
        Create a server that will expect some data.  The server will be torn
        down after the test.
        
        @param endpoint: The endpoint to listen on
        
        @param expected_data: A list of expected_data, 1 string for each
            Protocol you expected to be created.
        
        @return: a L{YippyYuckFactory} instance.
        """
        server = YippyYuckFactory(expected_data)
        ep = endpoints.serverFromString(reactor, endpoint)
        port = yield ep.listen(server)
        self.addCleanup(port.stopListening)
        defer.returnValue(server)


    @defer.inlineCallbacks
    def connectClient(self, endpoint, expected_data):
        """
        Create a client.
        
        @param endpoint: Endpoint to connect to
        
        @param expected_data: A single string of data this client expects to
            get back from the server.
            
        @return: a L{YippyYuckProtocol} instance.
        """
        clientf = ClientFactory(expected_data)
        client_ep = endpoints.clientFromString(reactor, endpoint)
        client = yield client_ep.connect(clientf)
        self.addCleanup(client.transport.loseConnection)
        defer.returnValue(client)


    @defer.inlineCallbacks
    def t_endpoints(self, client, pfserver, pfclient, server):
        """
        Test that forwarding works from C{client} to C{pfserver}
        using C{pfclient} to C{server}
        """
        # set up service we're forwarding to.
        server = yield self.startServer(server, ['hey'])
        
        # start Pipe
        pipe = Pipe(pfclient)
        pipe_ep = endpoints.serverFromString(reactor, pfserver)
        pipe_port = yield pipe_ep.listen(pipe)
        self.addCleanup(pipe_port.stopListening)
        
        # start a client to test
        client = yield self.connectClient(client, 'hey back')

        # send some data forward and back
        client.transport.write('hey')
        server_proto = yield server.connected(0)
        server_received = yield server_proto.satisfied
        
        server_proto.transport.write('hey back')
        client_received = yield client.satisfied


    def test_TCP_to_TCP(self):
        return self.t_endpoints(
            'tcp:host=127.0.0.1:port=10333',
            'tcp:10333',
            'tcp:host=127.0.0.1:port=10111',
            'tcp:10111',
        )


    def test_TCP_to_UNIX(self):
        socket = self.mktemp()
        return self.t_endpoints(
            'tcp:host=127.0.0.1:port=10333',
            'tcp:10333',
            'unix:path=%s' % socket,
            'unix:%s' % socket,
        )


    def test_UNIX_to_TCP(self):
        socket = self.mktemp()
        return self.t_endpoints(
            'unix:path=%s' % socket,
            'unix:%s' % socket,
            'tcp:host=127.0.0.1:port=10333',
            'tcp:10333',
        )


    def test_UNIX_to_UNIX(self):
        socket1 = self.mktemp()
        socket2 = self.mktemp()
        return self.t_endpoints(
            'unix:path=%s' % socket1,
            'unix:%s' % socket1,
            'unix:path=%s' % socket2,
            'unix:%s' % socket2,
        )


    @defer.inlineCallbacks
    def test_switch(self):
        """
        Switching the forwarder to a different endpoint will make all future
        connections use that endpoint.  When all existing connections through
        the first forwarding are done a deferred will fire.
        """
        socket1 = self.mktemp()
        server1 = yield self.startServer('unix:'+socket1, ['hey1hey3'])
        socket2 = self.mktemp()
        server2 = yield self.startServer('unix:'+socket2, ['hey2'])

        # pipe
        pipesocket = self.mktemp()
        pipe = Pipe('unix:path=' + socket1)
        pipe_ep = endpoints.serverFromString(reactor, 'unix:'+pipesocket)
        pipe_port = yield pipe_ep.listen(pipe)
        self.addCleanup(pipe_port.stopListening)
        
        # client1
        client1 = yield self.connectClient('unix:path='+pipesocket, '')

        # send some data from client1
        client1.transport.write('hey1')
        server1_proto = yield server1.connected(0)
        
        # switch to new endpoint
        r = pipe.switch('unix:path=' + socket2)
        r2 = pipe.alive['unix:path=' + socket1]
        self.assertEqual(r, r2, "The Deferred returned by the switch command "
                         "should be the same one that's accessible in the "
                         "alive dict.")

        # client2
        client2 = yield self.connectClient('unix:path='+pipesocket, '')
        
        # send some data from client2
        client2.transport.write('hey2')
        server2_proto = yield server2.connected(0)
        yield server2_proto.satisfied
        
        # send more data from client1
        client1.transport.write('hey3')
        yield server1_proto.satisfied
        
        # disconnect client1
        self.assertFalse(r2.called, "There is still a connection, so the "
                 "forwarding is still alive")
        yield client1.transport.loseConnection()
        dead_notice = yield r2
        self.assertEqual(dead_notice, 'unix:path=' + socket1, "The Deferred "
                         "should have fired back with the endpoint that just "
                         "disconnected.")


    def test_noswitch_nocallback(self):
        """
        If the Pipe is still forwarding to an endpoint, the
        alive Deferred should not fire even when the last 
        connection is done.
        """
        p = Pipe('foo')
        proto1 = object()
        p.addConnection('foo', proto1)
        p.removeConnection('foo', proto1)
        d = p.alive['foo']
        self.assertEqual(d.called, False, "Should not have called "
                         "the Deferred because it's still "
                         "forwarding to that endpoint")


    def test_switch_back(self):
        """
        If you switch forwarding to one dst, then switch back, the original
        destination's Deferred should not fire, but the intermediate destination
        should.
        """
        # X -> foo
        p = Pipe('foo')
        foo_d = p.alive['foo'] 
        proto1 = object()
        p.addConnection('foo', proto1)
        
        # X -> bar
        p.switch('bar')
        bar_d = p.alive['bar']
        proto2 = object()
        p.addConnection('bar', proto2)
        
        # X -> foo
        p.switch('foo')
        p.removeConnection('foo', proto1)
        
        self.assertFalse(foo_d.called, "Should not have called"
                         " since that is where the current forwarding is")
        self.assertEqual(p._connections['foo'], 0)
        self.assertFalse(bar_d.called)
        
        p.removeConnection('bar', proto2)
        self.assertTrue(bar_d.called)


    def test_ls(self):
        """
        You should be able to list the endpoints currently 
        forwarding
        """
        p = Pipe('foo')
        r = set(p.ls())
        self.assertEqual(r, set([
            # endpoint, connections, active/not
            ('foo', 0, True),
        ]))
        
        proto1 = object()
        p.addConnection('foo', proto1)
        self.assertEqual(set(p.ls()), set([
            ('foo', 1, True),
        ]))
        
        p.switch('bar')
        proto2 = object()
        p.addConnection('bar', proto2)
        self.assertEqual(set(p.ls()), set([
            ('foo', 1, False),
            ('bar', 1, True),
        ]))
        
        p.removeConnection('bar', proto2)
        self.assertEqual(set(p.ls()), set([
            ('foo', 1, False),
            ('bar', 0, True),
        ]))
        
        p.removeConnection('foo', proto1)
        self.assertEqual(set(p.ls()), set([
            ('bar', 0, True),
        ]))
        self.assertEqual(p.alive.keys(), ['bar'], "Only active or"
                         " still working endpoints should be "
                         "listed")
        p.switch('foo')
        self.assertEqual(set(p.ls()), set([
            ('foo', 0, True),
        ]))
        self.assertEqual(p.alive.keys(), ['foo'], "Only active or"
                         " still working endpoints should be listed")


    def test_wait_no_connections(self):
        """
        Waiting when there are no connections will succeed immediately.
        """
        p = Pipe('foo')
        return p.wait()


    def test_wait_conns(self):
        """
        If there are pending connections, wait is only called once they have
        finished.
        """
        p = Pipe('foo')
        
        proto1 = object()
        p.addConnection('foo', proto1)
        proto2 = object()
        p.addConnection('foo', proto2)
        
        p.switch('bar')
        
        w = p.wait()
        self.assertFalse(w.called, "Should not have called yet, because there "
                         "is an active connection to an old destination")
        
        p.removeConnection('foo', proto1)
        self.assertFalse(w.called)
        
        p.removeConnection('foo', proto2)
        self.assertTrue(w.called, "Should have called; the last connection "
                        "finished")


    def test_wait_multi_switch(self):
        """
        If you switch between lots of things, wait should wait for all previous
        connections -- not just the most recent.
        """
        p = Pipe('foo')
        
        proto1 = object()
        p.addConnection('foo', proto1)
        
        p.switch('bar')
        proto2 = object()
        p.addConnection('bar', proto2)
        
        p.switch('coo')
        proto3 = object()
        p.addConnection('coo', proto3)
        
        w = p.wait()
        self.assertFalse(w.called)
        
        p.removeConnection('bar', proto2)
        self.assertFalse(w.called)
        
        p.removeConnection('foo', proto1)
        self.assertTrue(w.called)


    def test_wait_switch_back_and_forth(self):
        """
        Switching back and forth should work
        """
        pipe = Pipe('foo')
        
        p1 = object()
        pipe.addConnection('foo', p1)
        
        foo_d = pipe.alive['foo']
        pipe.switch('bar')
        wait = pipe.wait()
        
        p2 = object()
        pipe.addConnection('bar', p2)
        
        pipe.switch('foo')
        p3 = object()
        pipe.addConnection('foo', p3)
        
        pipe.switch('bar')
        p4 = object()
        pipe.addConnection('bar', p4)
        
        pipe.switch('foo')
        p5 = object()
        pipe.addConnection('foo', p5)
        
        pipe.switch('bar')
        p6 = object()
        pipe.addConnection('bar', p6)
        
        self.assertFalse(wait.called, "Should not have called wait yet")
        self.assertFalse(foo_d.called)
        
        pipe.removeConnection('bar', p6)
        
        self.assertFalse(wait.called)
        self.assertFalse(foo_d.called)
        
        pipe.removeConnection('foo', p5)
        
        self.assertFalse(wait.called)
        self.assertFalse(foo_d.called)
        
        pipe.removeConnection('bar', p4)
        
        self.assertFalse(wait.called)
        self.assertFalse(foo_d.called)
        
        pipe.removeConnection('foo', p3)
        
        self.assertFalse(wait.called)
        self.assertFalse(foo_d.called)
        
        pipe.removeConnection('bar', p2)
        
        self.assertFalse(wait.called)
        self.assertFalse(foo_d.called)
        
        pipe.removeConnection('foo', p1)
        
        self.assertTrue(wait.called)
        self.assertTrue(foo_d.called)


    def test_wait_wait(self):
        """
        Calling wait multiple times should behave correctly
        """
        pipe = Pipe('foo')
        
        proto = object()
        pipe.addConnection('foo', proto)
        pipe.switch('bar')
        
        wait = pipe.wait()
        pipe.removeConnection('foo', proto)
        self.assertTrue(wait.called)
        
        pipe.switch('foo')
        proto = object()
        pipe.addConnection('foo', proto)
        pipe.switch('bar')
        
        wait = pipe.wait()
        pipe.removeConnection('foo', proto)
        self.assertTrue(wait.called)
        


