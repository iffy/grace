from twisted.internet import protocol, defer, reactor, utils, task
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
        r = self.twistd(['--logfile=grace.log', '--pidfile=grace.pid',
                         '--python=grace.tac'], env=None, path=basedir)
        
        def cb(result, basedir):
            socket = self._waitForFile(FilePath(basedir).child('grace.socket'))
            return socket.addCallback(lambda x:result)
        return r.addCallback(cb, basedir)


    def _waitForFile(self, filepath):
        """
        Start waiting for a file
        """
        d = defer.Deferred()
        def f(filepath, d):
            if filepath.exists():
                d.callback(None)
                
        lc = task.LoopingCall(f, filepath, d)
        lc.start(0.1)
        
        def cb(result, lc):
            lc.stop()
            return
        return d.addCallback(cb, lc)
        


    def stop(self, basedir):
        """
        Stop a grace forwarder.
        
        @param basedir: Directory with pid file
        """
        from grace.control import Stop
        from twisted.protocols import amp

        fp = FilePath(basedir)
        client = protocol.ClientCreator(reactor, amp.AMP)
        socket = fp.child('grace.socket').path
        r = client.connectUNIX(socket)
        r.addCallback(lambda p: p.callRemote(Stop))
        return r


    def ls(self, basedir):
        """
        XXX
        """
        from grace.control import List
        from twisted.protocols import amp

        fp = FilePath(basedir)
        client = protocol.ClientCreator(reactor, amp.AMP)
        socket = fp.child('grace.socket').path
        r = client.connectUNIX(socket)
        self.proto = None
        def gotProto(proto):
            self.proto = proto
            return proto.callRemote(List)
        
        def gotList(result):
            self.proto.transport.loseConnection()
            return result['pipes']
        
        r.addCallback(gotProto)
        r.addCallback(gotList)
        return r


    def switch(self, basedir, src, dst):
        """
        XXX
        """
        from grace.control import Switch
        from twisted.protocols import amp

        fp = FilePath(basedir)
        client = protocol.ClientCreator(reactor, amp.AMP)
        socket = fp.child('grace.socket').path
        r = client.connectUNIX(socket)
        self.proto = None
        def gotProto(proto):
            self.proto = proto
            return proto.callRemote(Switch, src=src, dst=dst)
        
        def gotList(result):
            self.proto.transport.loseConnection()
            return result
        
        r.addCallback(gotProto)
        r.addCallback(gotList)
        return r


    def wait(self, basedir, src):
        """
        XXX
        """
        # XXX holy duplicate code, batman
        from grace.control import Wait
        from twisted.protocols import amp
        
        fp = FilePath(basedir)
        client = protocol.ClientCreator(reactor, amp.AMP)
        socket = fp.child('grace.socket').path
        r = client.connectUNIX(socket)
        self.proto = None
        def gotProto(proto):
            self.proto = proto
            return proto.callRemote(Wait, src=src)
        
        def doneWaiting(result):
            self.proto.transport.loseConnection()
            return result
        
        r.addCallback(gotProto)
        r.addCallback(doneWaiting)
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
        elif options.subCommand == 'stop':
            self.code = 0
            r = self.stop(options['basedir'])
            def cb(result):
                print 'Stopped'
                reactor.stop()
            def eb(result):
                print 'Error: %s' % result
                reactor.stop()
            r.addCallback(cb)
            r.addErrback(eb)
            reactor.run()
            sys.exit(self.code)
        elif options.subCommand == 'ls':
            self.code = 0
            r = self.ls(options['basedir'])
            def cb(result):
                print 'src dst connections status'
                for row in result:
                    if row['active']:
                        row['active'] = 'active'
                    else:
                        row['active'] = 'inactive'
                    print '%(src)s %(dst)s %(conns)s %(active)s' % row
                reactor.stop()
            def eb(result):
                print 'Error: %s' % result
                self.code = 1
                reactor.stop()
            r.addCallback(cb)
            r.addErrback(eb)
            reactor.run()
            sys.exit(self.code)
        elif options.subCommand == 'switch':
            self.code = 0
            r = self.switch(options['basedir'], so['src'], so['dst'])
            def cb(result):
                reactor.stop()
            def eb(result):
                print 'Error: %s' % result
                self.code = 1
                reactor.stop()
            r.addCallback(cb)
            r.addErrback(eb)
            reactor.run()
            sys.exit(self.code)
        elif options.subCommand == 'wait':
            self.code = 0
            r = self.wait(options['basedir'], so['src'])
            def cb(result):
                reactor.stop()
            def eb(result):
                print 'Error: %s' % result
                self.code = 1
                reactor.stop()
            r.addCallback(cb)
            r.addErrback(eb)
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



class ListOptions(usage.Options):

    synopsis = ''
    longdesc = ('List current forwarding rules')



class SwitchOptions(usage.Options):

    synopsis = 'src dst'
    longdesc = ('`src` is the server endpoint on which grace is currently '
                'listening.  `dst` is the client endpoint to connect future '
                'connections to.  For example, if you started grace like this:'
                '\n\ngrace start tcp:9000 tcp:host=127.0.0.1:port=8700'
                '\n\nThen you can switch traffic from port 8700 to another by '
                'doing this:'
                '\n\ngrace switch tcp:9000 tcp:host=127.0.0.1:port=6000')


    def parseArgs(self, src, dst):
        self['src'] = src
        self['dst'] = dst


class WaitOptions(usage.Options):

    synopsis = 'src'
    longdesc = ('`src` is the listening endpoint')


    def parseArgs(self, src):
        self['src'] = src



class Options(usage.Options):


    optParameters = [
        ['basedir', 'd', '~/.grace', "Directory in which to store running "
            "process information"],
    ]

    subCommands = [
        ['start', None, StartOptions, "Start forwarding"],
        ['stop', None, StopOptions, "Stop forwarding"],
        ['ls', None, ListOptions, "List forwards"],
        ['switch', 'x', SwitchOptions, "Switch forwarding"],
        ['wait', 'w', WaitOptions, "Wait for all traffic to forward to new "
            "destination"],
    ]
    
    
    def postOptions(self):
        self['basedir'] = os.path.expanduser(self['basedir'])



_runner = Runner()
run = _runner.run



