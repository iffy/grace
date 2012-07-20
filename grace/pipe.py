from twisted.internet import protocol, endpoints, defer
from twisted.protocols.portforward import ProxyServer



class ProxyServer(ProxyServer):


    def connectionMade(self):
        # Don't read anything from the connecting client until we have
        # somewhere to send it to.
        self.transport.pauseProducing()

        client = self.clientProtocolFactory()
        client.setServer(self)

        from twisted.internet import reactor
        endpoint = endpoints.clientFromString(reactor, self.factory.dst)
        endpoint.connect(client)



class Pipe(protocol.Factory):
    """
    XXX
    """
    
    protocol = ProxyServer
    
    
    def __init__(self, dst):
        """
        XXX
        """
        self.dst = dst
        self.alive = {
            dst: defer.Deferred(),
        }


    def switch(self, dst):
        """
        Switch the place that this forwarder forwards to.
        
        @param dst: The client endpoint needed to connect to the receiving
            server.
        """
        old_dst = self.dst
        self.dst = dst
        return self.alive[old_dst]



