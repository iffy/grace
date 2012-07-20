from twisted.internet import protocol, defer
from twisted.python import log

from collections import defaultdict



class YippyYuckProtocol(protocol.Protocol):
    """
    I am the protocol that just keeps holding on.
    
    I am useful for testing because I accept connections and only
    finish the connections when commanded.
    """
    
    def __init__(self):
        self.satisfied = defer.Deferred()


    def connectionMade(self):
        log.msg('%r.connectionMade()' % self)
        self.data = ''
        self.factory.connectionMade(self)
        

    def dataReceived(self, data):
        log.msg('%r.dataReceived(%r)' % (self, data))
        self.data += data
        if self.data == self.expected_data:
            self.satisfied.callback(self)
        elif len(self.data) >= len(self.expected_data):
            self.satisfied.errback(Exception('Got unexpected data: %r\n%r' % (
                                     self.data, self.expected_data)))


    def connectionLost(self, reason):
        log.msg('%r.connectionLost(%r)' % (self, reason))



class YippyYuckFactory(protocol.Factory):

    
    protocol = YippyYuckProtocol

    
    def __init__(self, expected_data):
        self.protocols = []
        self.deferreds = defaultdict(lambda:defer.Deferred())
        self.expected_data = expected_data


    def buildProtocol(self, addr):
        proto = protocol.Factory.buildProtocol(self, addr)
        self.protocols.append(proto)
        return proto


    def dc(self, index):
        """
        Disconnect a protocol
        """
        proto = self.protocols[index]
        proto.transport.loseConnection()


    def connectionMade(self, proto):
        idx = self.protocols.index(proto)
        try:
            proto.expected_data = self.expected_data[idx]
        except IndexError as e:
            raise Exception("An unexpected protocol connected: %s" % idx)
        self.deferreds[idx].callback(proto)


    def connected(self, index):
        return self.deferreds[index]



class ClientFactory(protocol.ClientFactory):

    
    protocol = YippyYuckProtocol
    proto = None


    def __init__(self, expected_data):
        self.connected = defer.Deferred()
        self.expected_data = expected_data


    def connectionMade(self, proto):
        self.proto = proto
        proto.expected_data = self.expected_data
        self.connected.callback(proto)

