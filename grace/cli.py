from twisted.internet import protocol, defer, reactor, utils
from twisted.python import usage
from twisted.python.filepath import FilePath

import commands
import sys, os


from grace.tac import setupDir



class Runner:
    """
    I interface between the command line and grace.
    """

    
    def _twistdBin(self):
        """
        Get the path to the twistd executable.
        
        @return: Full path to C{twistd} exectuable.
        """
        # XXX what problems will this cause by blocking?
        return commands.getoutput('which twistd')


    def twistd(self, *args, **kwargs):
        """
        Run the C{twistd} command-line executable with the given arguments.
        
        @param *args: Passed through to
            C{twisted.internet.utils.getProcessOutputAndValue}.
        @param *kwargs: Passed through to
            C{twisted.internet.utils.getProcessOutputAndValue}.
        
        @return: C{Deferred} which fires with (out, err, code) tuple.
        """
        twistd = self._twistdBin()
        return utils.getProcessOutputAndValue(twistd, *args, **kwargs)


    def start(self, basedir, src, dst):
        """
        Start a grace forwarder.
        
        @param basedir: Directory to put the configuration, log and pid files.
        @param src: Listening endpoint
        @param dst: Connecting endpoint
        
        @return: C{Deferred} which fires with (out, err, code) tuple from
            running C{twistd} to start the process.
        """
        setupDir(basedir, (src, dst))
        return self.twistd(['--logfile=grace.log', '--pidfile=grace.pid',
                            '--python=grace.tac'], env=None, path=basedir)


    def stop(self, basedir):
        """
        Stop a grace forwarder.
        
        @param basedir: Directory with pid file
        """
        from grace.control import Stop
        from twisted.protocols import amp

        def eb(response):
            self.fail(response)

        fp = FilePath(basedir)
        client = protocol.ClientCreator(reactor, amp.AMP)
        socket = fp.child('grace.socket').path
        r = client.connectUNIX(socket)
        r.addCallback(lambda p: p.callRemote(Stop)).addErrback(eb)
        return r


    def run(self):
        """
        Run a command from the command line.
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



class StopOptions(usage.Options):

    synopsis = ''
    longdesc = ('Stop a running grace process')



class Options(usage.Options):


    optParameters = [
        ['basedir', 'd', '~/.grace', "Directory in which to store running "
            "process information"],
    ]

    subCommands = [
        ['start', None, StartOptions, "Start forwarding"],
        ['stop', None, StopOptions, "Stop forwarding"],
    ]
    
    
    def postOptions(self):
        self['basedir'] = os.path.expanduser(self['basedir'])



_runner = Runner()
run = _runner.run



