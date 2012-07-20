from twisted.trial.unittest import TestCase
from twisted.internet import reactor, defer, task, endpoints


from grace.test.util import YippyYuckFactory, ClientFactory
from grace.pipe import Pipe



class PipeTest(TestCase):

    timeout = 3


    @defer.inlineCallbacks
    def test_forwards_TCP(self):
        """
        Forwarding should work (the data should get to the remote
        and vice versa).
        """
        # set up service we're forwarding to.
        testf = YippyYuckFactory()
        ep = endpoints.serverFromString(reactor, 'tcp:10333')
        test_port = yield ep.listen(testf)
        self.addCleanup(test_port.stopListening)
        
        # start Pipe
        pipe = Pipe('tcp:host=127.0.0.1:port=10333')
        pipe_ep = endpoints.serverFromString(reactor, 'tcp:10111')
        pipe_port = yield pipe_ep.listen(pipe)
        self.addCleanup(pipe_port.stopListening)
        
        # start a client to test
        clientf = ClientFactory()
        client_ep = endpoints.clientFromString(reactor, 
                'tcp:host=127.0.0.1:port=10111')
        client = yield client_ep.connect(clientf)
        self.addCleanup(client.transport.loseConnection)

        # send some data forward and back
        client.transport.write('hey')
        testf.protocols[0].transport.write('hey back')
        
        def check():
            self.assertEqual(testf.protocols[0].data, 'hey')
            self.assertEqual(client.data, 'hey back')
        
        # XXX how can this be better?
        yield task.deferLater(reactor, 1, check)


