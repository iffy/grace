from twisted.internet import protocol, endpoints, defer
from twisted.python import log
from twisted.protocols import portforward



class ProxyServer(portforward.ProxyServer):


    def connectionMade(self):
        # Don't read anything from the connecting client until we have
        # somewhere to send it to.
        self._dst = dst = self.factory.dst
        self.factory.addConnection(dst, self)
        self.transport.pauseProducing()

        client = self.clientProtocolFactory()
        client.setServer(self)

        from twisted.internet import reactor
        endpoint = endpoints.clientFromString(reactor, dst)
        endpoint.connect(client)


    def connectionLost(self, reason):
        self.factory.removeConnection(self._dst, self)
        return portforward.ProxyServer.connectionLost(self, reason)



class Pipe(protocol.Factory):
    """
    XXX
    """
    
    protocol = ProxyServer
    
    
    def __init__(self, dst):
        """
        XXX
        """
        self.alive = {}
        self.connections = {}
        self._setDst(dst)


    def addConnection(self, dst, conn):
        log.msg('addConnection(%r, %r)' % (dst, conn))
        self.connections[dst] += 1


    def removeConnection(self, dst, conn):
        log.msg('removeConnection(%r, %r)' % (dst, conn))
        self.connections[dst] -= 1
        if self.connections[dst] == 0:
            self.alive[dst].callback(dst)


    def _setDst(self, dst):
        self.dst = dst
        self.connections[dst] = 0
        self.alive[dst] = defer.Deferred()
        

    def switch(self, dst):
        """
        Switch the place that this forwarder forwards to.
        
        @param dst: The client endpoint needed to connect to the receiving
            server.
        """
        old_dst = self.dst
        self._setDst(dst)
        return self.alive[old_dst]



