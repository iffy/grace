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
        dead_notice = yield r2.called
        self.assertEqual(dead_notice, 'unix:path=' + socket1, "The Deferred "
                         "should have fired back with the endpoint that just "
                         "disconnected.")


