"""
Grace daemon
"""

from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import strports
from twisted.python.filepath import FilePath



class Options(usage.Options):

    
    longdesc = ''

    synopsis = '[options] basedirectory'
    
    def parseArgs(self, directory):
        self['dir'] = directory



class ServiceMaker(object):

    implements(IServiceMaker, IPlugin)
    
    tapname = 'grace'
    description = 'Graceful port forwarder'
    options = Options
    
    
    def makeService(self, options):
        """
        Construct the grace daemon service
        """
        base_dir = FilePath(options['dir'])
        socket = base_dir.child('grace.socket')
        if not base_dir.exists():
            base_dir.makedirs()

        from grace.plumbing import Plumber
        plumber = Plumber()
        
        from grace.control import Server
        server = Server(plumber)

        from twisted.internet.protocol import Factory
        f = Factory()
        f.protocol = lambda *a: Server(plumber)

        admin_endpoint = 'unix:' + socket.path
        return strports.service(admin_endpoint, f)
        