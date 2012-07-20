from twisted.internet import protocol, endpoints
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



