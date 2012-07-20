from twisted.trial.unittest import TestCase
from twisted.internet import reactor, defer, task, endpoints
from twisted.python import log


from grace.test.util import YippyYuckFactory, ClientFactory
from grace.pipe import Pipe



class PipeTest(TestCase):

    timeout = 1


    @defer.inlineCallbacks
    def t_endpoints(self, client, pfserver, pfclient, server):
        """
        Test that forwarding works from C{client} to C{pfserver}
        using C{pfclient} to C{server}
        """
        # set up service we're forwarding to.
        testf = YippyYuckFactory(expected_data=['hey'])
        ep = endpoints.serverFromString(reactor, server)
        test_port = yield ep.listen(testf)
        self.addCleanup(test_port.stopListening)
        
        # start Pipe
        pipe = Pipe(pfclient)
        pipe_ep = endpoints.serverFromString(reactor, pfserver)
        pipe_port = yield pipe_ep.listen(pipe)
        self.addCleanup(pipe_port.stopListening)
        
        # start a client to test
        clientf = ClientFactory(expected_data='hey back')
        client_ep = endpoints.clientFromString(reactor, client)
        client = yield client_ep.connect(clientf)
        self.addCleanup(client.transport.loseConnection)

        # send some data forward and back
        client.transport.write('hey')
        server_proto = yield testf.connected(0)
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


