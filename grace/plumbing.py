
from twisted.internet import defer
from twisted.application import service, strports


from grace.pipe import Pipe



class Plumber:
    """
    XXX
    """
    
    pipeFactory = Pipe


    def __init__(self):
        self.pipe_services = service.MultiService()


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
        self.pipe_services.addService(s)
        return s


    def rmPipe(self, src):
        """
        Remove an existing L{Pipe}.
        
        @param src: server endpoint on which the L{Pipe} is listening.
        
        @return: A C{Deferred} which will fire once the L{Pipe} has stopped
            listening.
        """
        s = [x for x in self.pipe_services if x.name == src][0]
        return defer.maybeDeferred(self.pipe_services.removeService, s)


    def getPipe(self, src):
        """
        Get the L{Pipe} that's listening on the given endpoint.
        
        @param src: An endpoint that was originally given to L{addPipe}.
        
        @return: L{Pipe}.
        """
        s = [x for x in self.pipe_services if x.name == src][0]
        return s.factory