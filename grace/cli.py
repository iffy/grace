from twisted.internet import protocol, defer, reactor, utils
from twisted.python import usage

import commands
import sys, os


from grace.tac import setupDir



class Runner:

    
    def _twistdBin(self):
        """
        Get the path to the twistd executable.
        """
        # XXX what problems will this cause by blocking?
        return commands.getoutput('which twistd')


    def twistd(self, *args, **kwargs):
        twistd = self._twistdBin()
        return utils.getProcessOutputAndValue(twistd, *args, **kwargs)


    def start(self, basedir, src, dst):
        setupDir(basedir, (src, dst))
        return self.twistd(['--logfile=grace.log', '--pidfile=grace.pid',
                            '--python=grace.tac'], env=None, path=basedir)


    def run(self):
        """
        """
        options = Options()
        options.parseOptions()
        so = options.subOptions
        if options.subCommand == 'start':
            self.code = 0
            r = self.start(options['basedir'], so['src'], so['dst'])
            def done(result):
                out, err, code = result
                self.code = code
                if out:
                    sys.stdout.write(out)
                    sys.stdout.flush()
                if err:
                    sys.stderr.write(err)
                    sys.stderr.flush()
                if not err and not self.code:
                    print 'Started'
                reactor.stop()
            r.addCallback(done)
            reactor.run()
            sys.exit(self.code)
            



class StartOptions(usage.Options):

    synopsis = 'src dst'
    longdesc = ('`src` is the server endpoint on which to listen.  `dst` is a '
                'client endpoint to connect to.  For example, to start '
                'forwarding from tcp port 9000 to tcp port 8700 do: '
                '\n\ngrace start tcp:9000 tcp:host=127.0.0.1:port=8700')


    def parseArgs(self, src, dst):
        self['src'] = src
        self['dst'] = dst



class Options(usage.Options):


    optParameters = [
        ['basedir', 'd', '~/.grace', "Directory in which to store running "
            "process information"],
    ]

    subCommands = [
        ['start', None, StartOptions, "Start forwarding"],
    ]
    
    
    def postOptions(self):
        self['basedir'] = os.path.expanduser(self['basedir'])



_runner = Runner()
run = _runner.run