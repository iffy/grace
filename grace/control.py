from twisted.protocols import amp


class Server(amp.AMP):
    """
    XXX
    """
    
    
    def __init__(self, plumber):
        self.plumber = plumber


    def addPipe(self, *args):
        self.plumber.addPipe(*args)


    def rmPipe(self, *args):
        self.plumber.rmPipe(*args)


    def switch(self, key, *args, **kwargs):
        self.plumber.pipeCommand(key, 'switch', *args, **kwargs)



class Client:
    pass