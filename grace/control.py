from twisted.protocols import amp


class Control(amp.AMP):
    """
    XXX
    """
    
    
    def __init__(self, plumber):
        self.plumber = plumber


    def addPipe(self, 