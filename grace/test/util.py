from twisted.internet import protocol, defer
from twisted.python import log

from collections import defaultdict



class YippyYuckProtocol(protocol.Protocol):
    """
    I am the protocol that just keeps holding on.
    
    I am useful for testing because I accept connections and only
    finish the connections when commanded.
    """


    def connectionMade(self):
        log.msg('%r.connectionMade()' % self)
        self.data = ''
        self.factory.connectionMade(self)
        

    def dataReceived(self, data):
        log.msg('%r.dataReceived(%r)' % (self, data))
        self.data += data


    def connectionLost(self, reason):
        log.msg('%r.connectionLost(%r)' % (self, reason))



class YippyYuckFactory(protocol.Factory):

    
    protocol = YippyYuckProtocol

    
    def __init__(self):
        self.protocols = []
        self.deferreds = defaultdict(lambda:defer.Deferred())


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
        self.deferreds[idx].callback(proto)


    def connected(self, index):
        return self.deferreds[index]



class ClientFactory(protocol.ClientFactory):

    
    protocol = YippyYuckProtocol
    proto = None
    connected = defer.Deferred()


    def connectionMade(self, proto):
        self.proto = proto
        self.connected.callback(proto)

