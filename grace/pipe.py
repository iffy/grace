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
    I forward connections from wherever I'm listening to a
    particular endpoint.  The endpoint I forward to can be changed
    at runtime with L{switch}.
    
    @ivar alive: A dictionary whose keys are endpoints to which I
        have at least one connection going and whose values are
        C{Deferred}s that fire when the connections have finished.
    """
    
    protocol = ProxyServer
    
    
    def __init__(self, dst):
        """
        @param dst: The endpoint a client would use to connect to
            the server I will forward to.  For instance:
            C{tcp:host=127.0.0.1:port=2930}.
        """
        self.alive = {}
        self._connections = {}
        self._setDst(dst)


    def addConnection(self, dst, conn):
        self._connections[dst] += 1


    def removeConnection(self, dst, conn):
        self._connections[dst] -= 1
        self._expireDst(dst)


    def _expireDst(self, dst):
        if self._connections[dst] == 0 and dst != self.dst:
            self.alive[dst].callback(dst)
            del self._connections[dst]
            del self.alive[dst]


    def _setDst(self, dst):
        self.dst = dst
        if dst not in self._connections:
            self._connections[dst] = 0
        self.alive[dst] = defer.Deferred()
        

    def switch(self, dst):
        """
        Switch the place that this forwarder forwards to.
        
        @param dst: The client endpoint needed to connect to the receiving
            server.
        
        @return: A C{Deferred} which will fire when the last
            remaining connection from the previous destination has
            been closed.  It will fire with the previous destination
            endpoint.
        """
        old_dst = self.dst
        self._setDst(dst)
        r = self.alive[old_dst]
        self._expireDst(old_dst)
        return r


    def ls(self):
        """
        List the endpoints that are either currently active or
        have connections pending.
        
        @rtype: generator
        @return: A list of 3-tuples of the form:
            (ENDPOINT, NUMBER OF CONNECTIONS, ACTIVE?)
        """
        for endpoint, conns in self._connections.items():
            yield (endpoint, conns, endpoint == self.dst)


