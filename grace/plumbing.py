
from twisted.internet import defer, reactor
from twisted.application import service, strports


from grace.pipe import Pipe



class Plumber:
    """
    XXX
    """
    
    pipeFactory = Pipe


    def __init__(self, _reactor=None):
        self.pipe_services = service.MultiService()
        self._reactor = _reactor or reactor


    def addPipe(self, src, dst):
        """
        Start a new L{Pipe}.
        
        @param src: server endpoint on which to listen
        @param dst: client endpoint L{Pipe} will connect to
        
        @return: The newly-created Service for this pipe.  You can get to the
            L{Pipe} itself by accessing the C{factory} attribute.  Or you can
            get it with L{getPipe}.
        """
        factory = self.pipeFactory(dst)
        s = strports.service(src, factory)
        s.setName(src)
        s.setServiceParent(self.pipe_services)
        return s


    def rmPipe(self, src):
        """
        Remove an existing L{Pipe}.
        
        @param src: server endpoint on which the L{Pipe} is listening.
        
        @return: A C{Deferred} which will fire once the L{Pipe} has stopped
            listening.
        """
        s = [x for x in self.pipe_services if x.name == src][0]
        return defer.maybeDeferred(s.disownServiceParent)


    def getPipe(self, src):
        """
        Get the L{Pipe} that's listening on the given endpoint.
        
        @param src: An endpoint that was originally given to L{addPipe}.
        
        @return: L{Pipe}.
        """
        s = [x for x in self.pipe_services if x.name == src][0]
        return s.factory


    def pipeCommand(self, src, command, *args, **kwargs):
        """
        Call a method on one of my L{Pipe}s.
        
        @param src: The C{src} endpoint used to add the L{Pipe} with L{addPipe}.
        
        @type command: string
        @param command: Method name on L{Pipe} to execute
        
        @param *args: Args passed through to method.
        @param **kwargs: Keyword arguments passed through to method.
        
        @return: Whatever the L{Pipe}'s method returns.
        """
        pipe = self.getPipe(src)
        m = getattr(pipe, command, None)
        return m(*args, **kwargs)


    def ls(self):
        """
        List all my L{Pipe}s and their status.
        """
        keys = [x.name for x in self.pipe_services]
        keys.sort()
        for key in keys:
            for x in self.pipeCommand(key, 'ls'):
                yield tuple([key] + list(x))


    def stop(self):
        """
        Stop this whole process
        """
        self._reactor.stop()


