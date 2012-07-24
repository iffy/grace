

from twisted.python import usage
import os.path



class StartOptions(usage.Options):

    longdesc = ('Start forwarding from one endpoint to another.'
                '  The from argument must be a server endpoint.  The to '
                'argument must be a client endpoint')

    synopsis = '[options] from to'

    def parseArgs(self, src, dst):
        self['dst'] = dst
        self['src'] = src




class Options(usage.Options):


    optParameters = [
        ['dir', 'd', '~/.grace', "Directory to store grace process info"],
    ]

    subCommands = [
        ['start', None, StartOptions, "Start forwarding"],
    ]
    
    def postOptions(self):
        self['dir'] = os.path.expanduser(self['dir'])



def run():
    options = Options()
    options.parseOptions()
    
    if options.subCommand == 'start':
        from grace.control import AddPipe
    
    print repr(options)
