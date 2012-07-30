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


class Stop(amp.Command):
    
    arguments = []
    response = []


class Wait(amp.Command):

    arguments = [
        ('src', amp.String()),
    ]
    response = []


class List(amp.Command):

    response = [
        ('pipes', amp.AmpList(
            [
                ('src', amp.String()),
                ('dst', amp.String()),
                ('conns', amp.Integer()),
                ('active', amp.Boolean()),
            ]
        )),
    ]



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

    
    @Stop.responder
    def stop(self):
        self.plumber.stop()
        return {}


    @List.responder
    def ls(self):
        r = list(self.plumber.ls())
        pipes = []
        for src,dst,conns,active in r:
            pipes.append({
                'src': src,
                'dst': dst,
                'conns': conns,
                'active': active,
            })
        return {'pipes':pipes}


    @Wait.responder
    def wait(self, src):
        r = self.plumber.pipeCommand(src, 'wait')
        r.addCallback(lambda x: {})
        return r


class ServerFactory(Factory):


    protocol = Server
    
    
    def __init__(self, plumber):
        self.plumber = plumber


    def buildProtocol(self, addr):
        proto = self.protocol(self.plumber)
        proto.factory = self
        return proto
