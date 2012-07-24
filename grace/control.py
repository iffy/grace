from twisted.protocols import amp
from twisted.internet.protocol import Factory



class AddPipe(amp.Command):
    
    arguments = [
        ('src', amp.String()),
        ('dst', amp.String()),
    ]
    response = []


class RemovePipe(amp.Command):
    
    arguments = [
        ('src', amp.String()),
    ]
    response = []


class Switch(amp.Command):
    
    arguments = [
        ('src', amp.String()),
        ('dst', amp.String()),
    ]
    response = []



class Server(amp.AMP):
    """
    Administration server protocol
    """
    
    
    def __init__(self, plumber):
        self.plumber = plumber


    @AddPipe.responder
    def addPipe(self, src, dst):
        self.plumber.addPipe(src, dst)
        return {}


    @RemovePipe.responder
    def rmPipe(self, src):
        self.plumber.rmPipe(src)
        return {}


    @Switch.responder
    def switch(self, src, dst):
        self.plumber.pipeCommand(src, 'switch', dst)
        return {}


class ServerFactory(Factory):


    protocol = Server
